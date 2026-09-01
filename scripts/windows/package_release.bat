@echo off

setlocal EnableExtensions

cd /d "%~dp0..\.."

set "EXE=AimSyncCS2Makcu.exe"
set "ZIP=AimSyncCS2Makcu.zip"
set "DIR=AimSyncCS2Makcu"

if exist "dist\%EXE%" goto :onefile

if exist "dist\%DIR%\%EXE%" goto :onedir

echo [ERROR] No build found - run scripts\build_app.bat first.

exit /b 1



:onefile

if exist "dist\%ZIP%" del /f "dist\%ZIP%"

powershell -NoProfile -Command "Compress-Archive -LiteralPath 'dist\%EXE%' -DestinationPath 'dist\%ZIP%' -Force"

if errorlevel 1 (

    echo [WARN] zip failed - exe ready: dist\%EXE%

    exit /b 1

)

echo Created: dist\%ZIP%  (contains %EXE% only)

exit /b 0



:onedir

if exist "dist\%ZIP%" del /f "dist\%ZIP%"

powershell -NoProfile -Command "Compress-Archive -LiteralPath 'dist\%DIR%' -DestinationPath 'dist\%ZIP%' -Force"

if errorlevel 1 (

    echo [WARN] zip failed - folder ready: dist\%DIR%\

    exit /b 1

)

echo Created: dist\%ZIP%  (full onedir bundle)

exit /b 0
