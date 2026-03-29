"""
XPS to PMX - Blender插件
快速将XPS格式模型转换为MMD（MikuMikuDance）格式

特性：
- 自动识别XPS骨骼并映射到MMD日文名
- 创建D骨和IK约束
- 权重转移和修复
- 一键导出PMX格式
"""

bl_info = {
    "name": "XPS to PMX",
    "author": "Claude",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > XPS to PMX",
    "description": "Convert XPS rigs to MMD format quickly with flexible mapping system",
    "category": "Import-Export",
    # 更新时间戳 - 用于检查插件版本
    "last_updated": "2026-03-29 18:45:00",
    # 版本历史
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
from . import ui, pipeline, mapping_ui, mmd_bone_tree_ui, operators


# ─────────────────────────────────────────────────────────────────────────────
# 场景属性注册
# ─────────────────────────────────────────────────────────────────────────────

def register_properties():
    """注册Scene属性用于存储UI状态和中间结果"""

    bpy.types.Scene.xps_pmx_output_path = bpy.props.StringProperty(
        name="Output Path",
        description="PMX导出路径",
        subtype='FILE_PATH',
        default=""
    )

    bpy.types.Scene.xps_pmx_skip_apose = bpy.props.BoolProperty(
        name="Skip A-Pose",
        description="模型已是A-Pose，跳过Stage3",
        default=False
    )

    bpy.types.Scene.xps_pmx_detected_type = bpy.props.StringProperty(
        name="Detected Type",
        description="检测到的骨架格式",
        default="unknown"
    )

    bpy.types.Scene.xps_pmx_skeleton_type = bpy.props.StringProperty(
        name="Skeleton Type",
        description="选中的骨架格式",
        default="auto"
    )

    bpy.types.Scene.xps_pmx_check_results = bpy.props.StringProperty(
        name="Check Results",
        description="骨架检测结果（JSON）",
        default=""
    )

    bpy.types.Scene.xps_pmx_last_result = bpy.props.StringProperty(
        name="Last Result",
        description="最后操作的结果信息",
        default=""
    )


def unregister_properties():
    """注销Scene属性"""
    for attr in [
        'xps_pmx_output_path',
        'xps_pmx_skip_apose',
        'xps_pmx_detected_type',
        'xps_pmx_skeleton_type',
        'xps_pmx_check_results',
        'xps_pmx_last_result',
    ]:
        if hasattr(bpy.types.Scene, attr):
            delattr(bpy.types.Scene, attr)


# ─────────────────────────────────────────────────────────────────────────────
# 注册/注销
# ─────────────────────────────────────────────────────────────────────────────

def register():
    """注册所有操作和UI面板"""
    # 注册Scene属性
    register_properties()

    # 注册UI模块中的所有类
    ui.register()

    # 注册新的映射UI系统
    mapping_ui.register()

    # 注册 MMD 骨骼树形 UI
    mmd_bone_tree_ui.register()

    # 注册转换管道操作符
    operators.register()


def unregister():
    """注销所有操作和UI面板"""
    # 注销转换管道操作符
    operators.unregister()

    # 注销 MMD 骨骼树形 UI
    mmd_bone_tree_ui.unregister()

    # 注销新的映射UI系统
    mapping_ui.unregister()

    # 注销UI模块中的所有类
    ui.unregister()

    # 注销Scene属性
    unregister_properties()


if __name__ == "__main__":
    register()
