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
import IOModule as io

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

is_finish=False

def _measure_start(macro):
    """
    測定のメインとなる関数. 測定マクロに書かれた各関数はMAIN.pyによってここに渡されて
    ここでそれぞれの関数を適切なタイミングで呼んでいる

    """
    global _file_manager,_plot_agency
    _file_manager=io.FileManager()
    _plot_agency=io.PlotAgency()

    global _state
    _state=State.READY

    while msvcrt.kbhit():#既に入っている入力は消す
        msvcrt.getwch()
    
    
    filename = _get_filename()
    _file_manager.create_file(filename=filename,data_label=macro._data_label,is_bunkatsu=(macro.bunkatsu is not None))#ファイル作成
    
    set_plot_info()#start内で呼ばれなかったときのためにここで一回呼んでおく


    if macro.start is not None:
        _state=State.START
        macro.start()

    

    if not __nograph:
        _plot_agency.run_plot_window()#グラフウィンドウの立ち上げ

    
    while msvcrt.kbhit():#既に入っている入力は消す
        msvcrt.getwch()

    command_receiver=io.CommandReceiver()
    if macro.on_command is not None:
        command_receiver.initialize()

    printlog("measuring start...")
    _state=State.UPDATE
    global is_finish
    while True:#測定終了までupdateを回す
        if is_finish:
            break
        command=command_receiver.get_command()
        if command is None:
            flag=macro.update()
            if flag==False:
                is_finish=True
        else:
            macro.on_command(command) #コマンドが入っていればコマンドを呼ぶ

    command_receiver.close()
    _plot_agency.stop_renew_plot_window()

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
    global is_finish
    is_finish=True
    

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
        while True:
            #print(_plot_agency.is_plot_window_alive())
            if not _plot_agency.is_plot_window_alive():
                break
            time.sleep(0.2)
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
                _plot_agency.close()
            break
        time.sleep(0.05)




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
    _plot_agency.set_plot_info(line=line,xlog=xlog,ylog=ylog,renew_interval=renew_interval,legend=legend,flowwidth=flowwidth)



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
    
def write_file(text):
    _file_manager.write(text)


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
    _plot_agency.plot(x,y,label)


def _get_filename():#ファイル名入力
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

    _copy_prefilename()
    filename,_datelabel,filename_withoutdate=inp.get_filename()
    _set_filename(filename_withoutdate)
    return filename

def no_plot():
    if _state!=State.START:
        __logger.warning(sys._getframe().f_code.co_name+"はstart関数内で用いてください")
    _plot_agency.not_run_plot_window()