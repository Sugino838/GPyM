import importlib
import sys
import os
import tkinter.filedialog as tkfd
from tkinter import Tk
import inputModule as inp
import measurementManager as mm
import utilityModule as util
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader 
import ctypes
from utilityModule import GPyMException,printlog,inputlog

#簡易編集モードをOFFにするためのおまじない
kernel32 = ctypes.windll.kernel32
mode=0xFDB7 #簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)


TEMPDIR=None#TEMPフォルダーのパス
SHERED_SETTINGS_DIR=None #共有設定フォルダのパス
logger=util.mklogger(__name__)

def main():
    """
    測定マクロを動かすための準備をするスクリプト

    実装としては

    定義ファイル選択
    ↓
    測定マクロ選択
    ↓
    測定マクロ読み込み
    ↓
    必要な関数(updateなど)があるか確認
    ↓
    measurementManager._measure_startを実行

    """
    #sys.path.append(os.path.dirname(sys.executable))

    path_deffilepath=TEMPDIR+"\\deffilepath"#前回の定義ファルのパスが保存されているファイル
    if not os.path.isfile(path_deffilepath):#deffilepathがなければ作る
        with open(path_deffilepath,mode="w",encoding="utf-8") as f:
            pass
    
    with open(path_deffilepath,mode="r",encoding="utf-8") as f:#前回の定義ファイルのフォルダを開いて定義ファイル選択画面へ
        predefpath=f.read()
        predefdir=None
        predeffilename=None
        if os.path.isfile(predefpath):
            predefdir,predeffilename=os.path.split(predefpath)
        print("定義ファイル選択...")
        defpath,datadir,default_macrodir,tempdir=inp.read_defdir(dirpath=predefdir,filename=predeffilename)#前回の定義ファイルのパスがあったところからファイル選択ダイアログを開く

    with open(path_deffilepath,mode="w",encoding="utf-8") as f:#今回の定義ファイルのパスを保存
        f.write(defpath)
    
    
        
        
    path_premacroname=TEMPDIR+"\\premacroname"
    if not os.path.isfile(path_premacroname):
        with open(path_premacroname,mode="w",encoding="utf-8") as f:
            pass

    with open(path_premacroname,mode="r",encoding="utf-8") as f:
        premacroname=f.read()


    tk = Tk()
    print("マクロ選択...")
    typ = [('pythonファイル','*.py *.gpym')] #gpymは勝手に作った拡張子
    macropath=tkfd.askopenfilename(filetypes = typ,title="マクロを選択してください",initialdir=default_macrodir,initialfile=premacroname) #マクロ選択
    tk.destroy() #これとtk=Tk()がないと謎のウィンドウが残って邪魔になる


    macrodir,macroname=os.path.split(macropath)#マクロのパスをフォルダとファイル名に分割

    with open(path_premacroname,mode="w",encoding="utf-8") as f:
        f.write(macroname)


    printlog("macro : "+macroname)
    macroname=os.path.splitext(macroname)[0]#ファイル名から拡張子をとる

    #importlibを使って動的にpythonファイルを読み込む
    spec = spec_from_loader(macroname, SourceFileLoader(macroname,macropath))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    #測定マクロに必要な関数と引数が含まれているか確認
    UNDIFINE_ERROR=False
    UNDIFINE_WARNING=""
    if not hasattr(target, 'start'):
        target.start=None
        UNDIFINE_WARNING+="start, "
    elif target.start.__code__.co_argcount!=0:
        logger.error(target.__name__+".startには引数を設定してはいけません")
        UNDIFINE_ERROR=True

    if not hasattr(target, 'update'):
        logger.error(target.__name__+".pyの中でupdateを定義する必要があります")
        UNDIFINE_ERROR=True
    elif target.update.__code__.co_argcount!=0:
        logger.error(target.__name__+".updateには引数を設定してはいけません")
        UNDIFINE_ERROR=True

    if not hasattr(target, 'end'):
        target.end=None
        UNDIFINE_WARNING+="end, "
    elif target.end.__code__.co_argcount!=0:
        logger.error(target.__name__+".endには引数を設定してはいけません")
        UNDIFINE_ERROR=True

    if not hasattr(target, 'on_command'):
        target.on_command=None
        UNDIFINE_WARNING+="on_command, "
    elif target.on_command.__code__.co_argcount!=1:
        logger.error(target.__name__+".on_commandには引数を設定してはいけません")
        UNDIFINE_ERROR=True

    if not hasattr(target, 'bunkatsu'):
        target.bunkatsu=None
        UNDIFINE_WARNING+="bunkatsu, "
    elif target.bunkatsu.__code__.co_argcount!=1:
        logger.error(target.__name__+".bunkatsuには引数を設定してはいけません")
        UNDIFINE_ERROR=True
               

    
    if issubclass(target.Data,tuple):
        data_label=""
        count=1
        for s in target.Data._fields:
            data_label+="["+str(count)+"]"+s+", "
            count+=1
        data_label=data_label[:-2]
    else:
        logger.error("Dataをnamedtupleで定義してください")
        UNDIFINE_ERROR=True

    if UNDIFINE_ERROR:
        input("エラーのため終了します...")
        sys.exit()

    if UNDIFINE_WARNING !="":
        UNDIFINE_WARNING=UNDIFINE_WARNING[:-2]
        printlog("UNDEFINED FUNCTION : "+UNDIFINE_WARNING)

    mm._set_variables(datadir=datadir,tempdir=tempdir,file_label=data_label,shared_settings_dir=SHERED_SETTINGS_DIR)

    os.chdir(macrodir)#カレントディレクトリを測定マクロ側に変更

    mm._measure_start(start=target.start,update=target.update,end=target.end,on_command=target.on_command,bunkatsu=target.bunkatsu)#測定開始
    


if __name__=="__main__":
    filedir=os.getcwd()
    if not os.path.isdir("TEMP"):#TEMPDIRが無ければつくる
        os.mkdir("TEMP")
    TEMPDIR=filedir+"\\TEMP"

    if not os.path.isdir("SHERED_SETTINGS"):#SHERED_SETTINGSが無ければつくる
        os.mkdir("SHERED_SETTINGS")
    SHERED_SETTINGS_DIR=filedir+"\\SHERED_SETTINGS"

    
    util.set_LOG(TEMPDIR+"\\LOG.txt")



    try:
        main()
    except Exception as e:
        util.output_ErrorLog(TEMPDIR+"\\ERRORLOG.txt",e)
        import traceback

        if type(e) is not GPyMException:#自分で設定したエラー以外はコンソールウィンドウにエラーログを表示
            traceback.print_exc()#エラー表示
            input("__Error__")#コンソールウィンドウが落ちないように入力待ちを入れる
    else:
        util.cut_LOG()
    

    