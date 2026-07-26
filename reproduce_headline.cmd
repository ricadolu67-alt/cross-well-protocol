@echo off
setlocal
python "%~dp0reproduction\recompute_headline.py"
if errorlevel 1 exit /b %errorlevel%
endlocal
