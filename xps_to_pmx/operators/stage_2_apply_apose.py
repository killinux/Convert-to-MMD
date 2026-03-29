"""
Stage 2: Apply A-Pose - Rotate arms to standard MMD pose
转换到 A-Pose（标准 MMD 人物姿态）
"""

import bpy
from bpy.types import Operator
from mathutils import Euler
from typing import Tuple
import math


class XPSPMX_OT_stage_2_apply_apose(Operator):
    """Apply A-Pose: rotate arms to standard MMD pose."""
    bl_idname = "xpspmx_pipeline.stage_2_apply_apose"
    bl_label = "应用 A-Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if we have an armature selected."""
        return (context.active_object is not None and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        """Apply A-Pose by rotating arms."""
        armature = context.active_object

        print("\n" + "="*60)
        print("🔄 Stage 2: 应用 A-Pose")
        print("="*60)

        try:
            # Step 1: Enter pose mode
            print("\n1️⃣ 进入姿态编辑模式...")
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='POSE')

            rotated_count = 0

            # Step 2: Rotate left arm
            print("\n2️⃣ 旋转左手臂...")
            success = self._rotate_arm(armature, "左腕", 37.0)
            if success:
                rotated_count += 1
                print(f"   ✓ 左腕 旋转 +37°")
            else:
                print(f"   ⚠ 左腕 旋转失败（可能不存在）")

            # Step 3: Rotate right arm
            print("\n3️⃣ 旋转右手臂...")
            success = self._rotate_arm(armature, "右腕", -37.0)
            if success:
                rotated_count += 1
                print(f"   ✓ 右腕 旋转 -37°")
            else:
                print(f"   ⚠ 右腕 旋转失败（可能不存在）")

            # Step 4: Bake pose to rest pose
            print("\n4️⃣ 烘焙姿态到 Rest Pose...")
            bake_count = self._bake_pose_to_rest(armature)
            print(f"   ✓ 烘焙了 {bake_count} 个骨骼")

            # Return to object mode
            print("\n5️⃣ 返回物体模式...")
            bpy.ops.object.mode_set(mode='OBJECT')

            # Report summary
            print("\n" + "="*60)
            print(f"✅ Stage 2 完成")
            print(f"   旋转骨骼: {rotated_count}")
            print(f"   烘焙骨骼: {bake_count}")
            print(f"="*60 + "\n")

            self.report({'INFO'}, f"✓ A-Pose 应用完成: {rotated_count} 个手臂已旋转")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"A-Pose 转换失败: {str(e)}")
            print(f"ERROR: {str(e)}")
            return {'CANCELLED'}
        finally:
            try:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass

    def _rotate_arm(self, armature, arm_bone_name: str, degrees: float) -> bool:
        """Rotate an arm bone to the specified angle.

        Args:
            armature: Armature object
            arm_bone_name: Name of the arm bone (e.g., "左腕")
            degrees: Rotation angle in degrees

        Returns:
            True if successful, False otherwise
        """
        try:
            pose_bone = armature.pose.bones.get(arm_bone_name)
            if not pose_bone:
                return False

            # Convert degrees to radians
            radians = math.radians(degrees)

            # Set rotation (rotate around Y axis)
            # Rotation order: (X, Y, Z) in Euler angles
            pose_bone.rotation_euler = Euler((0, radians, 0), 'XYZ')

            return True
        except Exception as e:
            print(f"   Error rotating {arm_bone_name}: {e}")
            return False

    def _bake_pose_to_rest(self, armature) -> int:
        """Bake pose to rest pose for all posed bones.

        This sets the current pose as the new rest pose,
        clearing the pose for all bones.

        Args:
            armature: Armature object

        Returns:
            Number of bones processed
        """
        try:
            # Select all bones
            bpy.ops.pose.select_all(action='SELECT')

            # Apply pose as rest pose
            # In Blender, this is done by setting the armature's rest pose
            # For simplicity, we'll use the pose as the new rest pose
            bpy.ops.pose.armature_apply(selected=False)

            return len(armature.pose.bones)

        except Exception as e:
            print(f"   Error baking pose: {e}")
            return 0


def register():
    """Register the Stage 2 operator."""
    bpy.utils.register_class(XPSPMX_OT_stage_2_apply_apose)


def unregister():
    """Unregister the Stage 2 operator."""
    bpy.utils.unregister_class(XPSPMX_OT_stage_2_apply_apose)
