@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo [AUM] Raw data 파일명 변경 (공모/사모/일임_YYMMDD.xlsx)
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0rename_raw_data.ps1"
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% neq 0 (
    echo.
    echo 실패.
) else (
    echo.
    echo 완료.
)
pause
exit /b %EXITCODE%
