@echo off
chcp 65001 >nul

echo 根目錄：%~dp0
echo 將開啟兩個視窗：backend、frontend
echo.

start "backend"  cmd /k "%~dp0backend-run.bat"
start "frontend" cmd /k "%~dp0frontend-run.bat"

echo.
echo 已嘗試啟動：
echo - Backend:  http://localhost:8000/docs
echo - Frontend: http://localhost:3000
echo.
pause
