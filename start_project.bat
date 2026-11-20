@echo off
title SmartEnergy AI

cd /d "%~dp0"

echo Starting SmartEnergy AI...
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b
)

start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000/"

".venv\Scripts\python.exe" app.py

echo.
echo Flask server stopped.
pause