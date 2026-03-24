import bpy
from mathutils import Vector


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _get_mesh_objects(armature, scene):
    return [
        obj for obj in scene.objects
        if obj.type == 'MESH' and any(
            m.type == 'ARMATURE' and m.object == armature
            for m in obj.modifiers
        )
    ]


def _count_vertices_per_bone(armature, scene):
    """统计各骨骼的权重顶点数，返回 {bone_name: count}"""
    counts = {}
    for obj in _get_mesh_objects(armature, scene):
        idx_to_name = {vg.index: vg.name for vg in obj.vertex_groups}
        for v in obj.data.vertices:
            for g in v.groups:
                if g.weight > 0.001:
                    name = idx_to_name.get(g.group)
                    if name:
                        counts[name] = counts.get(name, 0) + 1
    return counts


# 权重冲突规则（不该同时影响同一顶点的骨骼对）
CONFLICT_PAIRS = [
    ("足D.L", "下半身"), ("足D.R", "下半身"),
    ("足D.L", "腰"),     ("足D.R", "腰"),
    ("ひざD.L", "下半身"), ("ひざD.R", "下半身"),
    ("ひざD.L", "腰"),    ("ひざD.R", "腰"),
    ("足首D.L", "下半身"), ("足首D.R", "下半身"),
    ("足首D.L", "腰"),    ("足首D.R", "腰"),
]
CONFLICT_VG_NAME = "冲突顶点"


# ─────────────────────────────────────────────────────────────────────────────
# 功能A：逐骨顶点数对比
# ─────────────────────────────────────────────────────────────────────────────

class OBJECT_OT_compare_bone_weights(bpy.types.Operator):
    """对比当前骨架与参考骨架的逐骨顶点数分布，标出差异超过3倍的骨骼"""
    bl_idname = "object.compare_bone_weights"
    bl_label = "比较骨骼权重分布"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选中当前骨架")
            return {'CANCELLED'}
        ref_arm = getattr(context.scene, 'weight_ref_armature', None)
        if not ref_arm or ref_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "请在下方选择参考骨架")
            return {'CANCELLED'}

        cur_counts = _count_vertices_per_bone(armature, context.scene)
        ref_counts = _count_vertices_per_bone(ref_arm, context.scene)

        deform_bones = [b.name for b in armature.data.bones if b.use_deform]

        entries = []
        for bname in deform_bones:
            cur = cur_counts.get(bname, 0)
            ref = ref_counts.get(bname, 0)
            if ref == 0:
                flag = "📌"
                sort_key = 999.0
            else:
                ratio = cur / ref
                sort_key = abs(ratio - 1.0)
                if ratio < 0.3 or ratio > 3.0:
                    flag = "⚠️"
                elif 0.7 <= ratio <= 1.4:
                    flag = "✅"
                else:
                    flag = "🔶"
            entries.append((sort_key, flag, bname, cur, ref))

        entries.sort(key=lambda x: -x[0])

        lines = []
        for sort_key, flag, bname, cur, ref in entries[:20]:
            if ref == 0:
                lines.append(f"{flag} {bname}: 当前={cur} 参考=无")
            else:
                ratio = cur / ref
                lines.append(f"{flag} {bname}: 当前={cur} 参考={ref} ({ratio:.0%})")

        context.scene.weight_compare_result = "||".join(lines)
        context.scene.weight_compare_done = True

        warn_count = sum(1 for e in entries if e[1] == "⚠️")
        self.report(
            {'INFO'} if warn_count == 0 else {'WARNING'},
            f"对比完成，{warn_count} 个骨骼差异 >3x（共检查 {len(deform_bones)} 块变形骨）"
        )
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# 功能B：冲突顶点高亮
# ─────────────────────────────────────────────────────────────────────────────

class OBJECT_OT_highlight_conflict_vertices(bpy.types.Operator):
    """高亮同时受冲突骨骼（如 足D + 下半身）影响的顶点，创建顶点组便于 Weight Paint 查看"""
    bl_idname = "object.highlight_conflict_vertices"
    bl_label = "高亮冲突顶点"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选中骨架对象")
            return {'CANCELLED'}

        mesh_objects = _get_mesh_objects(armature, context.scene)
        total_conflict = 0
        conflict_pairs_found = set()

        for obj in mesh_objects:
            old_vg = obj.vertex_groups.get(CONFLICT_VG_NAME)
            if old_vg:
                obj.vertex_groups.remove(old_vg)

            name_to_idx = {vg.name: vg.index for vg in obj.vertex_groups}
            conflict_indices = []

            for v in obj.data.vertices:
                weighted_groups = {g.group for g in v.groups if g.weight > 0.001}
                for bone_a, bone_b in CONFLICT_PAIRS:
                    idx_a = name_to_idx.get(bone_a)
                    idx_b = name_to_idx.get(bone_b)
                    if idx_a is not None and idx_b is not None:
                        if idx_a in weighted_groups and idx_b in weighted_groups:
                            conflict_indices.append(v.index)
                            conflict_pairs_found.add((bone_a, bone_b))
                            break

            if conflict_indices:
                cvg = obj.vertex_groups.new(name=CONFLICT_VG_NAME)
                cvg.add(conflict_indices, 1.0, 'REPLACE')
                total_conflict += len(conflict_indices)

        context.scene.weight_conflict_count = total_conflict
        context.scene.weight_conflict_done = True

        if total_conflict == 0:
            self.report({'INFO'}, "✅ 无冲突顶点，腿部权重干净")
        else:
            pairs_str = ", ".join(f"{a}+{b}" for a, b in sorted(conflict_pairs_found)[:3])
            self.report(
                {'WARNING'},
                f"发现 {total_conflict} 个冲突顶点 | "
                f"切到 Weight Paint 选「{CONFLICT_VG_NAME}」查看 | "
                f"冲突对: {pairs_str}"
            )
        return {'FINISHED'}


class OBJECT_OT_clear_conflict_highlight(bpy.types.Operator):
    """删除冲突顶点标记组（清除高亮，方便下次重新检查）"""
    bl_idname = "object.clear_conflict_highlight"
    bl_label = "清除高亮"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选中骨架对象")
            return {'CANCELLED'}

        removed = 0
        for obj in _get_mesh_objects(armature, context.scene):
            vg = obj.vertex_groups.get(CONFLICT_VG_NAME)
            if vg:
                obj.vertex_groups.remove(vg)
                removed += 1

        context.scene.weight_conflict_done = False
        self.report({'INFO'}, f"已清除 {removed} 个网格的冲突顶点组")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# 功能D：摆 Pose 测试
# ─────────────────────────────────────────────────────────────────────────────

class OBJECT_OT_pose_test(bpy.types.Operator):
    """摆出抬左腿测试姿势，直观检验腿部权重变形是否正确"""
    bl_idname = "object.pose_test_raise_leg"
    bl_label = "摆姿势：抬左腿"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选中骨架对象")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='POSE')

        IK_NAMES = ["左足ＩＫ", "左足IK"]
        ik_bone = None
        for name in IK_NAMES:
            pb = armature.pose.bones.get(name)
            if pb:
                ik_bone = pb
                break

        if ik_bone is None:
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'WARNING'}, f"未找到左足IK骨骼（尝试了: {IK_NAMES}），请手动摆姿势")
            return {'CANCELLED'}

        # 向前上方抬腿
        ik_bone.location = Vector((0.0, 0.5, 0.3))
        context.view_layer.update()

        self.report({'INFO'}, f"已设置 {ik_bone.name}，处于 POSE 模式，查看左腿变形效果")
        return {'FINISHED'}


class OBJECT_OT_pose_test_reset(bpy.types.Operator):
    """恢复骨架到 Rest Pose，清除所有测试姿势变换"""
    bl_idname = "object.pose_test_reset"
    bl_label = "恢复 Rest Pose"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选中骨架对象")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, "已恢复 Rest Pose")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# 原有 Operator（以下保持不变）
# ─────────────────────────────────────────────────────────────────────────────

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
        total_vert_count = 0
        unweighted_vert_count = 0
        for obj in mesh_objects:
            total_vert_count += len(obj.data.vertices)
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
        context.scene.weight_verify_total_verts = total_vert_count
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

        # FK腿骨 → D系骨 优先映射（父链会错误找到下半身，必须硬编码覆盖）
        LEG_FK_TO_D = {
            "左足":   "足D.L",   "右足":   "足D.R",
            "左ひざ": "ひざD.L", "右ひざ": "ひざD.R",
            "左足首": "足首D.L", "右足首": "足首D.R",
            "左足先EX": "足先EX.L", "右足先EX": "足先EX.R",
        }

        # 为每个非变形骨计算重定向目标：优先使用硬编码映射，其次向上找 use_deform=True 祖先
        redirect = {}
        for bname in non_deform:
            # 优先：FK腿骨直接映射到对应D系骨
            if bname in LEG_FK_TO_D:
                target = LEG_FK_TO_D[bname]
                if arm_data.bones.get(target):
                    redirect[bname] = target
                    continue

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
