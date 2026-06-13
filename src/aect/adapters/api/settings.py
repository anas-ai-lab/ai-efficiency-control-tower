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

    model_config = SettingsConfigDict(
        env_prefix="AECT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
