import time

from GPIB import get_instrument
from measurement_manager import (
    finish,
    plot,
    save,
    set_file_name,
    set_plot_info,
    write_file,
)


def update():
    print("今からGPyMのテストを始めます...")
    time.sleep(1)

    print("まずGPIBの動作チェックをします...")
    num = input("接続している機器のGPIB番号を入力してください >>")
    print("接続しています...")
    time.sleep(2)
    inst = get_instrument(int(num))
    name = inst.query("")
    print(f"接続している機器の名前は {name} です")

    time.sleep(2)

    print("最後に、ファイル書き出しのチェックを行います")

    text = input("ファイルに書きたい文字を入力してください")

    write_file(text)


def after(path):
    print("終了しました。ファイルを確認してみてください")
    time.sleep(5)
