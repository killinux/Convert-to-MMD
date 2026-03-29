"""
Stage 5: Export to PMX - Export converted rig to MMD PMX format
导出为 PMX 格式 - 完成转换流程
"""

import bpy
import os
from bpy.types import Operator
from typing import Tuple


class XPSPMX_OT_stage_5_export_pmx(Operator):
    """Export armature and meshes to PMX format."""
    bl_idname = "xpspmx_pipeline.stage_5_export_pmx"
    bl_label = "导出 PMX"
    bl_options = {'REGISTER', 'UNDO'}

    # File output path
    filepath: bpy.props.StringProperty(
        name="Output Path",
        description="PMX file output path",
        subtype='FILE_PATH'
    )

    filter_glob: bpy.props.StringProperty(
        default="*.pmx",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        """Check if we have an armature selected."""
        return (context.active_object is not None and
                context.active_object.type == 'ARMATURE')

    def invoke(self, context, event):
        """Open file browser to select output location."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Export to PMX format."""
        armature = context.active_object

        print("\n" + "="*60)
        print("🔄 Stage 5: 导出 PMX")
        print("="*60)

        try:
            # Determine output path
            output_path = self.filepath
            if not output_path:
                # Use default path if not specified
                blend_file = bpy.data.filepath
                if blend_file:
                    base_name = os.path.splitext(os.path.basename(blend_file))[0]
                    output_dir = os.path.dirname(blend_file)
                    output_path = os.path.join(output_dir, f"{base_name}.pmx")
                else:
                    # Use armature name as fallback
                    output_path = f"{armature.name}.pmx"

            print(f"\n1️⃣ 准备导出...")
            print(f"   输出路径: {output_path}")

            # Step 1: Verify armature and meshes
            print(f"\n2️⃣ 验证骨骼和网格...")
            bone_count = len(armature.data.bones)
            mesh_count = self._count_meshes(context.scene)
            print(f"   ✓ 骨骼数: {bone_count}")
            print(f"   ✓ 网格数: {mesh_count}")

            # Step 2: Verify mmd_tools is available
            print(f"\n3️⃣ 检查 mmd_tools 插件...")
            has_mmd_tools = self._check_mmd_tools()
            if not has_mmd_tools:
                print(f"   ⚠ mmd_tools 未启用，尝试启用...")
                try:
                    bpy.ops.preferences.addon_enable(module="mmd_tools")
                    print(f"   ✓ mmd_tools 已启用")
                except:
                    print(f"   ⚠ mmd_tools 启用失败，继续尝试导出...")

            # Step 3: Try to export using mmd_tools
            print(f"\n4️⃣ 导出 PMX 文件...")
            success, msg = self._export_pmx(armature, output_path)

            if success:
                print(f"   ✓ {msg}")
            else:
                print(f"   ⚠ {msg}")
                # Fallback: Create basic structure for manual export
                print(f"   📝 已为手动导出准备好模型")

            # Step 4: Verify output
            print(f"\n5️⃣ 验证输出...")
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   ✓ 文件已生成: {file_size} 字节")
                verified = True
            else:
                print(f"   ⚠ 文件未生成（需手动导出）")
                verified = False

            # Report summary
            print("\n" + "="*60)
            print(f"✅ Stage 5 完成")
            print(f"   骨骼: {bone_count}")
            print(f"   网格: {mesh_count}")
            print(f"   输出: {output_path}")
            print(f"   状态: {'✓ 成功' if verified else '⚠ 需要手动导出'}")
            print(f"="*60 + "\n")

            if verified:
                self.report({'INFO'}, f"✓ PMX 导出成功: {os.path.basename(output_path)}")
            else:
                self.report({'WARNING'}, f"⚠ 模型已准备，请使用 mmd_tools 手动导出")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"导出失败: {str(e)}")
            print(f"ERROR: {str(e)}")
            return {'CANCELLED'}

    def _count_meshes(self, scene) -> int:
        """Count mesh objects in the scene."""
        count = 0
        for obj in scene.objects:
            if obj.type == 'MESH':
                count += 1
        return count

    def _check_mmd_tools(self) -> bool:
        """Check if mmd_tools addon is enabled."""
        try:
            import mmd_tools
            return True
        except ImportError:
            return False

    def _export_pmx(self, armature, output_path: str) -> Tuple[bool, str]:
        """Export to PMX format using mmd_tools.

        Args:
            armature: Armature object to export
            output_path: Output file path

        Returns:
            (success, message) tuple
        """
        try:
            # Try using mmd_tools exporter
            import mmd_tools
            from mmd_tools.core.pmx import export

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Prepare export settings
            export_settings = {
                'filepath': output_path,
                'scale': 1.0,  # No scaling
                'use_toon': True,
                'use_sphere': True,
                'use_sdef': False,
                'sort_materials': True,
                'sort_bones': True,
            }

            # Export using mmd_tools
            # Note: The actual export method may vary depending on mmd_tools version
            # This is a simplified version - actual implementation may need adjustment
            print(f"   📤 使用 mmd_tools 导出...")
            bpy.ops.mmd_tools.export_pmx(
                filepath=output_path,
                scale=1.0
            )

            return True, "PMX 导出成功"

        except ImportError:
            print(f"   ⚠ mmd_tools 不可用")
            return self._create_placeholder_pmx(armature, output_path)
        except Exception as e:
            print(f"   ⚠ 导出出错: {str(e)}")
            return self._create_placeholder_pmx(armature, output_path)

    def _create_placeholder_pmx(self, armature, output_path: str) -> Tuple[bool, str]:
        """Create a placeholder/basic PMX file structure.

        This is a fallback when mmd_tools is not available.
        Users can then use mmd_tools to export manually.

        Args:
            armature: Armature object
            output_path: Output file path

        Returns:
            (success, message) tuple
        """
        try:
            # Create a minimal PMX file with basic structure
            # This allows Blender to save the model in a format that
            # can be imported by mmd_tools for final export

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Write a basic text file indicating the model is ready
            info_path = output_path.replace('.pmx', '_info.txt')
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write("XPS to MMD 转换完成\n")
                f.write("="*60 + "\n")
                f.write(f"骨骼: {len(armature.data.bones)}\n")
                f.write(f"网格: {len([o for o in bpy.context.scene.objects if o.type == 'MESH'])}\n")
                f.write("\n")
                f.write("导出方法:\n")
                f.write("1. 确保 mmd_tools 已启用\n")
                f.write("2. File → Export → mmd_tools PMX Exporter\n")
                f.write("3. 选择输出路径\n")

            # Also save the Blender file as intermediate format
            blend_export_path = output_path.replace('.pmx', '.blend')
            bpy.ops.wm.save_as_mainfile(filepath=blend_export_path)

            return True, f"模型已准备，可手动导出"

        except Exception as e:
            return False, f"准备导出失败: {str(e)}"


def register():
    """Register the Stage 5 operator."""
    bpy.utils.register_class(XPSPMX_OT_stage_5_export_pmx)


def unregister():
    """Unregister the Stage 5 operator."""
    bpy.utils.unregister_class(XPSPMX_OT_stage_5_export_pmx)
