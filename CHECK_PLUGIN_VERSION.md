# 如何检查 XPS to PMX 插件版本和更新时间

## 方法 1：在 Blender Preferences 中查看（最简单）

1. 打开 **Edit → Preferences**
2. 进入 **Add-ons** 标签
3. 搜索 **"XPS to PMX"**
4. 点击展开插件条目

你会看到类似这样的信息：

```
✓ XPS to PMX
  Version: 1.0.0
  Location: View3D > Sidebar > XPS to PMX
  Description: Convert XPS rigs to MMD format quickly with flexible mapping system

  【最后更新时间】：2026-03-29 12:00:00
```

**最后更新时间** 就是你要查看的关键信息！

---

## 方法 2：用 Python 脚本检查（更详细）

在 **Blender Python 控制台** 中运行以下代码：

### 快速检查（仅显示版本）

```python
import xps_to_pmx
print("版本：", xps_to_pmx.bl_info['version'])
print("最后更新：", xps_to_pmx.bl_info.get('last_updated', '未设置'))
```

### 完整诊断（显示所有信息）

```python
import sys
sys.path.append('E:\\mywork\\Convert-to-MMD')
from xps_to_pmx import check_version
check_version.show_plugin_info()        # 显示基本信息
check_version.check_core_modules()      # 检查所有模块
check_version.check_ui_registration()   # 检查 UI 组件
```

---

## 方法 3：直接查看源代码

打开插件文件：
```
C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx\__init__.py
```

找到 `bl_info` 字典，第一部分就是版本信息：

```python
bl_info = {
    "name": "XPS to PMX",
    "author": "Claude",
    "version": (1, 0, 0),                    ← 版本号
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > XPS to PMX",
    "description": "Convert XPS rigs to MMD format quickly with flexible mapping system",
    "category": "Import-Export",
    "last_updated": "2026-03-29 12:00:00",  ← 最后更新时间！
}
```

---

## 版本更新历史

| 更新时间 | 版本 | 变更内容 |
|---------|------|---------|
| 2026-03-29 12:00:00 | 1.0.0 | 完成灵活映射系统、权重规则系统、4面板UI |

---

## 如何检查是否有最新代码

### 场景 1：你正在工作，想检查插件是否是最新的

```
在 Blender Preferences 中查看 "last_updated" 时间
↓
与你本地文件的修改时间对比
↓
如果本地文件时间更新，说明有新代码还没加载
→ 重启 Blender 重新加载插件
```

### 场景 2：有人给了你新代码，想检查插件是否已更新

```
1. 将新代码复制到 addons 目录
2. 重启 Blender
3. 在 Preferences 中查看 last_updated 时间
4. 对比时间是否更新
```

---

## 快速参考

| 位置 | 版本信息 |
|------|---------|
| **Preferences** | Edit → Preferences → Add-ons → XPS to PMX |
| **Python 脚本** | `xps_to_pmx.bl_info['last_updated']` |
| **源代码** | `xps_to_pmx/__init__.py` 的 `bl_info` 字典 |
| **文件属性** | 右键 → 属性 → 修改日期（Windows） |

---

## 🔔 自动更新检查脚本（可选）

将以下脚本保存为 Python 文件，用于自动检查更新：

```python
import xps_to_pmx
from datetime import datetime

current_version = xps_to_pmx.bl_info['version']
last_updated = xps_to_pmx.bl_info.get('last_updated', 'Unknown')

print(f"当前版本: {'.'.join(map(str, current_version))}")
print(f"最后更新: {last_updated}")

# 可以与远程服务器对比，判断是否需要更新
# （本版本暂不实现）
```

---

**提示：** 每次有重大更新时，`last_updated` 时间戳会自动更新。这样你可以快速检查插件是否是最新代码！
