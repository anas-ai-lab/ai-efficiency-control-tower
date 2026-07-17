"""Sprachkataloge fuer alle deterministischen Textbausteine der Domain (V4.1-S6).

Deutsch bleibt die Default-Sprache; Englisch ist die zweite Fassung. Kein
Framework -- reine ``dict``-Kataloge, keyed nach der Sprache (``Lang``). Die
Erklaerbarkeits-, Routing-, Vorfilter- und Machbarkeits-Schicht ziehen ihren
Klartext ausschliesslich hier heraus, statt Strings inline zu halten.

Schicht: domain -- importiert NUR aus ``aect.domain.types`` (StrEnum-Anker).
RoutingRecommendation (in ``routing``) und FeasibilityFlag (in ``feasibility``)
werden bewusst ueber ihren ``.value``-String gekeyt, damit dieses Modul nicht
zyklisch auf ``routing``/``feasibility`` zurueckimportiert.

Invariante (per Test abgesichert): jede sprach-gekeyte Map traegt fuer ``de``
und ``en`` exakt dieselbe innere Schluesselstruktur. Ein fehlender ``en``-Wert
ist ein Fehler, kein stiller Fallback.
"""

from __future__ import annotations

from typing import Literal

from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EvidenceLevel,
    ImplementationApproach,
    TriageZone,
)

#: Unterstuetzte Sprachen. Deutsch ist Default (SDR-0003, V4.1-S6).
Lang = Literal["de", "en"]

#: Reihenfolge/Menge der Sprachen -- zentral, damit Paritaets-Tests iterieren.
LANGS: tuple[Lang, ...] = ("de", "en")

#: Default-Sprache. Endpoints ohne ``lang``-Parameter verhalten sich wie ``de``.
DEFAULT_LANG: Lang = "de"

# ---------------------------------------------------------------------------
# 1. Erklaerbarkeit -- Zonen-, Ansatz-, Datenschutz-, Evidenz-, Verbindlichkeit
# ---------------------------------------------------------------------------

#: Deutsche/englische Zonen-Labels fuer Entscheider (Empfehlungs-/Kipp-Saetze,
#: Berechnungs-Ebene). Bewusst getrennt von den Frontend-ZONE_CONFIG-Labels.
ZONE_LABELS: dict[Lang, dict[TriageZone, str]] = {
    "de": {
        TriageZone.LIKELY_WIN: "Klarer Gewinn",
        TriageZone.CALCULATED_RISK: "Kalkuliertes Risiko",
        TriageZone.MARGINAL_GAIN: "Geringer Nutzen",
    },
    "en": {
        TriageZone.LIKELY_WIN: "Clear win",
        TriageZone.CALCULATED_RISK: "Calculated risk",
        TriageZone.MARGINAL_GAIN: "Marginal gain",
    },
}

#: Machbarkeits-Definition (Score-Breakdown, Board-Daten).
FEASIBILITY_DEFINITION: dict[Lang, str] = {
    "de": "Machbarkeit = 10 - Aufwandscore; hoher Wert = leichter umsetzbar.",
    "en": "Feasibility = 10 - effort score; a higher value is easier to implement.",
}

#: Umsetzungsansatz-Labels (Score-Herkunft, Komplexitaets-Begruendung).
APPROACH_LABEL: dict[Lang, dict[ImplementationApproach, str]] = {
    "de": {
        ImplementationApproach.SIMPLE_INTEGRATION: "Einfache Integration in Bestand",
        ImplementationApproach.DEVELOPMENT_ON_EXISTING: "Entwicklung auf Bestehendem",
        ImplementationApproach.API_INTEGRATION: "API-Anbindung an Bestehendes",
        ImplementationApproach.CUSTOM_DEVELOPMENT: "Eigene Entwicklung",
        ImplementationApproach.NEW_TOOL: "Einführung eines neuen Tools",
    },
    "en": {
        ImplementationApproach.SIMPLE_INTEGRATION: "Simple integration into existing systems",
        ImplementationApproach.DEVELOPMENT_ON_EXISTING: "Development on existing systems",
        ImplementationApproach.API_INTEGRATION: "API integration with existing systems",
        ImplementationApproach.CUSTOM_DEVELOPMENT: "Custom development",
        ImplementationApproach.NEW_TOOL: "Introduction of a new tool",
    },
}

#: Datenschutz-Klartext (Empfehlungssatz, Contra-Punkte, Datenlage).
DATA_CLASSIFICATION_CLARTEXT: dict[Lang, dict[DataClassification, str]] = {
    "de": {
        DataClassification.NO_PERSONAL_DATA: "keine personenbezogenen Daten",
        DataClassification.PSEUDONYMOUS: (
            "pseudonyme Daten (bleiben personenbezogen, Art. 4 Nr. 5 DSGVO)"
        ),
        DataClassification.PERSONAL: "personenbezogene Daten (Art. 4 DSGVO)",
        DataClassification.SENSITIVE_PERSONAL: (
            "besondere Kategorien personenbezogener Daten (Art. 9 DSGVO)"
        ),
    },
    "en": {
        DataClassification.NO_PERSONAL_DATA: "no personal data",
        DataClassification.PSEUDONYMOUS: (
            "pseudonymous data (still personal, Art. 4(5) GDPR)"
        ),
        DataClassification.PERSONAL: "personal data (Art. 4 GDPR)",
        DataClassification.SENSITIVE_PERSONAL: (
            "special categories of personal data (Art. 9 GDPR)"
        ),
    },
}

#: Evidenz-Labels (technischer Report, Datenlage).
EVIDENCE_LABELS: dict[Lang, dict[EvidenceLevel, str]] = {
    "de": {
        EvidenceLevel.PURE_ESTIMATE: "reine Einschätzung",
        EvidenceLevel.SIMILAR_PROJECT: "eigene Erfahrung / Analogieprojekt",
        EvidenceLevel.TESTED_PILOTED: "mit realen Beispielen getestet",
    },
    "en": {
        EvidenceLevel.PURE_ESTIMATE: "pure estimate",
        EvidenceLevel.SIMILAR_PROJECT: "own experience / comparable project",
        EvidenceLevel.TESTED_PILOTED: "tested with real examples",
    },
}

#: Verbindlichkeits-Labels (technischer Report, Datenlage).
ADOPTION_LABELS: dict[Lang, dict[AdoptionType, str]] = {
    "de": {
        AdoptionType.VOLUNTARY: "freiwillige Nutzung",
        AdoptionType.RECOMMENDED_STANDARD: "empfohlener Teamstandard",
        AdoptionType.FIXED_PROCESS_STEP: "fester Prozessschritt",
    },
    "en": {
        AdoptionType.VOLUNTARY: "voluntary use",
        AdoptionType.RECOMMENDED_STANDARD: "recommended team standard",
        AdoptionType.FIXED_PROCESS_STEP: "fixed process step",
    },
}

#: Datenschutz-Begruendung je Klassifizierung (Score-Herkunft).
DATA_PROTECTION_REASON: dict[Lang, dict[DataClassification, str]] = {
    "de": {
        DataClassification.NO_PERSONAL_DATA: "Keine personenbezogenen Daten -> 0 Punkte",
        DataClassification.PSEUDONYMOUS: (
            "Pseudonyme Daten (bleiben personenbezogen, Art. 4 Nr. 5 DSGVO) -> +1"
        ),
        DataClassification.PERSONAL: "Personenbezogene Daten (Art. 4 DSGVO) -> +1",
        DataClassification.SENSITIVE_PERSONAL: (
            "Besondere Kategorien personenbezogener Daten (Art. 9 DSGVO) -> +2"
        ),
    },
    "en": {
        DataClassification.NO_PERSONAL_DATA: "No personal data -> 0 points",
        DataClassification.PSEUDONYMOUS: (
            "Pseudonymous data (still personal, Art. 4(5) GDPR) -> +1"
        ),
        DataClassification.PERSONAL: "Personal data (Art. 4 GDPR) -> +1",
        DataClassification.SENSITIVE_PERSONAL: (
            "Special categories of personal data (Art. 9 GDPR) -> +2"
        ),
    },
}

# ---------------------------------------------------------------------------
# 2. Aufwand + Konfidenz (Anzeige-Uebersetzung der Maschinen-Keys)
# ---------------------------------------------------------------------------

#: Aufwand-Adjektiv fuer den Management-Satz. Keyed am effort_label
#: (NIEDRIG/MITTEL/HOCH -- Maschinen-Key aus scoring.CompositeScore).
EFFORT_ADJEKTIV: dict[Lang, dict[str, str]] = {
    "de": {"NIEDRIG": "niedrigem", "MITTEL": "mittlerem", "HOCH": "hohem"},
    "en": {"NIEDRIG": "low", "MITTEL": "moderate", "HOCH": "high"},
}

#: Verbale Aufwands-Einordnung (Berechnungs-Ebene).
EFFORT_KLARTEXT: dict[Lang, dict[str, str]] = {
    "de": {
        "NIEDRIG": "niedrig -- kurzfristig umsetzbar",
        "MITTEL": "mittel -- mit planbarem Vorlauf umsetzbar",
        "HOCH": "hoch -- erheblicher Umsetzungsaufwand",
    },
    "en": {
        "NIEDRIG": "low -- can be implemented quickly",
        "MITTEL": "moderate -- implementable with plannable lead time",
        "HOCH": "high -- considerable implementation effort",
    },
}

#: Anzeige-Fassung des effort_label (total_line). de: unveraendert (Grossschrift).
EFFORT_LABEL_DISPLAY: dict[Lang, dict[str, str]] = {
    "de": {"NIEDRIG": "NIEDRIG", "MITTEL": "MITTEL", "HOCH": "HOCH"},
    "en": {"NIEDRIG": "LOW", "MITTEL": "MEDIUM", "HOCH": "HIGH"},
}

# CONFIDENCE_LEVEL_DISPLAY (hoch/mittel/niedrig -> Anzeigetext) ist mit V4.1-S9
# entfallen: die Konfidenz-Stufe wird nirgends mehr angezeigt. Sie bleibt
# berechnet und steht als Maschinen-Key im Response (zone.confidence_reasoning.
# level) -- ein Anzeige-Katalog dafuer haette keinen Aufrufer mehr.

# ---------------------------------------------------------------------------
# 3. Empfehlung + Routing-Begruendung (Management-Ebene)
# ---------------------------------------------------------------------------

#: Empfehlung als Klartext-Ansatz (Management-Satz). Keyed am
#: RoutingRecommendation-.value-String (kein Import von routing).
EMPFEHLUNG_ANSATZ: dict[Lang, dict[str, str]] = {
    "de": {
        "AUTOMATION_RECOMMENDED": "Automatisierung (regelbasiert, ohne KI)",
        "AI_RECOMMENDED": "Umsetzung mit KI-Unterstützung",
        "HUMAN_REVIEW_REQUIRED": "fachliche Prüfung vor der Umsetzung",
        "BORDERLINE": "Einzelfallprüfung (die Signale sind gemischt)",
    },
    "en": {
        "AUTOMATION_RECOMMENDED": "automation (rule-based, without AI)",
        "AI_RECOMMENDED": "implementation with AI support",
        "HUMAN_REVIEW_REQUIRED": "expert review before implementation",
        "BORDERLINE": "case-by-case review (signals are mixed)",
    },
}

#: Datenlage-Satz fuer die Zonen-Zusammenfassung (Ebene 1). Sagt in Alltags-
#: sprache, worauf die Schaetzung beruht -- OHNE die frueher angehaengte
#: "Belastbarkeit <hoch/mittel/niedrig>"-Stufe (V4.1-S9): die Stufe war ein
#: internes Konfidenz-Label, das Entscheider ohne die Rechenregel dahinter nicht
#: einordnen konnten. Die Evidenz-Logik selbst ist unveraendert.
BELASTBARKEIT_ZONE_SATZ: dict[Lang, dict[EvidenceLevel, str]] = {
    "de": {
        EvidenceLevel.PURE_ESTIMATE: (
            "Die Schätzung beruht bisher auf Einschätzungen ohne Belege"
        ),
        EvidenceLevel.SIMILAR_PROJECT: (
            "Die Schätzung stützt sich auf Erfahrung aus einem Analogieprojekt"
        ),
        EvidenceLevel.TESTED_PILOTED: (
            "Die Schätzung ist mit realen Beispielen getestet"
        ),
    },
    "en": {
        EvidenceLevel.PURE_ESTIMATE: (
            "The estimate so far rests on assessments without evidence"
        ),
        EvidenceLevel.SIMILAR_PROJECT: (
            "The estimate draws on experience from a comparable project"
        ),
        EvidenceLevel.TESTED_PILOTED: "The estimate is tested with real examples",
    },
}

#: Routing-Begruendung (V4.1-S9): warum GENAU dieser Weg empfohlen wird.
#: Keyed nach dem Zweig der Entscheidungsmatrix in routing._decide -- die Zweige
#: werden am Response-Rand aus den Signal-ZAEHLERN re-abgeleitet (dieselbe Regel,
#: keine zweite Wahrheit). {gruende} traegt die tatsaechlich erkannten Kriterien.
ROUTING_BEGRUENDUNG: dict[Lang, dict[str, str]] = {
    "de": {
        "human_review": (
            "Mindestens zwei Risikohinweise erzwingen eine fachliche Prüfung -- "
            "unabhängig von Nutzen und Aufwand: {gruende}"
        ),
        "auto_clear": (
            "Ausschlaggebend für Automatisierung; kein Kriterium sprach für KI: "
            "{gruende}"
        ),
        "ai_clear": (
            "Ausschlaggebend für KI; kein Kriterium sprach für Automatisierung: "
            "{gruende}"
        ),
        "auto_majority": (
            "Beide Seiten hatten Kriterien, für Automatisierung sprachen mehr: "
            "{gruende}"
        ),
        "ai_majority": (
            "Beide Seiten hatten Kriterien, für KI sprachen mehr: {gruende}"
        ),
        "borderline_tie": (
            "Kein Weg überwiegt -- für beide Seiten sprachen gleich viele "
            "Kriterien: {gruende}"
        ),
        "borderline_none": (
            "Die Regeln erkennen weder für Automatisierung noch für KI ein "
            "Kriterium -- deshalb die Einzelfallprüfung."
        ),
    },
    "en": {
        "human_review": (
            "At least two risk indicators force an expert review -- regardless of "
            "benefit and effort: {gruende}"
        ),
        "auto_clear": ("Decisive for automation; no criterion spoke for AI: {gruende}"),
        "ai_clear": ("Decisive for AI; no criterion spoke for automation: {gruende}"),
        "auto_majority": (
            "Both sides had criteria, more spoke for automation: {gruende}"
        ),
        "ai_majority": "Both sides had criteria, more spoke for AI: {gruende}",
        "borderline_tie": (
            "Neither path prevails -- both sides had the same number of criteria: "
            "{gruende}"
        ),
        "borderline_none": (
            "The rules find no criterion for automation or for AI -- hence the "
            "case-by-case review."
        ),
    },
}

#: Formel des erwarteten Nutzens in Worten (Berechnungs-Ebene). ASCII-"x".
NUTZEN_FORMEL_WORTE: dict[Lang, str] = {
    "de": (
        "Minuten pro Vorgang x Vorgänge pro Mitarbeiter und Jahr x betroffene "
        "Mitarbeiter x Stundensatz, anschließend gedämpft nach Datenlage und "
        "erwarteter Nutzung."
    ),
    "en": (
        "minutes per case x cases per employee per year x affected employees x "
        "hourly rate, then damped by the evidence base and the expected adoption."
    ),
}

#: Erklaerung der Basis-Einstufung (Berechnungs-Ebene).
BASIS_EINSTUFUNG_ERKLAERUNG: dict[Lang, str] = {
    "de": (
        "Einstufung allein aus erwartetem Nutzen und Aufwand; der Handlungsdruck "
        "kann sie danach noch hochstufen."
    ),
    "en": (
        "Classification from expected benefit and effort alone; the urgency signal "
        "can still upgrade it afterwards."
    ),
}

# ---------------------------------------------------------------------------
# 4. Inline-Templates + Labels der build_*-Funktionen (Erklaerbarkeit)
# ---------------------------------------------------------------------------

#: Score-Komponenten-Labels (Aufwandscore-Herkunft).
SCORE_COMPONENT_LABELS: dict[Lang, dict[str, str]] = {
    "de": {
        "complexity": "Komplexität",
        "cost": "Kosten",
        "data_protection": "Datenschutz",
    },
    "en": {
        "complexity": "Complexity",
        "cost": "Cost",
        "data_protection": "Data protection",
    },
}

# COST_LABELS (Lizenzkosten/Implementierungskosten/-Jahr als Bausteine) ist mit
# V4.1-S9 entfallen: die Kostenbegruendung ist jetzt EIN fertiger Satz je Ausgang
# (EXPLAIN_TEXT cost_*) statt einer aus Label + Betrag + Schwelle
# zusammengesetzten Vergleichskette.

#: Berechnungs-Ebenen-Labels (Ebene 2). Die frueher vierte Zeile "Belastbarkeit"
#: (Stufe + "Angesetzt werden 40 % des theoretischen Potenzials ...") entfaellt
#: (V4.1-S9) -- der Kipp-Hinweis daraus haengt jetzt an der Basis-Einstufung, wo
#: er hingehoert (er beschreibt genau deren Kippen).
BERECHNUNG_LABELS: dict[Lang, dict[str, str]] = {
    "de": {
        "benefit": "Erwarteter Nutzen",
        "effort": "Aufwand",
        "base_zone": "Basis-Einstufung vor Dämpfung",
    },
    "en": {
        "benefit": "Expected Benefit",
        "effort": "Effort",
        "base_zone": "Base classification before damping",
    },
}

#: Freitext-Bausteine der Erklaerbarkeit, die als Ganzes uebersetzt werden.
#: Templates behalten die Platzhalter ({...}); die Formel-Argumente sind
#: sprachneutrale Zahlen. Marker-Wort ``flip`` erkennt den Kipp-Satz sprachweise.
EXPLAIN_TEXT: dict[Lang, dict[str, str]] = {
    "de": {
        "flip_marker": "kippt",
        "complexity_reason": "{approach} -> Komplexität {n} von 5",
        # Kostenpunkte kompakt (V4.1-S9): frueher zwei aneinandergehaengte
        # Vergleichsketten ("Lizenzkosten 0 EUR/Jahr < 10.000 EUR -> kein Punkt;
        # Implementierungskosten ..."). Ein Satz je Ausgang statt der Rechnung.
        # Die _same-Varianten greifen nur, wenn beide Schwellen identisch sind
        # (Default); bei abweichenden Schwellen nennen die _diff-Varianten beide.
        "cost_none_same": (
            "Lizenz- und Implementierungskosten unter {threshold} -- keine "
            "Aufwandspunkte."
        ),
        "cost_both_same": (
            "Lizenz- und Implementierungskosten ab {threshold} -- +2 Aufwandspunkte."
        ),
        "cost_none_diff": (
            "Lizenzkosten unter {license_threshold}, Implementierungskosten unter "
            "{impl_threshold} -- keine Aufwandspunkte."
        ),
        "cost_both_diff": (
            "Lizenzkosten ab {license_threshold}, Implementierungskosten ab "
            "{impl_threshold} -- +2 Aufwandspunkte."
        ),
        "cost_license_only": (
            "Lizenzkosten ab {license_threshold} -- +1 Aufwandspunkt; "
            "Implementierungskosten darunter."
        ),
        "cost_impl_only": (
            "Implementierungskosten ab {impl_threshold} -- +1 Aufwandspunkt; "
            "Lizenzkosten darunter."
        ),
        "total_line": "Aufwandscore {total} von {max} -> {effort}",
        "pure_estimate_grund": (
            "Nutzen basiert auf reiner Einschätzung (Faktor {factor})."
        ),
        "clear_margin_grund": (
            "Evidenz gemessen und deutlicher Abstand zu allen Zonengrenzen."
        ),
        "flip_benefit": (
            "Mit {pct} % {richtung} erwartetem Nutzen kippt der Case von "
            "{from_zone} nach {to_zone}."
        ),
        "flip_composite": (
            "Mit {points} {richtung} kippt der Case von {from_zone} nach {to_zone}."
        ),
        "richtung_less": "weniger",
        "richtung_more": "mehr",
        "point_singular": "einem Aufwandspunkt",
        "point_plural": "{n} Aufwandspunkten",
        "eval_pending": (
            "Noch nicht bewertet: der Implementierungsansatz fehlt. Ein Admin "
            "trägt ihn nach, danach wird der Fall vollständig bewertet."
        ),
        "not_recommended_no_time": (
            "Nicht zur Umsetzung empfohlen: der Vorgang mit KI ist nicht schneller "
            "als heute -- kein Zeitgewinn."
        ),
        "not_recommended_prefilter": (
            "Nicht zur Umsetzung empfohlen: Vorfilter nicht bestanden ({criteria})."
        ),
        "benefit_per_year": "{eur} / Jahr",
        # Ohne "-- Belastbarkeit <level>" (V4.1-S9). {bel_zone} bleibt: der Satz
        # sagt in Alltagssprache, worauf die Schaetzung beruht, ohne die interne
        # Konfidenz-Stufe zu nennen.
        "zonen_satz": (
            "Erwarteter Nutzen rund {eur} pro Jahr bei {adjektiv} "
            "Umsetzungsaufwand. {bel_zone}."
        ),
        # Ohne "Belastbarkeit der Empfehlung: <level>" (V4.1-S9). Die
        # fallspezifische Begruendung liefert routing.begruendung daneben.
        "empfehlung_satz": "Empfehlung: {ansatz}.",
    },
    "en": {
        "flip_marker": "flips",
        "complexity_reason": "{approach} -> complexity {n} of 5",
        "cost_none_same": (
            "License and implementation cost below {threshold} -- no effort points."
        ),
        "cost_both_same": (
            "License and implementation cost at or above {threshold} -- "
            "+2 effort points."
        ),
        "cost_none_diff": (
            "License cost below {license_threshold}, implementation cost below "
            "{impl_threshold} -- no effort points."
        ),
        "cost_both_diff": (
            "License cost at or above {license_threshold}, implementation cost at "
            "or above {impl_threshold} -- +2 effort points."
        ),
        "cost_license_only": (
            "License cost at or above {license_threshold} -- +1 effort point; "
            "implementation cost below it."
        ),
        "cost_impl_only": (
            "Implementation cost at or above {impl_threshold} -- +1 effort point; "
            "license cost below it."
        ),
        "total_line": "Effort score {total} of {max} -> {effort}",
        "pure_estimate_grund": (
            "Benefit is based on a pure estimate (factor {factor})."
        ),
        "clear_margin_grund": (
            "Evidence measured and a clear margin to all zone boundaries."
        ),
        "flip_benefit": (
            "With {pct} % {richtung} expected benefit the case flips from "
            "{from_zone} to {to_zone}."
        ),
        "flip_composite": (
            "With {points} {richtung} the case flips from {from_zone} to {to_zone}."
        ),
        "richtung_less": "less",
        "richtung_more": "more",
        "point_singular": "one effort point",
        "point_plural": "{n} effort points",
        "eval_pending": (
            "Not evaluated yet: the implementation approach is missing. An admin "
            "adds it, after which the case is fully evaluated."
        ),
        "not_recommended_no_time": (
            "Not recommended for implementation: the process with AI is not faster "
            "than today -- no time saved."
        ),
        "not_recommended_prefilter": (
            "Not recommended for implementation: prefilter not passed ({criteria})."
        ),
        "benefit_per_year": "{eur} / year",
        "zonen_satz": (
            "Expected benefit around {eur} per year at {adjektiv} implementation "
            "effort. {bel_zone}."
        ),
        "empfehlung_satz": "Recommendation: {ansatz}.",
    },
}

#: Empfehlungs-Satz-Templates (build_recommendation_text). Feste Argument-
#: Reihenfolge: eingesparte Stunden/Jahr -> Netto-Nutzen -> Aufwand -> Datenlage.
RECOMMENDATION_TEMPLATES: dict[Lang, dict[str, str]] = {
    "de": {
        "AUTOMATION_RECOMMENDED": (
            "Automatisierung empfohlen: rechnerisch {h} eingesparte Stunden pro "
            "Jahr ({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
        ),
        "AI_RECOMMENDED": (
            "AI-Einsatz empfohlen: rechnerisch {h} eingesparte Stunden pro Jahr "
            "({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
        ),
        "HUMAN_REVIEW_REQUIRED": (
            "Vor Umsetzung fachliche Prüfung erforderlich: {h} eingesparte Stunden "
            "pro Jahr ({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
        ),
        "BORDERLINE": (
            "Mischsignale, Einzelfallprüfung empfohlen: {h} eingesparte Stunden "
            "pro Jahr ({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
        ),
    },
    "en": {
        "AUTOMATION_RECOMMENDED": (
            "Automation recommended: about {h} hours saved per year "
            "({netto} EUR net benefit) at effort {x} of 9 and {dp}."
        ),
        "AI_RECOMMENDED": (
            "AI use recommended: about {h} hours saved per year "
            "({netto} EUR net benefit) at effort {x} of 9 and {dp}."
        ),
        "HUMAN_REVIEW_REQUIRED": (
            "Expert review required before implementation: {h} hours saved per year "
            "({netto} EUR net benefit) at effort {x} of 9 and {dp}."
        ),
        "BORDERLINE": (
            "Mixed signals, case-by-case review recommended: {h} hours saved per "
            "year ({netto} EUR net benefit) at effort {x} of 9 and {dp}."
        ),
    },
}

#: "Zu entscheiden"-Satz je Empfehlung (Entscheider-Report).
ZU_ENTSCHEIDEN: dict[Lang, dict[str, str]] = {
    "de": {
        "AUTOMATION_RECOMMENDED": (
            "Freigabe zur Umsetzung als klassische Automatisierung "
            "(ohne AI-Komponente)."
        ),
        "AI_RECOMMENDED": "Freigabe zur Umsetzung mit AI-Komponente.",
        "HUMAN_REVIEW_REQUIRED": (
            "Freigabe einer vertieften fachlichen und datenschutzrechtlichen "
            "Prüfung vor der Umsetzung."
        ),
        "BORDERLINE": (
            "Entscheidung über eine Einzelfallprüfung -- die Signale sind gemischt."
        ),
    },
    "en": {
        "AUTOMATION_RECOMMENDED": (
            "Approval to implement as classic automation (without an AI component)."
        ),
        "AI_RECOMMENDED": "Approval to implement with an AI component.",
        "HUMAN_REVIEW_REQUIRED": (
            "Approval of an in-depth expert and data-protection review before "
            "implementation."
        ),
        "BORDERLINE": ("Decision on a case-by-case review -- the signals are mixed."),
    },
}

#: "Zu entscheiden"-Satz bei Vorfilter-Fail.
ZU_ENTSCHEIDEN_FAIL: dict[Lang, str] = {
    "de": (
        "Keine Freigabe -- der Case erfuellt die Mindestkriterien des Vorfilters nicht."
    ),
    "en": (
        "No approval -- the case does not meet the minimum criteria of the prefilter."
    ),
}

#: Contra-Punkte (Entscheider-Report). Keyed nach stabilem Grund-Schluessel.
CONTRA_POINTS: dict[Lang, dict[str, str]] = {
    "de": {
        "pure_estimate": (
            "Der erwartete Nutzen beruht auf einer reinen Einschätzung -- keine "
            "gemessene Grundlage."
        ),
        "voluntary": (
            "Die Nutzung ist freiwillig -- ohne Verbindlichkeit bleibt die "
            "tatsaechliche Adoption unsicher."
        ),
        "data_sensitive": (
            "Besondere Kategorien personenbezogener Daten (Art. 9 DSGVO) -- "
            "Datenschutz-Folgenabschaetzung erforderlich."
        ),
        "data_personal": (
            "Es werden personenbezogene Daten verarbeitet -- Datenschutzaufwand "
            "einplanen."
        ),
        "cost": (
            "Der Aufwandscore trägt Kostenpunkte (Lizenz- und/oder "
            "Implementierungskosten oberhalb der Schwelle)."
        ),
        "boundary": (
            "Der Case liegt nahe an einer Zonengrenze -- kleine Änderungen an "
            "Nutzen oder Aufwand kippen die Einstufung."
        ),
        "no_time": (
            "Der Vorgang spart mit KI keine Zeit -- der wirtschaftliche Nutzen ist "
            "fraglich."
        ),
        "little_time": (
            "Die Zeitersparnis pro Vorgang ist mit unter 3 Minuten knapp -- der "
            "Nutzen hängt stark am Volumen."
        ),
        "fallback_no_validation": (
            "Bewertung beruht vollständig auf Angaben des Einreichers; keine "
            "unabhängige Validierung."
        ),
        "fallback_ex_ante": (
            "Die Bewertung ist eine Ex-ante-Schaetzung -- der tatsaechliche Nutzen "
            "zeigt sich erst nach der Umsetzung."
        ),
    },
    "en": {
        "pure_estimate": (
            "The expected benefit rests on a pure estimate -- no measured basis."
        ),
        "voluntary": (
            "Use is voluntary -- without commitment, actual adoption remains uncertain."
        ),
        "data_sensitive": (
            "Special categories of personal data (Art. 9 GDPR) -- a data protection "
            "impact assessment is required."
        ),
        "data_personal": (
            "Personal data is processed -- plan for data protection effort."
        ),
        "cost": (
            "The effort score carries cost points (license and/or implementation "
            "cost above the threshold)."
        ),
        "boundary": (
            "The case is close to a zone boundary -- small changes to benefit or "
            "effort flip the classification."
        ),
        "no_time": (
            "The process saves no time with AI -- the economic benefit is questionable."
        ),
        "little_time": (
            "The time saved per case is tight at under 3 minutes -- the benefit "
            "depends heavily on volume."
        ),
        "fallback_no_validation": (
            "The assessment rests entirely on the submitter's data; no independent "
            "validation."
        ),
        "fallback_ex_ante": (
            "The assessment is an ex-ante estimate -- the actual benefit only shows "
            "after implementation."
        ),
    },
}

# ---------------------------------------------------------------------------
# 5. Routing-Signale (Automation-/AI-/Risk-Sammler)
# ---------------------------------------------------------------------------
# Loest den TODO(S6/i18n) aus routing.py ab: Fliesstext uebersetzt, echte
# Umlaute; Enum-Werte in Klammern (pure_estimate) bleiben unangetastet.

#: Signal-/Flag-Templates der drei Sammler. Keyed nach stabilem Schluessel.
ROUTING_SIGNALS: dict[Lang, dict[str, str]] = {
    "de": {
        "auto_simple": (
            "Komplexität {complexity} <= {threshold} -- einfacher, regelbasierter "
            "Ablauf"
        ),
        "auto_volume": (
            "Volumen {volume}/Jahr je MA >= {threshold} -- hoher Automatisierungs-ROI"
        ),
        "auto_fixed": (
            "Fester Prozessschritt -- konsistentes Nutzungsverhalten begünstigt "
            "Automatisierung"
        ),
        "ai_complex": (
            "Komplexität {complexity} >= {threshold} -- kontextabhängige, ambigue "
            "Aufgabe"
        ),
        "ai_estimate": (
            "Schätzqualität gering (pure_estimate) -- AI für explorativen, "
            "unsicheren Anwendungsfall geeignet"
        ),
        "ai_ambiguous": (
            "Soll-Beschreibung {length} Zeichen -- mehrdimensionale Anforderung "
            "deutet auf AI-Bedarf hin"
        ),
        "risk_sensitive": (
            "Sensible Personendaten (Art. 9 DSGVO) -- DSFA-Prüfung und Human Review "
            "vor Umsetzung erforderlich"
        ),
        "risk_regulatory": (
            "Regulatorischer Druck + PII-Verarbeitung -- Human Review und "
            "Datenschutzfolgenabschätzung empfohlen"
        ),
    },
    "en": {
        "auto_simple": (
            "Complexity {complexity} <= {threshold} -- simple, rule-based workflow"
        ),
        "auto_volume": (
            "Volume {volume}/year per employee >= {threshold} -- high automation ROI"
        ),
        "auto_fixed": ("Fixed process step -- consistent usage favors automation"),
        "ai_complex": (
            "Complexity {complexity} >= {threshold} -- context-dependent, ambiguous "
            "task"
        ),
        "ai_estimate": (
            "Low estimate quality (pure_estimate) -- AI suited to an exploratory, "
            "uncertain use case"
        ),
        "ai_ambiguous": (
            "Target description {length} characters -- multi-dimensional requirement "
            "suggests a need for AI"
        ),
        "risk_sensitive": (
            "Sensitive personal data (Art. 9 GDPR) -- DPIA review and human review "
            "required before implementation"
        ),
        "risk_regulatory": (
            "Regulatory pressure + PII processing -- human review and data "
            "protection impact assessment recommended"
        ),
    },
}

# ---------------------------------------------------------------------------
# 6. Vorfilter-Kriterien (Namen der drei Mindestkriterien)
# ---------------------------------------------------------------------------

#: Kriteriums-Namen, keyed nach stabilem Schluessel. Die Domain (filters.py)
#: haelt die deutschen Namen als dict-Keys (Audit-Trail unveraendert); dieser
#: Katalog uebersetzt sie am Response-Rand.
VORFILTER_CRITERIA: dict[Lang, dict[str, str]] = {
    "de": {
        "potential": "Theoretisches Potenzial",
        "hours": "Stundeneinsparung",
        "net_benefit": "Nettonutzen",
    },
    "en": {
        "potential": "Theoretical potential",
        "hours": "Hours saved",
        "net_benefit": "Net benefit",
    },
}

#: Rueckwaerts-Map: kanonischer deutscher Kriteriums-Name -> stabiler Schluessel.
#: Erlaubt die Uebersetzung der persistierten (deutschen) failed_criteria am
#: Response-Rand, ohne die Vorfilter-Logik anzufassen.
_VORFILTER_KEY_BY_DE: dict[str, str] = {
    de_name: key for key, de_name in VORFILTER_CRITERIA["de"].items()
}


def localize_vorfilter_criteria(failed_criteria: list[str], lang: Lang) -> list[str]:
    """Uebersetzt die persistierten (deutschen) Vorfilter-Kriteriums-Namen.

    Unbekannte Namen (sollten nicht vorkommen) werden unveraendert
    durchgereicht -- fail-safe fuer die Anzeige, nie ein Crash.
    """
    catalog = VORFILTER_CRITERIA[lang]
    out: list[str] = []
    for name in failed_criteria:
        key = _VORFILTER_KEY_BY_DE.get(name)
        out.append(catalog[key] if key is not None else name)
    return out


# ---------------------------------------------------------------------------
# 7. Machbarkeit (Feasibility) -- Flag-Saetze + Assemblierung
# ---------------------------------------------------------------------------

#: Machbarkeits-Empfehlungs-Bausteine, keyed nach FeasibilityFlag.value.
FEASIBILITY_RECOMMENDATION: dict[Lang, dict[str, str]] = {
    "de": {
        "DESCRIPTION_TOO_VAGUE": (
            "Ist- und Soll-Zustand ausführlicher beschreiben "
            "(mind. {min_len} Zeichen je Feld)."
        ),
        "MISSING_EXAMPLE": "Konkreten Beispielvorgang ergänzen.",
        "NO_TIME_SAVING": "Zeitersparnis pro Vorgang muss größer 0 sein.",
        "NOT_RECURRING": (
            "Vorgangshäufigkeit (pro Monat) muss angegeben und größer 0 sein."
        ),
    },
    "en": {
        "DESCRIPTION_TOO_VAGUE": (
            "Describe the current and target state in more detail "
            "(at least {min_len} characters per field)."
        ),
        "MISSING_EXAMPLE": "Add a concrete example process.",
        "NO_TIME_SAVING": "Time saved per case must be greater than 0.",
        "NOT_RECURRING": (
            "Case frequency (per month) must be provided and greater than 0."
        ),
    },
}

# ---------------------------------------------------------------------------
# 8. Technischer Report (Datenlage / Risiken / offene Fragen)
# ---------------------------------------------------------------------------

TECHNICAL_REPORT: dict[Lang, dict[str, str]] = {
    "de": {
        # Ohne Endpoint-Angabe (V4.1-S9): der Platzhalter zeigte einem Fachnutzer
        # eine API-Route, mit der er nichts anfangen kann. Jetzt der Weg durch die
        # Oberflaeche -- der Button-Name ist der aus caseTools.solution.
        "architektur_placeholder": (
            "Noch kein Lösungsvorschlag erzeugt -- über den Button "
            '"Lösungsvorschlag" im Bereich Werkzeuge starten.'
        ),
        "datenlage": (
            "Datenschutz: {datenschutz}. Evidenz: {evidenz}. "
            "Verbindlichkeit: {verbindlichkeit}."
        ),
        # Nennt die tatsaechlich geprueften Kategorien (domain/routing.
        # _collect_risk_flags prueft genau diese zwei) statt "keine Flags"
        # (V4.1-S9): "keine Risikoflags" sagt nicht, WORAUF geprueft wurde.
        "risiken_none": (
            "Die automatische Prüfung hat keine Risikofaktoren erkannt. Geprüft "
            "wurden: besondere Kategorien personenbezogener Daten (Art. 9 DSGVO) "
            "sowie regulatorischer Druck in Verbindung mit personenbezogenen Daten."
        ),
        "offene_solution": "Technischer Lösungsansatz noch offen.",
        "offene_review": "Fachliche/datenschutzrechtliche Prüfung offen.",
        "offene_estimate": "Zeitersparnis ist unbelegt (reine Einschätzung).",
        "offene_none": "Keine offenen technischen Fragen erkennbar.",
    },
    "en": {
        "architektur_placeholder": (
            "No solution proposal generated yet -- start it via the "
            '"Propose solution" button in the tools section.'
        ),
        "datenlage": (
            "Data protection: {datenschutz}. Evidence: {evidenz}. "
            "Commitment: {verbindlichkeit}."
        ),
        "risiken_none": (
            "The automated check found no risk factors. Checked: special categories "
            "of personal data (Art. 9 GDPR) and regulatory pressure in combination "
            "with personal data."
        ),
        "offene_solution": "Technical solution approach still open.",
        "offene_review": "Expert / data-protection review still open.",
        "offene_estimate": "Time saving is unproven (pure estimate).",
        "offene_none": "No open technical questions identified.",
    },
}

# ---------------------------------------------------------------------------
# 8. Deterministische Compliance-Texte
# ---------------------------------------------------------------------------

#: Compliance-Bausteine, die die Regel-Schicht selbst formuliert (KEIN
#: LLM-Ergebnis). ``kb_unavailable`` ist die ehrliche Fail-loud-Antwort, wenn
#: das Retrieval nur mock-praefigierte Quellen liefert -- die echte Wissensbasis
#: ist dann nicht verdrahtet (s. service.generate_compliance_hints). Lag bis
#: V4.1 als deutschsprachige Modul-Konstante in der Application-Schicht und war
#: damit der einzige nutzerseitige Text ausserhalb der Kataloge -- bei lang=en
#: erschien er trotzdem auf Deutsch.
COMPLIANCE_TEXT: dict[Lang, dict[str, str]] = {
    "de": {
        "kb_unavailable": (
            "Wissensbasis nicht verfügbar -- keine belegten Compliance-Hinweise "
            "möglich."
        ),
    },
    "en": {
        "kb_unavailable": (
            "Knowledge base unavailable -- no evidence-backed compliance hints "
            "possible."
        ),
    },
}
