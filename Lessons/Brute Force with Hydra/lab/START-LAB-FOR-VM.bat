@echo off
setlocal
title CyberKata Hydra Lab - VM Mode
cd /d "%~dp0"

echo.
echo ================================================================
echo   WARNING: VM MODE LISTENS ON YOUR LOCAL NETWORK
echo ================================================================
echo   Use this only when Hydra runs inside a Kali virtual machine.
echo   Keep the lab on a trusted network and stop it after training.
echo ================================================================
echo.
pause

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 server.py --host 0.0.0.0
    goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python server.py --host 0.0.0.0
    goto :done
)

echo.
echo [!] Python 3 was not found. See README.md for installation help.
pause
exit /b 1

:done
if not %errorlevel%==0 pause
