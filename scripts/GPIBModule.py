import time
from logging import getLogger

import pyvisa

from utility import MyException

logger = getLogger(__name__)


class GPIBException(MyException):
    pass


def get_instrument(address):
    """
    指定されたGPIBアドレスに機器が存在するか調べる(種類は調べない. 何かつながっていればOK)

    Parameters
    _________

    address: string or int
        機器のGPIBアドレス stringならGPIB0::9::INSTRの形式

    Returns
    _________

    inst :型不明
        機器にアクセスできるインスタンス

    """

    if type(address) is int:
        address = f"GPIB0::{address}::INSTR"

    rm = pyvisa.ResourceManager()
    try:
        # 機器にアクセス. GPIBがつながってないとここでエラーが出る
        inst = rm.open_resource(address)
    except pyvisa.errors.VisaIOError as e:  # エラーが出たらここを実行
        logger.exception("")
        raise GPIBException("GPIBケーブルが抜けている可能性があります")
    except Exception as e:  # エラーの種類に応じて場合分け
        logger.exception("")
        raise GPIBException("予期せぬエラーが発生しました")

    try:
        # IDNコマンドで機器と通信. GPIB番号に機器がないとここでエラー
        idn = inst.query("*IDN?")
    except pyvisa.errors.VisaIOError as e:
        logger.exception("")
        raise GPIBException(
            address + "が'IDN?'コマンドに応答しません. 設定されているGPIBの番号が間違っている可能性があります"
        )
    except Exception as e:
        logger.exception("")
        raise GPIBException("予期せぬエラーが発生しました")

    # 問題が無ければinstを返す
    return inst


def command_check(inst, *commands):
    for command in commands:
        try:
            text = inst.query(command)
        except Exception as e:
            raise GPIBException(
                "GPIB"
                + str(inst.primary_address)
                + "番への'"
                + command
                + "'のコマンドでエラーが発生しました",
                logger,
                e,
            )
