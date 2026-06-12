"""structlog-Konfiguration fuer AECT.

Allowlist (aect-security-checklist v2.1, Phase B; erweitert Tag 32/33):
  Erlaubt:  timestamp, level, logger, request_id, route,
            status, latency_ms, token_count, case_id, operation,
            input_tokens, output_tokens, cost_eur_estimate, fields.
  Verboten: body, prompt, PII, Secrets.

JSON-Output: maschinenlesbar, kompatibel mit Azure Monitor und ELK.
configure_logging() ist idempotent -- Mehrfachaufruf in Tests harmlos.
"""

from __future__ import annotations

import logging

import structlog


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
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
