# ADR-0006: Prompt-Loader, Versionierung und Schaerfungs-Workflow

**Status:** Accepted
**Datum:** Juni 2026

## Kontext

Phase C (Master-Plan v3.1) braucht Use-Case-Schaerfung: Original-Eingabe
bleibt unveraendert sichtbar, daneben steht eine geschaerfte Version
(Projekt-Anforderung). Prompts muessen versioniert und vom Code getrennt
sein, damit sich Prompt-Iterationen nicht in Code-Deploys verstecken.

## Entscheidung

- Prompts liegen in `prompts/<name>/<version>/{system,user}.md`, geladen
  ueber `load_prompt(name, role, version="v1")`. Pfadauflösung analog
  `load_roi_config()` (`parents[3]` -> Repo-Root).
- Der User-Prompt trennt Nutzerdaten vom Instruktionstext per
  `<<<DATA>>>`/`<<<END_DATA>>>`-Delimiter (OWASP LLM01-Vorbereitung,
  aect-security-checklist v2.1 Phase C: Messages-API, kein String-Concat).
- `TriageService.sharpen_case(case_id, prompt_version="v1")` liefert
  `SharpenedUseCase` (Original-Felder + `sharpened_text` + `prompt_version`)
  oder `None`, wenn `case_id` nicht existiert -- die Route mapped das auf 404.
- `LLMPort` wird per Constructor-DI in `TriageService` injiziert (Pflicht-
  Parameter, kein Default), `get_llm_adapter()` liefert aktuell
  `MockLLMAdapter` (ADR-0005).

## Konsequenzen

- Prompt-Aenderungen brauchen eine neue Versionsdatei, kein Code-Deploy.
  `prompt_version` im Ergebnis macht nachvollziehbar, welche Version welches
  Ergebnis erzeugt hat.
- MockLLMAdapter liefert deterministisch den eingebetteten Prompt zurueck --
  die heutigen Tests pruefen das Wiring (Original-Felder kommen durch,
  Prompt wird korrekt zusammengebaut), nicht die Qualitaet einer echten
  Schaerfung.

## Offene Punkte (bewusst, nicht versteckt)

- **Output-Validation:** `sharpened_text` ist `str`. Ein striktes
  Pydantic-Schema fuer die LLM-Antwort (aect-security-checklist v2.1, Phase C:
  "LLM-Output gegen striktes Pydantic-Schema, als untrusted behandeln") wird
  eingefuehrt, sobald ein Provider strukturierte Antworten liefert -- das ist
  ein Breaking Change auf `SharpenedUseCase` und bewusst auf den
  Azure-Adapter-Tag verschoben.
- **LLM-Red-Team-Tests** (Injection-Payloads gegen den `<<<DATA>>>`-Delimiter)
  folgen, sobald ein Provider den Prompt-Inhalt tatsaechlich interpretiert.
  Gegen `MockLLMAdapter` (reines Echo) liefern solche Tests keinen
  Erkenntniswert.

## Addendum (ADR-0013 Teil 2, Juni 2026)

Output-Validation ist umgesetzt: SharpenedContentV2 (Pydantic, striktes
Schema) + parse_structured_llm_output() + Graceful Degradation bei
Schema-Verstoss. Dieser offene Punkt ist geschlossen.
