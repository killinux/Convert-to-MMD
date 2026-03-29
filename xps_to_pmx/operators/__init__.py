"""XPS to PMX Pipeline Operators"""

from . import stage_0_apply_mapping, stage_1_rebuild_skeleton, stage_2_apply_apose


def register():
    """Register all pipeline operators."""
    stage_0_apply_mapping.register()
    stage_1_rebuild_skeleton.register()
    stage_2_apply_apose.register()


def unregister():
    """Unregister all pipeline operators."""
    stage_2_apply_apose.unregister()
    stage_1_rebuild_skeleton.unregister()
    stage_0_apply_mapping.unregister()
