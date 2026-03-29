"""Data structures for flexible bone and weight mapping system."""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class BoneType(Enum):
    """Classification of bone types."""
    SPINE = "spine"
    ARM = "arm"
    LEG = "leg"
    HAND = "hand"
    FINGER = "finger"
    EYE = "eye"
    CONTROL = "control"
    D_BONE = "d_bone"
    IK = "ik"


class WeightRuleType(Enum):
    """Types of weight transfer rules."""
    FK_TO_D = "fk_to_d"
    TWIST = "twist"
    WAIST_CANCEL = "waist_cancel"
    HIP_BLEND = "hip_blend"
    NORMALIZE = "normalize"
    ORPHAN_TRANSFER = "orphan_transfer"


class FalloffType(Enum):
    """Weight gradient falloff types."""
    LINEAR = "linear"
    QUADRATIC = "quadratic"
    SMOOTH = "smooth"


@dataclass
class BoneMapping:
    """Mapping record for a single bone from XPS to MMD.

    Attributes:
        xps_name: XPS bone name (English)
        mmd_name: MMD bone name (Japanese)
        confidence: Auto-detection confidence (0~1)
        parent_xps: Parent bone name in XPS skeleton
        parent_mmd: Corresponding parent bone name in MMD skeleton (as mapped by user)
        parent_mmd_expected: Expected parent in MMD standard skeleton (source of truth)
        parent_match: Whether parent_mmd matches parent_mmd_expected (validation result)
        bone_type: Classification of this bone
        is_deform: Whether this is a deform bone (use_deform)
        is_unmapped: Whether this bone is unmapped (mmd_name is empty or placeholder)
        position_offset: Relative position offset for new bones (for rebuild stage)
        vertex_group_count: Number of vertex groups affected by this bone (for weight tracking)
        user_notes: User notes explaining why this mapping was chosen
        source_info: Where this mapping came from (e.g., "preset:standard_xps", "auto_detect", "user_edit")
    """
    xps_name: str
    mmd_name: str
    confidence: float = 1.0
    parent_xps: Optional[str] = None
    parent_mmd: Optional[str] = None
    parent_mmd_expected: Optional[str] = None  # MMD standard parent (source of truth)
    parent_match: bool = True  # Whether mapping respects MMD hierarchy
    bone_type: str = BoneType.SPINE.value
    is_deform: bool = True
    is_unmapped: bool = False  # True if mmd_name is empty or unresolved
    position_offset: Optional[Tuple[float, float, float]] = None  # (x, y, z)
    vertex_group_count: int = 0  # Count of vertex groups with weights
    user_notes: str = ""  # Detailed notes about this mapping decision
    source_info: str = ""  # Source of mapping (e.g., "auto_detect", "preset", "user_edit")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.position_offset:
            data['position_offset'] = list(self.position_offset)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoneMapping':
        """Create from dictionary (e.g., from JSON)."""
        data = data.copy()
        if isinstance(data.get('position_offset'), list):
            data['position_offset'] = tuple(data['position_offset'])
        return cls(**data)


@dataclass
class WeightMappingRule:
    """A rule for transferring vertex weights from one bone to another.

    Attributes:
        source_bone: Source bone name (XPS name)
        target_bone: Target bone name (MMD name)
        transfer_ratio: Ratio of weight to transfer (0~1)
        zone: Zone classification: zone1 (upper), zone2 (hip), zone3 (lower)
        falloff_type: Gradient falloff type
        blend_threshold: Threshold for blending (e.g., 0.46 for hip blend)
        is_hip_cancel: Whether this is a waist cancel bone (deform=False)
        rule_type: Type of rule to execute
        order: Execution order (rules are applied in order)
    """
    source_bone: str
    target_bone: str
    transfer_ratio: float = 1.0
    zone: str = "zone3"
    falloff_type: str = FalloffType.LINEAR.value
    blend_threshold: float = 0.5
    is_hip_cancel: bool = False
    rule_type: str = WeightRuleType.FK_TO_D.value
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeightMappingRule':
        """Create from dictionary (e.g., from JSON)."""
        return cls(**data)


@dataclass
class MMDBone:
    """Definition of a standard MMD bone (source of truth for hierarchy).

    Attributes:
        mmd_name: MMD bone name (Japanese)
        parent_mmd: Parent bone name in MMD hierarchy
        is_deform: Whether this is a deform bone
        bone_type: Classification of this bone
        notes: Description of this bone
    """
    mmd_name: str
    parent_mmd: Optional[str] = None
    is_deform: bool = True
    bone_type: str = BoneType.SPINE.value
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MMDBone':
        """Create from dictionary (e.g., from JSON)."""
        return cls(**data)


@dataclass
class UnmappedBone:
    """Tracking information for a bone that couldn't be automatically mapped.

    Attributes:
        xps_name: XPS bone name that couldn't be mapped
        bone_type: Classification of this unmapped bone
        vertex_group_count: Number of vertex groups affected
        weight_percentage: Percentage of total mesh weight affected
        parent_xps: Parent bone in XPS hierarchy
        suggestions: List of suggested MMD bones to map to
        reason: Why this bone couldn't be automatically mapped
        user_mapped_to: What MMD bone the user manually mapped this to (if any)
    """
    xps_name: str
    bone_type: str = BoneType.CONTROL.value
    vertex_group_count: int = 0
    weight_percentage: float = 0.0  # 0~100
    parent_xps: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)  # Suggested MMD bone names
    reason: str = ""  # Explanation of why it couldn't be mapped
    user_mapped_to: Optional[str] = None  # User's manual mapping choice
    user_notes: str = ""  # User notes about this mapping decision
    is_ignored: bool = False  # Whether user chose to ignore this bone

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnmappedBone':
        """Create from dictionary (e.g., from JSON)."""
        return cls(**data)


@dataclass
class WeightRepairStrategy:
    """A suggested strategy for repairing weights of an unmapped bone.

    Attributes:
        unmapped_bone: XPS bone name that needs weight repair
        target_bones: List of (MMD bone name, transfer ratio) tuples
        strategy_type: Type of repair (parent_transfer, sibling_transfer, geometric_distance, delete)
        reasoning: Explanation of why this strategy is recommended
        expected_weight_loss: Expected percentage of weights that might be lost (0~100)
        confidence: Confidence in this strategy (0~1)
    """
    unmapped_bone: str
    target_bones: List[Tuple[str, float]] = field(default_factory=list)  # (bone_name, ratio)
    strategy_type: str = "parent_transfer"  # parent_transfer, sibling_transfer, geometric_distance, delete
    reasoning: str = ""
    expected_weight_loss: float = 0.0  # 0~100
    confidence: float = 0.5  # 0~1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert target_bones list of tuples to list of lists for JSON compatibility
        if self.target_bones:
            data['target_bones'] = [list(t) for t in self.target_bones]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeightRepairStrategy':
        """Create from dictionary (e.g., from JSON)."""
        data = data.copy()
        # Convert target_bones back to tuples
        if 'target_bones' in data:
            data['target_bones'] = [tuple(t) for t in data['target_bones']]
        return cls(**data)


@dataclass
class ValidationResult:
    """Results of mapping validation.

    Attributes:
        is_valid: Whether the mapping is valid
        parent_issues: Dict of bone_name -> parent mismatch details
        unmapped_issues: List of unmapped bones that should be mapped
        weight_issues: List of potential weight problems
        messages: Detailed validation messages
    """
    is_valid: bool = True
    parent_issues: Dict[str, dict] = field(default_factory=dict)
    unmapped_issues: List[str] = field(default_factory=list)
    weight_issues: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """Create from dictionary (e.g., from JSON)."""
        return cls(**data)


@dataclass
class MappingConfiguration:
    """Complete mapping configuration for a conversion session.

    Attributes:
        name: Configuration name
        version: Configuration version
        source_skeleton_type: Type of source skeleton (e.g., "xps_standard", "xps_female")
        bone_mappings: Dict of XPS name -> BoneMapping (includes both mapped and unmapped)
        unmapped_bones: List of UnmappedBone for bones that couldn't be mapped
        weight_repair_strategies: List of suggested weight repair strategies
        weight_rules: List of weight transfer rules (in execution order)
        ik_chains: Dict of chain name -> list of bone names
        bone_groups: Dict of group name -> list of bone names
        validation_status: Validation results
        mmd_skeleton: Reference to MMD standard skeleton (for validation)
    """
    name: str
    version: str = "1.0"
    source_skeleton_type: str = "xps_standard"
    bone_mappings: Dict[str, BoneMapping] = field(default_factory=dict)
    unmapped_bones: List[UnmappedBone] = field(default_factory=list)
    weight_repair_strategies: List[WeightRepairStrategy] = field(default_factory=list)
    weight_rules: List[WeightMappingRule] = field(default_factory=list)
    ik_chains: Dict[str, List[str]] = field(default_factory=dict)
    bone_groups: Dict[str, List[str]] = field(default_factory=dict)
    validation_status: Dict[str, Any] = field(default_factory=dict)
    mmd_skeleton: Optional[Dict[str, MMDBone]] = None  # Reference to MMD standard bones
    missing_mmd_bones: Dict[str, Any] = field(default_factory=dict)  # Missing MMD bones detected by bone detection

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'source_skeleton_type': self.source_skeleton_type,
            'bone_mappings': {
                k: v.to_dict() if isinstance(v, BoneMapping) else v
                for k, v in self.bone_mappings.items()
            },
            'unmapped_bones': [
                u.to_dict() if isinstance(u, UnmappedBone) else u
                for u in self.unmapped_bones
            ],
            'weight_repair_strategies': [
                s.to_dict() if isinstance(s, WeightRepairStrategy) else s
                for s in self.weight_repair_strategies
            ],
            'weight_rules': [
                r.to_dict() if isinstance(r, WeightMappingRule) else r
                for r in self.weight_rules
            ],
            'ik_chains': self.ik_chains,
            'bone_groups': self.bone_groups,
            'validation_status': self.validation_status,
            'missing_mmd_bones': self.missing_mmd_bones,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MappingConfiguration':
        """Create from dictionary (e.g., from JSON)."""
        data = data.copy()

        # Convert bone_mappings
        if 'bone_mappings' in data:
            bone_mappings_data = data['bone_mappings']
            bone_mappings = {}
            for k, v in bone_mappings_data.items():
                bone_mappings[k] = BoneMapping.from_dict(v) if isinstance(v, dict) else v
            data['bone_mappings'] = bone_mappings

        # Convert unmapped_bones
        if 'unmapped_bones' in data:
            unmapped_bones_data = data['unmapped_bones']
            unmapped_bones = []
            for v in unmapped_bones_data:
                unmapped_bones.append(UnmappedBone.from_dict(v) if isinstance(v, dict) else v)
            data['unmapped_bones'] = unmapped_bones

        # Convert weight_repair_strategies
        if 'weight_repair_strategies' in data:
            strategies_data = data['weight_repair_strategies']
            strategies = []
            for v in strategies_data:
                strategies.append(WeightRepairStrategy.from_dict(v) if isinstance(v, dict) else v)
            data['weight_repair_strategies'] = strategies

        # Convert weight_rules
        if 'weight_rules' in data:
            weight_rules_data = data['weight_rules']
            weight_rules = []
            for v in weight_rules_data:
                weight_rules.append(WeightMappingRule.from_dict(v) if isinstance(v, dict) else v)
            data['weight_rules'] = weight_rules

        # Remove mmd_skeleton from data if present (it's derived, not serialized)
        data.pop('mmd_skeleton', None)

        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'MappingConfiguration':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, filepath: str) -> 'MappingConfiguration':
        """Load configuration from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

    def validate_parent_relationships(self) -> ValidationResult:
        """Validate that parent-child relationships are correctly mapped.

        Checks if the parent mapping relationship in XPS matches the parent mapping in MMD.

        Returns:
            ValidationResult with parent_issues populated
        """
        result = ValidationResult()

        # Build XPS name -> mapping lookup
        xps_to_mapping = {m.xps_name: m for m in self.bone_mappings.values()}

        for xps_name, mapping in self.bone_mappings.items():
            if mapping.is_unmapped:
                continue

            # If this bone has a parent in XPS
            if mapping.parent_xps and mapping.parent_xps in xps_to_mapping:
                parent_mapping = xps_to_mapping[mapping.parent_xps]
                expected_parent_mmd = parent_mapping.mmd_name

                # Check if parent_mmd matches expected
                if mapping.parent_mmd != expected_parent_mmd:
                    result.parent_issues[xps_name] = {
                        'parent_xps': mapping.parent_xps,
                        'parent_mmd_expected': expected_parent_mmd,
                        'parent_mmd_actual': mapping.parent_mmd,
                        'message': f"Parent mismatch: expected '{expected_parent_mmd}', got '{mapping.parent_mmd}'"
                    }
                    result.is_valid = False
                    result.messages.append(f"⚠️ {xps_name}: {result.parent_issues[xps_name]['message']}")
            elif mapping.parent_xps:
                # Parent XPS bone not found in mapping
                result.parent_issues[xps_name] = {
                    'parent_xps': mapping.parent_xps,
                    'message': f"Parent XPS bone '{mapping.parent_xps}' not found in mapping"
                }
                result.is_valid = False
                result.messages.append(f"⚠️ {xps_name}: Parent bone not found")

        return result

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the mapping configuration.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check IK chains validity
        for chain_name, bones in self.ik_chains.items():
            if not bones:
                errors.append(f"IK chain '{chain_name}' is empty")
            for bone in bones:
                if bone not in [m.mmd_name for m in self.bone_mappings.values()]:
                    errors.append(f"IK chain '{chain_name}' references unmapped bone '{bone}'")

        # Check bone groups validity
        for group_name, bones in self.bone_groups.items():
            if not bones:
                errors.append(f"Bone group '{group_name}' is empty")
            for bone in bones:
                if bone not in [m.mmd_name for m in self.bone_mappings.values()]:
                    errors.append(f"Bone group '{group_name}' references unmapped bone '{bone}'")

        # Check weight rules
        for rule in self.weight_rules:
            if rule.source_bone and rule.source_bone not in self.bone_mappings:
                errors.append(f"Weight rule references unmapped source bone '{rule.source_bone}'")
            if rule.target_bone not in [m.mmd_name for m in self.bone_mappings.values()]:
                errors.append(f"Weight rule references unmapped target bone '{rule.target_bone}'")

        # Validate parent relationships
        parent_validation = self.validate_parent_relationships()
        if not parent_validation.is_valid:
            errors.extend([m['message'] for m in parent_validation.parent_issues.values()])

        self.validation_status = {
            'is_valid': len(errors) == 0,
            'error_count': len(errors),
            'errors': errors
        }

        return len(errors) == 0, errors

    def count_unmapped_bones(self) -> int:
        """Count the number of unmapped bones."""
        return len(self.unmapped_bones)

    def count_affected_vertices_from_unmapped(self) -> Tuple[int, float]:
        """Count total vertex groups affected by unmapped bones.

        Returns:
            (total_vertex_group_count, total_weight_percentage)
        """
        total_count = sum(u.vertex_group_count for u in self.unmapped_bones)
        total_weight = sum(u.weight_percentage for u in self.unmapped_bones)
        return total_count, total_weight
