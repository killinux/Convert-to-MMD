# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Blender addon** that converts arbitrary 3D character rigs into **MMD (MikuMikuDance)** format. It handles bone renaming to Japanese MMD names, creating missing bones, D-bone splitting, IK chain generation, weight fixing, and preset management for 25+ source rig formats (Mixamo, VRM, VRoid, DAZ, iClone, MotionBuilder, etc.).

**Dependencies:**
- Blender 3.0+ (Python API `bpy`)
- `mmd_tools` addon v0.5.0+ installed and enabled in Blender

## Installation & Running

This is a Blender addon — there is no build step or standalone runtime.

1. Place the addon folder in Blender's addons directory (e.g., `~/.config/blender/3.x/scripts/addons/`)
2. Enable it in Blender Preferences > Add-ons > "Convert to MMD"
3. In the 3D View sidebar, find the "Convert to MMD" tab with an armature selected

There are no unit tests or CLI commands. All testing is manual inside Blender.

## Architecture

### Entry Point & Registration
`__init__.py` registers all 30+ operator classes, defines dynamic `bpy.props` on `bpy.types.Scene` for bone mapping selections, and loads preset enums from `presets/`.

### Operator Pipeline (12 steps, orchestrated by `auto_convert_operator.py`)
1. Merge meshes — `operators/mesh_operator.py`
2. Clear unweighted bones — `operators/clear_unweighted_bones_operator.py`
3. Convert to A-Pose — `operators/pose_operator.py`
4. Rename bones to MMD — `operators/bone_operator.py` (`rename_to_mmd`)
5. Complete missing bones — `operators/bone_operator.py` (`complete_missing_bones`)
6. Split D-bones (spine/shoulder deform pairs) — `operators/bone_split_operator.py`
7. Add twist bones — `operators/twist_bone_operator.py`
8. Add IK chains — `operators/ik_operator.py`
9. Create bone groups/collections — `operators/collection_operator.py`
10. Convert materials — `operators/material_operator.py`
11. Fix missing/orphan weights — `operators/bone_operator.py` (weight repair functions)
12. Verify weights — `operators/weight_verify_operator.py`

### Core Files
- **`operators/bone_operator.py`** (1524 lines) — Heaviest file; contains bone renaming logic, missing bone creation, weight transfer for D-bones, and hip blend zone repair. Most weight-processing bugs originate here.
- **`bone_map_and_group.py`** — Authoritative source for English property name → Japanese MMD bone name mappings (60+ entries) and 8 bone group definitions. Edit this when adding new bone types.
- **`ui_panel.py`** — All UI rendering. Bone dropdowns are dynamically built from scene properties.
- **`operators/weight_monitor.py`** — Snapshot-based health monitoring; compares before/after weights for each pipeline step.

### Preset System
JSON files in `presets/` map source rig bone names to the addon's internal property names. Loaded dynamically at registration. `operators/preset_operator.py` handles save/load.

### Known Architectural Issue (see `REFACTOR_PLAN.md`)
The linear pipeline causes cleanup steps (normalize, orphan removal) to destroy weight gradients built by earlier steps. A zone-based refactor is planned: **Zone 1** (upper body — aggressive cleanup OK), **Zone 2** (hip blend — no global normalize, preserve gradients), **Zone 3** (lower body — single-side normalize). When editing weight-processing code in `bone_operator.py`, be aware of this constraint.

### Key Conventions
- All MMD bone names are Japanese (stored in `bone_map_and_group.py`)
- Bone property names follow the pattern `left_arm_bone`, `right_leg_bone`, etc.
- D-bones (deform bones) follow naming convention: original name + `_D` suffix or `D_` prefix depending on bone type
- Hip blend zone bones require strict left/right weight separation — never globally normalize across sides
- `debug_leg_weights.py` is a standalone development/debugging script, not part of the addon itself
