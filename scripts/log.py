import json
import logging
from datetime import datetime
from logging import INFO, Formatter, Logger, config, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

import variables as vars
from utility import GPyMException

__logger = getLogger(__name__)


def log(text: str):
    __logger.info(text)


def setlog():
    with open(f"{vars.SHARED_SCRIPTSDIR}/log_config.json", "r") as f:
        conf = json.load(f)

        now = datetime.now()

        # 月ごとに新しいファイルにログを書き出す
        conf["handlers"]["sharedFileHandler"]["filename"] = str(
            vars.SHARED_LOGDIR / f"{now.year}-{now.month}.log"
        )

        config.dictConfig(conf)


def set_user_log(path: str):
    path = Path(path) / "log.txt"
    handler = RotatingFileHandler(
        filename=path,
        encoding="utf-8",
        maxBytes=1024 * 100,
    )
    fmt = Formatter(
        "[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s"
    )

    handler.setLevel(INFO)
    handler.setFormatter(fmt)
    getLogger().addHandler(handler)


# TODO (sakakibara): 将来的に消す
# ロガーの作成
def mklogger(logname: str):
    return getLogger(logname)


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
def output_ErrorLog(_errorlogpath, e: Exception):
    logging.exception(e)
