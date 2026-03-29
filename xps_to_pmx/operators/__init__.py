"""XPS to PMX Pipeline Operators"""

from . import stage_0_apply_mapping


def register():
    """Register all pipeline operators."""
    stage_0_apply_mapping.register()


def unregister():
    """Unregister all pipeline operators."""
    stage_0_apply_mapping.unregister()
