"""MockRetriever -- deterministischer Retriever fuer Tests und lokale Entwicklung."""

from __future__ import annotations

from aect.application.ports.retriever import RetrievedChunk

# Synthetische Platzhalter-Wissensbasis -- bewusst generisch, keine kuratierten
# Quellen und keine firmenspezifischen Werte (vertraglich bedingte IP-Trennung). Echte
# kuratierte Inhalte (DSGVO-/EU-AI-Act-Auszuege, Stack-Doku) folgen als
# Markdown-Dateien in knowledge_base/ (Folge-Tage). (text, source_id)-Paare:
_MOCK_CORPUS: tuple[tuple[str, str], ...] = (
    (
        "Open WebUI ist eine selbst-gehostete Open-Source-Chatoberflaeche "
        "fuer LLMs, geeignet fuer interne Pilotierung ohne Lizenzkosten.",
        "mock-stack-open-webui",
    ),
    (
        "Eine Datenschutz-Folgenabschaetzung kann erforderlich sein, wenn eine "
        "Verarbeitung voraussichtlich ein hohes Risiko fuer Betroffene birgt.",
        "mock-compliance-dsfa",
    ),
    (
        "Reciprocal Rank Fusion kombiniert mehrere Ergebnislisten zu einer "
        "gemeinsamen Rangfolge, ohne die Scores direkt vergleichen zu muessen.",
        "mock-retrieval-rrf",
    ),
)


class MockRetriever:
    """Implementiert RetrieverPort ohne echte Suche.

    Haelt eine feste, synthetische Wissensbasis und bewertet jeden Eintrag
    deterministisch nach der Anzahl uebereinstimmender Query-Token
    (Gross-/Kleinschreibung ignoriert, naives Substring-Matching). Rueckgabe:
    nur Treffer mit Score > 0, nach Score absteigend, bei Gleichstand in
    Ursprungsreihenfolge (stabil), hoechstens top_k. Leere Liste, wenn nichts
    passt. Macht Retrieval-Tests reproduzierbar ohne Netzwerk, Embeddings oder
    Kosten. Implementiert RetrieverPort via strukturellem Subtyping.

    Bewusste Einschraenkung: kein semantisches Verstaendnis -- reines
    Token-Matching, analog dazu, dass MockLLMAdapter nur den letzten
    User-Content echo't. Echte Relevanz liefert erst ein Vektor-/Hybrid-Adapter
    (adapters/rag/, Folge-Tage).
    """

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_tokens = query.lower().split()
        scored: list[tuple[int, int, RetrievedChunk]] = []
        for index, (text, source_id) in enumerate(_MOCK_CORPUS):
            text_lower = text.lower()
            matches = sum(1 for token in query_tokens if token in text_lower)
            if matches == 0:
                continue
            chunk = RetrievedChunk(text=text, source_id=source_id, score=float(matches))
            scored.append((matches, index, chunk))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [chunk for _, _, chunk in scored[:top_k]]

    async def delete_by_source_id(self, source_id: str) -> None:
        """No-op (ADR-0038): das synthetische Mock-Korpus ist statisch und
        enthaelt keine personenbezogenen Daten -- nichts zu loeschen."""
        return None
