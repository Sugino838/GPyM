import sys
import os
import ctypes
from collections import namedtuple
import os
import threading
import math
import matplotlib.pyplot as plt
import inputModule
from scipy import interpolate
import msvcrt
import time 
import utilityModule as util
from chardet.universaldetector import UniversalDetector
import matplotlib.style as mplstyle
from collections import deque

def get_error_info(e):
    """
    エラーの情報を返す
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return "%s, %s, %s" % (exc_type, fname, exc_tb.tb_lineno)

def get_encode_type( file_path ) :#テキストファイルの文字コードを判別する. ほぼコピペ
    detector = UniversalDetector()
    with open(file_path, mode= "rb" ) as f:
        for binary in f:
            detector.feed( binary )
            if detector.done:
                break
    detector.close()
    encode_type= detector.result[ "encoding" ]
    if  encode_type=="Windows-1252": #shift-jisがwindows-1252に誤認識されるので強引に直す.(windows-1252が使われているファイルが存在しないことを想定している)
        encode_type="SHIFT_JIS"
    
    return encode_type



