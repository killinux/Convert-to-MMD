# 🚀 快速开始 - 同步脚本使用

## ❌ 不需要 Python！

所有脚本现在只需要：
- ✅ Windows 10+ 自带的 PowerShell
- ✅ 基础的 batch 命令
- ❌ **不需要 Python**

---

## 🎯 最简单的方法

### 步骤 1：关闭 Blender
```
完全关闭 Blender（不是最小化）
```

### 步骤 2：运行同步脚本
```
双击：E:\mywork\Convert-to-MMD\sync-full.bat
```

脚本会自动：
- ✓ 清除 Python 缓存
- ✓ 复制新文件
- ✓ 更新时间戳
- ✓ 显示最新时间戳

### 步骤 3：重新打开 Blender
```
打开 Blender
```

### 步骤 4：验证时间戳
```
XPS to PMX Mapper 面板 → ① AUTO DETECTION

应该显示：
  Plugin v1.0.0
  Updated: 2026-03-29 HH:MM:SS (当前时间)
```

---

## 📁 可用脚本

| 脚本文件 | 功能 | 何时用 |
|---------|------|-------|
| `sync-full.bat` | 完整同步（推荐） | 每次修改代码 |
| `sync.bat` | 快速同步 | 只更新文件 |
| `clear_cache.bat` | 仅清除缓存 | 时间戳不更新时 |
| `Sync-Update-Timestamp.ps1` | PowerShell 脚本 | 高级用户 |

---

## 🔧 故障排除

### 问题：脚本显示找不到 Python
**解决：** 不需要担心！新版脚本不需要 Python。

只需确保：
- [ ] Windows PowerShell 可用（Win+X → Windows PowerShell）
- [ ] 以管理员身份运行脚本（右键 → 以管理员身份运行）

### 问题：时间戳仍然不更新
**解决步骤：**
```
1. 确保 Blender 完全关闭（任务管理器查看）
2. 双击 clear_cache.bat
3. 双击 sync-full.bat
4. 关闭后 5 秒再打开 Blender
```

### 问题：PowerShell 脚本无法运行
**解决：** 在 PowerShell 中运行一次：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

输入 `Y` 并按 Enter。

---

## 💡 使用提示

### 推荐工作流
```
1. 编辑代码（在 E:\mywork\Convert-to-MMD\xps_to_pmx\）
2. 关闭 Blender
3. 双击 sync-full.bat
4. 打开 Blender
5. 验证时间戳
6. 继续工作
```

### 快速更新
如果只改了几行代码，可以只运行：
```
sync.bat（不清除缓存，更快）
```

### 确保更新生效
如果改了核心文件（__init__.py、mapping_ui.py 等），务必使用：
```
sync-full.bat（完整清除+更新）
```

---

## ✅ 验证清单

每次同步后检查：

- [ ] Blender 中 XPS to PMX Mapper 面板可以打开
- [ ] ① AUTO DETECTION 面板顶部显示时间戳
- [ ] 时间戳是当前时间（不是旧时间）
- [ ] 面板中的改进（如完整的骨骼列表）生效了

---

## 🆘 如果还有问题

运行 PowerShell 测试：

```powershell
# 打开 PowerShell
$file = "C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__init__.py"
$content = Get-Content $file -Raw
$content -match '"last_updated":\s*"([^"]*)"'
Write-Host "当前时间戳: $($matches[1])"
```

应该显示最新的时间戳。

---

**现在就试试 sync-full.bat 吧！** 🎉
