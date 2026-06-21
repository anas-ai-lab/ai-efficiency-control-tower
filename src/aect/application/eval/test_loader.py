"""Tests fuer den Eval-Case-Loader (Master-Plan v3.1 Phase E, ADR-0029)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aect.application.eval import EvalCase, EvalCaseLoadError, load_eval_cases

GOLDEN_CASES_PATH = Path("evals/golden/use_cases.jsonl")


class TestLoadEvalCases:
    def test_loads_all_golden_cases(self) -> None:
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        assert len(cases) == 4
        assert all(isinstance(case, EvalCase) for case in cases)

    def test_case_ids_are_unique(self) -> None:
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        case_ids = [case.case_id for case in cases]
        assert len(case_ids) == len(set(case_ids))

    def test_golden_cases_have_no_expert_label_yet(self) -> None:
        """Expert-Labels werden bewusst an einem spaeteren Phase-E-Tag ergaenzt."""
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        assert all(case.expected_zone is None for case in cases)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(EvalCaseLoadError, match="nicht gefunden"):
            load_eval_cases(tmp_path / "does-not-exist.jsonl")

    def test_malformed_json_raises_with_line_number(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.jsonl"
        bad_file.write_text(
            '{"case_id": "x", "use_case": {}}\nnot json at all\n', encoding="utf-8"
        )
        with pytest.raises(EvalCaseLoadError, match="Zeile 2"):
            load_eval_cases(bad_file)

    def test_invalid_use_case_raises_with_line_number(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.jsonl"
        bad_file.write_text(
            '{"case_id": "x", "use_case": {"title": "zu kurz"}}\n', encoding="utf-8"
        )
        with pytest.raises(EvalCaseLoadError, match="Zeile 1"):
            load_eval_cases(bad_file)

    def test_blank_lines_are_skipped(self, tmp_path: Path) -> None:
        good_line = GOLDEN_CASES_PATH.read_text(encoding="utf-8").splitlines()[0]
        f = tmp_path / "with_blanks.jsonl"
        f.write_text(f"\n{good_line}\n\n", encoding="utf-8")
        cases = load_eval_cases(f)
        assert len(cases) == 1
