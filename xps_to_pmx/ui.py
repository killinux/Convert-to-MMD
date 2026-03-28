"""
XPS to PMX UI 面板和操作
"""

import bpy
from . import pipeline


# ─────────────────────────────────────────────────────────────────────────────
# 操作类
# ─────────────────────────────────────────────────────────────────────────────

class XPS_OT_full_convert(bpy.types.Operator):
    """一键执行全部转换流程"""
    bl_idname = "xps_to_pmx.full_convert"
    bl_label = "Convert → PMX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = context.active_object
        if not arm or arm.type != 'ARMATURE':
            self.report({'ERROR'}, "请先选中骨架对象")
            return {'CANCELLED'}

        scene = context.scene
        output_path = bpy.path.abspath(scene.xps_pmx_output_path)
        if not output_path:
            import os
            blend_path = bpy.data.filepath
            output_path = (os.path.splitext(blend_path)[0] + ".pmx") if blend_path else "output.pmx"

        success, results = pipeline.run_full_pipeline(
            arm, context, output_path,
            skip_apose=scene.xps_pmx_skip_apose
        )

        for r in results:
            level = 'ERROR' if 'FAILED' in r or 'ERROR' in r else 'INFO'
            self.report({level}, r)

        scene.xps_pmx_last_result = results[-1] if results else ""
        return {'FINISHED'} if success else {'CANCELLED'}


class XPS_OT_stage(bpy.types.Operator):
    """执行单个转换阶段"""
    bl_idname = "xps_to_pmx.run_stage"
    bl_label = "Run Stage"
    bl_options = {'REGISTER', 'UNDO'}

    stage: bpy.props.IntProperty(default=1)

    def execute(self, context):
        arm = context.active_object
        if not arm or arm.type != 'ARMATURE':
            self.report({'ERROR'}, "请先选中骨架对象")
            return {'CANCELLED'}

        scene = context.scene
        stage_fns = {
            1: lambda: pipeline.stage_rebuild_skeleton(arm, context),
            2: lambda: pipeline.stage_pose_to_apose(arm, context),
            3: lambda: pipeline.stage_fix_weights(arm, context),
            4: lambda: pipeline.stage_setup_additional_transform(arm, context),
            5: lambda: pipeline.stage_export_pmx(arm, context, bpy.path.abspath(scene.xps_pmx_output_path)),
        }

        fn = stage_fns.get(self.stage)
        if not fn:
            self.report({'ERROR'}, f"未知阶段 {self.stage}")
            return {'CANCELLED'}

        try:
            success, msg = fn()
            self.report({'INFO' if success else 'ERROR'}, msg)
            scene.xps_pmx_last_result = msg
            return {'FINISHED'} if success else {'CANCELLED'}
        except Exception as e:
            import traceback
            self.report({'ERROR'}, traceback.format_exc())
            return {'CANCELLED'}


# ─────────────────────────────────────────────────────────────────────────────
# UI 面板
# ─────────────────────────────────────────────────────────────────────────────

class XPS_PT_main_panel(bpy.types.Panel):
    bl_label = "XPS to PMX"
    bl_idname = "XPS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        # 版本信息
        row = layout.row()
        row.scale_y = 0.6
        row.label(text="XPS to PMX v1.0", icon='TIME')

        layout.separator()

        # 检查是否选中骨架
        if not obj or obj.type != 'ARMATURE':
            layout.label(text="请选中骨架对象", icon='ERROR')
            return

        # 主按钮
        row = layout.row()
        row.scale_y = 2.0
        row.operator("xps_to_pmx.full_convert", icon='ARMATURE_DATA')

        layout.separator()

        # 设置
        box = layout.box()
        box.label(text="设置", icon='SETTINGS')
        box.prop(scene, "xps_pmx_output_path", text="输出路径")
        box.prop(scene, "xps_pmx_skip_apose", text="已是A-Pose（跳过Stage2）")

        layout.separator()

        # 单步操作
        col = layout.column(align=True)
        col.label(text="单步操作：")
        steps = [
            (1, "1. 重建骨架", 'BONE_DATA'),
            (2, "2. A-Pose转换", 'POSE_HLT'),
            (3, "3. 权重修复", 'GROUP_VERTEX'),
            (4, "4. 付与&IK", 'CONSTRAINT_BONE'),
            (5, "5. 导出PMX", 'EXPORT'),
        ]
        for stage_id, label, icon in steps:
            op = col.operator("xps_to_pmx.run_stage", text=label, icon=icon)
            op.stage = stage_id

        layout.separator()

        # 状态信息
        if scene.xps_pmx_last_result:
            box = layout.box()
            is_err = 'FAILED' in scene.xps_pmx_last_result or 'ERROR' in scene.xps_pmx_last_result
            box.label(text="状态：", icon='ERROR' if is_err else 'INFO')
            msg = scene.xps_pmx_last_result
            for chunk in [msg[i:i+50] for i in range(0, len(msg), 50)]:
                box.label(text=chunk)


# ─────────────────────────────────────────────────────────────────────────────
# 注册/注销
# ─────────────────────────────────────────────────────────────────────────────

CLASSES = [
    XPS_OT_full_convert,
    XPS_OT_stage,
    XPS_PT_main_panel,
]


def register():
    """注册所有UI类"""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    """注销所有UI类"""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
