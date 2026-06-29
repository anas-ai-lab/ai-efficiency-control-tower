#!/usr/bin/env python3
"""Exportiert das FastAPI-OpenAPI-Schema als JSON fuer die Frontend-Typgenerierung.

Quelle der Wahrheit fuer die Frontend-Typen ist das Backend-Schema. Dieses
Script schreibt das aktuelle Schema nach stdout; `openapi.json` im Repo-Root
wird daraus erzeugt (siehe scripts/-Aufruf unten) und in CI gegen den
generierten Stand gediffed (Drift-Detection, G-S4).

Aufruf:
    uv run python scripts/export_openapi.py > openapi.json
"""

from __future__ import annotations

import json

from aect.adapters.api.app import app


def main() -> None:
    schema = app.openapi()
    print(json.dumps(schema, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
