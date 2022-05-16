import ctypes
import importlib
import os
import sys
import tkinter.filedialog as tkfd
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from tkinter import Tk

import inputModule as inp
import measurementManager as mm
import utility as util

#簡易編集モードをOFFにするためのおまじない
kernel32 = ctypes.windll.kernel32
mode=0xFDB7 #簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)

logger=util.mklogger(__name__)

def main():

    tk = Tk()
    print("分割マクロ選択...")
    typ = [('pythonファイル','*.py *.gpym')] 
    macroPath=tkfd.askopenfilename(filetypes = typ,title="分割マクロを選択してください") #ファイルダイアログでファイルを取得 

    macrodir,macroname=os.path.split(macroPath)
    macroname=os.path.splitext(macroname)[0]
    os.chdir(macrodir)
    print("macro : "+macroname)


    def hoge(address):
        return None
    import GPIBModule
    GPIBModule.get_instrument=hoge#GPIBモジュールの関数を書き換えてGPIBがつながって無くてもエラーが出ないようにする
    print("INFO : you can't use GPIB.get_instrument in GPyM_bunkatsu")



    #bunkatsufunc=get_bunkatsu_func(macroPath) #マクロからbunkatsu関数部分だけを抜き出し
     
    #importlibを使って動的にpythonファイルを読み込む
    spec = spec_from_loader(macroname, SourceFileLoader(macroname,macroPath))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)
       

    if not hasattr(target, 'bunkatsu'):
        raise util.create_error(target.__name__+".pyにはbunkatsu関数を定義する必要があります",logger)
    elif target.bunkatsu.__code__.co_argcount!=1:
        raise util.create_error(target.__name__+".bunkatsuには1つの引数が必要です",logger)


    print("分割ファイル選択...")
    typ = [('データファイル','*.txt *dat')] 
    filePath=tkfd.askopenfilename(filetypes = typ,title="分割するファイルを選択してください") #ファイルダイアログでファイルを取得
    tk.destroy() #これとtk=Tk()がないと謎のウィンドウが残って邪魔になる

    
    target.bunkatsu(filePath)
    input()
    








if __name__=="__main__":
    try:
        main()
    except Exception as e: #めんどくさいのでMAIN.pyとちがってエラーログの書き出しはしない
        import traceback
        traceback.print_exc()
        input("__Error__")

