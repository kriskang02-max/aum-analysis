@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo [AUM] Excel sync and deploy to GitHub / Streamlit...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_deploy.ps1"
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% neq 0 (
    echo.
    echo FAILED. See logs\sync_deploy.log
    pause
    exit /b %EXITCODE%
)

echo.
echo Done. See logs\sync_deploy.log
timeout /t 4 >nul
exit /b 0
