@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [AUM] 엑셀/데이터 변경 감시 후 자동 배포 (5분마다). 종료: Ctrl+C
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_deploy.ps1" -Watch -WatchIntervalSec 300
pause
