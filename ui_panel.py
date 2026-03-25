import bpy
import os
import json

ARM_BEND_THRESHOLD = 3.0  # 与 pose_operator.py 保持一致

from datetime import datetime as _dt
INSTALL_TIME = _dt.now().strftime("%Y-%m-%d %H:%M") + " (fix: 大腿权重渐变区)"

class OBJECT_OT_load_preset(bpy.types.Operator):
    bl_idname = "object.load_preset"
    bl_label = "Load Preset"
    
    preset_name: bpy.props.StringProperty()
    
    def execute(self, context):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        presets_dir = os.path.join(script_dir, "presets")
        preset_path = os.path.join(presets_dir, f"{self.preset_name}.json")
        
        if os.path.exists(preset_path):
            with open(preset_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
                
            for prop_name, bone_name in preset_data.items():
                if hasattr(context.scene, prop_name):
                    setattr(context.scene, prop_name, bone_name)
        
        return {'FINISHED'}

class OBJECT_PT_skeleton_hierarchy(bpy.types.Panel):
    bl_label = "Convert to MMD"
    bl_idname = "OBJECT_PT_convert_to_mmd"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Convert to MMD"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 版本时间戳（用于确认安装成功）
        layout.label(text=f"v: {INSTALL_TIME}", icon='INFO')

        # 检查活动对象是否为骨架
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            layout.menu("TOPBAR_MT_file_import", text="Import", icon='IMPORT')
            return

        # 添加带有标签、prop_search用于骨骼和填充按钮的行的函数
        def add_bone_row_with_button(layout, label_text, prop_name):
            row = layout.row(align=True)
            split_name = row.split(factor=0.1, align=True)
            # 左侧部分：骨骼名称
            split_name.label(text=label_text)
            # action部分占用剩余的0.8
            split_action = split_name.split(factor=1)
            sub_split = split_action.split(factor=(0.49*0.1), align=True)
            # 按钮部分
            sub_split.operator(
                "object.fill_from_selection_specific",
                text="",
                icon='ZOOM_SELECTED'
            ).bone_property = prop_name
            # 选择框部分
            sub_split.prop_search(
                scene,
                prop_name,
                obj.data,
                "bones",
                text=""
            )
        def add_symmetric_bones_with_buttons(layout, label_text, left_prop, right_prop):
            # 第一层划分：将行分为 0.2 和 0.8 两部分
            row = layout.row(align=True)
            # 骨骼名字（Name）使用0.2
            split_name = row.split(factor=0.1, align=True)
            split_name.label(text=label_text)  # 显示骨骼名字
            # split() 的比例是基于当前容器的剩余空间
            # action部分使用name剩下的0.8
            split_action = split_name.split(factor=1, align=True)

            # 左侧操作部分 使用action的0.49
            split_left_action = split_action.split(factor=0.49, align=True)  # 使用相对比例
            col_left_action = split_left_action.column(align=True)
            row_left_action = col_left_action.row(align=True)

            # 在左侧操作部分进一步划分为 Button 和 Search Box
            sub_split_left_button = row_left_action.split(factor=0.1, align=True)
            sub_split_left_button.operator(
                "object.fill_from_selection_specific",
                text="",
                icon='ZOOM_SELECTED'
            ).bone_property = left_prop  # 左侧按钮（Button）
            sub_split_left_button.prop_search(
                scene,
                left_prop,
                obj.data,
                "bones",
                text=""  # 左侧选择框（Search Box）
            )

            # 中间部分使用left_action剩下的0.51划分0.02/(0.02+0.49)给中间分割符
            split_divider = split_left_action.split(factor=(0.02/(0.02+0.49)), align=True)  # 动态计算剩余比例
            split_divider.label(text="|")  # 使用 "|" 模拟分割线

            # 右侧操作部分使用剩下的0.49
            split_right_action = split_divider.split(factor=1,align=True)
            col_right_action = split_right_action.column(align=True)
            row_right_action = col_right_action.row(align=True)

            # 在右侧操作部分进一步划分为 Button 和 Search Box
            sub_split_right_button = row_right_action.split(factor=0.1, align=True)
            sub_split_right_button.operator(
                "object.fill_from_selection_specific",
                text="",
                icon='ZOOM_SELECTED'
            ).bone_property = right_prop  # 右侧按钮（Button）
            sub_split_right_button.prop_search(
                scene,
                right_prop,
                obj.data,
                "bones",
                text=""  # 右侧选择框（Search Box）
            )
        def add_finger_bones_with_buttons(layout, label_text, first_prop, second_prop, third_prop):
            
            divider_ratio = 0.02
            split_ratio = (1-2*divider_ratio)/3
            # 第一层划分：将行分为 0.2 和 0.8 两部分
            row = layout.row(align=True)
            # 骨骼名字（Name）使用0.2
            split_name = row.split(factor=0.1, align=True)
            split_name.label(text=label_text)  # 显示骨骼名字
            # split() 的比例是基于当前容器的剩余空间
            # action部分使用name剩下的0.8
            split_action = split_name.split(factor=1, align=True)

            # 右侧操作区域划分为三列：split_ratio divider_ratio split_ratio divider_ratio split_ratio
            # 第一个操作区域（0.32）
            split_first_action = split_action.split(factor=split_ratio, align=True)
            col_first_action = split_first_action.column(align=True)
            row_first_action = col_first_action.row(align=True)
            # 在右侧操作部分进一步划分为 Button 和 Search Box
            sub_split_first_button = row_first_action.split(factor=0.1, align=True)
            sub_split_first_button.operator(
                "object.fill_from_selection_specific",
                text="",
                icon='ZOOM_SELECTED'
            ).bone_property = first_prop  # 右側按钮（Button）
            sub_split_first_button.prop_search(
                scene,
                first_prop,
                obj.data,
                "bones",
                text=""  # 右側选择框（Search Box）
            )
            # 中间分割线（{divider_ratio}）
            split_divider1 = split_first_action.split(factor=divider_ratio/(1-split_ratio), align=True)
            split_divider1.label(text="|")  # 分割线
            # 第二个操作区域（0.32）
            split_second_bone = split_divider1.split(factor=split_ratio/(1-split_ratio-divider_ratio), align=True)
            col_second_bone = split_second_bone.column(align=True)
            row_second_bone = col_second_bone.row(align=True)
            # 在右侧操作部分进一步划分为 Button 和 Search Box
            sub_split_second_button = row_second_bone.split(factor=0.1, align=True)
            sub_split_second_button.operator(
                "object.fill_from_selection_specific",
                text="",
                icon='ZOOM_SELECTED'
            ).bone_property = second_prop  # 右側按钮（Button）
            sub_split_second_button.prop_search(
                scene,
                second_prop,
                obj.data,
                "bones",
                text=""  # 右側选择框（Search Box）
            )
            # 中间分割线（{divider_ratio}）
            split_divider2 = split_second_bone.split(factor=divider_ratio/(1-split_ratio*2-divider_ratio), align=True)
            split_divider2.label(text="|")
            
            # 第三个操作区
            split_third_bone = split_divider2.split(factor=1, align=True)
            col_third_bone = split_third_bone.column(align=True)
            row_third_bone = col_third_bone.row(align=True)
            # 在右侧操作部分进一步划分为 Button 和 Search Box
            sub_split_third_button = row_third_bone.split(factor=0.1, align=True)
            sub_split_third_button.operator(
                "object.fill_from_selection_specific",
                text="",
                icon='ZOOM_SELECTED'
            ).bone_property = third_prop  # 右側按钮（Button）
            sub_split_third_button.prop_search(
                scene,
                third_prop,
                obj.data,
                "bones",
                text=""  # 右側选择框（Search Box）
            )
        # 添加选项卡按钮 - 移动到条件判断外部，使其始终可见
        row = layout.row()
        row.prop(scene, "my_enum", expand=True)
        if scene.my_enum == 'option1':

            # 新增 EnumProperty 下拉菜单
            row = layout.row()
            row.prop(scene, "preset_enum", text="")
        
            main_col = layout.column(align=True)
            # 全ての親到腰部分
            full_body_box = main_col.box()
            col = full_body_box.column()
            add_bone_row_with_button(col, "操作中心:", "control_center_bone")
            add_bone_row_with_button(col, "全ての親", "all_parents_bone")
            add_bone_row_with_button(col, "センター", "center_bone")
            add_bone_row_with_button(col, "グルーブ", "groove_bone")
            add_bone_row_with_button(col, "腰", "hip_bone")

            # 上半身到頭部分
            upper_body_box = main_col.box()
            col = upper_body_box.column()
            add_bone_row_with_button(col, "上半身", "upper_body_bone")
            add_bone_row_with_button(col, "上半身2", "upper_body2_bone")
            add_bone_row_with_button(col, "首", "neck_bone")
            add_bone_row_with_button(col, "頭", "head_bone")
            add_symmetric_bones_with_buttons(col, "目:", "left_eye_bone", "right_eye_bone")
            add_symmetric_bones_with_buttons(col, "肩:", "left_shoulder_bone", "right_shoulder_bone")
            add_symmetric_bones_with_buttons(col, "腕:", "left_upper_arm_bone", "right_upper_arm_bone")
            add_symmetric_bones_with_buttons(col, "ひじ:", "left_lower_arm_bone", "right_lower_arm_bone")
            add_symmetric_bones_with_buttons(col, "手首:", "left_hand_bone", "right_hand_bone")

            # 下半身到足首部分
            lower_body_box = main_col.box()
            col = lower_body_box.column()
            add_bone_row_with_button(col, "下半身", "lower_body_bone")
            add_symmetric_bones_with_buttons(col, "足:", "left_thigh_bone", "right_thigh_bone")
            add_symmetric_bones_with_buttons(col, "ひざ:", "left_calf_bone", "right_calf_bone")
            add_symmetric_bones_with_buttons(col, "足首:", "left_foot_bone", "right_foot_bone")
            add_symmetric_bones_with_buttons(col, "足先EX:", "left_toe_bone", "right_toe_bone")

            fingers_box = main_col.box()
            col = fingers_box.column()
            add_finger_bones_with_buttons(col, "左親指:", "left_thumb_0", "left_thumb_1", "left_thumb_2")
            add_finger_bones_with_buttons(col, "左人指:", "left_index_1", "left_index_2", "left_index_3")
            add_finger_bones_with_buttons(col, "左中指:", "left_middle_1", "left_middle_2", "left_middle_3")
            add_finger_bones_with_buttons(col, "左薬指:", "left_ring_1", "left_ring_2", "left_ring_3")
            add_finger_bones_with_buttons(col, "左小指:", "left_pinky_1", "left_pinky_2", "left_pinky_3")

            add_finger_bones_with_buttons(col, "右親指:", "right_thumb_0", "right_thumb_1", "right_thumb_2")
            add_finger_bones_with_buttons(col, "右人指:", "right_index_1", "right_index_2", "right_index_3")
            add_finger_bones_with_buttons(col, "右中指:", "right_middle_1", "right_middle_2", "right_middle_3")
            add_finger_bones_with_buttons(col, "右薬指:", "right_ring_1", "right_ring_2", "right_ring_3")
            add_finger_bones_with_buttons(col, "右小指:", "right_pinky_1", "right_pinky_2", "right_pinky_3")    
                
            # 添加导入/导出预设按钮
            row = layout.row()
            row.operator("object.import_preset", text="导入预设")
            row.operator("object.export_preset", text="导出预设")

            # ══════════════════════════════════════════════
            # A-Pose 区域（⚠️ 必须在步骤1之前完成！）
            # ══════════════════════════════════════════════
            apose_box = layout.box()
            r_title = apose_box.row()
            r_title.alert = True
            r_title.label(text="⚠️ A-Pose 转换（必须在步骤1之前完成！）", icon='ERROR')

            # 第一步：检测关节
            apose_box.operator("object.check_arm_straightness",
                               text="0a. 检测手臂关节", icon='VIEWZOOM')

            # 检测结果显示
            if scene.arm_check_done:
                if scene.arm_check_has_problem:
                    r = apose_box.row()
                    r.alert = True
                    r.label(
                        text=f"⚠️ 肘弯曲：左 {scene.arm_check_left_bend:.1f}°  右 {scene.arm_check_right_bend:.1f}°",
                        icon='ERROR'
                    )
                    lw = getattr(scene, "arm_check_left_wrist", 0.0)
                    rw = getattr(scene, "arm_check_right_wrist", 0.0)
                    if lw > ARM_BEND_THRESHOLD or rw > ARM_BEND_THRESHOLD:
                        r2 = apose_box.row()
                        r2.alert = True
                        r2.label(
                            text=f"⚠️ 腕弯曲：左 {lw:.1f}°  右 {rw:.1f}°",
                            icon='ERROR'
                        )
                    # 第二步：修复弯曲（有问题时显示）
                    fix_row = apose_box.row(align=True)
                    fix_row.alert = True
                    fix_row.operator("object.fix_elbow_straightness", text="0b. 修复肘弯曲", icon='BONE_DATA')
                    fix_row.operator("object.fix_wrist_straightness", text="0c. 修复腕弯曲", icon='BONE_DATA')
                    apose_box.label(text="修复完成后重新检测，确认 ✅ 后再转A-Pose", icon='INFO')
                else:
                    row2 = apose_box.row()
                    row2.label(
                        text=f"✅ 关节笔直  肘 左{scene.arm_check_left_bend:.1f}° 右{scene.arm_check_right_bend:.1f}°",
                        icon='CHECKMARK'
                    )

            # 最后一步：转A-Pose（始终显示在最底部）
            apose_box.separator(factor=0.3)
            r_apose = apose_box.row()
            if scene.arm_check_done and scene.arm_check_has_problem:
                r_apose.alert = True
                r_apose.operator("object.convert_to_apose",
                                 text="0d. 转A-Pose（建议先修复弯曲！）", icon='POSE_HLT')
            elif not scene.arm_check_done:
                r_apose.operator("object.convert_to_apose",
                                 text="0d. 转A-Pose（建议先检测关节）", icon='POSE_HLT')
            else:
                r_apose.operator("object.convert_to_apose",
                                 text="0d. 转A-Pose ✅", icon='POSE_HLT')

            # 步骤1-6：骨骼结构搭建
            # 解析权重监控状态
            try:
                wm_status = json.loads(scene.get("wm_step_status", "{}"))
            except (json.JSONDecodeError, TypeError, ValueError):
                wm_status = {}

            row = layout.row()
            row.operator("object.rename_to_mmd", text="1. 重命名为MMD")
            sub = row.row()
            sub.operator("object.complete_missing_bones", text="2. 补全缺失骨骼")
            s2 = wm_status.get("step_2", "")
            if s2 == "ok":
                sub.label(text="", icon='CHECKMARK')
            elif s2 in ("warning", "error"):
                sub.label(text="", icon='ERROR')

            row3 = layout.row(align=True)
            row3.operator("object.split_spine_shoulder", text="3. 骨骼切分（spine/shoulder）", icon='BONE_DATA')
            s3 = wm_status.get("step_3", "")
            if s3 == "ok":
                row3.label(text="", icon='CHECKMARK')
            elif s3 in ("warning", "error"):
                row3.label(text="", icon='ERROR')

            row = layout.row()
            row.operator("object.add_mmd_ik", text="4. 添加MMD IK")
            row.operator("object.create_bone_group", text="5. 创建骨骼集合")

            layout.operator("object.add_twist_bones", text="6. 添加扭转骨骼（腕捩/手捩）", icon='CON_ROTLIKE')

            layout.separator(factor=0.5)

            # 步骤7/8：权重检查与修复
            weight_box = layout.box()
            row_hdr = weight_box.row()
            row_hdr.label(text="权重检查与修复", icon='WPAINT_HLT')
            row_hdr.operator("object.weight_health_check", text="权重体检", icon='FUND')

            # ── 权重监控状态 ──
            wm_result = scene.get("wm_last_check_result", "")
            if wm_result:
                wm_row = weight_box.row()
                if wm_result.startswith("✅"):
                    wm_row.label(text=wm_result, icon='CHECKMARK')
                else:
                    wm_row.alert = True
                    wm_row.label(text=wm_result, icon='ERROR')

            weight_box.separator(factor=0.3)

            # ── 7. 孤立骨（非MMD骨有权重） ──
            row = weight_box.row(align=True)
            row.operator("object.check_orphan_weights", text="7. 检查孤立骨", icon='VIEWZOOM')
            s7 = wm_status.get("step_7", "")
            if s7 == "ok":
                row.label(text="", icon='CHECKMARK')
            elif s7 in ("warning", "error"):
                row.label(text="", icon='ERROR')
            if scene.weight_orphan_check_done:
                if scene.weight_orphan_count == 0:
                    weight_box.label(text="✅ 无孤立骨", icon='CHECKMARK')
                else:
                    r = weight_box.row()
                    r.alert = True
                    r.label(text=f"⚠️ {scene.weight_orphan_count} 个孤立骨待转移", icon='ERROR')
                    if scene.weight_orphan_preview:
                        for line in scene.weight_orphan_preview.split(' | ')[:4]:
                            weight_box.label(text=f"  {line}", icon='BLANK1')
                    weight_box.operator("object.fix_orphan_weights",
                                        text="修复：转移到最近MMD骨", icon='BONE_DATA')

            weight_box.separator(factor=0.5)

            # ── 8. MMD变形骨缺失权重 ──
            row = weight_box.row(align=True)
            row.operator("object.check_missing_weights", text="8. 检查缺失MMD骨权重", icon='VIEWZOOM')
            s8 = wm_status.get("step_8", "")
            if s8 == "ok":
                row.label(text="", icon='CHECKMARK')
            elif s8 in ("warning", "error"):
                row.label(text="", icon='ERROR')
            if scene.weight_missing_check_done:
                if scene.weight_missing_count == 0:
                    weight_box.label(text="✅ 所有MMD变形骨均有权重", icon='CHECKMARK')
                else:
                    r = weight_box.row()
                    r.alert = True
                    r.label(text=f"⚠️ {scene.weight_missing_count} 个MMD骨无权重", icon='ERROR')
                    if scene.weight_missing_names:
                        for line in scene.weight_missing_names.split(' | ')[:4]:
                            weight_box.label(text=f"  {line}", icon='BLANK1')
                    weight_box.operator("object.fix_missing_weights",
                                        text="修复：从祖先分配权重", icon='WPAINT_HLT')

            # ── 7b / 8b：髋部渐变区（步骤7/8修复后自动重建，此处可验证结果） ──
            weight_box.separator(factor=0.5)
            hip_row = weight_box.row(align=True)
            hip_row.label(text="髋部渐变区（腰腿权重过渡）", icon='MOD_SMOOTH')
            hip_act = weight_box.row(align=True)
            hip_act.operator("object.check_hip_blend_zone", text="检查渐变区", icon='VIEWZOOM')
            hip_act.operator("object.fix_hip_blend_zone",   text="修复渐变区", icon='BRUSH_DATA')
            sh = wm_status.get("hip_fix", "")
            if sh == "ok":
                hip_act.label(text="", icon='CHECKMARK')
            elif sh in ("warning", "error"):
                hip_act.label(text="", icon='ERROR')
            if scene.hip_blend_check_done:
                lb = scene.hip_blend_left_binary;  rb = scene.hip_blend_right_binary
                lm = scene.hip_blend_left_count;   rm = scene.hip_blend_right_count
                if lb > 100 or rb > 100:
                    r = weight_box.row(); r.alert = True
                    r.label(text=f"⚠️ 硬切割：左={lb} 右={rb}  → 点「修复渐变区」", icon='ERROR')
                else:
                    weight_box.label(text=f"✅ 渐变正常  混合顶点：左={lm}  右={rm}", icon='CHECKMARK')

            # ── 手动权重转移（可选，任意骨骼名均可） ──
            weight_box.separator(factor=0.5)
            weight_box.label(text="手动转移权重（可选）", icon='BONE_DATA')
            weight_box.prop_search(scene, "weight_manual_src", obj.data, "bones", text="源骨骼")
            weight_box.prop_search(scene, "weight_manual_dst", obj.data, "bones", text="目标骨骼")
            weight_box.operator("object.manual_weight_transfer",
                                text="转移：源骨骼权重 → 目标骨骼", icon='FORWARD')

            layout.separator(factor=0.5)

            # 步骤9/10：网格与材质
            layout.operator("object.merge_meshes", text="9. 网格合并", icon='OBJECT_DATA')
            layout.operator("object.convert_materials_to_mmd", text="10. 材质转换（→MMD格式）", icon='MATERIAL')

            layout.separator()
            # 导出区域
            export_box = layout.box()
            export_box.label(text="导出 PMX", icon='EXPORT')
            export_box.operator("mmd_tools.convert_to_mmd_model", text="10.转换为 MMD 模型结构", icon='OUTLINER_OB_ARMATURE')
            export_box.operator("mmd_tools.export_pmx", text="11.导出 PMX", icon='EXPORT')

            layout.separator()
            # 一键全流程（串联所有步骤）
            layout.operator("object.auto_convert_to_mmd", text="一键全流程转换", icon='PLAY')

            layout.separator()
            layout.operator("object.use_mmd_tools_convert", text="使用mmdtools转换格式")
        # 骨骼清理选项卡
        elif scene.my_enum == 'option2':
            row = layout.row()
            row.operator("object.clear_unweighted_bones", text="清理无权重骨骼", icon='X')
            row.operator("object.merge_single_child_bones", text="合并单子级骨骼", icon='CONSTRAINT_BONE')

            layout.separator()
            # ══════════════════════════════════════════════
            # 功能C：基础权重验证
            # ══════════════════════════════════════════════
            box = layout.box()
            box.label(text="权重验证", icon='ARMATURE_DATA')
            box.operator("object.verify_weights", text="运行权重验证", icon='CHECKMARK')
            box.operator("object.fix_nondeform_weights",
                         text="修复头发/非变形骨权重", icon='BRUSH_DATA')

            if scene.weight_verify_done:
                orphan = scene.weight_verify_orphan_vgs
                total = getattr(scene, 'weight_verify_total_verts', 0)
                unweighted = scene.weight_verify_unweighted_verts
                no_vg = scene.weight_verify_bones_without_vg
                nondeform = getattr(scene, 'weight_verify_nondeform_verts', 0)
                nondeform_names = getattr(scene, 'weight_verify_nondeform_names', '')

                row = box.row()
                if nondeform == 0:
                    row.label(text="非变形骨权重: 0  ✅", icon='CHECKMARK')
                else:
                    row.label(text=f"非变形骨权重: {nondeform} 顶点 ⚠️", icon='ERROR')
                    if nondeform_names:
                        box.label(text=f"涉及骨骼: {nondeform_names}", icon='INFO')

                row = box.row()
                if orphan == 0:
                    row.label(text="孤儿顶点组: 0  ✅", icon='CHECKMARK')
                else:
                    row.label(text=f"孤儿顶点组: {orphan} ⚠️", icon='ERROR')
                    if scene.weight_verify_orphan_names:
                        box.label(text=scene.weight_verify_orphan_names, icon='INFO')
                    box.operator("object.clean_orphan_vertex_groups",
                                 text="一键清理孤儿顶点组", icon='TRASH')

                row = box.row()
                if unweighted == 0:
                    row.label(text="无权重顶点: 0  ✅", icon='CHECKMARK')
                else:
                    pct = f" ({unweighted/total:.1%})" if total > 0 else ""
                    row.label(text=f"无权重顶点: {unweighted}{pct} ❌", icon='ERROR')

                box.label(text=f"控制骨（无顶点组）: {no_vg}", icon='INFO')

            layout.separator()
            # ══════════════════════════════════════════════
            # 功能A：逐骨顶点数对比
            # ══════════════════════════════════════════════
            cmp_box = layout.box()
            cmp_box.label(text="逐骨权重分布对比", icon='LINENUMBERS_ON')
            cmp_box.prop(scene, "weight_ref_armature", text="参考骨架")
            cmp_box.operator("object.compare_bone_weights",
                             text="比较骨骼权重分布", icon='DRIVER_DISTANCE')

            if scene.weight_compare_done and scene.weight_compare_result:
                lines = scene.weight_compare_result.split("||")
                for line in lines[:12]:
                    icon = 'ERROR' if '⚠️' in line else ('INFO' if '📌' in line else 'CHECKMARK')
                    cmp_box.label(text=line, icon=icon)
                if len(lines) > 12:
                    cmp_box.label(text=f"... 还有 {len(lines)-12} 条（仅显示前12）", icon='BLANK1')

            layout.separator()
            # ══════════════════════════════════════════════
            # 功能B：冲突顶点高亮
            # ══════════════════════════════════════════════
            conf_box = layout.box()
            conf_box.label(text="冲突顶点检查（足D vs 下半身/腰）", icon='MODIFIER_ON')
            row = conf_box.row(align=True)
            row.operator("object.highlight_conflict_vertices",
                         text="高亮冲突顶点", icon='WPAINT_HLT')
            row.operator("object.clear_conflict_highlight",
                         text="清除", icon='X')

            if scene.weight_conflict_done:
                cnt = scene.weight_conflict_count
                if cnt == 0:
                    conf_box.label(text="✅ 无冲突顶点，腿部权重干净", icon='CHECKMARK')
                else:
                    r = conf_box.row()
                    r.alert = True
                    r.label(text=f"❌ {cnt} 个冲突顶点  →  Weight Paint 查看「冲突顶点」组", icon='ERROR')
                    conf_box.operator("object.cleanup_leg_conflict",
                                      text="一键修复：移除D系区域的下半身/腰权重", icon='BRUSH_DATA')

            layout.separator()
            # ══════════════════════════════════════════════
            # 髋部渐变区 检查 + 修复（通用，XPS/DAZ/CC3 等模型均适用）
            # ══════════════════════════════════════════════
            hip_box = layout.box()
            hip_box.label(text="髋部渐变区（腰腿权重过渡）", icon='MOD_SMOOTH')
            hip_box.label(text="修复 XPS/DAZ 等二值权重导致的腰部硬切割", icon='INFO')
            row = hip_box.row(align=True)
            row.operator("object.check_hip_blend_zone", text="检查", icon='VIEWZOOM')
            row.operator("object.fix_hip_blend_zone",   text="修复", icon='BRUSH_DATA')

            if scene.hip_blend_check_done:
                lb = scene.hip_blend_left_binary
                rb = scene.hip_blend_right_binary
                lm = scene.hip_blend_left_count
                rm = scene.hip_blend_right_count
                if lb > 100 or rb > 100:
                    r = hip_box.row()
                    r.alert = True
                    r.label(text=f"⚠️ 硬切割顶点：左={lb}  右={rb}  → 需要修复", icon='ERROR')
                    hip_box.label(text=f"已混合顶点：左={lm}  右={rm}", icon='INFO')
                else:
                    hip_box.label(text=f"✅ 过渡区正常  混合顶点：左={lm}  右={rm}", icon='CHECKMARK')

            layout.separator()
            # ══════════════════════════════════════════════
            # 功能D：摆 Pose 测试
            # ══════════════════════════════════════════════
            pose_box = layout.box()
            pose_box.label(text="变形效果测试", icon='POSE_HLT')
            row = pose_box.row(align=True)
            row.operator("object.pose_test_raise_leg",
                         text="摆姿势：抬左腿", icon='ARMATURE_DATA')
            row.operator("object.pose_test_reset",
                         text="恢复 Rest Pose", icon='LOOP_BACK')
