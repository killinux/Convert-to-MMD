@echo off
REM XPS to PMX Sync Script
REM Simple and reliable version - English only!

setlocal enabledelayedexpansion

set "SOURCE=E:\mywork\Convert-to-MMD\xps_to_pmx"
set "TARGET=C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx"
set "INIT_FILE=%TARGET%\__init__.py"

echo.
echo ========== XPS to PMX Sync ==========
echo.

REM Check source exists
if not exist "%SOURCE%" (
    echo ERROR: Source folder not found
    echo %SOURCE%
    pause
    exit /b 1
)

echo Source: %SOURCE%
echo.

REM Remove __pycache__
if exist "%TARGET%\__pycache__" (
    echo Removing cache...
    rmdir /s /q "%TARGET%\__pycache__" >nul 2>&1
    echo Cache removed.
)

REM Remove old target
if exist "%TARGET%" (
    echo Removing old files...
    rmdir /s /q "%TARGET%" >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo Old files removed.
)

REM Copy new files
echo Copying files...
xcopy "%SOURCE%" "%TARGET%" /E /I /Y >nul 2>&1

if %errorlevel% equ 0 (
    echo.
    echo Updating timestamp...

    REM Update timestamp using PowerShell script
    powershell -NoProfile -ExecutionPolicy Bypass -File "E:\mywork\Convert-to-MMD\update_timestamp.ps1" -FilePath "%INIT_FILE%"

    echo.
    echo SUCCESS! Sync complete.
    echo Target: %TARGET%
    echo.
    REM Display the new timestamp
    for /f "tokens=*" %%A in ('findstr "last_updated" "%TARGET%\__init__.py"') do (
        echo Current version: %%A
    )
    echo.
    echo Next steps:
    echo 1. Close Blender completely
    echo 2. Reopen Blender
    echo 3. Open "XPS to PMX Mapper" panel
    echo 4. You should see the version and timestamp at the top
) else (
    echo ERROR during copy
)

echo.
pause
