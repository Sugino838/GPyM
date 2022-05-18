import json
import logging
from datetime import datetime
from logging import INFO, Formatter, Logger, config, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

import variables as vars
from utility import MyException

logger = getLogger(__name__)


def log(text: str):
    logger.info(text)


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
