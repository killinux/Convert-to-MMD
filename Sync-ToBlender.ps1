# XPS to PMX 插件同步脚本 (PowerShell)
#
# 使用方法：
# 1. 在 PowerShell 中运行：
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#    (只需运行一次)
#
# 2. 然后运行这个脚本：
#    .\Sync-ToBlender.ps1

param(
    [switch]$Force = $false,
    [switch]$NoVerify = $false
)

# 设置编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 定义颜色
$SuccessColor = 'Green'
$ErrorColor = 'Red'
$WarningColor = 'Yellow'
$InfoColor = 'Cyan'

# 定义路径
$SourceDir = 'E:\mywork\Convert-to-MMD\xps_to_pmx'
$TargetDir = 'C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx'
$PyCache = Join-Path $TargetDir '__pycache__'

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  XPS to PMX 插件同步脚本" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: 检查源文件夹
Write-Host "📁 检查源文件夹..." -ForegroundColor $InfoColor
if (-not (Test-Path $SourceDir)) {
    Write-Host "✗ 错误：源文件夹不存在" -ForegroundColor $ErrorColor
    Write-Host "  位置：$SourceDir" -ForegroundColor $ErrorColor
    exit 1
}

Write-Host "✓ 找到源文件夹" -ForegroundColor $SuccessColor
Write-Host "  源: $SourceDir" -ForegroundColor White
Write-Host ""

# Step 2: 检查 Blender 是否运行中
Write-Host "🔍 检查 Blender 是否运行..." -ForegroundColor $InfoColor
if (Get-Process blender -ErrorAction SilentlyContinue) {
    Write-Host "⚠ 警告：Blender 正在运行，应该关闭它" -ForegroundColor $WarningColor
    $continue = Read-Host "继续同步吗？(y/n)"
    if ($continue -ne 'y') {
        Write-Host "已取消" -ForegroundColor $WarningColor
        exit 0
    }
} else {
    Write-Host "✓ Blender 未运行" -ForegroundColor $SuccessColor
}
Write-Host ""

# Step 3: 清除 Python 缓存
Write-Host "🧹 清除 Python 缓存..." -ForegroundColor $InfoColor
if (Test-Path $PyCache) {
    Remove-Item -Path $PyCache -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Write-Host "✓ 缓存已清除" -ForegroundColor $SuccessColor
} else {
    Write-Host "ℹ 无缓存需要清除" -ForegroundColor $InfoColor
}
Write-Host ""

# Step 4: 删除旧文件
Write-Host "🗑 删除旧插件文件夹..." -ForegroundColor $InfoColor
if (Test-Path $TargetDir) {
    Remove-Item -Path $TargetDir -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Write-Host "✓ 旧文件夹已删除" -ForegroundColor $SuccessColor
} else {
    Write-Host "ℹ 不存在旧文件夹" -ForegroundColor $InfoColor
}
Write-Host ""

# Step 5: 复制文件
Write-Host "📋 正在复制文件..." -ForegroundColor $InfoColor
try {
    Copy-Item -Path $SourceDir -Destination $TargetDir -Recurse -Force -ErrorAction Stop
    Write-Host "✓ 文件复制成功" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ 文件复制失败：$_" -ForegroundColor $ErrorColor
    exit 1
}
Write-Host ""

# Step 6: 验证
Write-Host "✔ 验证同步结果..." -ForegroundColor $InfoColor
if (Test-Path "$TargetDir\__init__.py") {
    Write-Host "✓ __init__.py 已复制" -ForegroundColor $SuccessColor

    # 检查 last_updated
    $content = Get-Content "$TargetDir\__init__.py" -Raw
    if ($content -like '*last_updated*') {
        Write-Host "✓ last_updated 时间戳已包含" -ForegroundColor $SuccessColor
    } else {
        Write-Host "⚠ 未找到 last_updated 时间戳" -ForegroundColor $WarningColor
    }

    # 检查其他关键文件
    $criticalFiles = @(
        'mapping_ui.py',
        'weights.py',
        'pipeline.py',
        'mapping\data_structures.py',
        'mapping\detection.py'
    )

    Write-Host "✓ 关键文件检查：" -ForegroundColor $SuccessColor
    foreach ($file in $criticalFiles) {
        $filePath = Join-Path $TargetDir $file
        if (Test-Path $filePath) {
            Write-Host "  ✓ $file" -ForegroundColor $SuccessColor
        } else {
            Write-Host "  ✗ $file (缺失)" -ForegroundColor $ErrorColor
        }
    }
} else {
    Write-Host "✗ 验证失败：__init__.py 不存在" -ForegroundColor $ErrorColor
    exit 1
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✓ 同步完成！" -ForegroundColor $SuccessColor
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "【下一步】" -ForegroundColor $InfoColor
Write-Host "1. 完全关闭 Blender（如果打开了的话）" -ForegroundColor White
Write-Host "2. 重新打开 Blender" -ForegroundColor White
Write-Host "3. 在 Python 控制台运行以下代码验证：" -ForegroundColor White
Write-Host ""
Write-Host "   import xps_to_pmx" -ForegroundColor Yellow
Write-Host "   print('最后更新：', xps_to_pmx.bl_info.get('last_updated'))" -ForegroundColor Yellow
Write-Host ""
Write-Host "应该显示：最后更新： 2026-03-29 12:00:00" -ForegroundColor Green
Write-Host ""
