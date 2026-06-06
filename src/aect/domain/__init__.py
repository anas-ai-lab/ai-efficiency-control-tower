"""AECT Domain-Schicht — öffentliche API.

Hexagonal Architecture: Die Domain-Schicht ist die innerste Schicht.
Erlaubte Imports: Standard-Library, Pydantic.
Verbotene Imports: aect.adapters, aect.application (würde Dependency Inversion verletzen).
"""

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
)

__all__ = [
    "AdoptionType",
    "CompositeScore",  # neu
    "DataClassification",
    "EmployeeCategory",
    "EvidenceLevel",
    "FilterResult",  # neu
    "FrequencyUnit",
    "ImplementationApproach",
    "ROIConfig",
    "ROIResult",
    "UseCaseInput",
    "apply_prefilter",  # neu
    "calculate_roi",
    "compute_composite_score",  # neu
    "load_roi_config",
]
