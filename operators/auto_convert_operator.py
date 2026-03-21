import bpy


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
            ("object.verify_weights",          "权重验证"),
        ]

        failed = []
        for op_idname, step_name in steps:
            # 确保每步开始前活动对象是骨架
            context.view_layer.objects.active = obj
            try:
                result = getattr(bpy.ops, op_idname.replace(".", "_", 1))()
                if 'CANCELLED' in result:
                    self.report({'WARNING'}, f"步骤「{step_name}」被跳过（CANCELLED）")
            except Exception as e:
                failed.append(f"{step_name}: {e}")
                self.report({'WARNING'}, f"步骤「{step_name}」失败: {e}")

        if failed:
            self.report({'WARNING'}, f"全流程完成，{len(failed)} 个步骤有问题")
        else:
            self.report({'INFO'}, "全流程转换完成！请检查权重验证结果")

        return {'FINISHED'}
