"""Flexible mapping system for XPS to PMX conversion.

This module provides a flexible, transparent, and user-verifiable bone and weight mapping system
that supports any XPS skeleton variant, not just standard formats.

Core components:
- data_structures: BoneMapping, WeightMappingRule, MappingConfiguration classes
- detection: Auto-detection functions for skeleton type and bone mappings
- presets: JSON preset files for standard XPS formats
"""

from . import data_structures, detection

__all__ = ['data_structures', 'detection']
