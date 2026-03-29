@echo off
REM Clear Blender cache for xps_to_pmx addon
REM English only - no Chinese characters!

setlocal enabledelayedexpansion

set "CACHE_DIR=C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__pycache__"

echo.
echo ========== Clearing Blender Cache ==========
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

echo Blender is not running. OK!
echo.

REM Delete cache
if exist "%CACHE_DIR%" (
    echo Deleting cache folder...
    rmdir /s /q "%CACHE_DIR%"
    if %errorlevel% equ 0 (
        echo Cache deleted successfully.
    ) else (
        echo Warning: Could not delete some cache files.
    )
) else (
    echo Cache folder does not exist (already clean).
)

echo.
echo Cache cleared!
echo.
echo Next steps:
echo 1. Reopen Blender
echo 2. Open XPS to PMX Mapper panel
echo 3. Check timestamp at the top
echo.
pause
