@echo off
if exist BUNKATSU_ONLY.py (
rem
) else (
echo %CD%В…ВЌBUNKATSU_ONLY.pyВ™СґНЁВµВ№ВєВс
set /p __=
exit /b
)
echo on
py BUNKATSU_ONLY.py