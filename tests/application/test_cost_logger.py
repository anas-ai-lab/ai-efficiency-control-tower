"""Tests fuer Cost-Logger -- Token-Zaehlung und Kostenschaetzung (tiktoken)."""

from __future__ import annotations

from structlog.testing import capture_logs

from aect.application.cost_logger import count_tokens, estimate_cost_eur, log_llm_cost
from aect.application.ports.llm import LLMMessage, LLMResponse


class TestCountTokens:
    def test_empty_string_has_zero_tokens(self) -> None:
        assert count_tokens("") == 0

    def test_nonempty_text_has_positive_tokens(self) -> None:
        assert count_tokens("Hallo Welt") > 0

    def test_longer_text_has_more_tokens(self) -> None:
        short = count_tokens("Kurzer Text.")
        long_ = count_tokens("Kurzer Text. " * 10)
        assert long_ > short


class TestEstimateCostEur:
    def test_zero_tokens_costs_nothing(self) -> None:
        assert estimate_cost_eur(0, 0) == 0.0

    def test_output_tokens_cost_more_than_input_tokens(self) -> None:
        input_cost = estimate_cost_eur(1000, 0)
        output_cost = estimate_cost_eur(0, 1000)
        assert output_cost > input_cost

    def test_cost_scales_linearly(self) -> None:
        single = estimate_cost_eur(1_000_000, 0)
        double = estimate_cost_eur(2_000_000, 0)
        assert double == single * 2


class TestLogLlmCost:
    def test_logs_llm_call_cost_event_with_expected_fields(self) -> None:
        messages = [
            LLMMessage(role="system", content="Du bist ein hilfreicher Assistent."),
            LLMMessage(role="user", content="Fasse diesen Use Case zusammen."),
        ]
        response = LLMResponse(content="Zusammenfassung des Use Cases.")

        with capture_logs() as logs:
            log_llm_cost(
                case_id="case-123",
                messages=messages,
                response=response,
                operation="sharpen_case",
            )

        cost_logs = [log for log in logs if log["event"] == "llm_call_cost"]
        assert len(cost_logs) == 1
        entry = cost_logs[0]
        assert entry["case_id"] == "case-123"
        assert entry["operation"] == "sharpen_case"
        assert entry["input_tokens"] > 0
        assert entry["output_tokens"] > 0
        assert entry["token_count"] == entry["input_tokens"] + entry["output_tokens"]
        assert entry["cost_eur_estimate"] > 0
