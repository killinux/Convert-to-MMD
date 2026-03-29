"""
Stage 3: Apply Weight Rules - Transfer and fix vertex weights
应用权重规则：FK→D骨、腰Cancel、髋部渐变、扭转骨等
"""

import bpy
from bpy.types import Operator
from typing import Tuple, Dict, List
import json

from .. import weights
from ..mapping import data_structures


class XPSPMX_OT_stage_3_apply_weight_rules(Operator):
    """Apply weight transfer rules (FK→D, hip blend, twist bones, etc)."""
    bl_idname = "xpspmx_pipeline.stage_3_apply_weight_rules"
    bl_label = "应用权重规则"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if we have an armature selected."""
        return (context.active_object is not None and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        """Apply weight transfer rules."""
        from .. import mapping_ui

        scene = context.scene
        armature = context.active_object

        # Get mapping configuration
        config = mapping_ui._GLOBAL_CONFIG.get('config')
        if config is None or not config.weight_rules:
            self.report({'INFO'}, "没有权重规则需要应用")
            return {'FINISHED'}

        print("\n" + "="*60)
        print("🔄 Stage 3: 应用权重规则")
        print("="*60)

        try:
            # Step 1: Collect mesh objects
            print("\n1️⃣ 收集网格对象...")
            mesh_objects = self._collect_mesh_objects(scene)
            if not mesh_objects:
                self.report({'WARNING'}, "未找到具有权重的网格")
                return {'FINISHED'}
            print(f"   ✓ 找到 {len(mesh_objects)} 个网格")

            # Step 2: Apply all weight rules
            print("\n2️⃣ 应用权重规则...")
            results = weights.apply_all_weight_rules(armature, mesh_objects, config.weight_rules)
            applied_count = len(results['applied_rules'])
            failed_count = len(results['failed_rules'])

            print(f"   ✓ 应用了 {applied_count} 条规则")
            if failed_count > 0:
                print(f"   ⚠ 失败了 {failed_count} 条规则")

            # Step 3: Normalize weights
            print("\n3️⃣ 归一化顶点权重...")
            normalized_count = self._normalize_all_weights(mesh_objects)
            print(f"   ✓ 归一化了 {normalized_count} 个顶点")

            # Step 4: Verify results
            print("\n4️⃣ 验证权重...")
            verify_count, warnings = self._verify_weights(mesh_objects)
            print(f"   ✓ 验证通过: {verify_count} 个顶点")
            if warnings:
                for warning in warnings[:5]:
                    print(f"   ⚠ {warning}")
                if len(warnings) > 5:
                    print(f"   ... 还有 {len(warnings) - 5} 个警告")

            # Report summary
            print("\n" + "="*60)
            print(f"✅ Stage 3 完成")
            print(f"   应用规则: {applied_count}")
            print(f"   归一化: {normalized_count}")
            print(f"   验证: {verify_count}")
            print(f"="*60 + "\n")

            message = f"✓ 权重规则应用完成: {applied_count} 条规则"
            if failed_count > 0:
                message += f", {failed_count} 条失败"
            self.report({'INFO'}, message)
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"权重规则应用失败: {str(e)}")
            print(f"ERROR: {str(e)}")
            return {'CANCELLED'}

    def _collect_mesh_objects(self, scene) -> List[bpy.types.Object]:
        """Collect all mesh objects with vertex groups.

        Args:
            scene: Blender scene

        Returns:
            List of mesh objects
        """
        mesh_objects = []
        for obj in scene.objects:
            if obj.type == 'MESH' and obj.vertex_groups:
                mesh_objects.append(obj)
        return mesh_objects

    def _normalize_all_weights(self, mesh_objects: List[bpy.types.Object]) -> int:
        """Normalize vertex weights to ≤1.0 across all meshes.

        Args:
            mesh_objects: List of mesh objects to process

        Returns:
            Number of vertices normalized
        """
        normalized_count = 0

        for obj in mesh_objects:
            for vertex in obj.data.vertices:
                # Calculate total weight for this vertex
                total_weight = sum(g.weight for g in vertex.groups)

                # If total > 1.0, normalize
                if total_weight > 1.0:
                    for g in vertex.groups:
                        g.weight = g.weight / total_weight
                    normalized_count += 1

        return normalized_count

    def _verify_weights(self, mesh_objects: List[bpy.types.Object]) -> Tuple[int, List[str]]:
        """Verify weights are valid and within expected ranges.

        Args:
            mesh_objects: List of mesh objects to verify

        Returns:
            (verified_count, warning_list)
        """
        verified_count = 0
        warnings = []

        for obj in mesh_objects:
            for vertex in obj.data.vertices:
                total_weight = sum(g.weight for g in vertex.groups)

                # Check if weight is valid
                if 0.0 <= total_weight <= 1.0:
                    verified_count += 1
                else:
                    warnings.append(
                        f"{obj.name}: Vertex {vertex.index} total_weight={total_weight:.3f} (invalid)"
                    )

                # Check for suspicious weights
                if total_weight == 0.0 and len(vertex.groups) == 0:
                    warnings.append(
                        f"{obj.name}: Vertex {vertex.index} has no weights (orphaned)"
                    )

        return verified_count, warnings


def register():
    """Register the Stage 3 operator."""
    bpy.utils.register_class(XPSPMX_OT_stage_3_apply_weight_rules)


def unregister():
    """Unregister the Stage 3 operator."""
    bpy.utils.unregister_class(XPSPMX_OT_stage_3_apply_weight_rules)
