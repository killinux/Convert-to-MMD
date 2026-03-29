#!/usr/bin/env python3
"""
修复 standard_xps.json 以匹配增强的 BoneMapping 数据结构
"""

import json
from pathlib import Path

def load_mmd_standard():
    """加载 MMD 标准骨骼库"""
    mmd_file = Path(r"E:\mywork\Convert-to-MMD\xps_to_pmx\mapping\presets\mmd_standard_skeleton.json")
    with open(mmd_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 建立快速查询表
    lookup = {}
    for mmd_name, bone_def in data.get('bones', {}).items():
        lookup[mmd_name] = bone_def
    return lookup

def fix_preset():
    """修复 standard_xps.json"""
    preset_file = Path(r"E:\mywork\Convert-to-MMD\xps_to_pmx\mapping\presets\standard_xps.json")

    # 加载 MMD 标准
    mmd_lookup = load_mmd_standard()

    # 加载现有的 preset
    with open(preset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 修复每个 bone_mapping
    for xps_name, mapping in data.get('bone_mappings', {}).items():
        # 1. 将 "notes" 改为 "user_notes"
        if 'notes' in mapping:
            mapping['user_notes'] = mapping.pop('notes')

        # 2. 添加新字段
        mmd_name = mapping.get('mmd_name', '')

        # parent_mmd_expected: 从 MMD 标准库查询
        if mmd_name and mmd_name in mmd_lookup:
            parent_mmd_expected = mmd_lookup[mmd_name].get('parent_mmd')
        else:
            parent_mmd_expected = None

        # parent_match: 比较 parent_mmd 和 parent_mmd_expected
        parent_mmd = mapping.get('parent_mmd')
        parent_match = (parent_mmd == parent_mmd_expected) if parent_mmd_expected else True

        # is_unmapped: 检查是否有有效的 mmd_name 映射
        is_unmapped = not mmd_name or mmd_name == ""

        # 添加新字段
        mapping['parent_mmd_expected'] = parent_mmd_expected
        mapping['parent_match'] = parent_match
        mapping['is_unmapped'] = is_unmapped
        mapping['vertex_group_count'] = 0  # 初始化为 0，实际数据由 Blender 获取
        mapping['source_info'] = "standard_xps"

        print(f"✓ {xps_name:20} → {mmd_name:15} [parent_match={parent_match}, unmapped={is_unmapped}]")

    # 保存修复后的文件
    with open(preset_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 修复完成！已更新 {len(data['bone_mappings'])} 个骨骼映射")
    print(f"📁 保存到: {preset_file}")

if __name__ == '__main__':
    fix_preset()
