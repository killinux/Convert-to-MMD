"""
显示XPS原始模型的所有骨骼和目标模型的脊椎链结构对比
"""

import bpy

def get_armature_from_collection(collection_name):
    """从指定Collection中获取骨架"""
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        return None
    
    for obj in coll.all_objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def show_bone_hierarchy(armature, indent=0, parent=None):
    """递归显示骨骼层次结构"""
    lines = []
    for bone in armature.data.bones:
        if bone.parent == parent:
            prefix = "  " * indent + "├─ " if indent > 0 else ""
            mw = armature.matrix_world
            head = (mw @ bone.head_local)
            length = ((mw @ bone.tail_local) - head).length
            deform = "✓" if bone.use_deform else "✗"
            lines.append(f"{prefix}{bone.name:30} {deform} 长度:{length:6.3f}")
            lines.extend(show_bone_hierarchy(armature, indent + 1, bone))
    return lines


def find_spine_bones(armature):
    """找出脊椎相关的骨骼"""
    spine_keywords = ["spine", "upper", "middle", "lower", "neck", "head", "センター", "グルーブ", "腰", "上半身", "首", "頭"]
    
    spine_bones = []
    for bone in armature.data.bones:
        if any(kw.lower() in bone.name.lower() for kw in spine_keywords):
            spine_bones.append(bone)
    
    return sorted(spine_bones, key=lambda b: (b.head_local.z, b.name), reverse=True)


def main():
    arm_xps = get_armature_from_collection("Collection")
    arm_target = get_armature_from_collection("Collection2")
    
    print("=" * 100)
    print(f"【XPS原始模型骨骼检查】")
    print("=" * 100)
    
    if not arm_xps:
        print("❌ Collection 中找不到骨架")
        return
    
    print(f"\n骨架名: {arm_xps.name}")
    print(f"总骨骼数: {len(arm_xps.data.bones)}\n")
    
    # 显示脊椎相关骨骼
    print("【脊椎相关骨骼（按Z高度从高到低）】\n")
    spine_bones = find_spine_bones(arm_xps)
    
    mw = arm_xps.matrix_world
    for bone in spine_bones:
        head = (mw @ bone.head_local)
        tail = (mw @ bone.tail_local)
        length = (tail - head).length
        parent_name = bone.parent.name if bone.parent else "无"
        deform = "✓变形" if bone.use_deform else "✗非变形"
        
        print(f"{bone.name:25} | 父级:{parent_name:25} | 长度:{length:6.3f} | Z:{head.z:7.3f} | {deform}")
    
    # 显示所有骨骼的层次结构（只显示根骨骼及其子骨骼）
    print("\n【完整骨骼层次结构】\n")
    lines = show_bone_hierarchy(arm_xps)
    # 只显示前50行
    for line in lines[:50]:
        print(line)
    
    if len(lines) > 50:
        print(f"... 还有 {len(lines) - 50} 根骨骼")
    
    # 显示目标模型的脊椎链结构
    print("\n" + "=" * 100)
    print(f"【目标模型脊椎链结构（参考）】")
    print("=" * 100)
    
    if arm_target:
        print(f"\n骨架名: {arm_target.name}\n")
        
        spine_chain = []
        current = arm_target.data.bones.get("頭")
        while current:
            spine_chain.insert(0, current)
            current = current.parent
            if current and "全ての親" in current.name:
                spine_chain.insert(0, current)
                break
        
        mw_target = arm_target.matrix_world
        for i, bone in enumerate(spine_chain):
            head = (mw_target @ bone.head_local)
            tail = (mw_target @ bone.tail_local)
            length = (tail - head).length
            parent_name = bone.parent.name if bone.parent else "無"
            indent = "  " * (i // 2)
            
            print(f"{indent}{bone.name:25} | 父級:{parent_name:12} | 長度:{length:6.3f} | Z:{head.z:7.3f}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
