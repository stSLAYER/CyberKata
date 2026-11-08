@echo off
setlocal
title CyberKata Hydra Lab
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 server.py
    goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python server.py
    goto :done
)

echo.
echo [!] Python 3 was not found.
echo [!] Install it from https://www.python.org/downloads/
echo [!] During setup, tick "Add Python to PATH", then run this file again.
echo.
pause
exit /b 1

:done
if not %errorlevel%==0 pause
