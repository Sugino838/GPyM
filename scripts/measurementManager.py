from ctypes import Union
import sys
import os
import threading
import math
from typing import Optional
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
import variables as vars
from typing import Any, Union
import calibration as calib


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



__logger=util.mklogger(__name__)

__nograph=False

def _measure_start(macro):
    """
    測定のメインとなる関数. 測定マクロに書かれた各関数はMAIN.pyによってここに渡されて
    ここでそれぞれの関数を適切なタイミングで呼んでいる

    """
    global _file_manager
    _file_manager=FileManager()

    global _state
    _state=State.READY

    while msvcrt.kbhit():#既に入っている入力は消す
        msvcrt.getwch()
    
    
    filename = _input_filename()
    
    
    set_plot_info()#start内で呼ばれなかったときのためにここで一回呼んでおく

    if macro.start is not None:
        _state=State.START
        macro.start()

    _file_manager.create_file(filename=filename,data_label=macro._data_label,is_bunkatsu=(macro.bunkatsu is not None))#ファイル作成

    if not __nograph:
        _run_window()#グラフウィンドウの立ち上げ

    
    while msvcrt.kbhit():#既に入っている入力は消す
        msvcrt.getwch()

    command_receiver=CommandReceiver()
    if macro.on_command is not None:
        command_receiver.initialize()

    printlog("measuring start...")
    _state=State.UPDATE
    while True:#測定終了までupdateを回す
        if __isfinish.value==1:
            break
        command=command_receiver.get_command()
        if command is None:
            flag=macro.update()
            if flag==False:
                __isfinish.value=1
        else:
            macro.on_command(command) #コマンドが入っていればコマンドを呼ぶ

    command_receiver.close()

    printlog("measurement has finished...")

    if macro.end is not None:
        _state=State.END
        macro.end()
    
    _file_manager.close()
    
    if macro.bunkatsu is not None:
        _state=State.BUNKATSU
        macro.bunkatsu(_file_manager.filepath)
    _state=State.ALLEND
    

    _end()







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

class FileManager(): #ファイルの管理

    filepath:str
    filename:str
    file=None
    _user_label=""

    def create_file(self,filename:str,data_label:str,is_bunkatsu:bool)->None:
        self.name=filename
        """
        フォルダが無ければエラーを出し､あれば新規でファイルを作り､__savefileに代入
        """

        if not os.path.isdir(vars.DATADIR):#フォルダの存在確認
            raise util.create_error(vars.DATADIR+"のフォルダにアクセスしようとしましたが､存在しませんでした",__logger)
        

        if is_bunkatsu :
            self.path=vars.DATADIR+"\\"+ filename+".txt"
        else:
            nowdatadir=vars.DATADIR+"\\"+ filename
            os.mkdir(nowdatadir)
            self.path=nowdatadir+"\\"+ filename+".txt"
        

    
        

        self.file = open(self.path, 'x',encoding="utf-8") #ファイル作成

        file_label=self._user_label+data_label+"\n"
        self.file.write(file_label) #測定データのラベル書き込み

        self.file.flush() #書き込みを反映させる

    def save(self,data:Union[str,tuple]):

        if type(data) is not str and not isinstance(data, tuple):
            raise util.create_error(sys._getframe().f_code.co_name+": dataはタプル型､もしくはstring型でなければなりません",__logger)

        if type(data) is str:#文字列を入力したときにも一応対応
            self.file.write(data)#書き込み
        else:
            text=""
            for i in range(len(data)):#タプルの全要素をstringにして並べる
                if i == 0:
                    text+=str(data[0])
                else:
                    text+=","+str(data[i])
            text+="\n"#末尾に改行記号
            self.file.write(text)#書き込み
        self.file.flush()#反映. 

    def set_label(self,label:str)->None:
        if not label[-1]=="\n":#末尾に改行コードがついていなければくっつける
            label+="\n"
        self._user_label=self._user_label+label

    def close(self):
        self.file.close()

class CommandReceiver():#コマンドの入力を受け取るクラス

    __command:Optional[str]=None
    __isfinish:bool=False

            
    def initialize(self):
        cmthr=threading.Thread(target=self.__command_receive_thread)
        cmthr.setDaemon(True)
        cmthr.start()

    def __command_receive_thread(self) -> None:#終了コマンドの入力待ち, これは別スレッドで動かす
        while True:
            if msvcrt.kbhit() and not self.__isfinish: #入力が入って初めてinputが動くように(inputが動くとその間ループを抜けられないので)
                self.__command=inputlog()
                while self.__command is not None:
                    time.sleep(0.1)
            elif self.__isfinish:
                break
            time.sleep(0.1)
        
    def get_command(self) -> str: #受け取ったコマンドを返す。なければNoneを返す
        send=self.__command
        self.__command=None
        return send
    
    def close(self):
        self.__isfinish=True


def set_calibration(filepath_calib=None):
    """
    この関数は非推奨です。calibration.pyを作ったのでそちらをから呼んでください
    プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み
    """
    global calibration
    calibration=calib.TMRCalibration()
    if filepath_calib==None:
        calibration.set_shared_calib_file()
    else:
        calibration.set_own_calib_file(filepath_calib)

def calibration(x):
    """
    この関数は非推奨です。calibration.pyを作ったのでそちらをから呼んでください
    プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す
    """
    global calibration
    return calibration.calibration(x)


def set_label(label):
    if _state!=State.START:
            __logger.warning(sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    global _file_manager
    _file_manager.set_label(label=label)






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

    if _state!=State.READY and _state!=State.START:
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
    if _state!=State.UPDATE and _state!=State.END:
        __logger.warning(sys._getframe().f_code.co_name+"はupdateもしくはend関数内で用いてください")
    global _file_manager
    _file_manager.save(data)
    
    


def plot_data(x,y,label="default"):#データをグラフにプロット
    plot(x,y,label)
    
def plot(x,y,label="default"):
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

    if _state!=State.UPDATE:
        __logger.warning(sys._getframe().f_code.co_name+"はstartもしくはupdate関数内で用いてください")
    data=(x,y,label)
    __lock_process.acquire() #   ロックをかけて別プロセスからアクセスできないようにする
    __share_list.append(data)# プロセス間で共有するリストにデータを追加
    __lock_process.release()#ロック解除





def _copy_prefilename():#前回のファイル名をコピー
    path=vars.TEMPDIR+"\\prefilename"
    if os.path.isfile(path):
        with open(path,mode="r",encoding=util.get_encode_type(path)) as f:
            prefilename=f.read()
            pyperclip.copy(prefilename)

def _set_filename(filename):#ファイル名をtemodirに保存
    path=vars.TEMPDIR+"\\prefilename"
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

