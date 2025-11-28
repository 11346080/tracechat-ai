@echo off
chcp 65001 >nul

echo [Frontend] 進入 chat-app 目錄...
cd /d "%~dp0chat-app"
echo [Frontend] 目前所在目錄：%cd%

echo [Frontend] 啟動 npm run dev...
npm run dev
