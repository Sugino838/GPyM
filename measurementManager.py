import sys
import os
import threading
import math
import matplotlib.pyplot as plt
import inputModule as inp
from scipy import interpolate
import msvcrt
import time 
import utilityModule as util
from chardet.universaldetector import UniversalDetector
from multiprocessing import Process, Lock, Manager,Value
import windowModule
from enum import Enum,auto
from concurrent.futures import ThreadPoolExecutor
import pyperclip

class State(Enum):
    READY=auto()
    START=auto()
    UPDATE=auto()
    END=auto()
    BUNKATSU=auto()
    ALLEND=auto()

def set_dirpath(datadir,tempdir):
    global _datadir,_tempdir
    _datadir=datadir
    _tempdir=tempdir


_file_label=""
graph_renew_interval=1



__state=State.READY

def measure_start(start,update,end,on_command,bunkatsu):

    
    global __state
    global _filename,_datelabel
    _filename,_datelabel,_filename_withoutdate=inp.get_filename()
    _copy_filename(_filename_withoutdate)

    if start is not None:
        __state=State.START
        start()

    _set_file()#ファイル作成
    _run_window()#グラフウィンドウの立ち上げ

    
    #finishコマンドの入力待ちをする
    global _lock_thread
    _lock_thread=threading.Lock()

    if on_command is not None:
        threading.Thread(target=_wait_command_input,args=(on_command,_lock_thread)).start()

    print("measuring start...")

    __state=State.UPDATE
    while True:#測定終了までupdateを回す
        if _isfinish.value==1:
            break
        _lock_thread.acquire()
        update()
        _lock_thread.release()

    print("measurement has finished...")

    if end is not None:
        __state=State.END
        end()
    
    _savefile.close()
    
    if bunkatsu is not None:
        __state=State.BUNKATSU
        _bunkatsu(bunkatsu)
    __state=State.ALLEND
    

    
    _end()





def get_tempdir():
    return _tempdir

def finish():
    _isfinish.value=1
    

def _end():
    def wait_enter():
        nonlocal endflag
        input("enter and close window...") 
        endflag=True
    def wait_closewindow():
        nonlocal endflag
        _window_process.join()
        endflag=True

    endflag=False

    thread1=threading.Thread(target=wait_closewindow)
    thread1.setDaemon(True)
    thread1.start()

    time.sleep(0.1)

    endflag=False #既にグラフが消えていた場合はwait_enterを終了処理とする. それ以外の場合はwait_closewindowも終了処理とする


    thread2=threading.Thread(target=wait_enter)
    thread2.setDaemon(True)
    thread2.start()

    while True:
        if endflag:
            _window_process.terminate()
            sys.exit()
        time.sleep(0.2)
    


        
def _wait_command_input(on_command,_lock_thread):#終了コマンドの入力待ち, これは別スレッドで動かす
    print("enter 'finish' and finish measurement... ")
    while True:

        isf=_isfinish.value
        if msvcrt.kbhit() and isf==0: #入力が入って初めてinputが動くように(inputが動くとその間ループを抜けられないので)
            command=input()
            _lock_thread.acquire()#メイン部分でどんな処理が書かれるか分からないのでGPIB制御がupdateと衝突しないように鍵をかける
            on_command(command)
            _lock_thread.release()
        elif isf==1:
            break
        time.sleep(0.1)

        
def _bunkatsu(bunkatsu):
    dirpath=_datadir+"\\"+_filename
    os.mkdir(dirpath)
    import shutil
    new_filepath=dirpath+"\\"+_filename+".txt"
    global _filepath
    shutil.move(_filepath,new_filepath)
    _filepath=new_filepath
    bunkatsu(_filepath)


def set_calibration_file(filename_calb): #プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み


    if not os.path.isfile(filename_calb):
        input(os.getcwd()+"で"+filename_calb+"にアクセスしようとしましたが存在しませんでした. キャリブレーションファイルはマクロと同じフォルダに置いてください")
        sys.exit()


    global _interpolate_func
    file=open(filename_calb,'r',encoding=util.get_encode_type(filename_calb))

    x=[]
    y=[]

    while True:
        line=file.readline() #1行ずつ読み取り
        line = line.strip() #前後空白削除
        line = line.replace('\n','') #末尾の\nの削除

        if line == "": #空なら終了
            break

        try:
            array_string = line.split(",") #","で分割して配列にする
            array_float=[float(s) for s in array_string] #文字列からfloatに変換
            
            x.append(array_float[1])#抵抗値の情報
            y.append(array_float[0])#対応する温度の情報
        except Exception:
            pass
        
    print("calibration_range: x=",x[0]," ~ ",x[len(x)-1])
    global _interpolate_func
    _interpolate_func = interpolate.interp1d(x,y) # 線形補間関数定義

def calibration(x):
    """
    プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す
    """
    try:
        y=_interpolate_func(x)
    except ValueError as e:
        print(util.get_error_info(e))
        input("Keithleyから入力されるデータがキャリブレーションファイルのデータ範囲外です")
        print(e)
        raise
    except NameError as e:
        print(util.get_error_info(e))
        input("キャリブレーションファイルが読み込まれていません")
        print(e)
        raise
    except Exception as e:
        print(util.get_error_info(e))    
        input("calibration:予期せぬエラーが発生しました") 
        print(e)
        raise
    return y


def set_label(label):
    if __state!=State.START:
        print("WARNING : "+sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    global _file_label
    if not label[-1]=="\n":#末尾に改行コードがついていなければくっつける
        label+="\n"
    _file_label=label

def _set_file():#ファイルの作成,準備
    
    if not os.path.isdir(_datadir):#フォルダの存在確認
        input(_datadir+"のフォルダにアクセス使用としましたが､存在しませんでした")   
        sys.exit()
    

    
    global _filepath
    _filepath=_datadir+"\\"+ _filename+".txt"
        
    global _savefile
    _savefile = open(_filepath, 'x',encoding="utf-8") #ファイル作成
    _savefile.write(_file_label) #測定データのラベル書き込み

    _savefile.flush() #書き込みを反映させる

    return _filepath




def _run_window():#グラフと終了コマンド待ち処理を走らせる
    manager = Manager() 
    global _share_list,_isfinish,_lock_process
    _share_list=manager.list()#プロセス間で共有できるリスト
    _isfinish=Value("i",0)#測定の終了を判断するためのint
    _lock_process=Lock()#2つのプロセスで同時に同じデータを触らないようにする排他制御のキー
    #グラフ表示は別プロセスで実行する
    global _window_process
    _window_process=Process(target=windowModule.exec,args=(_share_list,_isfinish,_lock_process,_xlog,_ylog,graph_renew_interval))
    _window_process.daemon=True
    _window_process.start()





_xlog=False
_ylog=False
def set_logscale(xlog=False,ylog=False):#グラフのlogスケール設定
    if __state!=State.START:
        print("WARNING : "+sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    if type(xlog) is not bool or type(ylog) is not bool:
        input("Error: set_logscaleの引数はTrueかFalseです")
        sys.exit()
    global _xlog,_ylog
    _xlog=xlog
    _ylog=ylog





    
def rename_file():#ファイル名変更
    if __state!=State.END:
        input("Error : "+sys._getframe().f_code.co_name+"はend関数内で用いてください")
        sys.exit()


    _,_,new_filename=inp.get_filename(text="ファイル名を変更する場合は入力してください > ")



    if new_filename !="": #何も入力しなかったときは名前変更しない
        new_filename=_datelabel+"_"+new_filename
        global _filepath, _savefile,_filename

        _savefile.close()

        oldfilepath=_datadir+"\\"+_filename+".txt"
        newfilepath=_datadir+"\\"+new_filename+".txt"
    
        os.rename(oldfilepath,newfilepath)
        
        _filepath=newfilepath
        _filename=new_filename
        _savefile=open(_filepath,mode="a",encoding=util.get_encode_type(_filepath))
        print("ファイル名を"+new_filename+"に変更しました")

    else:
        print("ファイル名を変更しませんでした")

    




def save_data(data):#データ保存
    if __state!=State.UPDATE and __state!=State.END:
        print("WARNING : "+sys._getframe().f_code.co_name+"はupdateもしくはend関数内で用いてください")
    
    if type(data) is str:#文字列を入力したときにも一応対応
        _savefile.write(data)#書き込み
    else:
        text=""
        for i in range(len(data)):#タプルの全要素をstringにして並べる
            if i == 0:
                text+=str(data[0])
            else:
                text+=","+str(data[i])
        text+="\n"#末尾に改行記号
        _savefile.write(text)#書き込み
    _savefile.flush()#反映. この処理はやや重いので高速化したいならこれを呼ばずに最後にcloseで一気に反映させるのが良い
    
    


def plot_data(x,y,color="black"):#データをグラフにプロット
    if __state!=State.UPDATE:
        print("WARNING : "+sys._getframe().f_code.co_name+"はstartもしくはupdate関数内で用いてください")
    data=(x,y,color)
    _lock_process.acquire() #   ロックをかけて別プロセスからアクセスできないようにする
    _share_list.append(data)# プロセス間で共有するリストにデータを追加
    _lock_process.release()#ロック解除
    

def _copy_filename(filename):
    pyperclip.copy(filename)