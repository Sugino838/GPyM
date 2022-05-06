import datetime
import os
import sys
import tkinter.filedialog as tkfd
from pathlib import Path
from tkinter import Tk

import utilityModule as util
from utilityModule import inputlog, printlog


def get_filename(text="file name is > "):
    """
    出力ファイル名を取得

    Returns
    _____________
    filename: string
        出力ファイル名(入力した文字列に日時を追加したものを返す)
    """

    ngwords = ["\\", "/", "?", '"', "<", ">", "|", ":", "*"]  # ファイルに使えない文字
    wordok = False
    while not wordok:

        filename = inputlog(text)
        for ng in ngwords:
            if ng in filename:
                printlog("WARNING : 以下の文字列はファイル名に使えません. 入力し直してください")
                for w in ngwords:
                    print(w, end="")
                print("")
                break
        else:
            wordok = True

    # 半角スペース,全角スペース,タブは削除
    filename = filename.replace(" ", "")
    filename = filename.replace("\u3000", "")
    filename = filename.replace("\t", "")

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
    fullfilename = datelabel + "_" + filename
    return fullfilename, datelabel, filename


def read_defdir(dirpath=None, filename=None):

    """
    定義ファイルからデータの保存先ディレクトリを取得

    Returns
    _____________
    datadir: string
        データの保存先ディレクトリ
    """

    tk = Tk()
    typ = [("定義ファイル", "*.def")]
    defpath = tkfd.askopenfilename(
        filetypes=typ, title="定義ファイルを選んでください", initialdir=dirpath, initialfile=filename
    )  # ファイルダイアログでファイルを取得
    fileobj = open(defpath, "r", encoding=util.get_encode_type(defpath))  # ファイルの読み込み

    tk.destroy()  # これとtk=Tk()がないと謎のウィンドウが残って邪魔になる

    printlog("define file : " + os.path.basename(defpath))

    datadir = None
    macrodir = None
    tempdir = None
    # ファイルの中身を1行ずつ見ていく
    while True:
        line = fileobj.readline()  # ファイルから1行取得
        if line:
            line = "".join(line.split())  # スペース･改行文字の削除
            line = line.rstrip("\\")  # パスの最後尾に"\"があれば削除
            if "DATADIR=" in line:
                datadir = line[8:]  # "DATADIR="の後ろの文字列を取得
            if "TMPDIR=" in line:
                tempdir = line[7:]
            if "MACRODIR=" in line:
                macrodir = line[9:]

        else:  # 最後の行までいったらbreak
            break

    if datadir == None:
        # 最後まで見てDATADIRが無ければエラー表示
        input("ERROR : 定義ファイルにDATADIRの定義がありません")
        sys.exit()
    else:

        if ":" not in datadir:  # 相対パスなら定義ファイルからの絶対パスに変換
            datadir = os.path.dirname(defpath) + "/" + datadir

        if not os.path.isdir(datadir):  # データフォルダが存在しなければエラー
            input("定義ファイルERROR : " + datadir + "は存在しないフォルダですがDATADIRとして設定されています")
            sys.exit()

    if tempdir == None:
        # 最後まで見てTEMPDIRが無ければエラー表示
        input("ERROR : 定義ファイルにTMPDIRの定義がありません")
        sys.exit()
    else:

        if ":" not in tempdir:  # 相対パスなら定義ファイルからの絶対パスに変換
            tempdir = os.path.dirname(defpath) + "/" + tempdir

        if not os.path.isdir(tempdir):  # データフォルダが存在しなければエラー
            input("定義ファイルERROR : " + tempdir + "は存在しないフォルダですがTMPDIRとして設定されています")
            sys.exit()

    if macrodir == None:
        print("warning:you can set MACRODIR in your define file")
    else:
        if ":" not in macrodir:  # 相対パスなら定義ファイルからの絶対パスに変換
            macrodir = os.path.dirname(defpath) + "/" + macrodir

        if not os.path.isdir(macrodir):  # マクロフォルダが存在しなければ警告
            print("定義ファイルWARING : " + macrodir + "は存在しないフォルダですがMACRODIRとして設定されています")
            macrodir = None

    return defpath, datadir, macrodir, tempdir  # MACRODIRは定義されてなくても通す


def ask_open_filename(filetypes=None, title=None, initialdir=None, initialfile=None):
    tk = Tk()

    # ファイルダイアログでファイルを取得
    path = tkfd.askopenfilename(
        filetypes=filetypes,
        title=title,
        initialdir=initialdir,
        initialfile=initialfile,
    )

    # これとtk=Tk()がないと謎のウィンドウが残って邪魔になる
    tk.destroy()

    return Path(path).absolute()


if __name__ == "__main__":
    print(input_num("input>"))
