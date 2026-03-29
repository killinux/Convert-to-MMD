# ⏰ 时间戳更新 - 完整解决方案

## 问题
同步后，Blender 面板中的时间戳没有更新。

## 根本原因
Blender 的 Python 模块缓存（`__pycache__`）导致旧版本的代码仍然被加载。

---

## ✅ 完整解决步骤

### 步骤 1：完全关闭 Blender
```
1. 关闭 Blender 主窗口
2. 检查任务管理器（Ctrl+Shift+Esc）
3. 如果还有 blender.exe 进程，右键 → 结束任务
```

### 步骤 2：清除缓存
运行清除脚本：
```
双击：E:\mywork\Convert-to-MMD\clear_cache.bat
```

或者手动删除：
```
C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__pycache__
```

### 步骤 3：重新打开 Blender
```
1. 重新启动 Blender
2. 打开 XPS to PMX Mapper 面板
3. 查看 ① AUTO DETECTION 面板顶部的时间戳
4. 应该显示最新的时间戳！
```

---

## 🔄 以后的同步流程

为了避免这个问题，每次修改代码后按以下步骤：

### 推荐流程 A（最安全）
```
1. 编辑 E:\mywork\Convert-to-MMD\xps_to_pmx\ 中的代码
2. 关闭 Blender
3. 双击 clear_cache.bat（清除缓存）
4. 双击 sync.bat（同步代码）
5. 重新打开 Blender
6. 验证时间戳
```

### 快速流程 B（稍快）
```
1. 编辑代码
2. 关闭 Blender
3. 双击 sync-full.bat（一次完成所有操作）
4. 重新打开 Blender
```

---

## 现在的状态

当前源文件时间戳已更新为：
```
"last_updated": "2026-03-29 11:19:38"
```

**现在需要你做：**

1. ✅ **关闭 Blender 完全**
2. ✅ **双击 clear_cache.bat**（位置：E:\mywork\Convert-to-MMD\）
3. ✅ **重新打开 Blender**
4. ✅ **查看时间戳** - 应该显示 `2026-03-29 11:19:38`

---

## 验证方式

### 方法 1：在 Blender 面板中查看（最直观）
```
XPS to PMX Mapper → ① AUTO DETECTION

应该显示：
Plugin v1.0.0
Updated: 2026-03-29 11:19:38 ✓
```

### 方法 2：在 Python 控制台验证
打开 Blender → Python 控制台（顶部菜单）：
```python
import xps_to_pmx
print(xps_to_pmx.bl_info['last_updated'])
# 应该打印：2026-03-29 11:19:38
```

### 方法 3：查看文件
```
C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__init__.py

应该包含：
"last_updated": "2026-03-29 11:19:38"
```

---

## 如果还是不对

### 检查清单
- [ ] Blender 完全关闭了吗？（任务管理器中看不到 blender.exe）
- [ ] __pycache__ 文件夹真的被删除了吗？
- [ ] Blender 重新打开后等待 5 秒让它加载？
- [ ] 确实是选中了骨架才打开的面板？

### 如果都检查过了还是不对

手动更新时间戳：

1. 打开文件编辑器：
   ```
   C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__init__.py
   ```

2. 找到第 21 行（大约）：
   ```python
   "last_updated": "2026-03-29 11:19:38",
   ```

3. 手动改为当前时间，保存

4. 重新打开 Blender 验证

---

## 自动更新脚本（将来使用）

我会创建一个 `sync-full.bat` 脚本，自动完成：
- 清除缓存
- 复制文件
- 更新时间戳

这样以后只需双击一个脚本就可以了。

---

**现在就试试吧！** 按照上面的三个步骤做，时间戳应该就会显示正确了。
