"""Cost-Logger -- Token-Zaehlung und Kostenschaetzung fuer LLM-Calls (tiktoken).

Provider-agnostisch: LLMResponse hat kein usage-Feld, und MockLLMAdapter
wuerde keins liefern. Statt auf provider-spezifische Token-Counts zu warten,
zaehlt dieses Modul Input- und Output-Tokens selbst -- funktioniert identisch
fuer Mock und den spaeteren Azure-Adapter.

Pricing-Konstanten: Stand 16.06.2026, gpt-4.1-mini (Azure: $0.40 Input /
$1.60 Output pro 1M Tokens). Aktualisiert von gpt-4o-mini-Default (Tag 45 --
gpt-4o-mini war bei Azure fuer Neukunden zum Setup-Zeitpunkt nicht mehr
deploybar, siehe phase-c-review.md). Bei jedem weiteren Modellwechsel hier
erneut pruefen.

IP-Trennung (interne Referenz (entfernt) Paragraph 5): Pricing und Encoding-Name sind
Provider-Daten, keine firmenspezifischen Werte -- bleiben im generischen Code,
keine Config-Datei noetig.
"""

from __future__ import annotations

import structlog
import tiktoken

from aect.application.ports.llm import LLMMessage, LLMResponse

# gpt-4o, gpt-4o-mini und die gpt-4.1-Familie (inkl. gpt-4.1-mini) nutzen die
# o200k_base-Encoding (cl100k_base war GPT-4/3.5). Falscher Name wuerde
# get_encoding() klar mit Exception fehlschlagen lassen -- kein stiller Fehler.
_ENCODING_NAME = "o200k_base"

# USD pro 1 Million Tokens, gpt-4.1-mini, Stand 16.06.2026.
_PRICE_INPUT_USD_PER_1M = 0.40
_PRICE_OUTPUT_USD_PER_1M = 1.60

# Naeherungs-Wechselkurs USD->EUR, konservativ. Fuer eine grobe
# Budget-Schaetzung ausreichend, kein Buchhaltungswert.
_USD_TO_EUR = 0.95


def count_tokens(text: str, encoding_name: str = _ENCODING_NAME) -> int:
    """Zaehlt Tokens in `text` mit der gegebenen tiktoken-Encoding.

    Fallback (F-031, 02.07.2026): tiktoken laedt die BPE-Datei beim ersten
    Aufruf pro Prozess per HTTP von openaipublic.blob.core.windows.net und
    cached sie danach lokal. In Umgebungen mit restriktiver Egress-Policy
    (z. B. Azure Container Apps hinter NSG/Firewall ohne diese Domain in der
    Allowlist) schlaegt das fehl -- und zwar NACH einem bereits erfolgreich
    bezahlten Azure-OpenAI-Call, den log_llm_cost() sonst mit hochreisst.
    Deshalb: bei Fehlschlag grobe Naeherung (~4 Zeichen/Token, gaengiger
    Schaetzwert fuer GPT-Tokenizer) statt Exception; einmalig geloggt.
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as exc:
        structlog.get_logger().warning(
            "tiktoken_encoding_unavailable_using_approximation",
            encoding_name=encoding_name,
            error=str(exc),
        )
        return len(text) // 4 if text else 0


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
