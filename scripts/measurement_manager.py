import math
import msvcrt
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from ctypes import Union
from logging import getLogger
from multiprocessing import Lock, Manager, Process, Value
from typing import Any, Optional, Union

import matplotlib.pyplot as plt
import pyperclip
from chardet.universaldetector import UniversalDetector
from scipy import interpolate

import calibration as calib
import inputModule as inp
import utility as util
import variables as vars
from log import inputlog, printlog
from measurement_manager_support import (
    CommandReceiver,
    FileManager,
    MeasurementState,
    MeasurementStep,
    PlotAgency,
)
from utility import GPyMException

"""
基本的にアンダーバー(_)が先頭についている関数､変数は外部からアクセスすることを想定していません. どうしてもという場合にだけアクセスしてください

アンダーバー2つ(__)が先頭についている関数､変数ははマンダリングされており､アンダーバー1つのもの以上に外部からアクセスしにくくしています(やろうとすればできる)
"""


__logger = getLogger(__name__)


def start_macro(macro):
    global _measurement_manager
    _measurement_manager = MeasurementManager(macro)
    _measurement_manager.measure_start()


def finish():
    _measurement_manager.state.is_measuring = False


def set_file_name(filename):
    _measurement_manager.file_manager.filename = filename


def set_calibration(filepath_calib=None):
    """
    この関数は非推奨です。calibration.pyを作ったのでそちらをから呼んでください
    プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み
    """
    global calibration_manager
    calibration_manager = calib.TMRCalibrationManager()
    if filepath_calib == None:
        calibration_manager.set_shared_calib_file()
    else:
        calibration_manager.set_own_calib_file(filepath_calib)


def calibration(x):
    """
    この関数は非推奨です。calibration.pyを作ったのでそちらをから呼んでください
    プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す
    """
    global calibration_manager
    return calibration_manager.calibration(x)


def set_label(label):
    if _measurement_manager.state.current_step != MeasurementStep.START:
        __logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.file_manager.write(label)


def write_file(text: str):
    _measurement_manager.file_manager.write(text)


def set_plot_info(
    line=False, xlog=False, ylog=False, renew_interval=1, legend=False, flowwidth=0
):  # プロット情報の入力
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

    if (
        _measurement_manager.state.current_step != MeasurementStep.READY
        and _measurement_manager.state.current_step != MeasurementStep.START
    ):
        __logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.plot_agency.set_plot_info(
        line=line,
        xlog=xlog,
        ylog=ylog,
        renew_interval=renew_interval,
        legend=legend,
        flowwidth=flowwidth,
    )


def save_data(*data):  # データ保存
    """
    引数のデータをファイルに書き込む.
    この関数が呼ばれるごとに書き込みの反映( __savefile.flush)をおこなっているので途中で測定が落ちてもそれまでのデータは残るようになっている.

    stringの引数にも対応しているので､測定のデータは測定マクロ側でstringで保持しておいて最後にまとめて書き込むことも可能.

    Parameter
    __________________________

    data : tuple or string
        書き込むデータ

    """
    if (
        _measurement_manager.state.current_step != MeasurementStep.UPDATE
        and _measurement_manager.state.current_step != MeasurementStep.END
    ):
        __logger.warning(sys._getframe().f_code.co_name + "はupdateもしくはend関数内で用いてください")
    _measurement_manager.file_manager.save(*data)


def plot_data(x, y, label="default"):  # データをグラフにプロット
    plot(x, y, label)


def plot(x, y, label="default"):
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

    if _measurement_manager.state.current_step != MeasurementStep.UPDATE:
        __logger.warning(sys._getframe().f_code.co_name + "はstartもしくはupdate関数内で用いてください")

    if _measurement_manager.state.is_measuring:
        _measurement_manager.plot_agency.plot(x, y, label)


def no_plot():
    if _measurement_manager.state.current_step != MeasurementStep.START:
        __logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.plot_agency.not_run_plot_window()


class MeasurementManager:

    file_manager = None
    plot_agency = None
    command_receiver = None
    state = MeasurementState()

    def __init__(self, macro) -> None:
        self.macro = macro
        self.file_manager = FileManager()
        self.plot_agency = PlotAgency()
        self.command_receiver = CommandReceiver(self.state)

    def measure_start(self):
        """
        測定のメインとなる関数. 測定マクロに書かれた各関数はMAIN.pyによってここに渡されて
        ここでそれぞれの関数を適切なタイミングで呼んでいる

        """

        self.state.current_step = MeasurementStep.READY

        while msvcrt.kbhit():  # 既に入っている入力は消す
            msvcrt.getwch()

        self.state.current_step = MeasurementStep.START

        if self.macro.start is not None:
            self.macro.start()

        self.file_manager.create_file(
            do_make_folder=(self.macro.bunkatsu is not None),
        )  # ファイル作成

        self.plot_agency.run_plot_window()  # グラフウィンドウの立ち上げ

        while msvcrt.kbhit():  # 既に入っている入力は消す
            msvcrt.getwch()

        if self.macro.on_command is not None:
            self.command_receiver.initialize()

        printlog("measuring start...")
        self.state.current_step = MeasurementStep.UPDATE

        self.state.is_measuring = True
        while True:  # 測定終了までupdateを回す
            if not self.state.is_measuring:
                break
            command = self.command_receiver.get_command()
            if command is None:
                flag = self.macro.update()
                if flag == False:
                    self.state.is_measuring = False
            else:
                self.macro.on_command(command)  # コマンドが入っていればコマンドを呼ぶ

            if self.plot_agency.is_plot_window_forced_terminated():
                self.state.is_measuring = False

        self.plot_agency.stop_renew_plot_window()

        printlog("measurement has finished...")

        if self.macro.end is not None:
            self.state.current_step = MeasurementStep.END
            self.macro.end()

        self.file_manager.close()

        self.state.current_step = MeasurementStep.AFTER
        if self.macro.bunkatsu is not None:
            self.macro.bunkatsu(self.file_manager.filepath)

        if self.macro.after is not None:
            self.macro.after(self.file_manager.filepath)

        self.end()

    def end(self):
        """
        終了処理. コンソールからの終了と､グラフウィンドウを閉じたときの終了の2つを実行できるようにスレッドを用いる
        """

        def wait_enter():  # コンソール側の終了
            nonlocal endflag, windowclose  # nonlocalを使うとクロージャーになる
            inputlog("enter and close window...")  # エンターを押したら次へ進める
            endflag = True
            windowclose = True

        def wait_closewindow():  # グラフウィンドウからの終了
            nonlocal endflag
            while True:
                # print(self.plot_agency.is_plot_window_alive())
                if not self.plot_agency.is_plot_window_alive():
                    break
                time.sleep(0.2)
            endflag = True

        endflag = False
        windowclose = False

        thread1 = threading.Thread(target=wait_closewindow)
        thread1.setDaemon(True)
        thread1.start()

        time.sleep(0.1)

        endflag = (
            False  # 既にグラフが消えていた場合はwait_enterを終了処理とする. それ以外の場合はwait_closewindowも終了処理とする
        )

        thread2 = threading.Thread(target=wait_enter)
        thread2.setDaemon(True)
        thread2.start()

        while True:
            if endflag:
                if not windowclose:
                    self.plot_agency.close()
                break
            time.sleep(0.05)
