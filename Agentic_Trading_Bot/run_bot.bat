@echo off
:: ============================================================
:: run_bot.bat — Launches the Agentic Trading Bot
:: Called by Windows Task Scheduler at 9:00 AM on weekdays
:: ============================================================

set BOT_DIR=C:\Users\cblum2\OneDrive - Babson College\Documents\GitHub\oim3640\Agentic_Trading_Bot
set PYTHON=C:\Users\cblum2\AppData\Local\anaconda3\python.exe
set LOG=%BOT_DIR%\.logs\scheduler.log

:: Load .env variables into this shell session
for /f "tokens=1,2 delims==" %%a in (%BOT_DIR%\.env) do (
    set %%a=%%b
)

cd /d "%BOT_DIR%"
echo [%date% %time%] Bot starting >> "%LOG%"
"%PYTHON%" main.py --mode paper >> "%LOG%" 2>&1
echo [%date% %time%] Bot stopped >> "%LOG%"
