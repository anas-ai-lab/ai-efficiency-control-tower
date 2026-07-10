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
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class InvalidLLMOutputError(Exception):
    """LLM-Antwort ist kein valides JSON oder verletzt das Ziel-Schema.

    Wird von parse_structured_llm_output() geworfen -- ein
    pydantic.ValidationError oder json.JSONDecodeError wird nie direkt nach
    aussen durchgereicht (einheitlicher Fehlertyp fuer Aufrufer, Exceptions
    statt Result-Pattern, Master-Plan v3.1 Phase B).
    """


class CaseField(StrEnum):
    """Bezugsfeld eines Verbesserungsvorschlags (V4, Hebel-Pflicht).

    Werte = exakte UseCaseInput-Feldnamen (domain/models.py) -- so kann das
    Frontend (V4-P7) einen Vorschlag direkt einem Formularfeld zuordnen und der
    Prompt kann die erlaubten Werte aufzaehlen. Ein Vorschlag muss benennen,
    WELCHES Feld er betrifft (kein generischer Beratungssatz ohne Feldbezug).

    Kein Config-Key -> gehoert NICHT in domain/types.py (dort liegt der StrEnum-
    Anker ausschliesslich fuer TOML-Config-Keys, siehe SketchNodeKind). Teil des
    LLM-Output-Schemas, lebt daher bei den uebrigen Schema-Typen.
    """

    TITLE = "title"
    CURRENT_STATE = "current_state"
    DESIRED_STATE = "desired_state"
    EXAMPLE_PROCESS = "example_process"
    DESIRED_EXAMPLE_PROCESS = "desired_example_process"
    TIME_SAVINGS = "time_savings_hours_per_case"
    FREQUENCY = "frequency_per_year"
    AFFECTED_EMPLOYEES = "affected_employees_count"
    EMPLOYEE_CATEGORY = "employee_category"
    EVIDENCE_LEVEL = "evidence_level"
    ADOPTION_TYPE = "adoption_type"
    IMPLEMENTATION_APPROACH = "implementation_approach"
    IMPLEMENTATION_COMPLEXITY = "implementation_complexity"
    ESTIMATED_LICENSE_COST = "estimated_license_cost_eur"
    IMPLEMENTATION_COST = "implementation_cost_eur"
    DATA_CLASSIFICATION = "data_classification"
    NOTES = "notes"


class ImprovementSuggestion(BaseModel):
    """Ein Verbesserungsvorschlag mit Feldbezug und Hebel (V4).

    Ersetzt die frueheren generischen Beratungs-Floskeln (freier String). Jeder
    Vorschlag muss dreiteilig sein:
      bezugsfeld: welches Case-Feld er betrifft (CaseField),
      vorschlag:  die konkrete, umsetzbare Massnahme,
      hebel:      welche Bewertungsgroesse sich wie veraendert (z. B.
                  "Evidenzfaktor steigt von 0,40 auf 0,90").

    Fehlt bezugsfeld oder hebel, ist das ein Schema-Fehler -- die Retry-/Fail-
    Mechanik in sharpen_case() (application/service.py) greift dann analog zum
    Zahlen-Guard.

    extra="forbid"/frozen=True analog den uebrigen Schema-Typen.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    bezugsfeld: CaseField
    vorschlag: str = Field(min_length=5, max_length=500)
    hebel: str = Field(min_length=5, max_length=300)


class SharpenedContentV2(BaseModel):
    """Strukturierte Schaerfung (ADR-0013 Teil 2, erweitert V4).

    Feld-Bounds orientieren sich an UseCaseInput (domain/models.py):
    sharpened_title analog title (5-200), sharpened_current_state/
    sharpened_desired_state analog current_state/desired_state (30-2000).

    improvement_suggestions: max. 3 Eintraege (V4, Hebel-Pflicht -- Fokus statt
    Floskel-Liste), je ein ImprovementSuggestion mit bezugsfeld/vorschlag/hebel.

    extra="forbid": unerwartete Felder im LLM-Output sind ein
    Validierungsfehler, kein stiller Datenverlust (OWASP LLM10).
    frozen=True: analog SharpenedUseCase -- nach Validierung unveraenderlich.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    sharpened_title: str = Field(min_length=5, max_length=200)
    sharpened_current_state: str = Field(min_length=30, max_length=2000)
    sharpened_desired_state: str = Field(min_length=30, max_length=2000)
    improvement_suggestions: list[ImprovementSuggestion] = Field(
        min_length=1, max_length=3
    )


_OpenQuestion = Annotated[str, Field(min_length=5, max_length=200)]


class IdeationDraft(BaseModel):
    """Ein einzelner AI-Use-Case-Entwurf aus einer Problembeschreibung (P10).

    Erzeugt von generate_ideation() fuer einen internen Intake, aus einer
    vagen Problembeschreibung. Bewusst unvollstaendig: die qualitativen Felder
    tragen die EXAKTEN UseCaseInput-Feldnamen (domain/models.py) --
    current_state/desired_state/example_process -- damit ein Entwurf spaeter
    ohne Feld-Umbenennung in ein UseCaseInput-Formular uebernommen werden kann.
    title analog UseCaseInput.title, hier aber max 120 (kuerzere Entwurfs-
    Titel), current_state/desired_state/example_process analog den
    UseCaseInput-Bounds.

    Zahlen-Regel (D17, ADR-0048): quantitative Angaben werden NICHT erfunden.
    Statt eines Ziffern-Regex-Validators (zu fehleranfaellig -- legitime
    Ziffern in Systemnamen wie "SAP S/4") ist die Regel doppelt gesichert:
    (a) Prompt-Instruktion (prompts/ideation/v1), (b) P14 befuellt die
    quantitativen Intake-Felder grundsaetzlich nicht vor. open_questions
    traegt die quantitativen Luecken, die der Einreicher schliessen muss.

    extra="forbid": unerwartete Felder im LLM-Output sind ein
    Validierungsfehler (OWASP LLM10). frozen=True: nach Validierung
    unveraenderlich (analog SharpenedContentV2).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=5, max_length=120)
    current_state: str = Field(min_length=20, max_length=2000)
    desired_state: str = Field(min_length=20, max_length=2000)
    example_process: str = Field(min_length=20, max_length=2000)
    rationale: str = Field(min_length=10, max_length=600)
    open_questions: list[_OpenQuestion] = Field(min_length=1, max_length=8)


class IdeationResult(BaseModel):
    """1 bis 3 Use-Case-Entwuerfe aus einer Problembeschreibung (P10, ADR-0048).

    max_length=3 begrenzt die Entwurfszahl gegen Token-Flooding (LLM10) und
    haelt den Intake fokussiert. extra="forbid"/frozen=True analog
    IdeationDraft.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    drafts: list[IdeationDraft] = Field(min_length=1, max_length=3)


class SketchNodeKind(StrEnum):
    """Bausteintyp eines Architektur-Skizzen-Knotens (P11, Vertrag Paragraph 3.7).

    Bewusst genau fuenf generische Typen -- keine firmenspezifische Terminologie
    (IP-Regel SDR-0002 Paragraph 5). Jeder Typ bestimmt die Mermaid-Knotenform
    im deterministischen Builder (application/mermaid.py): user=Stadium,
    system=Rechteck, ai_service=Hexagon, data_store=Zylinder, external=Subroutine.

    Kein Config-Key -> gehoert NICHT in domain/types.py (dort liegt der StrEnum-
    Anker ausschliesslich fuer TOML-Config-Keys). Dieses Enum ist Teil des
    LLM-Output-Schemas und lebt daher bei den uebrigen Schema-Typen.
    """

    USER = "user"
    SYSTEM = "system"
    AI_SERVICE = "ai_service"
    DATA_STORE = "data_store"
    EXTERNAL = "external"


# Node-IDs sind Mermaid-Bezeichner: kleingeschrieben, alphanumerisch + Unterstrich,
# 1-24 Zeichen. Bewusst eng -- so kann keine Node-ID Mermaid-Syntax einschleusen
# (die ID steht unescaped links vor der Knotenform, anders als das Label).
_NODE_ID_PATTERN = r"^[a-z0-9_]{1,24}$"


class SketchNode(BaseModel):
    """Ein Knoten der Architektur-Skizze (P11).

    id: Mermaid-Bezeichner (Pattern _NODE_ID_PATTERN). label: Anzeigetext,
    1-60 Zeichen -- wird im Builder escaped, bevor er in die Mermaid-Form geht.
    kind: einer der fuenf SketchNodeKind-Typen.

    extra="forbid": unerwartete Felder im LLM-Output sind ein Validierungsfehler
    (OWASP LLM10). frozen=True: nach Validierung unveraenderlich.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=_NODE_ID_PATTERN)
    label: str = Field(min_length=1, max_length=60)
    kind: SketchNodeKind


class SketchEdge(BaseModel):
    """Eine gerichtete Kante zwischen zwei Knoten der Architektur-Skizze (P11).

    source/target: Node-IDs (Pattern _NODE_ID_PATTERN) -- die Referenz-Integritaet
    (beide zeigen auf existierende Knoten) prueft der Model-Validator von
    ArchitectureSketch, nicht der einzelne Kanten-Typ. label: optionale
    Kantenbeschriftung, max 60 Zeichen -- ebenfalls im Builder escaped.

    extra="forbid"/frozen=True analog SketchNode.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str = Field(pattern=_NODE_ID_PATTERN)
    target: str = Field(pattern=_NODE_ID_PATTERN)
    label: str | None = Field(default=None, max_length=60)


class ArchitectureSketch(BaseModel):
    """Strukturierter Architektur-Graph aus einem Loesungsvorschlag (P11, D18).

    Das LLM emittiert NIE Mermaid-Syntax, nur dieses Graph-JSON -- der
    deterministische Builder (application/mermaid.py) erzeugt daraus die
    Mermaid-Zeichenkette. Das eliminiert die Syntaxfehler-Klasse und minimiert
    die Injection-Flaeche (ADR-0049).

    nodes: 2-10 Knoten (bewusst begrenzt -- eine Skizze, kein vollstaendiges
    Architekturbild). edges: 0-15 Kanten. Der Model-Validator erzwingt zwei
    Invarianten, die einzelne Felder nicht sehen: Node-IDs sind eindeutig, und
    jede Kante referenziert existierende Knoten -- sonst ValidationError (kein
    500, die Route mappt auf 502 wie bei jedem anderen kaputten LLM-Output).

    extra="forbid"/frozen=True analog SketchNode/SketchEdge.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    nodes: list[SketchNode] = Field(min_length=2, max_length=10)
    edges: list[SketchEdge] = Field(max_length=15)

    @model_validator(mode="after")
    def _check_referential_integrity(self) -> ArchitectureSketch:
        """Node-IDs eindeutig; jede Kante referenziert existierende IDs."""
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("node ids must be unique")
        id_set = set(ids)
        for edge in self.edges:
            if edge.source not in id_set:
                raise ValueError(f"edge references unknown node id: {edge.source}")
            if edge.target not in id_set:
                raise ValueError(f"edge references unknown node id: {edge.target}")
        return self


def _extract_json_object(raw: str) -> str:
    """Extrahiert den JSON-Objekt-Anteil aus einer LLM-Antwort (H-021).

    Toleriert Markdown-Fences (```json ... ```) und erklaerenden Text vor/nach
    dem Objekt, indem auf den Bereich vom ERSTEN '{' bis zum LETZTEN '}'
    geschnitten wird. Findet sich kein Objekt-Bereich, wird der Rohtext
    unveraendert zurueckgegeben -- der nachfolgende json.loads erzeugt dann die
    uebliche InvalidLLMOutputError (Verhalten wie zuvor).
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end > start:
        return raw[start : end + 1]
    return raw


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
        data = json.loads(_extract_json_object(raw))
    except json.JSONDecodeError as exc:
        raise InvalidLLMOutputError(f"LLM-Output ist kein valides JSON: {exc}") from exc

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        # Nur loc/type je Fehler aufnehmen -- NICHT str(exc)/input_value, das
        # LLM-Output-Fragmente (ggf. PII/Secrets) enthaelt und sonst ueber
        # Logs und die 502-Antwort leakt (OWASP LLM02, H-031). Der volle
        # ValidationError bleibt als __cause__ (from exc) fuer lokales Debugging.
        summary = "; ".join(
            f"{'.'.join(str(p) for p in err['loc']) or '<root>'}: {err['type']}"
            for err in exc.errors()
        )
        raise InvalidLLMOutputError(
            f"LLM-Output erfuellt das Schema {schema.__name__} nicht "
            f"({exc.error_count()} Fehler): {summary}"
        ) from exc
