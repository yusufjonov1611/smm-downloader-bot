@echo off
title SMM Downloader Bot (@smm_downbot)
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [Xatolik] Virtual muhit (.venv) topilmadi!
    pause
    exit /b
)

echo SMM Downloader Bot ishga tushirilmoqda...
.venv\Scripts\python.exe main.py
pause
