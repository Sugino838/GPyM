@echo off
if not exist scripts (
echo %CD%にはscriptsという名前のフォルダーが存在しません
set /p __=
exit /b
)
if not exist BUNKATSU_ONLY.py (
echo %CD%\scriptsにはBUNKATSU_ONLY.pyが存在しません
set /p __=
exit /b
)
echo on
py scripts\BUNKATSU_ONLY.py 