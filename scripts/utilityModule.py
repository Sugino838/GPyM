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
    confidence=0
    for prober in detector._charset_probers:#誤認識を回避するためにutf-8かSHIFT_JISの可能性があればそっちに変更
        if prober.charset_name=="utf-8" or prober.charset_name=="SHIFT_JIS":
            if prober.get_confidence()>confidence:
                encode_type=prober.charset_name
                confidence=prober.get_confidence()
    
    
    return encode_type





def mklogger(logname,level=WARNING):#ロガーの作成
    logger = getLogger(logname)
    logger.setLevel(level)
    
    handler = StreamHandler()
    formatter = Formatter('[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

    
class GPyMException(Exception):
    pass


def create_error(errorlog,logger,e=None):#エラー表示
    if e is not None:
        print(get_error_info(e))
        print(e)
    
    logger.error(errorlog,stacklevel=2)
    input()

    if e is not None:
        return #エラーが既に発生している場合は何も返さないことで現在発生しているエラーをログに出せる
    else:
        return GPyMException(errorlog)


__LOGFILE=None
__LOGPATH=None
def set_LOG(logpath):
    global __LOGFILE,__LOGPATH
    __LOGPATH=logpath
    if os.path.isfile(logpath):
        __LOGFILE=open(logpath,mode="a",encoding=get_encode_type(logpath))
    else:
        __LOGFILE=open(logpath,mode="w",encoding="utf-8")

    import datetime
    date=datetime.datetime.now()
    date=str(date.year)+"-"+str(date.month)+"-"+str(date.day)+"-"+str(date.hour)+":"+str(date.minute)+"\n\n"#日時情報
    __LOGFILE.write("\n\n\n\n\n"+date)


def printlog(text,isprint=True):
    if isprint:
        print(text)
    __LOGFILE.write(text+"\n")
    __LOGFILE.flush()


def inputlog(text=""):
    value =input(text)
    __LOGFILE.write(text+" "+value+"\n")
    __LOGFILE.flush()
    return value

def cut_LOG():
    linemax=10000
    __LOGFILE.close()

    lines=[]
    with open(__LOGPATH,mode="r",encoding=get_encode_type(__LOGPATH)) as f:
        
        
        while True:
            line=f.readline()
            if line=="":
                break
            lines.append(line)
        
    
    if len(lines)>linemax:
        lines=lines[-linemax:]
        newlog=""
        for l in lines:
            newlog+=l
        with open(__LOGPATH,mode="w",encoding="utf-8") as f:
            f.write(newlog)
        

        

def output_ErrorLog(errorlogpath,e):
    import traceback
    #エラーをログファイルに書き出す処理
    loglist=list(traceback.TracebackException.from_exception(e).format())
    log=""
    for l in loglist:
        log=log+l+"\n"
    prelog=[]
    if os.path.isfile(errorlogpath):
        with open (errorlogpath,mode="r",encoding="utf-8") as f: #過去のエラー取得
            while True:
                line=f.readline()
                if line=="":
                    break
                prelog.append(line)
    with open(errorlogpath,mode="w",encoding="utf-8") as f: #今回のエラーを日付と一緒に書き出し
        import datetime
        datetime=datetime.datetime.now()
        f.write("ERROR - "+str(datetime.year)+"-"+str(datetime.month)+"-"+str(datetime.day)+"-"+str(datetime.hour)+":"+str(datetime.minute)+"\n\n")#日時情報
        f.write(log)
        f.write("\n\n\n\n\n")

        #過去のエラーも1000行分は残す
        log_max=1000
        num=log_max if len(prelog) >log_max else len(prelog)

        for i in range(num):
            f.write(prelog[i])






