import importlib
import sys
import os
import tkinter.filedialog as tkfd
from tkinter import Tk
import inputModule as inp
import measurementManager as mm
import utilityModule as util

import ctypes

#簡易編集モードをOFFにするためのおまじない
kernel32 = ctypes.windll.kernel32
mode=0xFDB7 #簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)

def main():

    tk = Tk()
    print("分割マクロ選択...")
    typ = [('pythonファイル','*.py')] 
    macroPath=tkfd.askopenfilename(filetypes = typ,title="分割マクロを選択してください") #ファイルダイアログでファイルを取得 

    filedir,filename=os.path.split(macroPath)
    filename=os.path.splitext(filename)[0]
    os.chdir(filedir)
    print("macro : "+filename)

    bunkatsufunc=get_bunkatsu_func(macroPath) #マクロからbunkatsu関数部分だけを抜き出し
     

       




    print("分割ファイル選択...")
    typ = [('データファイル','*.txt *dat')] 
    filePath=tkfd.askopenfilename(filetypes = typ,title="分割するファイルを選択してください") #ファイルダイアログでファイルを取得
    tk.destroy() #これとtk=Tk()がないと謎のウィンドウが残って邪魔になる

    
    bunkatsufunc(filePath)
    input()
    




def get_bunkatsu_func(macropath):
    #一応GPIBケーブルが刺さって無くても動くようにしたかったのでグローバルエリアの処理は(importを除いて)無視するという実装にしています
    #あまり良い実装ではないので良い解決策があれば誰か直して下さい
    import ast
    import types
    import utilityModule 
    with open(macropath,mode="r",encoding=utilityModule.get_encode_type(macropath)) as f:
        p = ast.parse(f.read())


    for node in p.body[:]:
        if isinstance(node, ast.Assign): #Assign(グローバルエリアでの代入処理?)は排除. これによってGPIBModule.get_instrumentを排除
            p.body.remove(node)
        
    #コピペ
    module = types.ModuleType("mod")
    code = compile(p, "mod.py", 'exec')
    sys.modules["mod"] = module
    exec(code,  module.__dict__)

    import mod 

    if not hasattr(mod, 'bunkatsu'):
        input(mod.__name__+".py : マクロにはbunkatsu関数を定義する必要があります")
        sys.exit()
    elif mod.bunkatsu.__code__.co_argcount!=1:
        input(mod.__name__+".py : bunkatsu関数には1つの引数が必要です")
        sys.exit()

    print("WARNING : グローバル変数など, グローバルエリアに書いた処理は無視されます(仕様です)") 
    return mod.bunkatsu




if __name__=="__main__":
    try:
        main()
    except Exception as e: #めんどくさいのでMAIN.pyとちがってエラーログの書き出しはしない
        import traceback
        traceback.print_exc()
        input("__Error__")

