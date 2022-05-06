import ctypes
import os
import sys
from logging import getLogger

import measurementManager as mm
import variables as vars
from define import read_deffile
from inputModule import ask_open_filename
from macro import get_macro, get_macro_bunkatsu, get_macropath
from utilityModule import setlog

logger = getLogger(__name__)


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
    # 定義ファイル読み取り
    read_deffile()

    macropath, _, macrodir = get_macropath()

    macro = get_macro(macropath)

# <<<<<<< HEAD
#     macropath,macroname,macrodir=get_macropath(macrodir_default)#マクロファイルの取得

#     macro=get_macro(macropath)#マクロファイルからpythonマクロに変換
# =======
    # mm._set_variables(
    #     datadir=vars.DATADIR,
    #     tempdir=vars.MACRODIR,
    #     file_label=data_label,
    #     shared_settings_dir=str(vars.SHARED_SETTINGSDIR),
    # )

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(macrodir)


    # 測定開始
    mm._measure_start(macro)

# <<<<<<< HEAD
    

#     os.chdir(macrodir)#カレントディレクトリを測定マクロ側に変更

#     mm._measure_start(macro)#測定開始
    

# def get_deffile():
#     path_deffilepath=vars.SHARED_TEMPDIR+"\\deffilepath"#前回の定義ファルのパスが保存されているファイル
#     if not os.path.isfile(path_deffilepath):#deffilepathがなければ作る
#         with open(path_deffilepath,mode="w",encoding="utf-8") as f:
#             pass

#     with open(path_deffilepath,mode="r",encoding="utf-8") as f:#前回の定義ファイルのフォルダを開いて定義ファイル選択画面へ
#         predefpath=f.read()
#         predefdir=None
#         predeffilename=None
#         if os.path.isfile(predefpath):
#             predefdir,predeffilename=os.path.split(predefpath)
#         print("定義ファイル選択...")


#         tk = Tk()
#         typ = [('定義ファイル', '*.def')]
#         defpath=tkfd.askopenfilename(filetypes = typ,title="定義ファイルを選んでください",initialdir=predefdir,initialfile=predeffilename) #ファイルダイアログでファイルを取得
#         tk.destroy() #これとtk=Tk()がないと謎のウィンドウが残って邪魔になる

#     if os.path.isfile(defpath):
#         with open(path_deffilepath,mode="w",encoding="utf-8") as f:#今回の定義ファイルのパスを保存
#             f.write(defpath)

#     return defpath


# def read_deffile(path_deffile):#定義ファイルを読み込んで各フォルダのパスを取得
#     datadir=None
#     macrodir=None
#     tempdir=None

#     with open(path_deffile, "r", encoding=util.get_encode_type(path_deffile)) as f: #ファイルの読み込み
#         #ファイルの中身を1行ずつ見ていく
#         while True:
#             line=f.readline() #ファイルから1行取得
#             if line:
#                 line = "".join(line.split()) #スペース･改行文字の削除
#                 line=line.rstrip("\\") #パスの最後尾に"\"があれば削除
#                 if "DATADIR=" in line:
#                     datadir=line[8:] #"DATADIR="の後ろの文字列を取得
#                 if "TMPDIR=" in line:
#                     tempdir=line[7:]
#                 if "MACRODIR=" in line:
#                     macrodir=line[9:]
                    
#             else:#最後の行までいったらbreak
#                 break

        
        
#         if datadir==None:
#             #最後まで見てDATADIRが無ければエラー表示
#             input("ERROR : 定義ファイルにDATADIRの定義がありません")
#             sys.exit()
#         else:

#             if ":" not in datadir:#相対パスなら定義ファイルからの絶対パスに変換
#                 datadir=os.path.dirname(path_deffile)+"/"+datadir

#             if not os.path.isdir(datadir):#データフォルダが存在しなければエラー
#                 input("定義ファイルERROR : "+datadir+"は定義ファイルに設定されていますが存在しません")
#                 sys.exit()


#         if tempdir==None:
#             #最後まで見てTEMPDIRが無ければエラー表示
#             input("ERROR : 定義ファイルにTMPDIRの定義がありません")
#             sys.exit()
#         else:

#             if ":" not in tempdir:#相対パスなら定義ファイルからの絶対パスに変換
#                 tempdir=os.path.dirname(path_deffile)+"/"+tempdir

#             if not os.path.isdir(tempdir):#TEMPフォルダが存在しなければエラー
#                 input("定義ファイルERROR : "+tempdir+"は定義ファイルに設定されていますが存在しません")
#                 sys.exit()


#         if macrodir==None:
#             print("warning:you can set MACRODIR in your define file")
#         else:
#             if ":" not in macrodir:#相対パスなら定義ファイルからの絶対パスに変換
#                 macrodir=os.path.dirname(path_deffile)+"/"+macrodir

#             if not os.path.isdir(macrodir):#マクロフォルダが存在しなければ警告
#                 print("定義ファイルWARING : "+macrodir+"は定義ファイルに設定されていますが存在しません")
#                 macrodir=None

#         vars.DATADIR=datadir
#         vars.TEMPDIR=tempdir
#         vars.MACRODIR=macrodir

#         return datadir,macrodir,tempdir #MACRODIRは定義されてなくても通す


# def get_macropath(path_macrodir):
#     path_premacroname=vars.SHARED_TEMPDIR+"\\premacroname"#前回のマクロ名が保存されたファイルのパス
#     if not os.path.isfile(path_premacroname):
#         with open(path_premacroname,mode="w",encoding="utf-8") as f:
#             pass

#     with open(path_premacroname,mode="r",encoding="utf-8") as f:
#         premacroname=f.read()


#     tk = Tk()
#     print("マクロ選択...")
#     typ = [('pythonファイル','*.py *.gpym')] #gpymは勝手に作った拡張子
#     macropath=tkfd.askopenfilename(filetypes = typ,title="マクロを選択してください",initialdir=path_macrodir,initialfile=premacroname) #マクロ選択
#     tk.destroy() #これとtk=Tk()がないと謎のウィンドウが残って邪魔になる


#     macrodir,macroname=os.path.split(macropath)#マクロのパスをフォルダとファイル名に分割

#     with open(path_premacroname,mode="w",encoding="utf-8") as f:
#         f.write(macroname)


#     printlog("macro : "+macroname)
#     macroname=os.path.splitext(macroname)[0]#ファイル名から拡張子をとる
#     return macropath,macroname,macrodir

# def get_macro(macropath):#パスから各種関数を読み込み

#     macroname=os.path.splitext(os.path.split(macropath)[1])[0]
#     #importlibを使って動的にpythonファイルを読み込む
#     spec = spec_from_loader(macroname, SourceFileLoader(macroname,macropath))
#     target = module_from_spec(spec)
#     spec.loader.exec_module(target)

#     #測定マクロに必要な関数と引数が含まれているか確認
#     UNDIFINE_ERROR=False
#     UNDIFINE_WARNING=""
#     if not hasattr(target, 'start'):
#         target.start=None
#         UNDIFINE_WARNING+="start, "
#     elif target.start.__code__.co_argcount!=0:
#         logger.error(target.__name__+".startには引数を設定してはいけません")
#         UNDIFINE_ERROR=True

#     if not hasattr(target, 'update'):
#         logger.error(target.__name__+".pyの中でupdateを定義する必要があります")
#         UNDIFINE_ERROR=True
#     elif target.update.__code__.co_argcount!=0:
#         logger.error(target.__name__+".updateには引数を設定してはいけません")
#         UNDIFINE_ERROR=True

#     if not hasattr(target, 'end'):
#         target.end=None
#         UNDIFINE_WARNING+="end, "
#     elif target.end.__code__.co_argcount!=0:
#         logger.error(target.__name__+".endには引数を設定してはいけません")
#         UNDIFINE_ERROR=True

#     if not hasattr(target, 'on_command'):
#         target.on_command=None
#         UNDIFINE_WARNING+="on_command, "
#     elif target.on_command.__code__.co_argcount!=1:
#         logger.error(target.__name__+".on_commandには引数を設定してはいけません")
#         UNDIFINE_ERROR=True

#     if not hasattr(target, 'bunkatsu'):
#         target.bunkatsu=None
#         UNDIFINE_WARNING+="bunkatsu, "
#     elif target.bunkatsu.__code__.co_argcount!=1:
#         logger.error(target.__name__+".bunkatsuには引数を設定してはいけません")
#         UNDIFINE_ERROR=True
               
#     if UNDIFINE_WARNING !="":
#         UNDIFINE_WARNING=UNDIFINE_WARNING[:-2]
#         printlog("UNDEFINED FUNCTION : "+UNDIFINE_WARNING)

    
#     if issubclass(target.Data,tuple):
#         data_label=""
#         count=1
#         for s in target.Data._fields:
#             data_label+="["+str(count)+"]"+s+", "
#             count+=1
#         data_label=data_label[:-2]
#     else:
#         logger.error("Dataをnamedtupleで定義してください")
#         UNDIFINE_ERROR=True
#     target._data_label=data_label

#     if UNDIFINE_ERROR:
#         input("エラーのため終了します...")
#         sys.exit()

#     return target
# =======
# >>>>>>> 78c856629d8dd82ca491405187676af907cbaace

def bunkatsu_only():
    print("分割マクロ選択...")
    macroPath = ask_open_filename(
        filetypes=[("pythonファイル", "*.py *.gpym")], title="分割マクロを選択してください"
    )

    os.chdir(str(macroPath.parent))
    print(f"macro: {macroPath.stem}")

    def noop(address):
        return None

    import GPIBModule

    # GPIBモジュールの関数を書き換えてGPIBがつながって無くてもエラーが出ないようにする
    GPIBModule.get_instrument = noop
    logger.info("you can't use GPIB.get_instrument in GPyM_bunkatsu")
    logger.info("you can't use most of measurementManager's methods in GPyM_bunkatsu")

    target = get_macro_bunkatsu(macroPath)

    print("分割ファイル選択...")
    filePath = ask_open_filename(
        filetypes=[("データファイル", "*.txt *dat")], title="分割するファイルを選択してください"
    )

    mm._set_variables(
        datadir=None,
        tempdir=None,
        file_label=None,
        shared_settings_dir=vars.SHARED_SETTINGSDIR,
    )
    target.bunkatsu(filePath)
    input()


def setting():
    """変数のセット"""
    setlog()

    # 簡易編集モードをOFFにするためのおまじない
    kernel32 = ctypes.windll.kernel32
    # 簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
    mode = 0xFDB7
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)


if __name__ == "__main__":
    setting()

    mode = ""
    args = sys.argv
    if len(args) > 1:
        mode = args[1].upper()

    while True:
        if mode in ["MEAS", "BUNKATSU"]:
            break
        mode = input("mode is > ").upper()

    try:
        if mode == "MEAS":
            main()
        else:
            bunkatsu_only()

    except Exception as e:
        logger.exception(e)

        # コンソールウィンドウが落ちないように入力待ちを入れる
        input("__Error__")
