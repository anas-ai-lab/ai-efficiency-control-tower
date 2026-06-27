# AECT Roadmap v2 -- Luecken, Markt, Opportunitaeten

> **Status: Analyse, kein Commitment.** Phase G auditiert und plant. Dieses
> Dokument identifiziert Optionen -- es committet KEINEN Pivot und KEINEN
> Feature-Build. Jeder echte Produkt-Pfad braucht einen eigenen
> Entscheidungs-Record (ADR/SDR), bevor Code entsteht.
>
> **Zweck:** Markt- und Produktdenken als Interview-Asset fuer
> Solution-Architect-Rollen. NICHT die Vorbereitung eines Startups. AECT bleibt
> ein privates Portfolio-Projekt (interne Referenz (entfernt) SS1).
>
> Stand: G-S7, Tag 82 (2026-06-27).

---

## 1. Funktionale Luecken (was ein realer Intake braeuchte)

| # | Luecke | Beschreibung | Verankert in |
|---|---|---|---|
| L-1 | **Portfolio-/Fleet-View** | AECT bewertet einen Case isoliert. Es gibt keine Quervergleichs-, Ranking- oder Dashboard-Ansicht ueber alle Cases. Genau das ist die Funktion, die der Name "Control Tower" verspricht -- ein Tower ueberblickt eine Flotte, nicht ein Flugzeug. | Neu (G-S7) |
| L-2 | **Feedback-Loop / praediktive Validitaet** | Kein Plan-vs-Actual-Abgleich: realisiert der Use Case den prognostizierten Nutzen? | known_limitations #1 |
| L-3 | **Dedup aehnlicher Antraege** | Zwei fast identische Einreichungen werden unabhaengig bewertet; keine Aehnlichkeitserkennung beim Intake. | Neu (G-S7) |
| L-4 | **KB-Abdeckung + Staleness** | KB deckt nur DSGVO Art. 35 + EU AI Act Art. 50. Kein Staleness-Alert nach Rechtsaenderungen. | known_limitations #5, G-007 |
| L-5 | **Kontinuierlicher Score statt harter Zonen** | Hard-Threshold-Brittleness an Zonengrenzen. | known_limitations #2, G-015 |
| L-6 | **Einsprachig (DE)** | Kein i18n; UI und Prompts nur Deutsch. | Neu (G-S7) |
| L-7 | **Kein Batch-Intake / keine Analytics** | Kein CSV-Import mehrerer Cases, kein aggregiertes Reporting. | Neu (G-S7) |

Die staerkste Luecke ist L-1: Sie schliesst die Distanz zwischen Name und
Funktion und baut direkt auf der vorhandenen Pro-Case-Rigorositaet auf
(Multi-Kriterien-Ranking ueber bestehende ROI-/Zonen-/Routing-Ergebnisse).

---

## 2. Markt- und Wettbewerbs-Findings (belegt)

Der Markt 2026 zerfaellt in vier Kategorien: GRC-Automation, Enterprise-AI-
Governance (Portfolio-Inventar + Assessments), LLM-Observability und
Runtime-Control-Plane [1]. Ab 2. August 2026 muessen High-Risk-AI-Systeme
kontinuierliche, strukturierte Compliance-Evidenz liefern -- keine
Policy-Dokumente [1].

**Schwergewichte (System-of-Record):**
- Microsoft Purview / Agent 365 als unified Control Plane ueber alle Agents,
  auch Drittplattformen (SAP, ServiceNow, Workday) [2].
- ServiceNow "AI Control Tower", integriert mit Microsoft Foundry/Copilot
  Studio fuer Agent-Oversight [2]. (Namensueberschneidung mit AECT -- ehrlich
  zu benennen; AECT ist kein Konkurrent, sondern ein Portfolio-Projekt.)
- Trustible: purpose-built AI-Governance-Plattform, "orchestrates AI use case
  intake, risk and impact assessments, regulatory compliance, vendor and model
  evaluations" [3] -- Intake ist hier ein Feature INNERHALB der schweren
  Governance-Suite.
- EQS Group (DACH): AI-Governance-Plattform fuer EU-AI-Act-Compliance [4].

**Leichtgewicht / Nicht-Software:**
- Use-Case-Priorisierung mit Feasibility + ROI als initialem Screen ist als
  Methodik etabliert (Wavestone, IBM, CIO, cigen) [5][6][7] -- aber meist als
  Consulting-Framework/Template geliefert, nicht als deterministisches Tool.

**Die Luecke:** Zwischen den schweren Enterprise-System-of-Record (zu gross/teuer
fuer den DACH-Mittelstand, der noch nicht bei "kontinuierlicher Evidenz" ist) und
den nicht-softwarebasierten Consulting-Frameworks liegt ein schmaler Streifen:
ein leichtgewichtiger, deterministischer Intake-/Triage-Layer, der UPSTREAM der
Governance sitzt und die Frage "Lohnt sich das ueberhaupt, und ist es AI oder
Automation?" beantwortet, bevor ein Case ueberhaupt in eine Governance-Plattform
wandert. Genau das ist AECTs konzeptuelle Position. Der DACH-/EU-AI-Act-Winkel
mit Mittelstands-Fokus ist softwareseitig duenn besetzt -- die meisten Tools
zielen auf Enterprise-GRC.

**Interview-Wert (nicht Startup-These):** AECT demonstriert, dass der Kandidat
die Marktkategorien kennt (GRC vs. Enterprise-Governance vs. Observability vs.
Runtime), die regulatorische Zeitleiste (Aug 2026) und die architektonische
Differenzierung (deterministische Triage + Citations-before-LLM) artikulieren
kann. Das ist Solution-Architect-Denken, kein Produkt-Anspruch.

---

## 3. Opportunity-Scoring

Skala 1-5, hoeher = attraktiver fuer das Portfolio-Ziel. Achsen:
**PT** Portfolio-Tiefe · **AG** Aufwand-Guenstigkeit (5 = billig zu bauen) ·
**DI** Differenzierung · **MR** Markt-/Interview-Relevanz ·
**IP** IP-Sicherheit (5 = sicher zeigbar, fern der realer Firmenkontext).

| Option | PT | AG | DI | MR | IP | Summe |
|---|---|---|---|---|---|---|
| L-1 Portfolio-/Fleet-View | 5 | 3 | 5 | 5 | 4 | **22** |
| L-5 Kontinuierlicher Score (Fuzzy-Zonen) | 4 | 4 | 4 | 4 | 5 | **21** |
| L-3 Dedup (Embedding-Similarity Intake) | 4 | 4 | 3 | 3 | 5 | **19** |
| L-4 KB-Erweiterung + Staleness-Alert | 3 | 4 | 3 | 4 | 5 | **19** |
| L-2 Feedback-Loop praediktive Validitaet | 5 | 2 | 4 | 5 | 3 | **19** |
| Ideation-Modul (v2-Backlog #1) | 3 | 3 | 2 | 3 | 4 | **15** |
| L-6 i18n (EN) | 1 | 3 | 1 | 3 | 5 | **13** |
| L-7 Batch-Intake / Analytics | 2 | 3 | 2 | 2 | 4 | **13** |

Begruendungs-Schlaglichter:
- **L-1** fuehrt, weil es Name und Funktion zusammenbringt, hohe Differenzierung
  hat (Multi-Kriterien-Portfolio-Ranking ist sichtbar anspruchsvoll) und direkt
  auf bestehenden Ergebnissen aufbaut. AG nur 3, weil eine Vergleichs-/Ranking-UI
  plus Aggregations-Endpoint echter Build ist. IP 4: Ranking-Methodik ist
  generisch, firmenspezifische Gewichte bleiben in config/.
- **L-5** ist hoch, weil es eine real dokumentierte Schwaeche (Hard-Threshold)
  adressiert, rein in der Domain-Schicht lebt (gut testbar, kein I/O), und
  vollstaendig generisch ist (IP 5).
- **L-2** hat hoechste Tiefe/Relevanz, aber AG 2 (braucht Produktiv-Loop, real
  schwer im privaten Build) und IP 3 (Plan-vs-Actual-Daten naehern sich der
  realen Firmendaten).

---

## 4. Top-Empfehlung (2-3)

1. **L-1 Portfolio-/Fleet-View** -- der kohaerenteste naechste Schritt. Erfuellt
   das Namensversprechen, hoechste Differenzierung und Interview-Relevanz.
2. **L-5 Kontinuierlicher Score / Fuzzy-Zonen** -- billigster hoher Hebel, rein
   Domain, adressiert eine benannte Schwaeche, vollstaendig zeigbar.
3. **L-3 Dedup via Embedding-Similarity** -- nutzt die vorhandene RAG-Infra
   (Embedder ist schon da), generisch, mittlerer Aufwand.

Diese drei zusammen ergaeben ein kohaerentes "v2-Narrativ": von der
Einzelfall-Triage zum Portfolio-Ueberblick mit robusteren Scores und
Eingangs-Dedup -- ohne den Charakter (deterministisch, advisory, EU-fokussiert)
zu verlassen.

---

## 5. Ideation-Modul -- Re-Evaluierung nach Vollaudit

Das Ideation-Modul war v2-Backlog #1. Nach dem Vollaudit ist es NICHT mehr der
beste naechste Schritt. Begruendung: AECTs Staerke ist das rigorose BEWERTEN von
Eingaben (deterministisch, belegt, advisory). Ein Ideation-Modul wuerde mehr
Eingaben GENERIEREN -- es zieht in die entgegengesetzte Richtung und konkurriert
mit generischen LLM-Brainstorming-Tools, wo AECT keine Differenzierung hat
(DI 2). Die Portfolio-View (L-1) hebelt dagegen genau die vorhandene Rigorositaet.
Empfehlung: Ideation-Modul von "v2-Backlog #1" auf "spaeter / niedrige Prioritaet"
herabstufen.

---

## 6. Benoetigt eigenen Entscheidungs-Record (kein Phase-G-Commitment)

Jede der folgenden Optionen ist ein Produkt-/Architektur-Schritt, der vor dem
Bau einen eigenen Record braucht -- Phase G baut nichts davon:

- **L-1 Portfolio-View** -> braucht ADR (Aggregations-Port, Ranking-Algorithmus,
  UI-Architektur) + ggf. SDR (aendert den Produkt-Charakter Richtung Dashboard).
- **L-5 Fuzzy-Zonen** -> braucht ADR (Score-Modell-Aenderung, Migration der
  Zonen-Semantik, Eval-Auswirkung auf golden-001/003).
- **L-3 Dedup** -> braucht ADR (Similarity-Schwelle, False-Positive-Umgang,
  Intake-Flow-Aenderung).
- **L-2 Feedback-Loop** -> braucht SDR (Produktiv-Loop noetig -> verlaesst
  "privates Build", IP-Klaerung-relevant) + ADR.
- **Jeder Pivot Richtung Produkt/SaaS** -> SDR-Update (widerspricht interne Referenz (entfernt) SS1
  in der heutigen Fassung).

---

## Quellen

[1] [Best EU AI Act Compliance Software 2026 (Kategorien) -- kla.digital](https://kla.digital/blog/best-eu-ai-act-compliance-software-2026)
[2] [ServiceNow + Microsoft: AI governance & orchestration -- diginomica](https://diginomica.com/servicenow-and-microsoft-bet-ai-governance-and-orchestration-path-enterprise-platform-value)
[3] [Best AI Governance Tools 2026 (Trustible) -- aigovernancedesk.com](https://aigovernancedesk.com/best-ai-governance-tools/)
[4] [AI governance platform for EU AI Act compliance -- EQS Group](https://www.eqs.com/platform-data-privacy/ai-compliance/)
[5] [What AI use cases must be prioritized to drive ROI -- Wavestone](https://www.wavestone.com/en/insight/what-ai-use-cases-must-be-prioritized-to-drive-clear-and-significant-roi/)
[6] [How to maximize AI ROI in 2026 -- IBM](https://www.ibm.com/think/insights/ai-roi)
[7] [AI Use Case Prioritization: Practical Framework -- cigen](https://www.cigen.io/insights/ai-use-case-prioritization-the-critical-step-in-a-practical-ai-adoption-journey)
