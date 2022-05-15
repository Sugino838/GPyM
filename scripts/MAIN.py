import ctypes
import os
import sys
import time
from logging import getLogger
from pathlib import Path

import win32api
import win32con

import measurementManager as mm
import variables as vars
from define import read_deffile
from inputModule import ask_open_filename
from macro import get_macro, get_macro_bunkatsu, get_macropath
from utilityModule import set_user_log, setlog

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

    set_user_log(vars.TEMPDIR)

    macropath, _, macrodir = get_macropath()

    macro = get_macro(macropath)

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(macrodir)

    on_forced_termination(lambda: mm.finish())
    # 測定開始
    mm.start(macro)


def on_forced_termination(func):
    def consoleCtrHandler(ctrlType):
        if ctrlType == win32con.CTRL_CLOSE_EVENT:
            func()
            print("terminating measurement...")
            for i in range(100):
                time.sleep(1)

    win32api.SetConsoleCtrlHandler(consoleCtrHandler, True)


def bunkatsu_only():
    print("分割マクロ選択...")
    macroPath = ask_open_filename(
        filetypes=[("pythonファイル", "*.py *.gpym")], title="分割マクロを選択してください"
    )

    os.chdir(str(macroPath.parent))
    print(f"macro: {macroPath.stem}")

    def noop(address):
        return None

    try:
        import GPIBModule

        # GPIBモジュールの関数を書き換えてGPIBがつながって無くてもエラーが出ないようにする
        GPIBModule.get_instrument = noop
        logger.info("you can't use GPIB.get_instrument in GPyM_bunkatsu")
        logger.info(
            "you can't use most of measurementManager's methods in GPyM_bunkatsu"
        )
    except Exception:
        pass

    target = get_macro_bunkatsu(macroPath)

    print("分割ファイル選択...")
    filePath = ask_open_filename(
        filetypes=[("データファイル", "*.txt *dat")], title="分割するファイルを選択してください"
    )

    target.bunkatsu(filePath)
    input()


def setting():
    """変数のセット"""

    vars.init(Path.cwd())

    # 簡易編集モードをOFFにするためのおまじない
    kernel32 = ctypes.windll.kernel32
    # 簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
    mode = 0xFDB7
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)


if __name__ == "__main__":
    setting()
    setlog()

    mode = ""
    args = sys.argv
    if len(args) > 1:
        mode = args[1].upper()

    while True:
        if mode in ["MEAS", "BUNKATSU"]:
            break
        mode = input("mode is > ").upper()

    try:
        if mode == "MEAS":
            main()
        else:
            bunkatsu_only()

    except Exception as e:
        logger.exception(e)

        # コンソールウィンドウが落ちないように入力待ちを入れる
        input("__Error__")
