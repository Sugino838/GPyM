import os
from logging import getLogger
from pathlib import Path

import variables as vars
from inputModule import ask_open_filename
from utility import MyException, get_encode_type

logger = getLogger(__name__)


def get_deffile():
    # 前回の定義ファルのパスが保存されているファイル
    path_deffilepath = vars.SHARED_TEMPDIR / "deffilepath"
    path_deffilepath.touch()

    # 前回の定義ファイルのフォルダを開いて定義ファイル選択画面へ
    predefdir = None
    predeffilename = None
    predefpath = Path(path_deffilepath.read_text(encoding="utf-8"))
    if predefpath.is_file():
        predefdir = str(predefpath.parent)
        predeffilename = predefpath.name

    print("定義ファイル選択...")
    defpath = ask_open_filename(
        filetypes=[("定義ファイル", "*.def")],
        title="定義ファイルを選んでください",
        initialdir=predefdir,
        initialfile=predeffilename,
    )

    if defpath.is_file():
        # 今回の定義ファイルのパスを保存
        path_deffilepath.write_text(str(defpath), encoding="utf-8")

    return defpath


def read_deffile():
    """定義ファイルを読み込んで各フォルダのパスを取得"""
    path_deffile = get_deffile()
    logger.info(f"define file: {path_deffile.stem}")

    datadir = None
    macrodir = None
    tempdir = None

    with path_deffile.open(mode="r", encoding=get_encode_type(path_deffile)) as f:
        # ファイルの中身を1行ずつ見ていく
        for l in f:
            # スペース･改行文字の削除
            l = "".join(l.split())
            if l.startswith("DATADIR="):
                # "DATADIR="の後ろの文字列を取得
                datadir = Path(l[8:])
            elif l.startswith("TMPDIR="):
                tempdir = Path(l[7:])
            elif l.startswith("MACRODIR="):
                macrodir = Path(l[9:])

    # 最後まで見てDATADIRが無ければエラー表示
    if datadir == None:
        raise MyException("定義ファイルにDATADIRの定義がありません")
    # 相対パスなら定義ファイルからの絶対パスに変換
    if not datadir.is_absolute():
        datadir = path_deffile.parent / datadir
    # データフォルダが存在しなければエラー
    if not datadir.is_dir():
        raise MyException(f"{datadir}は定義ファイルに設定されていますが存在しません")

    if tempdir == None:
        raise MyException("定義ファイルにTMPDIRの定義がありません")
    if not tempdir.is_absolute():
        tempdir = path_deffile.parent / tempdir
    if not tempdir.is_dir():
        raise MyException(f"{tempdir}は定義ファイルに設定されていますが存在しません")

    if macrodir == None:
        logger.warning("you can set MACRODIR in your define file")
    else:
        if not macrodir.is_absolute():
            macrodir = path_deffile.parent / macrodir
        if not macrodir.is_dir():
            logger.warning(f"{macrodir}は定義ファイルに設定されていますが存在しません")
            macrodir = None

    # TODO (sakakibara): Use pathlib
    vars.DATADIR = str(datadir)
    vars.TEMPDIR = str(tempdir)
    vars.MACRODIR = str(macrodir)
