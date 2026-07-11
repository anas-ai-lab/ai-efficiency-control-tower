"""TriageService -- Application Service fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt), aect.application.ports (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog

from aect.application.cost_logger import log_llm_cost
from aect.application.mermaid import build_mermaid
from aect.application.models import (
    ArchitectureSketchResult,
    AufwandKennzahl,
    BusinessSummary,
    ComplianceCitation,
    ComplianceHintsResult,
    DecisionDetails,
    DecisionKennzahlen,
    DecisionReport,
    MonitoringEntry,
    PortfolioStats,
    ReportResult,
    SharpenedUseCase,
    SimilarityPair,
    SimilarityPairsResult,
    SimilarityWarning,
    SolutionProposal,
    SubmittedCase,
    TechnicalDetail,
    TechnicalReport,
)
from aect.application.ports.clock import ClockPort
from aect.application.ports.embedder import EmbedderPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.llm import LLMMessage, LLMPort
from aect.application.ports.pii_redactor import PIIRedactorPort
from aect.application.ports.repository import RepositoryPort
from aect.application.ports.retriever import RetrievedChunk, RetrieverPort
from aect.application.prompts import load_prompt
from aect.application.sanitization import (
    detect_injection_patterns,
    neutralize_delimiters,
)
from aect.application.structured_output import (
    ArchitectureSketch,
    IdeationResult,
    InvalidLLMOutputError,
    SharpenedContentV2,
    SolutionProposalV2,
    parse_structured_llm_output,
)
from aect.application.tools import (
    TOOL_DEFINITIONS,
    UnknownToolError,
    dispatch_tool_call,
)
from aect.domain import (
    CaseStatus,
    EvidenceLevel,
    ReviewerDecision,
    ROIConfig,
    TriageExplanation,
    TriageResult,
    UseCaseInput,
    ZoneClassifier,
    build_contra_points,
    build_zu_entscheiden,
    evaluate_use_case,
    explain_triage,
    load_zone_classifier,
)
from aect.domain.explainability import (
    ADOPTION_LABELS,
    COMPOSITE_MAX_TOTAL,
    DATA_CLASSIFICATION_CLARTEXT,
    EVIDENCE_LABELS,
    ZONE_LABELS,
)
from aect.domain.sharpening_guard import build_allowlist, find_violations
from aect.domain.solution_guard import find_vocabulary_violations

# Canonical Retrieval-Queries fuer Compliance-Hinweise (ADR-0024). Bewusst
# fest, nicht aus Use-Case-Freitext abgeleitet -- vermeidet jede
# Injection-Flaeche im Retrieval-Pfad selbst (anders als sharpen_case/
# propose_solution, wo Nutzereingabe in den Prompt fliesst).
_DSFA_QUERY = "Datenschutz-Folgenabschaetzung personenbezogene Daten Risiko"
_TRANSPARENCY_QUERY = "Transparenzpflicht KI-System Offenlegung"

# Fail loud statt stiller Mock-Fallback (CLAUDE.md). Chunks aus dem
# synthetischen MockRetriever tragen einen "mock-"-praefigierten source_id. Sie
# duerfen NIE als echte Quelle in einer Compliance-Citation erscheinen -- taucht
# ein solcher Chunk auf, ist die echte Wissensbasis nicht verdrahtet
# (AECT_CHROMA_HOST leer -> resolve_retriever() faellt auf MockRetriever zurueck).
# Dann liefert der Compliance-Teil eine ehrliche "nicht verfuegbar"-Antwort statt
# Mock-Zitaten. Mock-Fixtures sind ausschliesslich in Tests zulaessig.
_MOCK_SOURCE_PREFIX = "mock-"
_KB_UNAVAILABLE_HINT = (
    "Wissensbasis nicht verfuegbar -- keine belegten Compliance-Hinweise moeglich."
)

# Dedup-Schwellen (L-3, ADR-0039). Generische Cosinus-Aehnlichkeitsgrenzen,
# KEINE firmenspezifischen Werte (anders als ROI-/Zonen-Schwellen in config/):
# Standardwerte fuer semantische Embedding-Aehnlichkeit, methodisch zeigbar.
_DEDUP_THRESHOLD_AWARENESS = 0.75  # ab hier: Hinweis "Aehnliches existiert"
_DEDUP_THRESHOLD_COMBINE = 0.90  # ab hier zusaetzlich: "zusammenlegen?"


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosinus-Aehnlichkeit zweier Vektoren in [-1.0, 1.0] (manuell, kein numpy).

    Skaleninvariant (normiert auf die Vektorlaengen) -- daher robuster als ein
    reines Skalarprodukt. Defensive Rueckgabe 0.0 bei Laengen-Mismatch oder
    Nullvektor (keine Aehnlichkeit definierbar).
    """
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _flag_injection_in_fields(
    fields: dict[str, str], **log_context: object
) -> dict[str, list[str]]:
    """Prueft Freitextfelder auf Injection-Muster und loggt Treffer (OWASP LLM01).

    Zentrale Stelle fuer alle LLM-Pfade (sharpen/propose/compliance/sketch):
    FLAGGEN, nicht BLOCKEN -- Treffer werden geloggt (Feldname + Pattern-Namen,
    kein Body -- Logging-Allowlist), der Aufrufer laeuft trotzdem weiter. Frischer
    Logger pro Aufruf (kein Modul-globaler get_logger()) -- cache_logger_on_first_use
    wuerde capture_logs() in Tests an die falsche Prozessor-Kette binden (Tag 32).
    """
    detected: dict[str, list[str]] = {
        field_name: patterns
        for field_name, field_value in fields.items()
        if (patterns := detect_injection_patterns(field_value))
    }
    if detected:
        structlog.get_logger().warning(
            "injection_pattern_detected", fields=detected, **log_context
        )
    return detected


class CaseNotFoundError(Exception):
    """Angeforderte Case-ID existiert nicht (DSGVO-Loeschpfad, ADR-0038).

    Wird von delete_case() geworfen und in der DELETE-Route auf HTTP 404
    gemappt -- HTTP-Exceptions gehoeren in die Adapter-Schicht, nicht in den
    Application Service (Hexagonal, ADR-0004).
    """

    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case not found: {case_id}")
        self.case_id = case_id


class NoProposalForSketchError(Exception):
    """Architektur-Skizze angefordert, aber der Case hat keinen Loesungsvorschlag
    (P11, ADR-0049).

    generate_sketch() braucht proposal_text als Eingabe -- ohne ihn gibt es kein
    Beschreibungsmaterial fuer die Skizze. Eigener, typisierter Fehlerfall
    (nicht None wie "Case fehlt"), damit die Route ihn von 404 unterscheiden und
    auf 409 mappen kann (HTTP-Exceptions gehoeren in die Adapter-Schicht,
    ADR-0004).
    """

    def __init__(self, case_id: str) -> None:
        super().__init__(f"No proposal for sketch: {case_id}")
        self.case_id = case_id


class SharpeningNumberViolationError(Exception):
    """Die Schaerfung hat Zahlen erfunden, die nicht im Original stehen (V4).

    Wird von sharpen_case() geworfen, wenn der deterministische Zahlen-Guard
    (domain/sharpening_guard) auch NACH einem Korrektur-Retry noch Zahlen im
    geschaerften Text findet, die nicht in der Allowlist der Eingabe-Zahlen
    liegen. Die Route mappt auf HTTP 422 mit der Violation-Liste; nichts wird
    gespeichert (Projektregel "keine erfundenen Zahlen", Fail loud).
    """

    def __init__(self, case_id: str, violations: list[str]) -> None:
        super().__init__(
            f"Sharpening invented numbers not in the original ({case_id}): "
            + ", ".join(violations)
        )
        self.case_id = case_id
        self.violations = violations


class SolutionVocabularyViolationError(Exception):
    """Der Geschaeftsleitungs-Absatz nutzt verbotenes technisches Vokabular (V4-P6).

    Wird von propose_solution() geworfen, wenn der deterministische Vokabular-Guard
    (domain/solution_guard) auch NACH einem Korrektur-Retry noch Technik-/
    Architektur-Begriffe im solution_business-Absatz findet. Die Route mappt auf
    HTTP 422 mit der Violation-Liste; nichts wird gespeichert (Fail loud).
    """

    def __init__(self, case_id: str, violations: list[str]) -> None:
        super().__init__(
            f"Solution business paragraph uses forbidden technical vocabulary "
            f"({case_id}): " + ", ".join(violations)
        )
        self.case_id = case_id
        self.violations = violations


class NoSharpeningDraftError(Exception):
    """Draft-Aktion (accept/reject) angefordert, aber kein Draft vorhanden (V4).

    accept_sharpening()/reject_sharpening() setzen einen offenen
    sharpening_draft voraus. Fehlt er (nie geschaerft, oder bereits
    uebernommen/verworfen), ist das ein typisierter Fehlerfall -- von "Case
    fehlt" (None -> 404) unterschieden, damit die Route auf 409 mappen kann.
    """

    def __init__(self, case_id: str) -> None:
        super().__init__(f"No open sharpening draft: {case_id}")
        self.case_id = case_id


def _render_suggestion_line(suggestion: object) -> str:
    """Rendert einen Verbesserungsvorschlag als lesbare Zeile.

    Neue Form (V4): dict mit bezugsfeld/vorschlag/hebel -> "- vorschlag
    (Feld: bezugsfeld; Hebel: hebel)". Alt-Form (vor V4, reiner String in
    persistierten Cases) -> unveraendert als "- <string>" (Rueckwaerts-
    kompatibel fuer bereits gespeicherte sharpened_content_json).
    """
    if isinstance(suggestion, dict):
        vorschlag = suggestion.get("vorschlag", "")
        bezugsfeld = suggestion.get("bezugsfeld", "")
        hebel = suggestion.get("hebel", "")
        return f"- {vorschlag} (Feld: {bezugsfeld}; Hebel: {hebel})"
    return f"- {suggestion}"


def _render_sharpened_content(content_json: str | None) -> str | None:
    """Rendert den persistierten Schaerfungs-Inhalt zu lesbarem Text.

    Reine Regel-Schicht (ADR-0011: kein LLM-Call). content_json ist entweder
    None (sharpen_case() lief nie fuer diesen Case), ein Graceful-
    Degradation-JSON (raw_text gesetzt, ADR-0013 Teil 2) oder ein valides
    SharpenedContentV2-JSON (strukturierte Felder gesetzt).
    """
    if content_json is None:
        return None
    data = json.loads(content_json)
    # raw_text: Rueckwaerts-kompatibel fuer vor V4 persistierte Graceful-
    # Degradation-Cases (der neue Fail-loud-Pfad schreibt nie mehr raw_text).
    if data.get("raw_text") is not None:
        return str(data["raw_text"])
    lines = [
        f"Titel: {data['sharpened_title']}",
        f"Ist-Zustand: {data['sharpened_current_state']}",
        f"Soll-Zustand: {data['sharpened_desired_state']}",
        "Verbesserungsvorschlaege:",
    ]
    lines += [_render_suggestion_line(s) for s in data["improvement_suggestions"]]
    return "\n".join(lines)


def _render_compliance_hints(
    content_json: str | None,
) -> tuple[str | None, tuple[ComplianceCitation, ...]]:
    """Rendert die persistierten Compliance-Hinweise zu Anzeige-Daten.

    Reine Regel-Schicht (ADR-0026: kein LLM-Call). content_json ist
    entweder None (generate_compliance_hints() lief nie fuer diesen Case)
    oder ein JSON-Objekt mit hint_text (str | None) und citations (Liste
    von Citation-Dicts) -- analog zu _render_sharpened_content().

    hint_text ist None sowohl wenn generate_compliance_hints() nie lief
    als auch wenn es lief, aber das Retrieval keine Treffer hatte (Graceful
    Degradation, ADR-0024) -- beide Faelle sind fuer den Report-Konsumenten
    aequivalent: kein Hinweis anzuzeigen.
    """
    if content_json is None:
        return None, ()
    data = json.loads(content_json)
    hint_text = data.get("hint_text")
    citations = tuple(
        ComplianceCitation(
            number=int(c["number"]),
            source_id=str(c["source_id"]),
            citation=str(c["citation"]),
            url=c.get("url"),
        )
        for c in data.get("citations", [])
    )
    return hint_text, citations


def _build_kennzahlen(result: TriageResult) -> DecisionKennzahlen:
    """Harte Kennzahlen des Entscheider-Reports (None bei Vorfilter-Fail)."""
    if result.zone is None or result.roi is None or result.composite is None:
        return DecisionKennzahlen(
            netto_eur=None, stunden_pro_jahr=None, aufwand=None, zone_label=None
        )
    return DecisionKennzahlen(
        netto_eur=float(result.roi.net_expected_benefit_eur),
        stunden_pro_jahr=result.roi.hours_per_year,
        aufwand=AufwandKennzahl(
            wert=result.composite.total,
            max=COMPOSITE_MAX_TOTAL,
            label=result.composite.effort_label,
        ),
        zone_label=ZONE_LABELS[result.zone.final_zone],
    )


def _build_decision_report(
    result: TriageResult,
    use_case: UseCaseInput,
    explanation: TriageExplanation,
    sharpened_text: str | None,
    solution_business: str | None,
    compliance_hint_text: str | None,
) -> DecisionReport:
    """Baut den Entscheider-Report v2 aus TriageResult + Erklaerbarkeit (V4-P6)."""
    return DecisionReport(
        empfehlung_satz=explanation.recommendation_text,
        kennzahlen=_build_kennzahlen(result),
        zu_entscheiden=build_zu_entscheiden(result),
        contra_punkte=build_contra_points(
            result, use_case, confidence=explanation.confidence
        ),
        details=DecisionDetails(
            sharpened_text=sharpened_text,
            solution_business=solution_business,
            compliance_hint_text=compliance_hint_text,
        ),
    )


def _build_technical_report(
    result: TriageResult, use_case: UseCaseInput, solution_technical: str | None
) -> TechnicalReport:
    """Baut den technischen Report in Abschnitten (V4-P6, Abschnitte statt Textwueste)."""
    architektur = (
        solution_technical
        if solution_technical
        else (
            "Noch kein technischer Loesungsvorschlag erzeugt "
            "(POST /cases/{id}/propose-solution)."
        )
    )
    datenlage = (
        f"Datenschutz: {DATA_CLASSIFICATION_CLARTEXT[use_case.data_classification]}. "
        f"Evidenz: {EVIDENCE_LABELS[use_case.evidence_level]}. "
        f"Verbindlichkeit: {ADOPTION_LABELS[use_case.adoption_type]}."
    )
    risiken = (
        "; ".join(result.routing.risk_flags)
        if result.routing.risk_flags
        else "Keine regelbasierten Risikoflags."
    )
    offene: list[str] = []
    if not solution_technical:
        offene.append("Technischer Loesungsansatz noch offen.")
    if result.routing.requires_human_review:
        offene.append("Fachliche/datenschutzrechtliche Pruefung offen.")
    if use_case.evidence_level == EvidenceLevel.PURE_ESTIMATE:
        offene.append("Zeitersparnis ist unbelegt (reine Einschaetzung).")
    offene_text = (
        " ".join(offene) if offene else "Keine offenen technischen Fragen erkennbar."
    )
    return TechnicalReport(
        architektur_kurzfassung=architektur,
        datenlage=datenlage,
        risiken=risiken,
        offene_technische_fragen=offene_text,
    )


def _build_business_summary(
    result: TriageResult,
    use_case: UseCaseInput,
    explanation: TriageExplanation,
    sharpened_text: str | None,
    solution_business: str | None,
    compliance_hint_text: str | None,
    compliance_citations: tuple[ComplianceCitation, ...],
    reviewer_decision: str,
    reviewer_note: str | None,
    decided_at: datetime | None,
) -> BusinessSummary:
    """Leitet die Entscheider-Schicht deterministisch aus TriageResult ab.

    result.zone ist None genau dann, wenn der Vorfilter nicht bestanden wurde
    (domain/pipeline.py) -- in diesem Fall auch result.roi None. Die frueher
    redundante summary_text-Zeile entfaellt zugunsten von decision_report (V4-P6).
    """
    zone_value: str | None = (
        result.zone.final_zone.value if result.zone is not None else None
    )
    expected_benefit: float | None = (
        float(result.roi.expected_benefit_eur) if result.roi is not None else None
    )
    return BusinessSummary(
        title=result.title,
        zone=zone_value,
        is_actionable=result.is_actionable,
        recommendation=result.routing.recommendation.value,
        expected_benefit_eur=expected_benefit,
        decision_report=_build_decision_report(
            result,
            use_case,
            explanation,
            sharpened_text,
            solution_business,
            compliance_hint_text,
        ),
        solution_business=solution_business,
        sharpened_text=sharpened_text,
        compliance_hint_text=compliance_hint_text,
        compliance_citations=compliance_citations,
        reviewer_decision=reviewer_decision,
        reviewer_note=reviewer_note,
        decided_at=decided_at,
    )


def _build_technical_detail(
    result: TriageResult, use_case: UseCaseInput, proposal_text: str | None
) -> TechnicalDetail:
    """Leitet die Reviewer-Schicht deterministisch aus TriageResult ab.

    composite/roi sind None wenn passed_vorfilter False ist (siehe
    domain/pipeline.py) -- entsprechende Felder werden dann None. proposal_text
    ist die technische Loesungsfassung (solution_technical).
    """
    return TechnicalDetail(
        passed_vorfilter=result.passed_vorfilter,
        vorfilter_failed_criteria=list(result.vorfilter.failed_criteria),
        composite_total=(
            result.composite.total if result.composite is not None else None
        ),
        composite_effort_label=(
            result.composite.effort_label if result.composite is not None else None
        ),
        feasibility_flags=[f.value for f in result.feasibility.flags],
        feasibility_recommendation=result.feasibility.recommendation,
        automation_signals=list(result.routing.automation_signals),
        ai_signals=list(result.routing.ai_signals),
        risk_flags=list(result.routing.risk_flags),
        requires_human_review=result.routing.requires_human_review,
        roi_theoretical_potential_eur=(
            float(result.roi.theoretical_potential_eur)
            if result.roi is not None
            else None
        ),
        roi_net_expected_benefit_eur=(
            float(result.roi.net_expected_benefit_eur)
            if result.roi is not None
            else None
        ),
        technical_report=_build_technical_report(result, use_case, proposal_text),
        proposal_text=proposal_text,
    )


def _build_compliance_data_block(chunks: list[RetrievedChunk]) -> str:
    """Baut den nummerierten DATA-Block fuer den compliance_hints-Prompt.

    Nummerierung (1-basiert) ist identisch zur spaeteren Citation-Liste
    (ComplianceCitation.number) -- das LLM referenziert nur die Nummer im
    Fliesstext, die eigentliche Quellenaufloesung passiert deterministisch
    in generate_compliance_hints() (ADR-0024), nicht aus der LLM-Antwort.
    """
    return "\n\n".join(f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(chunks))


def _build_compliance_citations(
    chunks: list[RetrievedChunk],
) -> tuple[ComplianceCitation, ...]:
    """Baut die Citation-Liste deterministisch aus den Retrieval-Treffern.

    citation faellt auf source_id zurueck, wenn ein Treffer kein
    metadata['citation'] traegt (z. B. MockRetriever, dessen Treffer
    metadata={} liefern, ADR-0014).
    """
    return tuple(
        ComplianceCitation(
            number=index + 1,
            source_id=chunk.source_id,
            citation=chunk.metadata.get("citation", chunk.source_id),
            url=chunk.metadata.get("url"),
        )
        for index, chunk in enumerate(chunks)
    )


_CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")


def _strip_dangling_citation_markers(
    hint_text: str, citation_count: int
) -> tuple[str, list[int]]:
    """Entfernt [N]-Marker ohne Gegenstueck in der Citation-Liste (F-016).

    Die Citation-Liste ist deterministisch 1..citation_count nummeriert
    (_build_compliance_citations). Ein Marker ausserhalb dieses Bereichs
    ist eine LLM-Halluzination -- er wuerde im Report auf keine Quelle
    aufloesen und damit genau die ungegruendete Behauptung suggerieren,
    die Citations-before-LLM strukturell ausschliessen soll. Strippen
    statt Abbrechen: Graceful Degradation, analog sharpen_case.

    Returns:
        (bereinigter Text, Liste der entfernten Marker-Nummern).
    """
    dangling: list[int] = []

    def _keep_or_strip(match: re.Match[str]) -> str:
        number = int(match.group(1))
        if 1 <= number <= citation_count:
            return match.group(0)
        dangling.append(number)
        return ""

    cleaned = _CITATION_MARKER_RE.sub(_keep_or_strip, hint_text)
    if dangling:
        # Luecken aus entfernten Markern glaetten ("siehe  ." -> "siehe .").
        cleaned = re.sub(r" {2,}", " ", cleaned).strip()
    return cleaned, dangling


class TriageService:
    """Orchestriert Use-Case-Einreichung: ID -> Zeitstempel -> Domain -> Persistenz.

    Alle Abhaengigkeiten werden von aussen injiziert (Constructor DI).
    Die Domain-Logik liegt vollstaendig in evaluate_use_case() -- der Service
    ist ausschliesslich fuer Orchestrierung und Persistenz zustaendig.

    llm: LLMPort -- Phase C, fuer sharpen_case()/propose_solution()/
    generate_compliance_hints(). retriever: RetrieverPort -- Phase D, fuer
    generate_compliance_hints() (ADR-0024). Beide Pflicht-Parameter, kein
    Default: ein Default wuerde aus aect.adapters importieren und die
    Dependency-Inversion-Grenze verletzen (siehe Modul-Docstring).
    """

    def __init__(
        self,
        repository: RepositoryPort,
        clock: ClockPort,
        id_generator: IdGeneratorPort,
        roi_config: ROIConfig,
        llm: LLMPort,
        retriever: RetrieverPort,
        embedder: EmbedderPort | None = None,
        redactor: PIIRedactorPort | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator
        self._roi_config = roi_config
        self._llm = llm
        self._retriever = retriever
        # Das Land fuer den Stundensatz-Lookup kommt jetzt aus use_case.country
        # (UseCaseInput-Feld) -- kein service-weiter country-Parameter mehr.
        # Optional (L-3, ADR-0039): nur fuer die Dedup-Aehnlichkeitspruefung bei
        # Intake. None -> Pruefung wird uebersprungen (Mock-/Testbetrieb ohne
        # echtes Embedding-Modell). Kein Pflichtparameter, damit bestehende
        # Konstruktionsstellen unveraendert bleiben.
        self._embedder = embedder
        # Zonen-Klassifikator fuer die Erklaerbarkeit (V4-P6): lazily geladen,
        # danach gecached. explain_case() braucht die Zonen-Schwellen fuer die
        # Konfidenz-Begruendung (Zonengrenz-Abstand). Dieselben Schwellen, die
        # der Pipeline-Pfad (load_zone_classifier) beim Klassifizieren nutzt.
        self._zone_classifier: ZoneClassifier | None = None
        # Optional (Phase G Privacy-Haertung, B1-Spike): redaktiert PII NUR
        # im Text, der an den Dedup-Embedder geht (check_similarity()) --
        # NICHT die gespeicherten title/current_state-Felder selbst (siehe
        # dort). None -> Text geht unredaktiert an embed(), identisch zum
        # Verhalten vor diesem Feature. Kein Pflichtparameter, aus demselben
        # Grund wie embedder oben (bestehende Konstruktionsstellen bleiben
        # unveraendert).
        self._redactor = redactor

    def submit_use_case(self, use_case: UseCaseInput) -> SubmittedCase:
        """Bewertet einen Use Case und persistiert das Ergebnis.

        Reihenfolge: ID generieren -> Zeitstempel -> Domain-Evaluate -> Speichern.
        Exceptions aus evaluate_use_case() (z. B. ungueltige Config-Keys) propagieren.
        """
        case_id = self._id_generator.generate()
        submitted_at = self._clock.now()
        result = evaluate_use_case(use_case, self._roi_config)
        case = SubmittedCase(
            id=case_id,
            submitted_at=submitted_at,
            use_case=use_case,
            result=result,
        )
        self._repository.save(case)
        return case

    async def check_similarity(self, case: SubmittedCase) -> SimilarityWarning | None:
        """Dedup-Pruefung bei Intake: aehnelt der Case einem bestehenden? (ADR-0039).

        Additiv -- veraendert die Triage-Entscheidung nicht, liefert nur einen
        optionalen Hinweis. Wird nach submit_use_case() aufgerufen (der Case ist
        bereits persistiert); das berechnete Embedding wird am Case gespeichert,
        damit kuenftige Cases dagegen vergleichen koennen.

        Effizienz-/Robustheitsregeln:
        - Kein Embedder injiziert (Mock-/Testbetrieb): still ueberspringen, einmal
          als Warnung loggen.
        - Keine anderen Cases in der DB: ganz ueberspringen, KEIN Embedding
          berechnen (nichts zu vergleichen).
        - Embedding-Berechnung schlaegt fehl: Fehler loggen, ohne Hinweis
          fortfahren -- die Triage darf nie an der Dedup-Pruefung scheitern.

        PII-Redaktion vor dem Embedding (Phase G Privacy-Haertung, B1-Spike):
        NUR der Text, der hier an den Embedder geht, wird redaktiert -- die
        gespeicherten Felder case.use_case.title/current_state bleiben im
        Klartext (Fallbearbeitung und sharpen_case()/propose_solution()
        brauchen sie unveraendert). Kein Redactor injiziert (redactor=None,
        z. B. Mock-/Testbetrieb) -> Text geht unredaktiert an embed(), exakt
        wie vor diesem Feature. Eine fehlschlagende Redaktion faellt unter
        dieselbe Best-Effort-Regel wie eine fehlschlagende Embedding-
        Berechnung (try-Block unten) -- die Dedup-Pruefung ist additiv und
        darf nie die Triage scheitern lassen.

        Schwellen (_DEDUP_THRESHOLD_*): < 0.75 kein Hinweis; [0.75, 0.90)
        Hinweis (suggest_combine=False); >= 0.90 Hinweis mit suggest_combine=True.
        """
        logger = structlog.get_logger()
        if self._embedder is None:
            logger.warning("dedup_skipped_no_embedder", case_id=case.id)
            return None

        all_cases = await self._repository.list_all_async()
        others = [c for c in all_cases if c.id != case.id]
        if not others:
            return None  # keine Vergleichsbasis -> kein Embedding berechnen

        try:
            text = f"{case.use_case.title} {case.use_case.current_state}"
            if self._redactor is not None:
                text = self._redactor.redact(text)
            vectors = await self._embedder.embed([text])
            new_vector = list(vectors[0])
        except Exception as exc:
            logger.error("dedup_embedding_failed", case_id=case.id, error=str(exc))
            return None

        # Embedding fuer kuenftige Vergleiche persistieren (Case ist bereits da).
        # Per-Feld-UPDATE (F-011): ueberschreibt keine parallel gesetzten
        # Narrative-Felder desselben Case.
        await self._repository.update_field_async(
            case.id, "embedding", json.dumps(new_vector)
        )

        best_case: SubmittedCase | None = None
        best_score = 0.0
        for other in others:
            if other.embedding is None:
                continue
            score = _cosine_similarity(new_vector, other.embedding)
            if score > best_score:
                best_score = score
                best_case = other

        if best_case is None or best_score < _DEDUP_THRESHOLD_AWARENESS:
            return None

        return SimilarityWarning(
            similar_case_id=best_case.id,
            similar_case_title=best_case.use_case.title,
            similarity_score=round(best_score, 4),
            suggest_combine=best_score >= _DEDUP_THRESHOLD_COMBINE,
        )

    async def list_similarity_pairs(self) -> SimilarityPairsResult:
        """Aggregiert alle Dedup-Beziehungen ueber die persistierten Cases (P9).

        Read-only Gegenstueck zu check_similarity(): dort "neuer Case vs.
        bestehende" beim Intake, hier "alle bestehenden paarweise" fuer eine
        Dedup-Uebersicht. Dieselbe Cosinus-Funktion (_cosine_similarity) und
        dieselben BEIDEN Schwellen (_DEDUP_THRESHOLD_AWARENESS/_COMBINE) --
        eine Quelle im Code, keine zweite Implementierung.

        Nur Cases mit persistiertem Embedding gehen in die Paarbildung ein;
        Cases ohne Embedding (Embedder beim Intake nicht verfuegbar, oder Case
        aus einer aelteren DB-Version) werden gezaehlt und in
        cases_without_embedding zurueckgegeben, damit die Luecke im UI sichtbar
        bleibt statt still zu verschwinden.

        Komplexitaet O(n^2): bewusste Entscheidung fuer einen privaten Build
        ohne Pagination-Scope (SDR-0002 Paragraph 12) -- die paarweise
        Vollvergleichs-Matrix ueber eine kleine Portfolio-Datenmenge ist
        akzeptabel; kein ADR, siehe Daily-Note.

        Reine Lese-Operation: kein Schreiben in die DB, kein LLM-Call, keine
        Aenderung an der Intake-Dedup-Logik.
        """
        all_cases = await self._repository.list_all_async()
        # Embedding-Narrowing im Comprehension-Guard: (case, embedding) mit
        # embedding als list[float] (nicht None) -- mypy-sauber ohne assert.
        with_embedding = [
            (case, case.embedding) for case in all_cases if case.embedding is not None
        ]
        cases_without_embedding = len(all_cases) - len(with_embedding)

        pairs: list[SimilarityPair] = []
        for i in range(len(with_embedding)):
            case_a, embedding_a = with_embedding[i]
            for j in range(i + 1, len(with_embedding)):
                case_b, embedding_b = with_embedding[j]
                score = _cosine_similarity(embedding_a, embedding_b)
                if score < _DEDUP_THRESHOLD_AWARENESS:
                    continue
                # case_a/case_b deterministisch nach id -- ein Paar hat
                # unabhaengig von der Iterationsreihenfolge dieselbe Gestalt.
                first, second = sorted((case_a, case_b), key=lambda c: c.id)
                pairs.append(
                    SimilarityPair(
                        case_a_id=first.id,
                        case_a_title=first.use_case.title,
                        case_b_id=second.id,
                        case_b_title=second.use_case.title,
                        similarity_score=round(score, 4),
                        suggest_combine=score >= _DEDUP_THRESHOLD_COMBINE,
                    )
                )

        # Absteigend nach score; Sekundaerschluessel (case_a_id, case_b_id)
        # haelt die Reihenfolge bei Gleichstand deterministisch.
        pairs.sort(key=lambda p: (-p.similarity_score, p.case_a_id, p.case_b_id))
        return SimilarityPairsResult(
            pairs=pairs, cases_without_embedding=cases_without_embedding
        )

    def _get_zone_classifier(self) -> ZoneClassifier:
        """Lazily geladener, gecachter Zonen-Klassifikator (V4-P6)."""
        if self._zone_classifier is None:
            self._zone_classifier = load_zone_classifier()
        return self._zone_classifier

    def explain_case(self, case: SubmittedCase) -> TriageExplanation:
        """Deterministische Erklaerbarkeit eines Case (V4-P6).

        Score-Herkunft, Konfidenz-Begruendung und Empfehlungs-Satz -- reine
        Read-Time-Projektion ueber case.result, kein LLM, keine Persistenz. Nutzt
        dieselben Kostenschwellen (roi_config) und Zonen-Schwellen (classifier)
        wie die Pipeline-Bewertung. Wird sowohl von der Triage-Response als auch
        vom Entscheider-Report (generate_report) verwendet -- eine Quelle.
        """
        return explain_triage(
            case.use_case,
            case.result,
            impl_cost_point_min_eur=self._roi_config.impl_cost_point_min_eur,
            license_cost_point_min_eur=self._roi_config.license_cost_point_min_eur,
            classifier=self._get_zone_classifier(),
        )

    def get_case(self, case_id: str) -> SubmittedCase | None:
        """Gibt einen gespeicherten Case zurueck oder None wenn nicht gefunden."""
        return self._repository.get(case_id)

    def list_cases(self) -> list[SubmittedCase]:
        """Alle bisher eingereichten Cases."""
        return self._repository.list_all()

    def compute_stats(self) -> PortfolioStats:
        """Aggregiert die Portfolio-Kennzahlen fuer die Startseite (V4-P7).

        Ein einziger list_all()-Durchlauf, rein lesend -- kein LLM, keine
        Persistenz-Aenderung. Semantik: siehe PortfolioStats-Docstring
        (Funnel eingereicht -> bewertet -> umgesetzt + freigegebener Netto-Nutzen).
        """
        cases = self._repository.list_all()
        released_statuses = {CaseStatus.APPROVED, CaseStatus.IMPLEMENTED}
        net_sum = sum(
            (
                c.result.roi.net_expected_benefit_eur
                for c in cases
                if c.status in released_statuses and c.result.roi is not None
            ),
            Decimal("0"),
        )
        return PortfolioStats(
            eingereicht=len(cases),
            bewertet=sum(1 for c in cases if c.result.passed_vorfilter),
            umgesetzt=sum(1 for c in cases if c.status is CaseStatus.IMPLEMENTED),
            netto_nutzen_freigegeben_eur=net_sum,
        )

    async def delete_case(self, case_id: str) -> None:
        """Loescht einen Case kaskadiert: Repository + Vektor-Store + Audit-Log.

        DSGVO Art. 17 (ADR-0038): echte Loeschung, kein Soft-Delete. Ablauf:
        1. Existenz pruefen -> CaseNotFoundError wenn fehlend (Route -> 404).
        2. Aus dem Repository loeschen (primaere, persistente Quelle). Der
           Repository-Delete loescht die Monitoring-Eintraege des Case in
           derselben Operation mit (Monitoring-ADR) -- die append-only
           Zeitleiste ueberlebt ihren Case nicht. Das geschieht VOR dem
           Audit-Log-Event unten; das Loesch-Event selbst bleibt erhalten.
        3. Best-effort aus dem Vektor-Store (ChromaDB) ueber den source_id-Tag.
           Faellt der Store aus, wird das geloggt aber NICHT propagiert -- die
           primaere Loeschung ist bereits erfolgt und darf nicht zurueckgedreht
           werden (Cases liegen aktuell ohnehin nur im Repository, nicht im
           Vektor-Store; der Schritt ist eine vorausschauende Absicherung).
        4. Loesch-Ereignis als Audit-Trail loggen.

        Audit-Trail (DSGVO Art. 5(2) Rechenschaftspflicht): das Loesch-Ereignis
        selbst (case_id + deleted_at) wird geloggt -- der Loesch-Nachweis ist
        keine personenbezogene Information und muss erhalten bleiben, gerade
        weil die Daten geloescht wurden.

        Raises:
            CaseNotFoundError: case_id existiert nicht.
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            raise CaseNotFoundError(case_id)

        await self._repository.delete_async(case_id)

        logger = structlog.get_logger()
        try:
            await self._retriever.delete_by_source_id(case_id)
        except Exception as exc:
            # Best-effort: ein Vektor-Store-Ausfall darf die bereits erfolgte
            # Repository-Loeschung nicht zurueckdrehen (DSGVO: Loeschung steht).
            logger.warning(
                "chromadb_delete_failed",
                case_id=case_id,
                error=str(exc),
            )

        logger.info(
            "case_deleted",
            case_id=case_id,
            deleted_at=self._clock.now().isoformat(),
        )

    async def record_decision(
        self, case_id: str, decision: ReviewerDecision, note: str | None
    ) -> SubmittedCase | None:
        """Setzt eine Freigabe-/Ablehnungsentscheidung fuer einen Case
        (Human-in-the-Loop, minimaler Decision-Record -- ADR-0043, bewusst
        kein voller Multi-User-Reviewer-Workflow mit Rollen/Notifications).

        Ueberschreiben einer bestehenden Entscheidung ist erlaubt
        (Korrektur-Fall, kein Bug) -- decided_at wird bei jedem Aufruf
        aktualisiert.

        Persistenz: dediziertes UPDATE ueber RepositoryPort.record_decision_
        async (F-011-Muster, siehe adapters/sqlite/repository.py) statt
        save() der ganzen Zeile -- kein Lost-Update-Risiko gegenueber
        parallelen LLM-Feld-Schreibvorgaengen (sharpen/propose/compliance)
        auf demselben Case.

        Audit-Trail: case_decision_recorded wird geloggt (case_id, decision,
        decided_at) -- OHNE reviewer_note (PII-Allowlist-konform: Freitext
        koennte personenbezogene Angaben enthalten, analog case_deleted,
        das ebenfalls keine Inhaltsfelder loggt).

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        decided_at = self._clock.now()
        await self._repository.record_decision_async(
            case_id, decision, note, decided_at
        )
        case.reviewer_decision = decision
        case.reviewer_note = note
        case.decided_at = decided_at

        # Lifecycle-Kopplung (Lifecycle-ADR), monoton (H-034): der Freigabe-/
        # Ablehnungs-Akt bewegt den Case im Lifecycle NUR, solange er noch in
        # einem fruehen Zustand ({submitted, in_review}) steht. Ein bereits
        # fortgeschrittener Status (z. B. implemented/integrated) wird NICHT
        # zurueckgestuft -- die reviewer_decision wird dennoch festgehalten.
        # PENDING hat keinen Lifecycle-Gegenwert (kommt ueber die Route nicht).
        status_map = {
            ReviewerDecision.APPROVED: CaseStatus.APPROVED,
            ReviewerDecision.REJECTED: CaseStatus.REJECTED,
        }
        coupled_status = status_map.get(decision)
        early_statuses = (CaseStatus.SUBMITTED, CaseStatus.IN_REVIEW)
        if coupled_status is not None and case.status in early_statuses:
            await self._repository.update_status_async(
                case_id, coupled_status, decided_at
            )
            case.status = coupled_status
            case.status_updated_at = decided_at

        logger = structlog.get_logger()
        logger.info(
            "case_decision_recorded",
            case_id=case_id,
            decision=decision.value,
            decided_at=decided_at.isoformat(),
        )
        return case

    async def update_status(
        self, case_id: str, status: CaseStatus
    ) -> SubmittedCase | None:
        """Setzt den Lifecycle-Status eines Case (Lifecycle-ADR).

        Bewusst keine Transitions-Matrix: jeder Zustand ist aus jedem setzbar
        (menschliche Autoritaet in einem Single-User-Build). Kopplung an
        ReviewerDecision liegt in record_decision(), nicht hier -- dieser Pfad
        setzt den Status frei.

        Persistenz: dediziertes UPDATE ueber RepositoryPort.update_status_async
        (F-011-Muster, analog record_decision) statt save() der ganzen Zeile --
        kein Lost-Update gegenueber parallelen LLM-Feld-Schreibvorgaengen
        (sharpen/propose/compliance) auf demselben Case.

        Audit-Trail: case_status_changed wird geloggt (case_id, old_status,
        new_status, updated_at) -- reine Allowlist-Felder, kein Freitext
        (PII-Allowlist-konform, analog case_decision_recorded/case_deleted).
        Der updated_at-Zeitstempel (clock.now()) wird persistiert
        (status_updated_at, analog decided_at), geloggt und am Case zurueckgegeben.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        old_status = case.status
        updated_at = self._clock.now()
        await self._repository.update_status_async(case_id, status, updated_at)
        case.status = status
        case.status_updated_at = updated_at

        logger = structlog.get_logger()
        logger.info(
            "case_status_changed",
            case_id=case_id,
            old_status=old_status.value,
            new_status=status.value,
            updated_at=updated_at.isoformat(),
        )
        return case

    async def add_monitoring_note(
        self, case_id: str, note: str
    ) -> MonitoringEntry | None:
        """Haengt eine Monitoring-Notiz an die Zeitleiste eines Case (Monitoring-ADR).

        Append-only: der Eintrag wird geschrieben, nie veraendert -- eine
        Zeitleiste manueller Beobachtungen mit Audit-Charakter. id via
        IdGeneratorPort, created_at via ClockPort (beide testbar-injiziert).

        status_snapshot ist der case.status zum Zeitpunkt des Eintrags, als
        String eingefroren -- eine Momentaufnahme, kein Live-Verweis: ein
        spaeterer Statuswechsel des Case aendert bestehende Eintraege nicht.

        Audit-Trail: monitoring_entry_added wird geloggt (case_id, entry_id,
        created_at) -- OHNE note (Freitext koennte PII enthalten,
        PII-Allowlist-konform, analog case_decision_recorded/case_deleted).

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        entry = MonitoringEntry(
            id=self._id_generator.generate(),
            case_id=case_id,
            created_at=self._clock.now(),
            note=note,
            status_snapshot=case.status.value,
        )
        await self._repository.add_monitoring_entry_async(entry)

        logger = structlog.get_logger()
        logger.info(
            "monitoring_entry_added",
            case_id=case_id,
            entry_id=entry.id,
            created_at=entry.created_at.isoformat(),
        )
        return entry

    async def list_monitoring(self, case_id: str) -> list[MonitoringEntry] | None:
        """Gibt die Monitoring-Zeitleiste eines Case zurueck (chronologisch).

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404) --
            unterscheidet "Case existiert nicht" von "Case ohne Eintraege"
            (leere Liste), analog get_case().
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None
        return await self._repository.list_monitoring_entries_async(case_id)

    def _validate_sharpening(
        self, content: str, allowlist: set[str]
    ) -> tuple[SharpenedContentV2 | None, InvalidLLMOutputError | None, list[str]]:
        """Prueft eine rohe LLM-Antwort auf Schema UND erfundene Zahlen.

        Rueckgabe (parsed, schema_error, violations):
        - Schema verletzt -> (None, InvalidLLMOutputError, []).
        - Schema ok, aber erfundene Zahlen -> (parsed, None, [Zahlen]).
        - Sauber -> (parsed, None, []).

        Der Zahlen-Guard laeuft NUR ueber die drei Beschreibungs-Felder
        (sharpened_title/current_state/desired_state) -- NICHT ueber die
        improvement_suggestions. Deren hebel darf bewusst Bewertungsgroessen
        beziffern ("Evidenzfaktor steigt von 0,40 auf 0,90"); das sind
        Config-/Modell-Werte, keine erfundenen Case-Zahlen.
        """
        try:
            parsed = parse_structured_llm_output(content, SharpenedContentV2)
        except InvalidLLMOutputError as exc:
            return None, exc, []
        guarded_text = "\n".join(
            (
                parsed.sharpened_title,
                parsed.sharpened_current_state,
                parsed.sharpened_desired_state,
            )
        )
        return parsed, None, find_violations(allowlist, guarded_text)

    @staticmethod
    def _sharpening_correction(
        schema_error: InvalidLLMOutputError | None, violations: list[str]
    ) -> str:
        """Baut die an den Retry angehaengte Korrektur-Instruktion."""
        if violations:
            return (
                "Du hast folgende Zahlen verwendet, die nicht im Original "
                f"stehen: {', '.join(violations)}. Entferne sie ersatzlos oder "
                "formuliere qualitativ, ohne neue Zahlen einzufuehren."
            )
        return (
            "Deine Antwort erfuellte das vorgegebene JSON-Schema nicht "
            f"({schema_error}). Antworte erneut exakt im Schema; jeder "
            "Verbesserungsvorschlag braucht bezugsfeld, vorschlag und hebel."
        )

    def _validate_solution(
        self, content: str
    ) -> tuple[SolutionProposalV2 | None, InvalidLLMOutputError | None, list[str]]:
        """Prueft eine rohe LLM-Antwort auf Schema UND verbotenes Vokabular (V4-P6).

        Rueckgabe (parsed, schema_error, violations):
        - Schema verletzt -> (None, InvalidLLMOutputError, []).
        - Schema ok, aber Technik-/Architektur-Vokabular im Business-Absatz ->
          (parsed, None, [Begriffe]).
        - Sauber -> (parsed, None, []).

        Der Vokabular-Guard laeuft NUR ueber solution_business -- solution_technical
        darf und soll Technologiebegriffe nennen.
        """
        try:
            parsed = parse_structured_llm_output(content, SolutionProposalV2)
        except InvalidLLMOutputError as exc:
            return None, exc, []
        return parsed, None, find_vocabulary_violations(parsed.solution_business)

    @staticmethod
    def _solution_correction(
        schema_error: InvalidLLMOutputError | None, violations: list[str]
    ) -> str:
        """Baut die an den Retry angehaengte Korrektur-Instruktion (V4-P6)."""
        if violations:
            return (
                "Der Absatz fuer die Geschaeftsleitung (solution_business) enthaelt "
                f"verbotene technische Begriffe: {', '.join(violations)}. Formuliere "
                "ihn ohne Technologie-/Produktnamen und ohne Architekturvokabular "
                "neu; das JSON-Schema (solution_business, solution_technical) bleibt "
                "gleich."
            )
        return (
            "Deine Antwort erfuellte das vorgegebene JSON-Schema nicht "
            f"({schema_error}). Antworte erneut exakt im Schema mit genau den "
            "Feldern solution_business und solution_technical."
        )

    async def sharpen_case(
        self, case_id: str, prompt_version: str = "v3"
    ) -> SharpenedUseCase | None:
        """Schaerft die Use-Case-Beschreibung eines persistierten Cases via LLM.

        Original-Felder (title, current_state, desired_state) werden aus dem
        gespeicherten Case uebernommen und nie ueberschrieben -- die
        geschaerfte Version steht daneben (sharpened_title/current_state/
        desired_state + improvement_suggestions).

        Zahlen-Guard + Retry + Fail loud (V4, SDR-0003): die rohe Antwort wird
        gegen SharpenedContentV2 validiert UND ein deterministischer
        Zahlen-Guard (domain/sharpening_guard) prueft, dass die geschaerften
        Beschreibungs-Felder keine im Original fehlenden Zahlen erfinden.
        Schlaegt Schema ODER Zahlen-Guard an, laeuft genau EIN Retry mit
        angehaengter Korrektur-Instruktion (Cost-Logging wie ueblich). Bleibt
        der Verstoss:
        - Schema weiterhin verletzt -> InvalidLLMOutputError (Route -> 422).
        - Zahlen weiterhin erfunden -> SharpeningNumberViolationError (422 mit
          Violation-Liste). Nichts wird gespeichert.

        Draft statt Direkt-Speichern (V4): Erfolg persistiert das Ergebnis als
        sharpening_draft (per-Feld-UPDATE, F-011) -- ueberschreibt NICHTS am
        Case. Erst accept_sharpening() traegt es nach sharpened_content_json.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).

        Messages-API (aect-security-checklist v2.1, Phase C): System- und
        User-Prompt bleiben getrennte LLMMessage-Eintraege, kein String-Concat.

        Injection-Pattern-Check (OWASP LLM01, Tag 32): Freitextfelder werden vor
        dem LLM-Call auf bekannte Injection-Muster geprueft. Treffer werden
        geloggt (case_id + Feldname + Pattern-Namen, kein Body), der Call laeuft
        trotzdem weiter -- Flaggen, nicht Blocken (siehe sanitization.py).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        _flag_injection_in_fields(
            {
                "title": case.use_case.title,
                "current_state": case.use_case.current_state,
                "desired_state": case.use_case.desired_state,
                "example_process": case.use_case.example_process,
            },
            case_id=case.id,
        )

        system_prompt = load_prompt("sharpen_use_case", "system", prompt_version)
        user_template = load_prompt("sharpen_use_case", "user", prompt_version)
        user_content = user_template.format(
            title=neutralize_delimiters(case.use_case.title),
            current_state=neutralize_delimiters(case.use_case.current_state),
            desired_state=neutralize_delimiters(case.use_case.desired_state),
            example_process=neutralize_delimiters(case.use_case.example_process),
        )
        allowlist = build_allowlist(case.use_case)

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self._llm.complete(messages)
        log_llm_cost(
            case_id=case.id,
            messages=messages,
            response=response,
            operation="sharpen_case",
        )
        parsed, schema_error, violations = self._validate_sharpening(
            response.content, allowlist
        )

        if parsed is None or violations:
            logger = structlog.get_logger()
            logger.warning(
                "sharpening_guard_retry",
                case_id=case.id,
                reason="numbers" if violations else "schema",
                violations=violations,
            )
            correction = self._sharpening_correction(schema_error, violations)
            retry_messages = [
                *messages,
                LLMMessage(role="assistant", content=response.content),
                LLMMessage(role="user", content=correction),
            ]
            retry_response = await self._llm.complete(retry_messages)
            log_llm_cost(
                case_id=case.id,
                messages=retry_messages,
                response=retry_response,
                operation="sharpen_case_retry",
            )
            parsed, schema_error, violations = self._validate_sharpening(
                retry_response.content, allowlist
            )

        if parsed is None:
            # parsed None <=> _validate_sharpening lieferte einen schema_error.
            structlog.get_logger().warning(
                "sharpening_schema_invalid_after_retry", case_id=case.id
            )
            raise schema_error or InvalidLLMOutputError("LLM-Output ohne Schema")
        if violations:
            structlog.get_logger().warning(
                "sharpening_number_violation_after_retry",
                case_id=case.id,
                violations=violations,
            )
            raise SharpeningNumberViolationError(case.id, violations)

        suggestions = tuple(parsed.improvement_suggestions)
        draft_json = json.dumps(
            {
                "original": {
                    "title": case.use_case.title,
                    "current_state": case.use_case.current_state,
                    "desired_state": case.use_case.desired_state,
                },
                "sharpened": {
                    "sharpened_title": parsed.sharpened_title,
                    "sharpened_current_state": parsed.sharpened_current_state,
                    "sharpened_desired_state": parsed.sharpened_desired_state,
                },
                "improvement_suggestions": [
                    s.model_dump(mode="json") for s in suggestions
                ],
                "prompt_version": prompt_version,
                "created_at": self._clock.now().isoformat(),
            }
        )
        await self._repository.update_field_async(
            case.id, "sharpening_draft", draft_json
        )

        return SharpenedUseCase(
            case_id=case.id,
            original_title=case.use_case.title,
            original_current_state=case.use_case.current_state,
            original_desired_state=case.use_case.desired_state,
            sharpened_title=parsed.sharpened_title,
            sharpened_current_state=parsed.sharpened_current_state,
            sharpened_desired_state=parsed.sharpened_desired_state,
            improvement_suggestions=suggestions,
            prompt_version=prompt_version,
        )

    async def accept_sharpening(self, case_id: str) -> SubmittedCase | None:
        """Uebernimmt den offenen Schaerfungs-Draft in die regulaeren Felder (V4).

        Traegt den sharpening_draft nach sharpened_content_json (das Feld, das
        generate_report() rendert -- bestehende Zwei-Versionen-Logik: Original
        bleibt unangetastet, geschaerfte Fassung steht daneben) und leert den
        Draft. Beide Schreibvorgaenge sind per-Feld-UPDATEs (F-011).

        Returns:
            Den aktualisierten Case (reload), oder None wenn case_id fehlt
            (Route -> 404).

        Raises:
            NoSharpeningDraftError: kein offener Draft (Route -> 409).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None
        if case.sharpening_draft is None:
            raise NoSharpeningDraftError(case.id)

        draft = json.loads(case.sharpening_draft)
        sharpened = draft["sharpened"]
        content_json = json.dumps(
            {
                "sharpened_title": sharpened["sharpened_title"],
                "sharpened_current_state": sharpened["sharpened_current_state"],
                "sharpened_desired_state": sharpened["sharpened_desired_state"],
                "improvement_suggestions": draft["improvement_suggestions"],
                "prompt_version": draft.get("prompt_version"),
            }
        )
        await self._repository.update_field_async(
            case.id, "sharpened_content_json", content_json
        )
        await self._repository.update_field_async(case.id, "sharpening_draft", None)
        return await self._repository.get_async(case.id)

    async def reject_sharpening(self, case_id: str) -> SubmittedCase | None:
        """Verwirft den offenen Schaerfungs-Draft (V4) -- leert sharpening_draft.

        Returns:
            Den aktualisierten Case (reload), oder None wenn case_id fehlt
            (Route -> 404).

        Raises:
            NoSharpeningDraftError: kein offener Draft (Route -> 409).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None
        if case.sharpening_draft is None:
            raise NoSharpeningDraftError(case.id)
        await self._repository.update_field_async(case.id, "sharpening_draft", None)
        return await self._repository.get_async(case.id)

    async def propose_solution(
        self, case_id: str, prompt_version: str = "v3"
    ) -> SolutionProposal | None:
        """Skizziert einen Loesungsansatz fuer einen persistierten Case via LLM.

        Function-Calling-Loop (Tag 38, ADR-0009): propose_solution() bietet
        TOOL_DEFINITIONS an. Fordert das LLM einen Tool-Call an
        (response.tool_calls nicht leer), wird jeder Aufruf via
        dispatch_tool_call() ausgefuehrt, das Ergebnis als role="tool"-
        Nachricht angehaengt und complete() ein zweites Mal aufgerufen.
        Kein while-Loop -- maximal zwei complete()-Aufrufe pro Call
        (LLM10 Unbounded Consumption, siehe ADR-0009).

        LLM06 Excessive Agency: dispatch_tool_call() wirft UnknownToolError
        fuer nicht registrierte Tool-Namen. Der Fehler wird als
        Tool-Ergebnis ({"error": ...}) an das LLM zurueckgegeben statt die
        Anfrage abzubrechen -- Graceful Degradation.

        Persistenz (Tag 42, ADR-0012): die finale response.content (nach
        einem etwaigen Tool-Call-Loop) wird zusaetzlich auf
        case.proposal_text gespeichert (per-Feld-UPDATE, F-011), damit
        generate_report() es ohne erneuten Request-Body-Transport anzeigen
        kann.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).

        v2-Prompt (prompts/propose_solution/v2/) weist das LLM auf
        lookup_stack_options hin und markiert die Plattform-Beschreibungen
        als vorlaeufig/unbelegt (RAG-Grounding folgt Phase D). v1 bleibt
        unveraendert erhalten (Versionierung, application/prompts.py).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        _flag_injection_in_fields(
            {
                "title": case.use_case.title,
                "current_state": case.use_case.current_state,
                "desired_state": case.use_case.desired_state,
                "example_process": case.use_case.example_process,
            },
            case_id=case.id,
        )

        system_prompt = load_prompt("propose_solution", "system", prompt_version)
        user_template = load_prompt("propose_solution", "user", prompt_version)
        user_content = user_template.format(
            title=neutralize_delimiters(case.use_case.title),
            current_state=neutralize_delimiters(case.use_case.current_state),
            desired_state=neutralize_delimiters(case.use_case.desired_state),
            example_process=neutralize_delimiters(case.use_case.example_process),
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self._llm.complete(messages, tools=TOOL_DEFINITIONS)

        log_llm_cost(
            case_id=case.id,
            messages=messages,
            response=response,
            operation="propose_solution",
        )

        if response.tool_calls:
            messages.append(
                LLMMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            for tool_call in response.tool_calls:
                tool_result: dict[str, Any]
                try:
                    tool_result = dispatch_tool_call(tool_call)
                except UnknownToolError as exc:
                    tool_result = {"error": str(exc)}
                messages.append(
                    LLMMessage(
                        role="tool",
                        content=json.dumps(tool_result),
                        tool_call_id=tool_call.id,
                    )
                )

            response = await self._llm.complete(messages, tools=TOOL_DEFINITIONS)

            log_llm_cost(
                case_id=case.id,
                messages=messages,
                response=response,
                operation="propose_solution",
            )

        # Strukturierte Ausgabe + Vokabular-Guard + genau EIN Retry (V4-P6, Muster
        # aus sharpen_case). Schlaegt Schema ODER der Business-Vokabular-Guard an,
        # laeuft ein Korrektur-Retry; bleibt der Verstoss -> Fail loud (Route 422).
        parsed, schema_error, violations = self._validate_solution(response.content)

        if parsed is None or violations:
            logger = structlog.get_logger()
            logger.warning(
                "solution_guard_retry",
                case_id=case.id,
                reason="vocabulary" if violations else "schema",
                violations=violations,
            )
            correction = self._solution_correction(schema_error, violations)
            retry_messages = [
                *messages,
                LLMMessage(role="assistant", content=response.content),
                LLMMessage(role="user", content=correction),
            ]
            retry_response = await self._llm.complete(retry_messages)
            log_llm_cost(
                case_id=case.id,
                messages=retry_messages,
                response=retry_response,
                operation="propose_solution_retry",
            )
            parsed, schema_error, violations = self._validate_solution(
                retry_response.content
            )

        if parsed is None:
            structlog.get_logger().warning(
                "solution_schema_invalid_after_retry", case_id=case.id
            )
            raise schema_error or InvalidLLMOutputError("LLM-Output ohne Schema")
        if violations:
            structlog.get_logger().warning(
                "solution_vocabulary_violation_after_retry",
                case_id=case.id,
                violations=violations,
            )
            raise SolutionVocabularyViolationError(case.id, violations)

        # proposal_text traegt weiter die technische Fassung (Sketch-Eingabe,
        # technische Report-Sicht, Request-Override); solution_business daneben.
        await self._repository.update_field_async(
            case.id, "proposal_text", parsed.solution_technical
        )
        await self._repository.update_field_async(
            case.id, "solution_business", parsed.solution_business
        )

        return SolutionProposal(
            case_id=case.id,
            solution_business=parsed.solution_business,
            solution_technical=parsed.solution_technical,
            prompt_version=prompt_version,
        )

    async def generate_compliance_hints(
        self, case_id: str, prompt_version: str = "v1"
    ) -> ComplianceHintsResult | None:
        """RAG-gegruendete Compliance-Hinweise fuer einen persistierten Case.

        Retrieval-Trigger ist regelbasiert (Projekt-Prinzip: Regeln triggern,
        RAG belegt), nicht aus Use-Case-Freitext:
        - Transparenz-Query (EU AI Act Art. 50): immer -- jeder Report wird
          fuer Menschen ausgegeben, der Transparenzhinweis ist nicht an
          Risikoflags gebunden (knowledge_base/eu-ai-act-art-50-transparenz.md).
        - DSFA-Query (DSGVO Art. 35): zusaetzlich, wenn
          case.result.routing.risk_flags nicht leer ist -- dasselbe Signal,
          das _build_technical_detail() bereits ausgibt (domain/routing.py).
          Bewusst KEINE zweite, lose PII-Schwelle in dieser Methode: eine
          Quelle der Wahrheit, analog zur in ADR-0023 verworfenen
          Zweit-Lookup-Tabelle fuer Citations.

        Kein Freitext fliesst in die Queries -> kein Injection-Pattern-Check
        noetig an dieser Stelle (anders als sharpen_case/propose_solution).

        Persistenz (ADR-0026, analog ADR-0012): das Ergebnis (hint_text +
        citations) wird in beiden Faellen -- mit und ohne Treffer -- als
        JSON auf case.compliance_hints_json gespeichert (per-Feld-UPDATE,
        F-011). generate_report() rendert daraus die Anzeige-Daten
        (_render_compliance_hints) in BusinessSummary.

        Graceful Degradation: liefert das Retrieval ueber alle Queries
        zusammen null Treffer, findet KEIN LLM-Call statt -- hint_text ist
        None, citations leer. Verhindert ungegruendete Hinweise und spart
        Kosten (passiert planmaessig mit MockRetriever fuer Cases ohne
        Risikoflags, dessen Corpus keinen Art.-50-Eintrag hat).

        Citations werden deterministisch aus den Retrieval-Treffern gebaut
        (_build_compliance_citations), NICHT aus der LLM-Antwort geparst --
        einzige Methode, "keine halluzinierte Artikel-Nummer"
        (Master-Plan v3.1 Phase-D-Gate) strukturell statt durch
        Prompt-Disziplin allein zu garantieren. Das LLM referenziert nur die
        Nummer [N] im Fliesstext.

        Bekannte Einschraenkung (v1): keine Deduplizierung, falls derselbe
        Chunk ueber beide Queries zurueckkommt -- bei der heutigen, kleinen
        Wissensbasis nicht relevant, Folge-Punkt sobald sie waechst.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        queries = [_TRANSPARENCY_QUERY]
        if case.result.routing.risk_flags:
            queries.append(_DSFA_QUERY)

        retrieved: list[RetrievedChunk] = []
        for query in queries:
            retrieved.extend(await self._retriever.retrieve(query, top_k=2))

        # Fail loud (CLAUDE.md): taucht ein mock-praefigierter source_id auf, ist
        # die echte Wissensbasis nicht verdrahtet (MockRetriever-Fallback). Dann
        # eine ehrliche "nicht verfuegbar"-Antwort, KEIN LLM-Call und KEINE
        # (Mock-)Citation -- eine API-Response traegt so nie eine mock-Quelle.
        # Persistiert wie jeder andere Ausgang (ADR-0026), damit der Report
        # denselben ehrlichen Stand rendert.
        if any(chunk.source_id.startswith(_MOCK_SOURCE_PREFIX) for chunk in retrieved):
            structlog.get_logger().warning(
                "compliance_kb_unavailable_mock_fallback",
                case_id=case.id,
                retrieved_source_ids=[chunk.source_id for chunk in retrieved],
            )
            await self._repository.update_field_async(
                case.id,
                "compliance_hints_json",
                json.dumps({"hint_text": _KB_UNAVAILABLE_HINT, "citations": []}),
            )
            return ComplianceHintsResult(
                case_id=case.id,
                hint_text=_KB_UNAVAILABLE_HINT,
                citations=(),
                prompt_version=prompt_version,
            )

        if not retrieved:
            await self._repository.update_field_async(
                case.id,
                "compliance_hints_json",
                json.dumps({"hint_text": None, "citations": []}),
            )
            return ComplianceHintsResult(
                case_id=case.id,
                hint_text=None,
                citations=(),
                prompt_version=prompt_version,
            )

        citations = _build_compliance_citations(retrieved)

        # Injection-Check auch hier (H-030): der Titel geht in den Prompt.
        # retrieved_chunks stammen aus der kuratierten KB (trusted), nicht aus
        # User-Freitext -- daher nur der Titel geprueft/neutralisiert.
        _flag_injection_in_fields({"title": case.use_case.title}, case_id=case.id)

        system_prompt = load_prompt("compliance_hints", "system", prompt_version)
        user_template = load_prompt("compliance_hints", "user", prompt_version)
        user_content = user_template.format(
            title=neutralize_delimiters(case.use_case.title),
            retrieved_chunks=_build_compliance_data_block(retrieved),
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self._llm.complete(messages)

        log_llm_cost(
            case_id=case.id,
            messages=messages,
            response=response,
            operation="generate_compliance_hints",
        )

        # F-016: [N]-Marker ohne Citation-Gegenstueck entfernen, BEVOR
        # persistiert wird -- Report und API-Antwort sehen denselben Stand.
        hint_text, dangling_markers = _strip_dangling_citation_markers(
            response.content, len(citations)
        )
        if dangling_markers:
            logger = structlog.get_logger()
            logger.warning(
                "dangling_citation_markers_stripped",
                case_id=case.id,
                markers=dangling_markers,
                citation_count=len(citations),
            )

        compliance_hints_json = json.dumps(
            {
                "hint_text": hint_text,
                "citations": [
                    {
                        "number": c.number,
                        "source_id": c.source_id,
                        "citation": c.citation,
                        "url": c.url,
                    }
                    for c in citations
                ],
            }
        )
        await self._repository.update_field_async(
            case.id, "compliance_hints_json", compliance_hints_json
        )

        return ComplianceHintsResult(
            case_id=case.id,
            hint_text=hint_text,
            citations=citations,
            prompt_version=prompt_version,
        )

    async def ideate(self, problem_description: str) -> tuple[IdeationResult, bool]:
        """Erzeugt AI-Use-Case-Entwuerfe aus einer Problembeschreibung (P10).

        Ephemer (D16): KEINE Persistenz -- kein Repository-Aufruf, kein Case.
        Die Entwuerfe leben nur in der Response.

        Reihenfolge exakt wie der bestehende LLM-Pfad (sharpen_case/
        propose_solution):
        1. PII-Redaction: nur wenn ein Redactor injiziert ist (Mock-/Testbetrieb
           None -> Text geht unredaktiert weiter, identisch zu check_similarity).
        2. Injection-Sanitization (D21, OWASP LLM01): FLAGGEN, nicht BLOCKEN.
           Erkannte Muster werden geloggt (nur Pattern-Namen, kein Body --
           Logging-Allowlist) und als flagged in der Response gefuehrt; der
           LLM-Call laeuft trotzdem. Geprueft wird der (ggf. redaktierte) Text,
           der auch an das LLM geht.
        3. LLM-Call: generate_ideation() validiert die rohe Antwort gegen
           IdeationResult (Output als untrusted, ADR-0013). Eine
           InvalidLLMOutputError propagiert -- die Route mappt sie auf einen
           sauberen HTTP-Fehler (kein 500-Stack-Trace).

        Log-Event ideation_requested: flagged + draft_count, KEIN Problemtext
        (Allowlist-Regel). request_id kommt ueber structlog-contextvars
        (CorrelationIDMiddleware) automatisch dazu.

        Returns:
            (IdeationResult, flagged) -- flagged True, wenn im Input ein
            Injection-Muster erkannt wurde.
        """
        logger = structlog.get_logger()

        description = problem_description
        if self._redactor is not None:
            description = self._redactor.redact(description)

        detected = detect_injection_patterns(description)
        flagged = bool(detected)
        if flagged:
            logger.warning(
                "injection_pattern_detected",
                operation="ideation",
                patterns=detected,
            )

        result = await self._llm.generate_ideation(neutralize_delimiters(description))

        logger.info(
            "ideation_requested",
            flagged=flagged,
            draft_count=len(result.drafts),
        )
        return result, flagged

    async def generate_sketch(
        self, case_id: str, prompt_version: str = "v1"
    ) -> ArchitectureSketchResult | None:
        """Erzeugt eine On-Demand-Architektur-Skizze fuer einen Case (P11, ADR-0049).

        On-Demand, KEIN Pipeline-Schritt: die Triage-Kosten/-Latenz beim Intake
        bleiben unveraendert. Drei Ausgaenge:
        - Case fehlt -> None (Route -> 404).
        - proposal_text fehlt/leer -> NoProposalForSketchError (Route -> 409):
          ohne Loesungsvorschlag gibt es kein Beschreibungsmaterial.
        - sonst: LLM -> Schema-Validierung (im Adapter) -> build_mermaid ->
          persistieren -> zurueckgeben.

        Eingabe an das LLM: Titel + geschaerfte Version (Fallback: Original-Ist/
        Soll-Zustand) + proposal_text. proposal_text ist selbst LLM-Output
        (Injection-Kette LLM->LLM) -- der Prompt markiert alles als
        Beschreibungsmaterial (prompts/architecture_sketch/v1/user.md).

        Persistenz (D20, abgeleitetes Artefakt): das Ergebnis wird als JSON auf
        case.architecture_sketch gespeichert (per-Feld-UPDATE, F-011).
        Regenerieren ueberschreibt (kein Verlauf, kein Audit-Log) -- generated_at
        aendert sich bei jedem Aufruf.

        Log-Event sketch_generated: case_id, node_count, edge_count,
        prompt_version -- KEINE Labels, kein Freitext (Logging-Allowlist).

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).

        Raises:
            NoProposalForSketchError: Case hat keinen Loesungsvorschlag (-> 409).
            InvalidLLMOutputError: LLM-Antwort verletzt das Graph-Schema (-> 502).
            ConnectionError/TimeoutError: LLM nicht erreichbar (-> 503).
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            return None

        proposal_text = case.proposal_text
        if proposal_text is None or not proposal_text.strip():
            raise NoProposalForSketchError(case_id)

        # Injection-Check auch hier (H-030): Titel + Ist/Soll-Zustand koennen
        # ueber die description in den Prompt fliessen.
        _flag_injection_in_fields(
            {
                "title": case.use_case.title,
                "current_state": case.use_case.current_state,
                "desired_state": case.use_case.desired_state,
            },
            case_id=case.id,
        )

        # Geschaerfte Version bevorzugt; Fallback auf den Original-Ist/Soll-Zustand,
        # wenn sharpen_case() fuer diesen Case nie lief.
        description = _render_sharpened_content(case.sharpened_content_json)
        if not description:
            description = (
                f"Ist-Zustand: {case.use_case.current_state}\n"
                f"Soll-Zustand: {case.use_case.desired_state}"
            )

        sketch = await self._llm.generate_architecture_sketch(
            case.id,
            neutralize_delimiters(case.use_case.title),
            neutralize_delimiters(description),
            neutralize_delimiters(proposal_text),
        )
        mermaid_source = build_mermaid(sketch)
        generated_at = self._clock.now()

        sketch_json = json.dumps(
            {
                "graph": sketch.model_dump(mode="json"),
                "mermaid_source": mermaid_source,
                "generated_at": generated_at.isoformat(),
                "prompt_version": prompt_version,
            }
        )
        await self._repository.update_field_async(
            case.id, "architecture_sketch", sketch_json
        )

        logger = structlog.get_logger()
        logger.info(
            "sketch_generated",
            case_id=case.id,
            node_count=len(sketch.nodes),
            edge_count=len(sketch.edges),
            prompt_version=prompt_version,
        )

        return ArchitectureSketchResult(
            case_id=case.id,
            graph=sketch,
            mermaid_source=mermaid_source,
            generated_at=generated_at,
            prompt_version=prompt_version,
        )

    async def get_sketch(self, case_id: str) -> ArchitectureSketchResult | None:
        """Liest die persistierte Architektur-Skizze eines Case (P11, ADR-0049).

        Read-Pfad zu generate_sketch(). Die beiden None-Faelle sind sauber
        getrennt, damit die Route sie unterschiedlich mappen kann:
        - Case fehlt -> CaseNotFoundError (Route -> 404).
        - Case existiert, aber es wurde nie eine Skizze erzeugt -> None
          (Route -> 200 {"sketch": null}).

        Raises:
            CaseNotFoundError: case_id existiert nicht.
        """
        case = await self._repository.get_async(case_id)
        if case is None:
            raise CaseNotFoundError(case_id)
        if case.architecture_sketch is None:
            return None

        data = json.loads(case.architecture_sketch)
        graph = ArchitectureSketch.model_validate(data["graph"])
        return ArchitectureSketchResult(
            case_id=case.id,
            graph=graph,
            mermaid_source=str(data["mermaid_source"]),
            generated_at=datetime.fromisoformat(str(data["generated_at"])),
            prompt_version=str(data["prompt_version"]),
        )

    def generate_report(
        self,
        case_id: str,
        sharpened_text: str | None = None,
        proposal_text: str | None = None,
    ) -> ReportResult | None:
        """Erstellt den zweischichtigen Report (Business + Technisch) fuer einen Case.

        Reine Regel-Schicht (Master-Plan v3.1, Phase C: "Zweischichtiger
        Report-Renderer", ADR-0011): kombiniert das deterministische
        TriageResult mit optionalen LLM-Narrativen aus sharpen_case() /
        propose_solution() / generate_compliance_hints().

        Persistenz (Tag 42, ADR-0012): sharpened_text/proposal_text werden
        standardmaessig aus dem persistierten SubmittedCase gelesen (sofern
        sharpen_case()/propose_solution() fuer diesen Case bereits liefen).
        Ein hier uebergebener Wert ueberschreibt den persistierten -- z. B.
        fuer Tests oder eine Vorschau ohne erneuten Persist.

        sharpened_text/proposal_text fliessen unveraendert als untrusted
        LLM-Output durch (aect-security-checklist v2.1: "LLM-Output immer
        als untrusted behandeln") -- sie wirken nicht auf Berechnungen,
        nur auf die Anzeige.

        Compliance-Hinweise (ADR-0026): hint_text + citations werden aus
        dem persistierten compliance_hints_json gelesen (generate_
        compliance_hints()) und unveraendert in BusinessSummary uebernommen.
        Kein Request-Body-Override hierfuer (anders als sharpened_text/
        proposal_text) -- hint_text referenziert seine Quellen ueber
        [N]-Marker, die exakt zur citations-Liste passen muessen; ein
        freier Text-Override ohne passende Citation-Liste wuerde diese
        Kopplung brechen.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).
        """
        case = self._repository.get(case_id)
        if case is None:
            return None

        effective_sharpened_text = (
            sharpened_text
            if sharpened_text is not None
            else _render_sharpened_content(case.sharpened_content_json)
        )
        effective_proposal_text = (
            proposal_text if proposal_text is not None else case.proposal_text
        )
        compliance_hint_text, compliance_citations = _render_compliance_hints(
            case.compliance_hints_json
        )
        explanation = self.explain_case(case)

        return ReportResult(
            case_id=case.id,
            business_summary=_build_business_summary(
                case.result,
                case.use_case,
                explanation,
                effective_sharpened_text,
                case.solution_business,
                compliance_hint_text,
                compliance_citations,
                case.reviewer_decision.value,
                case.reviewer_note,
                case.decided_at,
            ),
            technical_detail=_build_technical_detail(
                case.result, case.use_case, effective_proposal_text
            ),
        )
