from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from logging import getLogger
from pathlib import Path

import variables as vars
from inputModule import ask_open_filename
from utility import GPyMException

logger = getLogger(__name__)


class MacroError(GPyMException):
    pass


def get_macropath():
    # 前回のマクロ名が保存されたファイルのパス
    path_premacroname = vars.SHARED_TEMPDIR / "premacroname"
    path_premacroname.touch()

    premacroname = path_premacroname.read_text(encoding="utf-8")

    # gpymは勝手に作った拡張子
    macropath = ask_open_filename(
        filetypes=[("pythonファイル", "*.py *.gpym")],
        title="マクロを選択してください",
        initialdir=vars.MACRODIR,
        initialfile=premacroname,
    )

    macrodir = str(macropath.parent)
    macroname = macropath.stem

    path_premacroname.write_text(macropath.name, encoding="utf-8")
    logger.info(f"macro: {macropath.name}")

    return macropath, macroname, macrodir


def get_macro(macropath: Path):
    """パスから各種関数を読み込み"""
    macroname = macropath.stem

    # importlibを使って動的にpythonファイルを読み込む
    spec = spec_from_loader(macroname, SourceFileLoader(macroname, str(macropath)))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    # 測定マクロに必要な関数と引数が含まれているか確認
    UNDIFINE_ERROR = False
    UNDIFINE_WARNING = []
    if not hasattr(target, "start"):
        target.start = None
        UNDIFINE_WARNING.append("start")
    elif target.start.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".startには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "update"):
        logger.error(target.__name__ + ".pyの中でupdateを定義する必要があります")
        UNDIFINE_ERROR = True
    elif target.update.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".updateには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "end"):
        target.end = None
        UNDIFINE_WARNING.append("end")
    elif target.end.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".endには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "on_command"):
        target.on_command = None
        UNDIFINE_WARNING.append("on_command")
    elif target.on_command.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".on_commandには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "bunkatsu"):
        target.bunkatsu = None
        UNDIFINE_WARNING.append("bunkatsu")
    elif target.bunkatsu.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".bunkatsuには引数filepathだけを設定しなければいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "after"):
        target.after = None
        UNDIFINE_WARNING.append("after")
    elif target.after.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".afterには引数filepathだけを設定しなければいけません")
        UNDIFINE_ERROR = True

    if len(UNDIFINE_WARNING) > 0:
        logger.info("UNDEFINED FUNCTION: " + ", ".join(UNDIFINE_WARNING))

    if UNDIFINE_ERROR:
        raise MacroError("macroの関数定義が正しくありません")

    return target


def get_macro_bunkatsu(macroPath: Path):
    macroname = macroPath.stem
    spec = spec_from_loader(macroname, SourceFileLoader(macroname, str(macroPath)))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    if not hasattr(target, "bunkatsu"):
        raise MacroError(f"{target.__name__}.pyにはbunkatsu関数を定義する必要があります")
    elif target.bunkatsu.__code__.co_argcount != 1:
        raise MacroError(f"{target.__name__}.bunkatsuには1つの引数が必要です")

    return target
