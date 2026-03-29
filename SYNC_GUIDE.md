# 🔄 XPS to PMX 插件同步指南

## 快速开始

### 方法 1：使用 Batch 脚本（推荐 - 最简单）

```
E:\mywork\Convert-to-MMD\sync.bat
```

**步骤：**
1. 双击运行 `sync.bat`
2. 脚本会：
   - ✓ 清除 Python 缓存
   - ✓ 删除旧插件文件
   - ✓ 复制新代码
   - ✓ **自动更新时间戳**（关键！）
   - ✓ 显示新的版本信息
3. 关闭 Blender 后重新打开
4. 在 "XPS to PMX Mapper" 面板顶部看到最新的时间戳

---

## 方法 2：使用 PowerShell 脚本

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后运行：
```powershell
E:\mywork\Convert-to-MMD\Sync-Update-Timestamp.ps1
```

---

## 时间戳验证

### 在 Blender 中验证

同步后，打开 Blender：

1. 打开 **XPS to PMX Mapper** 面板
2. 在 **① AUTO DETECTION** 面板顶部查看：
   ```
   Plugin v1.0.0
   Updated: 2026-03-29 HH:MM:SS  ← 应该是当前时间
   ```

### 在 Python 控制台验证

```python
import xps_to_pmx
print(xps_to_pmx.bl_info['last_updated'])
# 应该显示当前时间，如：2026-03-29 14:45:23
```

---

## 使用流程

每次修改代码后：

```
1. 编辑 E:\mywork\Convert-to-MMD\xps_to_pmx\ 中的代码
   ↓
2. 双击运行 sync.bat
   ↓
3. 关闭并重启 Blender
   ↓
4. 验证 XPS to PMX Mapper 面板显示最新时间戳
   ↓
5. 开始使用新功能
```

---

## 故障排除

### 问题：sync.bat 运行后时间戳仍然不对

**解决：**
1. 确保 PowerShell 可用（Windows 10+ 自带）
2. 确保 Blender 完全关闭（不是后台运行）
3. 等待 5 秒后重新打开 Blender
4. 清除浏览器缓存（如适用）

### 问题：PowerShell 脚本无法运行

**解决：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

输入 `Y` 确认后重试。

### 问题：找不到 sync.bat

**位置：**
```
E:\mywork\Convert-to-MMD\
```

应该看到：
- ✓ sync.bat (推荐)
- ✓ Sync-Update-Timestamp.ps1
- ✓ SYNC_GUIDE.md (本文件)

---

## 技术细节

### sync.bat 做了什么

```batch
1. 检查源文件夹 (E:\mywork\Convert-to-MMD\xps_to_pmx)
2. 清除 Python 缓存 (__pycache__)
3. 删除旧的插件文件夹
4. 使用 xcopy 复制新文件到 Blender 插件目录
5. 使用 PowerShell 更新 __init__.py 中的时间戳
6. 显示更新后的时间戳以验证成功
```

### 自动时间戳更新原理

脚本使用 PowerShell 的 `Get-Date` 和正则表达式替换：

```powershell
# 获取当前时间
$now = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')

# 读取文件并替换时间戳
$content = Get-Content $file -Raw
$content = $content -replace '"last_updated":\s*"[^"]*"', ('"last_updated": "' + $now + '"')

# 写回文件
Set-Content -Path $file -Value $content -Encoding UTF8
```

---

## 快速参考

| 任务 | 命令 |
|------|------|
| 同步代码和更新时间戳 | 双击 `sync.bat` |
| 完整同步（PowerShell） | 运行 `Sync-Update-Timestamp.ps1` |
| 查看当前时间戳 | Blender → XPS to PMX Mapper → ① AUTO DETECTION |
| 验证 Python 中的时间戳 | `print(xps_to_pmx.bl_info['last_updated'])` |

---

**提示：** 每次修改代码后，记得运行 sync.bat 以同步到 Blender！
