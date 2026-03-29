# XPS to PMX Plugin Sync Script with Auto Timestamp Update
# Usage: Run this script to sync code and automatically update version timestamp

param(
    [switch]$UpdateTimestamp = $true
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Define colors
$SuccessColor = 'Green'
$ErrorColor = 'Red'
$WarningColor = 'Yellow'
$InfoColor = 'Cyan'

# Define paths
$SourceDir = 'E:\mywork\Convert-to-MMD\xps_to_pmx'
$TargetDir = 'C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx'
$PyCache = Join-Path $TargetDir '__pycache__'
$InitFile = Join-Path $TargetDir '__init__.py'

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  XPS to PMX 插件同步脚本 (带时间戳更新)" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check source folder
Write-Host "📁 检查源文件夹..." -ForegroundColor $InfoColor
if (-not (Test-Path $SourceDir)) {
    Write-Host "✗ 错误：源文件夹不存在" -ForegroundColor $ErrorColor
    Write-Host "  位置：$SourceDir" -ForegroundColor $ErrorColor
    exit 1
}

Write-Host "✓ 找到源文件夹" -ForegroundColor $SuccessColor
Write-Host "  源: $SourceDir" -ForegroundColor White
Write-Host ""

# Step 2: Clear Python cache
Write-Host "🧹 清除 Python 缓存..." -ForegroundColor $InfoColor
if (Test-Path $PyCache) {
    Remove-Item -Path $PyCache -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Write-Host "✓ 缓存已清除" -ForegroundColor $SuccessColor
} else {
    Write-Host "ℹ 无缓存需要清除" -ForegroundColor $InfoColor
}
Write-Host ""

# Step 3: Delete old target folder
Write-Host "🗑 删除旧插件文件夹..." -ForegroundColor $InfoColor
if (Test-Path $TargetDir) {
    Remove-Item -Path $TargetDir -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Write-Host "✓ 旧文件夹已删除" -ForegroundColor $SuccessColor
} else {
    Write-Host "ℹ 不存在旧文件夹" -ForegroundColor $InfoColor
}
Write-Host ""

# Step 4: Copy files
Write-Host "📋 正在复制文件..." -ForegroundColor $InfoColor
try {
    Copy-Item -Path $SourceDir -Destination $TargetDir -Recurse -Force -ErrorAction Stop
    Write-Host "✓ 文件复制成功" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ 文件复制失败：$_" -ForegroundColor $ErrorColor
    exit 1
}
Write-Host ""

# Step 5: Update timestamp if requested
if ($UpdateTimestamp) {
    Write-Host "⏰ 更新版本时间戳..." -ForegroundColor $InfoColor

    if (Test-Path $InitFile) {
        # Get current timestamp
        $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

        # Read file content
        $content = Get-Content $InitFile -Raw

        # Replace timestamp
        $content = $content -replace '"last_updated":\s*"[^"]*"', "`"last_updated`": `"$now`""

        # Write back
        Set-Content -Path $InitFile -Value $content -Encoding UTF8

        Write-Host "✓ 时间戳已更新: $now" -ForegroundColor $SuccessColor
    } else {
        Write-Host "⚠ __init__.py 文件不存在，无法更新时间戳" -ForegroundColor $WarningColor
    }
    Write-Host ""
}

# Step 6: Verify
Write-Host "✔ 验证同步结果..." -ForegroundColor $InfoColor
if (Test-Path "$TargetDir\__init__.py") {
    Write-Host "✓ __init__.py 已复制" -ForegroundColor $SuccessColor

    # Display current timestamp
    $content = Get-Content "$TargetDir\__init__.py" -Raw
    if ($content -match '"last_updated":\s*"([^"]*)"') {
        $timestamp = $matches[1]
        Write-Host "✓ 当前时间戳: $timestamp" -ForegroundColor $SuccessColor
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
Write-Host "3. 打开 XPS to PMX Mapper 面板" -ForegroundColor White
Write-Host "4. 在面板顶部应该看到最新的版本时间戳" -ForegroundColor White
Write-Host ""
Write-Host "版本信息会显示在 ① AUTO DETECTION 面板的顶部：" -ForegroundColor White
Write-Host "   Plugin v1.0.0" -ForegroundColor Yellow
Write-Host "   Updated: $timestamp" -ForegroundColor Yellow
Write-Host ""
