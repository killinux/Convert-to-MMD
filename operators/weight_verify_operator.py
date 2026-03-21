import bpy


class OBJECT_OT_verify_weights(bpy.types.Operator):
    """验证骨骼与顶点组的绑定完整性，检查孤儿顶点组和无权重顶点"""
    bl_idname = "object.verify_weights"
    bl_label = "7. 权重验证"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}

        bone_names = set(b.name for b in armature.data.bones)

        # 获取所有绑定到此骨架的网格
        mesh_objects = [
            obj for obj in context.scene.objects
            if obj.type == 'MESH' and any(
                m.type == 'ARMATURE' and m.object == armature
                for m in obj.modifiers
            )
        ]

        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定到此骨架的网格对象")
            return {'CANCELLED'}

        all_vg_names = set()
        for obj in mesh_objects:
            for vg in obj.vertex_groups:
                all_vg_names.add(vg.name)

        # 有骨骼但无顶点组（骨骼无权重，可能是控制骨骼，允许的）
        bones_without_vg = bone_names - all_vg_names

        # 有顶点组但骨骼已不存在（孤儿权重，会导致问题）
        orphan_vgs = all_vg_names - bone_names

        # 检查无权重顶点（没有任何权重的顶点）
        unweighted_vert_count = 0
        for obj in mesh_objects:
            for v in obj.data.vertices:
                if len(v.groups) == 0:
                    unweighted_vert_count += 1
                else:
                    total_w = sum(g.weight for g in v.groups)
                    if total_w < 0.001:
                        unweighted_vert_count += 1

        # 检查指向非变形骨骼的顶点组
        non_deform_bones = {b.name for b in armature.data.bones if not b.use_deform}
        nondeform_vg_names = set()
        nondeform_vert_count = 0
        for obj in mesh_objects:
            for vg in obj.vertex_groups:
                if vg.name in non_deform_bones:
                    nondeform_vg_names.add(vg.name)
                    for v in obj.data.vertices:
                        for g in v.groups:
                            if g.group == vg.index and g.weight > 0.001:
                                nondeform_vert_count += 1
                                break

        # 存储结果到 scene 属性供 UI 显示
        context.scene.weight_verify_bones_without_vg = len(bones_without_vg)
        context.scene.weight_verify_orphan_vgs = len(orphan_vgs)
        context.scene.weight_verify_orphan_names = ", ".join(sorted(orphan_vgs)[:10])
        context.scene.weight_verify_unweighted_verts = unweighted_vert_count
        context.scene.weight_verify_nondeform_verts = nondeform_vert_count
        context.scene.weight_verify_nondeform_names = ", ".join(sorted(nondeform_vg_names)[:5])
        context.scene.weight_verify_done = True

        # 报告摘要
        issues = []
        if orphan_vgs:
            issues.append(f"孤儿顶点组 {len(orphan_vgs)} 个")
        if nondeform_vert_count > 0:
            issues.append(f"非变形骨权重 {nondeform_vert_count} 顶点（{', '.join(sorted(nondeform_vg_names)[:3])}）")
        if unweighted_vert_count > 0:
            issues.append(f"无权重顶点 {unweighted_vert_count} 个")

        if issues:
            self.report({'WARNING'}, "权重问题: " + " | ".join(issues))
        else:
            self.report({'INFO'},
                f"权重验证通过 | 骨骼={len(bone_names)} "
                f"| 孤儿顶点组=0 | 无权重顶点=0")

        return {'FINISHED'}


class OBJECT_OT_clean_orphan_vertex_groups(bpy.types.Operator):
    """删除所有与骨骼名称不匹配的孤儿顶点组"""
    bl_idname = "object.clean_orphan_vertex_groups"
    bl_label = "一键清理孤儿顶点组"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}

        bone_names = set(b.name for b in armature.data.bones)
        removed = 0

        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            has_armature_mod = any(
                m.type == 'ARMATURE' and m.object == armature
                for m in obj.modifiers
            )
            if not has_armature_mod:
                continue

            to_remove = [vg for vg in obj.vertex_groups if vg.name not in bone_names]
            for vg in to_remove:
                obj.vertex_groups.remove(vg)
                removed += 1

        # 重置验证状态
        context.scene.weight_verify_done = False

        self.report({'INFO'}, f"已删除 {removed} 个孤儿顶点组")
        return {'FINISHED'}


class OBJECT_OT_fix_nondeform_weights(bpy.types.Operator):
    """将指向非变形骨骼（如全ての親/センター/グルーブ）的顶点权重
    转移到最近的可变形父骨（修复头发/物理网格不跟随骨骼的问题）"""
    bl_idname = "object.fix_nondeform_weights"
    bl_label = "修复非变形骨权重（头发等）"

    # 无可变形父骨时的备用骨骼（按优先级），通常用于 root 级别的权重（如头发）
    FALLBACK_BONES = ['頭', 'head neck upper', '首', 'head neck lower', '上半身2', '上半身']

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}

        arm_data = armature.data

        # 非变形骨骼集合
        non_deform = {b.name for b in arm_data.bones if not b.use_deform}
        if not non_deform:
            self.report({'INFO'}, "所有骨骼均为变形骨，无需修复")
            return {'FINISHED'}

        # 找备用骨骼（无可变形父级时使用）
        fallback = next((n for n in self.FALLBACK_BONES if arm_data.bones.get(n)), None)

        # 为每个非变形骨计算重定向目标：向上找最近的 use_deform=True 祖先
        redirect = {}
        for bname in non_deform:
            bone = arm_data.bones.get(bname)
            if not bone:
                continue
            cur = bone.parent
            while cur:
                if cur.use_deform:
                    redirect[bname] = cur.name
                    break
                cur = cur.parent
            else:
                redirect[bname] = fallback  # 一直到根也没找到，用备用骨

        fixed_verts = 0
        fixed_vgs = 0

        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            if not any(m.type == 'ARMATURE' and m.object == armature for m in obj.modifiers):
                continue

            # 找到该 mesh 中存在的问题顶点组
            problem = {vg.name: vg for vg in obj.vertex_groups if vg.name in non_deform}
            if not problem:
                continue

            for src_name, src_vg in problem.items():
                target_name = redirect.get(src_name)
                if not target_name:
                    continue  # 无合适目标，跳过

                # 确保目标顶点组存在
                target_vg = obj.vertex_groups.get(target_name)
                if not target_vg:
                    target_vg = obj.vertex_groups.new(name=target_name)

                # 将 src_vg 的权重累加到 target_vg
                moved = 0
                for v in obj.data.vertices:
                    src_w = 0.0
                    for g in v.groups:
                        if g.group == src_vg.index:
                            src_w = g.weight
                            break
                    if src_w <= 0:
                        continue

                    cur_w = 0.0
                    for g in v.groups:
                        if g.group == target_vg.index:
                            cur_w = g.weight
                            break

                    target_vg.add([v.index], min(1.0, cur_w + src_w), 'REPLACE')
                    moved += 1

                obj.vertex_groups.remove(src_vg)
                fixed_verts += moved
                fixed_vgs += 1

        context.scene.weight_verify_done = False
        self.report(
            {'INFO'},
            f"已修复 {fixed_vgs} 个非变形骨顶点组，影响顶点 {fixed_verts} 个"
            + (f"（备用骨骼: {fallback}）" if fallback else "")
        )
        return {'FINISHED'}
