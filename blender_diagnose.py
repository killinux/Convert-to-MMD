"""
Blender XPS to PMX 插件诊断脚本
在 Blender Python 控制台中运行此脚本来诊断问题
"""

import bpy

print("\n" + "="*60)
print("🔍 XPS to PMX 插件诊断开始")
print("="*60 + "\n")

# 1. 检查插件是否启用
print("1️⃣ 检查插件状态...")
addon_name = "xps_to_pmx"
is_enabled = addon_name in bpy.context.preferences.addons

if is_enabled:
    addon = bpy.context.preferences.addons[addon_name]
    print(f"   ✅ 插件已启用: {addon_name}")
    if hasattr(addon, 'bl_info'):
        print(f"   版本: {addon.bl_info.get('version')}")
        print(f"   最后更新: {addon.bl_info.get('last_updated')}")
else:
    print(f"   ❌ 插件未启用: {addon_name}")
    print("   请在 Edit → Preferences → Add-ons 中启用此插件")

# 2. 检查模块是否可以导入
print("\n2️⃣ 检查模块导入...")
try:
    import xps_to_pmx
    print("   ✅ xps_to_pmx 模块可以导入")

    # 检查子模块
    try:
        from xps_to_pmx import mapping_ui
        print("   ✅ mapping_ui 模块可用")
    except ImportError as e:
        print(f"   ❌ mapping_ui 导入失败: {e}")

    try:
        from xps_to_pmx import mmd_bone_tree_ui
        print("   ✅ mmd_bone_tree_ui 模块可用")
    except ImportError as e:
        print(f"   ❌ mmd_bone_tree_ui 导入失败: {e}")

except ImportError as e:
    print(f"   ❌ xps_to_pmx 模块导入失败: {e}")

# 3. 检查操作符是否注册
print("\n3️⃣ 检查操作符注册...")
operators = [
    "xpspmx_tree.toggle_expand",
    "xpspmx_tree.expand_all",
    "xpspmx_tree.collapse_all",
    "xpspmx_tree.select_bone",
    "xpspmx_mapper.edit_mapping",  # 关键操作符！
    "xpspmx_mapper.auto_map_bones",
]

for op_name in operators:
    try:
        op = getattr(bpy.ops, op_name.replace(".", "_"))
        print(f"   ✅ {op_name} - 已注册")
    except AttributeError:
        print(f"   ❌ {op_name} - 未注册或无法访问")

# 4. 检查 UI 面板是否注册
print("\n4️⃣ 检查 UI 面板注册...")
panel_classes = [
    "XPSPMX_PT_mmd_bone_tree",
    "XPSPMX_PT_unmapped_bones",
    "XPSPMX_PT_bone_detail",  # 包含编辑按钮的面板
]

for panel_name in panel_classes:
    panel_class = getattr(bpy.types, panel_name, None)
    if panel_class:
        print(f"   ✅ {panel_name} - 已注册")
        if hasattr(panel_class, 'bl_label'):
            print(f"      标签: {panel_class.bl_label}")
    else:
        print(f"   ❌ {panel_name} - 未找到")

# 5. 检查场景属性
print("\n5️⃣ 检查场景属性...")
scene = bpy.context.scene
if hasattr(scene, 'xpspmx_bone_tree_props'):
    print("   ✅ xpspmx_bone_tree_props 属性已注册")
    props = scene.xpspmx_bone_tree_props
    print(f"      - bone_tree_search: {props.bone_tree_search}")
    print(f"      - display_mode: {props.display_mode}")
    print(f"      - detail_panel_bone: {props.detail_panel_bone}")
else:
    print("   ❌ xpspmx_bone_tree_props 属性未找到")

# 6. 检查全局配置
print("\n6️⃣ 检查全局配置...")
try:
    from xps_to_pmx import mapping_ui
    config = mapping_ui._GLOBAL_CONFIG.get('config')
    if config:
        print(f"   ✅ 全局配置存在")
        print(f"      骨骼映射数: {len(config.bone_mappings)}")
    else:
        print("   ⚠️ 全局配置为空（需要运行 Auto Map Bones）")
except Exception as e:
    print(f"   ❌ 无法访问全局配置: {e}")

# 7. 检查 MMD 标准骨骼文件
print("\n7️⃣ 检查 MMD 标准骨骼文件...")
import os
import json

try:
    addon_path = os.path.dirname(xps_to_pmx.__file__)
    mmd_skeleton_path = os.path.join(
        addon_path, 'mapping', 'presets', 'mmd_standard_skeleton.json'
    )

    if os.path.exists(mmd_skeleton_path):
        with open(mmd_skeleton_path, 'r', encoding='utf-8') as f:
            mmd_data = json.load(f)
            bones_count = len(mmd_data.get('bones', {}))
            print(f"   ✅ MMD 骨骼文件存在")
            print(f"      MMD 骨骼数: {bones_count}")
    else:
        print(f"   ❌ MMD 骨骼文件未找到: {mmd_skeleton_path}")
except Exception as e:
    print(f"   ❌ 无法读取 MMD 骨骼文件: {e}")

# 8. 检查"骨骼详情"面板中的编辑按钮
print("\n8️⃣ 检查'骨骼详情'面板代码...")
try:
    from xps_to_pmx.mmd_bone_tree_ui import XPSPMX_PT_bone_detail_panel
    print("   ✅ XPSPMX_PT_bone_detail_panel 类已加载")

    # 检查是否有 draw 方法
    if hasattr(XPSPMX_PT_bone_detail_panel, 'draw'):
        print("   ✅ draw 方法存在")

        # 读取源代码检查是否有编辑按钮
        import inspect
        source = inspect.getsource(XPSPMX_PT_bone_detail_panel.draw)
        if 'edit_mapping' in source:
            print("   ✅ 源代码中包含 'edit_mapping' 按钮")
        else:
            print("   ❌ 源代码中未找到 'edit_mapping' 按钮")
    else:
        print("   ❌ draw 方法不存在")

except Exception as e:
    print(f"   ❌ 无法检查面板代码: {e}")

# 总结
print("\n" + "="*60)
print("📋 诊断总结")
print("="*60)

print("""
✅ 如果所有检查都通过，那么：
  1. 打开右侧面板，找到 "XPS to PMX Mapper" 标签
  2. 找到 "🌳 MMD 骨骼树形结构" 面板
  3. 在树中点击任何 MMD 骨骼名称（如"センター"）
  4. 向下滚动右侧面板，找到 "骨骼详情" 面板
  5. 在底部的 "🔧 操作" 区域应该看到 "✎ 编辑映射" 按钮

❌ 如果有检查失败：
  1. 检查失败的项目表明了问题所在
  2. 可能需要重启 Blender 或重新加载插件
  3. 检查插件文件是否正确同步

⚠️ 常见问题：
  • "全局配置为空" 是正常的，需要先运行 "Auto Map Bones"
  • 如果操作符未注册，说明模块导入有问题
  • 如果面板未注册，说明插件没有正确加载
""")

print("="*60)
print("诊断完成！")
print("="*60 + "\n")
