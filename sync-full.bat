@echo off
REM XPS to PMX Full Sync Script
REM Clears cache + copies files + updates timestamp
REM NO Chinese characters - pure English commands only!

setlocal enabledelayedexpansion

set "SOURCE=E:\mywork\Convert-to-MMD\xps_to_pmx"
set "TARGET=C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx"
set "CACHE=%TARGET%\__pycache__"
set "INIT_FILE=%TARGET%\__init__.py"

cls
echo.
echo ================================================================
echo  XPS to PMX Sync Script - Full Update
echo ================================================================
echo.

REM Check if Blender is running
tasklist /FI "IMAGENAME eq blender.exe" 2>NUL | find /I /N "blender.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ERROR: Blender is still running!
    echo Please close Blender completely and run this script again.
    echo.
    pause
    exit /b 1
)

echo OK: Blender is not running
echo.

REM Check source
if not exist "%SOURCE%" (
    echo ERROR: Source folder not found
    echo Location: %SOURCE%
    pause
    exit /b 1
)

echo Source: %SOURCE%
echo.

REM Step 1: Clear cache
echo Step 1: Clearing Python cache...
if exist "%CACHE%" (
    rmdir /s /q "%CACHE%" >nul 2>&1
    echo   Cache cleared
) else (
    echo   Cache folder not found (already clean)
)
echo.

REM Step 2: Delete old target
echo Step 2: Deleting old addon folder...
if exist "%TARGET%" (
    rmdir /s /q "%TARGET%" >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo   Old folder deleted
) else (
    echo   Old folder does not exist
)
echo.

REM Step 3: Copy new files
echo Step 3: Copying new files...
xcopy "%SOURCE%" "%TARGET%" /E /I /Y >nul 2>&1
if %errorlevel% equ 0 (
    echo   Files copied successfully
) else (
    echo   ERROR: Failed to copy files!
    pause
    exit /b 1
)
echo.

REM Step 4: Update timestamp using PowerShell script
echo Step 4: Updating timestamp...

powershell -NoProfile -ExecutionPolicy Bypass -File "E:\mywork\Convert-to-MMD\update_timestamp.ps1" -FilePath "%INIT_FILE%"

if %errorlevel% equ 0 (
    echo   Success
) else (
    echo   Warning: Timestamp update may have failed
)
echo.

REM Step 5: Verify
echo Step 5: Verifying sync...
if exist "%INIT_FILE%" (
    echo   __init__.py copied
    echo.
    echo   Current version info:
    for /f "tokens=*" %%A in ('findstr "last_updated" "%INIT_FILE%"') do (
        echo   %%A
    )
) else (
    echo   ERROR: __init__.py not found!
    pause
    exit /b 1
)
echo.

echo ================================================================
echo SUCCESS: Sync Complete!
echo ================================================================
echo.
echo Next steps:
echo 1. Reopen Blender
echo 2. Open XPS to PMX Mapper panel
echo 3. Check timestamp at the top of AUTO DETECTION panel
echo 4. Should show: Updated: 2026-03-29 HH:MM:SS (current time)
echo.
pause
