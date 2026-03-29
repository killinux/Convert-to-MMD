"""
XPS to PMX Weight processing system.

New rule-based system for transparent and auditable weight transfer rules.
Supports multiple rule types:
- FK→D: Copy weights from FK bone to D-bone
- Twist: Gradient distribution for twist bones
- Waist Cancel: Setup cancel bones (deform=False)
- Hip Blend: Linear blend zone for hip transitions
- Normalize: Normalize vertex weights to ≤1.0
- Orphan Transfer: Transfer orphaned bone weights
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from . import mapping
from .mapping import data_structures


# ─────────────────────────────────────────────────────────────────────────────
# Weight Transfer Rule System
# ─────────────────────────────────────────────────────────────────────────────

class WeightTransferRule(ABC):
    """Base class for weight transfer rules.

    Each rule type implements a specific weight transformation strategy.
    All rules return (success, message) tuple for transparent logging.
    """

    @abstractmethod
    def apply(self, armature, mesh_objects, rule: data_structures.WeightMappingRule) -> Tuple[bool, str]:
        """Apply the weight transfer rule.

        Args:
            armature: Blender armature object
            mesh_objects: List of mesh objects to process
            rule: WeightMappingRule specifying parameters

        Returns:
            (success, message) tuple
        """
        pass


class FKToDBoneRule(WeightTransferRule):
    """FK → D-Bone weight transfer rule.

    Copies weights from FK bone to D-bone, then clears the FK bone.
    This is critical for IK-based rigs where FK bones have no deform.
    """

    def apply(self, armature, mesh_objects, rule: data_structures.WeightMappingRule) -> Tuple[bool, str]:
        """Copy FK bone weights to D-bone."""
        fk_name = rule.source_bone
        d_name = rule.target_bone
        transferred_count = 0

        for obj in mesh_objects:
            if obj.type != 'MESH' or not obj.vertex_groups:
                continue

            src_vg = obj.vertex_groups.get(fk_name)
            if not src_vg:
                continue

            # Create or get target vertex group
            dst_vg = obj.vertex_groups.get(d_name)
            if not dst_vg:
                dst_vg = obj.vertex_groups.new(name=d_name)

            # Copy weights
            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group == src_vg.index and g.weight > 0:
                        dst_vg.add([v.index], g.weight, 'REPLACE')
                        transferred_count += 1
                        break

            # Clear source bone weights (critical to prevent explosion!)
            src_vg.remove([v.index for v in obj.data.vertices])

        # Set FK bones to non-deform
        bone = armature.data.bones.get(fk_name)
        if bone:
            bone.use_deform = False

        message = f"Copied {transferred_count} vertices from {fk_name} to {d_name}"
        return True, message


class HipBlendZoneRule(WeightTransferRule):
    """Hip Blend Zone rule.

    Creates a smooth transition zone in the hip/thigh area where weights
    blend from D-bone to lower body bone.
    """

    def apply(self, armature, mesh_objects, rule: data_structures.WeightMappingRule) -> Tuple[bool, str]:
        """Create hip blend zone."""
        d_name = rule.source_bone
        lower_name = rule.target_bone
        blend_frac = rule.blend_threshold  # e.g., 0.46 = top 46% of thigh
        modified_count = 0

        for obj in mesh_objects:
            if obj.type != 'MESH' or not obj.vertex_groups:
                continue

            d_vg = obj.vertex_groups.get(d_name)
            lower_vg = obj.vertex_groups.get(lower_name)

            if not (d_vg and lower_vg):
                continue

            # Get leg bone position
            leg_bone = armature.data.bones.get(d_name.replace("D.", "").replace("D.L", "左足").replace("D.R", "右足"))
            if not leg_bone:
                continue

            mw = obj.matrix_world
            arm_mw = armature.matrix_world
            leg_head_z = (arm_mw @ leg_bone.head_local).z

            # Apply blend zone
            for v in obj.data.vertices:
                # Find current D-bone weight
                d_weight = 0.0
                for g in v.groups:
                    if g.group == d_vg.index:
                        d_weight = g.weight
                        break

                # In blend zone: gradually add lower body weight
                if 0.0 < d_weight < 1.0:
                    # Linear blend: higher D-weight = less transition to lower
                    blend_amount = (1.0 - d_weight) * (1.0 - blend_frac)
                    if blend_amount > 0.001:
                        lower_vg.add([v.index], blend_amount, 'ADD')
                        modified_count += 1

        message = f"Created hip blend zone: {d_name} ↔ {lower_name} ({modified_count} vertices)"
        return True, message


class TwistBoneGradientRule(WeightTransferRule):
    """Twist bone weight gradient rule.

    Distributes weights from parent bone to twist bone using a gradient
    based on distance from the bone's axis.
    """

    def apply(self, armature, mesh_objects, rule: data_structures.WeightMappingRule) -> Tuple[bool, str]:
        """Create twist bone weight gradient."""
        # TODO: Implement gradient calculation along bone axis
        message = f"Twist gradient rule not yet implemented for {rule.source_bone} → {rule.target_bone}"
        return False, message


class NormalizeWeightsRule(WeightTransferRule):
    """Normalize vertex weights rule.

    Ensures that each vertex has total weight ≤ 1.0 for deform bones.
    """

    def apply(self, armature, mesh_objects, rule: data_structures.WeightMappingRule) -> Tuple[bool, str]:
        """Normalize all vertex weights."""
        normalized_count = 0
        deform_bones = {b.name for b in armature.data.bones if b.use_deform}

        for obj in mesh_objects:
            if obj.type != 'MESH' or not obj.vertex_groups:
                continue

            vg_idx_map = {vg.index: vg.name for vg in obj.vertex_groups}

            for v in obj.data.vertices:
                # Calculate total weight for deform bones only
                total = sum(
                    g.weight for g in v.groups
                    if g.group in vg_idx_map and vg_idx_map[g.group] in deform_bones
                )

                # Skip if weight is too low (boundary vertices)
                if total < 0.3:
                    continue

                # Normalize if exceeds 1.0
                if total > 1.001:
                    scale = 1.0 / total
                    for g in v.groups:
                        if g.group in vg_idx_map and vg_idx_map[g.group] in deform_bones:
                            g.weight *= scale
                    normalized_count += 1

        message = f"Normalized {normalized_count} vertices to weight ≤ 1.0"
        return True, message


class OrphanWeightTransferRule(WeightTransferRule):
    """Transfer weights from orphaned bones.

    Orphaned bones are those that couldn't be mapped or are auxiliary bones.
    Transfer their weights to the nearest deform bone.
    """

    def apply(self, armature, mesh_objects, rule: data_structures.WeightMappingRule) -> Tuple[bool, str]:
        """Transfer orphaned bone weights to nearest deform bone."""
        # TODO: Implement orphan detection and nearest bone transfer
        message = f"Orphan transfer rule not yet fully implemented"
        return False, message


# Rule handler mapping
RULE_HANDLERS: Dict[str, WeightTransferRule] = {
    data_structures.WeightRuleType.FK_TO_D.value: FKToDBoneRule(),
    data_structures.WeightRuleType.HIP_BLEND.value: HipBlendZoneRule(),
    data_structures.WeightRuleType.TWIST.value: TwistBoneGradientRule(),
    data_structures.WeightRuleType.NORMALIZE.value: NormalizeWeightsRule(),
    data_structures.WeightRuleType.ORPHAN_TRANSFER.value: OrphanWeightTransferRule(),
}


def apply_all_weight_rules(armature, mesh_objects, rules: List[data_structures.WeightMappingRule]) \
        -> Dict[str, any]:
    """Execute all weight rules in order.

    Returns a detailed report of what was done.

    Args:
        armature: Blender armature object
        mesh_objects: List of mesh objects to process
        rules: List of WeightMappingRule objects to apply

    Returns:
        Dictionary with execution results and logs
    """
    results = {
        'total_rules': len(rules),
        'applied_rules': [],
        'failed_rules': [],
        'logs': []
    }

    # Sort rules by order if specified
    sorted_rules = sorted(rules, key=lambda r: r.order if hasattr(r, 'order') else 0)

    for rule in sorted_rules:
        handler = RULE_HANDLERS.get(rule.rule_type)
        if not handler:
            error_msg = f"Unknown rule type: {rule.rule_type}"
            results['failed_rules'].append({'rule': rule, 'error': error_msg})
            results['logs'].append(f"[ERROR] {error_msg}")
            continue

        try:
            success, message = handler.apply(armature, mesh_objects, rule)
            if success:
                results['applied_rules'].append({'rule': rule, 'message': message})
                results['logs'].append(f"[OK] {message}")
            else:
                results['failed_rules'].append({'rule': rule, 'error': message})
                results['logs'].append(f"[WARNING] {message}")
        except Exception as e:
            error_msg = f"Exception in {rule.rule_type}: {e}"
            results['failed_rules'].append({'rule': rule, 'error': error_msg})
            results['logs'].append(f"[ERROR] {error_msg}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Legacy Functions (kept for backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────

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
