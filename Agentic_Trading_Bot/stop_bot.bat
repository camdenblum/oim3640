@echo off
:: ============================================================
:: stop_bot.bat — Gracefully stops the trading bot
:: Called by Windows Task Scheduler at 4:15 PM on weekdays
:: ============================================================

set LOG=C:\Users\cblum2\OneDrive - Babson College\Documents\GitHub\oim3640\Agentic_Trading_Bot\.logs\scheduler.log

echo [%date% %time%] Scheduler stopping bot >> "%LOG%"

:: Find and kill the python process running main.py
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr "PID:"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%main.py%%'" delete >nul 2>&1
)

:: Fallback: kill any python running main.py by command line match
wmic process where "CommandLine like '%%main.py%%mode paper%%'" delete >nul 2>&1

echo [%date% %time%] Stop signal sent >> "%LOG%"
