import time
import pyvisa
import sys
import utilityModule

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
        print(utilityModule.get_error_info(e))    
        input("ERROR : GPIBケーブルが抜けている可能性があります")
        print(e)
        raise
    except Exception as e: #エラーの種類に応じて場合分け
        print(utilityModule.get_error_info(e))    
        input("予期せぬエラーが発生しました") 
        print(e)
        raise


    try:
        #IDNコマンドで機器と通信. GPIB番号に機器がないとここでエラー
        idn=inst.query('*IDN?')
    except pyvisa.errors.VisaIOError as e:
        print(utilityModule.get_error_info(e))    
        input(address+"が'IDN?'コマンドに応答しません. 設定されているGPIBの番号が間違っている可能性があります")
        print(e)
        raise
    except Exception as e:
        print(utilityModule.get_error_info(e))    
        input("予期せぬエラーが発生しました") 
        print(e)
        raise

    #問題が無ければinstを返す
    return inst


def get_volt(instrument):
    try:
        volt= instrument.query('VOLT?')
    except Exception as e:
        print(utilityModule.get_error_info(e))    
        input("機器が'VOLT?'に応答しません")
        print(e)
        raise
    
    return volt
    


def command_check(inst,*commands):
    for command in commands:
        try:
            text=inst.query(command)
        except Exception as e:
            input("GPIB"+str(inst.primary_address)+"番への'"+command+"'のコマンドでエラーが発生しました")
            print(utilityModule.get_error_info(e))   
            raise
        


def main():
    get_volt(get_instrument("GPIB0::9::INSTR"))

if __name__ == "__main__":
    main()