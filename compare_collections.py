"""
对比Collection（XPS初始模型）和Collection2（目标模型）的骨架结构
"""

import bpy
from mathutils import Vector

def get_armature_from_collection(collection_name):
    """从指定Collection中获取骨架"""
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        return None
    
    for obj in coll.all_objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def analyze_spine_structure(armature, name_prefix=""):
    """分析脊椎骨架结构"""
    if not armature:
        return [f"{name_prefix}❌ 找不到骨架"]
    
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
            f"头Z:{head_world.z:7.3f} | "
            f"{deform_flag}"
        )
    
    return results


def main():
    print("=" * 140)
    print("【从Collections中提取骨架】")
    
    arm_collection = get_armature_from_collection("Collection")
    arm_collection2 = get_armature_from_collection("Collection2")
    
    if not arm_collection:
        print("❌ Collection 中找不到骨架")
        return
    
    if not arm_collection2:
        print("❌ Collection2 中找不到骨架")
        return
    
    print(f"  Collection: {arm_collection.name}")
    print(f"  Collection2: {arm_collection2.name}")
    print("=" * 140)
    
    results1 = analyze_spine_structure(arm_collection, f"XPS原始模型          | ")
    results2 = analyze_spine_structure(arm_collection2, f"目标参考模型         | ")
    
    print("\n【脊椎骨架结构对比】\n")
    print(f"{'模型':30} | {'骨骼名':12} | {'父级':12} | {'长度':8} | {'头Z坐标':9} | {'属性'}")
    print("-" * 140)
    
    # 并排显示
    max_len = max(len(results1), len(results2))
    for i in range(max_len):
        r1 = results1[i] if i < len(results1) else ""
        r2 = results2[i] if i < len(results2) else ""
        print(f"{r1:75} || {r2}")
    
    print("\n【差异分析】\n")
    
    # 检查父级关系差异
    print("【父级关系检查】")
    has_parent_diff = False
    for bone_name in ["上半身", "上半身1", "上半身2", "腰", "下半身"]:
        b1 = arm_collection.data.bones.get(bone_name)
        b2 = arm_collection2.data.bones.get(bone_name)
        
        if not b1 or not b2:
            continue
        
        parent1 = b1.parent.name if b1.parent else "无"
        parent2 = b2.parent.name if b2.parent else "无"
        
        status = "✓" if parent1 == parent2 else "⚠️"
        print(f"{status} {bone_name:12} | XPS: {parent1:12} | 目标: {parent2:12}")
        if parent1 != parent2:
            has_parent_diff = True
    
    if not has_parent_diff:
        print("✓ 父级关系完全一致")
    
    # 检查变形属性
    print("\n【变形属性检查】")
    control_bones = ["センター", "グルーブ", "腰"]
    for bone_name in control_bones:
        b1 = arm_collection.data.bones.get(bone_name)
        b2 = arm_collection2.data.bones.get(bone_name)
        
        if b1 and b2:
            deform1 = "✓变形" if b1.use_deform else "✗非变形"
            deform2 = "✓变形" if b2.use_deform else "✗非变形"
            status = "✓" if b1.use_deform == b2.use_deform else "⚠️"
            print(f"{status} {bone_name:12} | XPS: {deform1:8} | 目标: {deform2:8}")
    
    # 检查长度差异
    print("\n【骨骼长度对比】")
    mw1 = arm_collection.matrix_world
    mw2 = arm_collection2.matrix_world
    
    spine_bones = ["上半身", "上半身1", "上半身2", "上半身3"]
    for bone_name in spine_bones:
        b1 = arm_collection.data.bones.get(bone_name)
        b2 = arm_collection2.data.bones.get(bone_name)
        
        if not b1 or not b2:
            continue
        
        len1 = ((mw1 @ b1.tail_local) - (mw1 @ b1.head_local)).length
        len2 = ((mw2 @ b2.tail_local) - (mw2 @ b2.head_local)).length
        
        if len1 > 0.001:
            ratio = len2 / len1
            tolerance = 0.05  # ±5%
            status = "✓" if (1-tolerance) < ratio < (1+tolerance) else "⚠️"
            print(f"{status} {bone_name:12} | XPS: {len1:7.4f} | 目标: {len2:7.4f} | 比例: {ratio:.2%}")
    
    # 检查Z轴位置（身高）
    print("\n【Z轴位置对比（身高基准）】")
    
    height_diff_total = 0
    count = 0
    for bone_name in ["センター", "腰", "上半身", "上半身1", "上半身2", "首", "頭"]:
        b1 = arm_collection.data.bones.get(bone_name)
        b2 = arm_collection2.data.bones.get(bone_name)
        
        if b1 and b2:
            z1 = (mw1 @ b1.head_local).z
            z2 = (mw2 @ b2.head_local).z
            diff = z2 - z1
            status = "✓" if abs(diff) < 0.1 else "⚠️"
            print(f"{status} {bone_name:12} | XPS: {z1:8.4f} | 目标: {z2:8.4f} | 差异: {diff:+8.4f}")
            height_diff_total += diff
            count += 1
    
    if count > 0:
        avg_diff = height_diff_total / count
        print(f"\n平均Z轴差异: {avg_diff:+.4f}")
        
        if abs(avg_diff) < 0.1:
            print("✓ 两个模型的身高基本一致（可以进行后续处理）")
        else:
            print(f"⚠️ 模型存在显著的身高差异（可能需要缩放调整）")
    
    print("\n" + "=" * 140)


if __name__ == "__main__":
    main()
