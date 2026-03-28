# bone_checks.py — 骨架完整性检测与修复
# 每项检测: check_xxx(armature) -> (ok: bool, issues: list[str])
# 每项修复: fix_xxx(armature, context) -> (success: bool, message: str)

import bpy
from mathutils import Vector


# ─── 工具 ────────────────────────────────────────────────────────────────────

class _EditMode:
    """上下文管理器：自动进出 Edit Mode，返回 edit_bones"""
    def __init__(self, armature, context):
        self.arm = armature
        self.ctx = context
    def __enter__(self):
        self.ctx.view_layer.objects.active = self.arm
        bpy.ops.object.mode_set(mode='EDIT')
        return self.arm.data.edit_bones
    def __exit__(self, *_):
        bpy.ops.object.mode_set(mode='OBJECT')


def _new_bone(eb, name, head, tail, parent_name=None, use_deform=True):
    """创建骨骼（若已存在则返回已有骨骼，不重复创建）。"""
    b = eb.get(name) or eb.new(name)
    b.head = head.copy() if hasattr(head, 'copy') else Vector(head)
    b.tail = tail.copy() if hasattr(tail, 'copy') else Vector(tail)
    b.use_connect = False
    b.use_deform = use_deform
    if parent_name:
        p = eb.get(parent_name)
        if p:
            b.parent = p
    return b


def _rename_bone(armature, context, old_name, new_name):
    """重命名骨骼，同步所有网格 vertex group。"""
    pb = armature.pose.bones.get(old_name)
    if not pb:
        return False
    pb.name = new_name
    for obj in context.scene.objects:
        if obj.type != 'MESH':
            continue
        vg = obj.vertex_groups.get(old_name)
        if vg:
            vg.name = new_name
    return True


# ─── Check 1: 脊椎骨链（上半身3 + 首1）─────────────────────────────────────

def check_spine_chain(armature):
    """检测脊椎链是否完整：需要 上半身3（连接上半身2和首/肩）、首1（连接首和頭）。"""
    b = armature.data.bones
    issues = []
    if not b.get("上半身3"):
        issues.append("缺少 上半身3（应位于 上半身2 和 首 之间）")
    if not b.get("首1"):
        issues.append("缺少 首1（应位于 首 和 頭 之间）")
    return len(issues) == 0, issues


def fix_spine_chain(armature, context):
    """修复脊椎链：创建 上半身3 和 首1，调整相关骨骼的父级。"""
    b = armature.data.bones
    need_ub3   = not b.get("上半身3")
    need_neck1 = not b.get("首1")
    if not need_ub3 and not need_neck1:
        return True, "脊椎骨链已完整，无需修复"

    try:
        with _EditMode(armature, context) as eb:
            # ── 上半身3（插入 上半身2 和 首 之间） ──────────────────────
            if need_ub3:
                ub2  = eb.get("上半身2")
                neck = eb.get("首")
                if ub2 and neck:
                    h = ub2.tail.copy()
                    t = neck.head.copy()
                    if (t - h).length < 0.005:
                        t = h + Vector((0, 0, 0.05))
                    ub3 = _new_bone(eb, "上半身3", h, t, "上半身2", use_deform=True)
                    neck.parent = ub3
                    neck.use_connect = False
                    # 将 肩P.L/R 以及直接挂在 上半身2 的肩骨迁移到 上半身3
                    for sn in ["肩P.L", "肩P.R", "左肩", "右肩"]:
                        sp = eb.get(sn)
                        if sp and sp.parent and sp.parent.name == "上半身2":
                            sp.parent = ub3

            # ── 首1（插入 首 和 頭 之间） ─────────────────────────────────
            if need_neck1:
                neck  = eb.get("首")
                head_b = eb.get("頭")
                if neck and head_b:
                    h = neck.tail.copy()
                    t = head_b.head.copy()
                    if (t - h).length < 0.005:
                        t = h + Vector((0, 0, 0.04))
                    n1 = _new_bone(eb, "首1", h, t, "首", use_deform=True)
                    head_b.parent = n1
                    head_b.use_connect = False
    except Exception as e:
        import traceback
        return False, traceback.format_exc()

    msgs = []
    if need_ub3:   msgs.append("已创建 上半身3")
    if need_neck1: msgs.append("已创建 首1")
    return True, "、".join(msgs)


# ─── Check 2: 肩骨链（肩P + 肩C）───────────────────────────────────────────

def check_shoulder_chain(armature):
    """检测肩骨链：需要 肩P.L/R（肩的父级）和 肩C.L/R（腕的父级）。"""
    b = armature.data.bones
    issues = []
    for side, jp in [(".L", "左"), (".R", "右")]:
        shl = b.get(f"{jp}肩")
        if not shl:
            continue  # 没有肩骨，跳过
        if not b.get(f"肩P{side}"):
            issues.append(f"缺少 肩P{side}")
        if not b.get(f"肩C{side}"):
            issues.append(f"缺少 肩C{side}")
        arm_b = b.get(f"{jp}腕")
        if arm_b and arm_b.parent and arm_b.parent.name == f"{jp}肩":
            issues.append(f"{jp}腕 直接挂在 {jp}肩（应通过 肩C{side} 连接）")
    return len(issues) == 0, issues


def fix_shoulder_chain(armature, context):
    """修复肩骨链：创建 肩P.L/R 和 肩C.L/R，调整 肩 和 腕 的父级。"""
    ok, issues = check_shoulder_chain(armature)
    if ok:
        return True, "肩骨链已完整，无需修复"

    try:
        with _EditMode(armature, context) as eb:
            # 查找最合适的肩P父级（上半身3 > 上半身2 > 上半身1 > 上半身）
            spine_priority = ["上半身3", "上半身2", "上半身1", "上半身"]
            upper_parent = next((p for p in spine_priority if eb.get(p)), None)

            for side, jp in [(".L", "左"), (".R", "右")]:
                shl = eb.get(f"{jp}肩")
                arm = eb.get(f"{jp}腕")
                if not shl:
                    continue

                pP = f"肩P{side}"
                pC = f"肩C{side}"

                # 肩P：短骨，位于肩头，父级为上半身3
                if not eb.get(pP):
                    _new_bone(eb, pP,
                              shl.head.copy(),
                              shl.head + Vector((0, 0, 0.025)),
                              upper_parent, use_deform=False)
                shl.parent = eb.get(pP)
                shl.use_connect = False

                # 肩C：短骨，位于肩尾（腕头部），父级为肩
                arm_head = arm.head.copy() if arm else shl.tail.copy()
                if not eb.get(pC):
                    _new_bone(eb, pC,
                              arm_head,
                              arm_head + Vector((0, 0, 0.025)),
                              f"{jp}肩", use_deform=False)
                if arm:
                    arm.parent = eb.get(pC)
                    arm.use_connect = False
    except Exception as e:
        import traceback
        return False, traceback.format_exc()

    return True, "已创建 肩P.L/R、肩C.L/R，重新连接肩骨链"


# ─── Check 3: 捩骨接入骨链 ───────────────────────────────────────────────────

def check_twist_chain(armature):
    """
    检测捩骨是否正确插入骨链：
      腕 → 腕捩 → ひじ（ひじ.parent 应为 腕捩）
      ひじ → 手捩 → 手首（手首.parent 应为 手捩）
    """
    b = armature.data.bones
    issues = []
    pairs = [
        ("左腕捩",  "左ひじ"),
        ("右腕捩",  "右ひじ"),
        ("左手捩",  "左手首"),
        ("右手捩",  "右手首"),
    ]
    for twist_name, child_name in pairs:
        tb = b.get(twist_name)
        cb = b.get(child_name)
        if tb and cb:
            cur_parent = cb.parent.name if cb.parent else "None"
            if cur_parent != twist_name:
                issues.append(f"{child_name}.parent = {cur_parent}（应为 {twist_name}）")
    return len(issues) == 0, issues


def fix_twist_chain(armature, context):
    """将 ひじ 的父级改为 腕捩，将 手首 的父级改为 手捩，并调整捩骨位置到链中点。"""
    ok, issues = check_twist_chain(armature)
    if ok:
        return True, "捩骨链已正确，无需修复"

    triples = [
        ("左腕捩",  "左腕",  "左ひじ"),
        ("右腕捩",  "右腕",  "右ひじ"),
        ("左手捩",  "左ひじ", "左手首"),
        ("右手捩",  "右ひじ", "右手首"),
    ]
    fixed = 0
    try:
        with _EditMode(armature, context) as eb:
            for twist_name, src_name, child_name in triples:
                tb = eb.get(twist_name)
                sb = eb.get(src_name)
                cb = eb.get(child_name)
                if not (tb and sb and cb):
                    continue
                if cb.parent and cb.parent.name == twist_name:
                    continue  # already correct

                # 重新定位捩骨到 src→child 的中点
                mid = sb.tail.lerp(cb.head, 0.0)  # 捩骨从 src.tail 到 child.head
                tb.head = sb.tail.copy()
                tb.tail = cb.head.copy()
                tb.parent = sb
                tb.use_connect = False

                # 将 child 的父级改为捩骨
                cb.parent = tb
                cb.use_connect = False
                fixed += 1
    except Exception as e:
        import traceback
        return False, traceback.format_exc()

    return True, f"已修复 {fixed} 处捩骨链（共 {len(issues)} 处问题）"


# ─── Check 4: 趾骨（つま先 + 足先EX重复处理）────────────────────────────────

def check_toe_bones(armature):
    """
    检测趾骨是否正确：
    - つま先.L/R 应存在（FK趾骨控制，父级为 足首.L/R）
    - 足先EX.L.001 存在说明有重名骨，需要修复
    """
    b = armature.data.bones
    issues = []
    for side, jp in [(".L", "左"), (".R", "右")]:
        if not b.get(f"つま先{side}"):
            dup = b.get(f"足先EX{side}.001")
            ja  = b.get(f"{jp}足先EX")
            if dup:
                issues.append(f"足先EX{side}.001 存在（重名，应重命名为 つま先{side}）")
            elif ja:
                issues.append(f"{jp}足先EX 应重命名为 つま先{side}")
            else:
                issues.append(f"缺少 つま先{side}")
    return len(issues) == 0, issues


def fix_toe_bones(armature, context):
    """
    修复趾骨：将 足先EX.L.001 / 左足先EX 重命名为 つま先.L，
    调整父级为 FK 踝骨（足首.L），确保 足先EX.L（D骨）父级为 足首D.L。
    """
    ok, issues = check_toe_bones(armature)
    if ok:
        return True, "趾骨已正确，无需修复"

    fixed = []
    for side, jp in [(".L", "左"), (".R", "右")]:
        tsuma = f"つま先{side}"
        if armature.data.bones.get(tsuma):
            continue  # 已存在，跳过

        # 找到候选骨：优先 .001 重名骨，其次日文名
        candidate = None
        for name in [f"足先EX{side}.001", f"{jp}足先EX"]:
            if armature.data.bones.get(name):
                candidate = name
                break

        if not candidate:
            continue

        if _rename_bone(armature, context, candidate, tsuma):
            fixed.append(f"{candidate} → {tsuma}")
        else:
            continue

        # 修复父级：つま先 应挂在 FK 踝骨（足首.L/R）下
        ankle_fk = f"{jp}足首"
        try:
            with _EditMode(armature, context) as eb:
                tsuma_eb = eb.get(tsuma)
                ankle_eb = eb.get(ankle_fk)
                if tsuma_eb and ankle_eb:
                    tsuma_eb.parent = ankle_eb
                    tsuma_eb.use_connect = False
                    tsuma_eb.use_deform = True

                # 确保 足先EX.L D骨 存在并挂在 足首D.L 下
                d_name   = f"足先EX{side}"
                d_parent = f"足首D{side}"
                if eb.get(d_parent) and not eb.get(d_name):
                    tip = tsuma_eb.head if tsuma_eb else ankle_eb.tail
                    _new_bone(eb, d_name, tip, tip + Vector((0, -0.05, 0)),
                              d_parent, use_deform=True)
        except Exception as e:
            import traceback
            return False, traceback.format_exc()

    if fixed:
        return True, "已修复趾骨：" + "、".join(fixed)
    return False, "未找到可自动修复的趾骨"


# ─── Check 5: 手指基节（指０骨）────────────────────────────────────────────

def check_finger_bases(armature):
    """
    检测手指基节骨（指０）是否存在。
    仅在模型有手指骨（指１骨）时才报错。
    """
    b = armature.data.bones
    has_fingers = any(b.get(n) for n in ["左人指１", "左中指１", "右人指１"])
    if not has_fingers:
        return True, []
    expected = [
        "人指０.L", "中指０.L", "薬指０.L", "小指０.L",
        "人指０.R", "中指０.R", "薬指０.R", "小指０.R",
    ]
    missing = [n for n in expected if not b.get(n)]
    if missing:
        return False, [f"缺少手指基节骨: {missing[:4]}{'...' if len(missing) > 4 else ''}"]
    return True, []


def fix_finger_bases(armature, context):
    """
    将 DAZ carpal 骨（lCarpal1-4）重命名为 指０ 骨。
    若 carpal 不存在则跳过（其他格式可能本就没有基节骨）。
    """
    carpal_map = {
        "lCarpal1": "人指０.L", "lCarpal2": "中指０.L",
        "lCarpal3": "薬指０.L", "lCarpal4": "小指０.L",
        "rCarpal1": "人指０.R", "rCarpal2": "中指０.R",
        "rCarpal3": "薬指０.R", "rCarpal4": "小指０.R",
    }
    b = armature.data.bones
    fixed = []
    for src, dst in carpal_map.items():
        if b.get(src) and not b.get(dst):
            if _rename_bone(armature, context, src, dst):
                fixed.append(f"{src}→{dst}")

    if fixed:
        return True, f"已重命名 {len(fixed)} 个手指基节骨"

    ok, issues = check_finger_bases(armature)
    if ok:
        return True, "手指基节已完整，无需修复"
    return False, f"无法自动修复，请手动检查：{issues[0] if issues else ''}"


# ─── 注册表 + 批量运行 ────────────────────────────────────────────────────────

CHECK_REGISTRY = [
    ("spine",    "脊椎骨链",  check_spine_chain,    fix_spine_chain),
    ("shoulder", "肩骨链",    check_shoulder_chain, fix_shoulder_chain),
    ("twist",    "捩骨接链",  check_twist_chain,    fix_twist_chain),
    ("toe",      "趾骨",      check_toe_bones,      fix_toe_bones),
    ("fingers",  "手指基节",  check_finger_bases,   fix_finger_bases),
]


def run_all_checks(armature):
    """对骨架执行所有检测，返回 [(key, label, ok, issues)]。"""
    results = []
    for key, label, check_fn, _ in CHECK_REGISTRY:
        try:
            ok, issues = check_fn(armature)
        except Exception as e:
            ok, issues = False, [str(e)]
        results.append((key, label, ok, issues))
    return results


def fix_by_key(key, armature, context):
    """按 key 执行单项修复，返回 (success, message)。"""
    for k, label, _, fix_fn in CHECK_REGISTRY:
        if k == key:
            return fix_fn(armature, context)
    return False, f"未知检测项: {key}"


def fix_all(armature, context):
    """依次执行所有修复，返回 [(label, success, msg)]。"""
    results = []
    for key, label, _, fix_fn in CHECK_REGISTRY:
        try:
            ok, msg = fix_fn(armature, context)
        except Exception as e:
            import traceback
            ok, msg = False, traceback.format_exc()
        results.append((label, ok, msg))
    return results
