from pathlib import Path

TEMPDIR = None  # ユーザーTEMPフォルダーのパス
DATADIR = None  # ユーザーDATAフォルダーのパス
MACRODIR = None  # ユーザーMACROフォルダーのパス


# GPyMフォルダーのパス
GPYM_HOMEDIR = Path.cwd()

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
