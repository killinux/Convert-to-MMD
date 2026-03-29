@echo off
chcp 65001 >nul
cls

echo.
echo ══════════════════════════════════════════════════════════════
echo  XPS to PMX 插件同步脚本
echo ══════════════════════════════════════════════════════════════
echo.

REM 定义源和目标路径
set SOURCE_DIR=E:\mywork\Convert-to-MMD\xps_to_pmx
set TARGET_DIR=C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx
set PYCACHE_DIR=%TARGET_DIR%\__pycache__

REM 检查源文件夹是否存在
if not exist "%SOURCE_DIR%" (
    echo ✗ 错误：源文件夹不存在
    echo   位置：%SOURCE_DIR%
    pause
    exit /b 1
)

echo ✓ 找到源文件夹
echo   源: %SOURCE_DIR%
echo.

REM 删除旧的 __pycache__ 缓存
if exist "%PYCACHE_DIR%" (
    echo 正在清除 Python 缓存...
    rmdir /s /q "%PYCACHE_DIR%" >nul 2>&1
    echo ✓ 缓存已清除
    echo.
)

REM 删除旧的目标文件夹
if exist "%TARGET_DIR%" (
    echo 正在删除旧插件文件夹...
    rmdir /s /q "%TARGET_DIR%" >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo ✓ 旧文件夹已删除
    echo.
)

REM 复制新文件
echo 正在复制文件...
xcopy "%SOURCE_DIR%" "%TARGET_DIR%" /E /I /Y >nul

if %errorlevel% equ 0 (
    echo ✓ 文件复制成功
) else (
    echo ✗ 文件复制失败（错误代码：%errorlevel%）
    pause
    exit /b %errorlevel%
)

echo.

REM 验证
if exist "%TARGET_DIR%\__init__.py" (
    echo ✓ 同步完成！
    echo   目标: %TARGET_DIR%
    echo.
    echo 【下一步】
    echo 1. 完全关闭 Blender（如果打开了的话）
    echo 2. 重新打开 Blender
    echo 3. 在 Python 控制台运行以下代码验证：
    echo.
    echo    import xps_to_pmx
    echo    print(xps_to_pmx.bl_info.get('last_updated'))
    echo.
    echo 应该显示：2026-03-29 12:00:00
) else (
    echo ✗ 验证失败：__init__.py 不存在
)

echo.
echo ══════════════════════════════════════════════════════════════
pause
