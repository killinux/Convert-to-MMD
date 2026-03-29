"""
XPS to PMX Conversion Pipeline

New architecture supports flexible mappings:
- Stage 0: Apply bone mapping (rename XPS bones to MMD names)
- Stage 1: Rebuild skeleton (cut, complete, adjust parents)
- Stage 2: Apply A-Pose
- Stage 3: Apply weight rules (transparent, rule-based)
- Stage 4: Setup constraints and bone groups
- Stage 5: Export PMX
"""

import bpy
from mathutils import Vector, Matrix
from typing import Tuple, List, Optional, Dict
from . import mapping, weights
from .mapping import data_structures


# ─────────────────────────────────────────────────────────────────────────────
# New Stage Functions (Flexible Mapping System)
# ─────────────────────────────────────────────────────────────────────────────

def stage_apply_bone_mapping(armature, config: data_structures.MappingConfiguration) \
        -> Tuple[bool, str]:
    """Stage 0: Apply bone mapping configuration.

    Renames XPS bones to MMD names according to the mapping configuration.
    Also synchronizes all vertex group names.

    Args:
        armature: Target armature object
        config: MappingConfiguration with bone mappings

    Returns:
        (success, message)
    """
    if not armature or armature.type != 'ARMATURE':
        return False, "Invalid armature"

    try:
        # Enter edit mode to rename bones
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        renamed_count = 0
        failed_bones = []

        # Rename bones according to mapping
        for xps_name, mapping_obj in config.bone_mappings.items():
            bone = armature.data.edit_bones.get(xps_name)
            if not bone:
                failed_bones.append(xps_name)
                continue

            try:
                bone.name = mapping_obj.mmd_name
                renamed_count += 1
            except Exception as e:
                failed_bones.append(f"{xps_name}: {e}")

        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Sync vertex groups with renamed bones
        synced_count = 0
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.vertex_groups:
                for xps_name, mapping_obj in config.bone_mappings.items():
                    vg = obj.vertex_groups.get(xps_name)
                    if vg:
                        vg.name = mapping_obj.mmd_name
                        synced_count += 1

        message = f"Renamed {renamed_count} bones, synced {synced_count} vertex groups"
        if failed_bones:
            message += f" (failed: {len(failed_bones)})"

        return True, message

    except Exception as e:
        return False, f"Error during bone mapping: {e}"
    finally:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')


def stage_apply_weight_rules(armature, config: data_structures.MappingConfiguration = None) \
        -> Tuple[bool, str]:
    """Stage 3: Apply weight transfer rules via operator.

    Args:
        armature: Target armature object
        config: MappingConfiguration with weight rules (optional)

    Returns:
        (success, message)
    """
    if not armature or armature.type != 'ARMATURE':
        return False, "Invalid armature"

    try:
        # Call the Stage 3 operator
        bpy.context.view_layer.objects.active = armature
        bpy.ops.xpspmx_pipeline.stage_3_apply_weight_rules()
        return True, "权重规则应用完成"

    except Exception as e:
        return False, f"权重规则应用失败: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# Legacy Pipeline (refactored to use new stages)
# ─────────────────────────────────────────────────────────────────────────────

def run_full_pipeline(armature, context, output_path, skip_apose=False,
                      config: Optional[data_structures.MappingConfiguration] = None):
    """
    执行完整转换流水线（支持灵活映射系统）
    返回 (success: bool, results: list[str])

    新流程：
    - Stage 0: 应用骨骼映射（如果提供了配置）
    - Stage 1: 重建骨架
    - Stage 2: A-Pose 转换
    - Stage 3: 应用权重规则（或使用旧的权重修复）
    - Stage 4: 付与和 IK 设置
    - Stage 5: 导出 PMX
    """
    results = []

    try:
        # Stage 0: 应用骨骼映射（新系统）
        if config:
            success, msg = stage_apply_bone_mapping(armature, config)
            results.append(f"Stage 0: {msg}")
            if not success:
                results.append("警告：骨骼映射可能不完整，继续处理")

        # Stage 1: 重建骨架
        success, msg = stage_rebuild_skeleton(armature, context)
        results.append(f"Stage 1: {msg}")
        if not success:
            return False, results

        # Stage 2: A-Pose转换
        if not skip_apose:
            success, msg = stage_pose_to_apose(armature, context)
            results.append(f"Stage 2: {msg}")
            if not success:
                return False, results
        else:
            results.append("Stage 2: 跳过（已是A-Pose）")

        # Stage 3: 权重处理
        if config and config.weight_rules:
            # 使用新的规则系统
            success, msg = stage_apply_weight_rules(armature, config)
            results.append(f"Stage 3 (新规则): {msg}")
        else:
            # 使用旧的权重修复方法
            success, msg = stage_fix_weights(armature, context)
            results.append(f"Stage 3 (旧方法): {msg}")

        if not success:
            return False, results

        # Stage 4: 付与和IK设置
        success, msg = stage_setup_additional_transform(armature, context)
        results.append(f"Stage 4: {msg}")
        if not success:
            return False, results

        # Stage 5: 导出PMX
        success, msg = stage_export_pmx(armature, context, output_path)
        results.append(f"Stage 5: {msg}")
        if not success:
            return False, results

        return True, results

    except Exception as e:
        results.append(f"ERROR: {str(e)}")
        return False, results


def stage_rebuild_skeleton(armature, context):
    """
    Stage 1: 重建骨架
    - 创建缺失骨骼（グルーブ、腰、D骨、IK骨等）
    - 调整骨骼属性和父级关系
    """
    try:
        # Call the Stage 1 operator
        bpy.context.view_layer.objects.active = armature
        bpy.ops.xpspmx_pipeline.stage_1_rebuild_skeleton()
        return True, "骨架重建完成"

    except Exception as e:
        return False, f"骨架重建失败: {str(e)}"


def stage_pose_to_apose(armature, context):
    """
    Stage 2: 转换为A-Pose
    - 旋转手臂到标准A-Pose（左腕+37°，右腕-37°）
    - 烘焙姿态到rest pose
    """
    try:
        # Call the Stage 2 operator
        bpy.context.view_layer.objects.active = armature
        bpy.ops.xpspmx_pipeline.stage_2_apply_apose()
        return True, "A-Pose转换完成"

    except Exception as e:
        return False, f"A-Pose转换失败: {str(e)}"


def stage_fix_weights(armature, context):
    """
    Stage 3: 修复权重
    - 复制FK腿骨权重到D骨
    - 孤立骨转移
    - 髋部渐变区创建
    - 权重归一化
    """
    try:
        mesh_objects = [
            o for o in context.scene.objects
            if o.type == 'MESH' and any(
                m.type == 'ARMATURE' and m.object == armature
                for m in o.modifiers
            )
        ]

        if not mesh_objects:
            return True, "未找到网格（权重处理跳过）"

        # 调用权重处理函数
        modified = weights.transfer_leg_weights_to_d_bones(armature, mesh_objects)
        if modified > 0:
            return True, f"权重修复完成（{modified}顶点转移）"
        else:
            return True, "权重正常（无需修复）"

    except Exception as e:
        return False, f"权重修复失败: {str(e)}"


def stage_setup_additional_transform(armature, context):
    """
    Stage 4: 设置付与和IK约束
    - 配置D骨的additional_transform（付与）
    - 配置腰取消骨
    - 添加IK约束
    """
    try:
        # Call the Stage 4 operator
        bpy.context.view_layer.objects.active = armature
        bpy.ops.xpspmx_pipeline.stage_4_setup_constraints()
        return True, "付与和IK约束设置完成"

    except Exception as e:
        return False, f"付与设置失败: {str(e)}"


def stage_export_pmx(armature, context, output_path):
    """
    Stage 5: 导出PMX
    - 调用 Stage 5 操作符进行 PMX 导出
    """
    try:
        if not output_path:
            return False, "未指定输出路径"

        # Call the Stage 5 operator
        bpy.context.view_layer.objects.active = armature
        bpy.ops.xpspmx_pipeline.stage_5_export_pmx(filepath=output_path)
        return True, f"导出完成: {output_path}"

    except Exception as e:
        return False, f"导出失败: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# Note: Helper functions moved to Stage 4 operator
# ─────────────────────────────────────────────────────────────────────────────
