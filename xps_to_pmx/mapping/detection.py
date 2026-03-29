"""Auto-detection functions for skeleton type and bone mappings.

This module provides functions to:
1. Detect the skeleton type (XPS standard, female, male, etc.)
2. Auto-map bones based on name similarity, position, and weight distribution
3. Analyze weight distribution across bones
4. Suggest weight transfer rules
"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher

try:
    import bpy
except ImportError:
    bpy = None

from . import data_structures


def detect_skeleton_type(armature) -> str:
    """Detect the XPS skeleton variant type.

    Analyzes bone names, count, and structure to identify:
    - xps_standard: Standard XPS format
    - xps_female: Female variant
    - xps_male: Male variant
    - custom: Unknown variant

    Args:
        armature: Blender armature object

    Returns:
        Skeleton type string
    """
    if not armature or armature.type != 'ARMATURE':
        return "unknown"

    bone_names = [b.name for b in armature.data.bones]
    bone_count = len(bone_names)

    # Detect by bone count and name patterns
    has_standard_spine = any('abdomen' in name.lower() for name in bone_names)
    has_limbs = any('arm' in name.lower() or 'leg' in name.lower() for name in bone_names)

    # TODO: Implement more sophisticated detection
    # For now, just return standard if it looks like XPS
    if has_standard_spine and has_limbs and bone_count > 40:
        return "xps_standard"

    return "custom"


def analyze_skeleton_structure(armature) -> Dict[str, any]:
    """Analyze skeleton structure: bone count, hierarchy, naming patterns.

    Returns:
        Dictionary with skeleton analysis info
    """
    if not armature or armature.type != 'ARMATURE':
        return {}

    bones = armature.data.bones
    result = {
        'total_bones': len(bones),
        'bone_names': [b.name for b in bones],
        'naming_patterns': {},
        'hierarchy_depth': _calculate_hierarchy_depth(armature),
        'has_spine_bones': any('spine' in b.name.lower() or 'abdomen' in b.name.lower() for b in bones),
        'has_arm_bones': any('arm' in b.name.lower() for b in bones),
        'has_leg_bones': any('leg' in b.name.lower() for b in bones),
    }

    # Analyze naming patterns
    for bone in bones:
        name_lower = bone.name.lower()
        if 'spine' in name_lower or 'abdomen' in name_lower:
            result['naming_patterns']['spine'] = bone.name
        if 'arm' in name_lower:
            result['naming_patterns']['arm'] = bone.name
        if 'leg' in name_lower:
            result['naming_patterns']['leg'] = bone.name

    return result


def _calculate_hierarchy_depth(armature) -> int:
    """Calculate the maximum depth of bone hierarchy."""
    max_depth = 0

    def calculate_depth(bone, depth=0):
        nonlocal max_depth
        max_depth = max(max_depth, depth)
        for child in bone.children:
            calculate_depth(child, depth + 1)

    for bone in armature.data.bones:
        if not bone.parent:  # Root bones
            calculate_depth(bone, 0)

    return max_depth


def _classify_bone_type(bone_name: str) -> str:
    """Classify bone type based on name patterns.

    Args:
        bone_name: Name of the bone

    Returns:
        Bone type string
    """
    name_lower = bone_name.lower()

    if any(word in name_lower for word in ['spine', 'abdomen', 'chest', 'neck', 'head']):
        return data_structures.BoneType.SPINE.value
    elif any(word in name_lower for word in ['arm', 'shoulder']):
        return data_structures.BoneType.ARM.value
    elif any(word in name_lower for word in ['leg', 'thigh', 'knee', 'ankle']):
        return data_structures.BoneType.LEG.value
    elif any(word in name_lower for word in ['hand', 'wrist']):
        return data_structures.BoneType.HAND.value
    elif any(word in name_lower for word in ['finger', 'thumb']):
        return data_structures.BoneType.FINGER.value
    elif any(word in name_lower for word in ['eye']):
        return data_structures.BoneType.EYE.value
    else:
        return data_structures.BoneType.CONTROL.value


def name_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0~1).

    Uses SequenceMatcher ratio and also checks for keyword matches.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity score (0~1)
    """
    # Direct ratio
    ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    # Bonus for exact keyword matches
    keywords1 = set(re.findall(r'\b\w+\b', str1.lower()))
    keywords2 = set(re.findall(r'\b\w+\b', str2.lower()))
    common_keywords = keywords1 & keywords2

    if common_keywords:
        keyword_bonus = min(0.2, len(common_keywords) * 0.05)
        ratio = min(1.0, ratio + keyword_bonus)

    return ratio


def auto_map_bones(armature, reference_config: Optional[data_structures.MappingConfiguration] = None) \
        -> data_structures.MappingConfiguration:
    """Auto-detect and map XPS bones to MMD bones.

    Uses name similarity, position, and weight distribution to find the best mapping.

    Args:
        armature: XPS skeleton (Blender armature)
        reference_config: Reference configuration to use for mapping hints

    Returns:
        MappingConfiguration with auto-detected mappings
    """
    if not armature or armature.type != 'ARMATURE':
        return data_structures.MappingConfiguration(name="empty", source_skeleton_type="unknown")

    config = data_structures.MappingConfiguration(
        name=f"Auto-detected from {armature.name}",
        source_skeleton_type=detect_skeleton_type(armature)
    )

    # Load reference config if not provided
    if not reference_config:
        try:
            import json
            import os
            preset_path = os.path.join(os.path.dirname(__file__), 'presets', 'standard_xps.json')
            if os.path.exists(preset_path):
                reference_config = data_structures.MappingConfiguration.load_from_file(preset_path)
        except Exception:
            reference_config = None

    # Map each bone
    mmd_bone_names = set()
    if reference_config:
        mmd_bone_names = {m.mmd_name for m in reference_config.bone_mappings.values()}

    for bone in armature.data.bones:
        parent_name = bone.parent.name if bone.parent else None
        best_match = None
        best_confidence = 0.0

        # Try to find best match from reference config
        if reference_config:
            for ref_xps, ref_mapping in reference_config.bone_mappings.items():
                similarity = name_similarity(bone.name, ref_xps)
                if similarity > best_confidence:
                    best_confidence = similarity
                    best_match = ref_mapping.mmd_name

        # Create mapping
        mapping = data_structures.BoneMapping(
            xps_name=bone.name,
            mmd_name=best_match if best_match else bone.name,
            confidence=min(1.0, best_confidence + 0.2),  # Boost confidence a bit
            parent_xps=parent_name,
            parent_mmd=None,  # Will be filled in by build_parent_mapping
            bone_type=_classify_bone_type(bone.name),
            is_deform=True,
        )
        config.bone_mappings[bone.name] = mapping

    # Fill in parent relationships
    build_parent_mapping(armature, config)

    return config


def analyze_weight_distribution(mesh_objects: List) -> Dict[str, float]:
    """Analyze which bones have the most vertex weight in the mesh.

    Returns:
        Dict mapping bone name -> weight percentage (0~100)
    """
    if not mesh_objects:
        return {}

    bone_weights = {}

    for mesh in mesh_objects:
        if mesh.type != 'MESH' or not mesh.vertex_groups:
            continue

        total_weight = 0.0

        # Calculate total weight across all vertex groups
        for vg in mesh.vertex_groups:
            weight_sum = sum(
                v.weight for v in mesh.data.vertices
                for g in v.groups if g.group == vg.index
            )
            bone_weights[vg.name] = bone_weights.get(vg.name, 0.0) + weight_sum
            total_weight += weight_sum

        # Convert to percentages
        if total_weight > 0:
            for bone_name in bone_weights:
                bone_weights[bone_name] = (bone_weights[bone_name] / total_weight) * 100

    return bone_weights


def suggest_weight_rules(config: data_structures.MappingConfiguration) \
        -> List[data_structures.WeightMappingRule]:
    """Suggest weight transfer rules based on mapping and weights.

    Args:
        config: Mapping configuration

    Returns:
        List of suggested weight rules
    """
    rules = []
    order_counter = 0

    # Helper to find MMD name from XPS name
    def find_mmd_name(xps_name: str) -> Optional[str]:
        for mapping in config.bone_mappings.values():
            if mapping.xps_name == xps_name:
                return mapping.mmd_name
        return None

    # Rule 1: FK → D-Bone for leg bones (critical for IK rigs)
    leg_fk_to_d_pairs = [
        ("left_leg_thigh", "足D.L"),
        ("left_leg_knee", "ひざD.L"),
        ("left_leg_ankle", "足首D.L"),
        ("right_leg_thigh", "足D.R"),
        ("right_leg_knee", "ひざD.R"),
        ("right_leg_ankle", "足首D.R"),
    ]

    for src_xps, dst_mmd in leg_fk_to_d_pairs:
        src_mmd = find_mmd_name(src_xps)
        if src_mmd:
            rule = data_structures.WeightMappingRule(
                source_bone=src_xps,
                target_bone=dst_mmd,
                transfer_ratio=1.0,
                zone="zone3",
                falloff_type="linear",
                blend_threshold=0.5,
                is_hip_cancel=False,
                rule_type=data_structures.WeightRuleType.FK_TO_D.value,
                order=order_counter
            )
            rules.append(rule)
            order_counter += 1

    # Rule 2: Hip Blend Zone (if D-bones exist)
    if any("足D" in m.mmd_name for m in config.bone_mappings.values()):
        rule = data_structures.WeightMappingRule(
            source_bone="足D.L",
            target_bone="下半身",
            transfer_ratio=1.0,
            zone="zone2",
            falloff_type="linear",
            blend_threshold=0.46,  # Top 46% of thigh
            is_hip_cancel=False,
            rule_type=data_structures.WeightRuleType.HIP_BLEND.value,
            order=order_counter
        )
        rules.append(rule)
        order_counter += 1

        rule = data_structures.WeightMappingRule(
            source_bone="足D.R",
            target_bone="下半身",
            transfer_ratio=1.0,
            zone="zone2",
            falloff_type="linear",
            blend_threshold=0.46,
            is_hip_cancel=False,
            rule_type=data_structures.WeightRuleType.HIP_BLEND.value,
            order=order_counter
        )
        rules.append(rule)
        order_counter += 1

    # Rule 3: Orphan bone transfer (find unmapped bones)
    orphan_bones = []
    for mapping in config.bone_mappings.values():
        if all(c.isascii() for c in mapping.mmd_name):  # Still English name = orphan
            orphan_bones.append(mapping.xps_name)

    if orphan_bones:
        rule = data_structures.WeightMappingRule(
            source_bone="",  # Auto-detect
            target_bone="",  # Auto-detect nearest
            transfer_ratio=1.0,
            zone="zone1",
            falloff_type="linear",
            blend_threshold=0.5,
            is_hip_cancel=False,
            rule_type=data_structures.WeightRuleType.ORPHAN_TRANSFER.value,
            order=order_counter
        )
        rules.append(rule)
        order_counter += 1

    # Rule 4: Weight normalization (always last)
    rule = data_structures.WeightMappingRule(
        source_bone="",
        target_bone="",
        transfer_ratio=1.0,
        zone="zone1",
        falloff_type="linear",
        blend_threshold=0.3,
        is_hip_cancel=False,
        rule_type=data_structures.WeightRuleType.NORMALIZE.value,
        order=order_counter
    )
    rules.append(rule)

    # Update config with suggested rules
    config.weight_rules = rules

    return rules


def build_parent_mapping(xps_armature, config: data_structures.MappingConfiguration) -> None:
    """Fill in parent_mmd mappings based on XPS parent hierarchy.

    This updates the MappingConfiguration in-place, ensuring that if
    a bone's parent is mapped, the parent_mmd is set correctly.

    Args:
        xps_armature: XPS skeleton
        config: Configuration to update
    """
    # Build reverse mapping: XPS name -> mapping
    xps_to_mapping = {m.xps_name: m for m in config.bone_mappings.values()}

    for bone in xps_armature.data.bones:
        if bone.name not in xps_to_mapping:
            continue

        mapping = xps_to_mapping[bone.name]

        # Find parent mapping
        if bone.parent and bone.parent.name in xps_to_mapping:
            parent_mapping = xps_to_mapping[bone.parent.name]
            mapping.parent_mmd = parent_mapping.mmd_name


def validate_parent_relationships(config: data_structures.MappingConfiguration) -> Dict[str, dict]:
    """Validate that parent-child relationships are correctly mapped.

    Checks if the parent mapping relationship in XPS matches the parent mapping in MMD.

    Args:
        config: Mapping configuration to validate

    Returns:
        Dictionary mapping xps_bone_name -> {
            'is_valid': bool,
            'parent_xps': str,
            'parent_mmd_expected': str,
            'parent_mmd_actual': str,
            'message': str
        }
    """
    results = {}

    # Build XPS name -> mapping lookup
    xps_to_mapping = {m.xps_name: m for m in config.bone_mappings.values()}

    for xps_name, mapping in config.bone_mappings.items():
        result = {
            'is_valid': True,
            'parent_xps': mapping.parent_xps,
            'parent_mmd_expected': None,
            'parent_mmd_actual': mapping.parent_mmd,
            'message': '✓ Parent relationship correct'
        }

        # If this bone has a parent in XPS
        if mapping.parent_xps and mapping.parent_xps in xps_to_mapping:
            parent_mapping = xps_to_mapping[mapping.parent_xps]
            expected_parent_mmd = parent_mapping.mmd_name
            result['parent_mmd_expected'] = expected_parent_mmd

            # Check if parent_mmd matches expected
            if mapping.parent_mmd != expected_parent_mmd:
                result['is_valid'] = False
                result['message'] = f"⚠️ Parent mismatch: expected '{expected_parent_mmd}', got '{mapping.parent_mmd}'"
        elif mapping.parent_xps:
            # Parent XPS bone not found in mapping
            result['is_valid'] = False
            result['message'] = f"⚠️ Parent XPS bone '{mapping.parent_xps}' not found in mapping"
        else:
            # This is a root bone (no parent)
            result['message'] = '✓ Root bone (no parent)'

        results[xps_name] = result

    return results
