import tkinter.filedialog as tkfd
from tkinter import Tk
import sys
import os
import time
import utilityModule as util
import math



__logger=util.mklogger(__name__)

def heating_cooling_split(data,T_index,sample_and_cutout_num=(150,120),step=10,threshold=None):

    """
    heating,coolingを判断して分割する関数

    Parameters
    _____________

    data : 二次元配列
        瞬間の測定値の配列が並んだ二次元配列
    
    T_index : int
        温度が格納されている場所のインデックス(0始まり)

    sample_num : (int,int)
        温度変化を判断するためのサンプル数と閾値
        1つ目のintは温度変化を判定するために使用するプロット点の数
        2つ目のintは昇温降温を判断するための閾値(N個の点それぞれについて前の点より温度が上がっていれば+1,下がっていれば-1,絶対値がthreshold以下なら0で合計値がこのint以上なら昇温または降温とする)

    threshold : float
        温度変化を判断するための閾値
        直前のプロットからの温度変化がこれ以下なら温度変化を0として扱う

    Returns
    _____________

    new_data : 配列の配列
        分割したかたまりごとに配列につめる
    """


    if step==0:
        setp=1

    sample_num=sample_and_cutout_num[0]
    cutout_num=sample_and_cutout_num[1]


    def temp_judge(temp_grad):
        nonlocal threshold
        value=1 if temp_grad >0 else -1 #温度が上昇していれば1, いなければ-1をサンプルにつめる
        if threshold is not None and abs(temp_grad) < threshold:
            value=0
        return value



    samples_hc=[] #サンプルを入れる配列
    count=0
    for i in range(sample_num):
        if count>=len(data)-step:
            __logger.warning("データ数が少なすぎるかsample数が多すぎます. 必要最小データ数は"+sys._getframe().f_code.co_name+"の引数から設定できます")
            return [data]

        temp_grad=data[count+step][T_index]-data[count][T_index]

        samples_hc.append(temp_judge(temp_grad))
        count+=1
    
    previous_state=-5#一個前の昇温降温状態. 一度温度勾配がなくなった後に再び同じ方向に温度変化した場合に対応
    state=0 #全体としての状態, heatingなら1,coolingなら-1,どっちでもなければ0
    split_points_hc=[] #分割する点をいれる配列
    while True:
        
        
        sum_count=sum(samples_hc) #温度変化のサンプルの和をとる
        
        
        if sum_count>cutout_num: #閾値を設定してそれを超えるかどうかでheating,coolingを判定
            new_state=1
        elif sum_count<cutout_num*(-1):
            new_state=-1
        else:
            new_state=0

                
        


        if state!=new_state: #一個前の状態と違うならsplit_points_hcに情報を入れる
            if previous_state==new_state:
                del split_points_hc[-1]
            else:
                if state!=0:#一個前の状態がheating or cooling なら 分割の終わり
                    split_points_hc.append(count) 
            
                if new_state!=0:#今の状態がheating or cooling なら 分割の始まり
                    split_points_hc.append(count-sample_num)
                    previous_state=new_state
        

        if count>=len(data)-step: #countが最後まできたら終了
            if len(split_points_hc)%2==1:#最後の分割範囲が閉じてなければ閉じる
                split_points_hc.append(count)
            break

        state=new_state
        temp_grad=data[count+step][T_index]-data[count][T_index]
        samples_hc[count%sample_num]=temp_judge(temp_grad)
        count+=1

    new_data=[]
    for i in range(0,len(split_points_hc),2): #split_points_hcの情報に基づいて分割
        new_data.append(data[split_points_hc[i]:split_points_hc[i+1]])

    
    return new_data



    


def cyclic_split(data,cycle_num):
    """
    周期的に分割

    Parameters
    _____________

    cycle_num: int
        分割の周期

    Returns
    _____________

    new_data : 配列の配列

    """
    
    count=0
    max_num=len(data)

    new_data=[[] for i in range(cycle_num)]

    while True:
        for i in range(cycle_num): #データを上から順番に周期的に振り分け
            new_data[i].append(data[count])
            count+=1
            if count>=max_num:
                break
        else:
            continue #forループを正常に抜けたらcontinue 

        break #breakでforループを抜けたときだけここが実行される

    
    return new_data



def from_num_to_10Exx(num,significant_digits=2):

    """
    数字を10Exx形式にして文字列として返す

    Parameters
    _____________

    num : int or float
        10Exx形式に変換させたい数字

    significant_digits : int
        変換後の有効数字. significant_digits=3なら10E3.49などが返る
    
    Returns
    _____________

    index_txt : 10Exx形式に変換した文字列
    """

    logf=math.log10(num)#対数をとる
    abs_digits=significant_digits+1 - math.ceil(math.log10(abs(logf)))
    index_txt=str(round(logf, abs_digits))#有効数字におとす

    if abs_digits>0:
        while significant_digits >= len(index_txt):
            index_txt=index_txt+"0"

    index_txt="10E"+index_txt
    return index_txt

def file_open(filepath):
    """
    ファイルを開いて中身を二次元配列で返す

    Parameter
    _________________
    filepath : string
        見鋳込むファイルのpath(絶対パスを想定)

    Returns
    __________
    data : 二次元配列
        ファイルの中身を二次元配列に変換した物
    """
    
    dirpath=os.path.dirname(filepath) #ファイルのpathからディレクトリ名を取得
    filename=os.path.splitext(os.path.basename(filepath))[0] #fileのpathからファイル名(拡張子抜き)を取得


    file=open(filepath,'r',encoding=util.get_encode_type(filepath))#ファイルを開く

    #label =file.readline()+file.readline()#最初の2行はラベルだとしてそこは抜き出す
    label=""
    data=[]
    num_label=0
    num_data=0
    while True:
        line_raw=file.readline()
        line = line_raw.strip() #前後空白削除

        if line == "": #空なら終了
            break

        line = line.replace('\n','') #末尾の\nの削除

        if line == "": #空行なら次の行へ
            continue

        try:
            array_string = line.split(",") #","で分割して配列にする
            array_float=[float(s) for s in array_string] #文字列からfloatに変換
            data.append(array_float)
            num_data+=1
        except Exception:
            label+=line_raw
            num_label+=1

    file.close()
    
    print("非データ行 : ",num_label,", データ行 : " ,num_data)

    if num_data==0:
        raise util.create_error("データ行が0行です. 読み取りに失敗しました.",__logger)

    return data,filename,dirpath,label





            
            

        


def create_file(filepath,data,label=""):
    """
    新規ファイル作成. フォルダがない場合は作る


    Parameters
    _____________

    filepath : str
        作成するファイルのパス. パスに既にファイルが存在していればエラー

    data : 配列
        ファイルに入力するデータ配列

    label : str
        ファイル冒頭のラベル

    """
    def array2D_to_text(array2D):
        text=""
        for array1D in array2D:
            t=""
            for element in array1D:
                t+=str(element)+","
            t=t[:-1]
            t+="\n"
            text+=t

        return text


    dirpath = os.path.dirname(filepath)
    os.makedirs(dirpath, exist_ok=True)


    if os.path.isfile(filepath):
        raise util.create_error("新規作成しようとしたファイル"+filepath+"は既に存在しています.削除してからやり直してください.\n解決できない場合はcyclic_splitの分割数などを見直してみてください",__logger)

    with open(filepath,'x',encoding="utf-8") as f:
        f.write(label)
        f.write(array2D_to_text(data))




def TMR_bunkatsu(filepath,T_index,f_index,freq_num=16,sample_and_cutout_num=(150,120),step=10,threshold=0):
    """
    TMR用の分割関数.

    Parameter
    __________________________

    filepath : string
        分割元のファイルのパス

    T_index : int
        分割元のファイルの温度値の列番号(左から0始まり)

    f_index : int
        分割元のファイルの周波数値の列番号(左から0始まり)

    freq_num : int
        周波数の分割数

    sample_and_cutout_num : (int,int)
        1つ目のintは温度変化を判定するために使用するプロット点の数
        2つ目のintは昇温降温を判断するための閾値(N個の点それぞれについて前の点より温度が上がっていれば+1,下がっていれば-1,絶対値がthreshold以下なら0で合計値がこのint以上なら昇温または降温とする)

    step : int
        昇温降温判定でstep分離れたプロットと温度比較を行う.

    threshold : float
        昇温降温判定でthreshold以下の温度変化は温度変化なしとみなす

    """

    print("bunkatsu start...")
    data,filename,dirpath,label=file_open(filepath)#ファイルを開いて配列として取得
    count=0
    for split_data in heating_cooling_split(data,T_index=T_index,sample_and_cutout_num=sample_and_cutout_num,step=step,threshold=threshold):#昇温降温で分割

        displacement=split_data[len(split_data)-1][T_index]-split_data[0][T_index]
        state= "heating" if displacement>0 else "cooling"
        new_dir=dirpath+"\\"+filename+"_"+str(count)+"_"+state

        new_filepath=new_dir+"\\"+filename+"_"+str(count)+"_"+state+"_all.txt"
        create_file(filepath=new_filepath,data=split_data,label=label)

        for split_split_data in cyclic_split(split_data,cycle_num=14):#周波数でさらに分割


            freq=split_split_data[0][f_index]
            
            freq=from_num_to_10Exx(freq,significant_digits=3)

            new_filepath=new_dir+"\\"+filename+"_"+str(count)+"_"+state+"_"+freq+"Hz.txt"#ファイルのパスを設定

            create_file(filepath=new_filepath,data=split_split_data,label=label)

        count+=1


    print("file has been completely bunkatsued")




def main():
    tk = Tk()
    print("select bunkatsu file...")
    inputPath=tkfd.askopenfilename() #ファイルダイアログでファイルを取得
    tk.destroy()

    bunkatsu(inputPath)
    

if __name__ == "__main__":
    main()