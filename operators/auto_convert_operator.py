import bpy
from . import weight_monitor


# 会修改权重的步骤（需要前后快照对比）
WEIGHT_STEPS = {
    "object.complete_missing_bones",
    "object.split_spine_shoulder",
    "object.check_fix_missing_weights",
}

STEP_IDS = {
    "object.complete_missing_bones": "step_2",
    "object.split_spine_shoulder": "step_3",
    "object.check_fix_missing_weights": "step_11",
}


class OBJECT_OT_auto_convert(bpy.types.Operator):
    """一键全流程：依次执行所有转换步骤（可单独执行各步调试）"""
    bl_idname = "object.auto_convert_to_mmd"
    bl_label = "一键全流程转换"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}

        steps = [
            ("object.merge_meshes",           "网格合并"),
            ("object.clear_unweighted_bones",  "清理无权重骨骼"),
            ("object.convert_to_apose",        "转换为A-Pose"),
            ("object.rename_to_mmd",           "重命名为MMD"),
            ("object.complete_missing_bones",  "补全缺失骨骼"),
            ("object.split_spine_shoulder",    "骨骼切分"),
            ("object.add_twist_bones",         "添加扭转骨骼"),
            ("object.add_mmd_ik",              "添加MMD IK"),
            ("object.create_bone_group",       "创建骨骼集合"),
            ("object.convert_materials_to_mmd","材质转换"),
            ("object.check_fix_missing_weights","权重修复（孤立骨+缺失骨+髋部渐变）"),
            ("object.verify_weights",          "权重验证"),
        ]

        # 清除旧的监控记录
        if "wm_snapshots" in obj:
            del obj["wm_snapshots"]
        context.scene["wm_step_status"] = "{}"

        failed = []
        weight_warnings = []

        for op_idname, step_name in steps:
            # 确保每步开始前活动对象是骨架
            context.view_layer.objects.active = obj

            # 权重步骤：拍前快照
            pre_snapshot = None
            if op_idname in WEIGHT_STEPS:
                mesh_objects = weight_monitor._get_mesh_objects(context, obj)
                if mesh_objects:
                    pre_snapshot = weight_monitor.take_weight_snapshot(obj, mesh_objects)

            try:
                result = getattr(bpy.ops, op_idname.replace(".", "_", 1))()
                if 'CANCELLED' in result:
                    self.report({'WARNING'}, f"步骤「{step_name}」被跳过（CANCELLED）")
            except Exception as e:
                failed.append(f"{step_name}: {e}")
                self.report({'WARNING'}, f"步骤「{step_name}」失败: {e}")

            # 权重步骤：拍后快照并对比
            # 注意：各 operator 的 execute() 末尾已有 auto_check 调用，
            # 这里额外做一次对比检查，报告给用户
            if pre_snapshot and op_idname in WEIGHT_STEPS:
                mesh_objects = weight_monitor._get_mesh_objects(context, obj)
                if mesh_objects:
                    post_snapshot = weight_monitor.take_weight_snapshot(obj, mesh_objects)
                    status, issues = weight_monitor.compare_snapshots(pre_snapshot, post_snapshot)
                    if status in ("warning", "error"):
                        weight_warnings.append(f"{step_name}: {'; '.join(issues)}")
                        self.report({'WARNING'}, f"⚠️ {step_name}: {'; '.join(issues)}")

        # 汇总报告
        if failed:
            self.report({'WARNING'}, f"全流程完成，{len(failed)} 个步骤有问题")
        elif weight_warnings:
            self.report({'WARNING'},
                f"全流程完成，权重警告 {len(weight_warnings)} 处: {' | '.join(weight_warnings[:3])}")
        else:
            self.report({'INFO'}, "✅ 全流程转换完成！权重监控全部通过")

        return {'FINISHED'}
