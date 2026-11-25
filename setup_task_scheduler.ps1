# Registers a daily 8:00 PM Windows Task Scheduler job for run_daily.py
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = (Get-Command python).Source
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ProjectDir\run_daily.py`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00PM
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "ZahidArduinoShortsDaily" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily 8 PM Arduino/ESP32 YouTube Shorts uploader" -Force
Write-Host "Scheduled task 'ZahidArduinoShortsDaily' registered for 8:00 PM daily!"
