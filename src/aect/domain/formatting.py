"""Sprachabhaengige Zahlenformatierung fuer generierte Fliesstexte (V4-P7, V4.1-S6).

Die erklaerenden Textbausteine (Score-Begruendungen, Empfehlungssatz,
Zonen-Begruendung) betten Geldbetraege und Stunden in ganze Saetze ein. Sie
muessen das Tausenderformat der aktiven Sprache tragen: deutsch "6.000 EUR",
englisch "6,000 EUR". Der Ausgangsbefund aus dem manuellen V4-Durchlauf war
umgekehrt -- englisch formatierte Fliesstexte ("87,139 EUR") neben den korrekt
deutsch formatierten Frontend-Kennzahlen ("87.139 EUR"). Seit V4.1-S6 sind die
Texte selbst sprachabhaengig; die Formatierung muss der Sprache folgen.

``format_number(value, lang, unit)`` ist der sprachabhaengige Helfer; ``format_de``
bleibt als DE-Kurzform erhalten (delegiert an ``format_number(value, "de", unit)``)
und aendert sein Verhalten nicht.

Bewusst getrennt gehalten: Nachkommazahlen (Faktoren wie "0,40") formatieren die
Aufrufer weiterhin selbst per ``.replace(".", ",")`` -- ein blankes
Sentence-weites Ersetzen von "," -> "." wuerde diese Dezimal-Kommas zerstoeren.
Darum ein Helfer pro Zahl statt pro Satz.

ASCII-Regel (RUF001/002/003): keine Umlaute/Sonderzeichen in diesem Modul.
"""

from __future__ import annotations

from decimal import Decimal

from aect.domain.i18n import Lang


def format_number(value: float | Decimal, lang: Lang, unit: str = "") -> str:
    """Formatiert eine ganze Zahl im Tausenderformat der Sprache, optional mit Einheit.

    ``de``: deutsches Format ("259.200"), ``en``: englisches Format ("259,200").
    ``(259200, "en", "EUR") -> "259,200 EUR"``,
    ``(259200, "de", "EUR") -> "259.200 EUR"``. Rundet auf ganze Zahlen -- die
    Fliesstexte tragen keine Nachkommastellen.

    Trick: ``{:,.0f}`` liefert das englische Tausenderformat ("259,200") ohne
    Dezimalstellen. Da keine Nachkommastelle entsteht, ist das einzige "," ein
    reiner Tausendertrenner: fuer ``en`` bereits das Ziel, fuer ``de`` gefahrlos
    zu "." zu ersetzen.
    """
    formatted = f"{value:,.0f}"
    if lang == "de":
        formatted = formatted.replace(",", ".")
    return f"{formatted} {unit}" if unit else formatted


def format_de(value: float | Decimal, unit: str = "") -> str:
    """Deutsche Kurzform von ``format_number`` -- Verhalten unveraendert.

    ``6000 -> "6.000"``, ``(6000, "EUR") -> "6.000 EUR"``,
    ``(3360, "Stunden") -> "3.360 Stunden"``.
    """
    return format_number(value, "de", unit)
