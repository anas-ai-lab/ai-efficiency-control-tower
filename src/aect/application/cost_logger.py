"""Cost-Logger -- Token-Zaehlung und Kostenschaetzung fuer LLM-Calls (tiktoken).

Provider-agnostisch: LLMResponse hat kein usage-Feld, und MockLLMAdapter
wuerde keins liefern. Statt auf provider-spezifische Token-Counts zu warten,
zaehlt dieses Modul Input- und Output-Tokens selbst -- funktioniert identisch
fuer Mock und den spaeteren Azure-Adapter.

Pricing-Konstanten: Stand Juni 2026, gpt-4o-mini (OpenAI direct / Azure Global
Standard: $0.15 Input / $0.60 Output pro 1M Tokens). Azure Data Zone (EU) kann
abweichen -- vor dem ersten echten Azure-Call (Budget-Sentinel,
session-protocol v3 Paragraph 4) re-verifizieren.

IP-Trennung (interne Referenz (entfernt) Paragraph 5): Pricing und Encoding-Name sind
Provider-Daten, keine firmenspezifischen Werte -- bleiben im generischen Code,
keine Config-Datei noetig.
"""

from __future__ import annotations

import structlog
import tiktoken

from aect.application.ports.llm import LLMMessage, LLMResponse

# gpt-4o und gpt-4o-mini nutzen die o200k_base-Encoding (cl100k_base war
# GPT-4/3.5). Falscher Name wuerde get_encoding() klar mit Exception
# fehlschlagen lassen -- kein stiller Fehler.
_ENCODING_NAME = "o200k_base"

# USD pro 1 Million Tokens, gpt-4o-mini, Stand Juni 2026.
_PRICE_INPUT_USD_PER_1M = 0.15
_PRICE_OUTPUT_USD_PER_1M = 0.60

# Naeherungs-Wechselkurs USD->EUR, konservativ. Fuer eine grobe
# Budget-Schaetzung ausreichend, kein Buchhaltungswert.
_USD_TO_EUR = 0.95


def count_tokens(text: str, encoding_name: str = _ENCODING_NAME) -> int:
    """Zaehlt Tokens in `text` mit der gegebenen tiktoken-Encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def estimate_cost_eur(input_tokens: int, output_tokens: int) -> float:
    """Schaetzt die Kosten in EUR fuer gegebene Input-/Output-Token-Counts."""
    cost_usd = (
        input_tokens / 1_000_000 * _PRICE_INPUT_USD_PER_1M
        + output_tokens / 1_000_000 * _PRICE_OUTPUT_USD_PER_1M
    )
    return cost_usd * _USD_TO_EUR


def log_llm_cost(
    *,
    case_id: str,
    messages: list[LLMMessage],
    response: LLMResponse,
    operation: str,
) -> None:
    """Loggt Token-Counts und geschaetzte Kosten fuer einen abgeschlossenen LLM-Call.

    Frischer Logger pro Aufruf (kein Modul-globaler structlog.get_logger()) --
    selbe Begruendung wie in service.py fuer injection_pattern_detected
    (Tag 32): cache_logger_on_first_use wuerde capture_logs() in Tests an die
    falsche Prozessor-Kette binden.

    Logging-Allowlist (v2.1, erweitert): case_id, operation, input_tokens,
    output_tokens, token_count, cost_eur_estimate. Kein Body, kein Prompt.
    """
    input_tokens = sum(count_tokens(m.content) for m in messages)
    output_tokens = count_tokens(response.content)

    logger = structlog.get_logger()
    logger.info(
        "llm_call_cost",
        case_id=case_id,
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        token_count=input_tokens + output_tokens,
        cost_eur_estimate=round(estimate_cost_eur(input_tokens, output_tokens), 6),
    )
