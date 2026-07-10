"""AECT API-Konfiguration aus Umgebungsvariablen.

Alle Werte per Env-Variable oder .env-Datei.
.env ist in .gitignore -- nie committen.

Security (aect-security-checklist v2.1, Phase B):
  AECT_API_KEY: Pflicht fuer alle geschuetzten Endpoints.
  Leerer String == ungeschuetzt -- nur in isolierten Tests akzeptabel.
"""

from __future__ import annotations

import structlog
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from aect.adapters.api.keyvault_settings import AzureKeyVaultSettingsSource

# EU-Data-Zone-Allowlist (AUDIT-008). Azure-OpenAI-Endpoints liegen meist als
# https://<resource>.openai.azure.com vor -- die Region steckt nur drin, wenn
# der Ressourcenname sie enthaelt (Konvention, keine Garantie -- vgl. ADR-0010
# "nicht aus URL ableitbar"). Der Check ist daher ein Best-Effort-Guard gegen
# offensichtlich falsche Regionen, kein Ersatz fuer die Deployment-Zeit-Pflicht.
_EU_DATA_ZONE_REGIONS = ("swedencentral", "westeurope")


def check_azure_eu_region(endpoint: str, explicit_region: str = "") -> str:
    """Prueft die EU-Datenresidenz des Azure-OpenAI-Endpoints (AUDIT-008).

    Validiert nur echte Endpoints: leere, "mock"- oder localhost-Werte gelten
    als Test-/Mock-Konfiguration und werden uebersprungen.

    explicit_region (AECT_AZURE_OPENAI_REGION) umgeht, wenn gesetzt, die
    Hostname-Heuristik vollstaendig -- Azure-Custom-Subdomain-Endpoints
    (https://<resource>.openai.azure.com, das Standardformat aus Azure AI
    Foundry) enthalten die Region nie im Hostnamen. Ohne explicit_region
    bleibt der bisherige Hostname-Best-Effort als Fallback aktiv (mit
    Warn-Log bei einem Treffer, da die Erkennung dann nur geraten ist).

    Returns:
        "skipped_mock" wenn nicht validiert (Mock/Test), sonst "ok".

    Raises:
        ValueError: konfigurierte oder aus dem Hostnamen erkannte Region ist
        nicht in der EU-Data-Zone.
    """
    if (
        not endpoint
        or "mock" in endpoint.lower()
        or endpoint.startswith("http://localhost")
    ):
        return "skipped_mock"

    if explicit_region:
        if explicit_region.lower() not in _EU_DATA_ZONE_REGIONS:
            raise ValueError(
                f"Configured AECT_AZURE_OPENAI_REGION '{explicit_region}' is "
                "not an EU Data Zone (swedencentral or westeurope). See "
                "AUDIT-008 in docs/reviews."
            )
        return "ok"

    lowered = endpoint.lower()
    if not any(region in lowered for region in _EU_DATA_ZONE_REGIONS):
        raise ValueError(
            "Azure OpenAI endpoint must be in EU Data Zone (swedencentral or "
            f"westeurope). Configured: {endpoint}. See AUDIT-008 in docs/reviews."
        )
    # Kein Modul-globaler Logger (cache_logger_on_first_use=True bindet sonst
    # permanent an die Processor-Kette des ersten Aufrufs, vgl. dependencies.py).
    structlog.get_logger().warning(
        "azure_eu_region_guessed_from_hostname",
        endpoint=endpoint,
        hint="AECT_AZURE_OPENAI_REGION nicht gesetzt, Region nur aus "
        "Hostname geraten -- siehe AUDIT-008",
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
    # Explizite Region-Angabe (AUDIT-008-Fix): umgeht die Hostname-Heuristik
    # in check_azure_eu_region, wenn gesetzt -- Custom-Subdomain-Endpoints
    # (https://<resource>.openai.azure.com) enthalten die Region nicht
    # zuverlaessig im Hostnamen. Leer = bisherige Hostname-Heuristik als
    # Fallback (unveraendert).
    azure_openai_region: str = ""  # AECT_AZURE_OPENAI_REGION

    # ChromaDB (Phase D, ADR-0018/0019/0025). Default 127.0.0.1 (V4-P2): ein
    # lokal laufender, geseedeter Container wird automatisch genutzt -- kein
    # manuelles Setzen von AECT_CHROMA_HOST noetig. KEIN stiller MockRetriever-
    # Fallback mehr (CLAUDE.md fail loud): ist der Host nicht erreichbar, wirft
    # resolve_retriever() eine klare Exception statt still auf das synthetische
    # Mock-Korpus zu fallen; MockRetriever gibt es nur noch ueber einen
    # expliziten Test-Override. Docker-Container separat starten
    # (docker compose up -d).
    chroma_host: str = "127.0.0.1"  # AECT_CHROMA_HOST
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

    # Azure Key Vault (Phase G Security-Haertung, ADR-0041) -- leer (Default)
    # = Secrets kommen wie bisher aus Env-Vars/.env, kein Verhaltenswechsel.
    # Gesetzt -> AzureKeyVaultSettingsSource zieht api_key/api_key_next/
    # azure_openai_api_key aus dem Vault (settings_customise_sources unten),
    # mit Env/.env als Fallback fuer im Vault fehlende Einzel-Secrets.
    azure_key_vault_url: str = ""  # AECT_AZURE_KEY_VAULT_URL

    # Retention-Enforcement (Phase G Privacy-Haertung, DSGVO Art. 5(1)(e)
    # Speicherbegrenzung) -- scripts/enforce_retention.py loescht Cases
    # aelter als retention_days ueber den bestehenden Art.-17-Loeschpfad
    # (ADR-0038, TriageService.delete_case()). Default-Begruendung
    # (Commit-Message fuehrt sie aus): 90 Tage -- genug Zeit, einen Case im
    # Portfolio-/Interview-Kontext erneut aufzurufen oder zu zeigen, aber
    # eine bewusste, endliche Grenze statt unbegrenzter Aufbewahrung.
    retention_days: int = 90  # AECT_RETENTION_DAYS

    model_config = SettingsConfigDict(
        env_prefix="AECT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Fuegt AzureKeyVaultSettingsSource zwischen init_settings und
        env_settings ein.

        Prioritaet (erste Quelle gewinnt): init_settings (Konstruktor-
        Kwargs, z. B. Settings(api_key=...) in Tests) > Key Vault > Env >
        .env > File-Secrets. Konstruktor-Kwargs bleiben damit fuer JEDEN
        bestehenden Test unveraendert die staerkste Quelle -- die neue
        Key-Vault-Quelle kann kein Testverhalten aus Phase 1-3 beeinflussen.
        Key Vault gewinnt gegen Env, wenn AECT_AZURE_KEY_VAULT_URL gesetzt
        ist -- sonst liefert die Quelle ein leeres dict (No-op).
        """
        return (
            init_settings,
            AzureKeyVaultSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
