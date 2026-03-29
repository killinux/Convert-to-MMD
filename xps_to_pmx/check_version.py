"""
快速检查 XPS to PMX 插件版本和更新时间

在 Blender Python 控制台中运行：
import sys
sys.path.append('E:\\mywork\\Convert-to-MMD')
from xps_to_pmx import check_version
check_version.show_plugin_info()
"""

import bpy


def show_plugin_info():
    """显示插件信息和更新时间."""
    print("\n" + "="*70)
    print("XPS to PMX 插件版本信息")
    print("="*70)

    try:
        # 获取插件信息
        import xps_to_pmx
        addon_module = xps_to_pmx

        if hasattr(addon_module, 'bl_info'):
            bl_info = addon_module.bl_info

            print(f"📦 插件名称：{bl_info.get('name', '未知')}")
            print(f"👤 作者：{bl_info.get('author', '未知')}")

            version = bl_info.get('version', (0, 0, 0))
            version_str = '.'.join(map(str, version))
            print(f"📌 版本：{version_str}")

            blender_ver = bl_info.get('blender', (0, 0, 0))
            blender_str = '.'.join(map(str, blender_ver))
            print(f"🔧 Blender 最低版本：{blender_str}")

            print(f"📍 位置：{bl_info.get('location', '未知')}")
            print(f"📝 描述：{bl_info.get('description', '未知')}")

            # 关键：显示更新时间戳
            last_updated = bl_info.get('last_updated', '未设置')
            print(f"\n⏰ 【最后更新时间】：{last_updated}")
            print(f"   （用这个时间戳来检查你的代码是否是最新的）")

            print("\n" + "="*70)
            print("✓ 插件已正确加载")
            print("="*70 + "\n")

        else:
            print("❌ 无法找到 bl_info")

    except ImportError as e:
        print(f"❌ 无法加载插件：{e}")
        print("请确保插件路径正确")


def check_core_modules():
    """检查所有核心模块是否已加载."""
    print("\n核心模块检查：")
    print("-" * 70)

    modules_to_check = [
        ('xps_to_pmx', '主插件'),
        ('xps_to_pmx.mapping', '映射子包'),
        ('xps_to_pmx.mapping.data_structures', '数据结构'),
        ('xps_to_pmx.mapping.detection', '自动检测'),
        ('xps_to_pmx.mapping_ui', 'UI 系统'),
        ('xps_to_pmx.weights', '权重系统'),
        ('xps_to_pmx.pipeline', '流水线'),
    ]

    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {module_name:40} ({description})")
        except ImportError as e:
            print(f"✗ {module_name:40} ({description})")
            print(f"  └─ 错误：{e}")


def check_ui_registration():
    """检查 UI 组件是否已注册."""
    print("\n\nUI 组件检查：")
    print("-" * 70)

    ui_components = [
        ('XPSPMX_PT_auto_detection', '① 自动检测面板'),
        ('XPSPMX_PT_mapping_editor', '② 映射编辑器面板'),
        ('XPSPMX_PT_weight_rules', '③ 权重规则面板'),
        ('XPSPMX_PT_validation_preview', '④ 验证和预览面板'),
    ]

    for class_name, description in ui_components:
        try:
            cls = getattr(bpy.types, class_name, None)
            if cls:
                print(f"✓ {class_name:40} ({description})")
            else:
                print(f"✗ {class_name:40} ({description})")
                print(f"  └─ 类未找到")
        except Exception as e:
            print(f"✗ {class_name:40} ({description})")
            print(f"  └─ 错误：{e}")


def full_diagnostic():
    """完整诊断."""
    show_plugin_info()
    check_core_modules()
    check_ui_registration()

    print("\n" + "="*70)
    print("诊断完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    show_plugin_info()
