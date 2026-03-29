# 🔄 XPS to PMX 插件同步脚本

这个脚本可以自动将 E 盘的源代码同步到 Blender 的插件目录。

## 📍 脚本位置

```
E:\mywork\Convert-to-MMD\
├── SYNC_TO_BLENDER.bat        ← 批处理脚本（推荐新手）
└── Sync-ToBlender.ps1         ← PowerShell 脚本（功能更全）
```

---

## 方法 1️⃣：使用批处理脚本（最简单）

### 步骤

1. **打开文件管理器**，导航到：
   ```
   E:\mywork\Convert-to-MMD\
   ```

2. **找到 `SYNC_TO_BLENDER.bat` 文件**

3. **双击运行**（或右键 → 运行）

4. 脚本会自动：
   - ✓ 清除 Python 缓存
   - ✓ 删除旧的插件文件夹
   - ✓ 复制新代码
   - ✓ 验证同步结果

5. **等待脚本完成**，看到这样的消息：
   ```
   ✓ 同步完成！
   ```

### 优点
- 最简单，直接双击
- 不需要任何配置
- 自动清除缓存

---

## 方法 2️⃣：使用 PowerShell 脚本（功能更全）

### 首次设置（仅需一次）

打开 **PowerShell**（Win+X → Windows PowerShell），运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

输入 `Y` 并回车。

### 每次同步

1. 打开 **PowerShell**

2. 导航到脚本目录：
   ```powershell
   cd E:\mywork\Convert-to-MMD
   ```

3. 运行脚本：
   ```powershell
   .\Sync-ToBlender.ps1
   ```

4. 如果 Blender 正在运行，脚本会提示你

### 优点
- 更详细的输出信息
- 自动检测 Blender 是否运行
- 彩色输出，更易读
- 对每个步骤进行验证

---

## 🔍 验证同步成功

### 快速检查

在 **Blender Python 控制台** 中运行：

```python
import xps_to_pmx
print("最后更新：", xps_to_pmx.bl_info.get('last_updated'))
```

**应该显示：**
```
最后更新： 2026-03-29 12:00:00
```

### 完整检查

```python
import xps_to_pmx

print("="*60)
print("XPS to PMX 同步验证")
print("="*60)
print(f"✓ 版本：{xps_to_pmx.bl_info['version']}")
print(f"✓ 最后更新：{xps_to_pmx.bl_info.get('last_updated')}")
print(f"✓ 加载位置：{xps_to_pmx.__file__}")
print("="*60)
```

---

## ⚠️ 常见问题

### Q: 脚本说找不到源文件夹？

**A:** 检查 E 盘路径是否正确：
```
E:\mywork\Convert-to-MMD\xps_to_pmx\
```

如果路径不同，手动编辑脚本中的 `SOURCE_DIR` 变量。

### Q: 脚本运行了，但 Blender 还是看不到新代码？

**A:** 执行以下步骤：

1. 完全关闭 Blender（不是最小化）
2. 等待 5 秒
3. 重新打开 Blender
4. 重新运行同步脚本
5. 再次重启 Blender

### Q: PowerShell 脚本无法运行？

**A:** 确保运行了初始设置：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 同步后 Blender 崩溃？

**A:** 可能是 Python 缓存问题。脚本已经自动清除，但如果还有问题，手动删除：
```
C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__pycache__
```

---

## 📋 工作流程

### 开发代码 → 同步到 Blender → 测试

```
1. 在 E 盘编辑代码
   E:\mywork\Convert-to-MMD\xps_to_pmx\...

2. 运行同步脚本
   ↓ 双击 SYNC_TO_BLENDER.bat
   或
   ↓ 运行 Sync-ToBlender.ps1

3. 关闭并重启 Blender

4. 在 Blender 中测试新代码

5. 如果满意，重复步骤 1-4
```

---

## 🆘 故障排除

### 如果脚本失败，尝试这些：

1. **关闭 Blender**
   - 确保完全退出，检查任务管理器

2. **手动清除缓存**
   ```
   C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__pycache__
   ```
   完全删除这个文件夹

3. **重新运行脚本**

4. **如果还是失败**
   - 手动复制文件：
     ```
     源：E:\mywork\Convert-to-MMD\xps_to_pmx
     目标：C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx
     ```
   - 右键复制源文件夹
   - 导航到目标目录
   - 删除旧的 xps_to_pmx 文件夹
   - 粘贴新的

---

## 💡 提示

- **定期运行同步脚本**保持代码最新
- **在运行脚本前关闭 Blender**以避免文件锁定
- **脚本自动清除 Python 缓存**，不需要手动操作
- **保存脚本快捷方式**到桌面以快速访问

---

**一切就绪！现在你可以在 E 盘编辑代码，然后一键同步到 Blender！** 🚀
