"""
XPS to PMX 权重处理
"""

from . import mapping


def transfer_leg_weights_to_d_bones(armature, mesh_objects):
    """
    将腿部FK骨的权重复制到D骨
    返回转移的顶点数
    """
    transfer_map = [
        ("左足", "足D.L"),
        ("左ひざ", "ひざD.L"),
        ("左足首", "足首D.L"),
        ("右足", "足D.R"),
        ("右ひざ", "ひざD.R"),
        ("右足首", "足首D.R"),
    ]

    total_transferred = 0

    for fk_name, d_name in transfer_map:
        for obj in mesh_objects:
            src_vg = obj.vertex_groups.get(fk_name)
            if not src_vg:
                continue

            # 创建或获取目标VG
            dst_vg = obj.vertex_groups.get(d_name)
            if not dst_vg:
                dst_vg = obj.vertex_groups.new(name=d_name)

            # 复制权重
            transferred = 0
            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group == src_vg.index and g.weight > 0:
                        dst_vg.add([v.index], g.weight, 'REPLACE')
                        transferred += 1
                        break

            # 清零源骨权重
            src_vg.remove([v.index for v in obj.data.vertices])
            total_transferred += transferred

    # 将FK腿骨设为非变形骨
    fk_leg_bones = {"左足", "左ひざ", "左足首", "右足", "右ひざ", "右足首"}
    for bname in fk_leg_bones:
        bone = armature.data.bones.get(bname)
        if bone:
            bone.use_deform = False

    return total_transferred


def create_hip_blend_zone(armature, mesh_objects, blend_ratio=0.46):
    """
    在髋部创建权重过渡区
    从纯足D过渡到足D+下半身混合
    返回修改的顶点数
    """
    modified = 0

    for obj in mesh_objects:
        # 获取骨骼VG
        d_left_vg = obj.vertex_groups.get("足D.L")
        d_right_vg = obj.vertex_groups.get("足D.R")
        lower_vg = obj.vertex_groups.get("下半身")

        if not (d_left_vg and d_right_vg and lower_vg):
            continue

        mw = obj.matrix_world
        arm_mw = armature.matrix_world

        # 获取腿骨位置（世界坐标）
        left_leg = armature.data.bones.get("左足")
        right_leg = armature.data.bones.get("右足")

        if not (left_leg and right_leg):
            continue

        left_head_z = (arm_mw @ left_leg.head_local).z
        right_head_z = (arm_mw @ right_leg.head_local).z

        # 对每个顶点做权重过渡
        for v in obj.data.vertices:
            vz = (mw @ v.co).z

            # 确定在左还是右腿范围内
            if abs(vz - left_head_z) < abs(vz - right_head_z):
                d_vg = d_left_vg
            else:
                d_vg = d_right_vg

            # 检查是否在过渡区
            d_weight = 0.0
            for g in v.groups:
                if g.group == d_vg.index:
                    d_weight = g.weight
                    break

            # 在过渡区做渐变混合
            if 0.3 < d_weight < 0.7:
                # 线性过渡：高权重往下半身转移一些
                lower_vg.add([v.index], (1.0 - d_weight) * 0.5, 'ADD')
                modified += 1

    return modified


def normalize_weights(armature, mesh_objects):
    """
    归一化所有顶点权重，使总和≤1.0
    """
    normalized = 0
    deform_bones = {b.name for b in armature.data.bones if b.use_deform}

    for obj in mesh_objects:
        vg_idx_map = {vg.index: vg.name for vg in obj.vertex_groups}

        for v in obj.data.vertices:
            # 计算总权重
            total = sum(
                g.weight for g in v.groups
                if g.group in vg_idx_map
                and vg_idx_map[g.group] in deform_bones
            )

            if total > 1.001:
                # 缩放到1.0
                scale = 1.0 / total
                for g in v.groups:
                    if g.group in vg_idx_map and vg_idx_map[g.group] in deform_bones:
                        g.weight *= scale
                normalized += 1

    return normalized
