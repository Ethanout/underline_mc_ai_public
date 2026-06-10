@echo off
cd /d "%~dp0"

echo Starting MC Knowledge Base...
echo.

start "" "C:\Users\26297\AppData\Local\Programs\Python\Python313\python.exe" app.py

echo ========================================
echo   MC 知识库已启动
echo   浏览器打开 http://127.0.0.1:8765
echo   关闭此窗口停止服务
echo ========================================

start http://127.0.0.1:8765

rem 等待服务启动后打开浏览器
timeout /t 3 /nobreak >nul
start http://127.0.0.1:8765
rem Keep window open
pause >nul
