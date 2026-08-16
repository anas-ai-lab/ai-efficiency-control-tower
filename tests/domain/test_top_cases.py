"""Unit-Tests fuer die reine Top-Case-Auswahl (Ticket 4b)."""

from decimal import Decimal

from aect.domain.top_cases import TopCaseRef, select_top_cases


def test_empty_candidates_return_empty_list() -> None:
    assert select_top_cases([]) == []


def test_single_candidate_returns_single_reference() -> None:
    candidates = [("case-1", "Ein Case", Decimal("100"))]

    assert select_top_cases(candidates) == [
        TopCaseRef(case_id="case-1", title="Ein Case")
    ]


def test_two_candidates_are_not_padded_to_three() -> None:
    candidates = [
        ("case-1", "Erster Case", Decimal("100")),
        ("case-2", "Zweiter Case", Decimal("200")),
    ]

    assert select_top_cases(candidates) == [
        TopCaseRef(case_id="case-2", title="Zweiter Case"),
        TopCaseRef(case_id="case-1", title="Erster Case"),
    ]


def test_five_candidates_return_exactly_three_highest_in_order() -> None:
    candidates = [
        ("case-1", "Platz vier", Decimal("20")),
        ("case-2", "Platz zwei", Decimal("80")),
        ("case-3", "Platz fuenf", Decimal("10")),
        ("case-4", "Platz eins", Decimal("100")),
        ("case-5", "Platz drei", Decimal("50")),
    ]

    assert select_top_cases(candidates) == [
        TopCaseRef(case_id="case-4", title="Platz eins"),
        TopCaseRef(case_id="case-2", title="Platz zwei"),
        TopCaseRef(case_id="case-5", title="Platz drei"),
    ]


def test_equal_benefit_uses_case_id_tie_break_independent_of_input_order() -> None:
    candidates = [
        ("case-b", "Case B", Decimal("42")),
        ("case-a", "Case A", Decimal("42")),
    ]
    expected = [
        TopCaseRef(case_id="case-a", title="Case A"),
        TopCaseRef(case_id="case-b", title="Case B"),
    ]

    assert select_top_cases(candidates) == expected
    assert select_top_cases(list(reversed(candidates))) == expected


def test_negative_benefit_is_not_filtered_out() -> None:
    candidates = [
        ("case-negative", "Negativer Case", Decimal("-10")),
        ("case-positive", "Positiver Case", Decimal("10")),
    ]

    assert select_top_cases(candidates) == [
        TopCaseRef(case_id="case-positive", title="Positiver Case"),
        TopCaseRef(case_id="case-negative", title="Negativer Case"),
    ]
