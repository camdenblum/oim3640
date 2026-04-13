# ============================================================
# setup_schedule.ps1
# RIGHT-CLICK this file → "Run with PowerShell" (as Administrator)
# Registers the trading bot to start at 9:00 AM and stop at 4:15 PM
# on every weekday (Mon–Fri) automatically.
# ============================================================

$botDir = "C:\Users\cblum2\OneDrive - Babson College\Documents\GitHub\oim3640\Agentic_Trading_Bot"

Write-Host "Registering Trading Bot scheduled tasks..." -ForegroundColor Cyan

# --- START task: 9:00 AM Mon-Fri ---
$startAction  = New-ScheduledTaskAction `
    -Execute "$botDir\run_bot.bat" `
    -WorkingDirectory $botDir

$startTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "09:00AM"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 8) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable $true   # catches up if PC was off at 9 AM

Register-ScheduledTask `
    -TaskName    "TradingBot_Start" `
    -Action      $startAction `
    -Trigger     $startTrigger `
    -Settings    $settings `
    -RunLevel    Highest `
    -Description "Starts the Agentic Trading Bot at market open (Mon-Fri 9:00 AM)" `
    -Force

Write-Host "  [OK] TradingBot_Start registered (9:00 AM Mon-Fri)" -ForegroundColor Green

# --- STOP task: 4:15 PM Mon-Fri ---
$stopAction  = New-ScheduledTaskAction `
    -Execute "$botDir\stop_bot.bat" `
    -WorkingDirectory $botDir

$stopTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "04:15PM"

Register-ScheduledTask `
    -TaskName    "TradingBot_Stop" `
    -Action      $stopAction `
    -Trigger     $stopTrigger `
    -Settings    $settings `
    -RunLevel    Highest `
    -Description "Stops the Agentic Trading Bot after market close (Mon-Fri 4:15 PM)" `
    -Force

Write-Host "  [OK] TradingBot_Stop registered (4:15 PM Mon-Fri)" -ForegroundColor Green
Write-Host ""
Write-Host "Done! The bot will now start automatically every weekday morning." -ForegroundColor Cyan
Write-Host "You can view/edit the tasks in: Task Scheduler -> Task Scheduler Library" -ForegroundColor Yellow
Write-Host ""
Write-Host "To remove the tasks later, run:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName TradingBot_Start -Confirm:`$false"
Write-Host "  Unregister-ScheduledTask -TaskName TradingBot_Stop  -Confirm:`$false"

Read-Host "Press Enter to close"
