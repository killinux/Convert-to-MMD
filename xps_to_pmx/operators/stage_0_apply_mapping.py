"""
Stage 0: Apply Bone Mapping - Rename bones and sync vertex groups
将映射应用到 Blender：重命名骨骼并同步顶点组
"""

import bpy
from bpy.types import Operator
from typing import Tuple, Dict, List


class XPSPMX_OT_stage_0_apply_mapping(Operator):
    """Apply bone mapping - rename bones and sync vertex groups."""
    bl_idname = "xpspmx_pipeline.stage_0_apply_mapping"
    bl_label = "应用骨骼映射"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if we have an armature selected."""
        return (context.active_object is not None and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        """Apply bone mapping: rename bones and sync vertex groups."""
        from .. import mapping_ui

        scene = context.scene
        armature = context.active_object

        # Get mapping configuration
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config is None:
            self.report({'ERROR'}, "没有映射配置，请先运行自动映射")
            return {'CANCELLED'}

        print("\n" + "="*60)
        print("🔄 Stage 0: 应用骨骼映射")
        print("="*60)

        # Step 1: Validate and build rename mapping
        print("\n1️⃣ 验证映射配置...")
        rename_map = self._build_rename_map(config)
        print(f"   ✓ 找到 {len(rename_map)} 个骨骼需要重命名")

        # Step 2: Rename bones in armature
        print("\n2️⃣ 重命名骨骼...")
        renamed_count, errors = self._rename_bones(armature, rename_map)
        print(f"   ✓ 成功重命名: {renamed_count} 个骨骼")
        if errors:
            print(f"   ⚠ 失败: {len(errors)} 个骨骼")
            for error in errors[:5]:
                print(f"     - {error}")

        # Step 3: Sync vertex groups on all meshes
        print("\n3️⃣ 同步顶点组...")
        mesh_count, vg_count, vg_errors = self._sync_vertex_groups(scene, rename_map)
        print(f"   ✓ 处理了 {mesh_count} 个网格")
        print(f"   ✓ 重命名了 {vg_count} 个顶点组")
        if vg_errors:
            print(f"   ⚠ 失败: {len(vg_errors)} 个顶点组")

        # Step 4: Verify results
        print("\n4️⃣ 验证结果...")
        verify_count = self._verify_mapping(armature, config)
        print(f"   ✓ 验证通过: {verify_count} 个骨骼")

        # Report summary
        print("\n" + "="*60)
        print(f"✅ Stage 0 完成")
        print(f"   重命名骨骼: {renamed_count}/{len(rename_map)}")
        print(f"   重命名顶点组: {vg_count}")
        print(f"="*60 + "\n")

        self.report({'INFO'}, f"✓ 应用映射完成: {renamed_count} 个骨骼重命名")
        return {'FINISHED'}

    def _build_rename_map(self, config) -> Dict[str, str]:
        """Build a mapping from XPS bone names to MMD names.

        Returns:
            Dict mapping old_name -> new_name
        """
        rename_map = {}
        for mapping_obj in config.bone_mappings.values():
            if mapping_obj.mmd_name and not mapping_obj.is_unmapped:
                rename_map[mapping_obj.xps_name] = mapping_obj.mmd_name
        return rename_map

    def _rename_bones(self, armature: bpy.types.Object,
                      rename_map: Dict[str, str]) -> Tuple[int, List[str]]:
        """Rename all bones in the armature.

        Args:
            armature: The armature object
            rename_map: Dict mapping old names to new names

        Returns:
            (success_count, error_list)
        """
        success_count = 0
        errors = []

        # Enter edit mode to rename bones
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        try:
            for bone in armature.data.edit_bones:
                if bone.name in rename_map:
                    new_name = rename_map[bone.name]
                    try:
                        bone.name = new_name
                        success_count += 1
                    except Exception as e:
                        errors.append(f"{bone.name} → {new_name}: {str(e)[:50]}")
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        return success_count, errors

    def _sync_vertex_groups(self, scene: bpy.types.Scene,
                            rename_map: Dict[str, str]) -> Tuple[int, int, List[str]]:
        """Sync vertex group names on all meshes to match bone renames.

        Args:
            scene: The scene
            rename_map: Dict mapping old names to new names

        Returns:
            (mesh_count, vgroup_count, error_list)
        """
        mesh_count = 0
        vgroup_count = 0
        errors = []

        for obj in scene.objects:
            if obj.type != 'MESH':
                continue

            mesh_count += 1
            mesh = obj.data

            # Rename vertex groups
            for vgroup in mesh.vertex_groups:
                if vgroup.name in rename_map:
                    new_name = rename_map[vgroup.name]
                    try:
                        vgroup.name = new_name
                        vgroup_count += 1
                    except Exception as e:
                        errors.append(f"{obj.name}.{vgroup.name}: {str(e)[:50]}")

        return mesh_count, vgroup_count, errors

    def _verify_mapping(self, armature: bpy.types.Object, config) -> int:
        """Verify that bones have been renamed correctly.

        Args:
            armature: The armature object
            config: The mapping configuration

        Returns:
            Number of verified bones
        """
        verify_count = 0

        for bone in armature.data.bones:
            # Check if this bone is in the config
            for mapping_obj in config.bone_mappings.values():
                if mapping_obj.mmd_name == bone.name and not mapping_obj.is_unmapped:
                    verify_count += 1
                    break

        return verify_count


def register():
    """Register the Stage 0 operator."""
    bpy.utils.register_class(XPSPMX_OT_stage_0_apply_mapping)


def unregister():
    """Unregister the Stage 0 operator."""
    bpy.utils.unregister_class(XPSPMX_OT_stage_0_apply_mapping)
