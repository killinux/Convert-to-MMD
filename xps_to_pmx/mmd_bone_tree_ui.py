"""MMD Bone Tree UI - Friendly bone hierarchy visualization and editing.

Features:
- Complete bone hierarchy tree view (3 display modes)
- Color-coded bone types
- Weight indicators
- Search and filter functionality
- Right-side detail panel
- Parent relationship validation
"""

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, EnumProperty
from typing import Dict, List, Tuple, Optional, Callable
import json

from . import mapping


# Global state for tree UI
_TREE_STATE = {
    'expanded_bones': {'全ての親', 'センター'},  # Default expanded bones
    'selected_bone': None,     # Currently selected bone for detail panel
    'search_term': '',
    'show_only_errors': False,
    'show_only_deform': False,
    'display_mode': 'complete',  # complete / compact / table
}


class XPSPMXBoneTreeProperties(PropertyGroup):
    """Property group for bone tree UI state."""

    bone_tree_search: StringProperty(
        name="Search",
        description="Search bone names",
        default=""
    )

    show_only_errors: BoolProperty(
        name="Only Show Errors",
        description="Show only bones with mapping issues",
        default=False
    )

    show_only_deform: BoolProperty(
        name="Only Deform Bones",
        description="Show only deform bones",
        default=False
    )

    auto_expand: BoolProperty(
        name="Auto Expand",
        description="Auto-expand all bones",
        default=False
    )

    display_mode: EnumProperty(
        name="Display Mode",
        description="Tree display mode",
        items=[
            ('complete', '完整树', 'Complete tree with all details'),
            ('compact', '简洁树', 'Compact tree view'),
            ('table', '表格', 'Table view'),
        ],
        default='complete'
    )

    detail_panel_bone: StringProperty(
        name="Detail Bone",
        description="Selected bone for detail panel",
        default=""
    )


def get_mmd_standard_skeleton() -> Optional[Dict]:
    """Load MMD standard skeleton from JSON file."""
    try:
        import os
        preset_path = os.path.join(
            os.path.dirname(mapping.__file__),
            'presets',
            'mmd_standard_skeleton.json'
        )
        # Try UTF-8 first, then UTF-8-sig (with BOM), then fall back to cp1252 for Windows
        encodings = ['utf-8', 'utf-8-sig', 'cp1252']
        data = None

        for encoding in encodings:
            try:
                with open(preset_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

        if data is None:
            print(f"Error loading MMD skeleton: unable to decode {preset_path}")
            return None

        # Ensure all bone names are proper UTF-8 strings
        bones = data.get('bones', {})
        cleaned_bones = {}
        for bone_name, bone_def in bones.items():
            # Ensure bone name is a proper string
            if isinstance(bone_name, bytes):
                bone_name = bone_name.decode('utf-8', errors='replace')
            cleaned_bones[str(bone_name)] = bone_def

        return cleaned_bones
    except Exception as e:
        print(f"Error loading MMD skeleton: {e}")
        return None


def get_bone_icon(bone_type: str) -> str:
    """Get icon for bone type."""
    icon_map = {
        'control': 'BONE_DATA',
        'center': 'POINT',
        'spine': 'BONE_DATA',
        'arm': 'BONE_DATA',
        'leg': 'BONE_DATA',
        'hand': 'BONE_DATA',
        'finger': 'BONE_DATA',
        'eye': 'HIDE_OFF',
        'd_bone': 'BONE_DATA',
        'ik': 'CON_CHILDOF',
        'twist': 'OUTLINER_OB_ARMATURE',
    }
    return icon_map.get(bone_type, 'BONE_DATA')


def get_bone_color(bone_type: str) -> Tuple[float, float, float, float]:
    """Get color for bone type (RGBA)."""
    color_map = {
        'control': (1.0, 0.4, 0.4, 1.0),      # Red
        'center': (0.8, 0.8, 0.8, 1.0),       # Gray
        'spine': (0.3, 0.8, 0.3, 1.0),        # Green
        'arm': (0.3, 0.7, 1.0, 1.0),          # Blue
        'leg': (0.3, 0.7, 1.0, 1.0),          # Blue
        'hand': (0.7, 0.7, 1.0, 1.0),         # Light Blue
        'finger': (0.7, 0.7, 1.0, 1.0),       # Light Blue
        'eye': (1.0, 1.0, 0.5, 1.0),          # Yellow
        'd_bone': (1.0, 1.0, 0.3, 1.0),       # Gold
        'ik': (1.0, 0.7, 0.3, 1.0),           # Orange
        'twist': (1.0, 0.5, 1.0, 1.0),        # Purple
    }
    return color_map.get(bone_type, (0.7, 0.7, 0.7, 1.0))


def format_weight_stars(weight_percentage: float) -> str:
    """Convert weight percentage to star rating."""
    if weight_percentage > 5.0:
        return "⬜⬜⬜⬜⬜"  # Very large
    elif weight_percentage > 2.0:
        return "⬜⬜⬜⬜"    # Large
    elif weight_percentage > 0.5:
        return "⬜⬜⬜"      # Medium
    elif weight_percentage > 0.0:
        return "⬜⬜"        # Small
    else:
        return "⭕"         # No weight


def should_show_bone(bone_obj, search_term: str, show_only_errors: bool, show_only_deform: bool) -> bool:
    """Check if bone should be displayed based on filters."""
    # Search filter
    if search_term:
        search_lower = search_term.lower()
        mmd_name = bone_obj.get('mmd_name', '').lower()
        if search_lower not in mmd_name:
            return False

    # Error filter (未映射 or parent mismatch)
    if show_only_errors:
        # For now, show all (will implement proper checking)
        pass

    # Deform filter
    if show_only_deform:
        is_deform = bone_obj.get('is_deform', False)
        if not is_deform:
            return False

    return True


class XPSPMX_OT_toggle_bone_expand(Operator):
    """Toggle bone expand/collapse state."""
    bl_idname = "xpspmx_tree.toggle_expand"
    bl_label = "Toggle Bone Expand"

    bone_name: StringProperty(name="Bone Name")

    def execute(self, context):
        if self.bone_name in _TREE_STATE['expanded_bones']:
            _TREE_STATE['expanded_bones'].remove(self.bone_name)
        else:
            _TREE_STATE['expanded_bones'].add(self.bone_name)

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class XPSPMX_OT_select_bone_detail(Operator):
    """Select a bone to show its details in side panel."""
    bl_idname = "xpspmx_tree.select_bone"
    bl_label = "Select Bone for Details"

    bone_name: StringProperty(name="Bone Name")

    def execute(self, context):
        _TREE_STATE['selected_bone'] = self.bone_name
        context.scene.xpspmx_bone_tree_props.detail_panel_bone = self.bone_name

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class XPSPMX_OT_expand_all(Operator):
    """Expand all bones in tree."""
    bl_idname = "xpspmx_tree.expand_all"
    bl_label = "Expand All Bones"

    def execute(self, context):
        from . import mapping_ui
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config:
            # Add all MMD bone names to expanded set
            for mapping_obj in config.bone_mappings.values():
                if mapping_obj.mmd_name:
                    _TREE_STATE['expanded_bones'].add(mapping_obj.mmd_name)

        # Also add all bones from MMD standard skeleton
        import json
        import os
        preset_path = os.path.join(
            os.path.dirname(mapping.__file__),
            'presets',
            'mmd_standard_skeleton.json'
        )
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for mmd_name in data.get('bones', {}).keys():
                    _TREE_STATE['expanded_bones'].add(mmd_name)
        except:
            pass

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class XPSPMX_OT_collapse_all(Operator):
    """Collapse all bones in tree."""
    bl_idname = "xpspmx_tree.collapse_all"
    bl_label = "Collapse All Bones"

    def execute(self, context):
        _TREE_STATE['expanded_bones'].clear()

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


def _get_mmd_bones_enum(self, context) -> List[Tuple[str, str, str]]:
    """Generate enum items for all MMD bones - callback for EnumProperty (Blender 3.6 compatible)."""
    try:
        mmd_skeleton = get_mmd_standard_skeleton()
        if mmd_skeleton is None:
            return [("", "无法加载 MMD 骨骼", "")]

        items = []
        for bone_name in sorted(mmd_skeleton.keys()):
            # Ensure proper UTF-8 encoding
            try:
                # If it's bytes, decode it
                if isinstance(bone_name, bytes):
                    bone_name = bone_name.decode('utf-8')
                # Ensure it's a proper string
                bone_name = str(bone_name)
            except (UnicodeDecodeError, AttributeError):
                continue

            items.append((bone_name, bone_name, f"选择 {bone_name}"))

        return items if items else [("", "无可用骨骼", "")]
    except Exception as e:
        print(f"[ENUM_CALLBACK] Error in _get_mmd_bones_enum: {e}")
        return [("", f"错误: {str(e)[:30]}", "")]


class XPSPMX_OT_quick_select_bone(Operator):
    """Quick select a bone from the list in the dialog."""
    bl_idname = "xpspmx_mapper.quick_select_bone"
    bl_label = "Select Bone"

    bone_name: StringProperty(name="Bone Name")

    def execute(self, context):
        # Store the selected bone in global state so the dialog can read it
        _TREE_STATE['quick_selected_bone'] = self.bone_name
        return {'RUNNING_MODAL'}  # Keep dialog open


class XPSPMX_OT_save_preset(Operator):
    """Save current mapping configuration as a preset."""
    bl_idname = "xpspmx_mapper.save_preset"
    bl_label = "保存映射预设"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(
        name="预设名称",
        description="输入新预设的名称（不包含 .json）",
        default="custom_preset"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="输入预设名称:")
        layout.prop(self, "preset_name", text="名称")
        layout.label(text="示例: my_custom_v1", icon='INFO')

    def execute(self, context):
        """Save the current mapping configuration to a JSON preset file."""
        from . import mapping_ui
        import json
        import os
        from datetime import datetime

        preset_name = self.preset_name.strip()
        if not preset_name:
            self.report({'ERROR'}, "预设名称不能为空")
            return {'CANCELLED'}

        # Get current config
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config is None:
            self.report({'ERROR'}, "没有映射配置可保存")
            return {'CANCELLED'}

        # Build preset data
        preset_data = {
            "name": preset_name,
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "description": f"Custom mapping preset created by user",
            "bone_mappings": {}
        }

        # Serialize all bone mappings
        for xps_name, mapping_obj in config.bone_mappings.items():
            preset_data["bone_mappings"][xps_name] = {
                "xps_name": mapping_obj.xps_name,
                "mmd_name": mapping_obj.mmd_name,
                "confidence": mapping_obj.confidence,
                "is_unmapped": mapping_obj.is_unmapped,
                "parent_xps": mapping_obj.parent_xps,
                "parent_mmd": mapping_obj.parent_mmd,
                "parent_mmd_expected": mapping_obj.parent_mmd_expected,
                "parent_match": mapping_obj.parent_match,
                "notes": mapping_obj.notes if hasattr(mapping_obj, 'notes') else ""
            }

        # Determine file path
        preset_path = os.path.join(
            os.path.dirname(mapping.__file__),
            'presets',
            f'{preset_name}.json'
        )

        # Check if file already exists
        if os.path.exists(preset_path):
            self.report({'WARNING'}, f"预设 '{preset_name}' 已存在，将被覆盖")

        # Save to file
        try:
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)

            self.report({'INFO'}, f"✓ 预设已保存: {preset_name}.json")
            print(f"[PRESET_SAVE] Saved preset to: {preset_path}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"保存失败: {str(e)[:100]}")
            print(f"[PRESET_SAVE] Error: {e}")
            return {'CANCELLED'}


class XPSPMX_OT_edit_bone_mapping(Operator):
    """Edit a bone mapping - Method B: Complete MMD bone list."""
    bl_idname = "xpspmx_mapper.edit_mapping"
    bl_label = "编辑骨骼映射"
    bl_options = {'REGISTER', 'UNDO'}

    # Store the MMD bone name we're editing
    mmd_bone_name: StringProperty(name="MMD Bone Name")

    # Use StringProperty instead of EnumProperty to avoid Blender's Windows UTF-8 encoding issues
    selected_mmd_bone: StringProperty(
        name="选择 MMD 骨骼",
        description="选择要映射到的 MMD 骨骼",
        default=""
    )

    # Store available bones for validation
    _available_bones: List[str] = []

    def invoke(self, context, event):
        """Open dialog with MMD bone selection."""
        from . import mapping_ui

        # Check if a bone was just quick-selected
        quick_selected = _TREE_STATE.get('quick_selected_bone')
        if quick_selected:
            # User clicked on a bone in the list - update the property and clear
            self.selected_mmd_bone = quick_selected
            _TREE_STATE['quick_selected_bone'] = None
            # Re-invoke the dialog to show the updated selection
            return context.window_manager.invoke_props_dialog(self, width=700)

        # Get the currently selected MMD bone from the detail panel
        scene = context.scene
        props = scene.xpspmx_bone_tree_props
        self.mmd_bone_name = props.detail_panel_bone

        if not self.mmd_bone_name:
            self.report({'ERROR'}, "请先选择一个 MMD 骨骼")
            return {'CANCELLED'}

        # Find the XPS bone that maps to this MMD bone
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config is None:
            self.report({'ERROR'}, "尚未进行骨骼自动映射")
            return {'CANCELLED'}

        # Load available MMD bones and store them (avoiding EnumProperty encoding issues)
        mmd_skeleton = get_mmd_standard_skeleton()
        if mmd_skeleton:
            self._available_bones = sorted(mmd_skeleton.keys())
        else:
            self.report({'ERROR'}, "无法加载 MMD 标准骨骼库")
            return {'CANCELLED'}

        # Find the XPS bone that maps to this MMD bone (如果有的话)
        xps_mapping = None
        for mapping_obj in config.bone_mappings.values():
            if mapping_obj.mmd_name == self.mmd_bone_name:
                xps_mapping = mapping_obj
                break

        # 如果没有映射，则查找未映射的 XPS 骨骼
        if xps_mapping is None:
            # 查找未映射的 XPS 骨骼
            unmapped_bones = [m for m in config.bone_mappings.values() if m.is_unmapped]

            if not unmapped_bones:
                self.report({'WARNING'}, f"'{self.mmd_bone_name}' 目前没有 XPS 骨骼映射，也没有未映射的 XPS 骨骼可用")
                # 允许编辑现有的映射关系
                # 查找任何已映射的骨骼（用于演示）
                mapped_bones = [m for m in config.bone_mappings.values() if not m.is_unmapped]
                if mapped_bones:
                    xps_mapping = mapped_bones[0]
            else:
                # 使用第一个未映射的骨骼
                xps_mapping = unmapped_bones[0]

        if xps_mapping is None:
            # 如果还是找不到，用一个占位符
            self.report({'INFO'}, f"无法为 '{self.mmd_bone_name}' 找到合适的编辑骨骼")
            return {'CANCELLED'}

        # Store the XPS mapping object in global state for later access
        _TREE_STATE['editing_xps_mapping'] = xps_mapping

        # Show dialog with larger width to accommodate bone list
        return context.window_manager.invoke_props_dialog(self, width=700)

    def draw(self, context):
        """Draw the dialog with MMD bone selection."""
        layout = self.layout

        # Information about the bone being edited
        xps_mapping = _TREE_STATE.get('editing_xps_mapping')
        if xps_mapping:
            info_box = layout.box()
            info_row = info_box.row()
            info_row.label(text="📋 编辑映射信息")

            detail_row = info_box.row()
            detail_row.label(text="XPS 骨骼:")
            detail_row.label(text=xps_mapping.xps_name)

            detail_row = info_box.row()
            detail_row.label(text="当前映射到:")
            detail_row.label(text=xps_mapping.mmd_name)

        layout.separator()

        # Input box with instructions
        layout.label(text="👇 输入 MMD 骨骼名称:")
        layout.prop(self, "selected_mmd_bone", text="骨骼名")

        layout.separator()

        # Show matching bones as clickable list
        if self._available_bones:
            search_term = self.selected_mmd_bone.lower() if self.selected_mmd_bone else ""
            filtered_bones = [
                b for b in self._available_bones
                if not search_term or search_term in b.lower()
            ]

            if search_term and filtered_bones:
                # Show matching bones with select buttons
                ref_box = layout.box()
                ref_box.label(text=f"📝 匹配的骨骼 ({len(filtered_bones)} 个) - 点击选择:")

                # Display up to 20 matching bones as selectable buttons
                for bone in filtered_bones[:20]:
                    row = ref_box.row()
                    # Button to select this bone
                    row.operator(
                        "xpspmx_mapper.quick_select_bone",
                        text=bone,
                        emboss=True
                    ).bone_name = bone

                if len(filtered_bones) > 20:
                    ref_box.label(text=f"... 还有 {len(filtered_bones) - 20} 个")
            elif not search_term:
                # Show all bones when search is empty
                ref_box = layout.box()
                ref_box.label(text=f"📚 所有可用骨骼 ({len(self._available_bones)} 个) - 搜索或点击:")

                # Display first 10 bones as preview
                for bone in self._available_bones[:10]:
                    row = ref_box.row()
                    row.operator(
                        "xpspmx_mapper.quick_select_bone",
                        text=bone,
                        emboss=False
                    ).bone_name = bone

                if len(self._available_bones) > 10:
                    ref_box.label(text=f"... 共 {len(self._available_bones)} 个骨骼（输入搜索）")

        layout.separator()

        # Show validation info
        if xps_mapping and self.selected_mmd_bone:
            if self.selected_mmd_bone in self._available_bones:
                if self.selected_mmd_bone != xps_mapping.mmd_name:
                    info_box = layout.box()
                    info_box.label(text="✓ 确认更改:")
                    info_row = info_box.row()
                    info_row.label(text=f"  {xps_mapping.xps_name}")
                    info_row.label(text="→")
                    info_row.label(text=f"  {self.selected_mmd_bone}")
                else:
                    layout.label(text="⚠️ 新映射与当前映射相同")
            else:
                layout.label(text=f"⚠️ '{self.selected_mmd_bone}' 不是有效的 MMD 骨骼")

    def execute(self, context):
        """Apply the mapping change."""
        selected_bone = self.selected_mmd_bone.strip() if self.selected_mmd_bone else ""

        if not selected_bone:
            self.report({'ERROR'}, "请输入或选择一个 MMD 骨骼")
            return {'CANCELLED'}

        from . import mapping_ui

        xps_mapping = _TREE_STATE.get('editing_xps_mapping')
        if xps_mapping is None:
            self.report({'ERROR'}, "未找到要编辑的 XPS 骨骼映射")
            return {'CANCELLED'}

        # Validate that the selected bone exists in MMD skeleton
        mmd_skeleton = get_mmd_standard_skeleton()
        if not mmd_skeleton or selected_bone not in mmd_skeleton:
            self.report({'ERROR'}, f"'{selected_bone}' 不是有效的 MMD 骨骼")
            return {'CANCELLED'}

        # Skip if selection hasn't changed
        if selected_bone == xps_mapping.mmd_name:
            self.report({'INFO'}, "映射未改变")
            return {'FINISHED'}

        # Check if new MMD bone is already mapped from another XPS bone
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        warning_msg = ""
        if config:
            for other_mapping in config.bone_mappings.values():
                if (other_mapping.xps_name != xps_mapping.xps_name and
                    other_mapping.mmd_name == selected_bone):
                    warning_msg = f"⚠️ '{selected_bone}' 已从 '{other_mapping.xps_name}' 映射，将被覆盖"
                    # Unmap the previous bone
                    other_mapping.mmd_name = ""
                    other_mapping.is_unmapped = True
                    break

        # Update the mapping
        xps_mapping.mmd_name = selected_bone
        xps_mapping.is_unmapped = False

        # Validate parent relationship after mapping change
        if mmd_skeleton and selected_bone in mmd_skeleton:
            new_bone_def = mmd_skeleton[selected_bone]
            expected_parent = new_bone_def.get('parent_mmd')
            xps_mapping.parent_mmd_expected = expected_parent

            # Get current parent in XPS
            if xps_mapping.parent_xps and config:
                # Find what the XPS parent maps to
                for m in config.bone_mappings.values():
                    if m.xps_name == xps_mapping.parent_xps:
                        xps_mapping.parent_mmd = m.mmd_name
                        xps_mapping.parent_match = (m.mmd_name == expected_parent)
                        break

        # Clear editing state
        _TREE_STATE['editing_xps_mapping'] = None

        # Report result
        msg = f"✓ 已更新: {xps_mapping.xps_name} → {selected_bone}"
        if warning_msg:
            msg += f" | {warning_msg}"

        self.report({'INFO'}, msg)

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class XPSPMX_PT_mmd_bone_tree(Panel):
    """Panel: MMD Bone Tree Visualization."""
    bl_label = "🌳 MMD 骨骼树形结构"
    bl_idname = "XPSPMX_PT_mmd_bone_tree"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.xpspmx_bone_tree_props

        # Check if config exists
        from . import mapping_ui
        config = mapping_ui._GLOBAL_CONFIG.get('config')

        if config is None:
            layout.label(text="⚠️ 尚未自动映射骨骼")
            layout.label(text="请点击下方按钮运行自动映射:", text_ctxt="")

            # 添加运行自动映射的按钮
            row = layout.row(align=True)
            row.scale_y = 1.5
            row.operator("xpspmx_mapper.auto_map_bones", text="🔄 Auto Map Bones")

            return

        # Load MMD standard skeleton
        mmd_skeleton = get_mmd_standard_skeleton()
        if mmd_skeleton is None:
            layout.label(text="⚠️ 无法加载 MMD 标准骨骼库")
            return

        # ─────────────────────────────────────────
        # 搜索和过滤
        # ─────────────────────────────────────────
        layout.label(text="🔍 搜索和过滤:")
        layout.prop(props, 'bone_tree_search', text="搜索")

        row = layout.row(align=True)
        row.prop(props, 'show_only_errors', text="仅错误")
        row.prop(props, 'show_only_deform', text="仅变形骨")
        row.prop(props, 'auto_expand', text="自动展开")

        # 显示模式选择
        layout.label(text="显示模式:")
        row = layout.row(align=True)
        row.prop_enum(props, 'display_mode', value='complete', text='完整树')
        row.prop_enum(props, 'display_mode', value='compact', text='简洁')
        row.prop_enum(props, 'display_mode', value='table', text='表格')

        # 展开/折叠控制
        row = layout.row(align=True)
        row.operator("xpspmx_tree.expand_all", text="展开全部")
        row.operator("xpspmx_tree.collapse_all", text="折叠全部")

        layout.separator()

        # ─────────────────────────────────────────
        # 主要显示区域
        # ─────────────────────────────────────────
        search_term = props.bone_tree_search.lower()

        # Create scrollable column
        scroll_col = layout.column(align=True)

        if props.display_mode == 'complete':
            self._draw_complete_tree(scroll_col, mmd_skeleton, config, search_term, props)
        elif props.display_mode == 'compact':
            self._draw_compact_tree(scroll_col, mmd_skeleton, config, search_term, props)
        elif props.display_mode == 'table':
            self._draw_table_view(scroll_col, mmd_skeleton, config, search_term, props)

        layout.separator()

        # ─────────────────────────────────────────
        # 统计摘要
        # ─────────────────────────────────────────
        self._draw_statistics(layout, mmd_skeleton, config)

        layout.separator()

        # ─────────────────────────────────────────
        # 转换流程
        # ─────────────────────────────────────────
        convert_box = layout.box()
        convert_box.label(text="▶ 转换流程")

        row = convert_box.row(align=True)
        row.scale_y = 1.3
        row.operator("xpspmx_pipeline.stage_0_apply_mapping", text="🔄 Stage 0: 应用映射")

        row = convert_box.row(align=True)
        row.scale_y = 1.3
        row.operator("xpspmx_pipeline.stage_1_rebuild_skeleton", text="🛠 Stage 1: 重建骨架")

        row = convert_box.row(align=True)
        row.scale_y = 1.3
        row.operator("xpspmx_pipeline.stage_2_apply_apose", text="🧍 Stage 2: 应用 A-Pose")

        row = convert_box.row(align=True)
        row.scale_y = 1.3
        row.operator("xpspmx_pipeline.stage_3_apply_weight_rules", text="⚖ Stage 3: 应用权重规则")

        row = convert_box.row(align=True)
        row.scale_y = 1.3
        row.operator("xpspmx_pipeline.stage_4_setup_constraints", text="🔗 Stage 4: 设置约束")

        convert_box.label(text="⏳ Stage 5: 导出 PMX（开发中...）", icon='INFO')

    def _draw_complete_tree(self, layout, mmd_skeleton: Dict, config, search_term: str, props):
        """Draw complete tree with all details."""
        # Find root bones (parent_mmd is null)
        root_bones = [
            (name, bone_def)
            for name, bone_def in mmd_skeleton.items()
            if bone_def.get('parent_mmd') is None
        ]

        for mmd_name, bone_def in sorted(root_bones):
            self._draw_bone_row(
                layout, mmd_skeleton, config, mmd_name, bone_def,
                depth=0, search_term=search_term, props=props
            )

    def _draw_compact_tree(self, layout, mmd_skeleton: Dict, config, search_term: str, props):
        """Draw compact tree with minimal details."""
        root_bones = [
            (name, bone_def)
            for name, bone_def in mmd_skeleton.items()
            if bone_def.get('parent_mmd') is None
        ]

        for mmd_name, bone_def in sorted(root_bones):
            self._draw_compact_bone_row(
                layout, mmd_skeleton, config, mmd_name, bone_def,
                depth=0, search_term=search_term, props=props
            )

    def _draw_table_view(self, layout, mmd_skeleton: Dict, config, search_term: str, props):
        """Draw table view of all bones."""

        # Sort bones by hierarchy level
        sorted_bones = sorted(mmd_skeleton.items())

        # 计算显示的骨骼数
        visible_bones = []
        for mmd_name, bone_def in sorted_bones:
            show_errors = props.show_only_errors if props else False
            show_deform = props.show_only_deform if props else False
            if should_show_bone(bone_def, search_term, show_errors, show_deform):
                visible_bones.append((mmd_name, bone_def))

        if not visible_bones:
            layout.label(text="⚠️ 没有符合条件的骨骼")
            return

        box = layout.box()

        # Table header
        header_row = box.row(align=True)
        header_row.label(text="MMD 骨骼")
        header_row.label(text="XPS 映射")
        header_row.label(text="权重")
        header_row.label(text="变形")

        # Display visible bones
        for mmd_name, bone_def in visible_bones:
            try:
                row = box.row(align=True)

                # MMD bone name - 可点击的按钮
                bone_button = row.operator(
                    "xpspmx_tree.select_bone",
                    text=f"【{mmd_name}】"
                )
                bone_button.bone_name = mmd_name

                # XPS mapping
                xps_mapping = self._get_xps_mapping_for_mmd(mmd_name, config)
                if xps_mapping:
                    row.label(text=f"✓ {xps_mapping}")
                else:
                    row.label(text="✗ 未映射")

                # Weight
                weight_pct = self._get_weight_percentage(mmd_name, config)
                row.label(text=f"{weight_pct:.1f}%")

                # Is deform
                is_deform = bone_def.get('is_deform', False)
                row.label(text="✓" if is_deform else "✗")
            except:
                pass

    def _draw_bone_row(self, layout, mmd_skeleton: Dict, config, mmd_name: str, bone_def: Dict,
                       depth: int = 0, search_term: str = "", props=None):
        """Draw a single bone row with children - depth limited."""

        # 防止递归过深 (Blender UI 限制)
        MAX_DEPTH = 15
        if depth > MAX_DEPTH:
            return

        if not should_show_bone(bone_def, search_term, props.show_only_errors if props else False,
                               props.show_only_deform if props else False):
            return

        # 获取子骨骼
        children = [
            (name, child_def)
            for name, child_def in mmd_skeleton.items()
            if child_def.get('parent_mmd') == mmd_name
        ]

        is_expanded = (mmd_name in _TREE_STATE['expanded_bones'] or
                      (props and props.auto_expand))
        has_children = len(children) > 0

        # 缩进
        indent = "  " * depth

        # 单行显示
        row = layout.row(align=True)

        # 展开/折叠按钮
        if has_children:
            expand_icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
            row.operator(
                "xpspmx_tree.toggle_expand",
                text="",
                icon=expand_icon,
                emboss=False
            ).bone_name = mmd_name
        else:
            row.label(text=" ")

        # 骨骼名称 (带缩进) - 可点击的按钮
        bone_button = row.operator(
            "xpspmx_tree.select_bone",
            text=f"{indent}【{mmd_name}】"
        )
        bone_button.bone_name = mmd_name

        # 权重星标
        try:
            weight_pct = self._get_weight_percentage(mmd_name, config)
            weight_stars = format_weight_stars(weight_pct)
            row.label(text=weight_stars)
        except:
            row.label(text="")

        # XPS 映射状态
        try:
            xps_mapping = self._get_xps_mapping_for_mmd(mmd_name, config)
            if xps_mapping:
                row.label(text=f"✓ {xps_mapping}")
            else:
                row.label(text="✗ 未映射")
        except:
            row.label(text="")

        # 递归绘制子骨骼 (限制深度)
        if is_expanded and has_children and depth < MAX_DEPTH:
            for child_name, child_def in sorted(children):
                self._draw_bone_row(
                    layout, mmd_skeleton, config, child_name, child_def,
                    depth=depth + 1, search_term=search_term, props=props
                )

    def _draw_compact_bone_row(self, layout, mmd_skeleton: Dict, config, mmd_name: str, bone_def: Dict,
                              depth: int = 0, search_term: str = "", props=None):
        """Draw a compact bone row - depth limited."""

        # 防止递归过深
        MAX_DEPTH = 15
        if depth > MAX_DEPTH:
            return

        if not should_show_bone(bone_def, search_term, props.show_only_errors if props else False,
                               props.show_only_deform if props else False):
            return

        children = [
            (name, child_def)
            for name, child_def in mmd_skeleton.items()
            if child_def.get('parent_mmd') == mmd_name
        ]

        is_expanded = mmd_name in _TREE_STATE['expanded_bones'] or (props and props.auto_expand)
        has_children = len(children) > 0

        indent = "  " * depth

        row = layout.row(align=True)

        # 展开符号
        if has_children:
            expand_icon = '▼' if is_expanded else '►'
            row.operator(
                "xpspmx_tree.toggle_expand",
                text=expand_icon,
                emboss=False
            ).bone_name = mmd_name
        else:
            row.label(text=" ")

        # 骨骼名称 - 可点击的按钮
        bone_button = row.operator(
            "xpspmx_tree.select_bone",
            text=f"{indent}【{mmd_name}】",
            emboss=False
        )
        bone_button.bone_name = mmd_name

        # 状态图标
        xps_mapping = self._get_xps_mapping_for_mmd(mmd_name, config)
        if xps_mapping:
            row.label(text="✓")
        else:
            row.label(text="✗")

        # 递归绘制子骨骼 (深度限制)
        if is_expanded and has_children and depth < MAX_DEPTH:
            for child_name, child_def in sorted(children):
                self._draw_compact_bone_row(
                    layout, mmd_skeleton, config, child_name, child_def,
                    depth=depth + 1, search_term=search_term, props=props
                )

    def _draw_statistics(self, layout, mmd_skeleton: Dict, config):
        """Draw statistics summary."""
        box = layout.box()
        row = box.row()
        row.label(text="📊 统计摘要")

        # XPS 骨骼统计
        xps_total = len(config.bone_mappings)
        xps_mapped = len([m for m in config.bone_mappings.values() if not m.is_unmapped])
        xps_unmapped = xps_total - xps_mapped

        row = box.row()
        row.label(text=f"XPS 总骨骼: {xps_total} 个")
        row.label(text=f"已映射: {xps_mapped} 个")
        row.label(text=f"未映射: {xps_unmapped} 个")

        # XPS 映射覆盖率
        percentage = (xps_mapped / xps_total * 100) if xps_total > 0 else 0
        row = box.row()
        row.label(text=f"XPS 映射覆盖: {percentage:.1f}%")

        # MMD 骨骼统计
        mmd_total = len(mmd_skeleton)
        mmd_mapped = len([name for name, _ in mmd_skeleton.items()
                         if any(m.mmd_name == name for m in config.bone_mappings.values())])

        row = box.row()
        row.label(text=f"MMD 总骨骼: {mmd_total} 个")
        row.label(text=f"已使用: {mmd_mapped} 个")

    def _get_xps_mapping_for_mmd(self, mmd_name: str, config) -> Optional[str]:
        """Get XPS bone name that maps to this MMD bone."""
        for mapping_obj in config.bone_mappings.values():
            if mapping_obj.mmd_name == mmd_name:
                return mapping_obj.xps_name
        return None

    def _get_weight_percentage(self, mmd_name: str, config) -> float:
        """Get weight percentage for this MMD bone."""
        for mapping_obj in config.bone_mappings.values():
            if mapping_obj.mmd_name == mmd_name:
                return mapping_obj.vertex_group_count * 0.1  # Mock calculation
        return 0.0

    def _check_parent_valid(self, mmd_name: str, config, mmd_skeleton: Dict) -> bool:
        """Check if parent relationship is valid."""
        # Will be enhanced with proper validation
        return True


class XPSPMX_PT_unmapped_bones_panel(Panel):
    """Panel showing unmapped bones and their vertex information."""
    bl_label = "⚠️ 未映射骨骼检查"
    bl_idname = "XPSPMX_PT_unmapped_bones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        from . import mapping_ui
        config = mapping_ui._GLOBAL_CONFIG.get('config')

        if config is None:
            layout.label(text="⚠️ 请先运行 'Auto Map Bones'")
            return

        # 获取问题骨骼：真正未映射的 + 映射到不合理位置的
        # (1) 真正未映射的
        unmapped_bones = [m for m in config.bone_mappings.values() if m.is_unmapped]

        # (2) 映射到不合理位置的（如低置信度、或父级不匹配）
        problematic_bones = [
            m for m in config.bone_mappings.values()
            if not m.is_unmapped and (
                m.confidence < 0.8 or  # 置信度低
                not m.parent_match or  # 父级不匹配
                (m.vertex_group_count > 0 and m.confidence < 1.0)  # 有权重但置信度不是100%
            )
        ]

        problem_bones = unmapped_bones + problematic_bones

        if not problem_bones:
            layout.label(text="✅ 所有骨骼映射质量都很好!")
            return

        # 统计信息
        box = layout.box()
        row = box.row()
        row.label(text=f"问题骨骼: {len(problem_bones)} 个")
        if unmapped_bones:
            row.label(text=f"(未映射: {len(unmapped_bones)} 个)")

        # 计算问题骨骼的总顶点数
        total_vertex_count = sum(m.vertex_group_count for m in problem_bones)
        row = box.row()
        row.label(text=f"涉及顶点: {total_vertex_count} 个")

        # 按顶点数排序，优先处理权重较大的骨骼
        sorted_bones = sorted(problem_bones,
                            key=lambda x: x.vertex_group_count,
                            reverse=True)

        # 显示问题骨骼列表
        layout.label(text="📋 需要检查的骨骼 (按顶点数排序):")

        for i, mapping in enumerate(sorted_bones[:25]):  # 显示前 25 个
            box = layout.box()
            row = box.row(align=True)

            # 问题标记
            if mapping.is_unmapped:
                row.label(text="🔴")
            elif mapping.confidence < 0.8:
                row.label(text="🟡")
            else:
                row.label(text="⚠️")

            # XPS 骨骼名
            row.label(text=f"{i+1}. {mapping.xps_name}")

            # 顶点数
            vertex_count = mapping.vertex_group_count
            if vertex_count > 0:
                row.label(text=f"({vertex_count}v)")

            # 显示详细信息的第二行
            sub_row = box.row()
            if mapping.is_unmapped:
                sub_row.label(text="❌ 未映射")
            else:
                info_text = f"✓ {mapping.mmd_name}"
                if mapping.confidence < 1.0:
                    info_text += f" (置信度: {mapping.confidence:.0%})"
                if not mapping.parent_match:
                    info_text += " ⚠️ 父级不匹配"
                sub_row.label(text=info_text)

        if len(sorted_bones) > 25:
            layout.label(text=f"... 还有 {len(sorted_bones) - 25} 个未显示")

        # 快速操作按钮
        layout.separator()
        layout.label(text="💡 优先处理:")
        layout.label(text="🔴 红色 = 未映射")
        layout.label(text="🟡 黄色 = 置信度低")
        layout.label(text="⚠️ 灰色 = 其他问题")


class XPSPMX_PT_bone_detail_panel(Panel):
    """Right side panel showing bone details."""
    bl_label = "骨骼详情"
    bl_idname = "XPSPMX_PT_bone_detail"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.xpspmx_bone_tree_props

        selected_bone = props.detail_panel_bone
        if not selected_bone:
            layout.label(text="点击骨骼查看详情")
            return

        # Load MMD skeleton
        mmd_skeleton = get_mmd_standard_skeleton()
        if mmd_skeleton is None:
            return

        bone_def = mmd_skeleton.get(selected_bone)
        if bone_def is None:
            layout.label(text=f"骨骼 '{selected_bone}' 未找到")
            return

        from . import mapping_ui
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config is None:
            return

        # 基本属性
        box = layout.box()
        box.label(text="📊 基本属性")
        box.label(text=f"名称: 【{selected_bone}】")
        box.label(text=f"类型: {bone_def.get('bone_type', 'unknown')}")
        box.label(text=f"描述: {bone_def.get('notes', 'N/A')}")

        # XPS 映射
        box = layout.box()
        box.label(text="🔗 XPS 映射信息")
        xps_mapping = self._get_xps_mapping_for_mmd(selected_bone, config)
        if xps_mapping:
            box.label(text=f"XPS: {xps_mapping} ✓")
        else:
            box.label(text="XPS: [无] ❌")

        # 层级关系
        box = layout.box()
        box.label(text="👨‍👩‍👧 层级关系")
        parent = bone_def.get('parent_mmd')
        if parent:
            box.label(text=f"父级: 【{parent}】")
        else:
            box.label(text="父级: [无] (根骨骼)")

        # 权重信息
        box = layout.box()
        box.label(text="⚖️ 权重信息")
        weight_pct = self._get_weight_percentage(selected_bone, config)
        box.label(text=f"权重: {weight_pct:.1f}%")

        # 操作按钮
        box = layout.box()
        box.label(text="🔧 操作")
        row = box.row(align=True)
        row.operator("xpspmx_mapper.edit_mapping", text="✎ 编辑映射")
        row.operator("xpspmx_mapper.save_preset", text="💾 保存预设")

    def _get_xps_mapping_for_mmd(self, mmd_name: str, config) -> Optional[str]:
        """Get XPS bone name that maps to this MMD bone."""
        for mapping_obj in config.bone_mappings.values():
            if mapping_obj.mmd_name == mmd_name:
                return mapping_obj.xps_name
        return None

    def _get_weight_percentage(self, mmd_name: str, config) -> float:
        """Get weight percentage for this MMD bone."""
        for mapping_obj in config.bone_mappings.values():
            if mapping_obj.mmd_name == mmd_name:
                return mapping_obj.vertex_group_count * 0.1
        return 0.0


# Registration
def register():
    """Register all classes."""
    bpy.utils.register_class(XPSPMXBoneTreeProperties)
    bpy.utils.register_class(XPSPMX_OT_toggle_bone_expand)
    bpy.utils.register_class(XPSPMX_OT_expand_all)
    bpy.utils.register_class(XPSPMX_OT_collapse_all)
    bpy.utils.register_class(XPSPMX_OT_select_bone_detail)
    bpy.utils.register_class(XPSPMX_OT_quick_select_bone)
    bpy.utils.register_class(XPSPMX_OT_save_preset)
    bpy.utils.register_class(XPSPMX_OT_edit_bone_mapping)
    bpy.utils.register_class(XPSPMX_PT_mmd_bone_tree)
    bpy.utils.register_class(XPSPMX_PT_unmapped_bones_panel)
    bpy.utils.register_class(XPSPMX_PT_bone_detail_panel)

    # Add properties to scene
    bpy.types.Scene.xpspmx_bone_tree_props = bpy.props.PointerProperty(
        type=XPSPMXBoneTreeProperties
    )


def unregister():
    """Unregister all classes."""
    if hasattr(bpy.types.Scene, 'xpspmx_bone_tree_props'):
        del bpy.types.Scene.xpspmx_bone_tree_props

    bpy.utils.unregister_class(XPSPMX_PT_bone_detail_panel)
    bpy.utils.unregister_class(XPSPMX_PT_unmapped_bones_panel)
    bpy.utils.unregister_class(XPSPMX_PT_mmd_bone_tree)
    bpy.utils.unregister_class(XPSPMX_OT_edit_bone_mapping)
    bpy.utils.unregister_class(XPSPMX_OT_save_preset)
    bpy.utils.unregister_class(XPSPMX_OT_quick_select_bone)
    bpy.utils.unregister_class(XPSPMX_OT_select_bone_detail)
    bpy.utils.unregister_class(XPSPMX_OT_collapse_all)
    bpy.utils.unregister_class(XPSPMX_OT_expand_all)
    bpy.utils.unregister_class(XPSPMX_OT_toggle_bone_expand)
    bpy.utils.unregister_class(XPSPMXBoneTreeProperties)
