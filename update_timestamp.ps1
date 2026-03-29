# Update timestamp in __init__.py
# Called from sync-full.bat

param(
    [string]$FilePath = "C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__init__.py"
)

if (-not (Test-Path $FilePath)) {
    Write-Host "ERROR: File not found: $FilePath"
    exit 1
}

$now = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')

try {
    $content = Get-Content $FilePath -Raw -Encoding UTF8
    $content = $content -replace '"last_updated":\s*"[^"]*"', ('"last_updated": "' + $now + '"')
    Set-Content -Path $FilePath -Value $content -Encoding UTF8
    Write-Host "Timestamp updated: $now"
} catch {
    Write-Host "ERROR: Failed to update timestamp"
    Write-Host $_.Exception.Message
    exit 1
}
