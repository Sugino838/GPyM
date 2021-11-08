import sys
import os
from chardet.universaldetector import UniversalDetector
from logging import getLogger,DEBUG,WARNING,StreamHandler,Formatter

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





def mklogger(logname,level=WARNING):
    logger = getLogger(logname)
    logger.setLevel(level)
    
    handler = StreamHandler()
    formatter = Formatter('[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

    
class GPyMException(Exception):
    pass


def create_error(errorlog,logger,e=None):
    if e is not None:
        print(get_error_info(e))
        print(e)
    
    logger.error(errorlog,stacklevel=2)
    input()

    if e is not None:
        return #エラーが既に発生している場合は何も返さないことで現在発生しているエラーをログに出せる
    else:
        return GPyMException(errorlog)
