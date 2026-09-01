@echo off
setlocal EnableExtensions
cd /d "%~dp0..\.."

if not exist "build-venv\Scripts\python.exe" (
    echo [ERROR] build-venv missing. Run scripts\create_build_venv.bat first.
    pause
    exit /b 1
)

echo [build] AimSync CS2 Makcu onefile exe — recoil + Makcu + web UI
echo.
build-venv\Scripts\python.exe build_app.py
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Done: dist\AimSyncCS2Makcu.exe
echo Zip:   scripts\package_release.bat
pause
