"""KB-Indexing-Vorbereitung -- kuratierte Markdown-Quellen zu Records (Phase D).

Bindeglied zwischen knowledge_base/ und dem (Folge-Tag) Chroma-Upsert:
liest *.md, trennt Front-Matter vom Body, chunkt den Body ueber den
vorhandenen chunk_document() (ADR-0017) und baut upsert-fertige IndexRecords
mit Quellen-Metadaten (Citation-Konvention, ADR-0021).

Bewusst rein und offline: nur Datei-I/O + Chunking, kein Embedding, kein
Chroma, kein torch. Der echte Upsert in eine laufende Collection ist ein
eigener Folge-Tag (Docker, MiniLM-Modell, collection.add).

PII-Redaction (LLM08) ist hier kein Thema: kuratierter oeffentlicher
Rechtstext enthaelt keine personenbezogenen Daten (ADR-0021). Der Redactor
gehoert auf den User-Case-/Query-Pfad, Folge-Tag.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aect.adapters.rag.chunker import chunk_document

_REQUIRED_KEYS = ("source_id", "title", "citation")


@dataclass(frozen=True)
class IndexRecord:
    """Ein upsert-fertiger Datensatz fuer ChromaDB (Index-Pfad, Folge-Tag).

    id: stabiler Chunk-Identifier (= Chunk.chunk_id, "<source_id>:<index>",
        ADR-0017). Dient als Chroma-Dokument-ID und Loesch-Tag.
    document: der einzubettende Chunk-Text.
    metadata: Provenance/Citation, ausschliesslich str-Werte (Chroma erlaubt
        nur str/int/float/bool; wir bleiben einheitlich bei str, ADR-0021).
        Enthaelt mindestens source_id, title, citation und chunk_index.

    frozen=True: Wertobjekt, analog Chunk und RetrievedChunk.
    """

    id: str
    document: str
    metadata: dict[str, str]


def parse_kb_document(text: str) -> tuple[dict[str, str], str]:
    """Trennt den Front-Matter-Block (--- ... ---) vom Markdown-Body.

    Front-Matter: einfache `key: value`-Zeilen zwischen zwei `---`-Zeilen,
    keine Listen/Verschachtelung. Der Wert wird am ersten ":" getrennt, damit
    URLs (https://...) intakt bleiben. Pflichtschluessel: source_id, title,
    citation (ADR-0021).

    Raises:
        ValueError: wenn der Front-Matter fehlt, nicht geschlossen ist, eine
            Zeile keinen ":" enthaelt oder ein Pflichtschluessel fehlt
            (fail loud, analog zur overlap-Pruefung im Chunker).
    """
    lines = text.splitlines()

    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines) or lines[idx].strip() != "---":
        raise ValueError("Front-Matter fehlt: erste Zeile muss '---' sein")

    start = idx + 1
    end: int | None = None
    for i in range(start, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("Front-Matter nicht geschlossen: zweites '---' fehlt")

    metadata: dict[str, str] = {}
    for raw in lines[start:end]:
        line = raw.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Ungueltige Front-Matter-Zeile: {line!r}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    missing = [key for key in _REQUIRED_KEYS if key not in metadata]
    if missing:
        raise ValueError(f"Pflichtschluessel fehlen: {missing}")

    body = "\n".join(lines[end + 1 :]).strip()
    return metadata, body


def build_index_records(kb_dir: Path) -> list[IndexRecord]:
    """Liest alle *.md aus kb_dir (sortiert), chunkt sie, baut IndexRecords.

    Pro Datei: Front-Matter parsen, Body ueber chunk_document() zerteilen, je
    Chunk einen IndexRecord erzeugen. metadata = Front-Matter + chunk_index
    (als str). Nicht-*.md-Dateien werden ignoriert; README.md ist Doku des
    Verzeichnisses, keine Quelle, und wird ebenfalls uebersprungen. Ein
    leerer Body liefert keine Records (chunk_document gibt [] zurueck).
    """
    records: list[IndexRecord] = []
    for path in sorted(kb_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        metadata, body = parse_kb_document(path.read_text(encoding="utf-8"))
        for chunk in chunk_document(body, source_id=metadata["source_id"]):
            record_metadata = {**metadata, "chunk_index": str(chunk.chunk_index)}
            records.append(
                IndexRecord(
                    id=chunk.chunk_id,
                    document=chunk.text,
                    metadata=record_metadata,
                )
            )
    return records
