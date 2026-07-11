"""Deutsche Zahlenformatierung fuer generierte Fliesstexte (V4-P7).

Die erklaerenden Textbausteine (Score-Begruendungen, Empfehlungssatz,
Zonen-Begruendung) betten Geldbetraege und Stunden in ganze Saetze ein. Sie
muessen deutsches Tausenderformat tragen ("6.000 EUR", nicht "6,000 EUR") --
englische Formatierung war ein Befund aus dem manuellen V4-Durchlauf: auf der
Detailseite standen die korrekt formatierten Frontend-Kennzahlen ("87.139 EUR")
neben den englisch formatierten Fliesstexten ("87,139 EUR").

Bewusst getrennt gehalten: Nachkommazahlen (Faktoren wie "0,40") formatieren die
Aufrufer weiterhin selbst per ``.replace(".", ",")`` -- ein blankes
Sentence-weites Ersetzen von "," -> "." wuerde diese Dezimal-Kommas zerstoeren.
Darum ein Helfer pro Zahl statt pro Satz.

ASCII-Regel (RUF001/002/003): keine Umlaute/Sonderzeichen in diesem Modul.
"""

from __future__ import annotations

from decimal import Decimal


def format_de(value: float | Decimal, unit: str = "") -> str:
    """Formatiert eine ganze Zahl im deutschen Tausenderformat, optional mit Einheit.

    ``6000 -> "6.000"``, ``(6000, "EUR") -> "6.000 EUR"``,
    ``(3360, "Stunden") -> "3.360 Stunden"``. Rundet auf ganze Zahlen -- die
    Fliesstexte tragen keine Nachkommastellen.

    Trick: ``{:,.0f}`` liefert das englische Tausenderformat ("6,000") ohne
    Dezimalstellen; da keine Nachkommastelle entsteht, ist das einzige "," ein
    Tausendertrenner und kann gefahrlos zu "." werden.
    """
    formatted = f"{value:,.0f}".replace(",", ".")
    return f"{formatted} {unit}" if unit else formatted
