"""Drift-Guard: die Punktesystem-Erklaerung im Frontend gegen die Domain-Logik.

Die Erklaerung "Wie das Punktesystem funktioniert" (result.scoring.* in
frontend/messages/{de,en}.json) spiegelt `aect.domain.scoring` VON HAND: sie
nennt die Komplexitaets-Punkte je Ansatz, die Datenschutz-Punkte, den
Wertebereich und die Baender niedrig/mittel/hoch als ausgeschriebene Zahlen.
Ohne Kopplung faellt eine Aenderung an scoring.py niemandem auf -- der Text
bliebe plausibel und waere still falsch. Dasselbe Muster wie die Umlaut-Luecke
und _KB_UNAVAILABLE_HINT: Text und Logik ohne automatischen Gleichlauf.

Der Test vergleicht die im Text stehenden Zahlen mit Werten, die er AUS DEM
CODE ableitet -- keine Literale aus dem Text als Erwartung. Aendert jemand eine
Konstante in scoring.py ohne den Text, wird der Test rot.

Sprachunabhaengig: geprueft werden Ziffern, nicht Formulierungen. Beide
Kataloge muessen dieselben Zahlen tragen (der Score ist keine Sprachfrage).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from aect.domain.explainability import feasibility_from_composite
from aect.domain.scoring import (
    COMPLEXITY_BY_APPROACH,
    DATA_CLASSIFICATION_TO_SCORE,
    CompositeScore,
)

LANGS = ("de", "en")

# Zahlen, die aus dem Text gelesen werden, ohne Gesetzesverweise: "Art. 4 Nr. 5
# DSGVO" / "Art. 4(5) GDPR" traegt Ziffern, die nichts mit Punkten zu tun haben.
# Darum werden die Datenschutz-Punkte ueber ihr Bezugswort gelesen.
_POINTS_RE = {
    "de": re.compile(r"(\d+)\s+Punkte?\b"),
    "en": re.compile(r"(\d+)\s+points?\b"),
}
_INT_RE = re.compile(r"\d+")


def _messages(lang: str) -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[1] / "frontend" / "messages" / f"{lang}.json"
    )
    # Fail loud: fehlt der Katalog, ist der Guard wertlos -- kein Skip.
    assert path.is_file(), f"Katalog fehlt: {path}"
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def _text(lang: str, *keys: str) -> str:
    node: Any = _messages(lang)
    for key in keys:
        assert key in node, f"{lang}.json: Schluessel {'.'.join(keys)} fehlt"
        node = node[key]
    assert isinstance(node, str), f"{lang}.json: {'.'.join(keys)} ist kein String"
    return node


def _ints(text: str) -> list[int]:
    return [int(m) for m in _INT_RE.findall(text)]


# ---------------------------------------------------------------------------
# Erwartungswerte -- ausschliesslich aus dem Code abgeleitet
# ---------------------------------------------------------------------------
def _all_valid_scores() -> list[CompositeScore]:
    """Alle gueltigen Kombinationen -- die Bereiche/Baender fallen daraus."""
    out: list[CompositeScore] = []
    for complexity in sorted(set(COMPLEXITY_BY_APPROACH.values())):
        for cost in range(0, 3):
            for data in sorted(set(DATA_CLASSIFICATION_TO_SCORE.values())):
                out.append(
                    CompositeScore(
                        complexity_score=complexity,
                        cost_score=cost,
                        data_protection_score=data,
                        total=complexity + cost + data,
                    )
                )
    return out


def _band_maxima() -> tuple[int, int]:
    """Groesster Total mit NIEDRIG bzw. MITTEL -- aus effort_label gelesen."""
    by_label: dict[str, list[int]] = {}
    for score in _all_valid_scores():
        by_label.setdefault(score.effort_label, []).append(score.total)
    assert set(by_label) == {"NIEDRIG", "MITTEL", "HOCH"}, (
        f"effort_label liefert unerwartete Stufen: {sorted(by_label)} -- "
        "der Text nennt genau drei (niedrig/mittel/hoch)."
    )
    return max(by_label["NIEDRIG"]), max(by_label["MITTEL"])


def _total_range() -> tuple[int, int]:
    totals = [s.total for s in _all_valid_scores()]
    return min(totals), max(totals)


@pytest.mark.parametrize("lang", LANGS)
def test_complexity_points_match_scoring(lang: str) -> None:
    """Die Punkte je Umsetzungsansatz stehen so im Text wie im Mapping.

    Der Text zaehlt die Ansaetze in der Reihenfolge auf, in der sie in
    COMPLEXITY_BY_APPROACH deklariert sind (ordinal aufsteigend). Verglichen
    wird die Ziffernfolge -- das faengt geaenderte Werte, vertauschte Werte und
    einen neu hinzugekommenen Ansatz (dann stimmt die Anzahl nicht).
    """
    expected = list(COMPLEXITY_BY_APPROACH.values())
    found = _ints(_text(lang, "result", "scoring", "complexity", "text"))
    assert found == expected, (
        f"{lang}.json result.scoring.complexity.text nennt {found}, "
        f"COMPLEXITY_BY_APPROACH liefert {expected}. Text und scoring.py "
        "sind auseinandergelaufen."
    )


@pytest.mark.parametrize("lang", LANGS)
def test_data_protection_points_match_scoring(lang: str) -> None:
    """Die Datenschutz-Punkte im Text entsprechen DATA_CLASSIFICATION_TO_SCORE.

    Der Text fasst personenbezogen und pseudonym zu EINER Stufe zusammen (beide
    1 Punkt, Art. 4 Nr. 5 DSGVO) und nennt daher drei Punktwerte fuer vier
    Klassen. Geprueft werden die distinkten Punktwerte -- plus die Anzahl der
    Klassen, damit eine neue Klassifizierung nicht unbemerkt dazukommt.
    """
    assert len(DATA_CLASSIFICATION_TO_SCORE) == 4, (
        "DATA_CLASSIFICATION_TO_SCORE hat jetzt "
        f"{len(DATA_CLASSIFICATION_TO_SCORE)} Klassen statt 4 -- der Text fasst "
        "genau vier Klassen zu drei Punktstufen zusammen und muss nachgezogen "
        "werden."
    )
    expected = sorted(set(DATA_CLASSIFICATION_TO_SCORE.values()))
    found = _POINTS_RE[lang].findall(
        _text(lang, "result", "scoring", "dataProtection", "text")
    )
    assert [int(x) for x in found] == expected, (
        f"{lang}.json result.scoring.dataProtection.text nennt {found}, "
        f"DATA_CLASSIFICATION_TO_SCORE liefert {expected}."
    )


@pytest.mark.parametrize("lang", LANGS)
def test_total_range_bands_and_feasibility_match_scoring(lang: str) -> None:
    """Wertebereich, Baender und die Machbarkeits-Formel stehen richtig im Text.

    Erwartet wird die Ziffernfolge [min, max, niedrig-bis, mittel-bis,
    Machbarkeits-Konstante]. Die Konstante 10 wird nicht literal erwartet,
    sondern aus feasibility_from_composite(0) gelesen.
    """
    min_total, max_total = _total_range()
    low_max, mid_max = _band_maxima()
    feasibility_const = feasibility_from_composite(0)
    expected = [min_total, max_total, low_max, mid_max, feasibility_const]

    found = _ints(_text(lang, "result", "scoring", "total"))
    assert found == expected, (
        f"{lang}.json result.scoring.total nennt {found}, aus dem Code folgt "
        f"{expected} (Bereich {min_total}-{max_total}, Baender bis {low_max}/"
        f"bis {mid_max}, Machbarkeit = {feasibility_const} - Aufwandscore)."
    )


@pytest.mark.parametrize("lang", LANGS)
def test_board_axis_ranges_match_scoring(lang: str) -> None:
    """Die Achsenbeschreibung des Boards nennt die drei Dimensions-Bereiche.

    Erwartet: Komplexitaet min-max, Kosten min-max, Datenschutz min-max.
    """
    complexities = sorted(set(COMPLEXITY_BY_APPROACH.values()))
    data_scores = sorted(set(DATA_CLASSIFICATION_TO_SCORE.values()))
    # Kostenpunkte: je ein Punkt fuer Impl.- und Lizenzschwelle -> 0 bis 2.
    # Aus der Invariante von CompositeScore gelesen, nicht literal gesetzt.
    cost_min, cost_max = 0, 2
    with pytest.raises(ValueError):
        CompositeScore(
            complexity_score=complexities[0],
            cost_score=cost_max + 1,
            data_protection_score=0,
            total=complexities[0] + cost_max + 1,
        )

    expected = [
        complexities[0],
        complexities[-1],
        cost_min,
        cost_max,
        data_scores[0],
        data_scores[-1],
    ]
    found = _ints(_text(lang, "board", "yAxisDesc"))
    assert found == expected, (
        f"{lang}.json board.yAxisDesc nennt {found}, aus dem Code folgt {expected}."
    )


@pytest.mark.parametrize("lang", LANGS)
def test_board_effort_note_range_matches_scoring(lang: str) -> None:
    """Die Kurznotiz am Board nennt den Wertebereich des Aufwand-Scores."""
    min_total, max_total = _total_range()
    found = _ints(_text(lang, "board", "effortScoreNote"))
    assert found == [min_total, max_total], (
        f"{lang}.json board.effortScoreNote nennt {found}, aus dem Code folgt "
        f"{[min_total, max_total]}."
    )
