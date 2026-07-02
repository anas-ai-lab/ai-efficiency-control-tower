"""AECT API-Konfiguration aus Umgebungsvariablen.

Alle Werte per Env-Variable oder .env-Datei.
.env ist in .gitignore -- nie committen.

Security (aect-security-checklist v2.1, Phase B):
  AECT_API_KEY: Pflicht fuer alle geschuetzten Endpoints.
  Leerer String == ungeschuetzt -- nur in isolierten Tests akzeptabel.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

# EU-Data-Zone-Allowlist (AUDIT-008). Azure-OpenAI-Endpoints liegen meist als
# https://<resource>.openai.azure.com vor -- die Region steckt nur drin, wenn
# der Ressourcenname sie enthaelt (Konvention, keine Garantie -- vgl. ADR-0010
# "nicht aus URL ableitbar"). Der Check ist daher ein Best-Effort-Guard gegen
# offensichtlich falsche Regionen, kein Ersatz fuer die Deployment-Zeit-Pflicht.
_EU_DATA_ZONE_REGIONS = ("swedencentral", "westeurope")


def check_azure_eu_region(endpoint: str) -> str:
    """Prueft die EU-Datenresidenz des Azure-OpenAI-Endpoints (AUDIT-008).

    Validiert nur echte Endpoints: leere, "mock"- oder localhost-Werte gelten
    als Test-/Mock-Konfiguration und werden uebersprungen.

    Returns:
        "skipped_mock" wenn nicht validiert (Mock/Test), sonst "ok".

    Raises:
        ValueError: Endpoint gesetzt, kein Mock, aber nicht in der EU-Data-Zone.
    """
    if (
        not endpoint
        or "mock" in endpoint.lower()
        or endpoint.startswith("http://localhost")
    ):
        return "skipped_mock"
    lowered = endpoint.lower()
    if not any(region in lowered for region in _EU_DATA_ZONE_REGIONS):
        raise ValueError(
            "Azure OpenAI endpoint must be in EU Data Zone (swedencentral or "
            f"westeurope). Configured: {endpoint}. See AUDIT-008 in docs/reviews."
        )
    return "ok"


class Settings(BaseSettings):
    """Konfigurationswerte aus Umgebungsvariablen.

    Env-Prefix AECT_: z. B. AECT_API_KEY=geheimnis.
    .env-Datei wird automatisch geladen wenn vorhanden.
    """

    api_key: str = ""
    # Rotation ohne Downtime (Phase G Security-Haertung): waehrend einer
    # Rotation sind BEIDE Keys gueltig -- der primaere (api_key) und der
    # naechste (api_key_next). Leer = keine Rotation aktiv, nur api_key gilt.
    # Ablauf siehe README.md ("API-Key-Rotation").
    api_key_next: str = ""  # AECT_API_KEY_NEXT
    db_path: str = ""  # Leer = InMemoryRepository. AECT_DB_PATH=/pfad/aect.db = SQLite.

    # Azure OpenAI (Phase C, ADR-0010) -- leer = MockLLMAdapter.
    # EU-Data-Zone-Pflicht (ADR-0003): Deployment muss in swedencentral oder
    # westeurope liegen -- primaer Deployment-Zeit-Pflicht. AUDIT-008 ergaenzt
    # einen Best-Effort-URL-Guard (check_azure_eu_region oben): faengt
    # offensichtlich falsche Regionen ab, ersetzt aber nicht die Deployment-
    # Pflicht (Region steckt nicht garantiert im Ressourcennamen).
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

    # Token-Budget-Limiter (Phase G Security-Haertung) -- ergaenzt die
    # Request-Rate-Limits (10/min LLM-Endpoints) um eine Token-MENGEN-Grenze
    # pro API-Key und Stunde. Default-Begruendung (Commit-Message fuehrt sie
    # aus): 50.000 Tokens/h deckt grosszuegige legitime Nutzung (ca. 15-25
    # LLM-Calls/h bei realistischer Freitextlaenge) ab, begrenzt aber ein
    # Missbrauchsmuster (viele max_length-lange Faelle kurz hintereinander
    # geschaerft/vorgeschlagen/geprueft) deutlich staerker als die
    # Request-Rate allein.
    token_budget_per_hour: int = 50_000  # AECT_TOKEN_BUDGET_PER_HOUR

    model_config = SettingsConfigDict(
        env_prefix="AECT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
