import datetime
import tkinter.filedialog as tkfd
import os
import utilityModule as util
from tkinter import Tk
import sys


def get_filename(text="file name is > "):
    """
    出力ファイル名を取得

    Returns
    _____________
    filename: string
        出力ファイル名(入力した文字列に日時を追加したものを返す)
    """

    ngwords=["\\","/","?",'"',"<",">","|",":","*"]#ファイルに使えない文字
    wordok=False
    while not wordok:

        filename=input(text)
        for ng in ngwords:
            if ng in filename:
                print("WARNING : 以下の文字列はファイル名に使えません. 入力し直してください")
                for w in ngwords:
                    print(w,end="")
                print("")
                break
        else:
            wordok=True

    #半角スペース,全角スペース,タブは削除
    filename=filename.replace(" ","")
    filename=filename.replace("\u3000","")
    filename=filename.replace("\t","")


    

    dt_now = datetime.datetime.now() #日時取得

    #日時をゼロ埋めしたりしてからファイル名の先頭につける
    year=str(dt_now.year)

    datelabel=year[2]+year[3]+str(dt_now.month).zfill(2)+str(dt_now.day).zfill(2)+"-"+str(dt_now.hour).zfill(2)+str(dt_now.minute).zfill(2)+str(dt_now.second).zfill(2)
    fullfilename=datelabel+"_"+filename
    return fullfilename,datelabel,filename


def read_defdir(dirpath=None,filename=None):

    """
    定義ファイルからデータの保存先ディレクトリを取得

    Returns
    _____________
    datadir: string
        データの保存先ディレクトリ
    """

    

    
    tk = Tk()
    typ = [('定義ファイル', '*.def')]
    defpath=tkfd.askopenfilename(filetypes = typ,title="定義ファイルを選んでください",initialdir=dirpath,initialfile=filename) #ファイルダイアログでファイルを取得
    fileobj = open(defpath, "r", encoding=util.get_encode_type(defpath)) #ファイルの読み込み

    tk.destroy() #これとtk=Tk()がないと謎のウィンドウが残って邪魔になる

    print("define file : "+os.path.basename(defpath))

    datadir=None
    macrodir=None
    tempdir=None
    #ファイルの中身を1行ずつ見ていく
    while True:
        line=fileobj.readline() #ファイルから1行取得
        if line:
            line = "".join(line.split()) #スペース･改行文字の削除
            line=line.rstrip("\\") #パスの最後尾に"\"があれば削除
            if "DATADIR=" in line:
                datadir=line[8:] #"DATADIR="の後ろの文字列を取得
            if "TEMPDIR=" in line:
                tempdir=line[8:]
            if "MACRODIR=" in line:
                macrodir=line[9:]
                 
        else:#最後の行までいったらbreak
            break

    
    
    if datadir==None:
        #最後まで見てDATADIRが無ければエラー表示
        input("ERROR : 定義ファイルにDATADIRの定義がありません")
        sys.exit()
    else:

        if ":" not in datadir:#相対パスなら定義ファイルからの絶対パスに変換
            datadir=os.path.dirname(defpath)+"/"+datadir

        if not os.path.isdir(datadir):#データフォルダが存在しなければエラー
            input("定義ファイルERROR : "+datadir+"は存在しないフォルダです")
            sys.exit()


    if tempdir==None:
        #最後まで見てTEMPDIRが無ければエラー表示
        input("ERROR : 定義ファイルにTEMPDIRの定義がありません")
        sys.exit()
    else:

        if ":" not in tempdir:#相対パスなら定義ファイルからの絶対パスに変換
            tempdir=os.path.dirname(defpath)+"/"+tempdir

        if not os.path.isdir(tempdir):#データフォルダが存在しなければエラー
            input("定義ファイルERROR : "+tempdir+"は存在しないフォルダです")
            sys.exit()


    if macrodir==None:
        print("warning:you can set MACRODIR in your define file")
    else:
        if ":" not in macrodir:#相対パスなら定義ファイルからの絶対パスに変換
            macrodir=os.path.dirname(defpath)+"/"+macrodir

        if not os.path.isdir(macrodir):#マクロフォルダが存在しなければ警告
            print("定義ファイルWARING : "+macrodir+"は存在しないフォルダです")
            macrodir=None



    return defpath,datadir,macrodir,tempdir #MACRODIRは定義されてなくても通す


def input_num(text=""):
    while True:
        num_str=input(text)
        num_str="".join(num_str.split())
        
        try:
            num=float(num_str)
        except Exception:
            si_prefixes_str=num_str[-1:] 
            num_str=num_str[:-1]
            si_prefixes=None
            if si_prefixes_str=="k":
                si_prefixes=1.0e+3
            elif si_prefixes_str=="M":
                si_prefixes=1.0e+6
            elif si_prefixes_str=="G":
                si_prefixes=1.0e+9
            elif si_prefixes_str=="T":
                si_prefixes=1.0e+12
            elif si_prefixes_str=="P":
                si_prefixes=1.0e+15
            elif si_prefixes_str=="E":
                si_prefixes=1.0e+18
            elif si_prefixes_str=="m":
                si_prefixes=1.0e-3
            elif si_prefixes_str=="μ":
                si_prefixes=1.0e-6
            elif si_prefixes_str=="n":
                si_prefixes=1.0e-9
            elif si_prefixes_str=="p":
                si_prefixes=1.0e-12
            elif si_prefixes_str=="f":
                si_prefixes=1.0e-15
            elif si_prefixes_str=="a":
                si_prefixes=1.0e-18
        
            try:
                num=float(num_str)*si_prefixes
            except Exception:
                print("入力を数値に変換できませんでした. もう一度入力してください")
                continue
        break

    return num

if __name__=="__main__":
    print(input_num("input>"))
