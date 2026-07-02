"""Tests fuer AzureKeyVaultSettingsSource (Phase G, Design+testbar ohne Live-Azure).

Kein Netzwerk, kein echtes Azure -- SecretClient wird per Fake ersetzt
(analog dem strukturellen Test-Fake-Muster in adapters/rag/retriever.py:
ChromaCollection). Deckt zwei Ebenen ab:
  1. AzureKeyVaultSettingsSource direkt (isoliert, schnell).
  2. Settings() end-to-end mit gepatchter Client-Factory (beweist, dass
     settings_customise_sources korrekt verdrahtet ist).
"""

from __future__ import annotations

from typing import Any

import pytest

from aect.adapters.api.keyvault_settings import AzureKeyVaultSettingsSource
from aect.adapters.api.settings import Settings


class _FakeSecret:
    def __init__(self, value: str) -> None:
        self.value = value


class _FakeSecretClient:
    """Test-Fake fuer SecretClientProtocol -- kein Netzwerk, kein Azure."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = secrets

    def get_secret(self, name: str) -> _FakeSecret:
        if name not in self._secrets:
            raise KeyError(name)  # simuliert ResourceNotFoundError
        return _FakeSecret(self._secrets[name])


def _fake_factory(secrets: dict[str, str]) -> Any:
    def factory(vault_url: str) -> _FakeSecretClient:
        return _FakeSecretClient(secrets)

    return factory


# ---------------------------------------------------------------------------
# AzureKeyVaultSettingsSource direkt
# ---------------------------------------------------------------------------


def test_call_returns_empty_dict_without_vault_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AECT_AZURE_KEY_VAULT_URL", raising=False)
    source = AzureKeyVaultSettingsSource(
        Settings, secret_client_factory=_fake_factory({"api-key": "vault-secret"})
    )
    assert source() == {}


def test_call_pulls_configured_fields_from_vault(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    source = AzureKeyVaultSettingsSource(
        Settings,
        secret_client_factory=_fake_factory(
            {
                "api-key": "vault-api-key",
                "azure-openai-api-key": "vault-azure-key",
            }
        ),
    )
    result = source()
    assert result["api_key"] == "vault-api-key"
    assert result["azure_openai_api_key"] == "vault-azure-key"
    assert "api_key_next" not in result  # nicht im Fake-Vault vorhanden


def test_call_skips_missing_secret_without_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    source = AzureKeyVaultSettingsSource(
        Settings, secret_client_factory=_fake_factory({})
    )
    assert source() == {}


def test_get_field_value_ignores_non_secret_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """chroma_host ist kein Secret-Feld -- wird nie aus dem Vault gelesen,
    selbst wenn zufaellig ein gleichnamiges Secret existiert."""
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    source = AzureKeyVaultSettingsSource(
        Settings,
        secret_client_factory=_fake_factory({"chroma-host": "should-not-leak"}),
    )
    field = Settings.model_fields["chroma_host"]
    value, key, _ = source.get_field_value(field, "chroma_host")
    assert value is None
    assert key == "chroma_host"


def test_get_field_value_returns_secret_for_configured_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    source = AzureKeyVaultSettingsSource(
        Settings, secret_client_factory=_fake_factory({"api-key": "vault-value"})
    )
    field = Settings.model_fields["api_key"]
    value, key, _ = source.get_field_value(field, "api_key")
    assert value == "vault-value"
    assert key == "api_key"


# ---------------------------------------------------------------------------
# Settings() end-to-end: settings_customise_sources korrekt verdrahtet
# ---------------------------------------------------------------------------


def test_settings_pulls_api_key_from_vault_when_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    monkeypatch.setenv("AECT_API_KEY", "env-api-key")  # darf NICHT gewinnen
    monkeypatch.setattr(
        "aect.adapters.api.keyvault_settings._build_default_secret_client",
        lambda vault_url: _FakeSecretClient({"api-key": "vault-api-key"}),
    )
    settings = Settings()
    assert settings.api_key == "vault-api-key"


def test_settings_falls_back_to_env_without_vault_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AECT_AZURE_KEY_VAULT_URL", raising=False)
    monkeypatch.setenv("AECT_API_KEY", "env-api-key")
    settings = Settings()
    assert settings.api_key == "env-api-key"


def test_settings_constructor_kwarg_beats_vault(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """init_settings (Konstruktor-Kwargs) bleibt die staerkste Quelle -- die
    neue Key-Vault-Quelle darf kein bestehendes Testverhalten (Settings(
    api_key=...) in Phase 1-3) beeinflussen."""
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    monkeypatch.setattr(
        "aect.adapters.api.keyvault_settings._build_default_secret_client",
        lambda vault_url: _FakeSecretClient({"api-key": "vault-api-key"}),
    )
    settings = Settings(api_key="explicit-kwarg-key")
    assert settings.api_key == "explicit-kwarg-key"


def test_settings_falls_back_to_env_for_secret_missing_in_vault(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Vault gesetzt, aber das konkrete Secret fehlt dort -- Env liefert es."""
    monkeypatch.setenv("AECT_AZURE_KEY_VAULT_URL", "https://fake-vault.vault.azure.net")
    monkeypatch.setenv("AECT_API_KEY", "env-fallback-key")
    monkeypatch.setattr(
        "aect.adapters.api.keyvault_settings._build_default_secret_client",
        lambda vault_url: _FakeSecretClient({}),
    )
    settings = Settings()
    assert settings.api_key == "env-fallback-key"
