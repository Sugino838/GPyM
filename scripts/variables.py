"""共有度の高い変数を置いておく"""
from pathlib import Path

from utility import MyException

## TEMPDIR = None  # ユーザーTEMPフォルダーのパス
## DATADIR = None  # ユーザーDATAフォルダーのパス
## MACRODIR = None  # ユーザーMACROフォルダーのパス
## GPYM_HOMEDIR = None
## SHARED_LOGDIR = None
## SHARED_SCRIPTSDIR = None
## SHARED_SETTINGSDIR = None
## SHARED_TEMPDIR = None


def init(home: Path):
    """変数の初期化"""
    # GPyMフォルダーのパス

    SHARED_VARIABLES.set_GPYM_HOMEDIR(home)

    # 共有TEMPフォルダーのパス
    tempdir = home / "temp"
    if not tempdir.is_dir():
        tempdir.mkdir()
    SHARED_VARIABLES.set_TEMPDIR(tempdir)

    # 共有設定フォルダのパス
    settingdir = home / "shared_settings"
    if not settingdir.is_dir():
        settingdir.mkdir()
    SHARED_VARIABLES.set_SETTINGDIR(settingdir)

    # scriptsフォルダーのパス
    SHARED_VARIABLES.set_GPYM_SCRIPTSDIR(home / "scripts")

    # logフォルダーのパス
    logdir = home / "log"
    if not logdir.is_dir():
        logdir.mkdir()
    SHARED_VARIABLES.set_LOGDIR(logdir)


class VariablesError(MyException):
    """変数関係のエラー"""


class PathObject:
    __value = None

    @property
    def value(self) -> Path:
        if self.__value is None:
            raise ValueError("値がまだ入っていません。")
        return self.__value

    @value.setter
    def value(self, value: Path):
        if not isinstance(value, Path):
            raise ValueError("Pathクラスのインスタンスを入力してください")
        self.__value = value


class USER_VARIABLES:
    """各ユーザーがそれぞれ個別に持つ変数"""

    __TEMPDIR = PathObject()

    @classmethod
    @property
    def TEMPDIR(cls) -> Path:
        """プロパティ"""
        return cls.__TEMPDIR.value

    @classmethod
    def set_TEMPDIR(cls, value: Path):
        """セッター"""
        cls.__TEMPDIR.value = value

    __DATADIR = PathObject()

    @classmethod
    @property
    def DATADIR(cls) -> Path:
        return cls.__DATADIR.value

    @classmethod
    def set_DATADIR(cls, value: Path):
        cls.__DATADIR.value = value

    __MACRODIR = PathObject()

    @classmethod
    @property
    def MACRODIR(cls) -> Path:
        return cls.__MACRODIR.value

    @classmethod
    def set_MACRODIR(cls, value: Path):
        cls.__MACRODIR.value = value


class SHARED_VARIABLES:
    """ユーザー間で共通してもつ変数"""

    __SETTINGDIR = PathObject()

    @classmethod
    @property
    def SETTINGDIR(cls) -> Path:
        """プロパティ"""
        return cls.__SETTINGDIR.value

    @classmethod
    def set_SETTINGDIR(cls, value: Path):
        """セッター"""
        cls.__SETTINGDIR.value = value

    __TEMPDIR = PathObject()

    @classmethod
    @property
    def TEMPDIR(cls) -> Path:
        return cls.__TEMPDIR.value

    @classmethod
    def set_TEMPDIR(cls, value: Path):
        cls.__TEMPDIR.value = value

    __GPYM_SCRIPTSDIR = PathObject()

    @classmethod
    @property
    def GPYM_SCRIPTSDIR(cls) -> Path:
        return cls.__GPYM_SCRIPTSDIR.value

    @classmethod
    def set_GPYM_SCRIPTSDIR(cls, value: Path):
        cls.__GPYM_SCRIPTSDIR.value = value

    __LOGDIR = PathObject()

    @classmethod
    @property
    def LOGDIR(cls) -> Path:
        return cls.__LOGDIR.value

    @classmethod
    def set_LOGDIR(cls, value: Path):
        cls.__LOGDIR.value = value

    __GPYM_HOMEDIR = PathObject()

    @classmethod
    @property
    def GPYM_HOMEDIR(cls) -> Path:
        return cls.__GPYM_HOMEDIR.value

    @classmethod
    def set_GPYM_HOMEDIR(cls, value: Path):
        cls.__GPYM_HOMEDIR.value = value
