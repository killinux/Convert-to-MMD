"""XPS to PMX Pipeline Operators"""

from . import stage_0_apply_mapping, stage_1_rebuild_skeleton


def register():
    """Register all pipeline operators."""
    stage_0_apply_mapping.register()
    stage_1_rebuild_skeleton.register()


def unregister():
    """Unregister all pipeline operators."""
    stage_1_rebuild_skeleton.unregister()
    stage_0_apply_mapping.unregister()
