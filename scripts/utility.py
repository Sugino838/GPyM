"""その他諸々の便利関数"""
import tkinter.filedialog as tkfd
from pathlib import Path
from tkinter import Tk

from chardet.universaldetector import UniversalDetector


def get_encode_type(path: str) -> str:
    """テキストファイルの文字コードを判別する. ほぼコピペ"""
    detector = UniversalDetector()
    with open(path, mode="rb") as f:
        for binary in f:
            detector.feed(binary)
            if detector.done:
                break
    detector.close()
    encode_type = detector.result["encoding"]

    # 誤認識を回避するためにutf-8かSHIFT_JISの可能性があればそっちに変更
    confidence = 0
    for prober in detector._charset_probers:
        if prober.charset_name == "utf-8" or prober.charset_name == "SHIFT_JIS":
            if prober.get_confidence() > confidence:
                encode_type = prober.charset_name
                confidence = prober.get_confidence()

    # 日本語が入っていないコードはasciiもutf-8もSHIFT_JISも一緒なので
    # asciiと判断されるがasciiに日本語はないのでutf-8にする
    if encode_type == "ascii":
        encode_type = "utf-8"

    return encode_type


def ask_open_filename(filetypes=None, title=None, initialdir=None, initialfile=None):
    """ファイル選択ダイアログをつくってファイルを返す関数"""
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


class MyException(Exception):
    """測定システムのエラーの親クラス"""

    def __init__(self, message=""):
        super().__init__()
        self.message = message
