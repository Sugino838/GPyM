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
from utilityModule import printlog,inputlog

"""
基本的にアンダーバー(_)が先頭についている関数､変数は外部からアクセスすることを想定していません. どうしてもという場合にだけアクセスしてください

アンダーバー2つ(__)が先頭についている関数､変数ははマンダリングされており､アンダーバー1つのもの以上に外部からアクセスしにくくしています(やろうとすればできる)
"""


class State(Enum):
    READY=auto()
    START=auto()
    UPDATE=auto()
    END=auto()
    BUNKATSU=auto()
    ALLEND=auto()

def _set_variables(datadir,tempdir,file_label,shared_settings_dir):#グローバル変数のセット
    global __datadir,__tempdir,_data_label,__shared_settings_dir
    __datadir=datadir
    __tempdir=tempdir
    _data_label=file_label
    __shared_settings_dir=shared_settings_dir


__logger=util.mklogger(__name__)

__command=None
__repeat=False
__nograph=False

def _measure_start(start,update,end,on_command,bunkatsu):
    """
    測定のメインとなる関数. 測定マクロに書かれた各関数はMAIN.pyによってここに渡されて
    ここでそれぞれの関数を適切なタイミングで呼んでいる

    """
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

    _set_file(bunkatsu)#ファイル作成

    if not __nograph:
        _run_window()#グラフウィンドウの立ち上げ

    
    while msvcrt.kbhit():#既に入っている入力は消す
        msvcrt.getwch()

    if on_command is not None:
        cmthr=threading.Thread(target=_wait_command_input)
        cmthr.setDaemon(True)
        cmthr.start()


    printlog("measuring start...")
    __state=State.UPDATE
    global __command
    while True:#測定終了までupdateを回す
        if __isfinish.value==1:
            break
        if __command is None:
            flag=update()
            if flag==False:__isfinish.value=1
        else:
            on_command(__command) #コマンドが入っていればコマンドを呼ぶ
            __command=None


    printlog("measurement has finished...")

    if end is not None:
        __state=State.END
        end()
    
    __savefile.close()
    
    if bunkatsu is not None:
        __state=State.BUNKATSU
        bunkatsu(__filepath)
    __state=State.ALLEND
    

    if __repeat:
        __do_repeat(start,update,end,on_command,bunkatsu)
    else:
        _end()





def get_tempdir():
    return __tempdir
def get_datadir():
    return __datadir
def get_shared_settings_dir():
    return __shared_settings_dir

def finish():
    __isfinish.value=1
    

def _end():
    """
    終了処理. コンソールからの終了と､グラフウィンドウを閉じたときの終了の2つを実行できるようにスレッドを用いる
    """
    def wait_enter():#コンソール側の終了
        nonlocal endflag,windowclose #nonlocalを使うとクロージャーになる
        inputlog("enter and close window...") #エンターを押したら次へ進める
        endflag=True
        windowclose=True
    def wait_closewindow():#グラフウィンドウからの終了
        nonlocal endflag
        __window_process.join()#_window_processの終了待ち
        endflag=True
    endflag=False
    windowclose=False

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
            if not windowclose: 
                __window_process.terminate()
            break
        time.sleep(0.05)
    


        
def _wait_command_input():#終了コマンドの入力待ち, これは別スレッドで動かす
    while True:
        isf=__isfinish.value
        if msvcrt.kbhit() and isf==0: #入力が入って初めてinputが動くように(inputが動くとその間ループを抜けられないので)
            command=inputlog()
            global __command
            __command=command
            while __command is not None:
                time.sleep(0.1)
        elif isf==1:
            break
        time.sleep(0.1)



    



def set_calibration(filepath_calb=None):#プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み
    """
    キャリブレーションファイルの2列目をx,1列目をyとして線形補間関数を作る.
    基本的に引数は使わない.
    引数が無いときはSHARED_SETTINGSフォルダーにある標準のキャリブレーションファイルを用いる. 

    Parameter
    __________________________

    filepath_calb : string
        キャリブレーションファイルのパス. 基本的にはこの引数はわたさない

    """

    if filepath_calb is not None:
        if not os.path.isfile(filepath_calb):
            raise util.create_error("キャリブレーションファイル"+filepath_calb+"が存在しません. "+os.getcwd()+"で'"+filepath_calb+"'にアクセスしようとしましたが存在しませんでした.",__logger)
    else:
        path=__shared_settings_dir+"/calibration_file"
        if not os.path.isdir(path):
            raise util.create_error(__share_list+" にcalibration_fileフォルダーが存在しません. \n"+__share_list+" にcalibration_fileフォルダーを新規作成した後でフォルダー内にキャリブレーションファイルを置きもう一度実行してください. ",__logger)
        import glob
        files = glob.glob(path+"/*")

        
        if len(files)==0:
            raise util.create_error(path+"内には1つのキャリブレーションファイルを置く必要があります",__logger)
        if len(files)>=2:
            raise util.create_error(path+"内に2つ以上のファイルを置いてはいけません",__logger)
        filepath_calb=files[0]

    
    global __interpolate_func
    with open(filepath_calb,'r',encoding=util.get_encode_type(filepath_calb)) as file:

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

    calibfilename=os.path.split(filepath_calb)[1]
    printlog("calibration : "+filepath_calb)
    global __interpolate_func
    __interpolate_func = interpolate.interp1d(x,y,fill_value='extrapolate') # 線形補間関数定義

    return calibfilename

def calibration(x):
    """
    プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す
    """
    try:
        y=__interpolate_func(x)
    except ValueError as e:
        raise util.create_error("入力されたデータ "+str(x)+" がキャリブレーションファイルのデータ範囲外になっている可能性があります",__logger,e)
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

def _set_file(bunkatsu):#ファイルの作成,準備

    """
    フォルダが無ければエラーを出し､あれば新規でファイルを作り､__savefileに代入
    """

    if not os.path.isdir(__datadir):#フォルダの存在確認
        raise util.create_error(__datadir+"のフォルダにアクセスしようとしましたが､存在しませんでした",__logger)
    

    global __filepath
    if bunkatsu is None:
        __filepath=__datadir+"\\"+ _filename+".txt"
    else:
        nowdatadir=__datadir+"\\"+ _filename
        os.mkdir(nowdatadir)
        __filepath=nowdatadir+"\\"+ _filename+".txt"
        

    
        
    global __savefile
    __savefile = open(__filepath, 'x',encoding="utf-8") #ファイル作成

    file_label=__user_label+_data_label+"\n"
    __savefile.write(file_label) #測定データのラベル書き込み

    __savefile.flush() #書き込みを反映させる





def _run_window():#グラフと終了コマンド待ち処理を走らせる
    """
    GPyMではマルチプロセスを用いて測定プロセスとは別のプロセスでグラフの描画を行う.

    Pythonのマルチプロセスでは必要な値はプロセスの作成時に渡しておかなくてはならないので､(例外あり)
    ここではマルチプロセスの起動と必要な引数の受け渡しを行う.
    """
    manager = Manager() 
    global __share_list,__isfinish,__lock_process
    __share_list=manager.list()#プロセス間で共有できるリスト
    __isfinish=Value("i",0)#測定の終了を判断するためのint
    __lock_process=Lock()#2つのプロセスで同時に同じデータを触らないようにする排他制御のキー
    #グラフ表示は別プロセスで実行する
    global __window_process
    __window_process=Process(target=windowModule.exec,args=(__share_list,__isfinish,__lock_process,__plot_info))
    __window_process.daemon=True#プロセスのデーモン化
    __window_process.start()#マルチプロセス実行



def set_plot_info(line=False,xlog=False,ylog=False,renew_interval=1,legend=False,flowwidth=0):#プロット情報の入力
    """
    グラフ描画プロセスに渡す値はここで設定する.
    __plot_infoが辞書型なのはアンパックして引数に渡すため

    Parameter
    __________________________

    line: bool
        プロットに線を引くかどうか

    xlog,ylog :bool
        対数軸にするかどうか

    renew_interval : float (>0)
        グラフの更新間隔(秒)

    legend : bool
        凡例をつけるか. (凡例の名前はlabelの値)

    flowwidth : float (>0)
        これが0より大きい値のとき. グラフの横軸は固定され､横にプロットが流れるようなグラフになる.

    """

    if __state!=State.READY and __state!=State.START:
        __logger.warning(sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    if type(line) is not bool:
        raise util.create_error(sys._getframe().f_code.co_name+": lineの値はTrueかFalseです",__logger)
    if type(xlog) is not bool or type(ylog) is not bool:
        raise util.create_error(sys._getframe().f_code.co_name+": xlog,ylogの値はTrueかFalseです",__logger)
    if type(legend) is not bool :
        raise util.create_error(sys._getframe().f_code.co_name+": legendの値はTrueかFalseです",__logger)
    if type(flowwidth) is not float and type(flowwidth) is not int:
        raise util.create_error(sys._getframe().f_code.co_name+": flowwidthの型はintかfloatです",__logger)
    if flowwidth<0:
        raise util.create_error(sys._getframe().f_code.co_name+": flowwidthの値は0以上にする必要があります",__logger)
    if type(renew_interval) is not float and type(renew_interval) is not int:
        raise util.create_error(sys._getframe().f_code.co_name+": renew_intervalの型はintかfloatです",__logger)
    if renew_interval<0:
        raise util.create_error(sys._getframe().f_code.co_name+": renew_intervalの型は0以上にする必要があります",__logger)

    global __plot_info
    __plot_info={"line":line,"xlog":xlog,"ylog":ylog,"renew_interval":renew_interval,"legend":legend,"flowwidth":flowwidth}




def save_data(data):#データ保存
    """
    引数のデータをファイルに書き込む. 
    この関数が呼ばれるごとに書き込みの反映( __savefile.flush)をおこなっているので途中で測定が落ちてもそれまでのデータは残るようになっている.

    stringの引数にも対応しているので､測定のデータは測定マクロ側でstringで保持しておいて最後にまとめて書き込むことも可能.

    Parameter
    __________________________

    data : tuple or string
        書き込むデータ

    """

    if __state!=State.UPDATE and __state!=State.END:
        __logger.warning(sys._getframe().f_code.co_name+"はupdateもしくはend関数内で用いてください")
    if type(data) is not str and not isinstance(data, tuple):
        raise util.create_error(sys._getframe().f_code.co_name+": dataはタプル型､もしくはstring型でなければなりません",__logger)

    if type(data) is str:#文字列を入力したときにも一応対応
        __savefile.write(data)#書き込み
    else:
        text=""
        for i in range(len(data)):#タプルの全要素をstringにして並べる
            if i == 0:
                text+=str(data[0])
            else:
                text+=","+str(data[i])
        text+="\n"#末尾に改行記号
        __savefile.write(text)#書き込み
    __savefile.flush()#反映. 
    
    


def plot_data(x,y,label="default"):#データをグラフにプロット
    """
    データをグラフ描画プロセスに渡す. 
    labelが変わると色が変わる
    __share_listは測定プロセスとグラフ描画プロセスの橋渡しとなるリストでバッファーの役割をする


    Parameter
    __________________________

    x,y : float
        プロットのx,y座標

    label : string or float
        プロットの識別ラベル.
        これが同じだと同じ色でプロットしたり､線を引き設定のときは線を引いたりする.

    """

    if __state!=State.UPDATE:
        __logger.warning(sys._getframe().f_code.co_name+"はstartもしくはupdate関数内で用いてください")
    data=(x,y,label)
    __lock_process.acquire() #   ロックをかけて別プロセスからアクセスできないようにする
    __share_list.append(data)# プロセス間で共有するリストにデータを追加
    __lock_process.release()#ロック解除

def repeat_measurement(closewindow=True):#測定の繰り返しを伝える関数
    """
    測定を繰り返す場合はそのたびに呼ぶ.

    Parameter
    __________________________

    closewindow : bool
        各測定の終了でグラフウィンドウを閉じるかどうか.

    """
    global __repeat,__closewindow_repeat
    __repeat=True
    __closewindow_repeat=closewindow


def __do_repeat(start,update,end,on_command,bunkatsu):#実際に測定を繰り返す関数
    global __repeat
    if __closewindow_repeat:
        __window_process.terminate()
    printlog("next measurement start...")
    __repeat=False
    _measure_start(start,update,end,on_command,bunkatsu)


def _copy_prefilename():#前回のファイル名をコピー
    path=__tempdir+"\\prefilename"
    if os.path.isfile(path):
        with open(path,mode="r",encoding=util.get_encode_type(path)) as f:
            prefilename=f.read()
            pyperclip.copy(prefilename)

def _set_filename(filename):#ファイル名をtemodirに保存
    path=__tempdir+"\\prefilename"
    with open(path,mode="w",encoding="utf-8") as f:
        f.write(filename)

def _input_filename():#ファイル名入力
    _copy_prefilename()
    filename,_datelabel,filename_withoutdate=inp.get_filename()
    _set_filename(filename_withoutdate)
    return filename



def graph_window_off():
    global __nograph
    __nograph=True

    manager = Manager()
    global __share_list,__isfinish,__lock_process
    __share_list=manager.list()
    __isfinish=Value("i",0)
    __lock_process=Lock()

    class damy_window_proess():
        def join(self):
            pass
        def terminate(self):
            pass
        def start(self):
            pass

    global __window_process
    __window_process=damy_window_proess()

