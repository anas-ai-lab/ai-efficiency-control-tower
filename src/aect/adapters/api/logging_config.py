"""structlog-Konfiguration fuer AECT.

Allowlist (aect-security-checklist v2.1, Phase B; erweitert Tag 32/33):
  Erlaubt:  timestamp, level, logger, request_id, route,
            status, latency_ms, token_count, case_id, operation,
            input_tokens, output_tokens, cost_eur_estimate, fields,
            deleted_at, result, endpoint, error, chroma_host.
  Verboten: body, prompt, PII, Secrets.

Durchsetzung (H-027): _drop_denied_keys ist ein structlog-Processor, der die
strukturell gefaehrlichen Freitext-Keys (Prompt-Body, LLM-Output) VOR dem
Rendern aus jedem Event-Dict entfernt. Damit ist die Allowlist nicht mehr nur
Call-Site-Konvention, sondern Defense-in-Depth: ein versehentliches
logger.info(..., prompt=...) schreibt den Body nicht in die Logs.

JSON-Output: maschinenlesbar, kompatibel mit Azure Monitor und ELK.
configure_logging() ist idempotent -- Mehrfachaufruf in Tests harmlos.
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any

import structlog

# Event-Keys, die strukturell Freitext (Prompt-Body, LLM-Output, PII) tragen
# koennten. Werden aus jedem Log-Event entfernt -- unabhaengig von der
# Call-Site-Disziplin. Metadaten-Keys (case_id, operation, tokens, fields mit
# nur Pattern-Namen, error mit redaktierter Message) bleiben erlaubt.
_DENIED_KEYS: frozenset[str] = frozenset(
    {
        "prompt",
        "body",
        "input",
        "output",
        "text",
        "content",
        "message",
        "description",
        "problem_description",
        "hint_text",
        "proposal_text",
        "raw_text",
        "user_content",
        "messages",
        "response",
    }
)


def _drop_denied_keys(
    _logger: object, _method: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """structlog-Processor: entfernt Deny-Liste-Keys aus jedem Event-Dict.

    Strukturelle Durchsetzung der Logging-Allowlist (H-027) -- verhindert, dass
    Freitext-Keys wie prompt/body/output versehentlich in die Logs gelangen.
    """
    for key in _DENIED_KEYS:
        event_dict.pop(key, None)
    return event_dict


def configure_logging(log_level: int = logging.INFO) -> None:
    """Konfiguriert structlog einmalig fuer den Prozess.

    merge_contextvars: bindet request_id und route aus
    CorrelationIDMiddleware automatisch in jeden Log-Aufruf ein.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            _drop_denied_keys,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
