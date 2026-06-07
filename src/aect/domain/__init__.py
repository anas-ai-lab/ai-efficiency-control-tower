"""AECT Domain-Schicht — öffentliche API.

Hexagonal Architecture: Die Domain-Schicht ist die innerste Schicht.
Erlaubte Imports: Standard-Library, Pydantic.
Verbotene Imports: aect.adapters, aect.application (würde Dependency
Inversion verletzen).
"""

from aect.domain.feasibility import (
    FeasibilityChecker,
    FeasibilityFlag,
    FeasibilityResult,
)
from aect.domain.filters import FilterResult, apply_prefilter
from aect.domain.models import UseCaseInput
from aect.domain.roi import ROIConfig, ROIResult, calculate_roi, load_roi_config
from aect.domain.scoring import CompositeScore, compute_composite_score
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    FrequencyUnit,
    ImplementationApproach,
    TriageZone,
)
from aect.domain.zones import ZoneClassifier, ZoneResult, load_zone_classifier

__all__ = [
    # types
    "AdoptionType",
    # scoring
    "CompositeScore",
    "DataClassification",
    "EmployeeCategory",
    "EvidenceLevel",
    # feasibility
    "FeasibilityChecker",
    "FeasibilityFlag",
    "FeasibilityResult",
    # filters
    "FilterResult",
    "FrequencyUnit",
    "ImplementationApproach",
    # roi
    "ROIConfig",
    "ROIResult",
    "TriageZone",
    # models
    "UseCaseInput",
    # zones
    "ZoneClassifier",
    "ZoneResult",
    "apply_prefilter",
    "calculate_roi",
    "compute_composite_score",
    "load_roi_config",
    "load_zone_classifier",
]
