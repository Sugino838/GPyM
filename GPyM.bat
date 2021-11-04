@echo off
if exist MAIN.py (
rem
) else (
echo %CD%В…ВЌMAIN.pyВ™СґНЁВµВ№ВєВс
set /p __=
exit /b
)
echo on
py MAIN.py