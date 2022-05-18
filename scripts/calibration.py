import os
from logging import getLogger

from scipy import interpolate

import variables as vars
from utility import MyException, get_encode_type

logger = getLogger(__name__)


class CalibrationException(MyException):
    pass


class TMRCalibrationManager:

    """
    TMRの温度校正を行う

    Variables
    -----------
        calib_file_name: キャリブレーションファイルの名前

    Methods
    ---------
        set_shared_calib_file():                SHARED_SETTINGSフォルダに入ったキャリブレーションファイルを使って温度校正を行います

        set_own_calib_file(filepath_calib:str): キャリブレーションを指定して温度校正を行います。普通は使いません。

        calibration(x:float):float               入力xに対して線形補間を行ったyを返します
    """

    calib_file_name: str
    interpolate_func = None

    def set_shared_calib_file(self):
        path = vars.SHARED_SETTINGSDIR + "/calibration_file"
        if not os.path.isdir(path):
            os.mkdir(path)
        import glob

        files = glob.glob(path + "/*")

        files = list(
            filter(lambda f: os.path.split(f)[1][0] != "_")
        )  # 名前の先頭にアンダーバーがあるものは排除

        if len(files) == 0:
            raise CalibrationException(path + "内には1つのキャリブレーションファイルを置く必要があります")
        if len(files) >= 2:
            raise CalibrationException(
                path + "内に2つ以上のキャリブレーションファイルを置いてはいけません。古いファイルの戦闘にはアンダーバー'_'をつけてください"
            )
        filepath_calib = files[0]
        self.__set(filepath_calib)

    def set_own_calib_file(self, filepath_calib: str):
        if not os.path.isfile(filepath_calib):
            raise CalibrationException(
                "キャリブレーションファイル"
                + filepath_calib
                + "が存在しません. "
                + os.getcwd()
                + "で'"
                + filepath_calib
                + "'にアクセスしようとしましたが存在しませんでした."
            )
        self.__set(filepath_calib)

    def __set(self, filepath_calib=None):  # プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み
        """
        キャリブレーションファイルの2列目をx,1列目をyとして線形補間関数を作る.


        Parameter
        ---------

        filepath_calib : string
            キャリブレーションファイルのパス.

        """

        if filepath_calib is not None:
            if not os.path.isfile(filepath_calib):
                raise CalibrationException(
                    "キャリブレーションファイル"
                    + filepath_calib
                    + "が存在しません. "
                    + os.getcwd()
                    + "で'"
                    + filepath_calib
                    + "'にアクセスしようとしましたが存在しませんでした."
                )
        else:
            path = vars.SHARED_SETTINGSDIR + "/calibration_file"
            if not os.path.isdir(path):
                os.mkdir(path)
            import glob

            files = glob.glob(path + "/*")

            files = list(
                filter(lambda f: os.path.split(f)[1][0] != "_")
            )  # 名前の戦闘にアンダーバーがあるものは排除

            if len(files) == 0:
                raise CalibrationException(path + "内には1つのキャリブレーションファイルを置く必要があります")
            if len(files) >= 2:
                raise CalibrationException(
                    path + "内に2つ以上のキャリブレーションファイルを置いてはいけません。古いファイルの戦闘にはアンダーバー'_'をつけてください"
                )
            filepath_calib = files[0]

        with open(
            filepath_calib, "r", encoding=get_encode_type(filepath_calib)
        ) as file:

            x = []
            y = []

            while True:
                line = file.readline()  # 1行ずつ読み取り
                line = line.strip()  # 前後空白削除
                line = line.replace("\n", "")  # 末尾の\nの削除

                if line == "":  # 空なら終了
                    break

                try:
                    array_string = line.split(",")  # ","で分割して配列にする
                    array_float = [float(s) for s in array_string]  # 文字列からfloatに変換

                    x.append(array_float[1])  # 抵抗値の情報
                    y.append(array_float[0])  # 対応する温度の情報
                except Exception:
                    pass

        self.calib_file_name = os.path.split(filepath_calib)[1]
        logger.info("calibration : " + filepath_calib)

        self.interpolate_func = interpolate.interp1d(
            x, y, fill_value="extrapolate"
        )  # 線形補間関数定義

    def calibration(self, x: float):
        """
        プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す
        """
        try:
            y = self.interpolate_func(x)
        except ValueError as e:
            logger.exception("")
            raise CalibrationException(
                "入力されたデータ " + str(x) + " がキャリブレーションファイルのデータ範囲外になっている可能性があります"
            )
        except NameError as e:
            logger.exception("")
            raise CalibrationException("キャリブレーションファイルが読み込まれていない可能性があります")
        except Exception as e:
            logger.exception("")
            raise CalibrationException("予期せぬエラーが発生しました")
        return y
