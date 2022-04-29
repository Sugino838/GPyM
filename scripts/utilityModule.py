import json
import logging
from datetime import datetime
from logging import Formatter, Logger, config, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from chardet.universaldetector import UniversalDetector

with open("./log_config.json", "r") as f:
    conf = json.load(f)

    # 月ごとに新しいファイルにログを書き出す
    now = datetime.now()
    filename = Path.home() / "GPyM" / "log" / f"{now.year}-{now.month}.log"
    conf["handlers"]["fileHandler"]["filename"] = str(filename)

    config.dictConfig(conf)


# テキストファイルの文字コードを判別する. ほぼコピペ
def get_encode_type(path: str) -> str:
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


# TODO (sakakibara): 将来的に消す
# ロガーの作成
def mklogger(logname: str):
    return getLogger(logname)


class GPyMException(Exception):
    pass


# TODO (sakakibara): 将来的に消す
def create_error(msg: str, logger: Logger, e=None):
    if e is not None:
        logger.exception(e)
    else:
        logger.error(msg, stacklevel=2)

    input()

    # エラーが既に発生している場合は何も返さないことで現在発生しているエラーをログに出せる
    if e is not None:
        return
    else:
        return GPyMException(msg)


def set_LOG(path: str):
    """
    root loggerに新しくFileHandlerをついかする
    """
    handler = RotatingFileHandler(filename=path, encoding="utf-8", maxBytes=1024 * 100)
    fmt = Formatter(
        "[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s"
    )
    handler.setFormatter(fmt)
    logging.getLogger().addHandler(handler)


# TODO (sakakibara): 将来的に消す
def printlog(msg: str, isprint=True):
    if isprint:
        print(msg)
    logging.info(msg)


# TODO (sakakibara): 将来的に消す
def inputlog(ask=""):
    ans = input(ask)
    logging.info(f"{ask}: {ans}")
    return ans


# TODO (sakakibara): 将来的に消す
def cut_LOG():
    pass


# TODO (sakakibara): 将来的に消す
def output_ErrorLog(_errorlogpath, e: Exception):
    logging.exception(e)
