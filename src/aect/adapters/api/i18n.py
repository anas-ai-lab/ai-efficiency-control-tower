"""Sprachkatalog fuer darstellbare HTTP-Fehlerdetails (V4.1-S6).

Nur die *anzeigbaren* 4xx/5xx-``detail``-Texte, die als deutsche/englische Prosa
im UI landen (Guard-Verletzungen, "kein offener Entwurf", Schema-Verstoesse,
KI-nicht-erreichbar). Der API-Vertrags-Englisch-Anteil ("Case not found",
"Invalid password") bleibt bewusst englisch und wird NICHT hier gefuehrt -- er
ist maschinennah und wird im Frontend gemappt.

Schicht: adapters -- HTTP ist eine Adapter-Sorge. Importiert ``Lang`` aus der
Domain (reiner Typ). Paritaet de/en per Test abgesichert.
"""

from __future__ import annotations

from aect.domain.i18n import Lang

#: Darstellbare Fehlerdetails, keyed nach stabilem Schluessel. Templates mit
#: ``{exc}`` tragen die (bereits redigierte) Schema-Fehlerbeschreibung.
API_ERRORS: dict[Lang, dict[str, str]] = {
    "de": {
        "sharpen_invented_numbers": (
            "Die Schärfung enthielt Zahlen, die nicht im Original stehen, auch "
            "nach einem Korrektur-Versuch."
        ),
        "sharpen_schema": "KI-Antwort verletzt das Schärfungs-Schema: {exc}",
        "no_sharpening_draft": "Kein offener Schärfungs-Entwurf für diesen Case.",
        "solution_forbidden_vocab": (
            "Der Geschäftsleitungs-Absatz enthielt technisches Vokabular, auch "
            "nach einem Korrektur-Versuch."
        ),
        "solution_schema": "KI-Antwort verletzt das Lösungs-Schema: {exc}",
        "no_solution_draft": "Kein offener Lösungs-Entwurf für diesen Case.",
        "sketch_no_proposal": (
            "Fuer diesen Use Case liegt kein Loesungsvorschlag vor -- Skizze "
            "nicht moeglich."
        ),
        "sketch_schema": "KI-Antwort verletzt das Skizzen-Schema: {exc}",
        "sketch_internal": "Interner Fehler bei der Skizzen-Erzeugung.",
        "ideation_unusable": "KI-Antwort war nicht verwertbar -- bitte erneut versuchen.",
        "llm_unavailable": (
            "KI-Dienst derzeit nicht erreichbar -- bitte spaeter erneut versuchen."
        ),
    },
    "en": {
        "sharpen_invented_numbers": (
            "The refinement contained numbers not present in the original, even "
            "after a correction attempt."
        ),
        "sharpen_schema": "AI response violates the refinement schema: {exc}",
        "no_sharpening_draft": "No open refinement draft for this case.",
        "solution_forbidden_vocab": (
            "The management paragraph contained technical vocabulary, even after a "
            "correction attempt."
        ),
        "solution_schema": "AI response violates the solution schema: {exc}",
        "no_solution_draft": "No open solution draft for this case.",
        "sketch_no_proposal": (
            "There is no solution proposal for this use case -- a sketch is not "
            "possible."
        ),
        "sketch_schema": "AI response violates the sketch schema: {exc}",
        "sketch_internal": "Internal error while generating the sketch.",
        "ideation_unusable": "The AI response was not usable -- please try again.",
        "llm_unavailable": (
            "The AI service is currently unavailable -- please try again later."
        ),
    },
}
