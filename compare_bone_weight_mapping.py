"""
详细对比XPS初始模型和目标模型的骨骼-权重关系
找出相似的骨骼映射对
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

def get_mesh_objects(collection_name):
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        return []
    meshes = []
    for obj in coll.all_objects:
        if obj.type == 'MESH':
            meshes.append(obj)
    return meshes

def count_weighted_vertices(mesh_obj, bone_name):
    vg = mesh_obj.vertex_groups.get(bone_name)
    if not vg:
        return 0, 0.0
    count = 0
    total_weight = 0.0
    for v in mesh_obj.data.vertices:
        for g in v.groups:
            if g.group == vg.index and g.weight > 0.001:
                count += 1
                total_weight += g.weight
                break
    return count, total_weight

def analyze_bone_weights(armature, mesh_objects, spine_bones):
    """分析骨架的脊椎骨骼权重分布"""
    results = {}
    
    for bone_name in spine_bones:
        total_verts = 0
        total_weight_sum = 0.0
        
        for mesh in mesh_objects:
            verts, weight_sum = count_weighted_vertices(mesh, bone_name)
            total_verts += verts
            total_weight_sum += weight_sum
        
        if total_verts > 0:
            avg_weight = total_weight_sum / total_verts
        else:
            avg_weight = 0.0
        
        results[bone_name] = {
            'verts': total_verts,
            'total_weight': total_weight_sum,
            'avg_weight': avg_weight,
            'has_weight': total_verts > 0
        }
    
    return results

def main():
    arm_xps = get_armature_from_collection("Collection")
    arm_target = get_armature_from_collection("Collection2")
    meshes_xps = get_mesh_objects("Collection")
    meshes_target = get_mesh_objects("Collection2")
    
    if not arm_xps or not arm_target:
        print("❌ 找不到骨架")
        return
    
    # XPS脊椎骨骼
    spine_xps = [
        "pelvis", "abdomenLower", "abdomenUpper",
        "chestLower", "chestUpper",
        "neckLower", "neckUpper", "head"
    ]
    
    # MMD脊椎骨骼
    spine_mmd = [
        "腰", "下半身",
        "上半身", "上半身1", "上半身2", "上半身3",
        "首", "首1", "頭"
    ]
    
    weights_xps = analyze_bone_weights(arm_xps, meshes_xps, spine_xps)
    weights_mmd = analyze_bone_weights(arm_target, meshes_target, spine_mmd)
    
    print("=" * 140)
    print("【XPS初始模型 vs 目标MMD模型 - 骨骼权重详细对比】")
    print("=" * 140)
    
    # 显示XPS的权重分布
    print("\n【XPS初始模型的脊椎骨骼权重分布】\n")
    print(f"{'骨骼名':20} | {'顶点数':8} | {'总权重':10} | {'平均权重':10} | {'权重%':8} | {'状态'}")
    print("-" * 80)
    
    total_verts_xps = sum(w['verts'] for w in weights_xps.values())
    total_weight_xps = sum(w['total_weight'] for w in weights_xps.values())
    
    for bone_name in spine_xps:
        w = weights_xps[bone_name]
        if w['verts'] > 0:
            weight_pct = (w['verts'] / total_verts_xps) * 100
            status = "✓"
        else:
            weight_pct = 0.0
            status = "✗"
        
        print(f"{bone_name:20} | {w['verts']:8} | {w['total_weight']:10.2f} | {w['avg_weight']:10.4f} | {weight_pct:7.1f}% | {status}")
    
    print(f"\n{'总计':20} | {total_verts_xps:8} | {total_weight_xps:10.2f}")
    
    # 显示MMD的权重分布
    print("\n" + "=" * 140)
    print("\n【目标MMD模型的脊椎骨骼权重分布】\n")
    print(f"{'骨骼名':20} | {'顶点数':8} | {'总权重':10} | {'平均权重':10} | {'权重%':8} | {'状态'}")
    print("-" * 80)
    
    total_verts_mmd = sum(w['verts'] for w in weights_mmd.values())
    total_weight_mmd = sum(w['total_weight'] for w in weights_mmd.values())
    
    for bone_name in spine_mmd:
        w = weights_mmd[bone_name]
        if w['verts'] > 0:
            weight_pct = (w['verts'] / total_verts_mmd) * 100
            status = "✓"
        else:
            weight_pct = 0.0
            status = "✗"
        
        print(f"{bone_name:20} | {w['verts']:8} | {w['total_weight']:10.2f} | {w['avg_weight']:10.4f} | {weight_pct:7.1f}% | {status}")
    
    print(f"\n{'总计':20} | {total_verts_mmd:8} | {total_weight_mmd:10.2f}")
    
    # 分析相似点
    print("\n" + "=" * 140)
    print("\n【权重分布相似性分析】\n")
    
    # 列出有权重的骨骼
    xps_weighted = [(b, weights_xps[b]) for b in spine_xps if weights_xps[b]['has_weight']]
    mmd_weighted = [(b, weights_mmd[b]) for b in spine_mmd if weights_mmd[b]['has_weight']]
    
    print(f"XPS有权重的骨骼: {len(xps_weighted)}个")
    for b, w in xps_weighted:
        print(f"  {b:20} - {w['verts']:6} 顶点 ({w['verts']/total_verts_xps*100:5.1f}%)")
    
    print(f"\nMMD有权重的骨骼: {len(mmd_weighted)}个")
    for b, w in mmd_weighted:
        print(f"  {b:20} - {w['verts']:6} 顶点 ({w['verts']/total_verts_mmd*100:5.1f}%)")
    
    # 找相似的权重比例
    print("\n【权重比例相似的骨骼对（可能的映射）】\n")
    print(f"{'XPS骨骼':20} | {'权重%':8} | → | {'MMD骨骼':20} | {'权重%':8} | {'相似度'}")
    print("-" * 85)
    
    for xps_bone, xps_w in xps_weighted:
        xps_pct = (xps_w['verts'] / total_verts_xps) * 100
        
        # 找最相似的MMD骨骼
        best_match = None
        best_similarity = 0
        
        for mmd_bone, mmd_w in mmd_weighted:
            mmd_pct = (mmd_w['verts'] / total_verts_mmd) * 100
            # 相似度：百分比差异越小越相似
            similarity = 100 - abs(xps_pct - mmd_pct)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (mmd_bone, mmd_pct)
        
        if best_match:
            match_bone, match_pct = best_match
            status = "⭐" if best_similarity > 70 else "◎" if best_similarity > 50 else "◇"
            print(f"{xps_bone:20} | {xps_pct:7.1f}% | → | {match_bone:20} | {match_pct:7.1f}% | {best_similarity:5.1f}% {status}")
    
    print("\n【图例】⭐ = 高相似度 (>70%)  |  ◎ = 中等相似度 (>50%)  |  ◇ = 低相似度")
    
    print("\n" + "=" * 140)

if __name__ == "__main__":
    main()
