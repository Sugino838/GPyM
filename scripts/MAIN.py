import ctypes
import os
import sys
from logging import getLogger

import measurementManager as mm
import variables as vars
from define import read_deffile
from inputModule import ask_open_filename
from macro import get_macro, get_macro_bunkatsu, get_macropath
from utilityModule import setlog

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

    macropath, _, macrodir = get_macropath()

    macro, data_label = get_macro(macropath)

    mm._set_variables(
        datadir=vars.DATADIR,
        tempdir=vars.MACRODIR,
        file_label=data_label,
        shared_settings_dir=str(vars.SHARED_SETTINGSDIR),
    )

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(macrodir)

    # 測定開始
    mm._measure_start(
        start=macro.start,
        update=macro.update,
        end=macro.end,
        on_command=macro.on_command,
        bunkatsu=macro.bunkatsu,
    )


def bunkatsu_only():
    print("分割マクロ選択...")
    macroPath = ask_open_filename(
        filetypes=[("pythonファイル", "*.py *.gpym")], title="分割マクロを選択してください"
    )

    os.chdir(str(macroPath.parent))
    print(f"macro: {macroPath.stem}")

    def noop(address):
        return None

    import GPIBModule

    # GPIBモジュールの関数を書き換えてGPIBがつながって無くてもエラーが出ないようにする
    GPIBModule.get_instrument = noop
    logger.info("you can't use GPIB.get_instrument in GPyM_bunkatsu")
    logger.info("you can't use most of measurementManager's methods in GPyM_bunkatsu")

    target = get_macro_bunkatsu(macroPath)

    print("分割ファイル選択...")
    filePath = ask_open_filename(
        filetypes=[("データファイル", "*.txt *dat")], title="分割するファイルを選択してください"
    )

    mm._set_variables(
        datadir=None,
        tempdir=None,
        file_label=None,
        shared_settings_dir=vars.SHARED_SETTINGSDIR,
    )
    target.bunkatsu(filePath)
    input()


def setting():
    """変数のセット"""
    setlog()

    # 簡易編集モードをOFFにするためのおまじない
    kernel32 = ctypes.windll.kernel32
    # 簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
    mode = 0xFDB7
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)


if __name__ == "__main__":
    setting()

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
