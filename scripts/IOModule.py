import msvcrt
import os
import sys
import threading
import time
from mimetypes import init
from typing import Optional, Union

import utilityModule as util
import variables as vars
from utilityModule import inputlog

__logger = util.mklogger(__name__)


class FileManager:  # ファイルの管理
    """
    ファイルの作成・書き込みを行う

    Attributes
    ------------

    filepath:str
        書き込んだファイルのパス
    filename:str
        ファイル名
    file
        ファイルのインスタンス

    """

    _filepath: str
    _filename: str
    _file = None
    __prewrite = ""
    delimiter = ","

    @property
    def filepath(self):
        return self._filepath

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, new_filename):
        if self.has_fileNG_word(new_filename):
            inputlog("Error : 以下の文字列はファイル名に使えません. 入力し直してください")
            raise Exception("Error : 以下の文字列はファイル名に使えません. 入力し直してください")
        self._filename = self.get_date_text() + "_" + new_filename

    def __init__(self) -> None:
        self._filename = self.get_date_text() + "_"
        pass

    def get_date_text(self) -> str:
        import datetime

        dt_now = datetime.datetime.now()  # 日時取得

        # 日時をゼロ埋めしたりしてからファイル名の先頭につける
        year = str(dt_now.year)

        datelabel = (
            year[2]
            + year[3]
            + str(dt_now.month).zfill(2)
            + str(dt_now.day).zfill(2)
            + "-"
            + str(dt_now.hour).zfill(2)
            + str(dt_now.minute).zfill(2)
            + str(dt_now.second).zfill(2)
        )
        return datelabel

    def create_file(self, do_make_folder: bool) -> None:
        """
        フォルダが無ければエラーを出し､あれば新規でファイルを作り､__savefileに代入
        """

        if not os.path.isdir(vars.DATADIR):  # フォルダの存在確認
            raise util.create_error(
                vars.DATADIR + "のフォルダにアクセスしようとしましたが､存在しませんでした", __logger
            )

        if do_make_folder:
            nowdatadir = vars.DATADIR + "\\" + self._filename
            os.mkdir(nowdatadir)
            self._filepath = nowdatadir + "\\" + self._filename + ".txt"
        else:
            self._filepath = vars.DATADIR + "\\" + self._filename + ".txt"

        self._file = open(self._filepath, "x", encoding="utf-8")  # ファイル作成

        if self.__prewrite != "":
            self._file.write(self.__prewrite)  # 今までに書き込んだ分を入力
            self._file.flush()
            self.__prewrite = ""

    def save(self, *args):

        text = ""

        for data in args:
            if isinstance(data, tuple) or data is list:
                text += self.delimiter.join(map(str, data))
            else:
                text += str(data)
            text += self.delimiter
        text = text[0:-1] + "\n"
        self.write(text)

    def write(self, text: str):
        if self._file == None:
            self.__prewrite += text
        else:
            self._file.write(text)
            self._file.flush()

    def has_fileNG_word(self, text: str) -> bool:
        ngwords = ["\\", "/", "?", '"', "<", ">", "|", ":", "*"]  # ファイルに使えない文字
        for ng in ngwords:
            if ng in text:
                return True
        return False

    def close(self):
        self._file.close()


class CommandReceiver:  # コマンドの入力を受け取るクラス

    """
    コマンドの入力を検知する
    """

    __command: Optional[str] = None
    __isfinish: bool = False

    def initialize(self):
        """
        別スレッドで__command_receive_threadを実行
        """
        cmthr = threading.Thread(target=self.__command_receive_thread)
        cmthr.setDaemon(True)
        cmthr.start()

    def __command_receive_thread(self) -> None:  # 終了コマンドの入力待ち, これは別スレッドで動かす
        while True:
            if (
                msvcrt.kbhit() and not self.__isfinish
            ):  # 入力が入って初めてinputが動くように(inputが動くとその間ループを抜けられないので)
                self.__command = inputlog()
                while self.__command is not None:
                    time.sleep(0.1)
            elif self.__isfinish:
                break
            time.sleep(0.1)

    def get_command(self) -> str:  # 受け取ったコマンドを返す。なければNoneを返す
        command = self.__command
        self.__command = None
        return command

    def close(self):
        self.__isfinish = True


from multiprocessing import Lock, Manager, Process, Value
from typing import List

import windowModule


class PlotAgency:
    def __init__(self) -> None:
        self.set_plot_info()

    share_list: List[tuple]
    is_finish: Value
    process_lock: Lock
    window_process: Process

    def run_plot_window(self):  # グラフと終了コマンド待ち処理を走らせる
        """
        GPyMではマルチプロセスを用いて測定プロセスとは別のプロセスでグラフの描画を行う.

        Pythonのマルチプロセスでは必要な値はプロセスの作成時に渡しておかなくてはならないので､(例外あり)
        ここではマルチプロセスの起動と必要な引数の受け渡しを行う.
        """

        self.share_list = Manager().list()  # プロセス間で共有できるリスト
        self.is_finish = Value("i", 0)  # 測定の終了を判断するためのint
        self.process_lock = Lock()  # 2つのプロセスで同時に同じデータを触らないようにする排他制御のキー
        # グラフ表示は別プロセスで実行する
        self.window_process = Process(
            target=windowModule.exec,
            args=(self.share_list, self.is_finish, self.process_lock, self.plot_info),
        )
        self.window_process.daemon = True  # プロセスのデーモン化
        self.window_process.start()  # マルチプロセス実行

    def set_plot_info(
        self,
        line=False,
        xlog=False,
        ylog=False,
        renew_interval=1,
        legend=False,
        flowwidth=0,
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

        if type(line) is not bool:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": lineの値はTrueかFalseです", __logger
            )
        if type(xlog) is not bool or type(ylog) is not bool:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": xlog,ylogの値はTrueかFalseです", __logger
            )
        if type(legend) is not bool:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": legendの値はTrueかFalseです", __logger
            )
        if type(flowwidth) is not float and type(flowwidth) is not int:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": flowwidthの型はintかfloatです", __logger
            )
        if flowwidth < 0:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": flowwidthの値は0以上にする必要があります", __logger
            )
        if type(renew_interval) is not float and type(renew_interval) is not int:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": renew_intervalの型はintかfloatです",
                __logger,
            )
        if renew_interval < 0:
            raise util.create_error(
                sys._getframe().f_code.co_name + ": renew_intervalの型は0以上にする必要があります",
                __logger,
            )

        self.plot_info = {
            "line": line,
            "xlog": xlog,
            "ylog": ylog,
            "renew_interval": renew_interval,
            "legend": legend,
            "flowwidth": flowwidth,
        }

    def plot(self, x, y, label="default"):
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

        data = (x, y, label)
        self.process_lock.acquire()  #   ロックをかけて別プロセスからアクセスできないようにする
        self.share_list.append(data)  # プロセス間で共有するリストにデータを追加
        self.process_lock.release()  # ロック解除

    def stop_renew_plot_window(self):
        self.is_finish.value = 1

    def close(self):
        self.window_process.terminate()

    def is_plot_window_alive(self) -> bool:
        return self.window_process.is_alive()

    def not_run_plot_window(self):
        def void(*args):
            pass

        def voidbool(*args):
            return False

        self.run_plot_window = void
        self.set_plot_info = void
        self.plot = void
        self.stop_renew_plot_window = void
        self.close = void
        self.is_plot_window_alive = voidbool
