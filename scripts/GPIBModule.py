import time
import pyvisa
import utilityModule as util


logger=util.mklogger(__name__)

def get_instrument(address):
    """
    指定されたGPIBアドレスに機器が存在するか調べる(種類は調べない. 何かつながっていればOK)

    Parameters
    _________

    address: string
        機器のGPIBアドレス

    Returns
    _________

    inst :型不明
        機器にアクセスできる変数

    """
    rm = pyvisa.ResourceManager()
    try:
        #機器にアクセス. GPIBがつながってないとここでエラーが出る
        inst = rm.open_resource(address) 
    except pyvisa.errors.VisaIOError as e: #エラーが出たらここを実行
        raise util.create_error("GPIBケーブルが抜けている可能性があります",logger)
    except Exception as e: #エラーの種類に応じて場合分け
        raise util.create_error("予期せぬエラーが発生しました",logger,e)

    try:
        #IDNコマンドで機器と通信. GPIB番号に機器がないとここでエラー
        idn=inst.query('*IDN?')
    except pyvisa.errors.VisaIOError as e:
        raise util.create_error(address+"が'IDN?'コマンドに応答しません. 設定されているGPIBの番号が間違っている可能性があります",logger,e)
    except Exception as e:
        raise util.create_error("予期せぬエラーが発生しました",logger,e)

    #問題が無ければinstを返す
    return inst



def command_check(inst,*commands):
    for command in commands:
        try:
            text=inst.query(command)
        except Exception as e:
            raise util.create_error("GPIB"+str(inst.primary_address)+"番への'"+command+"'のコマンドでエラーが発生しました",logger,e)


def main():
    get_volt(get_instrument("GPIB0::9::INSTR"))

if __name__ == "__main__":
    main()