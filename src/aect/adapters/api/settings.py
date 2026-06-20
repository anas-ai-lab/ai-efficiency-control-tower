"""AECT API-Konfiguration aus Umgebungsvariablen.

Alle Werte per Env-Variable oder .env-Datei.
.env ist in .gitignore -- nie committen.

Security (aect-security-checklist v2.1, Phase B):
  AECT_API_KEY: Pflicht fuer alle geschuetzten Endpoints.
  Leerer String == ungeschuetzt -- nur in isolierten Tests akzeptabel.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurationswerte aus Umgebungsvariablen.

    Env-Prefix AECT_: z. B. AECT_API_KEY=geheimnis.
    .env-Datei wird automatisch geladen wenn vorhanden.
    """

    api_key: str = ""
    db_path: str = ""  # Leer = InMemoryRepository. AECT_DB_PATH=/pfad/aect.db = SQLite.

    # Azure OpenAI (Phase C, ADR-0010) -- leer = MockLLMAdapter.
    # EU-Data-Zone-Pflicht (ADR-0003): Deployment muss in swedencentral
    # oder westeurope liegen -- nicht aus Endpoint-URL pruefbar,
    # gilt als Deployment-Zeit-Pflicht, kein Code-Gate.
    azure_openai_endpoint: str = ""  # AECT_AZURE_OPENAI_ENDPOINT
    azure_openai_api_key: str = ""  # AECT_AZURE_OPENAI_API_KEY
    azure_openai_deployment: str = ""  # AECT_AZURE_OPENAI_DEPLOYMENT
    azure_openai_api_version: str = "2024-10-21"  # AECT_AZURE_OPENAI_API_VERSION

    # ChromaDB (Phase D, ADR-0018/0019/0025) -- leer = MockRetriever.
    # Docker-Container muss separat laufen (docker compose up -d).
    chroma_host: str = ""  # AECT_CHROMA_HOST, z. B. 127.0.0.1
    chroma_port: int = 8001  # AECT_CHROMA_PORT

    # Wissensbasis-Verzeichnis (Phase D, ADR-0027) -- Quelle fuer den
    # BM25-Index im Hybrid-Pfad, relativ zum Arbeitsverzeichnis (uv run
    # laeuft immer aus dem Projektordner, Fallen-Katalog SS6 Punkt 11).
    kb_dir: str = "knowledge_base"  # AECT_KB_DIR

    model_config = SettingsConfigDict(
        env_prefix="AECT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
