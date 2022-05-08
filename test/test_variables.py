from pathlib import Path

from scripts import variables

cwd = Path.cwd()


def test_gpym_home():
    assert variables.GPYM_HOMEDIR == cwd


def test_shared_tempdir():
    temp = cwd / "temp"

    assert variables.SHARED_TEMPDIR == temp


def test_shared_settingsdir():
    settings = cwd / "shared_settings"

    assert variables.SHARED_SETTINGSDIR == settings


def test_shared_scriptsdir():
    assert variables.SHARED_SCRIPTSDIR == cwd / "scripts"


def test_shared_logdir():
    log = cwd / "log"

    assert variables.SHARED_LOGDIR == log
