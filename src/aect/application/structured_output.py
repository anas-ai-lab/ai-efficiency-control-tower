"""Strukturierte LLM-Output-Validierung (ADR-0013, Teil 1/2).

Schicht: application -- importiert aus pydantic, Python stdlib.
Importiert NICHT aus aect.adapters.

Security (aect-security-checklist v2.1, Phase C, Permanente Regel 3):
LLM-Output wird immer als untrusted behandelt. parse_structured_llm_output()
validiert einen rohen JSON-String gegen ein striktes Pydantic-Schema
(extra="forbid", max_length auf allen Feldern) und wirft
InvalidLLMOutputError bei Verstoss, statt fehlerhafte Daten durchzulassen.

Verdrahtet (ADR-0013 Teil 2): SharpenedContentV2 wird von sharpen_case()
(application/service.py) gegen die rohe LLM-Antwort validiert. Bei Verstoss
Graceful Degradation auf raw_text statt Crash -- kein Fallback auf
ungepruefte strukturierte Felder.
"""

from __future__ import annotations

import json
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class InvalidLLMOutputError(Exception):
    """LLM-Antwort ist kein valides JSON oder verletzt das Ziel-Schema.

    Wird von parse_structured_llm_output() geworfen -- ein
    pydantic.ValidationError oder json.JSONDecodeError wird nie direkt nach
    aussen durchgereicht (einheitlicher Fehlertyp fuer Aufrufer, Exceptions
    statt Result-Pattern, Master-Plan v3.1 Phase B).
    """


_ImprovementSuggestion = Annotated[str, Field(min_length=5, max_length=500)]


class SharpenedContentV2(BaseModel):
    """Strukturierte Schaerfung (ADR-0013, Teil 1/2 -- noch nicht verdrahtet).

    Ersetzt perspektivisch SharpenedUseCase.sharpened_text: str (Teil 2,
    Breaking Change auf SubmittedCase/SQLite/API-Response, eigener Tag).

    Feld-Bounds orientieren sich an UseCaseInput (domain/models.py):
    sharpened_title analog title (5-200), sharpened_current_state/
    sharpened_desired_state analog current_state/desired_state (30-2000).

    improvement_suggestions deckt die Projekt-Anforderung ("konkrete
    Verbesserungsvorschlaege") ab -- max_length=10 begrenzt die Liste selbst
    gegen Token-Flooding (LLM10), je 5-500 Zeichen pro Eintrag.

    extra="forbid": unerwartete Felder im LLM-Output sind ein
    Validierungsfehler, kein stiller Datenverlust (OWASP LLM10).
    frozen=True: analog SharpenedUseCase -- nach Validierung unveraenderlich.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    sharpened_title: str = Field(min_length=5, max_length=200)
    sharpened_current_state: str = Field(min_length=30, max_length=2000)
    sharpened_desired_state: str = Field(min_length=30, max_length=2000)
    improvement_suggestions: list[_ImprovementSuggestion] = Field(
        min_length=1, max_length=10
    )


def parse_structured_llm_output[T: BaseModel](raw: str, schema: type[T]) -> T:
    """Validiert einen rohen LLM-Output-String gegen ein Pydantic-Schema.

    Args:
        raw: Roher String aus LLMResponse.content -- als untrusted behandelt
            (aect-security-checklist v2.1).
        schema: Ziel-Pydantic-Modell (z. B. SharpenedContentV2).

    Returns:
        Validierte Instanz von `schema`.

    Raises:
        InvalidLLMOutputError: `raw` ist kein valides JSON, oder das JSON
            verletzt `schema` (fehlendes Pflichtfeld, falscher Typ,
            unbekanntes Feld, Laengenverstoss).
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidLLMOutputError(f"LLM-Output ist kein valides JSON: {exc}") from exc

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise InvalidLLMOutputError(
            f"LLM-Output erfuellt das Schema {schema.__name__} nicht: {exc}"
        ) from exc
