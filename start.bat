@echo off
title KaraokePro
echo ========================================
echo        KaraokePro - Starting Up
echo ========================================
echo.

:: Check for Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Download it from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Install/update dependencies
echo Installing dependencies...
py -m pip install -r requirements.txt --quiet
echo.

:: Launch
echo Starting server...
echo The app will open in your browser automatically.
echo.
echo Press Ctrl+C to stop the server when you're done.
echo.
py main.py
pause
