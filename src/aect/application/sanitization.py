"""Injection-Pattern-Erkennung fuer LLM-Inputs (OWASP LLM01).

aect-security-checklist v2.1, Phase C: "Input-Sanitization vor LLM-Call:
bekannte Injection-Patterns flaggen/blocken."

Entscheidung (Tag 32): FLAGGEN, nicht BLOCKEN. AECT ist ein Advisory-Layer,
kein Gatekeeper -- ein hartes Blocken bei False Positives wuerde legitime
Einreichungen ablehnen (z. B. "ignoriere die alte Prozessbeschreibung" in
einem echten Ist-Zustand-Text). Erkannte Patterns werden geloggt
(case_id + Feldname + Pattern-Namen, kein Body -- Logging-Allowlist v2.1),
der LLM-Call laeuft trotzdem weiter. Der strukturelle Schutz (Delimiter
<<<DATA>>>/<<<END_DATA>>> in prompts/sharpen_use_case/v1/user.md) bleibt die
primaere Verteidigung; dies ist Defense-in-Depth + Observability.
"""

from __future__ import annotations

import re

# Jedes Pattern: (Name, compiled regex). Case-insensitive, DE + EN.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignore_instructions",
        re.compile(
            r"(ignore|disregard|forget)\s+"
            r"(all\s+|previous\s+|the\s+above\s+|your\s+)*"
            r"(instructions?|prompts?|rules)"
            r"|(ignorier(?:e|en)|vergiss|missachte)\s+"
            r"(alle\s+|vorherigen\s+|obigen\s+|deine\s+)*"
            r"(anweisungen|regeln|instruktionen)",
            re.IGNORECASE,
        ),
    ),
    (
        "role_hijack",
        re.compile(
            r"\b(you are now|act as|pretend to be|du bist (jetzt|ab jetzt)|"
            r"verhalte dich (als|wie))\b"
            r"|^(system|assistant)\s*:",
            re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "delimiter_breakout",
        re.compile(r"<<<\s*(DATA|END_DATA|SYSTEM|END_SYSTEM)\s*>>>", re.IGNORECASE),
    ),
    (
        "prompt_exfiltration",
        re.compile(
            r"(repeat|show|reveal|print|wiederhole|zeige|gib)\s+.{0,20}"
            r"(system.?prompt|instructions?|anweisungen)",
            re.IGNORECASE,
        ),
    ),
]


def detect_injection_patterns(text: str) -> list[str]:
    """Sucht bekannte Prompt-Injection-Muster in einem Text.

    Returns:
        Liste der Namen erkannter Patterns (leer wenn keine Treffer).
        Reihenfolge entspricht der Pruefreihenfolge, keine Duplikate.
    """
    return [name for name, pattern in _PATTERNS if pattern.search(text)]


# Delimiter-Marker, die die DATA-/SYSTEM-Region im Prompt abgrenzen
# (prompts/*/user.md). Gleiche Marker wie das delimiter_breakout-Pattern oben.
_DELIMITER_TOKEN: re.Pattern[str] = re.compile(
    r"<<<\s*(?:DATA|END_DATA|SYSTEM|END_SYSTEM)\s*>>>", re.IGNORECASE
)


def neutralize_delimiters(text: str) -> str:
    """Entschaerft Data-Region-Delimiter in User-Freitext (struktureller Schutz).

    Ersetzt jedes <<<DATA>>>/<<<END_DATA>>>/<<<SYSTEM>>>/<<<END_SYSTEM>>>-Token
    (case-insensitive, optionaler Whitespace) durch eine sichtbare, aber inerte
    Form (Winkelklammern -> runde Klammern), sodass ein Feldwert die vom
    Prompt-Template gesetzte Datenregion strukturell nicht aufbrechen kann.

    Das macht den Delimiter-Contract belastbar statt konventionell: Flaggen
    (detect_injection_patterns) bleibt Observability, dies ist die strukturelle
    Verteidigung (OWASP LLM01, Delimiter-Breakout).
    """
    return _DELIMITER_TOKEN.sub(
        lambda m: m.group(0).replace("<", "(").replace(">", ")"), text
    )
