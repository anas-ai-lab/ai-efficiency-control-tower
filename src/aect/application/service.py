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
from typing import Any

import structlog

from aect.application.cost_logger import log_llm_cost
from aect.application.models import (
    BusinessSummary,
    ComplianceCitation,
    ComplianceHintsResult,
    MonitoringEntry,
    ReportResult,
    SharpenedUseCase,
    SimilarityPair,
    SimilarityPairsResult,
    SimilarityWarning,
    SolutionProposal,
    SubmittedCase,
    TechnicalDetail,
)
from aect.application.ports.clock import ClockPort
from aect.application.ports.embedder import EmbedderPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.llm import LLMMessage, LLMPort
from aect.application.ports.pii_redactor import PIIRedactorPort
from aect.application.ports.repository import RepositoryPort
from aect.application.ports.retriever import RetrievedChunk, RetrieverPort
from aect.application.prompts import load_prompt
from aect.application.sanitization import detect_injection_patterns
from aect.application.structured_output import (
    InvalidLLMOutputError,
    SharpenedContentV2,
    parse_structured_llm_output,
)
from aect.application.tools import (
    TOOL_DEFINITIONS,
    UnknownToolError,
    dispatch_tool_call,
)
from aect.domain import (
    CaseStatus,
    ReviewerDecision,
    ROIConfig,
    TriageResult,
    UseCaseInput,
    evaluate_use_case,
)

# Canonical Retrieval-Queries fuer Compliance-Hinweise (ADR-0024). Bewusst
# fest, nicht aus Use-Case-Freitext abgeleitet -- vermeidet jede
# Injection-Flaeche im Retrieval-Pfad selbst (anders als sharpen_case/
# propose_solution, wo Nutzereingabe in den Prompt fliesst).
_DSFA_QUERY = "Datenschutz-Folgenabschaetzung personenbezogene Daten Risiko"
_TRANSPARENCY_QUERY = "Transparenzpflicht KI-System Offenlegung"

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


class CaseNotFoundError(Exception):
    """Angeforderte Case-ID existiert nicht (DSGVO-Loeschpfad, ADR-0038).

    Wird von delete_case() geworfen und in der DELETE-Route auf HTTP 404
    gemappt -- HTTP-Exceptions gehoeren in die Adapter-Schicht, nicht in den
    Application Service (Hexagonal, ADR-0004).
    """

    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case not found: {case_id}")
        self.case_id = case_id


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
    if data.get("raw_text") is not None:
        return str(data["raw_text"])
    lines = [
        f"Titel: {data['sharpened_title']}",
        f"Ist-Zustand: {data['sharpened_current_state']}",
        f"Soll-Zustand: {data['sharpened_desired_state']}",
        "Verbesserungsvorschlaege:",
    ]
    lines += [f"- {s}" for s in data["improvement_suggestions"]]
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


def _build_business_summary(
    result: TriageResult,
    sharpened_text: str | None,
    compliance_hint_text: str | None,
    compliance_citations: tuple[ComplianceCitation, ...],
    reviewer_decision: str,
    reviewer_note: str | None,
    decided_at: datetime | None,
) -> BusinessSummary:
    """Leitet die Entscheider-Schicht deterministisch aus TriageResult ab.

    result.zone ist None genau dann, wenn der Vorfilter nicht bestanden wurde
    (domain/pipeline.py) -- in diesem Fall auch result.roi None.
    """
    if result.zone is not None:
        zone_value: str | None = result.zone.final_zone.value
        expected_benefit: float | None = (
            float(result.roi.expected_benefit_eur) if result.roi is not None else None
        )
        summary_text = (
            f"'{result.title}': Zone {zone_value}, "
            f"Empfehlung {result.routing.recommendation.value}. "
            f"{result.zone.reason}"
        )
    else:
        zone_value = None
        expected_benefit = None
        summary_text = (
            f"'{result.title}' erfuellt die Vorfilter-Kriterien nicht "
            f"({', '.join(result.vorfilter.failed_criteria)}). "
            f"Empfehlung {result.routing.recommendation.value}."
        )

    return BusinessSummary(
        title=result.title,
        zone=zone_value,
        is_actionable=result.is_actionable,
        recommendation=result.routing.recommendation.value,
        expected_benefit_eur=expected_benefit,
        summary_text=summary_text,
        sharpened_text=sharpened_text,
        compliance_hint_text=compliance_hint_text,
        compliance_citations=compliance_citations,
        reviewer_decision=reviewer_decision,
        reviewer_note=reviewer_note,
        decided_at=decided_at,
    )


def _build_technical_detail(
    result: TriageResult, proposal_text: str | None
) -> TechnicalDetail:
    """Leitet die Reviewer-Schicht deterministisch aus TriageResult ab.

    composite/roi sind None wenn passed_vorfilter False ist (siehe
    domain/pipeline.py) -- entsprechende Felder werden dann None.
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

    def get_case(self, case_id: str) -> SubmittedCase | None:
        """Gibt einen gespeicherten Case zurueck oder None wenn nicht gefunden."""
        return self._repository.get(case_id)

    def list_cases(self) -> list[SubmittedCase]:
        """Alle bisher eingereichten Cases."""
        return self._repository.list_all()

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

        # Lifecycle-Kopplung (Lifecycle-ADR): der Freigabe-/Ablehnungs-Akt
        # bewegt den Case auch im Lifecycle -- ein zusaetzlicher dedizierter
        # UPDATE-Call (kein save()). Darf einen zuvor manuell gesetzten Status
        # ueberschreiben: die Freigabe gewinnt. PENDING hat keinen Lifecycle-
        # Gegenwert und wird uebersprungen (kommt ueber die Route ohnehin nicht).
        status_map = {
            ReviewerDecision.APPROVED: CaseStatus.APPROVED,
            ReviewerDecision.REJECTED: CaseStatus.REJECTED,
        }
        coupled_status = status_map.get(decision)
        if coupled_status is not None:
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

    async def sharpen_case(
        self, case_id: str, prompt_version: str = "v2"
    ) -> SharpenedUseCase | None:
        """Schaerft die Use-Case-Beschreibung eines persistierten Cases via LLM.

        Original-Felder (title, current_state, desired_state) werden aus dem
        gespeicherten Case uebernommen und nie ueberschrieben -- die
        geschaerfte Version steht daneben (sharpened_title/current_state/
        desired_state + improvement_suggestions).

        Strukturierte Ausgabe + Graceful Degradation (ADR-0013 Teil 2):
        response.content wird gegen SharpenedContentV2 validiert
        (parse_structured_llm_output). Erfolg -> strukturierte Felder
        gesetzt, raw_text=None. InvalidLLMOutputError -> alle strukturierten
        Felder None/leer, raw_text=response.content, Warnung
        "structured_output_validation_failed" geloggt (case_id, operation,
        error), kein Abbruch.

        Persistenz (Tag 42 ADR-0012, erweitert ADR-0013 Teil 2): das
        Ergebnis wird als JSON auf case.sharpened_content_json gespeichert
        (per-Feld-UPDATE, F-011 -- kein Lost Update bei parallelen
        LLM-Operationen auf demselben Case). generate_report() rendert daraus den
        sichtbaren Text (_render_sharpened_content) -- /report-Schema bleibt
        unveraendert.

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

        fields_to_check = {
            "title": case.use_case.title,
            "current_state": case.use_case.current_state,
            "desired_state": case.use_case.desired_state,
            "example_process": case.use_case.example_process,
        }
        detected: dict[str, list[str]] = {
            field_name: patterns
            for field_name, field_value in fields_to_check.items()
            if (patterns := detect_injection_patterns(field_value))
        }
        if detected:
            logger = structlog.get_logger()
            logger.warning(
                "injection_pattern_detected",
                case_id=case.id,
                fields=detected,
            )

        system_prompt = load_prompt("sharpen_use_case", "system", prompt_version)
        user_template = load_prompt("sharpen_use_case", "user", prompt_version)
        user_content = user_template.format(
            title=case.use_case.title,
            current_state=case.use_case.current_state,
            desired_state=case.use_case.desired_state,
            example_process=case.use_case.example_process,
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
            operation="sharpen_case",
        )

        try:
            parsed = parse_structured_llm_output(response.content, SharpenedContentV2)
        except InvalidLLMOutputError as exc:
            logger = structlog.get_logger()
            logger.warning(
                "structured_output_validation_failed",
                case_id=case.id,
                operation="sharpen_case",
                error=str(exc),
            )
            sharpened_title: str | None = None
            sharpened_current_state: str | None = None
            sharpened_desired_state: str | None = None
            improvement_suggestions: tuple[str, ...] = ()
            raw_text: str | None = response.content
        else:
            sharpened_title = parsed.sharpened_title
            sharpened_current_state = parsed.sharpened_current_state
            sharpened_desired_state = parsed.sharpened_desired_state
            improvement_suggestions = tuple(parsed.improvement_suggestions)
            raw_text = None

        sharpened_content_json = json.dumps(
            {
                "sharpened_title": sharpened_title,
                "sharpened_current_state": sharpened_current_state,
                "sharpened_desired_state": sharpened_desired_state,
                "improvement_suggestions": list(improvement_suggestions),
                "raw_text": raw_text,
            }
        )
        await self._repository.update_field_async(
            case.id, "sharpened_content_json", sharpened_content_json
        )

        return SharpenedUseCase(
            case_id=case.id,
            original_title=case.use_case.title,
            original_current_state=case.use_case.current_state,
            original_desired_state=case.use_case.desired_state,
            sharpened_title=sharpened_title,
            sharpened_current_state=sharpened_current_state,
            sharpened_desired_state=sharpened_desired_state,
            improvement_suggestions=improvement_suggestions,
            raw_text=raw_text,
            prompt_version=prompt_version,
        )

    async def propose_solution(
        self, case_id: str, prompt_version: str = "v2"
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

        fields_to_check = {
            "title": case.use_case.title,
            "current_state": case.use_case.current_state,
            "desired_state": case.use_case.desired_state,
            "example_process": case.use_case.example_process,
        }
        detected: dict[str, list[str]] = {
            field_name: patterns
            for field_name, field_value in fields_to_check.items()
            if (patterns := detect_injection_patterns(field_value))
        }
        if detected:
            logger = structlog.get_logger()
            logger.warning(
                "injection_pattern_detected",
                case_id=case.id,
                fields=detected,
            )

        system_prompt = load_prompt("propose_solution", "system", prompt_version)
        user_template = load_prompt("propose_solution", "user", prompt_version)
        user_content = user_template.format(
            title=case.use_case.title,
            current_state=case.use_case.current_state,
            desired_state=case.use_case.desired_state,
            example_process=case.use_case.example_process,
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

        await self._repository.update_field_async(
            case.id, "proposal_text", response.content
        )

        return SolutionProposal(
            case_id=case.id,
            proposal_text=response.content,
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

        system_prompt = load_prompt("compliance_hints", "system", prompt_version)
        user_template = load_prompt("compliance_hints", "user", prompt_version)
        user_content = user_template.format(
            title=case.use_case.title,
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

        return ReportResult(
            case_id=case.id,
            business_summary=_build_business_summary(
                case.result,
                effective_sharpened_text,
                compliance_hint_text,
                compliance_citations,
                case.reviewer_decision.value,
                case.reviewer_note,
                case.decided_at,
            ),
            technical_detail=_build_technical_detail(
                case.result, effective_proposal_text
            ),
        )
