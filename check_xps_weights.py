"""
检查XPS模型中脊椎相关骨骼的权重分配情况
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


def get_mesh_objects(collection_name):
    """从指定Collection中获取所有网格对象"""
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        return []
    
    meshes = []
    for obj in coll.all_objects:
        if obj.type == 'MESH':
            meshes.append(obj)
    return meshes


def count_weighted_vertices(mesh_obj, bone_name):
    """统计某个骨骼有权重的顶点数"""
    vg = mesh_obj.vertex_groups.get(bone_name)
    if not vg:
        return 0, 0.0  # 修复：返回元组
    
    count = 0
    total_weight = 0.0
    for v in mesh_obj.data.vertices:
        for g in v.groups:
            if g.group == vg.index and g.weight > 0.001:
                count += 1
                total_weight += g.weight
                break
    
    return count, total_weight


def main():
    arm = get_armature_from_collection("Collection")
    meshes = get_mesh_objects("Collection")
    
    if not arm:
        print("❌ 找不到XPS骨架")
        return
    
    if not meshes:
        print("❌ 找不到网格对象")
        return
    
    print("=" * 100)
    print(f"【XPS模型权重分析】")
    print(f"骨架: {arm.name}")
    print(f"网格对象: {len(meshes)} 个 - {', '.join(m.name for m in meshes)}")
    print("=" * 100)
    
    # 检查脊椎相关骨骼
    spine_bones = [
        "root", "hip", "pelvis", 
        "abdomenLower", "abdomenUpper",
        "chestLower", "chestUpper",
        "neckLower", "neckUpper",
        "head"
    ]
    
    print("\n【脊椎相关骨骼的权重统计】\n")
    print(f"{'骨骼名':20} | {'顶点数':8} | {'总权重':10} | {'平均权重':10} | {'状态'}")
    print("-" * 80)
    
    spine_weight_map = {}
    
    for bone_name in spine_bones:
        total_verts = 0
        total_weight_sum = 0.0
        
        for mesh in meshes:
            verts, weight_sum = count_weighted_vertices(mesh, bone_name)
            total_verts += verts
            total_weight_sum += weight_sum
        
        if total_verts > 0:
            avg_weight = total_weight_sum / total_verts
            status = "✓ 有权重"
        else:
            avg_weight = 0.0
            status = "✗ 无权重"
        
        spine_weight_map[bone_name] = total_verts
        
        print(f"{bone_name:20} | {total_verts:8} | {total_weight_sum:10.2f} | {avg_weight:10.4f} | {status}")
    
    # 分析结果
    print("\n【权重分析结果】\n")
    
    bones_with_weight = [b for b in spine_bones if spine_weight_map[b] > 0]
    bones_without_weight = [b for b in spine_bones if spine_weight_map[b] == 0]
    
    if bones_with_weight:
        print(f"✓ 有权重的骨骼 ({len(bones_with_weight)}个):")
        for b in bones_with_weight:
            print(f"  - {b:20} ({spine_weight_map[b]:5} 顶点)")
    
    if bones_without_weight:
        print(f"\n✗ 无权重的骨骼 ({len(bones_without_weight)}个) - 可以删除或跳过:")
        for b in bones_without_weight:
            print(f"  - {b}")
    
    # 特别关注abdomenLower
    print("\n【特别检查：abdomenLower】")
    al_weight = spine_weight_map.get("abdomenLower", 0)
    if al_weight == 0:
        print("✓ abdomenLower 无权重 → 可以直接跳过，不需要映射")
    else:
        print(f"⚠️ abdomenLower 有权重 ({al_weight} 顶点) → 需要转移权重到上半身或下半身")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
