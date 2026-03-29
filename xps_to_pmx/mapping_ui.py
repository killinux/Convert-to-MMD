"""4-panel UI system for flexible bone and weight mapping editor.

Panels:
1. AUTO DETECTION - Auto-detect skeleton type and map bones
2. MAPPING EDITOR - Manually edit bone mappings
3. WEIGHT RULES - Configure weight transfer rules
4. VALIDATION & PREVIEW - Validate configuration and preview results
"""

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, PointerProperty
from typing import Optional

from . import mapping

# Global storage for mapping configuration (since Scene properties are read-only)
_GLOBAL_CONFIG = {
    'config': None,
    'current_armature': None
}


class XPSToPMXMapperProperties(PropertyGroup):
    """Property group for storing mapping editor state."""

    # Auto-detection
    auto_detect_result: StringProperty(
        name="Auto Detect Result",
        description="Result of auto-detection",
        default=""
    )

    # Mapping editor state
    selected_mapping_tab: StringProperty(
        name="Selected Tab",
        description="Currently selected mapping editor tab (spine/arms/legs/etc)",
        default="spine"
    )

    mapping_search: StringProperty(
        name="Search",
        description="Search bone mappings",
        default=""
    )

    # Weight rules state
    selected_rule_category: StringProperty(
        name="Selected Rule Category",
        description="Selected weight rule category",
        default="fk_to_d"
    )

    # Config file path
    config_file_path: StringProperty(
        name="Config Path",
        description="Path to mapping configuration JSON",
        default="",
        subtype='FILE_PATH'
    )


class XPSPMX_OT_auto_detect_skeleton(Operator):
    """Automatically detect skeleton type and map bones."""
    bl_idname = "xpspmx_mapper.auto_detect_skeleton"
    bl_label = "Auto Detect Skeleton Type"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an armature")
            return {'CANCELLED'}

        # Detect skeleton type
        skeleton_type = mapping.detection.detect_skeleton_type(armature)
        self.report({'INFO'}, f"Detected skeleton type: {skeleton_type}")

        context.scene.xpspmx_mapper_props.auto_detect_result = f"Skeleton type: {skeleton_type}"
        return {'FINISHED'}


class XPSPMX_OT_auto_map_bones(Operator):
    """Automatically map all bones."""
    bl_idname = "xpspmx_mapper.auto_map_bones"
    bl_label = "Auto Map Bones"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an armature")
            return {'CANCELLED'}

        # Load reference config from preset (ensures fresh load)
        try:
            import os
            preset_path = os.path.join(os.path.dirname(mapping.__file__), 'presets', 'standard_xps.json')
            reference_config = mapping.data_structures.MappingConfiguration.load_from_file(preset_path)
        except Exception as e:
            self.report({'WARNING'}, f"Could not load preset: {e}, using auto-detection only")
            reference_config = None

        # Auto-detect and create configuration with the fresh preset
        config = mapping.detection.auto_map_bones(armature, reference_config=reference_config)

        # Store configuration in global storage
        _GLOBAL_CONFIG['config'] = config
        _GLOBAL_CONFIG['current_armature'] = armature

        mapped_count = len(config.bone_mappings)
        self.report({'INFO'}, f"Mapped {mapped_count} bones")

        return {'FINISHED'}


class XPSPMX_OT_save_mapping_config(Operator):
    """Save mapping configuration to JSON file."""
    bl_idname = "xpspmx_mapper.save_config"
    bl_label = "Save Configuration"

    filepath: StringProperty(
        name="File Path",
        description="Path to save configuration",
        subtype='FILE_PATH'
    )

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def execute(self, context):
        config = _GLOBAL_CONFIG['config']
        if config is None:
            self.report({'ERROR'}, "No configuration to save")
            return {'CANCELLED'}

        try:
            config.save_to_file(self.filepath)
            self.report({'INFO'}, f"Configuration saved to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error saving configuration: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class XPSPMX_OT_load_mapping_config(Operator):
    """Load mapping configuration from JSON file."""
    bl_idname = "xpspmx_mapper.load_config"
    bl_label = "Load Configuration"

    filepath: StringProperty(
        name="File Path",
        description="Path to load configuration",
        subtype='FILE_PATH'
    )

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def execute(self, context):
        try:
            config = mapping.data_structures.MappingConfiguration.load_from_file(self.filepath)
            _GLOBAL_CONFIG['config'] = config
            self.report({'INFO'}, f"Configuration loaded from {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error loading configuration: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class XPSPMX_PT_auto_detection(Panel):
    """Panel 1: Auto-detection controls."""
    bl_label = "① AUTO DETECTION"
    bl_idname = "XPSPMX_PT_auto_detection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.xpspmx_mapper_props

        # Show plugin version and timestamp
        try:
            import xps_to_pmx
            bl_info = xps_to_pmx.bl_info
            version = bl_info.get('version', (0, 0, 0))
            last_updated = bl_info.get('last_updated', 'Unknown')
            version_str = f"{version[0]}.{version[1]}.{version[2]}"

            layout.label(text=f"Plugin v{version_str}", icon='PLUGIN')
            layout.label(text=f"Updated: {last_updated}")
            layout.separator()
        except Exception as e:
            layout.label(text="Version: Error", icon='ERROR')

        # Auto detection buttons
        layout.label(text="Auto Detection:")
        layout.operator("xpspmx_mapper.auto_detect_skeleton", icon='ZOOM_IN')
        layout.operator("xpspmx_mapper.auto_map_bones", icon='SHAPEKEY_DATA')

        # Show result
        if props.auto_detect_result:
            layout.label(text="Detection Result:")
            layout.label(text=props.auto_detect_result)

        # Show mapping status
        config = _GLOBAL_CONFIG['config']
        if config is not None:
            layout.label(text=f"Mapped {len(config.bone_mappings)} bones")


class XPSPMX_PT_mapping_editor(Panel):
    """Panel 2: Manual mapping editor."""
    bl_label = "② MAPPING EDITOR"
    bl_idname = "XPSPMX_PT_mapping_editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.xpspmx_mapper_props

        config = _GLOBAL_CONFIG['config']
        if config is None:
            layout.label(text="Run 'Auto Map Bones' first", icon='ERROR')
            return

        # Validate parent relationships
        parent_validation = mapping.detection.validate_parent_relationships(config)

        # Search
        layout.label(text="Filter by Name:")
        layout.prop(props, 'mapping_search', text="")

        search_term = props.mapping_search.lower()

        # Group mappings by bone type
        groups = {
            'spine': [],
            'arm': [],
            'leg': [],
            'hand': [],
            'finger': [],
            'eye': [],
            'other': []
        }

        for xps_name, mapping_obj in config.bone_mappings.items():
            # Filter by search term
            if search_term and search_term not in xps_name.lower() and search_term not in mapping_obj.mmd_name.lower():
                continue

            bone_type = mapping_obj.bone_type.lower()
            if bone_type in groups:
                groups[bone_type].append((xps_name, mapping_obj))
            else:
                groups['other'].append((xps_name, mapping_obj))

        # Display grouped mappings
        layout.label(text=f"Total Mapped: {len(config.bone_mappings)} bones")
        layout.separator()

        # Show each group
        group_names = {
            'spine': '🧬 Spine Bones',
            'arm': '💪 Arm Bones',
            'leg': '🦵 Leg Bones',
            'hand': '✋ Hand Bones',
            'finger': '👆 Finger Bones',
            'eye': '👁️ Eye Bones',
            'other': '🔷 Other Bones'
        }

        for group_key, group_label in group_names.items():
            bones = groups[group_key]
            if not bones:
                continue

            # Group header with collapsible arrow
            box = layout.box()
            row = box.row(align=True)
            row.label(text=f"{group_label} ({len(bones)})", icon='TRIA_DOWN')

            # Display bones in this group
            for xps_name, mapping_obj in bones:
                row = box.row(align=False)

                # Confidence color indicator
                confidence = mapping_obj.confidence
                if confidence >= 0.95:
                    icon = 'CHECKMARK'
                    confidence_text = f"{confidence:.0%} ✓"
                elif confidence >= 0.80:
                    icon = 'INFO'
                    confidence_text = f"{confidence:.0%} ⚠"
                else:
                    icon = 'ERROR'
                    confidence_text = f"{confidence:.0%} ❌"

                # Left: XPS name
                row.label(text=xps_name, icon='BONE_DATA')

                # Middle: Arrow and MMD name
                row.label(text="→", icon='NONE')
                row.label(text=mapping_obj.mmd_name)

                # Right: Confidence score and parent validation
                row.label(text=confidence_text, icon=icon)

                # Parent validation indicator
                validation_result = parent_validation.get(xps_name, {})
                if validation_result.get('is_valid'):
                    row.label(text="✓", icon='CHECKMARK')
                else:
                    row.label(text="⚠", icon='ERROR')

                # Show parent info tooltip on hover
                if mapping_obj.parent_xps:
                    row.label(text=f"(parent: {mapping_obj.parent_xps})")
                else:
                    row.label(text="(root)")


class XPSPMX_PT_bone_detection(Panel):
    """Panel: Detect missing MMD standard bones.

    Shows which of the 49 MMD standard bones are missing from the current
    XPS model. Allows user to confirm which ones should be created.
    """
    bl_label = "🔍 BONE DETECTION"
    bl_idname = "XPSPMX_PT_bone_detection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = context.active_object

        # Check if we have an armature selected
        if not armature or armature.type != 'ARMATURE':
            layout.label(text="Please select an armature", icon='ERROR')
            return

        # Detect missing bones
        from . import mapping
        summary = mapping.detection.build_missing_bones_summary(armature)

        if not summary:
            layout.label(text="Error detecting bones", icon='ERROR')
            return

        # Show summary
        total_missing = summary['total_missing']
        total_mmd = summary['total_mmd_bones']
        missing_critical = summary['missing_critical']

        layout.label(text=f"MMD Standard Bones: {total_mmd - total_missing}/{total_mmd}", icon='BONE_DATA')
        layout.label(text=f"Missing: {total_missing} bones", icon='ERROR' if total_missing > 0 else 'CHECKMARK')

        if missing_critical:
            layout.label(text=f"Critical Missing: {len(missing_critical)}", icon='ALERT')
            row = layout.row()
            row.label(text="⚠️ These bones are needed for proper reconstruction:")
            for bone_name in missing_critical[:5]:
                row = layout.row()
                row.label(text=f"  • {bone_name}", icon='BONE_DATA')
            if len(missing_critical) > 5:
                row = layout.row()
                row.label(text=f"  ... and {len(missing_critical) - 5} more")

        # Show missing bones by category
        layout.separator()
        layout.label(text="Missing by Category:")

        missing_by_type = summary['missing_by_type']
        for bone_type, bones in sorted(missing_by_type.items()):
            box = layout.box()
            row = box.row()
            row.label(text=f"{bone_type.upper()} ({len(bones)})", icon='TRIA_DOWN')

            for bone_name in bones:
                detail = summary['missing_details'].get(bone_name, {})
                row = box.row()
                row.label(text=f"  • {bone_name}", icon='BONE_DATA')
                if detail.get('parent_mmd'):
                    row.label(text=f"(parent: {detail['parent_mmd']})", icon='NONE')

        # Confirmation button
        layout.separator()
        layout.operator("xpspmx_mapper.confirm_missing_bones",
                       text=f"Confirm & Create Missing Bones ({total_missing})",
                       icon='CHECKMARK')


class XPSPMX_OT_confirm_missing_bones(Operator):
    """Confirm detection and prepare to create missing bones in Stage 1."""
    bl_idname = "xpspmx_mapper.confirm_missing_bones"
    bl_label = "Confirm Missing Bones"

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an armature")
            return {'CANCELLED'}

        from . import mapping

        # Detect missing bones
        missing_details = mapping.detection.detect_missing_mmd_bones(armature)
        missing_bones = {name: details for name, details in missing_details.items() if details['is_missing']}

        # Store in global config for Stage 1
        if _GLOBAL_CONFIG['config'] is None:
            self.report({'ERROR'}, "No mapping configuration. Run Auto Map Bones first.")
            return {'CANCELLED'}

        config = _GLOBAL_CONFIG['config']
        config.missing_mmd_bones = missing_bones

        total_missing = len(missing_bones)
        self.report({'INFO'}, f"Confirmed: {total_missing} bones will be created in Stage 1")

        return {'FINISHED'}


class XPSPMX_PT_weight_rules(Panel):
    """Panel 3: Weight transfer rules configuration."""
    bl_label = "③ WEIGHT RULES"
    bl_idname = "XPSPMX_PT_weight_rules"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        config = _GLOBAL_CONFIG['config']
        if config is None:
            layout.label(text="Run 'Auto Map Bones' first", icon='ERROR')
            return

        # Rule categories
        layout.label(text="Rule Categories:")
        row = layout.row()
        row.operator("xpspmx_mapper.add_fk_to_d_rule", text="FK→D")
        row.operator("xpspmx_mapper.add_twist_rule", text="Twist")
        row.operator("xpspmx_mapper.add_hip_blend_rule", text="Hip Blend")

        # Display current rules
        layout.label(text=f"Weight Rules ({len(config.weight_rules)}):")

        for i, rule in enumerate(config.weight_rules):
            row = layout.row()
            row.label(text=f"{rule.source_bone} → {rule.target_bone}")
            row.label(text=f"({rule.rule_type})")


class XPSPMX_PT_validation_preview(Panel):
    """Panel 4: Validation and preview."""
    bl_label = "④ VALIDATION & PREVIEW"
    bl_idname = "XPSPMX_PT_validation_preview"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XPS to PMX Mapper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        config = _GLOBAL_CONFIG['config']
        if config is None:
            layout.label(text="Run 'Auto Map Bones' first", icon='ERROR')
            return

        # Validation button
        layout.label(text="Validation:")
        layout.operator("xpspmx_mapper.validate_config", icon='CHECKMARK')

        # Show validation results
        if config.validation_status:
            is_valid = config.validation_status.get('is_valid', False)
            error_count = config.validation_status.get('error_count', 0)

            icon = 'CHECKMARK' if is_valid else 'ERROR'
            layout.label(text=f"Status: {'Valid' if is_valid else 'Invalid'} ({error_count} errors)", icon=icon)

            # Show errors
            if error_count > 0:
                layout.label(text="Errors:")
                for error in config.validation_status.get('errors', [])[:5]:
                    layout.label(text=f"  • {error}", icon='ERROR')
                if error_count > 5:
                    layout.label(text=f"  ... and {error_count - 5} more errors")

        # Config file operations
        layout.label(text="Configuration:")
        row = layout.row()
        row.operator("xpspmx_mapper.save_config", icon='FILE_TICK')
        row.operator("xpspmx_mapper.load_config", icon='FILE_FOLDER')

        # Start conversion button
        layout.separator()
        layout.operator("xpspmx_mapper.start_conversion", icon='PLAY')


class XPSPMX_OT_validate_config(Operator):
    """Validate the current mapping configuration."""
    bl_idname = "xpspmx_mapper.validate_config"
    bl_label = "Validate Configuration"

    def execute(self, context):
        config = _GLOBAL_CONFIG['config']
        if config is None:
            self.report({'ERROR'}, "No configuration to validate")
            return {'CANCELLED'}

        is_valid, errors = config.validate()

        if is_valid:
            self.report({'INFO'}, "Configuration is valid!")
        else:
            self.report({'WARNING'}, f"Configuration has {len(errors)} errors")
            for error in errors[:3]:
                print(f"  - {error}")

        return {'FINISHED'}


class XPSPMX_OT_start_conversion(Operator):
    """Start the conversion process."""
    bl_idname = "xpspmx_mapper.start_conversion"
    bl_label = "Start Conversion"

    def execute(self, context):
        config = _GLOBAL_CONFIG['config']
        if config is None:
            self.report({'ERROR'}, "No configuration loaded")
            return {'CANCELLED'}

        # TODO: Call pipeline stages with loaded configuration
        self.report({'INFO'}, "Conversion started (not yet implemented)")
        return {'FINISHED'}


# Placeholder operators for rule management (to be implemented)
class XPSPMX_OT_add_fk_to_d_rule(Operator):
    bl_idname = "xpspmx_mapper.add_fk_to_d_rule"
    bl_label = "Add FK→D Rule"

    def execute(self, context):
        self.report({'INFO'}, "FK→D rule management not yet implemented")
        return {'FINISHED'}


class XPSPMX_OT_add_twist_rule(Operator):
    bl_idname = "xpspmx_mapper.add_twist_rule"
    bl_label = "Add Twist Rule"

    def execute(self, context):
        self.report({'INFO'}, "Twist rule management not yet implemented")
        return {'FINISHED'}


class XPSPMX_OT_add_hip_blend_rule(Operator):
    bl_idname = "xpspmx_mapper.add_hip_blend_rule"
    bl_label = "Add Hip Blend Rule"

    def execute(self, context):
        self.report({'INFO'}, "Hip blend rule management not yet implemented")
        return {'FINISHED'}


# Register all classes
classes = [
    XPSToPMXMapperProperties,
    XPSPMX_OT_auto_detect_skeleton,
    XPSPMX_OT_auto_map_bones,
    XPSPMX_OT_save_mapping_config,
    XPSPMX_OT_load_mapping_config,
    XPSPMX_OT_confirm_missing_bones,
    XPSPMX_OT_validate_config,
    XPSPMX_OT_start_conversion,
    XPSPMX_OT_add_fk_to_d_rule,
    XPSPMX_OT_add_twist_rule,
    XPSPMX_OT_add_hip_blend_rule,
    XPSPMX_PT_auto_detection,
    XPSPMX_PT_bone_detection,
    XPSPMX_PT_mapping_editor,
    XPSPMX_PT_weight_rules,
    XPSPMX_PT_validation_preview,
]


def register():
    """Register all classes and properties."""
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.xpspmx_mapper_props = PointerProperty(type=XPSToPMXMapperProperties)
    # Configuration is stored in global _GLOBAL_CONFIG dictionary


def unregister():
    """Unregister all classes and properties."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Scene, 'xpspmx_mapper_props'):
        del bpy.types.Scene.xpspmx_mapper_props

    # Clear global config
    _GLOBAL_CONFIG['config'] = None
    _GLOBAL_CONFIG['current_armature'] = None
