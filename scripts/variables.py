"""共有度の高い変数を置いておく"""
from pathlib import Path

TEMPDIR = None  # ユーザーTEMPフォルダーのパス
DATADIR = None  # ユーザーDATAフォルダーのパス
MACRODIR = None  # ユーザーMACROフォルダーのパス
GPYM_HOMEDIR = None
SHARED_LOGDIR = None
SHARED_SCRIPTSDIR = None
SHARED_SETTINGSDIR = None
SHARED_TEMPDIR = None


def init(home: Path):
    """変数の初期化"""
    global GPYM_HOMEDIR, SHARED_LOGDIR, SHARED_SCRIPTSDIR, SHARED_TEMPDIR, SHARED_SETTINGSDIR
    # GPyMフォルダーのパス
    GPYM_HOMEDIR = home

    # 共有TEMPフォルダーのパス
    SHARED_TEMPDIR = GPYM_HOMEDIR / "temp"
    if not SHARED_TEMPDIR.is_dir():
        SHARED_TEMPDIR.mkdir()

    # 共有設定フォルダのパス
    SHARED_SETTINGSDIR = GPYM_HOMEDIR / "shared_settings"
    if not SHARED_SETTINGSDIR.is_dir():
        SHARED_SETTINGSDIR.mkdir()

    # scriptsフォルダーのパス
    SHARED_SCRIPTSDIR = GPYM_HOMEDIR / "scripts"

    # logフォルダーのパス
    SHARED_LOGDIR = GPYM_HOMEDIR / "log"
    if not SHARED_LOGDIR.is_dir():
        SHARED_LOGDIR.mkdir()
