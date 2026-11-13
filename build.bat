@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo  BinaryReceptor v3.1.0 - Standalone Windows Build
echo ===================================================

python build.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed with exit code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [DONE] BinaryReceptor.exe is ready in the dist/ folder!
pause
