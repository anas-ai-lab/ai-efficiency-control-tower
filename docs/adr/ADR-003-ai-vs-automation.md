# ADR-003 — AI-vs-Automation-Router: Regelbasierte Vorpruefung

**Status:** Accepted
**Datum:** Juni 2026
**Phase:** A - Phase-C-Erweiterung vorgesehen
**Entscheider:** Anas

---

## Kontext

Das Einreichungsformular setzt implizit voraus, dass jeder eingereichte
Use Case ein AI-Fall ist. Das ist falsch: Viele Anfragen beschreiben
regelbasierte Automatisierung (RPA, Scripts, BPMN-Workflows), die kein
LLM benoetigen. AECT muss diese Fehlklassifikation erkennen, bevor
die ROI-Berechnung und Zonenempfehlung in die falsche Richtung zeigen.

---

## Entscheidung

`route_use_case()` sammelt Signale aus drei unabhaengigen Kategorien,
wendet eine Entscheidungsmatrix an und gibt `RoutingResult` zurueck.

**4 moegliche Empfehlungen:**

| Empfehlung | Bedeutung |
|---|---|
| AI_RECOMMENDED | Ambigue, kontextabhaengig, sprachbasiert |
| AUTOMATION_RECOMMENDED | Regelbasiert, deterministisch, hohes Volumen |
| HUMAN_REVIEW_REQUIRED | >= 2 Datenschutz-/Risikoflags aktiv |
| BORDERLINE | Gemischte Signale oder Gleichstand - Phase-C-LLM entscheidet |

### Signal-Quellen (Phase A, regelbasiert)

**Automation-Signale (max. 4):**
- Komplexitaet <= 2 (einfacher Ablauf)
- Volumen >= 2.000/Jahr (hoher Automatisierungs-ROI)
- Pflichtnutzung (MANDATORY) - konsistentes Nutzungsverhalten
- STANDARD_PRODUCT geplant

**AI-Signale (max. 4):**
- Komplexitaet >= 4 (kontextabhaengig)
- Evidenz = PURE_ESTIMATE (explorativer Anwendungsfall)
- Soll-Beschreibung >= 300 Zeichen (mehrdimensionale Anforderung)
- CUSTOM_BUILD geplant

**Risikoflags (max. 2, unabhaengig von AI/Automation):**
- SENSITIVE_PERSONAL (Art. 9 DSGVO - DSFA-Pflicht)
- Regulatorischer Druck + PII gleichzeitig aktiv

### Entscheidungsmatrix
= 2 Risikoflags         → HUMAN_REVIEW_REQUIRED (HIGH)
Automation >= 2, AI = 0  → AUTOMATION_RECOMMENDED (HIGH)
Automation = 1, AI = 0   → AUTOMATION_RECOMMENDED (MEDIUM)
AI >= 2, Automation = 0  → AI_RECOMMENDED (HIGH)
AI = 1, Automation = 0   → AI_RECOMMENDED (MEDIUM)
Automation > AI gemischt → AUTOMATION_RECOMMENDED (LOW)
AI > Automation gemischt → AI_RECOMMENDED (LOW)
Gleichstand / keine      → BORDERLINE (LOW)

### Konkrete Designentscheidungen

**1. Signal-Sammlung und Entscheidungsmatrix sind getrennte Funktionen.**
`_collect_automation_signals()`, `_collect_ai_signals()`,
`_collect_risk_flags()` sind einzeln testbar. `_decide()` erhaelt
nur Integer-Zaehler. Kein God-Function-Anti-Pattern.

**2. 1 Risikoflag: `requires_human_review=True`, Empfehlung bleibt signalbasiert.**
`HUMAN_REVIEW_REQUIRED` als Empfehlung tritt nur bei >= 2 Flags auf.
Bei 1 Flag: `requires_human_review`-Property ist True, Hauptempfehlung
spiegelt das AI/Automation-Signal. Begruendung: 1 Flag ist ein
Warnsignal, kein vollstaendiger Review-Blocker.

**3. `BORDERLINE` als expliziter Phase-C-Hook.**
Gleichstand oder keine Signale werden nicht durch weitere Heuristiken
aufgeloest. `BORDERLINE` ist der definierte Uebergabepunkt an die
LLM-Analyse in Phase C. Kein Code-Workaround fuer Grenzfaelle in Phase A.

**4. Signal-Schwellen als Modul-Konstanten, nicht in Config.**
`_SIMPLE_TASK_MAX_COMPLEXITY`, `_HIGH_VOLUME_MIN_ANNUAL` etc. sind
Methodik-Parameter (definieren was "einfach" und "hohes Volumen"
bedeutet), keine firmenspezifischen Geschaeftswerte. Sie gehoeren zum
generisch zeigbaren Code (vertraglich bedingte IP-Trennung). Aenderung erfordert bewussten
Code-Commit, nicht Config-Edit - das ist gewollt.

---

## Konsequenzen

**Positiv:**
- Verhindert falsche AI-Empfehlungen fuer reine Automatisierungsfaelle.
- Klarer Extension-Point fuer Phase-C-LLM (BORDERLINE-Cases).
- `risk_flags` fliessen in den Report ein - Datenschutz-Hinweise ohne LLM.
- `requires_human_review`-Property vereinfacht Downstream-Logic im
  Application Service.

**Einschraenkungen:**
- Regelbasiert: ungewoehnliche Signal-Kombinationen koennen falsch
  eingestuft werden. BORDERLINE faengt die Worst-Cases ab.
- Freitext (`current_state`, `desired_state`) wird inhaltlich nicht
  analysiert - nur Laenge als Proxy. Phase C verbessert das durch
  LLM-Analyse der BORDERLINE-Cases.
- Schwellen sind nicht empirisch kalibriert. Kalibrierung in Phase E.

---

## Verworfene Alternativen

**Keyword-Matching auf Freitext:** Zu fragil fuer Produktionsqualitaet.
Freitext-Analyse gehoert in Phase C (LLM-Layer), nicht Phase A.

**Nur 2 Ausgaben (AI / Automation) ohne BORDERLINE:** Erzwingt eine
Entscheidung bei unklaren Faellen. Ein falsches Routing ist schlechter
als ein ehrliches "unklar".

**Konfigurierbare Signal-Schwellen:** Verworfen zugunsten von
Modul-Konstanten (Methodik-Parameter-Argument, s.o.).
