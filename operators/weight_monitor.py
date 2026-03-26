"""权重健康监控系统 — 每步执行后自动拍快照，检测权重退化。"""

import bpy
import json
import time

# 监控的关键骨骼（MMD 变形骨）
WATCHED_BONES = [
    "足D.L", "足D.R", "ひざD.L", "ひざD.R", "足首D.L", "足首D.R",
    "足先EX.L", "足先EX.R",
    "下半身", "上半身", "上半身1", "上半身2", "上半身3",
    "左肩", "右肩", "左腕", "右腕", "左ひじ", "右ひじ",
    "肩.L", "肩.R", "肩P.L", "肩P.R", "肩C.L", "肩C.R",
]

# D系腿骨与躯干骨的冲突阈值
D_CONFLICT_THRESHOLD = 0.6


def _get_mesh_objects(context, armature):
    return [o for o in context.scene.objects
            if o.type == 'MESH' and any(
                m.type == 'ARMATURE' and m.object == armature for m in o.modifiers)]


def take_weight_snapshot(armature, mesh_objects):
    """单次遍历采集所有权重健康指标。目标 <100ms。"""
    bone_counts = {}
    bone_sums = {}

    # 预建 VG index → bone name 映射（只关注 WATCHED_BONES）
    # 同时收集髋部检测所需的 index
    hip_data = {}  # per-obj: {obj: {"idx_d_l", "idx_d_r", "idx_s"}}

    for obj in mesh_objects:
        idx_to_name = {}
        for name in WATCHED_BONES:
            vg = obj.vertex_groups.get(name)
            if vg:
                idx_to_name[vg.index] = name

        # 髋部相关 index
        vg_dl = obj.vertex_groups.get("足D.L")
        vg_dr = obj.vertex_groups.get("足D.R")
        vg_s = obj.vertex_groups.get("下半身")
        idx_dl = vg_dl.index if vg_dl else -1
        idx_dr = vg_dr.index if vg_dr else -1
        idx_s = vg_s.index if vg_s else -1

        mw = obj.matrix_world

        # 第一遍：找 足D.L/R 的 z_max（用于髋部过渡区判定）
        z_max_l = z_max_r = -999999.0
        for v in obj.data.vertices:
            for g in v.groups:
                if g.group == idx_dl and g.weight > 0.001:
                    vz = (mw @ v.co).z
                    if vz > z_max_l:
                        z_max_l = vz
                elif g.group == idx_dr and g.weight > 0.001:
                    vz = (mw @ v.co).z
                    if vz > z_max_r:
                        z_max_r = vz

        z_top_l = z_max_l - 1.5
        z_top_r = z_max_r - 1.5

        hip_left_binary = 0
        hip_left_blend = 0
        hip_right_binary = 0
        hip_right_blend = 0
        conflict_count = 0

        # 第二遍：采集所有指标
        for v in obj.data.vertices:
            vz = None  # lazy compute
            wd_l = wd_r = ws = 0.0

            for g in v.groups:
                gidx = g.group
                w = g.weight

                # 关键骨骼计数
                if gidx in idx_to_name and w > 0.001:
                    name = idx_to_name[gidx]
                    bone_counts[name] = bone_counts.get(name, 0) + 1
                    bone_sums[name] = bone_sums.get(name, 0.0) + w

                # 髋部指标收集
                if gidx == idx_dl:
                    wd_l = w
                elif gidx == idx_dr:
                    wd_r = w
                elif gidx == idx_s:
                    ws = w

            # 髋部过渡区判定（左）
            if wd_l > 0.001 and z_max_l > -999990:
                if vz is None:
                    vz = (mw @ v.co).z
                if vz >= z_top_l:
                    if ws > 0.05:
                        hip_left_blend += 1
                    elif wd_l > 0.85:
                        hip_left_binary += 1

            # 髋部过渡区判定（右）
            if wd_r > 0.001 and z_max_r > -999990:
                if vz is None:
                    vz = (mw @ v.co).z
                if vz >= z_top_r:
                    if ws > 0.05:
                        hip_right_blend += 1
                    elif wd_r > 0.85:
                        hip_right_binary += 1

            # 冲突检测：D系≥0.6 且 下半身>0
            d_total = wd_l + wd_r
            if d_total >= D_CONFLICT_THRESHOLD and ws > 0.001:
                conflict_count += 1

    total_verts = sum(len(obj.data.vertices) for obj in mesh_objects)

    return {
        "bone_counts": bone_counts,
        "bone_sums": bone_sums,
        "hip_left_binary": hip_left_binary,
        "hip_right_binary": hip_right_binary,
        "hip_left_blend": hip_left_blend,
        "hip_right_blend": hip_right_blend,
        "conflict_count": conflict_count,
        "total_verts": total_verts,
    }


def evaluate_health(snapshot):
    """绝对健康评估（不需要前后对比），返回 (status, issues)。"""
    issues = []

    lb = snapshot.get("hip_left_binary", 0)
    rb = snapshot.get("hip_right_binary", 0)
    if lb > 100 or rb > 100:
        issues.append(f"髋部硬切割: 左={lb} 右={rb}")

    cc = snapshot.get("conflict_count", 0)
    if cc > 50:
        issues.append(f"D系/下半身冲突: {cc}顶点")

    # 检查关键骨骼是否有权重
    for bone in ["足D.L", "足D.R", "下半身"]:
        if snapshot["bone_counts"].get(bone, 0) == 0:
            issues.append(f"{bone} 无权重")

    status = "error" if issues else "ok"
    return status, issues


def compare_snapshots(pre, post):
    """对比前后快照，返回 (status, issues)。"""
    issues = []

    # 1. 髋部二值化检测
    for side, key in [("左", "hip_left_binary"), ("右", "hip_right_binary")]:
        pre_val = pre.get(key, 0)
        post_val = post.get(key, 0)
        if post_val > 100 and post_val > pre_val + 50:
            issues.append(f"髋部{side}硬切割 {pre_val}→{post_val}")

    # 2. 冲突增加
    pre_cc = pre.get("conflict_count", 0)
    post_cc = post.get("conflict_count", 0)
    if post_cc > pre_cc + 50:
        issues.append(f"冲突顶点 +{post_cc - pre_cc}")

    # 3. 关键骨骼权重大幅下降
    for bone in ["足D.L", "足D.R", "下半身", "上半身", "上半身2"]:
        pre_sum = pre.get("bone_sums", {}).get(bone, 0)
        post_sum = post.get("bone_sums", {}).get(bone, 0)
        if pre_sum > 10 and post_sum < pre_sum * 0.3:
            issues.append(f"{bone} 权重骤降 {pre_sum:.0f}→{post_sum:.0f}")

    # 4. 关键骨骼顶点数归零
    for bone in ["足D.L", "足D.R", "下半身"]:
        pre_cnt = pre.get("bone_counts", {}).get(bone, 0)
        post_cnt = post.get("bone_counts", {}).get(bone, 0)
        if pre_cnt > 100 and post_cnt == 0:
            issues.append(f"{bone} 顶点全丢失")

    has_error = any("骤降" in i or "全丢失" in i or "硬切割" in i for i in issues)
    status = "error" if has_error else ("warning" if issues else "ok")
    return status, issues


def store_snapshot(armature, step_id, step_label, metrics, status, issues):
    """将快照存入骨架自定义属性。"""
    try:
        existing = json.loads(armature.get("wm_snapshots", "{}"))
    except (json.JSONDecodeError, TypeError):
        existing = {}

    existing[step_id] = {
        "label": step_label,
        "status": status,
        "issues": issues,
        "time": time.strftime("%H:%M:%S"),
        "hip_l_bin": metrics.get("hip_left_binary", 0),
        "hip_r_bin": metrics.get("hip_right_binary", 0),
        "hip_l_blend": metrics.get("hip_left_blend", 0),
        "hip_r_blend": metrics.get("hip_right_blend", 0),
        "conflict": metrics.get("conflict_count", 0),
    }
    armature["wm_snapshots"] = json.dumps(existing, ensure_ascii=False)


def auto_check_after_step(context, armature, step_id, step_label):
    """步骤执行后调用：拍快照 → 评估 → 存储 → 更新 UI。"""
    mesh_objects = _get_mesh_objects(context, armature)
    if not mesh_objects:
        return

    snapshot = take_weight_snapshot(armature, mesh_objects)

    # 尝试与上一步对比
    try:
        existing = json.loads(armature.get("wm_snapshots", "{}"))
    except (json.JSONDecodeError, TypeError):
        existing = {}

    prev_keys = sorted(existing.keys())
    if prev_keys and "metrics" not in existing.get(prev_keys[-1], {}):
        # 旧格式没有完整 metrics，只做绝对评估
        status, issues = evaluate_health(snapshot)
    elif prev_keys:
        # 用最近一步的 metrics 对比
        prev_entry = existing[prev_keys[-1]]
        # 构造伪 pre snapshot 用于对比
        pre_approx = {
            "hip_left_binary": prev_entry.get("hip_l_bin", 0),
            "hip_right_binary": prev_entry.get("hip_r_bin", 0),
            "conflict_count": prev_entry.get("conflict", 0),
            "bone_sums": {},
            "bone_counts": {},
        }
        status, issues = compare_snapshots(pre_approx, snapshot)
        # 同时做绝对评估，取更严重的
        abs_status, abs_issues = evaluate_health(snapshot)
        if abs_status == "error" and status != "error":
            status = abs_status
        issues = list(set(issues + abs_issues))
    else:
        status, issues = evaluate_health(snapshot)

    store_snapshot(armature, step_id, step_label, snapshot, status, issues)

    # 更新 Scene 属性供 UI 显示
    try:
        step_status = json.loads(context.scene.get("wm_step_status", "{}"))
    except (json.JSONDecodeError, TypeError):
        step_status = {}
    step_status[step_id] = status
    context.scene["wm_step_status"] = json.dumps(step_status, ensure_ascii=False)

    # 更新最近一次检查结果
    if issues:
        context.scene["wm_last_check_result"] = f"⚠️ {step_label}: {'; '.join(issues[:3])}"
    else:
        context.scene["wm_last_check_result"] = f"✅ {step_label}: 权重健康"


class OBJECT_OT_weight_health_check(bpy.types.Operator):
    """手动运行全局权重健康检查"""
    bl_idname = "object.weight_health_check"
    bl_label = "权重体检"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}

        mesh_objects = _get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        snapshot = take_weight_snapshot(armature, mesh_objects)
        status, issues = evaluate_health(snapshot)
        store_snapshot(armature, "manual", "手动体检", snapshot, status, issues)

        # 更新 UI
        try:
            step_status = json.loads(context.scene.get("wm_step_status", "{}"))
        except (json.JSONDecodeError, TypeError):
            step_status = {}
        step_status["manual"] = status
        context.scene["wm_step_status"] = json.dumps(step_status, ensure_ascii=False)

        # 构建详细报告
        bc = snapshot["bone_counts"]
        parts = []
        parts.append(f"足D: 左={bc.get('足D.L', 0)} 右={bc.get('足D.R', 0)}")
        parts.append(f"下半身={bc.get('下半身', 0)}")
        parts.append(f"髋部渐变: 左blend={snapshot['hip_left_blend']} 右blend={snapshot['hip_right_blend']}")
        parts.append(f"硬切割: 左={snapshot['hip_left_binary']} 右={snapshot['hip_right_binary']}")
        parts.append(f"冲突={snapshot['conflict_count']}")

        result_text = ' | '.join(parts)
        context.scene["wm_last_check_result"] = result_text

        if issues:
            self.report({'WARNING'}, f"⚠️ {'; '.join(issues)}")
        else:
            self.report({'INFO'}, f"✅ 权重健康 | {result_text}")
        return {'FINISHED'}


class OBJECT_OT_weight_clear_monitor(bpy.types.Operator):
    """清除权重监控历史记录"""
    bl_idname = "object.weight_clear_monitor"
    bl_label = "清除监控记录"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            if "wm_snapshots" in armature:
                del armature["wm_snapshots"]
        context.scene["wm_step_status"] = "{}"
        context.scene["wm_last_check_result"] = ""
        self.report({'INFO'}, "已清除监控记录")
        return {'FINISHED'}
