"""ログ出力関係"""
import json
from datetime import datetime
from logging import INFO, Formatter, config, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

import variables

logger = getLogger(__name__)


def log(text: str):
    """ユーザー用に簡易ログ出力を提供"""
    logger.info(text)


def setlog():
    """ログファイルのセット"""
    with open(
        f"{variables.SHARED_SCRIPTSDIR}/log_config.json", "r", encoding="utf-8"
    ) as f:
        conf = json.load(f)

        now = datetime.now()

        # 月ごとに新しいファイルにログを書き出す
        conf["handlers"]["sharedFileHandler"]["filename"] = str(
            variables.SHARED_LOGDIR / f"{now.year}-{now.month}.log"
        )

        config.dictConfig(conf)


def set_user_log(path: str):
    """ユーザーフォルダ内にもログファイル書き出し"""
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
