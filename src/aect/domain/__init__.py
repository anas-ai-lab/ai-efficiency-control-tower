"""AECT Domain-Schicht — öffentliche API.

Hexagonal Architecture: Die Domain-Schicht ist die innerste Schicht.
Erlaubte Imports: Standard-Library, Pydantic.
Verbotene Imports: aect.adapters, aect.application (würde Dependency Inversion verletzen).
"""

from aect.domain.models import UseCaseInput
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
    "DataClassification",
    "EmployeeCategory",
    "EvidenceLevel",
    "FrequencyUnit",
    "ImplementationApproach",
    "UseCaseInput",
]
