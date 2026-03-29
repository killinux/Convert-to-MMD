"""
对比两个骨架的上半身结构和位置
用法：在Blender中运行此脚本，确保有两个骨架在Scene中
"""

import bpy
from mathutils import Vector

def analyze_spine_structure(armature, name_prefix=""):
    """分析脊椎骨架结构"""
    bones_to_check = [
        "上半身", "上半身1", "上半身2", "上半身3",
        "腰", "グルーブ", "センター",
        "下半身", "首", "頭"
    ]
    
    results = []
    mw = armature.matrix_world
    
    for bone_name in bones_to_check:
        b = armature.data.bones.get(bone_name)
        if not b:
            results.append(f"{name_prefix}{bone_name}: ❌ 不存在")
            continue
        
        # 世界坐标位置
        head_world = (mw @ b.head_local)
        tail_world = (mw @ b.tail_local)
        length = (tail_world - head_world).length
        
        # 父级关系
        parent_name = b.parent.name if b.parent else "无"
        
        # 属性
        deform_flag = "✓变形" if b.use_deform else "✗非变形"
        
        results.append(
            f"{name_prefix}{bone_name:12} | "
            f"父级:{parent_name:12} | "
            f"长度:{length:6.3f} | "
            f"头:{head_world.z:7.3f} | "
            f"{deform_flag}"
        )
    
    return results


def main():
    scene = bpy.context.scene
    armatures = [obj for obj in scene.objects if obj.type == 'ARMATURE']
    
    if len(armatures) < 2:
        print("❌ 需要至少2个骨架对象来进行对比")
        print(f"   当前找到: {len(armatures)} 个")
        return
    
    arm1 = armatures[0]
    arm2 = armatures[1]
    
    print("=" * 100)
    print(f"【对比骨架】")
    print(f"  左侧: {arm1.name}")
    print(f"  右侧: {arm2.name}")
    print("=" * 100)
    
    results1 = analyze_spine_structure(arm1, f"{arm1.name:20} | ")
    results2 = analyze_spine_structure(arm2, f"{arm2.name:20} | ")
    
    print("\n【脊椎骨架结构对比】\n")
    print(f"{'骨骼名':70} | {'父级':12} | {'长度':8} | {'头Z坐标':9} | {'属性'}")
    print("-" * 140)
    
    # 并排显示
    max_len = max(len(results1), len(results2))
    for i in range(max_len):
        r1 = results1[i] if i < len(results1) else ""
        r2 = results2[i] if i < len(results2) else ""
        print(f"{r1:70} || {r2}")
    
    print("\n【差异分析】\n")
    
    # 检查父级关系差异
    for bone_name in ["上半身", "上半身1", "上半身2", "腰"]:
        b1 = arm1.data.bones.get(bone_name)
        b2 = arm2.data.bones.get(bone_name)
        
        if not b1 or not b2:
            continue
        
        parent1 = b1.parent.name if b1.parent else "无"
        parent2 = b2.parent.name if b2.parent else "无"
        
        if parent1 != parent2:
            print(f"⚠️  {bone_name} 父级不同:")
            print(f"    {arm1.name}: {parent1}")
            print(f"    {arm2.name}: {parent2}")
    
    # 检查长度差异
    print("\n【骨骼长度对比】\n")
    mw1 = arm1.matrix_world
    mw2 = arm2.matrix_world
    
    for bone_name in ["上半身", "上半身1", "上半身2", "上半身3"]:
        b1 = arm1.data.bones.get(bone_name)
        b2 = arm2.data.bones.get(bone_name)
        
        if not b1 or not b2:
            continue
        
        len1 = ((mw1 @ b1.tail_local) - (mw1 @ b1.head_local)).length
        len2 = ((mw2 @ b2.tail_local) - (mw2 @ b2.head_local)).length
        
        if len1 > 0:
            ratio = len2 / len1
            status = "✓" if 0.95 < ratio < 1.05 else "⚠️"
            print(f"{status} {bone_name:12} | {arm1.name}: {len1:.4f} | {arm2.name}: {len2:.4f} | 比例: {ratio:.2%}")
    
    # 检查Z轴位置（身高差异）
    print("\n【Z轴位置对比（身高）】\n")
    
    z_positions = {}
    for bone_name in ["センター", "腰", "上半身", "上半身1", "上半身2", "首", "頭"]:
        b1 = arm1.data.bones.get(bone_name)
        b2 = arm2.data.bones.get(bone_name)
        
        if b1 and b2:
            z1 = (mw1 @ b1.head_local).z
            z2 = (mw2 @ b2.head_local).z
            diff = z2 - z1
            status = "✓" if abs(diff) < 0.01 else "⚠️"
            print(f"{status} {bone_name:12} | {arm1.name}: {z1:7.4f} | {arm2.name}: {z2:7.4f} | 差异: {diff:+7.4f}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
