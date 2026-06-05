# ADR-0003: LLM-Strategie und Provider

**Status:** Accepted
**Datum:** 2026-06-05
**Autor:** Anas

## Kontext

AECT nutzt LLM für drei Aufgaben: Use-Case-Schärfung (Original + geschärfte Version),
Stack-Lösungsvorschlag, lesbarer zweischichtiger Report.

Offene Fragen: Welcher Provider? Wie wird EU-Datenresidenz für PII sichergestellt?
Wie werden Kosten kontrolliert? Wie verhält sich das System bei LLM-Ausfall?

Wichtiger Kontext: Das LLM ist eine Ergänzung, keine Voraussetzung. Die Regel-Triage
(ROI-Berechnung, Zonenbestimmung, AI-vs-Automation-Routing) läuft deterministisch ohne
LLM.

## Entscheidung

**1. Mock-First-Entwicklung:** Implementierung beginnt mit deterministischem Mock-LLM-Adapter
(Phase C). Kein echter Cloud-Call bis Mock-Tests vollständig grün.

**2. Provider (Produktion):** Azure OpenAI, EU Data Zone.
- Zulässige Regionen: `swedencentral` oder `westeurope`
- Unzulässig: Global/Worldwide Standard (kann außerhalb EU routen)

**3. Modell-Default:** `gpt-4o-mini`.
Für gezielte Qualitätstests: `gpt-4o` — nur mit Cost-Logging und Budget-Sentinel-Check.

**4. Provider-Abstraktion:** `LLMPort`-Interface (ADR-0002) macht den Provider austauschbar.

**5. Graceful Degradation:** Bei LLM-Ausfall → Regel-Triage-Ergebnis ohne LLM-Anreicherung
zurückgeben. Das System fällt nicht aus; es gibt weniger zurück.

**6. PII-Schutz:** Personenbezogene Daten werden vor dem LLM-Call redacted (Phase C/D).
Azure EU Data Zone und PII-Redaction sind beide notwendig — keine Alternative zueinander.

## Begründung

**Mock-First:** Echte LLM-Calls sind nicht-deterministisch und kosten Geld. Unit-Tests
müssen reproduzierbar sein. Der Mock-Adapter antwortet nach einer fixen Regel — nicht
per Zufall. Erst wenn Mock-Tests grün, wird der echte Azure-Adapter eingebunden.

**Azure OpenAI statt OpenAI Direct:** EU Data Zone garantiert, dass Daten nicht außerhalb
der EU verarbeitet werden. Microsoft DPA deckt Art. 28 DSGVO. Relevant sobald
Einreichungen PII enthalten können (Namen, Rollen, Kostenstellen, Projektnamen).

**EU Data Zone als Pflicht (nicht Option):** Global-Deployments können trotz EU-Standort
außerhalb EU routen. Für PII ist das ein DSGVO-Verstoß. Konservative Regel: immer
`swedencentral` oder `westeurope` — auch wenn im privaten Build noch kein PII aktiv
verarbeitet wird. Nachrüsten ist aufwändiger als von Anfang an richtig machen.

**gpt-4o-mini als Default:** Schärfung und Report-Formulierung liegen im
Kern-Kompetenzbereich von gpt-4o-mini. Ca. 10× günstiger als gpt-4o. Der Cost-Logger
in Phase C misst, ob die Qualität für den Anwendungsfall ausreicht.

| Alternative | Warum verworfen |
|---|---|
| OpenAI Direct | Keine EU-Data-Zone-Garantie für PII; DSGVO-Risiko bei personenbezogenen Einreichungen |
| Anthropic Claude API | US-basiert; weniger Enterprise-Integration im DACH-Azure-Stack |
| Lokale Modelle (Ollama/vLLM) | Ressourcenanforderungen unverhältnismäßig für Portfolio-Projekt; Latenz für Demo unakzeptabel |
| LangChain/LlamaIndex | Zusätzliche Abhängigkeit ohne Mehrwert; `LLMPort`-Interface leistet dasselbe projektspezifisch und ohne Framework-Lock-in |

## Konsequenzen

**Positiv:**
- EU-Compliance für PII ab Phase C ohne Nacharbeit
- Entwicklungskosten kontrollierbar: Mock-First + Cost-Logger + Budget-Sentinel
- Provider austauschbar ohne Domain-Änderung (ADR-0002)
- Demo ohne echte Credentials möglich (Mock-Adapter)

**Negativ / Trade-offs:**
- Azure-Setup-Overhead: Endpoint, Deployment-Name, Region, API-Key müssen in `.env`
  konfiguriert werden (Phase C, Environment Checker, Agent 4)
- Budget-Sentinel-Check vor jedem ersten echten Call erforderlich

**Security-Implikationen (OWASP LLM Top 10 2025):**
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_KEY` nur in
  `.env` — niemals committed. `BaseSettings` aus `pydantic-settings`.
- System-Prompt enthält keine Secrets, keine Auth-Logik, keine internen Endpoints
  (LLM07: System Prompt Leakage)
- LLM-Output immer als untrusted input behandeln; gegen striktes Pydantic-Schema
  validieren bevor Weiterverarbeitung (LLM05: Improper Output Handling)
- PII-Redaction vor dem LLM-Call, nicht erst danach (LLM02: Sensitive Info Disclosure)
