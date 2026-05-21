@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [AUM] 엑셀 동기화 후 GitHub/Streamlit 배포...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_deploy.ps1"
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% neq 0 (
    echo.
    echo 배포 실패. logs\sync_deploy.log 를 확인하세요.
    pause
    exit /b %EXITCODE%
)

echo.
echo 완료. logs\sync_deploy.log 에 기록되었습니다.
timeout /t 3 >nul
exit /b 0
