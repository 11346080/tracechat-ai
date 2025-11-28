@echo off
chcp 65001 >nul

echo [Backend] 進入 backend 目錄...
cd /d "%~dp0backend"
echo [Backend] 目前所在目錄：%cd%

if not exist "venv\Scripts\activate.bat" (
    echo [Backend] 找不到 venv，正在建立虛擬環境...
    python -m venv venv
)

echo [Backend] 啟動虛擬環境...
call venv\Scripts\activate

echo [Backend] 啟動 uvicorn...
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
