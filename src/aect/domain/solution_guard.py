"""Deterministischer Vokabular-Guard fuer den Geschaeftsleitungs-Absatz (V4-P6).

Der solution_business-Absatz beschreibt, was sich im Arbeitsalltag aendert -- wer
was tut, was beim Menschen bleibt. VERBOTEN ist Technologie-/Produkt- und
Architektur-Vokabular (Abkuerzungen wie OCR/LLM/API/ERP, Produktnamen,
Architekturbegriffe). Analog zum Zahlen-Guard fuer die Schaerfung
(domain/sharpening_guard) ist dies eine reine, deterministische Regel-Pruefung --
kein LLM. Der Aufrufer (application/service.propose_solution) faehrt bei einem
Treffer genau EINEN Korrektur-Retry und wirft danach 422 (Fail loud).

Schicht: domain -- kein Framework-Import, kein I/O.
"""

from __future__ import annotations

import re

# Denylist (lowercase, exakte Wort-Treffer). Bewusst fokussiert auf eindeutig
# technische Begriffe -- generische Woerter (z. B. "System", "KI") bleiben
# erlaubt, da der Absatz einen AI-Use-Case beschreibt.
_FORBIDDEN_TERMS: frozenset[str] = frozenset(
    {
        # Abkuerzungen
        "ocr",
        "llm",
        "llms",
        "api",
        "apis",
        "erp",
        "sdk",
        "sql",
        "nlp",
        "etl",
        "crm",
        "rpa",
        "json",
        "xml",
        "rest",
        "http",
        "https",
        "gpu",
        "saas",
        "ide",
        "orm",
        "gui",
        "cli",
        # Produkt-/Technologienamen
        "sap",
        "azure",
        "openai",
        "gpt",
        "chatgpt",
        "python",
        "docker",
        "kubernetes",
        "chromadb",
        "fastapi",
        "postgres",
        "postgresql",
        "sqlite",
        "redis",
        "chroma",
        "presidio",
        "langchain",
        "tesseract",
        "whisper",
        # Architektur-Vokabular
        "microservice",
        "microservices",
        "backend",
        "frontend",
        "datenbank",
        "datenbanken",
        "vektordatenbank",
        "endpoint",
        "endpoints",
        "endpunkt",
        "deployment",
        "pipeline",
        "pipelines",
        "embedding",
        "embeddings",
        "repository",
        "middleware",
        "framework",
        "webhook",
        "prompt",
        "prompts",
        "inferenz",
    }
)

# Wort-Tokenizer (inkl. deutscher Umlaute). Wort-Grenzen ueber die Tokenisierung
# statt \b-Regex je Term -- kein Substring-Fehltreffer (z. B. "API" in "Therapie").
_WORD_RE = re.compile(r"[0-9A-Za-zÄÖÜäöüß]+")


def find_vocabulary_violations(text: str) -> list[str]:
    """Findet verbotene technische Begriffe im Geschaeftsleitungs-Absatz.

    Exakte, case-insensitive Wort-Treffer gegen die Denylist. Rueckgabe: die
    verletzenden Original-Surface-Formen in Reihenfolge des ersten Auftretens
    (dedupliziert). Leere Liste = sauber.
    """
    seen: list[str] = []
    lowered_seen: set[str] = set()
    for match in _WORD_RE.finditer(text):
        surface = match.group(0)
        lowered = surface.lower()
        if lowered in _FORBIDDEN_TERMS and lowered not in lowered_seen:
            seen.append(surface)
            lowered_seen.add(lowered)
    return seen
