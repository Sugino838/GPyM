import ctypes
import os
import sys
import time
from logging import getLogger
from pathlib import Path

import win32api
import win32con

import measurement_manager as mm
import variables
from define import read_deffile
from log import set_user_log, setlog
from macro import get_macro, get_macro_split, get_macropath
from utility import MyException, ask_open_filename

logger = getLogger(__name__)


def main():
    """
    測定マクロを動かすための準備をするスクリプト

    実装としては

    定義ファイル選択
    ↓
    測定マクロ選択
    ↓
    測定マクロ読み込み
    ↓
    必要な関数(updateなど)があるか確認
    ↓
    measurementManager._measure_startを実行

    """
    # 定義ファイル読み取り
    read_deffile()

    # ユーザー側にlogファイル表示
    set_user_log(variables.TEMPDIR)

    # マクロファイルのパスを取得
    macropath, _, macrodir = get_macropath()

    # マクロファイルをマクロに変換
    macro = get_macro(macropath)

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(macrodir)

    # 強制終了時の処理を追加
    on_forced_termination(lambda: mm.finish())

    # 測定開始
    mm.start_macro(macro)


def on_forced_termination(func):
    """
    強制終了時の処理を追加する

    Parameter
    ----------
    func : func
        強制終了時に実行する関数
    """

    def consoleCtrHandler(ctrlType):
        """
        コマンドプロンプト上でイベントが発生したときに呼ばれる関数
        PC側で実行される(こちらから実行はしない)

        Parameter
        ------------
        ctrlType:
            イベントの種類 (バツボタンクリックやcrtl + C など)

        """
        if ctrlType == win32con.CTRL_CLOSE_EVENT:
            func()
            print("terminating measurement...")
            # マクロが終了するまで最大100秒待機
            for i in range(100):
                time.sleep(1)

    # イベントが起きたときにconsoleCtrHandlerを実行するようにPCに命令
    win32api.SetConsoleCtrlHandler(consoleCtrHandler, True)


# 分割関数だけを呼び出し
def split_only():
    print("分割マクロ選択...")
    macroPath = ask_open_filename(
        filetypes=[("pythonファイル", "*.py *.gpym")], title="分割マクロを選択してください"
    )

    os.chdir(str(macroPath.parent))
    print(f"macro: {macroPath.stem}")

    def noop(address):
        return None

    try:
        import GPIB

        # GPIBモジュールの関数を書き換えてGPIBがつながって無くてもエラーが出ないようにする
        GPIB.get_instrument = noop
        logger.info("you can't use GPIB.get_instrument in GPyM_bunkatsu")
        logger.info(
            "you can't use most of measurementManager's methods in GPyM_bunkatsu"
        )
    except Exception:
        pass

    target = get_macro_split(macroPath)

    print("分割ファイル選択...")
    filePath = ask_open_filename(
        filetypes=[("データファイル", "*.txt *dat")], title="分割するファイルを選択してください"
    )

    target.split(filePath)
    # 画面が閉じないようにinputをいれておく
    input()


def setting():
    """変数のセット"""
    variables.init(Path.cwd())

    # 簡易編集モードをOFFにするためのおまじない
    # (簡易編集モードがONだと、画面をクリックしたときに処理が停止してしまう)
    kernel32 = ctypes.windll.kernel32
    # 簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
    mode = 0xFDB7  # 16進数
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)

    setlog()


if __name__ == "__main__":
    setting()

    mode = ""
    args = sys.argv
    if len(args) > 1:
        mode = args[1].upper()

    # 引数によって測定モードか分割モードかを判定
    while True:
        if mode in ["MEAS", "SPLIT"]:
            break
        mode = input("mode is > ").upper()

    # 処理を開始
    try:
        if mode == "MEAS":
            main()
        else:
            split_only()
    # エラーは全てここでキャッチ
    except MyException as e:
        print("*****************Error*****************")
        print(e.message)  # MyExceptionならメッセージだけを表示
        input("*****************Error*****************")
        print("↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓詳細↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
        logger.exception("")
        input("↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑詳細↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑")
    except Exception as e:
        print("*****************Error*****************")
        logger.exception("")
        # コンソールウィンドウが落ちないように入力待ちを入れる
        input("*****************Error*****************")
