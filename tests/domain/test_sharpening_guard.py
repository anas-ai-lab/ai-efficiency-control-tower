"""Unit-Tests fuer den deterministischen Zahlen-Validator (V4, SDR-0003).

Deckt den real beobachteten Fall (Original ohne Zahlen -> geschaerfter Text
mit vier erfundenen Zahlen) plus die Normalisierungs-Regeln ab.
"""

from __future__ import annotations

from aect.domain import UseCaseInput
from aect.domain.sharpening_guard import (
    build_allowlist,
    extract_numbers,
    find_violations,
)


class TestExtractNumbers:
    def test_plain_integer(self) -> None:
        assert extract_numbers("Der Vorgang dauert 20 Minuten") == {"20"}

    def test_german_thousands_separator(self) -> None:
        # 4.200 ist Tausendertrennung, kein Dezimalpunkt.
        assert extract_numbers("Kosten von 4.200 EUR pro Jahr") == {"4200"}

    def test_german_decimal_comma(self) -> None:
        assert extract_numbers("Faktor 4,5 im Modell") == {"4.5"}

    def test_thousands_with_decimal(self) -> None:
        assert extract_numbers("Gesamt 1.000,50 EUR") == {"1000.5"}

    def test_units_and_percent_ignored(self) -> None:
        # Nur der numerische Wert zaehlt, Einheit/Prozent egal.
        assert extract_numbers("unter 1 Prozent und 2 Minuten") == {"1", "2"}

    def test_number_word_is_captured(self) -> None:
        assert extract_numbers("zwanzig Minuten pro Fall") == {"20"}

    def test_number_words_range(self) -> None:
        assert extract_numbers("fünf und zwölf und hundert und tausend") == {
            "5",
            "12",
            "100",
            "1000",
        }

    def test_enum_markers_are_ignored(self) -> None:
        text = "1. Erster Punkt\n2) Zweiter Punkt\n3: Dritter Punkt"
        assert extract_numbers(text) == set()

    def test_year_is_not_exempt(self) -> None:
        # Jahreszahlen duerfen ebenfalls nicht erfunden werden.
        assert extract_numbers("Start im Jahr 2026") == {"2026"}

    def test_thousands_marker_not_confused_with_enum(self) -> None:
        # "1.000" (Punkt direkt gefolgt von drei Ziffern) ist eine Zahl, kein
        # Aufzaehlungsmarker.
        assert extract_numbers("Es fallen 1.000 Vorgaenge an") == {"1000"}


class TestBuildAllowlist:
    def test_collects_numeric_case_fields(self, sample_use_case: UseCaseInput) -> None:
        allow = build_allowlist(sample_use_case)
        # Zeit_ist 0.5, Zeit_ai 0.3, Haeufigkeit/MA 5000, MA 10, Lizenz 15000,
        # Impl-Kosten 0 (Default).
        assert {"0.5", "0.3", "5000", "10", "15000", "0"} <= allow

    def test_collects_numbers_from_text_fields(
        self, sample_use_case: UseCaseInput
    ) -> None:
        enriched = sample_use_case.model_copy(
            update={
                "current_state": (
                    "Heute dauert ein Vorgang 15 Minuten und kommt oft vor "
                    "im Sachbearbeitungs-Team."
                )
            }
        )
        assert "15" in build_allowlist(enriched)

    def test_reused_thousands_format_matches_field_value(
        self, sample_use_case: UseCaseInput
    ) -> None:
        # Feldwert 5000 muss die deutsche Schreibweise 5.000 im Text decken.
        allow = build_allowlist(sample_use_case)
        assert find_violations(allow, "rund 5.000 Vorgaenge pro Jahr") == []


class TestFindViolations:
    def test_real_observed_case_four_violations(
        self, sample_use_case: UseCaseInput
    ) -> None:
        # Original (sample_use_case) traegt keine dieser Zahlen im Text; die
        # numerischen Felder sind 0.5/0.3/5000/10/15000/0 -- keine davon ist
        # 20/4200/1000/5. Der geschaerfte Text erfindet genau vier Zahlen.
        allow = build_allowlist(sample_use_case)
        sharpened = (
            "Der Vorgang dauert 20 Minuten und kostet 4.200 EUR, "
            "was 1.000 EUR spart und nur 5 Minuten benoetigt."
        )
        assert find_violations(allow, sharpened) == ["20", "4200", "1000", "5"]

    def test_reused_original_number_is_no_violation(self) -> None:
        assert find_violations({"15"}, "weiterhin 15 Minuten pro Vorgang") == []

    def test_number_word_triggers_violation_when_not_in_allowlist(self) -> None:
        assert find_violations(set(), "etwa zwanzig Minuten") == ["20"]

    def test_number_word_no_violation_when_value_in_allowlist(self) -> None:
        # "zwanzig" normalisiert auf 20 -- ist 20 in der Allowlist, keine
        # Verletzung.
        assert find_violations({"20"}, "etwa zwanzig Minuten") == []

    def test_enum_markers_are_no_violation(self) -> None:
        text = "1. Punkt A\n2. Punkt B\n3. Punkt C"
        assert find_violations(set(), text) == []

    def test_violations_are_deduplicated_in_appearance_order(self) -> None:
        text = "50 und 20 und 50 erneut"
        assert find_violations(set(), text) == ["50", "20"]
