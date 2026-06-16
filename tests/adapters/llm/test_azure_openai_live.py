"""Budget-Sentinel: ein echter Azure OpenAI Call mit Cost-Logging.

session-protocol v3 SS4 / aect-security-checklist v2.1 Phase C:
Voraussetzung fuer das Master-Plan-Phase-C-Gate (mindestens 1 echter
Azure-Call mit Cost-Logger-Eintrag < 0,01 EUR). Skippt automatisch, wenn
AECT_AZURE_OPENAI_ENDPOINT / API_KEY / DEPLOYMENT nicht gesetzt sind
(Mock-Only-Umgebung).

Bewusst die rohe AzureOpenAIAdapter-Instanz, nicht ResilientLLMAdapter:
Retry/Backoff sind in test_resilient.py mit Mocks abgedeckt. Hier geht es
nur um den echten Call + Kosten -- ein Retry wuerde Tokens unnoetig
vervielfachen.

EU-Data-Zone-Pflicht (ADR-0003): Deployment muss in swedencentral oder
westeurope liegen -- Deployment-Zeit-Pflicht, kein Code-Gate.

IP-Trennung (interne Referenz (entfernt) SS5): Endpoint/Deployment/Key kommen ausschliesslich
aus .env (nicht committed) ueber Settings -- keine Werte in diesem File.
"""

from __future__ import annotations

import pytest
from openai import AsyncAzureOpenAI

from aect.adapters.api.settings import Settings
from aect.adapters.llm.azure_openai import AzureOpenAIAdapter
from aect.application.cost_logger import count_tokens, estimate_cost_eur, log_llm_cost
from aect.application.ports.llm import LLMMessage

_settings = Settings()

pytestmark = pytest.mark.skipif(
    not (
        _settings.azure_openai_endpoint
        and _settings.azure_openai_api_key
        and _settings.azure_openai_deployment
    ),
    reason="AECT_AZURE_OPENAI_* nicht vollstaendig gesetzt (Mock-Only)",
)


@pytest.mark.integration
async def test_real_azure_call_costs_under_one_cent() -> None:
    """Echter Call gegen das konfigurierte Azure-Deployment.

    Budget-Sentinel: geschaetzte Kosten muessen < 0,01 EUR liegen.
    max_tokens=20 haelt den Output-Anteil klein.
    """
    client = AsyncAzureOpenAI(
        api_key=_settings.azure_openai_api_key,
        api_version=_settings.azure_openai_api_version,
        azure_endpoint=_settings.azure_openai_endpoint,
    )
    adapter = AzureOpenAIAdapter(
        client=client,
        deployment=_settings.azure_openai_deployment,
        max_tokens=20,
    )
    messages = [LLMMessage(role="user", content="Antworte nur mit dem Wort: OK")]

    response = await adapter.complete(messages)

    assert response.content.strip() != ""

    input_tokens = sum(count_tokens(m.content) for m in messages)
    output_tokens = count_tokens(response.content)
    cost_eur = estimate_cost_eur(input_tokens, output_tokens)

    log_llm_cost(
        case_id="budget-sentinel-tag44",
        messages=messages,
        response=response,
        operation="budget_sentinel_check",
    )

    print(
        f"Budget-Sentinel: input={input_tokens} output={output_tokens} "
        f"tokens, cost_eur_estimate={cost_eur:.6f}"
    )

    assert cost_eur < 0.01
