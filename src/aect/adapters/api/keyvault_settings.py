"""AzureKeyVaultSettingsSource -- zieht Secrets aus Azure Key Vault statt aus
Env-Vars (Phase G Security-Haertung).

Design-only, analog ADR-0035 (Azure Container Apps: Design, kein Deploy):
gebaut und getestet OHNE echte Azure-Infrastruktur. AECT_AZURE_KEY_VAULT_URL
NICHT gesetzt (Default, lokale Entwicklung, gesamte bestehende Test-Suite)
-> die Quelle liefert ein leeres dict, No-op -- Env-/.env-Verhalten bleibt
exakt wie vorher, kein Breaking Change.

Nur echte Secrets werden aus dem Vault gezogen (_KEY_VAULT_SECRET_FIELDS);
Infrastruktur-Adressen (chroma_host, kb_dir, ...) bleiben Env-Config, kein
Secret-Material -- IP-/Verantwortungs-Trennung analog ADR-0018/ADR-0010.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Protocol

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

_VAULT_URL_ENV_VAR = "AECT_AZURE_KEY_VAULT_URL"

_KEY_VAULT_SECRET_FIELDS: tuple[str, ...] = (
    "api_key",
    "api_key_next",
    "azure_openai_api_key",
)


class SecretClientProtocol(Protocol):
    """Minimaler struktureller Typ, den diese Quelle vom Key-Vault-Client
    braucht -- erfuellt von azure.keyvault.secrets.SecretClient UND von
    einem Test-Fake (analog ChromaCollection in adapters/rag/retriever.py)."""

    def get_secret(self, name: str) -> Any: ...


def _build_default_secret_client(vault_url: str) -> SecretClientProtocol:
    """Baut den echten Azure-SecretClient.

    Lokaler Import (kein Modulkopf-Import): haelt src/ frei von
    azure-identity/azure-keyvault-secrets im Mock-/Lokal-Pfad -- analog
    chromadb/sentence_transformers in dependencies.py (Konvention: schwere
    oder Cloud-gebundene Dependencies werden nur importiert, wenn der Pfad
    tatsaechlich genutzt wird).
    """
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    return SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())


class AzureKeyVaultSettingsSource(PydanticBaseSettingsSource):
    """pydantic-settings-Quelle: liest ausgewaehlte Secret-Felder aus Azure
    Key Vault, wenn AECT_AZURE_KEY_VAULT_URL gesetzt ist.

    Secret-Name im Vault = Feldname mit '-' statt '_' (Azure-Key-Vault-
    Namenskonvention erlaubt keine Unterstriche), z. B. Feld `api_key` ->
    Secret-Name `api-key`.

    Ein im Vault fehlendes einzelnes Secret wird uebersprungen (kein Eintrag
    im zurueckgegebenen dict) -- die nachfolgende Quelle (Env/.env) liefert
    dann den Wert fuer genau dieses Feld, kein harter Fehler fuer das
    gesamte Settings-Objekt wegen eines einzelnen fehlenden Secrets.

    secret_client_factory: austauschbar fuer Tests (Default baut den echten
    Azure-SecretClient via DefaultAzureCredential) -- macht die Quelle ohne
    Live-Azure-Verbindung testbar.
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        secret_client_factory: Callable[[str], SecretClientProtocol] | None = None,
    ) -> None:
        super().__init__(settings_cls)
        self._secret_client_factory = (
            secret_client_factory or _build_default_secret_client
        )

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        """Einzelfeld-Lookup -- Teil des abstrakten Vertrags von
        PydanticBaseSettingsSource. __call__() unten ruft dies NICHT auf
        (baut den Client einmal pro Aufruf statt einmal pro Feld), bleibt
        aber eigenstaendig korrekt fuer den Fall, dass pydantic-settings-
        Interna diese Methode direkt aufrufen."""
        vault_url = os.environ.get(_VAULT_URL_ENV_VAR, "")
        if not vault_url or field_name not in _KEY_VAULT_SECRET_FIELDS:
            return None, field_name, False
        client = self._secret_client_factory(vault_url)
        return self._fetch_secret(client, field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        vault_url = os.environ.get(_VAULT_URL_ENV_VAR, "")
        if not vault_url:
            return {}
        client = self._secret_client_factory(vault_url)
        data: dict[str, Any] = {}
        for field_name in _KEY_VAULT_SECRET_FIELDS:
            value = self._fetch_secret(client, field_name)
            if value is not None:
                data[field_name] = value
        return data

    @staticmethod
    def _fetch_secret(client: SecretClientProtocol, field_name: str) -> str | None:
        secret_name = field_name.replace("_", "-")
        try:
            secret = client.get_secret(secret_name)
        except Exception:
            # Secret fehlt im Vault, Vault nicht erreichbar, Berechtigung
            # fehlt, o.ae. -- kein harter Fehler, naechste Quelle (Env/.env)
            # liefert den Wert fuer dieses Feld.
            return None
        return secret.value if secret is not None else None
