import matplotlib.pyplot as plt
import time 
from multiprocessing import Process, Lock, Manager
import threading
import msvcrt
import sys
import numpy as np

"""
    プロットの処理と終了入力待ちは測定と別プロセスで行って非同期にする
    (データ数が増えてプロットに時間がかかっても測定に影響が出ないようにする)


    Variables
    ________________
    _isfinis :int
        測定の終了を測定側とplotWindow側で共有するための値

"""


_isfinish=None

def exec(share_list,isfinish,lock,xlog,ylog,graph_renew_interval):#別プロセスで最初に実行される場所
    global _isfinish
    _isfinish=isfinish

    PlotWindow(share_list,lock,xlog,ylog,graph_renew_interval).run()#インスタンス作成, 実行


   
        


class PlotWindow():
    """

        測定データをグラフにするクラス

        Variables
        ____________
        share_list :List
            測定したデータを一時的に保管しておく場所
            非同期処理のため測定とプロットがずれるので, そのためにバッファーのようなものを挟む必要がある
            測定側で測定データをshare_listに詰めていく
            PlotWindowはshare_listのデータを取り込んでプロットした後に中身を消す
            この処理が衝突しないようにlock(セマフォ)をかけて排他制御する

        lock:
            プロセス間の共有ファイルを同時に触らないためのロック
    """
   
    _figure=None
    _ax=None

    def __init__(self,share_list,lock,xlog,ylog,graph_renew_interval):#コンストラクタ
        self.share_list=share_list
        self.lock=lock
        self.xlog=xlog
        self.ylog=ylog
        self.interval=graph_renew_interval
    
    def run(self):#実行
        self.set_plotwindow(self.xlog,self.ylog)
        interval=self.interval
        while True:#一定時間ごとに更新
            self.renew_window()
            if _isfinish.value==1:#終了していたらbreak
                break
            time.sleep(interval)

        while True:#終了してもグラフを表示したままにする
            try:
                self._figure.canvas.flush_events()
            except Exception:#｢ここでエラーが出る⇒グラフウィンドウを消した｣と想定しているのでエラーはもみ消す
                break
            time.sleep(0.05)#グラフ操作のFPSを20くらいにする
   


        
    
    
    def renew_window(self):#グラフの更新
        self.lock.acquire()#共有リストにロックをかける
        #share_listのコピーを作成.(temp=share_listにすると参照になってしまうのでdel self.share_list[:]でtempも消えてしまう)
        temp=self.share_list[:] #[i for i in self.share_list]はかなり重い
        del self.share_list[:]#共有リストは削除
        self.lock.release()#ロック解除
        for i in  range(len(temp)) :#tempの中身をプロット
            x,y,color=temp[i]
            self._ax.plot(x,y,marker='.',color=color)

        self._figure.canvas.flush_events() #グラフを再描画するおまじない


    def set_plotwindow(self,xlog=False,ylog=False):#グラフの準備
        plt.ion()#ここはコピペ
        self._figure, self._ax = plt.subplots(figsize=(8,6))#ここはコピペ
        if xlog:
            plt.xscale('log')#横軸をlogスケールに
        if ylog:
            plt.yscale('log')#縦軸をlogスケールに