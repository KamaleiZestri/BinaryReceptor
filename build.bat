@echo off
setlocal
py -3.12 -m pip install -r requirements-build.txt
if errorlevel 1 exit /b %errorlevel%
py -3.12 build.py
exit /b %errorlevel%
