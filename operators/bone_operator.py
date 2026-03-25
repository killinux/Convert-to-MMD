import bpy
from mathutils import Vector
from .. import bone_map_and_group
from .. import bone_utils
from .. import preset_operator
from . import weight_monitor

class OBJECT_OT_rename_to_mmd(bpy.types.Operator):
    """将选定的骨骼重命名为 MMD 格式"""
    bl_idname = "object.rename_to_mmd"
    bl_label = "Rename to MMD"

    mmd_bone_map = bone_map_and_group.mmd_bone_map  # 使用导入的bone_map模块

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "没有选择骨架对象")
            return {'CANCELLED'}

        scene = context.scene
        # 检查选择框里是否有骨骼设置
        has_bone_set = False
        for prop_name in preset_operator.get_bones_list():  # 从operations.py中获取骨骼属性名称列表
            if getattr(scene, prop_name, None):
                has_bone_set = True
                break
        if not has_bone_set:
            self.report({'WARNING'}, "未设置骨骼")
            return {'CANCELLED'}
        for prop_name, new_name in self.mmd_bone_map.items():
            bone_name = getattr(scene, prop_name, None)
            if bone_name:
                bone = obj.pose.bones.get(bone_name)
                if bone:
                    # 检查骨骼是否已经重命名为 MMD 格式名称
                    if bone.name != new_name:
                        old_name = bone.name
                        bone.name = new_name
                        # 同步所有网格对象的顶点组名称，防止权重断链
                        for mesh_obj in context.scene.objects:
                            if mesh_obj.type == 'MESH':
                                vg = mesh_obj.vertex_groups.get(old_name)
                                if vg:
                                    vg.name = new_name
                        # 更新场景中的骨骼属性值
                        setattr(scene, prop_name, new_name)
                    else:
                        self.report({'INFO'}, f"骨骼 '{bone_name}' 已经重命名为 {new_name}")
                else:
                    self.report({'WARNING'}, f"未找到骨骼 '{bone_name}' 以重命名为 {new_name}")

        # 打开骨骼名称显示
        bpy.context.object.data.show_names = True

        return {'FINISHED'}

    def rename_finger_bone(self, context, obj, scene, base_finger_name, segment):
        for side in ["left", "right"]:
            prop_name = f"{side}_{base_finger_name}_{segment}"
            if prop_name in self.mmd_bone_map:
                new_name = self.mmd_bone_map.get(prop_name)
                bone_name = getattr(scene, prop_name, None)
                if bone_name:
                    bone = obj.pose.bones.get(bone_name)
                    if bone:
                        # Check if the bone has already been renamed to the MMD format name
                        if bone.name != new_name:
                            bone.name = new_name
                            # Update the bone property value in the scene
                            setattr(scene, prop_name, new_name)
                        else:
                            self.report({'INFO'}, f"Bone '{bone_name}' is already renamed to {new_name}")
                    else:
                        self.report({'WARNING'}, f"Bone '{bone_name}' not found for renaming to {new_name}")

class OBJECT_OT_complete_missing_bones(bpy.types.Operator):
    """补充缺失的 MMD 格式骨骼"""
    bl_idname = "object.complete_missing_bones"
    bl_label = "Complete Missing Bones"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "没有选择骨架")
            return {'CANCELLED'}

        # 确保当前处于编辑模式 (EDIT mode)
        if context.mode != 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='EDIT')
        
        edit_bones = obj.data.edit_bones
        # 获取需要修改的骨骼
        left_foot_bone = edit_bones.get("左足")
        right_foot_bone = edit_bones.get("右足")
        upper_body_bone = edit_bones.get("上半身")
        lower_body_bone = edit_bones.get("下半身")
        upper_body_2_bone = edit_bones.get("上半身2")
        # 兼容两种命名：标准 目.L/目.R 和 日文 左目/右目
        left_eye_bone = edit_bones.get("目.L") or edit_bones.get("左目")
        right_eye_bone = edit_bones.get("目.R") or edit_bones.get("右目")
        head_bone = edit_bones.get("頭")

        # 清除 左足 和 右足 骨骼的父级
        if left_foot_bone:
            left_foot_bone.use_connect = False
            left_foot_bone.parent = None
        if right_foot_bone:
            right_foot_bone.use_connect = False
            right_foot_bone.parent = None
        # 清除 上半身 骨骼的父级
        if upper_body_bone and upper_body_bone.parent:
            upper_body_bone.use_connect = False
            upper_body_bone.parent = None
        # 清除 下半身 骨骼的父级
        if lower_body_bone and lower_body_bone.parent:
            lower_body_bone.use_connect = False
            lower_body_bone.parent = None
        # 确认上半身骨骼存在
        if not upper_body_bone:
            self.report({'ERROR'}, "上半身骨骼不存在")
            return {'CANCELLED'}
        # 获取 上半身 骨骼的坐标
        upper_body_head = upper_body_bone.head.copy()
        upper_body_tail = upper_body_bone.tail.copy()

        # 计算 上半身1 的位置
        # head = 上半身的实际 tail（脊椎中段顶部），tail = spine_upper 下三分之一处
        upper1_head = upper_body_tail.copy()
        if upper_body_2_bone:
            ub2_head_z = upper_body_2_bone.head.z
            ub2_tail_z = upper_body_2_bone.tail.z
            step = (ub2_tail_z - ub2_head_z) / 3.0 if ub2_tail_z > ub2_head_z else 0.05
            upper1_tail = Vector((0, upper_body_2_bone.head.y, ub2_head_z + step))
        else:
            upper1_tail = upper1_head + Vector((0, 0, 0.05))

        # 计算 腰キャンセル 的位置（与足的头部相同）
        if left_foot_bone:
            left_koshi_head = left_foot_bone.head.copy()
        else:
            left_koshi_head = Vector((-0.1, 0, upper_body_head.z - 0.15))
        if right_foot_bone:
            right_koshi_head = right_foot_bone.head.copy()
        else:
            right_koshi_head = Vector((0.1, 0, upper_body_head.z - 0.15))

        # 计算脚尖（足先）位置：优先使用真实骨骼，回退到偏移量
        left_toe_ex  = edit_bones.get("左足先EX") or edit_bones.get("左つま先")
        right_toe_ex = edit_bones.get("右足先EX") or edit_bones.get("右つま先")
        if left_toe_ex:
            left_ankle_tail = left_toe_ex.head.copy()
        else:
            left_ankle_tail = Vector((edit_bones["左足首"].head.x, edit_bones["左足首"].head.y - 0.08, 0))
        if right_toe_ex:
            right_ankle_tail = right_toe_ex.head.copy()
        else:
            right_ankle_tail = Vector((edit_bones["右足首"].head.x, edit_bones["右足首"].head.y - 0.08, 0))

        # 计算 両目 的位置（两眼之间）
        if left_eye_bone and right_eye_bone:
            ryome_head = (left_eye_bone.head + right_eye_bone.head) / 2
            ryome_head = Vector((0, ryome_head.y, ryome_head.z))
        elif head_bone:
            ryome_head = head_bone.head + Vector((0, -0.1, 0.1))
        else:
            ryome_head = Vector((0, upper_body_head.y, upper_body_head.z + 0.5))
        ryome_tail = ryome_head + Vector((0, -0.1, 0))

        # 基于角色实际骨骼高度计算控制骨位置
        waist_z    = upper_body_head.z        # 腰（上半身起点）的 Z 高度
        center_z   = waist_z * 0.72           # センター/グルーブ：腰高度的 72%（参考 MMD 标准比例）
        bone_unit  = waist_z * 0.05           # 控制骨短边长度（腰高度的 5%）
        root_unit  = waist_z * 0.08           # 全ての親 的长度

        # 定义基本骨骼的属性（有序字典，按父子关系排列）
        bone_properties = {
            "全ての親": {"head": Vector((0, 0, 0)), "tail": Vector((0, 0, root_unit)), "parent": None, "use_deform": False, "use_connect": False},
            "センター": {"head": Vector((0, 0, center_z)), "tail": Vector((0, 0, center_z + bone_unit)), "parent": "全ての親", "use_deform": False, "use_connect": False},
            "グルーブ": {"head": Vector((0, 0, center_z)), "tail": Vector((0, 0, center_z + bone_unit)), "parent": "センター", "use_deform": False, "use_connect": False},
            "腰": {"head": Vector((0, upper_body_head.y + 0.1, upper_body_head.z - 0.12)), "tail": Vector((0, upper_body_head.y, upper_body_head.z)),
                "parent": "グルーブ", "use_deform": False, "use_connect": False},
            # 上半身：保留实际骨骼位置（spine_middle），只重置父级
            "上半身": {"head": upper_body_head, "tail": upper_body_tail, "parent": "腰", "use_connect": False},
            # 上半身1：从 上半身 tail 到 spine_upper 下三分之一处，朝上的桥接骨骼（deform=True 与 MMD 参考一致）
            "上半身1": {"head": upper1_head, "tail": upper1_tail, "parent": "上半身", "use_deform": True, "use_connect": False},
            # 上半身2：从 上半身1 tail 到 spine_upper 顶部，连接成完整链
            "上半身2": {
                "head": upper1_tail,
                "tail": Vector((0, upper_body_2_bone.tail.y, upper_body_2_bone.tail.z)) if upper_body_2_bone else upper1_tail + Vector((0, 0, 0.15)),
                "parent": "上半身1", "use_connect": False},

            # 下半身
            "下半身": {"head": Vector((0, upper_body_head.y, upper_body_head.z)), "tail": Vector((0, upper_body_head.y, upper_body_head.z - 0.15)), "parent": "腰", "use_connect": False},
            "腰キャンセル.L": {"head": left_koshi_head, "tail": left_koshi_head + Vector((0, 0, -0.05)), "parent": "下半身", "use_deform": False, "use_connect": False},
            "腰キャンセル.R": {"head": right_koshi_head, "tail": right_koshi_head + Vector((0, 0, -0.05)), "parent": "下半身", "use_deform": False, "use_connect": False},

            # 腿部（足→腰キャンセル）
            "左足": {"head": edit_bones["左足"].head, "tail": edit_bones["左ひざ"].head, "parent": "腰キャンセル.L", "use_connect": False},
            "右足": {"head": edit_bones["右足"].head, "tail": edit_bones["右ひざ"].head, "parent": "腰キャンセル.R", "use_connect": False},
            "左ひざ": {"head": edit_bones["左ひざ"].head, "tail": edit_bones["左足首"].head, "parent": "左足", "use_connect": False},
            "右ひざ": {"head": edit_bones["右ひざ"].head, "tail": edit_bones["右足首"].head, "parent": "右足", "use_connect": False},
            "左足首": {"head": edit_bones["左足首"].head, "tail": left_ankle_tail, "parent": "左ひざ", "use_connect": False},
            "右足首": {"head": edit_bones["右足首"].head, "tail": right_ankle_tail, "parent": "右ひざ", "use_connect": False},

            # D 系变形骨骼（tail 为向上的短 stub，与FK骨骼不对齐，
            # 使 mmd_tools 的 well-aligned 检查为 False，从而正确生成 shadow/dummy 骨骼和付与约束）
            "足D.L": {"head": edit_bones["左足"].head.copy(), "tail": edit_bones["左足"].head + Vector((0, 0, 0.082)), "parent": "腰キャンセル.L", "use_deform": True, "use_connect": False},
            "ひざD.L": {"head": edit_bones["左ひざ"].head.copy(), "tail": edit_bones["左ひざ"].head + Vector((0, 0, 0.082)), "parent": "足D.L", "use_deform": True, "use_connect": False},
            "足首D.L": {"head": edit_bones["左足首"].head.copy(), "tail": edit_bones["左足首"].head + Vector((0, 0, 0.082)), "parent": "ひざD.L", "use_deform": True, "use_connect": False},
            "足先EX.L": {"head": left_ankle_tail, "tail": left_ankle_tail + Vector((0, -0.082, 0)), "parent": "足首D.L", "use_deform": True, "use_connect": False},
            "足D.R": {"head": edit_bones["右足"].head.copy(), "tail": edit_bones["右足"].head + Vector((0, 0, 0.082)), "parent": "腰キャンセル.R", "use_deform": True, "use_connect": False},
            "ひざD.R": {"head": edit_bones["右ひざ"].head.copy(), "tail": edit_bones["右ひざ"].head + Vector((0, 0, 0.082)), "parent": "足D.R", "use_deform": True, "use_connect": False},
            "足首D.R": {"head": edit_bones["右足首"].head.copy(), "tail": edit_bones["右足首"].head + Vector((0, 0, 0.082)), "parent": "ひざD.R", "use_deform": True, "use_connect": False},
            "足先EX.R": {"head": right_ankle_tail, "tail": right_ankle_tail + Vector((0, -0.082, 0)), "parent": "足首D.R", "use_deform": True, "use_connect": False},

            # 上肢骨骼链
            "左肩": {"head": edit_bones["左肩"].head, "tail": edit_bones["左腕"].head,
                "parent": edit_bones["左肩"].parent.name if edit_bones["左肩"].parent else "上半身2", "use_connect": False},
            "左腕": {"head": edit_bones["左腕"].head, "tail": edit_bones["左ひじ"].head, "parent": "左肩", "use_connect": False},
            "左ひじ": {"head": edit_bones["左ひじ"].head, "tail": edit_bones["左手首"].head if edit_bones.get("左手首") else edit_bones["左ひじ"].tail, "parent": "左腕", "use_connect": False},
            "右肩": {"head": edit_bones["右肩"].head, "tail": edit_bones["右腕"].head,
                "parent": edit_bones["右肩"].parent.name if edit_bones["右肩"].parent else "上半身2", "use_connect": False},
            "右腕": {"head": edit_bones["右腕"].head, "tail": edit_bones["右ひじ"].head, "parent": "右肩", "use_connect": False},
            "右ひじ": {"head": edit_bones["右ひじ"].head, "tail": edit_bones["右手首"].head if edit_bones.get("右手首") else edit_bones["右ひじ"].tail, "parent": "右腕", "use_connect": False},

            # 両目（双眼父骨）
            "両目": {"head": ryome_head, "tail": ryome_tail, "parent": "頭" if edit_bones.get("頭") else None, "use_deform": False, "use_connect": False},
        }

        # 按顺序检查并创建或更新骨骼
        for bone_name, properties in bone_properties.items():
            bone_utils.create_or_update_bone(
                edit_bones, bone_name,
                properties["head"], properties["tail"],
                properties.get("use_connect", False),
                properties["parent"],
                properties.get("use_deform", True)
            )

        # 调用函数设置 roll 值
        bone_utils.set_roll_values(edit_bones, bone_utils.DEFAULT_ROLL_VALUES)

        # 切回 Object 模式，执行权重修复
        bpy.ops.object.mode_set(mode='OBJECT')
        self._setup_new_bone_weights(context, obj)

        weight_monitor.auto_check_after_step(context, obj, "step_2", "补全缺失骨骼")
        return {'FINISHED'}

    def _setup_new_bone_weights(self, context, armature):
        """
        补全缺失骨骼后的权重修复：
        1. 将腿部常规骨骼（左足/左ひざ/左足首）权重复制到 D 系骨骼，并将常规腿骨设为非变形骨
        2. 将 上半身2 在 上半身1 区间内的权重按高度比例分配给 上半身1
        """
        # ── 1. D 系腿骨权重 ──────────────────────────────────────────────
        # 常规腿骨 → D 系骨骼 的映射（左右对称）
        leg_copy_map = [
            ("左足",    "足D.L"),
            ("左ひざ",  "ひざD.L"),
            ("左足首",  "足首D.L"),
            ("左足先EX","足先EX.L"),
            ("右足",    "足D.R"),
            ("右ひざ",  "ひざD.R"),
            ("右足首",  "足首D.R"),
            ("右足先EX","足先EX.R"),
        ]
        # 复制权重后设为非变形骨的腿骨（IK 只需要姿态，不需要变形）
        leg_ik_only = {"左足", "左ひざ", "左足首", "左足先EX", "右足", "右ひざ", "右足首", "右足先EX"}

        mesh_objects = [
            o for o in context.scene.objects
            if o.type == 'MESH' and any(
                m.type == 'ARMATURE' and m.object == armature for m in o.modifiers)
        ]

        for src_name, dst_name in leg_copy_map:
            for obj in mesh_objects:
                src_vg = obj.vertex_groups.get(src_name)
                if not src_vg:
                    continue
                dst_vg = obj.vertex_groups.get(dst_name)
                if not dst_vg:
                    dst_vg = obj.vertex_groups.new(name=dst_name)
                for v in obj.data.vertices:
                    for g in v.groups:
                        if g.group == src_vg.index and g.weight > 0:
                            dst_vg.add([v.index], g.weight, 'REPLACE')
                            break

        # 将常规腿骨设为非变形骨（PMX 中它们只做 IK 控制）
        for bname in leg_ik_only:
            bone = armature.data.bones.get(bname)
            if bone:
                bone.use_deform = False

        # ── D 系骨骼设置 mmd_tools 付与（additional_transform）──────────────
        # 通过 mmd_bone.additional_transform_bone + FnBone.apply_additional_transformation
        # 生成标准的 shadow/dummy 骨骼和约束，PMX 导出时会正确转换为付与関係
        d_series_follow = [
            ("足D.L",   "左足"),
            ("ひざD.L", "左ひざ"),
            ("足首D.L", "左足首"),
            ("足D.R",   "右足"),
            ("ひざD.R", "右ひざ"),
            ("足首D.R", "右足首"),
        ]
        try:
            from mmd_tools.core.bone import FnBone
            needs_apply = False
            for d_name, src_name in d_series_follow:
                pb = armature.pose.bones.get(d_name)
                if not pb:
                    continue
                mb = pb.mmd_bone
                if mb.additional_transform_bone != src_name:
                    mb.additional_transform_bone = src_name
                    mb.has_additional_rotation = True
                    mb.additional_transform_influence = 1.0
                    needs_apply = True
            if needs_apply:
                bpy.ops.object.mode_set(mode='POSE')
                FnBone.apply_additional_transformation(armature)
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            self.report({'WARNING'}, f"D系付与设置失败（需要mmd_tools）: {e}")

        # ── 2. 上半身1 权重重分配 ─────────────────────────────────────────
        ub1_bone = armature.data.bones.get("上半身1")
        ub2_bone = armature.data.bones.get("上半身2")
        if not ub1_bone or not ub2_bone:
            self.report({'INFO'}, "D系骨骼权重已复制（上半身1/2不存在，跳过脊柱重分配）")
            return

        mw = armature.matrix_world
        ub1_head_z = (mw @ ub1_bone.head_local).z
        ub1_tail_z = (mw @ ub1_bone.tail_local).z  # = 上半身2.head.z
        span = ub1_tail_z - ub1_head_z
        if span <= 0:
            self.report({'INFO'}, "D系骨骼权重已复制（上半身1 高度为0，跳过重分配）")
            return

        for obj in mesh_objects:
            vg2 = obj.vertex_groups.get("上半身2")
            if not vg2:
                continue
            vg1 = obj.vertex_groups.get("上半身1")
            if not vg1:
                vg1 = obj.vertex_groups.new(name="上半身1")

            for v in obj.data.vertices:
                w2 = 0.0
                for g in v.groups:
                    if g.group == vg2.index:
                        w2 = g.weight
                        break
                if w2 <= 0:
                    continue

                world_z = (obj.matrix_world @ v.co).z
                # 在 上半身1 Z 范围内的顶点才重分配
                if world_z >= ub1_tail_z:
                    continue  # 完全在 上半身2 区域，不动

                # ratio_to_ub1：越靠近 ub1_head_z 越多给 上半身1
                t = max(0.0, min(1.0, (world_z - ub1_head_z) / span))
                ratio_ub2 = t          # 靠近 ub2 侧保留给 上半身2
                ratio_ub1 = 1.0 - t   # 靠近 ub1 侧分给 上半身1

                if ratio_ub2 > 0:
                    vg2.add([v.index], w2 * ratio_ub2, 'REPLACE')
                else:
                    vg2.remove([v.index])

                if ratio_ub1 > 0:
                    cur_w1 = 0.0
                    for g in v.groups:
                        if g.group == vg1.index:
                            cur_w1 = g.weight
                            break
                    vg1.add([v.index], min(1.0, cur_w1 + w2 * ratio_ub1), 'REPLACE')

        # ── 3. 髋部渐变过渡区 ───────────────────────────────────────────────
        # XPS 权重是二值的（足D在髋部全是1.0），没有腰腿过渡混合，
        # 会导致骨骼运动时出现硬切割（裂口感）。
        # 在 足D.L/R 权重范围顶部做渐变，将边界处的足D权重逐步转移给下半身。
        hip_modified = _create_hip_blend_zone(armature, mesh_objects, transition_height=1.5)
        if hip_modified > 0:
            self.report({'INFO'}, f"补全完成：D系腿骨已复制，上半身1已分配，髋部渐变区已创建（{hip_modified}顶点）")
        else:
            self.report({'INFO'}, "补全骨骼权重完成：D系腿骨已复制，上半身1已分配")


# ─────────────────────────────────────────────────────────────────────────────
# 共享工具函数
# ─────────────────────────────────────────────────────────────────────────────

def _create_hip_blend_zone(armature, mesh_objects, transition_height=1.5):
    """
    在髋部（大腿↔腰 边界）强制建立足D与下半身的正确权重分布。

    目标分布（参考 Purifier Inase 等标准 MMD 模型）：
      - 大腿主体（膝盖~髋部85%处）：足D ≈ 1.0，下半身 ≈ 0
      - 渐变区（髋部顶端15%）：足D 从1.0线性降到0，下半身从0升到1.0
      - 髋关节以上：下半身完全控制

    策略：基于骨骼位置计算每个顶点的「目标足D权重」，
    双向调整（足D不足则从下半身补充；足D过多则转回下半身）。
    当下半身权重不足以补充时，直接给足D追加权重（适配 XPS 二值权重）。

    返回修改的顶点数。
    """
    BLEND_PAIRS = [
        ("足D.L", "下半身", "左足"),
        ("足D.R", "下半身", "右足"),
    ]
    # 大腿顶部多少比例作为渐变区（参考模型约10~15%）
    BLEND_TOP_FRAC = 0.15
    total_modified = 0

    for obj in mesh_objects:
        mw = obj.matrix_world

        for d_bone_name, shimono_name, fk_bone_name in BLEND_PAIRS:
            vg_d = obj.vertex_groups.get(d_bone_name)
            vg_s = obj.vertex_groups.get(shimono_name)
            if not vg_d or not vg_s:
                continue

            idx_d = vg_d.index
            idx_s = vg_s.index

            fk_bone = armature.data.bones.get(fk_bone_name)
            if not fk_bone:
                continue

            hip_z  = (armature.matrix_world @ fk_bone.head_local).z  # 髋关节（高）
            knee_z = (armature.matrix_world @ fk_bone.tail_local).z  # 膝盖（低）
            hip_x  = (armature.matrix_world @ fk_bone.head_local).x  # 判断左右

            if abs(hip_z - knee_z) < 0.001:
                continue

            z_bottom  = min(hip_z, knee_z)
            z_top     = max(hip_z, knee_z)
            thigh_len = z_top - z_bottom

            # 对侧D骨的index（用于排除已属于对侧的顶点）
            opposite_d_name = "足D.R" if d_bone_name == "足D.L" else "足D.L"
            vg_opp = obj.vertex_groups.get(opposite_d_name)
            idx_opp = vg_opp.index if vg_opp else -1

            for v in obj.data.vertices:
                vz = (mw @ v.co).z
                # 只处理大腿范围内的顶点
                if vz < z_bottom or vz > z_top:
                    continue

                # 左右侧过滤：优先用X坐标判断，严格排除对侧顶点
                vx = (mw @ v.co).x
                if hip_x > 0 and vx < -0.02:
                    continue
                if hip_x < 0 and vx > 0.02:
                    continue

                # 若顶点对侧D骨权重 > 本侧，说明它属于对侧，跳过
                if idx_opp >= 0:
                    wd_self = wd_opp = 0.0
                    for g in v.groups:
                        if g.group == idx_d:   wd_self = g.weight
                        if g.group == idx_opp: wd_opp  = g.weight
                    if wd_opp > wd_self + 0.01:
                        continue

                # 高度参数 t：0=髋关节顶端，1=膝盖底端
                t = 1.0 - (vz - z_bottom) / thigh_len

                # 目标足D权重：大腿主体=1.0，顶端渐变区线性降到0
                if t >= BLEND_TOP_FRAC:
                    target_dr = 1.0
                else:
                    target_dr = t / BLEND_TOP_FRAC  # 0.0 ~ 1.0

                # 读取当前权重
                wd = ws = 0.0
                for g in v.groups:
                    if g.group == idx_d: wd = g.weight
                    if g.group == idx_s: ws = g.weight

                delta = target_dr - wd  # 正=需要增加足D，负=需要减少足D

                if abs(delta) < 0.0005:
                    continue

                if delta > 0:
                    # 足D不足：从下半身补充，不够则直接追加（XPS二值权重兼容）
                    transfer = min(ws, delta)
                    if transfer >= 0.0005:
                        vg_s.add([v.index], ws - transfer, 'REPLACE')
                        vg_d.add([v.index], wd + transfer, 'REPLACE')
                    elif delta >= 0.0005:
                        # 下半身权重为0时直接设定足D（XPS模型无pelvis权重场景）
                        vg_d.add([v.index], target_dr, 'REPLACE')
                else:
                    # 足D过多：将多余部分转回下半身
                    transfer = -delta  # 正数
                    vg_d.add([v.index], wd - transfer, 'REPLACE')
                    vg_s.add([v.index], ws + transfer, 'REPLACE')

                total_modified += 1

    # ── 步骤2：清理 足D.L / 足D.R 跨侧污染 ──────────────────────────────
    # XPS内裆区域的顶点可能同时被左右FK骨权重覆盖，复制到D系骨时带入污染。
    # 使用FK骨权重（右足/左足）判断顶点归属，清除非主导侧的D骨权重。
    for obj in mesh_objects:
        vg_dl  = obj.vertex_groups.get("足D.L")
        vg_dr  = obj.vertex_groups.get("足D.R")
        vg_fl  = obj.vertex_groups.get("左足")  # FK参考
        vg_fr  = obj.vertex_groups.get("右足")
        if not vg_dl or not vg_dr:
            continue
        idx_l = vg_dl.index
        idx_r = vg_dr.index
        idx_fl = vg_fl.index if vg_fl else -1
        idx_fr = vg_fr.index if vg_fr else -1

        mw = obj.matrix_world
        for v in obj.data.vertices:
            wl = wr = fl = fr = 0.0
            for g in v.groups:
                if g.group == idx_l:  wl = g.weight
                if g.group == idx_r:  wr = g.weight
                if g.group == idx_fl: fl = g.weight
                if g.group == idx_fr: fr = g.weight

            if wl < 0.001 and wr < 0.001:
                continue  # 两侧都没有，跳过

            vx = (mw @ v.co).x  # 正X=角色左侧，负X=角色右侧

            # ── 情况A：两侧D骨同时存在，判断哪侧主导 ──
            if wl >= 0.001 and wr >= 0.001:
                if fl > fr * 2.0:
                    vg_dr.add([v.index], 0.0, 'REPLACE'); total_modified += 1
                elif fr > fl * 2.0:
                    vg_dl.add([v.index], 0.0, 'REPLACE'); total_modified += 1
                elif vx > 0.02:
                    vg_dr.add([v.index], 0.0, 'REPLACE'); total_modified += 1
                elif vx < -0.02:
                    vg_dl.add([v.index], 0.0, 'REPLACE'); total_modified += 1
                # |X| ≤ 0.02：真正中线顶点，保留双侧
                continue

            # ── 情况B：只有一侧D骨，检查是否在错误的位置 ──
            # 左侧顶点（X > 0.02）不应该有足D.R
            if vx > 0.02 and wr >= 0.001:
                vg_dr.add([v.index], 0.0, 'REPLACE'); total_modified += 1
            # 右侧顶点（X < -0.02）不应该有足D.L
            elif vx < -0.02 and wl >= 0.001:
                vg_dl.add([v.index], 0.0, 'REPLACE'); total_modified += 1

    return total_modified


def _weight_is_orphan(bone_name):
    """判断骨骼是否为非MMD孤立骨。
    规则：重命名为MMD后，所有标准MMD骨骼名含日文字符（下半身/足D.L/腕捩.L等）。
    纯ASCII名称 = 非MMD骨（unused bip001 pelvis / root ground / breast.L 等），
    权重需转移到最近的有效MMD变形骨。
    适配 XPS / Mixamo / DAZ / CC3 / BVH 等任意来源模型。"""
    return all(ord(c) < 128 for c in bone_name)


def _weight_collect_weighted_vgs(mesh_objects):
    """收集所有网格中有顶点权重（>0.001）的顶点组名称集合。"""
    weighted = set()
    for obj in mesh_objects:
        for vg in obj.vertex_groups:
            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.001:
                        weighted.add(vg.name)
                        break
                else:
                    continue
                break
    return weighted


def _weight_get_mesh_objects(context, armature):
    return [o for o in context.scene.objects
            if o.type == 'MESH' and any(
                m.type == 'ARMATURE' and m.object == armature for m in o.modifiers)]


def _weight_compute_orphan_targets(armature, mesh_objects, orphan_bones, valid_deform_bones):
    """为每个孤立骨计算目标MMD骨。
    策略（优先级从高到低）：
    1. 父级链优先：沿父级链向上，找到第一个有效MMD变形骨（含日文名且use_deform=True）
    2. D系骨映射：若父级是非变形的IK腿骨（左足/右ひざ等），
       自动映射到对应D系骨（足D.L/ひざD.R等）
    3. 几何距离兜底：父级链走到根部仍无结果，
       用顶点重心到骨骼中点的3D距离找最近有效MMD骨
    返回 dict: {orphan_bone → (target_bone, method_str)}"""

    # D系骨映射表：非变形IK腿骨 → 对应变形D系骨
    D_SERIES = {
        '左足': '足D.L',   '右足': '足D.R',
        '左ひざ': 'ひざD.L', '右ひざ': 'ひざD.R',
        '左足首': '足首D.L', '右足首': '足首D.R',
        '左足先EX': '足先EX.L', '右足先EX': '足先EX.R',
    }
    valid_bone_set = {b.name: b for b in valid_deform_bones}
    mw = armature.matrix_world
    results = {}

    for bone in orphan_bones:
        target = None
        method = ''

        # ── 策略1+2：沿父级链查找 ────────────────────────────────
        cur = bone.parent
        while cur:
            if not _weight_is_orphan(cur.name) and cur.use_deform:
                # 找到有效MMD变形骨
                target = cur
                method = f'parent({cur.name})'
                break
            if not cur.use_deform:
                # 非变形骨：检查D系映射
                d_name = D_SERIES.get(cur.name)
                if d_name and d_name in valid_bone_set:
                    target = valid_bone_set[d_name]
                    method = f'D-series({cur.name}→{d_name})'
                    break
            cur = cur.parent

        # ── 策略3：几何距离兜底 ──────────────────────────────────
        if not target:
            centroid = Vector((0.0, 0.0, 0.0))
            total_w = 0.0
            for obj in mesh_objects:
                vg = obj.vertex_groups.get(bone.name)
                if not vg:
                    continue
                mw_obj = obj.matrix_world
                for v in obj.data.vertices:
                    for g in v.groups:
                        if g.group == vg.index and g.weight > 0.001:
                            centroid += (mw_obj @ v.co) * g.weight
                            total_w += g.weight
            if total_w < 0.001:
                continue
            centroid /= total_w

            best_dist = float('inf')
            for cand in valid_deform_bones:
                mid = (mw @ cand.head_local + mw @ cand.tail_local) * 0.5
                d = (mid - centroid).length
                if d < best_dist:
                    best_dist = d
                    target = cand
            method = f'geometry({target.name if target else "?"})'

        if target:
            results[bone] = (target, method)
    return results


def _weight_execute_orphan_transfer(mesh_objects, orphan_target_map, armature=None):
    """执行孤立骨权重转移：顶点级别的解剖区间覆盖。
    当目标骨为 下半身/腰 等躯干骨时，检查顶点所处Z区间：
    若顶点位于大腿/小腿/脚踝区间，则按X位置重定向到对应D系骨骼。
    """
    # 构建腿部区间信息（从骨架骨骼位置获取）
    leg_zones = []  # [(min_z, max_z, d_bone_left, d_bone_right), ...]
    torso_targets = {"下半身", "腰", "上半身", "センター", "グルーブ"}
    if armature:
        mw = armature.matrix_world
        zone_map = [
            ("左足",  "左ひざ",  "足D.L",  "足D.R"),
            ("左ひざ","左足首",  "ひざD.L","ひざD.R"),
            ("左足首","左足先EX","足首D.L","足首D.R"),
        ]
        for top_name, bot_name, dl, dr in zone_map:
            bt = armature.data.bones.get(top_name)
            bb = armature.data.bones.get(bot_name)
            if bt and bb:
                z_top = (mw @ bt.head_local).z
                z_bot = (mw @ bb.head_local).z
                z_min = min(z_top, z_bot) - 0.05
                z_max = max(z_top, z_bot) + 0.05
                # 只在D系骨骼存在时才用此区间
                if armature.data.bones.get(dl) and armature.data.bones.get(dr):
                    leg_zones.append((z_min, z_max, dl, dr))

    redirected = []
    for src_bone, (dst_bone, _) in orphan_target_map.items():
        for obj in mesh_objects:
            src_vg = obj.vertex_groups.get(src_bone.name)
            if not src_vg:
                continue
            # 预先缓存所有VG索引
            vg_cache = {}
            for v in obj.data.vertices:
                w = 0.0
                for g in v.groups:
                    if g.group == src_vg.index:
                        w = g.weight
                        break
                if w <= 0.001:
                    continue

                # 确定实际目标：对躯干目标做顶点级区间覆盖
                actual_dst_name = dst_bone.name
                if leg_zones and dst_bone.name in torso_targets:
                    world_z = (obj.matrix_world @ v.co).z
                    world_x = (obj.matrix_world @ v.co).x
                    for z_min, z_max, dl, dr in leg_zones:
                        if z_min <= world_z <= z_max:
                            actual_dst_name = dl if world_x >= 0 else dr
                            break

                if actual_dst_name not in vg_cache:
                    vg = obj.vertex_groups.get(actual_dst_name)
                    if not vg:
                        vg = obj.vertex_groups.new(name=actual_dst_name)
                    vg_cache[actual_dst_name] = vg
                actual_vg = vg_cache[actual_dst_name]

                cur = 0.0
                for g in v.groups:
                    if g.group == actual_vg.index:
                        cur = g.weight
                        break
                actual_vg.add([v.index], min(1.0, cur + w), 'REPLACE')
                src_vg.add([v.index], 0.0, 'REPLACE')

                # 区间覆盖发生时，同步清除原躯干目标骨骼（如下半身）上该顶点的权重，
                # 防止顶点同时被躯干骨和D系骨各拉一份造成形变错误
                if actual_dst_name != dst_bone.name:
                    if dst_bone.name not in vg_cache:
                        orig_vg = obj.vertex_groups.get(dst_bone.name)
                        if orig_vg:
                            vg_cache[dst_bone.name] = orig_vg
                    orig_torso_vg = vg_cache.get(dst_bone.name)
                    if orig_torso_vg:
                        orig_torso_vg.add([v.index], 0.0, 'REPLACE')
        redirected.append(f"{src_bone.name}→{dst_bone.name}")
    return redirected


def _weight_cleanup_leg_torso_conflict(armature, mesh_objects):
    """清理 D系腿骨 与 躯干骨 之间的真实冲突权重。

    ⚠️ 只处理 D系骨权重 >= 0.6（明确处于腿部区域）的顶点，
    保留 D系骨权重 < 0.6 的混合过渡区（腰臀部自然渐变，不应清除）。

    参考模型（Purifier Inase）中，腰臀过渡区有约3000个顶点
    同时具有 下半身 和 足D 权重，这是正常的权重混合，不是冲突。

    返回清理的顶点数量。"""
    D_DOMINANT_THRESHOLD = 0.6   # 只在D系权重占主导时才清躯干骨
    d_series = {"足D.L","足D.R","ひざD.L","ひざD.R","足首D.L","足首D.R","足先EX.L","足先EX.R"}
    torso_bones = {"下半身","腰"}
    cleaned = 0
    for obj in mesh_objects:
        # 收集各VG在obj中的index
        d_idx_set = {obj.vertex_groups[vg.name].index
                     for n in d_series if (vg := obj.vertex_groups.get(n))}
        torso_vgs = {n: obj.vertex_groups.get(n) for n in torso_bones}
        torso_vgs = {n: vg for n, vg in torso_vgs.items() if vg}
        if not d_idx_set or not torso_vgs:
            continue
        for v in obj.data.vertices:
            # 计算该顶点的D系总权重
            d_total = sum(g.weight for g in v.groups
                          if g.group in d_idx_set and g.weight > 0.001)
            # 只有D系占主导（>= 阈值）才清除躯干骨权重
            # 腰臀过渡区（D系 < 0.6）保留混合，防止硬切割
            if d_total < D_DOMINANT_THRESHOLD:
                continue
            for vg in torso_vgs.values():
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.001:
                        vg.add([v.index], 0.0, 'REPLACE')
                        cleaned += 1
                        break
    return cleaned


def _weight_execute_missing_fill(armature, mesh_objects, missing_bones, weighted_vgs):
    """对无权重的MMD变形骨执行bell-curve分配（从最近有权重祖先）。"""
    # D系腿骨：若祖先搜索到达躯干骨（下半身/腰），跳过填充，
    # 避免踝关节骨权重被错误扩散到腰部/大腿区域
    D_SERIES_LEG = {"足D.L","足D.R","ひざD.L","ひざD.R","足首D.L","足首D.R","足先EX.L","足先EX.R"}
    TORSO_LIMIT  = {"下半身","腰","グルーブ","センター","全ての親"}
    mw = armature.matrix_world
    fixed, unfixed = [], []
    for bone in missing_bones:
        ancestor = bone.parent
        while ancestor and ancestor.name not in weighted_vgs:
            ancestor = ancestor.parent
        if not ancestor:
            unfixed.append(bone.name)
            continue
        # D系腿骨不允许从躯干骨继承，留给后续手动修复
        if bone.name in D_SERIES_LEG and ancestor.name in TORSO_LIMIT:
            unfixed.append(bone.name)
            continue

        anc_h = mw @ ancestor.head_local
        anc_t = mw @ ancestor.tail_local
        anc_vec = anc_t - anc_h
        anc_len = anc_vec.length
        if anc_len < 1e-6:
            unfixed.append(bone.name)
            continue
        anc_dir = anc_vec / anc_len

        bone_h_world = mw @ bone.head_local
        t_center = max(0.0, min(1.0, (bone_h_world - anc_h).dot(anc_dir) / anc_len))
        radius = 0.20
        success = False

        for obj in mesh_objects:
            src_vg = obj.vertex_groups.get(ancestor.name)
            if not src_vg:
                continue
            dst_vg = obj.vertex_groups.get(bone.name) or obj.vertex_groups.new(name=bone.name)
            for v in obj.data.vertices:
                w_src = 0.0
                for g in v.groups:
                    if g.group == src_vg.index:
                        w_src = g.weight
                        break
                if w_src <= 0.001:
                    continue
                v_world = obj.matrix_world @ v.co
                t_v = (v_world - anc_h).dot(anc_dir) / anc_len
                dist = abs(t_v - t_center)
                if dist >= radius:
                    continue
                influence = (1.0 - dist / radius) * w_src
                cur = 0.0
                for g in v.groups:
                    if g.group == dst_vg.index:
                        cur = g.weight
                        break
                dst_vg.add([v.index], min(1.0, cur + influence), 'REPLACE')
                success = True

        (fixed if success else unfixed).append(bone.name)
    return fixed, unfixed


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — 孤立骨：检查
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_check_orphan_weights(bpy.types.Operator):
    """检查纯ASCII名称的孤立变形骨（非MMD骨有顶点权重），预览将转移到哪个MMD骨。
    不修改任何数据，仅在UI中显示结果。"""
    bl_idname = "object.check_orphan_weights"
    bl_label = "检查孤立骨（非MMD骨有权重）"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        weighted_vgs = _weight_collect_weighted_vgs(mesh_objects)
        valid_bones = [b for b in armature.data.bones
                       if b.use_deform and not _weight_is_orphan(b.name)]
        orphan_bones = [b for b in armature.data.bones
                        if b.use_deform and _weight_is_orphan(b.name)
                        and b.name in weighted_vgs]

        targets = _weight_compute_orphan_targets(armature, mesh_objects, orphan_bones, valid_bones)

        scene = context.scene
        scene.weight_orphan_check_done = True
        scene.weight_orphan_count = len(targets)
        preview_parts = [f"{b.name}→{t.name}[{m}]" for b, (t, m) in list(targets.items())[:8]]
        scene.weight_orphan_preview = ' | '.join(preview_parts)
        if len(targets) > 8:
            scene.weight_orphan_preview += f' ...共{len(targets)}个'

        if targets:
            self.report({'WARNING'}, f"发现 {len(targets)} 个孤立骨待转移")
        else:
            self.report({'INFO'}, "✅ 无孤立骨（所有变形骨名称均含日文）")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — 孤立骨：修复
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_fix_orphan_weights(bpy.types.Operator):
    """将孤立变形骨（纯ASCII名称）的顶点权重，按顶点重心距骨骼中点最近原则，
    转移到最近的有效MMD变形骨。操作不可逆，建议先运行检查确认目标骨。"""
    bl_idname = "object.fix_orphan_weights"
    bl_label = "修复：转移孤立骨权重到最近MMD骨"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        weighted_vgs = _weight_collect_weighted_vgs(mesh_objects)
        valid_bones = [b for b in armature.data.bones
                       if b.use_deform and not _weight_is_orphan(b.name)]
        orphan_bones = [b for b in armature.data.bones
                        if b.use_deform and _weight_is_orphan(b.name)
                        and b.name in weighted_vgs]

        targets = _weight_compute_orphan_targets(armature, mesh_objects, orphan_bones, valid_bones)
        redirected = _weight_execute_orphan_transfer(mesh_objects, targets, armature)

        # 清理D系腿骨与躯干骨的冲突权重（无论本次是否有孤立骨待转移，都执行）
        cleaned = _weight_cleanup_leg_torso_conflict(armature, mesh_objects)

        # 清理后重建髋部渐变过渡区（cleanup会清除blend zone，需在最后重建）
        _create_hip_blend_zone(armature, mesh_objects)

        # 重置检查状态（权重已变，结果过期）
        context.scene.weight_orphan_check_done = False
        context.scene.weight_orphan_count = 0

        if redirected:
            names = ' | '.join(redirected[:6]) + ('...' if len(redirected) > 6 else '')
            self.report({'INFO'}, f"已转移 {len(redirected)} 个孤立骨: {names}  清理冲突顶点: {cleaned}")
        else:
            self.report({'INFO'}, f"✅ 无孤立骨需要处理  清理冲突顶点: {cleaned}")
        weight_monitor.auto_check_after_step(context, armature, "step_7", "孤立骨修复")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — 缺失权重：检查
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_check_missing_weights(bpy.types.Operator):
    """检查有效MMD变形骨（含日文名称）中无顶点权重的骨骼，预览将从哪个祖先分配。
    不修改任何数据，仅在UI中显示结果。"""
    bl_idname = "object.check_missing_weights"
    bl_label = "检查MMD骨骼缺失权重"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        weighted_vgs = _weight_collect_weighted_vgs(mesh_objects)
        missing = [b for b in armature.data.bones
                   if b.use_deform and not _weight_is_orphan(b.name)
                   and b.name not in weighted_vgs]

        # 预览每个骨骼将从哪个祖先接收权重
        preview_parts = []
        for bone in missing[:10]:
            ancestor = bone.parent
            while ancestor and ancestor.name not in weighted_vgs:
                ancestor = ancestor.parent
            src = ancestor.name if ancestor else "无祖先"
            preview_parts.append(f"{bone.name}←{src}")

        scene = context.scene
        scene.weight_missing_check_done = True
        scene.weight_missing_count = len(missing)
        scene.weight_missing_names = ' | '.join(preview_parts)
        if len(missing) > 10:
            scene.weight_missing_names += f' ...共{len(missing)}个'

        if missing:
            self.report({'WARNING'}, f"发现 {len(missing)} 个MMD骨骼无权重")
        else:
            self.report({'INFO'}, "✅ 所有MMD变形骨骼均有顶点权重")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — 缺失权重：修复
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_fix_missing_weights(bpy.types.Operator):
    """对无顶点权重的MMD变形骨（D系骨/扭转骨/桥接骨等），从最近有权重的祖先骨骼
    按骨骼轴投影+bell-curve衰减（半径20%）分配权重。不减少祖先权重，
    由MMD导出时自动归一化。"""
    bl_idname = "object.fix_missing_weights"
    bl_label = "修复：从祖先骨骼分配缺失权重"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        weighted_vgs = _weight_collect_weighted_vgs(mesh_objects)
        missing = [b for b in armature.data.bones
                   if b.use_deform and not _weight_is_orphan(b.name)
                   and b.name not in weighted_vgs]

        fixed, unfixed = _weight_execute_missing_fill(armature, mesh_objects, missing, weighted_vgs)

        # 缺失权重填充后再次清理D系腿骨与躯干骨冲突，防止bell-curve误扩散
        cleaned = _weight_cleanup_leg_torso_conflict(armature, mesh_objects)

        # 清理后重建髋部渐变过渡区（cleanup会清除blend zone，需在最后重建）
        _create_hip_blend_zone(armature, mesh_objects)

        # 重置检查状态
        context.scene.weight_missing_check_done = False
        context.scene.weight_missing_count = 0

        parts = []
        if fixed:
            parts.append(f"补全 {len(fixed)} 个: {', '.join(fixed[:6])}{'...' if len(fixed)>6 else ''}")
        if unfixed:
            parts.append(f"无祖先跳过 {len(unfixed)} 个: {', '.join(unfixed[:4])}")
        if cleaned:
            parts.append(f"清理冲突 {cleaned} 顶点")
        if not parts:
            parts.append("✅ 所有MMD变形骨均有权重，无需操作")
        self.report({'INFO'}, ' | '.join(parts))
        weight_monitor.auto_check_after_step(context, armature, "step_8", "缺失权重修复")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# 独立的腿部权重冲突清理（D系骨 vs 下半身/腰）
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_cleanup_leg_conflict(bpy.types.Operator):
    """清理腿部D系骨（足D/ひざD/足首D）与躯干骨（下半身/腰）的权重冲突。
    当同一顶点同时被D系骨和躯干骨影响时，移除躯干骨权重。"""
    bl_idname = "object.cleanup_leg_conflict"
    bl_label = "清理腿部权重冲突（D系 vs 下半身）"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        cleaned = _weight_cleanup_leg_torso_conflict(armature, mesh_objects)
        if cleaned:
            self.report({'INFO'}, f"✅ 已清理 {cleaned} 个冲突权重（D系骨区域移除下半身/腰权重）")
        else:
            self.report({'INFO'}, "✅ 无冲突权重，无需清理")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# 独立的髋部渐变过渡区 检查 + 修复（通用，适用于任何 XPS/DAZ/CC3 等来源模型）
# ─────────────────────────────────────────────────────────────────────────────

class OBJECT_OT_check_hip_blend_zone(bpy.types.Operator):
    """检查髋部（下半身↔足D.L/R）是否存在权重渐变过渡区。
    XPS/DAZ 等来源模型的权重通常是二值的，会导致腰骨运动时出现硬切割。"""
    bl_idname = "object.check_hip_blend_zone"
    bl_label = "检查髋部渐变区"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        result = _check_hip_blend_zone(mesh_objects)
        scene = context.scene
        scene.hip_blend_check_done  = True
        scene.hip_blend_left_count  = result["left_blend"]
        scene.hip_blend_right_count = result["right_blend"]
        scene.hip_blend_left_binary = result["left_binary"]
        scene.hip_blend_right_binary = result["right_binary"]

        if result["left_binary"] > 100 or result["right_binary"] > 100:
            self.report({'WARNING'},
                f"髋部过渡区为二值权重：左={result['left_binary']}个硬边顶点  右={result['right_binary']}个  "
                f"（过渡混合顶点：左={result['left_blend']}  右={result['right_blend']}）"
                f" → 建议点「修复」")
        else:
            self.report({'INFO'},
                f"✅ 髋部渐变区正常（混合顶点：左={result['left_blend']}  右={result['right_blend']}）")
        return {'FINISHED'}


class OBJECT_OT_fix_hip_blend_zone(bpy.types.Operator):
    """修复髋部渐变区：在足D.L/R权重范围顶部创建下半身权重渐变，
    解决 XPS/DAZ/CC3 等来源模型的腰骨运动硬切割问题。"""
    bl_idname = "object.fix_hip_blend_zone"
    bl_label = "修复髋部渐变区"

    transition_height: bpy.props.FloatProperty(
        name="渐变高度",
        description="足D顶部往下多少单位开始渐变（默认1.5，可根据模型比例调整）",
        default=1.5, min=0.3, max=5.0
    )

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        modified = _create_hip_blend_zone(armature, mesh_objects, self.transition_height)
        context.scene.hip_blend_check_done = False  # 重置，需重新检查

        if modified > 0:
            self.report({'INFO'},
                f"✅ 髋部渐变区已创建（修改 {modified} 个顶点，渐变高度={self.transition_height:.1f}）")
        else:
            self.report({'WARNING'}, "未找到需要渐变的顶点（足D.L/R 或 下半身 不存在）")
        weight_monitor.auto_check_after_step(context, armature, "hip_fix", "髋部渐变修复")
        return {'FINISHED'}


def _check_hip_blend_zone(mesh_objects):
    """统计髋部过渡区的状态：有多少顶点已经混合，有多少还是二值。"""
    result = {"left_blend": 0, "right_blend": 0, "left_binary": 0, "right_binary": 0}
    for obj in mesh_objects:
        for d_bone, key_blend, key_binary in [
            ("足D.L", "left_blend",  "left_binary"),
            ("足D.R", "right_blend", "right_binary"),
        ]:
            vg_d = obj.vertex_groups.get(d_bone)
            vg_s = obj.vertex_groups.get("下半身")
            if not vg_d or not vg_s:
                continue
            idx_d, idx_s = vg_d.index, vg_s.index
            mw = obj.matrix_world

            z_vals = [(mw @ v.co).z for v in obj.data.vertices
                      for g in v.groups if g.group == idx_d and g.weight > 0.001]
            if not z_vals:
                continue
            z_max = max(z_vals)
            z_top_zone = z_max - 1.5  # 只检查顶部 1.5 单位

            for v in obj.data.vertices:
                vz = (mw @ v.co).z
                if vz < z_top_zone:
                    continue
                wd = ws = 0.0
                for g in v.groups:
                    if g.group == idx_d: wd = g.weight
                    if g.group == idx_s: ws = g.weight
                if wd <= 0.001:
                    continue
                if ws > 0.05:
                    result[key_blend] += 1   # 已经有混合
                elif wd > 0.85:
                    result[key_binary] += 1  # 二值，需要修复
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 保留一键合并版本（供自动转换流程调用）
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_check_fix_missing_weights(bpy.types.Operator):
    """一键执行孤立骨重定向（Phase1）+ 缺失权重补全（Phase2）。
    供"一键全流程转换"内部调用，手动使用建议分步骤检查。"""
    bl_idname = "object.check_fix_missing_weights"
    bl_label = "一键修复全部权重问题"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}
        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        weighted_vgs = _weight_collect_weighted_vgs(mesh_objects)
        valid_bones = [b for b in armature.data.bones
                       if b.use_deform and not _weight_is_orphan(b.name)]
        orphan_bones = [b for b in armature.data.bones
                        if b.use_deform and _weight_is_orphan(b.name)
                        and b.name in weighted_vgs]
        targets = _weight_compute_orphan_targets(armature, mesh_objects, orphan_bones, valid_bones)
        redirected = _weight_execute_orphan_transfer(mesh_objects, targets, armature)

        weighted_vgs = _weight_collect_weighted_vgs(mesh_objects)
        missing = [b for b in armature.data.bones
                   if b.use_deform and not _weight_is_orphan(b.name)
                   and b.name not in weighted_vgs]
        fixed, unfixed = _weight_execute_missing_fill(armature, mesh_objects, missing, weighted_vgs)

        # 全部权重操作完成后，统一清理冲突再重建髋部渐变区
        _weight_cleanup_leg_torso_conflict(armature, mesh_objects)
        _create_hip_blend_zone(armature, mesh_objects)

        parts = []
        if redirected:
            parts.append(f"[P1] 孤立骨→MMD {len(redirected)}个")
        if fixed:
            parts.append(f"[P2] 补全权重 {len(fixed)}个")
        if unfixed:
            parts.append(f"[P2] 跳过 {len(unfixed)}个(无祖先)")
        if not parts:
            parts.append("✅ 权重正常")
        self.report({'INFO'}, ' | '.join(parts))
        weight_monitor.auto_check_after_step(context, armature, "step_11", "一键权重修复")
        return {'FINISHED'}

# ─────────────────────────────────────────────────────────────────────────────
# 手动权重转移（通用，适配任意骨骼名称）
# ─────────────────────────────────────────────────────────────────────────────
class OBJECT_OT_manual_weight_transfer(bpy.types.Operator):
    """手动指定源骨骼和目标骨骼，将源骨骼的所有顶点权重叠加转移到目标骨骼。
    转移后源骨骼VG权重清零（保留VG）。
    适用于：修复孤立骨权重分配错误、手动调整肩/腕等骨骼权重分布。"""
    bl_idname = "object.manual_weight_transfer"
    bl_label = "手动转移权重（源 → 目标）"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择骨架对象")
            return {'CANCELLED'}

        src_name = context.scene.weight_manual_src
        dst_name = context.scene.weight_manual_dst
        if not src_name or not dst_name:
            self.report({'ERROR'}, "请填写源骨骼和目标骨骼名称")
            return {'CANCELLED'}
        if src_name == dst_name:
            self.report({'ERROR'}, "源骨骼和目标骨骼不能相同")
            return {'CANCELLED'}

        mesh_objects = _weight_get_mesh_objects(context, armature)
        if not mesh_objects:
            self.report({'WARNING'}, "未找到绑定网格")
            return {'CANCELLED'}

        transferred_verts = 0
        affected_meshes = 0

        for obj in mesh_objects:
            src_vg = obj.vertex_groups.get(src_name)
            if not src_vg:
                continue
            dst_vg = obj.vertex_groups.get(dst_name)
            if not dst_vg:
                dst_vg = obj.vertex_groups.new(name=dst_name)

            count = 0
            for v in obj.data.vertices:
                w_src = 0.0
                for g in v.groups:
                    if g.group == src_vg.index:
                        w_src = g.weight
                        break
                if w_src <= 0.001:
                    continue

                cur_dst = 0.0
                for g in v.groups:
                    if g.group == dst_vg.index:
                        cur_dst = g.weight
                        break

                dst_vg.add([v.index], min(1.0, cur_dst + w_src), 'REPLACE')
                src_vg.add([v.index], 0.0, 'REPLACE')
                count += 1

            if count:
                transferred_verts += count
                affected_meshes += 1

        if transferred_verts:
            self.report({'INFO'},
                f"✅ 已转移 {transferred_verts} 个顶点权重：{src_name} → {dst_name}（{affected_meshes}个网格）")
        else:
            self.report({'WARNING'}, f"源骨骼 '{src_name}' 无顶点权重，无需转移")
        return {'FINISHED'}
