"""Deterministischer Zahlen-Validator fuer die Use-Case-Schaerfung (V4, SDR-0003).

Schicht: domain -- kein Framework-Import, kein I/O. Importiert NUR aus
aect.domain (UseCaseInput). Reine Regel-Logik, kein LLM.

Zweck: Die LLM-Schaerfung darf keine Zahlen erfinden, die im Original nicht
vorkommen (Projektregel "keine erfundenen Zahlen"). Real beobachtet: der
geschaerfte Text enthielt "20 Minuten", "4.200 EUR", "1.000 EUR", "5 Minuten"
-- keine davon stand im Input. Dieser Validator laeuft VOR dem Persistieren:

  allowlist = build_allowlist(case.use_case)      # alle Eingabe-Zahlen
  violations = find_violations(allowlist, text)   # Zahlen im Ergebnis, die
                                                  # nicht im Original stehen

Kanonische Form: Zahlen werden vor dem Vergleich normalisiert, damit ein
uebernommener Wert unabhaengig von der Schreibweise als uebernommen erkannt
wird (deutsches "4.200" == Feldwert 4200 == "4200"). Ableitung: verwendet das
LLM eine tatsaechlich eingegebene Zahl wieder, ist das korrekt.

Bewusst KEIN NLP: eine feste Zahlwort-Liste (eins..zwoelf, zwanzig..neunzig,
hundert, tausend) genuegt fuer die haeufigen Faelle; alles andere fuehrt zu
mehr Fehlklassifikation als Nutzen.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from aect.domain.models import UseCaseInput

# Einfache deutsche Zahlwoerter -> kanonischer Zahlenstring. Die Schluessel
# muessen die Umlaute tragen, die das LLM ausgibt ("fuenf" schreibt es als
# "fünf") -- reine Datenstrings, keine RUF001-Confusables (Umlaute sind keine
# ASCII-Verwechsler). "dreissig" zusaetzlich fuer die ss-Schreibweise.
_NUMBER_WORDS: dict[str, str] = {
    "eins": "1",
    "zwei": "2",
    "drei": "3",
    "vier": "4",
    "fünf": "5",
    "sechs": "6",
    "sieben": "7",
    "acht": "8",
    "neun": "9",
    "zehn": "10",
    "elf": "11",
    "zwölf": "12",
    "zwanzig": "20",
    "dreißig": "30",
    "dreissig": "30",
    "vierzig": "40",
    "fünfzig": "50",
    "sechzig": "60",
    "siebzig": "70",
    "achtzig": "80",
    "neunzig": "90",
    "hundert": "100",
    "tausend": "1000",
}

# Zahlen-Token: beginnt und endet mit einer Ziffer, innen Punkte/Kommas erlaubt
# (deutsche Tausender-/Dezimaltrenner), oder eine einzelne Ziffer.
_NUMBER_TOKEN = r"\d[\d.,]*\d|\d"

# Zahlwort-Alternation, laengste zuerst (Boundaries trennen ohnehin, aber so
# bleibt die Alternation robust). \b arbeitet unter re.UNICODE (str-Default)
# auch fuer Umlaut-Woerter korrekt.
_WORD_ALT = "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))

_TOKEN_OR_WORD = re.compile(
    rf"(?P<num>{_NUMBER_TOKEN})|(?P<word>\b(?:{_WORD_ALT})\b)",
    re.IGNORECASE,
)

# Ordinal-/Aufzaehlungsmarker am Zeilenanfang bzw. nach Satzende: "1.", "2)",
# "3:" gefolgt von Whitespace. Werden vor der Extraktion entfernt -- ein
# Listenpunkt ist keine erfundene Zahl. Eine "1.000" (Punkt direkt gefolgt von
# drei Ziffern, kein Whitespace) bleibt unberuehrt.
_ENUM_MARKER_LINE = re.compile(r"(?m)^[ \t]*\d{1,3}[.):]\s")
_ENUM_MARKER_SENTENCE = re.compile(r"(?<=[.!?]\s)\d{1,3}[.):]\s")


def _strip_enum_markers(text: str) -> str:
    """Entfernt Aufzaehlungs-/Ordinalmarker am Zeilen-/Satzanfang."""
    text = _ENUM_MARKER_LINE.sub(" ", text)
    text = _ENUM_MARKER_SENTENCE.sub(" ", text)
    return text


def _token_to_ascii(token: str) -> str | None:
    """Deutsches Zahlen-Token -> ASCII-Dezimalstring (Punkt = Dezimaltrenner).

    Regeln:
      "1.000,50" (Punkt + Komma) -> Punkte sind Tausender, Komma ist Dezimal.
      "4,5"      (nur Komma)      -> Komma ist Dezimal.
      "4.200"    (nur Punkt, 3er-Gruppen) -> Tausendertrenner, Punkte entfernt.
      "4.5"      (nur Punkt, keine 3er-Gruppe) -> Dezimalpunkt.
      "20"       (nur Ziffern)    -> unveraendert.
    """
    has_dot = "." in token
    has_comma = "," in token

    if has_dot and has_comma:
        int_part, _, frac = token.rpartition(",")
        int_part = int_part.replace(".", "")
        return f"{int_part}.{frac}" if frac else int_part
    if has_comma:
        int_part, _, frac = token.rpartition(",")
        int_part = int_part.replace(",", "")
        return f"{int_part}.{frac}" if frac else int_part
    if has_dot:
        parts = token.split(".")
        is_thousands = (
            len(parts) >= 2
            and 1 <= len(parts[0]) <= 3
            and all(len(p) == 3 for p in parts[1:])
        )
        if is_thousands:
            return "".join(parts)
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}"
        return "".join(parts)
    return token


def _canonical(ascii_num: str) -> str | None:
    """ASCII-Dezimalstring -> kanonische Form (kein Exponent, keine Nachnull).

    20 -> "20", 4200 -> "4200", 1000.50 -> "1000.5", 0.0 -> "0". Ungueltiges
    (leerer/kaputter Token) -> None.
    """
    try:
        value = Decimal(ascii_num)
    except InvalidOperation:
        return None
    return f"{value.normalize():f}"


def _extract_ordered(text: str) -> list[str]:
    """Alle Zahlen in Erscheinungsreihenfolge, kanonisch (mit Duplikaten)."""
    cleaned = _strip_enum_markers(text)
    out: list[str] = []
    for match in _TOKEN_OR_WORD.finditer(cleaned):
        raw_num = match.group("num")
        if raw_num is not None:
            ascii_num = _token_to_ascii(raw_num)
            if ascii_num is None:
                continue
            canonical = _canonical(ascii_num)
            if canonical is not None:
                out.append(canonical)
        else:
            out.append(_NUMBER_WORDS[match.group("word").lower()])
    return out


def extract_numbers(text: str) -> set[str]:
    """Extrahiert alle Zahlen eines Textes in kanonischer Form.

    Deutsche Formate (4.200 -> "4200", 1.000,50 -> "1000.5", 4,5 -> "4.5"),
    einfache Zahlwoerter (zwanzig -> "20") und einzelne Ziffern. Prozent/
    Einheiten sind egal -- nur der numerische Wert zaehlt. Ordinal-/
    Aufzaehlungsmarker am Zeilen-/Satzanfang (1., 2), 3:) werden ignoriert;
    Jahreszahlen NICHT (auch die duerfen nicht erfunden werden).
    """
    return set(_extract_ordered(text))


def build_allowlist(use_case: UseCaseInput) -> set[str]:
    """Vereinigung aller Zahlen der Eingabe in kanonischer Form.

    Quellen: alle Original-Textfelder (Titel, Ist, Soll, Beispiele, Notizen,
    Einreicher, Abteilung) plus alle numerischen Case-Felder (Zeit_ist, Zeit_ai,
    Haeufigkeit je MA, MA-Anzahl, Kosten). Verwendet das LLM eine dieser Zahlen
    wieder, ist das korrekt (keine erfundene Zahl).
    """
    allow: set[str] = set()

    text_fields = (
        use_case.title,
        use_case.submitter,
        use_case.department,
        use_case.current_state,
        use_case.desired_state,
        use_case.example_process,
        use_case.desired_example_process,
        use_case.notes,
    )
    for field in text_fields:
        if field:
            allow |= extract_numbers(field)

    numeric_fields: tuple[float | int, ...] = (
        use_case.time_per_case_hours_current,
        use_case.time_per_case_hours_with_ai,
        use_case.occurrences_per_employee_per_year,
        use_case.affected_employees_count,
        use_case.estimated_license_cost_eur,
        use_case.implementation_cost_eur,
    )
    for value in numeric_fields:
        canonical = _canonical(str(value))
        if canonical is not None:
            allow.add(canonical)

    return allow


def find_violations(allowlist: set[str], sharpened_text: str) -> list[str]:
    """Zahlen im geschaerften Text, die nicht in der Allowlist stehen.

    Reihenfolge = erstes Erscheinen im Text (deterministisch, lesbar fuer die
    Korrektur-Instruktion und die 422-Antwort), Duplikate entfernt.
    """
    violations: list[str] = []
    seen: set[str] = set()
    for number in _extract_ordered(sharpened_text):
        if number in allowlist or number in seen:
            continue
        seen.add(number)
        violations.append(number)
    return violations
