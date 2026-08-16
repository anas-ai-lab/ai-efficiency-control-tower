"""Auswahl oeffentlicher Top-Case-Referenzen (Ticket 4b)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TopCaseRef:
    """Oeffentliche Referenz auf einen Top-Case -- bewusst OHNE Geldwert.

    Das Sortierkriterium bleibt intern: User duerfen nur die
    Top-3-Zugehoerigkeit sehen (Ticket 4b).
    """

    case_id: str
    title: str


def select_top_cases(
    candidates: list[tuple[str, str, Decimal]],
    limit: int = 3,
) -> list[TopCaseRef]:
    """Waehlt die Cases mit dem hoechsten Netto-Nutzen aus.

    candidates enthaelt (case_id, title, net_expected_benefit_eur) und ist vom
    Aufrufer bereits auf bewertete, nicht eingestellte Cases gefiltert.
    Sortiert wird absteigend nach Netto-Nutzen, bei Gleichstand aufsteigend nach
    case_id. Der Geldwert bleibt ausschliesslich im internen Sortierschluessel.
    """
    ranked = sorted(candidates, key=lambda candidate: (-candidate[2], candidate[0]))
    return [
        TopCaseRef(case_id=case_id, title=title)
        for case_id, title, _net_benefit in ranked[:limit]
    ]
