@echo off
if exist weather_monitor.pid (
    set /p PID=<weather_monitor.pid
    echo Stopping Weather Monitor background process with PID: %PID%...
    taskkill /F /PID %PID%
    del weather_monitor.pid
    echo Stopped successfully.
) else (
    echo Weather Monitor is not running (no weather_monitor.pid file found).
)
pause
