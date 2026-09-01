@echo off
setlocal EnableExtensions
cd /d "%~dp0..\.."

echo AimSync CS2 Makcu - first-time setup
echo.

call "%~dp0_ensure_venv.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Done. Use scripts\run.bat for production (Makcu).
pause
