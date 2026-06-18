"""Chunker -- teilt Wissensbasis-Dokumente in einbettbare Stuecke (Phase D).

Bindeglied zwischen kuratierten Markdown-Quellen (Folge-Tage:
knowledge_base/) und EmbedderPort (ADR-0015): embed() braucht Saetze/
Absaetze passender Groesse, nicht ein ganzes Dokument als einen Text -- ein
zu langer Text wuerde ein Embedding-Modell entweder abschneiden oder die
Vektor-Qualitaet verwaessern (zu viele unterschiedliche Themen in einem
Vektor).

Kein eigener Port (ADR-0017): anders als EmbedderPort/RetrieverPort/LLMPort
gibt es hier keinen austauschbaren Provider, den ein Mock ersetzen muesste --
Chunking ist eine deterministische Funktion ohne I/O, analog den reinen
Domain-Funktionen (domain/roi.py, domain/scoring.py), die ebenfalls ohne
Port-Abstraktion direkt getestet werden. Liegt trotzdem in adapters/rag/,
weil der Master-Plan v3.1 (Phase D) den Chunker dort verortet -- als
Baustein der RAG-Pipeline, nicht als reine Geschaeftsregel.

Strategie: Absatz-basiertes, gieriges Packen bis zu einer Token-Obergrenze
(tiktoken, dieselbe Encoding wie cost_logger.py: o200k_base) statt
Zeichen-Zaehlung -- konsistent mit der einzigen anderen "Groesse", die
dieses Projekt bereits kennt (Cost-Tracking). Ein einzelner Absatz, der die
Obergrenze allein schon ueberschreitet (seltener Fall, z. B. ein langer
Gesetzestext-Auszug ohne Leerzeile), wird hart in Token-Stuecke geschnitten.

Optionales Overlap (ganze Absaetze aus dem Ende des vorherigen Chunks):
verhindert, dass ein inhaltlicher Zusammenhang exakt an einer Chunk-Grenze
zerschnitten wird und dadurch fuer die Suche unauffindbar wird. Default 0
(kein Overlap) -- Kalibrierung folgt mit echten KB-Inhalten (ADR-0017).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken

from aect.application.cost_logger import count_tokens

# Gleiche Encoding wie application/cost_logger.py (bewusste Duplikation
# statt Import eines privaten Namens aus einem anderen Modul, ADR-0017).
_ENCODING_NAME = "o200k_base"

_DEFAULT_MAX_TOKENS = 200
_DEFAULT_OVERLAP_TOKENS = 0


@dataclass(frozen=True)
class Chunk:
    """Ein einzelnes Chunking-Ergebnis -- bereit fuer Embedding/Indexierung.

    Anders als RetrievedChunk (ports/retriever.py, das Ergebnis EINER Suche
    mit Relevanz-Score) ist Chunk das Ergebnis DER Aufteilung eines
    Quelldokuments VOR jeder Suche -- kein score-Feld, dafuer chunk_index
    fuer eine stabile Position innerhalb der Quelle.

    source_id: identisch im Zweck zu RetrievedChunk.source_id -- Citation-
    Anker und Loesch-Tag (aect-security-checklist v2.1, Phase D: "Records
    taggen (source_id) fuer gezielte Loeschung"). Wird vom Aufrufer vergeben
    (z. B. Dateiname der Wissensbasis-Quelle), nicht hier erzeugt.

    chunk_index: 0-basierte Position innerhalb der Quelle, in Packreihenfolge.
    Macht chunk_id stabil und reproduzierbar bei erneutem Chunking derselben
    Quelle mit denselben Parametern.

    frozen=True: Wertobjekt, analog RetrievedChunk und LLMResponse.
    """

    text: str
    source_id: str
    chunk_index: int

    @property
    def chunk_id(self) -> str:
        """Stabiler, eindeutiger Identifier fuer ChromaDB-Upserts (Folge-Tag)."""
        return f"{self.source_id}:{self.chunk_index}"


def chunk_document(
    text: str,
    source_id: str,
    *,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    overlap_tokens: int = _DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Teilt `text` in eine Liste von Chunks fuer Embedding/Indexierung.

    Absatz-basiertes, gieriges Packen: Absaetze werden der Reihe nach in
    einen Chunk gepackt, bis der naechste Absatz `max_tokens` ueberschreiten
    wuerde -- dann wird der aktuelle Chunk abgeschlossen und ein neuer
    begonnen. Ein einzelner Absatz, der `max_tokens` allein schon
    ueberschreitet, wird hart in Token-Stuecke geschnitten.

    overlap_tokens > 0: ganze Absaetze vom Ende des soeben abgeschlossenen
    Chunks werden, soweit sie ins Overlap-Budget passen, an den Anfang des
    naechsten Chunks kopiert (Kontext-Kontinuitaet ueber Chunk-Grenzen).

    Leere oder nur aus Leerraum bestehende Eingabe -> leere Liste, kein
    Fehler (Graceful Degradation, analog EmbedderPort/RetrieverPort).

    Raises:
        ValueError: wenn overlap_tokens >= max_tokens (fuehrte zu einem
            Chunk, der ausschliesslich aus uebernommenem Overlap-Inhalt
            bestehen koennte, ohne neuen Inhalt).
    """
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens muss kleiner als max_tokens sein")

    paragraphs = _split_into_paragraphs(text)
    if not paragraphs:
        return []

    encoding = tiktoken.get_encoding(_ENCODING_NAME)
    pieces: list[str] = []
    for paragraph in paragraphs:
        if count_tokens(paragraph, _ENCODING_NAME) > max_tokens:
            pieces.extend(_split_oversized_text(paragraph, max_tokens, encoding))
        else:
            pieces.append(paragraph)

    return _pack_pieces(pieces, source_id, max_tokens, overlap_tokens)


def _split_into_paragraphs(text: str) -> list[str]:
    """Trennt `text` an Leerzeilen, verwirft leere Stuecke."""
    raw_paragraphs = re.split(r"\n\s*\n", text.strip())
    return [paragraph.strip() for paragraph in raw_paragraphs if paragraph.strip()]


def _split_oversized_text(
    text: str, max_tokens: int, encoding: tiktoken.Encoding
) -> list[str]:
    """Schneidet einen einzelnen, zu langen Absatz hart in Token-Stuecke.

    Seltener Fallback -- der Normalfall ist absatzweises Packen. Verliert
    keinen Inhalt, ignoriert in diesem Fall nur die Absatzgrenze.
    """
    token_ids = encoding.encode(text)
    return [
        encoding.decode(token_ids[start : start + max_tokens])
        for start in range(0, len(token_ids), max_tokens)
    ]


def _pack_pieces(
    pieces: list[str], source_id: str, max_tokens: int, overlap_tokens: int
) -> list[Chunk]:
    """Packt vorab groessenkonforme Stuecke gierig in Chunks."""
    chunks: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0

    for piece in pieces:
        piece_tokens = count_tokens(piece, _ENCODING_NAME)
        if current and current_tokens + piece_tokens > max_tokens:
            chunks.append(_finalize_chunk(current, source_id, len(chunks)))
            current, current_tokens = _start_overlap(current, overlap_tokens)
        current.append(piece)
        current_tokens += piece_tokens

    if current:
        chunks.append(_finalize_chunk(current, source_id, len(chunks)))

    return chunks


def _start_overlap(
    previous_pieces: list[str], overlap_tokens: int
) -> tuple[list[str], int]:
    """Uebernimmt Absaetze vom Ende des vorherigen Chunks ins Overlap-Budget."""
    if overlap_tokens <= 0:
        return [], 0

    carried: list[str] = []
    carried_tokens = 0
    for piece in reversed(previous_pieces):
        piece_tokens = count_tokens(piece, _ENCODING_NAME)
        if carried_tokens + piece_tokens > overlap_tokens:
            break
        carried.insert(0, piece)
        carried_tokens += piece_tokens

    return carried, carried_tokens


def _finalize_chunk(pieces: list[str], source_id: str, chunk_index: int) -> Chunk:
    """Fuegt gesammelte Stuecke zu einem fertigen Chunk zusammen."""
    return Chunk(text="\n\n".join(pieces), source_id=source_id, chunk_index=chunk_index)
