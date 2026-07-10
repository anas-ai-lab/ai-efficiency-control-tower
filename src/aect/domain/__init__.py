"""AECT Domain-Schicht -- oeffentliche API.

Hexagonal Architecture: Die Domain-Schicht ist die innerste Schicht.
Erlaubte Imports: Standard-Library, Pydantic.
Verbotene Imports: aect.adapters, aect.application (wuerde Dependency
Inversion verletzen).
"""

from aect.domain.explainability import (
    ConfidenceReasoning,
    ScoreBreakdown,
    ScoreComponent,
    TriageExplanation,
    build_contra_points,
    build_zu_entscheiden,
    explain_triage,
)
from aect.domain.feasibility import (
    FeasibilityChecker,
    FeasibilityFlag,
    FeasibilityResult,
)
from aect.domain.filters import FilterResult, apply_prefilter
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import TriageResult, evaluate_use_case, handlungsdruck_score
from aect.domain.roi import ROIConfig, ROIResult, calculate_roi, load_roi_config
from aect.domain.routing import RoutingRecommendation, RoutingResult, route_use_case
from aect.domain.scoring import CompositeScore, compute_composite_score
from aect.domain.types import (
    AdoptionType,
    CaseStatus,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    ReviewerDecision,
    TriageZone,
)
from aect.domain.zones import ZoneClassifier, ZoneResult, load_zone_classifier

__all__ = [
    # types
    "AdoptionType",
    # lifecycle
    "CaseStatus",
    # scoring
    "CompositeScore",
    # explainability
    "ConfidenceReasoning",
    "Country",
    "DataClassification",
    "EmployeeCategory",
    "EvidenceLevel",
    # feasibility
    "FeasibilityChecker",
    "FeasibilityFlag",
    "FeasibilityResult",
    # filters
    "FilterResult",
    "ImplementationApproach",
    # roi
    "ROIConfig",
    "ROIResult",
    # routing
    "ReviewerDecision",
    "RoutingRecommendation",
    "RoutingResult",
    "ScoreBreakdown",
    "ScoreComponent",
    "TriageExplanation",
    "TriageResult",
    "TriageZone",
    # models
    "UseCaseInput",
    # zones
    "ZoneClassifier",
    "ZoneResult",
    "apply_prefilter",
    "build_contra_points",
    "build_zu_entscheiden",
    "calculate_roi",
    "compute_composite_score",
    "evaluate_use_case",
    "explain_triage",
    "handlungsdruck_score",
    "load_roi_config",
    "load_zone_classifier",
    "route_use_case",
]
