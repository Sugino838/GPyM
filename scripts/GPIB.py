from logging import getLogger

import pyvisa

from utility import MyException

logger = getLogger(__name__)


class GPIBError(MyException):
    """GPIB関係のえらー"""


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
    elif type(address) is not str:
        raise GPIBError("get_instrumentの引数はintかstrでなければなりません")

    try:
        resource_manager = pyvisa.ResourceManager()
    except ValueError as e:
        raise GPIBError("VISAがPCにインストールされていない可能性があります。 NIVISAをインストールしてください") from e
    except Exception as e:  # エラーの種類に応じて場合分け
        raise GPIBError("予期せぬエラーが発生しました") from e

    try:
        # 機器にアクセス. GPIBがつながってないとここでエラーが出る
        inst = resource_manager.open_resource(address)
    except pyvisa.errors.VisaIOError as e:  # エラーが出たらここを実行
        raise GPIBError("GPIBケーブルが抜けている可能性があります") from e
    except Exception as e:  # エラーの種類に応じて場合分け
        raise GPIBError("予期せぬエラーが発生しました") from e

    try:
        # IDNコマンドで機器と通信. GPIB番号に機器がないとここでエラー
        inst.query("*IDN?")
    except pyvisa.errors.VisaIOError as e:
        raise GPIBError(
            address + "が'IDN?'コマンドに応答しません. 設定されているGPIBの番号が間違っている可能性があります"
        ) from e
    except Exception as e:
        raise GPIBError("予期せぬエラーが発生しました") from e

    # 問題が無ければinstを返す
    return inst
