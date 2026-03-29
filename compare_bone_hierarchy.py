"""
详细分析两个骨骼的父子关系链
"""

import bpy

def get_armature_from_collection(collection_name):
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        return None
    for obj in coll.all_objects:
        if obj.type == 'ARMATURE':
            return obj
    return None

def get_parent_chain(bone):
    """获取骨骼的完整父链"""
    chain = []
    current = bone
    while current:
        chain.insert(0, current.name)
        current = current.parent
    return chain

def show_spine_hierarchy(armature, root_bone_names):
    """显示脊椎链的完整层次结构"""
    print(f"\n【{armature.name} - 脊椎层次结构】\n")
    
    for root_name in root_bone_names:
        root = armature.data.bones.get(root_name)
        if not root:
            print(f"❌ {root_name} 不存在\n")
            continue
        
        # 显示根骨骼
        print(f"📍 {root_name}")
        
        # 递归显示子骨骼
        def show_children(bone, indent=1):
            children = [b for b in armature.data.bones if b.parent == bone]
            children.sort(key=lambda b: b.head.z, reverse=True)  # 按Z高度排序
            
            for child in children:
                # 只显示脊椎相关的
                if any(kw in child.name.lower() for kw in 
                       ["abdomen", "chest", "neck", "head", "upper", "lower", 
                        "上", "下", "首", "腰", "身", "頭"]):
                    prefix = "  " * indent + "├─ "
                    mw = armature.matrix_world
                    head = (mw @ child.head_local)
                    length = ((mw @ child.tail_local) - head).length
                    
                    # 获取该骨骼的权重顶点数
                    weight_info = ""
                    
                    print(f"{prefix}{child.name:25} [长度:{length:6.3f}]")
                    show_children(child, indent + 1)
        
        show_children(root)

def analyze_hierarchy_alignment(arm_xps, arm_mmd):
    """分析两个骨骼系统的父子关系对齐"""
    print("\n【父子关系对齐分析】\n")
    
    # XPS脊椎链
    xps_spine = ["pelvis", "abdomenLower", "abdomenUpper", "chestLower", 
                 "chestUpper", "neckLower", "neckUpper", "head"]
    
    # MMD脊椎链（有权重的）
    mmd_spine = ["下半身", "上半身", "上半身1", "上半身2", "上半身3", "首", "首1", "頭"]
    
    print("XPS脊椎链的父级关系：\n")
    print(f"{'骨骼':20} | {'父级':20} | {'深度':4}")
    print("-" * 50)
    
    for bone_name in xps_spine:
        b = arm_xps.data.bones.get(bone_name)
        if b:
            parent_name = b.parent.name if b.parent else "无"
            chain = get_parent_chain(b)
            depth = len(chain) - 1
            print(f"{bone_name:20} | {parent_name:20} | {depth:4}")
    
    print("\n" + "=" * 50)
    print("\nMMD脊椎链的父级关系：\n")
    print(f"{'骨骼':20} | {'父级':20} | {'深度':4}")
    print("-" * 50)
    
    for bone_name in mmd_spine:
        b = arm_mmd.data.bones.get(bone_name)
        if b:
            parent_name = b.parent.name if b.parent else "无"
            chain = get_parent_chain(b)
            depth = len(chain) - 1
            print(f"{bone_name:20} | {parent_name:20} | {depth:4}")
    
    # 分析链长度
    print("\n【链长度分析】\n")
    
    xps_chain = get_parent_chain(arm_xps.data.bones.get("head"))
    mmd_chain = get_parent_chain(arm_mmd.data.bones.get("頭"))
    
    print(f"XPS 'head' 的完整父链 (深度{len(xps_chain)-1}):")
    print(" → ".join(xps_chain))
    
    print(f"\nMMD '頭' 的完整父链 (深度{len(mmd_chain)-1}):")
    print(" → ".join(mmd_chain))
    
    # 比较脊椎骨的直接父子关系
    print("\n【脊椎骨直接父子关系对比】\n")
    print(f"{'XPS':25} | {'父级':15} | {'MMD':25} | {'父级':15}")
    print("-" * 85)
    
    for i, (xps_bone, mmd_bone) in enumerate(zip(xps_spine, mmd_spine)):
        xps_b = arm_xps.data.bones.get(xps_bone)
        mmd_b = arm_mmd.data.bones.get(mmd_bone)
        
        if xps_b and mmd_b:
            xps_parent = xps_b.parent.name if xps_b.parent else "无"
            mmd_parent = mmd_b.parent.name if mmd_b.parent else "无"
            
            match = "✓" if (xps_parent in mmd_parent or mmd_parent in xps_parent) else "✗"
            print(f"{xps_bone:25} | {xps_parent:15} {match} | {mmd_bone:25} | {mmd_parent:15}")

def main():
    arm_xps = get_armature_from_collection("Collection")
    arm_mmd = get_armature_from_collection("Collection2")
    
    if not arm_xps or not arm_mmd:
        print("❌ 找不到骨架")
        return
    
    print("=" * 100)
    print("【XPS vs MMD - 骨骼父子关系详细分析】")
    print("=" * 100)
    
    # 显示XPS的脊椎层次
    show_spine_hierarchy(arm_xps, ["root", "hip"])
    
    # 显示MMD的脊椎层次
    show_spine_hierarchy(arm_mmd, ["全ての親"])
    
    # 分析对齐
    analyze_hierarchy_alignment(arm_xps, arm_mmd)
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    main()
