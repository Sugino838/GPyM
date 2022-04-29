# GPyM

【注意】ここに書いてあることと実際の実装が違う可能性があります。違うところを見つけたら修正しておいてください。

## セットアップ

[セットアップ方法](./setup/SETUP.md)を見てください。

## 定義ファイルの構成

- `DATADIR="任意のパス"`: データ保存先のパス（絶対パスor相対パス）必須
- `TEMPDIR="任意のパス"`: 一時データ保存先のパス（絶対パスor相対パス）必須
- `MACRODIR="任意のパス"`: 測定マクロのあるフォルダーのパス（絶対パスor相対パス）任意
  - これを設定しておくと測定マクロ選択画面でここのパスから始まる

## GPyM側のフォルダー情報

- scripts: GPyMを動かしているスクリプトが入っている。
- SHERED_SETTINGS: 共有設定フォルダー。キャリブレーションファイルなど共有して扱うものを入れる。
  - calibration_file: ここにキャリブレーションファイルを入れる。
- TEMP: エラーログや直前に使った定義ファイル名などが保存されている。無くても困らないものをいれる。
- LOG.txt: ログ。変更が無ければ1万文字分残る。すべてのログが残るわけではなく､ `printlog`、`inputlog`で書き出したものが残る。
- ERRORLOG.txt: エラーログ。変更が無ければ3千文字分残る。
- Example: 使い方の例としていくつかの測定マクロがある。

## 用語定義

- 測定マクロ: 実際に測定する処理を書いたpythonファイル。拡張子は`.py`か`.gpym`

## 仕様

測定マクロを書くときに注意すること

- インデントはスペース4つ分
  - 関数やfor文など":"がつく行の次の行は､前の行よりもスペース4つ分インデントを下げる
  - 関数やfor文などの範囲を抜けたらインデントを上げる
  - タブは使わない（使うとエラーが出る）
- update()の関数は絶対に定義すること
- 関数外の変数（グローバル変数）に代入するときはglobal修飾子をつけて宣言する
- それなりに性能の良いPCを持っているならメモ帳以外のエディター（VS Codeなど）で書くことをオススメします

## 基本仕様

- `start()`、`end()`、`on_command(command)`、`bunkatsu(filepath)`の関数は定義しなくても良いが、逆にスペルミスなどがあってもエラーを吐かない（ログはでる）
- `bunkatsu(filepath)`を定義した場合には測定データはフォルダーに入り、定義しなければ`DATAPATH`直下に測定データが置かれる
- `measurementManager`のいくつかの関数は特定の関数内（`start`,`update`など）でしか使えません。詳しくは下の方を見てください
- 入力したファイル名はクリップボードにコピーされる
  - コピーしたくないときはimport時に`mm._copy_prefilename=hoge`とでもしておけばよい（hogeは適当に定義した関数）
- `GPyM_bunkatsu`で`bunkatsu`関数を呼び出した場合に`GPIB.get_instrument`は引数にかかわらず`None`を返すので注意（GPIBケーブルがつながって無くても動くようにするため）
- 関数外でprintの処理を書くと2回実行される
  - print以外の処理も実は2回ずつ実行されている
  - これはmultiprocessingによって2つのプロセスが走っていることが原因（そのかわりそれぞれの処理は独立しているのでたいていの場合影響はない）
  - 関数外にprint("あああ")などと書くと確認できる

## 測定の流れ

```mermaid
flowchart TB
  A["start"] --> B[update]
  B --> C{"call mm.finish() ?"}
  C -->|Yes| D[end]
  C -->|No| B
  D --> E[bunkatsu]
  E --> F[終了]
```
  
※`on_command`関数はコマンドを打ち込んでEnterを押したときに実行されます。`on_command`が実行している間`update`は止まります。（詳しくはmeasurementManager.pyの中身を見てください）
  
※`mm.finish()`を呼ばなければ測定は終了しません

### 測定と分割の独立

分割の関数はend()の後に改めて呼ばれます｡ 分割に失敗したときなど､分割の処理だけを呼ぶことができます。

### `measurementManager.py (=mm)`について

measurementManager.pyは測定に必要な主な処理のうち､ 変更の可能性が低い処理をまとめているモジュールです。

```python
# データプロットの関数、update以外の場所から呼ばないでください（startでもいけるかも）
# x,y (float): プロットする座標
# label (str | int): ラベル、ラベルごとに色が変わったり線が引かれたりする
mm.plot_data(x, y, label="default")

# データ保存、update以外の場所から呼ばないでください（endでもいけるかも）
# data (tuple): 保存するデータ
mm.save_data(data)

# キャリブレーションファイルを読み込みます
# キャリブレーションファイルを変更するときは形式を以前のファイルとそろえてください
# 基本的に引数は入れずに使います(引数がない場合SHERED_SETTINGS内にあるキャリブレーションファイルを使います)
# 特別な事情がある場合のみ引数にファイルのパスを設定してください
# filename (str): キャリブレーションファイルの名前(パス)、入力しなければSHERED_SETTINGSのものを使うので基本的に入力はしない
# return (str): 使用したキャリブレーションファイル名
mm.set_calibration(filename=None)

# キャリブレーションファイルから読み取ったデータに基づいて線形補間
# 使うにはmm.set_calibration_fileを実行しておく必要があります
# x (float): 入力値
# return (float): 出力を線形補完したもの
mm.calibration(x)

# プロットの設定、startで呼ぶ
# line (bool): 点を線でつなぐかどうか                  
# xlog,ylog (bool): logスケールにするかどうか
# renew_interva (float): グラフの更新間隔（秒）
# legend (bool): 凡例をつけるか(plot_data)
# flowwidth (float): グラフの横幅を一定にして流れていくようなグラフにするときはこれに正の値を設定
mm.set_plot_info(line=False, xlog=False, ylog=False, renew_interval=1, legend=False, flowwidth=0)

# ファイルの冒頭につけるラベルの設定、これが呼ばれないときはラベル無しになる、start以外の場所から呼ばないでください
# label (str): ラベルの文字
mm.set_label(label)

# 測定を終わらせる関数、startで呼ぶとエラーになる（はず）
mm.finish()

# tempフォルダーのパスを返す、使いたければどうぞ
# return (str): tempフォルダーのパス
mm.get_tempdir()

# dataフォルダーのパスを返す、使いたければどうぞ
# return (str): dataフォルダーのパス
mm.get_datadir()

# 共有設定フォルダーのパスを返す、これを使うときは既にあるファイル名とかぶらないように注意！
# return (str): 共有設定フォルダーのパス
mm.get_shared_settings_dir()

# 測定を繰り返すことができる、グローバル変数は初期化されない
# closewindow (bool): グラフウィンドウを閉じるかどうか
mm.repeat_measurement(closewindow=True)
```

### bunkatsuModule.py(=bu)について

```python
# ファイルを開いてデータを配列で返す
# filepath (str): 開くファイルのパス
# return
#   data: ファイルの中身のうち数字の配列に変換できたもの
#   filename: filepathのファイルの名前
#   dirpath: filapathの親フォルダ
#   label: ファイルの中身のうち数字でないもの  
bu.file_open(filepath)

# 昇温/降温で分割
# data (list[list]): データ
# T_index: 温度データの場所（0始まり）
# sample_num (int): 温度変化を評価するサンプル数
# threshold (float): 温度変化を評価する閾値
# return (list[list]): 1つ1つの要素が分割されたデータ配列になっている
bu.heating_cooling_split(data, T_index, sample_num=150, threshold=0.7)

# 周期的に分割
# data (list[list]): データ
# cycle_num: 分割の周期
# return (list[list]): 1つ1つの要素が分割されたデータ配列になっている
bu.cyclic_split(data, cycle_num)返値:

# 新規ファイル作成
# filepath (str): 新しく作成するファイルのパス
# data (list[list]): ファイルに書き込むデータ
# label (str): ファイル先頭につけるラベル
bu.create_file(filepath, data, label):        

# 数値→文字変換（例 10000 → 10E4.0）
# num (int | float): 変換する数字
# significant_digits (int): 有効数字
# return (str): 変換した文字列
bu.from_num_to_10Exx(num, significant_digits=2):      

# TMR用の分割関数
# filepath (str): 分割するファイルのパス
# T_index (int): 温度が入っている場所（0始まり）
# f_index (int): 周波数が入っている場所（0始まり）
# freq_num (int): 測定周波数の数
# threshold (float): 温度変化の閾値、うまく分割できないときなどに設定してください  
bu.TMR_bunkatsu(filepath, T_index, f_index, freq_num=16, threshold=0)
```

### utilityModuleについて

```python
# 基本的にはprint、inputと同じだがこれを使うとTEMPフォルダーのLOG.txtにログが残る

# printしてログに書き込む、printと違って書き出せるのは文字列だけでなおかつ書き出しの引数は1つだけ
# text (str): 書き出す文字列
# isprint (bool): コンソールウィンドウに書き出すかどうか（Falseだとログにだけ書き込む）
printlog(text,isprint=True)

# inputと同じ（たぶん）
# text: inputと同じ（たぶん）
inputlog(text)
```

## FAQ

### GPyM.exeの中身は何か?

とくに変更がなければGPyM.batを実行しているので、GPyM.batを変更するとGPyM.exeの挙動も変わる

### プロットの色を変えたい

windowModuleのcolormapを外部から変更すればできる（たぶん）。元々のコードの書き換えは全員に影響が出るので基本的に行わないように。

### 実装を変えたい

pythonは外部からのアクセスが容易な言語なので､自分用に設定を変える場合などはコードを書き換える必要はなく､外部から関数や変数を自分のものに置き換えることができます。コード本体の書き換えを行う場合は､これまでの測定マクロとの互換性を壊す場合には他の使用者の確認をとってください

### エラーが出た

[エラーと解決法](./TROUBLE_SHOOTING.md)を見てみてください。
