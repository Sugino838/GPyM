from pathlib import Path

from pytest import raises
from pytest_mock import MockerFixture
from scripts.define import get_deffile, read_deffile
from scripts.utilityModule import GPyMException

cwd = Path.cwd()


def test_get_deffile(mocker: MockerFixture):
    temp = cwd / "test/deffile/temp"
    defpath = cwd / "test/deffile/valid.def"
    mocker.patch("scripts.define.vars.SHARED_TEMPDIR", temp)
    mocker.patch(
        "scripts.define.ask_open_filename",
        return_value=defpath,
    )

    path = get_deffile()
    assert path == defpath

    deffilepath = temp / "deffilepath"
    assert deffilepath.is_file()
    assert path == Path(deffilepath.read_text(encoding="utf-8"))


class Vars:
    DATADIR = None
    MACRODIR = None
    TEMPDIR = None


class Logger:
    msg = ""

    def error(self, msg: str):
        self.msg = msg

    def warning(self, msg: str):
        self.msg = msg

    def info(self, msg: str):
        pass


class TestReadDeffile:
    deffile = cwd / "test/deffile"

    def test_read_valid_deffile(self, mocker: MockerFixture):
        vars = Vars()

        mocker.patch("scripts.define.vars", vars)
        mocker.patch(
            "scripts.define.get_deffile", return_value=self.deffile / "valid.def"
        )

        read_deffile()

        assert vars.DATADIR == str(self.deffile / "data")
        assert vars.MACRODIR == str(self.deffile / "macro")
        assert vars.TEMPDIR == str(self.deffile / "temp")

    def test_no_data_dir(self, mocker: MockerFixture):
        mocker.patch(
            "scripts.define.get_deffile",
            return_value=self.deffile / "no_datadir.def",
        )

        with raises(GPyMException) as e:
            read_deffile()

        assert str(e.value) == "定義ファイルにDATADIRの定義がありません"

    def test_no_tmp_dir(self, mocker: MockerFixture):
        mocker.patch(
            "scripts.define.get_deffile",
            return_value=self.deffile / "no_tmpdir.def",
        )

        with raises(GPyMException) as e:
            read_deffile()

        assert str(e.value) == "定義ファイルにTMPDIRの定義がありません"

    def test_no_macro_dir(self, mocker: MockerFixture):
        vars = Vars()
        logger = Logger()

        mocker.patch("scripts.define.vars", vars)
        mocker.patch("scripts.define.logger", logger)
        mocker.patch(
            "scripts.define.get_deffile",
            return_value=self.deffile / "no_macrodir.def",
        )

        read_deffile()

        assert logger.msg == "you can set MACRODIR in your define file"
