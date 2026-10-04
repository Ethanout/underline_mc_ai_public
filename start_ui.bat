@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 同步 NapCat 配置 -> 起 web -> 起 NapCat。配置只在 .env 里改。
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m qqbot start %*
) else (
  py -3 -m qqbot start %*
)
pause
