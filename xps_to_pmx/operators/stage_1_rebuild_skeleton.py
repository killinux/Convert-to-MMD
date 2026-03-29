"""
Stage 1: Rebuild Skeleton - Create missing bones and adjust properties
补全缺失的骨骼，调整骨骼属性和父级关系
"""

import bpy
from bpy.types import Operator
from typing import Tuple, Dict, List, Set
import json
import os

from .. import mapping


class XPSPMX_OT_stage_1_rebuild_skeleton(Operator):
    """Rebuild skeleton: create missing bones and adjust properties."""
    bl_idname = "xpspmx_pipeline.stage_1_rebuild_skeleton"
    bl_label = "重建骨架"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if we have an armature selected."""
        return (context.active_object is not None and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        """Rebuild skeleton by creating missing bones."""
        from .. import mapping_ui

        scene = context.scene
        armature = context.active_object

        # Get mapping configuration
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config is None:
            self.report({'ERROR'}, "没有映射配置，请先运行 Stage 0")
            return {'CANCELLED'}

        print("\n" + "="*60)
        print("🔄 Stage 1: 重建骨架")
        print("="*60)

        try:
            # Step 1: Load MMD standard skeleton
            print("\n1️⃣ 加载 MMD 标准骨骼库...")
            mmd_skeleton = self._load_mmd_skeleton()
            if not mmd_skeleton:
                self.report({'ERROR'}, "无法加载 MMD 标准骨骼库")
                return {'CANCELLED'}
            print(f"   ✓ 加载了 {len(mmd_skeleton)} 个标准骨骼")

            # Step 2: Determine which bones are missing
            print("\n2️⃣ 检测缺失的骨骼...")
            existing_bones = set(bone.name for bone in armature.data.bones)
            missing_bones = self._find_missing_bones(existing_bones, mmd_skeleton)
            print(f"   ✓ 发现 {len(missing_bones)} 个缺失的骨骼")
            if missing_bones:
                for bone_name in list(missing_bones)[:10]:
                    print(f"     - {bone_name}")
                if len(missing_bones) > 10:
                    print(f"     ... 还有 {len(missing_bones) - 10} 个")

            # Step 3: Create missing bones
            print("\n3️⃣ 创建缺失的骨骼...")
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='EDIT')

            try:
                created_count = self._create_missing_bones(
                    armature, missing_bones, mmd_skeleton, config
                )
                print(f"   ✓ 创建了 {created_count} 个骨骼")
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')

            # Step 4: Adjust bone properties
            print("\n4️⃣ 调整骨骼属性...")
            adjusted_count = self._adjust_bone_properties(armature, mmd_skeleton)
            print(f"   ✓ 调整了 {adjusted_count} 个骨骼的属性")

            # Step 5: Verify parent-child relationships
            print("\n5️⃣ 验证父级关系...")
            verify_count = self._verify_hierarchy(armature, mmd_skeleton)
            print(f"   ✓ 验证通过: {verify_count} 个骨骼")

            # Report summary
            print("\n" + "="*60)
            print(f"✅ Stage 1 完成")
            print(f"   创建骨骼: {created_count}")
            print(f"   调整属性: {adjusted_count}")
            print(f"   验证成功: {verify_count}")
            print(f"="*60 + "\n")

            self.report({'INFO'}, f"✓ 骨架重建完成: {created_count} 个新骨骼")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"骨架重建失败: {str(e)}")
            print(f"ERROR: {str(e)}")
            return {'CANCELLED'}

    def _load_mmd_skeleton(self) -> Dict:
        """Load MMD standard skeleton from JSON."""
        try:
            preset_path = os.path.join(
                os.path.dirname(mapping.__file__),
                'presets',
                'mmd_standard_skeleton.json'
            )
            with open(preset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('bones', {})
        except Exception as e:
            print(f"Error loading MMD skeleton: {e}")
            return {}

    def _find_missing_bones(self, existing_bones: Set[str],
                           mmd_skeleton: Dict) -> Set[str]:
        """Find bones that exist in MMD standard but not in armature.

        Args:
            existing_bones: Set of existing bone names in armature
            mmd_skeleton: MMD standard skeleton definition

        Returns:
            Set of missing bone names
        """
        missing = set()
        for bone_name in mmd_skeleton.keys():
            if bone_name not in existing_bones:
                missing.add(bone_name)
        return missing

    def _create_missing_bones(self, armature, missing_bones: Set[str],
                             mmd_skeleton: Dict, config) -> int:
        """Create missing bones in edit mode.

        Args:
            armature: Target armature
            missing_bones: Set of bone names to create
            mmd_skeleton: MMD standard skeleton definition
            config: Current mapping configuration

        Returns:
            Number of bones created
        """
        if not missing_bones:
            return 0

        eb = armature.data.edit_bones
        created_count = 0

        # Use topological sort to ensure parents are created before children
        creation_order = self._topological_sort_bones(missing_bones, mmd_skeleton, eb)

        for bone_name in creation_order:
            if bone_name in eb:
                continue  # Already exists

            bone_def = mmd_skeleton.get(bone_name, {})
            parent_name = bone_def.get('parent_mmd')

            try:
                # Create bone
                new_bone = eb.new(bone_name)

                # Set parent if it exists (should exist due to topological sort)
                if parent_name and parent_name in eb:
                    new_bone.parent = eb[parent_name]

                # Position bone below parent or at origin
                if parent_name and parent_name in eb:
                    parent_bone = eb[parent_name]
                    # Position 0.5 units below parent in Z axis
                    new_bone.head = parent_bone.tail
                    new_bone.tail = (parent_bone.tail[0],
                                    parent_bone.tail[1],
                                    parent_bone.tail[2] - 0.5)
                else:
                    # Position at origin
                    new_bone.head = (0, 0, 0)
                    new_bone.tail = (0, 0, -0.5)

                # Set bone properties
                is_deform = bone_def.get('is_deform', True)
                new_bone.use_deform = is_deform

                created_count += 1
                print(f"   ✓ 创建: {bone_name} (parent: {parent_name or '无'})")

            except Exception as e:
                print(f"   ⚠ 失败: {bone_name} - {str(e)}")

        return created_count

    def _topological_sort_bones(self, missing_bones: Set[str],
                               mmd_skeleton: Dict,
                               edit_bones) -> List[str]:
        """Sort bones topologically so parents are created before children.

        Args:
            missing_bones: Set of bones to create
            mmd_skeleton: MMD standard skeleton definition
            edit_bones: Blender edit bones collection

        Returns:
            Sorted list of bone names (parents first)
        """
        # Build dependency graph
        result = []
        visited = set()
        temp_visited = set()

        def visit(bone_name):
            if bone_name in visited:
                return
            if bone_name in temp_visited:
                return  # Avoid cycles

            temp_visited.add(bone_name)

            # First, visit parent if it needs to be created
            if bone_name in missing_bones:
                bone_def = mmd_skeleton.get(bone_name, {})
                parent_name = bone_def.get('parent_mmd')

                # If parent is missing and needs to be created, visit it first
                if parent_name and parent_name in missing_bones and parent_name not in visited:
                    visit(parent_name)

            temp_visited.discard(bone_name)
            visited.add(bone_name)

            if bone_name in missing_bones:
                result.append(bone_name)

        # Visit all missing bones
        for bone_name in missing_bones:
            if bone_name not in visited:
                visit(bone_name)

        return result

    def _adjust_bone_properties(self, armature, mmd_skeleton: Dict) -> int:
        """Adjust bone properties (use_deform, etc.) based on MMD standard.

        Args:
            armature: Target armature
            mmd_skeleton: MMD standard skeleton definition

        Returns:
            Number of bones adjusted
        """
        adjusted_count = 0

        for bone in armature.data.bones:
            if bone.name not in mmd_skeleton:
                continue

            bone_def = mmd_skeleton[bone.name]
            is_deform = bone_def.get('is_deform', True)

            # Only adjust if it differs from standard
            if bone.use_deform != is_deform:
                bone.use_deform = is_deform
                adjusted_count += 1

        return adjusted_count

    def _verify_hierarchy(self, armature, mmd_skeleton: Dict) -> int:
        """Verify that parent-child relationships match MMD standard.

        Args:
            armature: Target armature
            mmd_skeleton: MMD standard skeleton definition

        Returns:
            Number of verified bones
        """
        verified_count = 0

        for bone in armature.data.bones:
            if bone.name not in mmd_skeleton:
                continue

            bone_def = mmd_skeleton[bone.name]
            expected_parent = bone_def.get('parent_mmd')

            # Get actual parent
            actual_parent = bone.parent.name if bone.parent else None

            # Check if parent matches
            if actual_parent == expected_parent:
                verified_count += 1
            else:
                print(f"   ⚠ 父级不匹配: {bone.name}")
                print(f"      期望: {expected_parent}, 实际: {actual_parent}")

        return verified_count


def register():
    """Register the Stage 1 operator."""
    bpy.utils.register_class(XPSPMX_OT_stage_1_rebuild_skeleton)


def unregister():
    """Unregister the Stage 1 operator."""
    bpy.utils.unregister_class(XPSPMX_OT_stage_1_rebuild_skeleton)
