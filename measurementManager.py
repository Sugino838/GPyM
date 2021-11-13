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
from utilityModule import GPyMException


colors=["black","red","green","blue","orange","deepskyblue","purple","saddlebrown","crimson","limegreen","royalblue","orangered","skyblue","darkviolet"]


class State(Enum):
    READY=auto()
    START=auto()
    UPDATE=auto()
    END=auto()
    BUNKATSU=auto()
    ALLEND=auto()

def _set_variables(datadir,tempdir,file_label):#グローバル変数のセット
    global _datadir,_tempdir,_data_label
    _datadir=datadir
    _tempdir=tempdir
    _data_label=file_label


graph_renew_interval=None

__logger=util.mklogger(__name__)


__flowwindow_parameter=None

__command=None
__repeat=False

def _measure_start(start,update,end,on_command,bunkatsu):
    global __state
    __state=State.READY

    while msvcrt.kbhit():#既に入っている入力は消す
        msvcrt.getwch()
    
    global _filename
    _filename = _input_filename()
    
    set_plot_info()#start内で呼ばれなかったときのためにここで一回呼んでおく

    if start is not None:
        __state=State.START
        start()

    _set_file()#ファイル作成
    _run_window()#グラフウィンドウの立ち上げ

    


    if on_command is not None:
        cmthr=threading.Thread(target=_wait_command_input)
        cmthr.setDaemon(True)
        cmthr.start()

    print("measuring start...")
    __state=State.UPDATE
    global __command
    while True:#測定終了までupdateを回す
        if _isfinish.value==1:
            break
        if __command is None:
            update()
        else:
            on_command(__command)
            __command=None


    print("measurement has finished...")

    if end is not None:
        __state=State.END
        end()
    
    _savefile.close()
    
    if bunkatsu is not None:
        __state=State.BUNKATSU
        _bunkatsu(bunkatsu)
    __state=State.ALLEND
    

    if __repeat:
        _do_repeat(start,update,end,on_command,bunkatsu)
    else:
        _end()





def get_tempdir():
    return _tempdir

def finish():
    _isfinish.value=1
    

def _end():
    """
    終了処理. コンソールからの終了と､グラフウィンドウを閉じたときの終了の2つを実行できるようにスレッドを用いる
    """
    def wait_enter():#コンソール側の終了
        nonlocal endflag #nonlocalを使うとクロージャーになる
        input("enter and close window...") #エンターを押したら次へ進める
        endflag=True
    def wait_closewindow():#グラフウィンドウからの終了
        nonlocal endflag
        _window_process.join()#_window_processの終了待ち
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
    


        
def _wait_command_input():#終了コマンドの入力待ち, これは別スレッドで動かす
    while True:
        isf=_isfinish.value
        if msvcrt.kbhit() and isf==0: #入力が入って初めてinputが動くように(inputが動くとその間ループを抜けられないので)
            command=input()
            global __command
            __command=command
            while __command is not None:
                time.sleep(0.1)
        elif isf==1:
            break
        time.sleep(0.1)

        
def _bunkatsu(bunkatsu):
    dirpath=_datadir+"\\"+_filename
    os.mkdir(dirpath)
    import shutil
    new_filepath=dirpath+"\\"+_filename+".txt"
    global _filepath
    shutil.move(_filepath,new_filepath)#DATADIR直下から新規フォルダにファイルを移し替える
    _filepath=new_filepath
    bunkatsu(_filepath)


def set_calibration_file(filename_calb): #プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み

    if not os.path.isfile(filename_calb):
        raise util.create_error("キャリブレーションファイル"+filename_calb+"が存在しません. "+os.getcwd()+"で'"+filename_calb+"'にアクセスしようとしましたが存在しませんでした. キャリブレーションファイルはマクロと同じフォルダに置いてください",__logger)


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
        raise util.create_error("Keithleyから入力されるデータがキャリブレーションファイルのデータ範囲外になっている可能性があります",__logger,e)
    except NameError as e:
        raise util.create_error("キャリブレーションファイルが読み込まれていない可能性があります",__logger,e)
    except Exception as e:
        raise util.create_error("予期せぬエラーが発生しました",__logger,e)
    return y

__user_label=""
def set_label(label):
    if __state!=State.START:
        __logger.warning(sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    global __user_label
    if not label[-1]=="\n":#末尾に改行コードがついていなければくっつける
        label+="\n"
    __user_label=__user_label+label

def _set_file():#ファイルの作成,準備
    
    if not os.path.isdir(_datadir):#フォルダの存在確認
        raise util.create_error(_datadir+"のフォルダにアクセスしようとしましたが､存在しませんでした",__logger)

    
    global _filepath
    _filepath=_datadir+"\\"+ _filename+".txt"
        
    global _savefile
    _savefile = open(_filepath, 'x',encoding="utf-8") #ファイル作成

    file_label=__user_label+_data_label+"\n"
    _savefile.write(file_label) #測定データのラベル書き込み

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
    _window_process=Process(target=windowModule.exec,args=(_share_list,_isfinish,_lock_process,__plot_info))
    _window_process.daemon=True
    _window_process.start()



def set_plot_info(line=False,xlog=False,ylog=False,renew_interval=1,flowwidth=0):
    if __state!=State.READY and __state!=State.START:
        __logger.warning(sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    if type(line) is not bool:
        raise util.create_error(sys._getframe().f_code.co_name+": lineの値はTrueかFalseです",__logger)
    if type(xlog) is not bool or type(ylog) is not bool:
        raise util.create_error(sys._getframe().f_code.co_name+": xlog,ylogの値はTrueかFalseです",__logger)
    if type(flowwidth) is not float and type(flowwidth) is not int:
        raise util.create_error(sys._getframe().f_code.co_name+": flowwidthの型はintかfloatです",__logger)
    if flowwidth<0:
        raise util.create_error(sys._getframe().f_code.co_name+": flowwidthの値は0以上にする必要があります",__logger)
    if type(renew_interval) is not float and type(renew_interval) is not int:
        raise util.create_error(sys._getframe().f_code.co_name+": renew_intervalの型はintかfloatです",__logger)
    if renew_interval<0:
        raise util.create_error(sys._getframe().f_code.co_name+": renew_intervalの型は0以上にする必要があります",__logger)

    global __plot_info
    __plot_info={"line":line,"xlog":xlog,"ylog":ylog,"renew_interval":renew_interval,"flowwidth":flowwidth}



def save_data(data):#データ保存
    if __state!=State.UPDATE and __state!=State.END:
        __logger.warning(sys._getframe().f_code.co_name+"はupdateもしくはend関数内で用いてください")
    
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
        __logger.warning(sys._getframe().f_code.co_name+"はstartもしくはupdate関数内で用いてください")
    data=(x,y,color)
    _lock_process.acquire() #   ロックをかけて別プロセスからアクセスできないようにする
    _share_list.append(data)# プロセス間で共有するリストにデータを追加
    _lock_process.release()#ロック解除


def _copy_prefilename():
    path=_tempdir+"\\prefilename"
    if os.path.isfile(path):
        with open(path,mode="r",encoding=util.get_encode_type(path)) as f:
            prefilename=f.read()
            pyperclip.copy(prefilename)

def _set_filename(filename):
    path=_tempdir+"\\prefilename"
    with open(path,mode="w",encoding="utf-8") as f:
        f.write(filename)

def repeat_measurement(closewindow=True):
    global __repeat,__closewindow_repeat
    __repeat=True
    __closewindow_repeat=closewindow


def _do_repeat(start,update,end,on_command,bunkatsu):
    global __repeat
    if __closewindow_repeat:
        _window_process.terminate()
    print("next measurement start...")
    __repeat=False
    _measure_start(start,update,end,on_command,bunkatsu)

def _input_filename():
    _copy_prefilename()
    _filename,_datelabel,_filename_withoutdate=inp.get_filename()
    _set_filename(_filename_withoutdate)
    return _filename