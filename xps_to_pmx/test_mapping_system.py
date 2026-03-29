"""
测试脚本：快速测试灵活映射系统

在 Blender Python 控制台中运行：
1. 导入 XPS 模型，选中骨架
2. 运行此脚本测试自动检测和映射功能
"""

import bpy
from . import mapping


def test_auto_detection():
    """Test skeleton type detection."""
    print("\n" + "="*60)
    print("TEST 1: 自动检测骨骼类型")
    print("="*60)

    armature = bpy.context.active_object
    if not armature or armature.type != 'ARMATURE':
        print("❌ 请选择一个骨架！")
        return

    print(f"选中的骨架：{armature.name}")
    print(f"骨骼数量：{len(armature.data.bones)}")

    # Detect skeleton type
    skeleton_type = mapping.detection.detect_skeleton_type(armature)
    print(f"✓ 检测到的骨骼类型：{skeleton_type}")

    # Analyze structure
    structure = mapping.detection.analyze_skeleton_structure(armature)
    print(f"✓ 骨骼层级深度：{structure['hierarchy_depth']}")
    print(f"  - 脊椎骨：{'有' if structure['has_spine_bones'] else '无'}")
    print(f"  - 手臂骨：{'有' if structure['has_arm_bones'] else '无'}")
    print(f"  - 腿部骨：{'有' if structure['has_leg_bones'] else '无'}")

    return armature


def test_auto_mapping(armature):
    """Test automatic bone mapping."""
    print("\n" + "="*60)
    print("TEST 2: 自动骨骼映射")
    print("="*60)

    # Auto-map bones
    config = mapping.detection.auto_map_bones(armature)
    print(f"✓ 自动映射了 {len(config.bone_mappings)} 个骨骼")

    # Show high-confidence mappings
    print("\n映射结果（置信度 > 80%）：")
    high_conf = [(xps, m) for xps, m in config.bone_mappings.items() if m.confidence > 0.8]
    for i, (xps_name, mapping_obj) in enumerate(sorted(high_conf, key=lambda x: x[1].confidence, reverse=True)[:10]):
        conf_pct = mapping_obj.confidence * 100
        print(f"  {i+1}. {xps_name:20} → {mapping_obj.mmd_name:12} ({conf_pct:.0f}%)")

    if len(high_conf) > 10:
        print(f"  ... 还有 {len(high_conf) - 10} 个")

    # Show low-confidence mappings
    low_conf = [(xps, m) for xps, m in config.bone_mappings.items() if m.confidence <= 0.8]
    if low_conf:
        print(f"\n需要手动检查的映射（置信度 ≤ 80%，共 {len(low_conf)} 个）：")
        for i, (xps_name, mapping_obj) in enumerate(sorted(low_conf, key=lambda x: x[1].confidence)[:5]):
            conf_pct = mapping_obj.confidence * 100
            print(f"  {i+1}. {xps_name:20} → {mapping_obj.mmd_name:12} ({conf_pct:.0f}%)")
        if len(low_conf) > 5:
            print(f"  ... 还有 {len(low_conf) - 5} 个")

    return config


def test_weight_rules(config):
    """Test weight rule suggestion."""
    print("\n" + "="*60)
    print("TEST 3: 权重规则建议")
    print("="*60)

    # Suggest rules
    rules = mapping.detection.suggest_weight_rules(config)
    print(f"✓ 建议了 {len(rules)} 条权重规则：")

    for i, rule in enumerate(rules, 1):
        print(f"\n  {i}. {rule.rule_type}")
        if rule.source_bone:
            print(f"     源：{rule.source_bone}")
        if rule.target_bone:
            print(f"     目标：{rule.target_bone}")
        print(f"     区域：{rule.zone} | 梯度：{rule.falloff_type}")

    return config


def test_config_serialization(config):
    """Test JSON serialization."""
    print("\n" + "="*60)
    print("TEST 4: 配置序列化")
    print("="*60)

    # Validate
    is_valid, errors = config.validate()
    if is_valid:
        print("✓ 配置验证通过")
    else:
        print(f"⚠ 配置有 {len(errors)} 个错误：")
        for error in errors[:3]:
            print(f"  - {error}")

    # Serialize to JSON
    json_str = config.to_json()
    json_lines = json_str.split('\n')
    print(f"\n✓ 成功序列化为 JSON（{len(json_str)} 字节）")
    print(f"  前 5 行：")
    for line in json_lines[:5]:
        print(f"  {line}")

    return json_str


def test_full_workflow():
    """Run full workflow test."""
    print("\n" + "#"*60)
    print("# 灵活映射系统 - 完整工作流测试")
    print("#"*60)

    # Step 1: Auto detection
    armature = test_auto_detection()
    if not armature:
        return

    # Step 2: Auto mapping
    config = test_auto_mapping(armature)

    # Step 3: Weight rules
    config = test_weight_rules(config)

    # Step 4: Serialization
    json_str = test_config_serialization(config)

    print("\n" + "#"*60)
    print("✅ 所有测试完成！")
    print("#"*60)
    print("\n下一步：")
    print("1. 在 ② MAPPING EDITOR 面板中编辑骨骼映射")
    print("2. 在 ③ WEIGHT RULES 面板中调整权重规则")
    print("4. 在 ④ VALIDATION & PREVIEW 面板中验证配置")
    print("5. 点击 [ ▶ Start Conversion ] 开始转换")


# Run test
if __name__ == "__main__":
    test_full_workflow()
else:
    # When imported, provide the test function
    pass
