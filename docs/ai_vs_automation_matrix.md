# AI vs. Automation Matrix
## AI Efficiency Control Tower — Schnellreferenz

**Version:** 2.0 | **Stand:** Mai 2026  
**Kontext:** IT-Beratungsunternehmen, DACH-Markt, erste AI-Governance-Initiative  
**Ergänzt:** `docs/ai-decision-framework.md`

---

## Executive Summary

> Für Internes Gremium und Management — Lesedauer: 90 Sekunden.

Unternehmen haben generative AI auf Probleme angewandt, die besser durch klassisches Machine Learning oder deterministische Automatisierung gelöst worden wären, und korrigieren das jetzt. 42% der Unternehmen haben AI-Initiativen 2025 abgebrochen — doppelt so viele wie 2024. 95% der Enterprise-AI-Piloten erreichten nie die Produktion.

Die Matrix beantwortet eine Frage: **Welcher Ansatz ist für diesen Use-Case-Typ der richtige — und warum?**

Kernaussagen:
- LLM ist nicht das Standardwerkzeug. Strukturierte Daten + klare Regeln → klassische Automatisierung.
- Classical ML ist die oft vergessene Mitte zwischen Regelengine und LLM.
- RAG ist nur sinnvoll wenn eine gute, aktuelle Wissensbasis existiert. Schlechte KB → schlechtere Outputs als ohne RAG.
- Human Review ist gesetzlich vorgeschrieben wenn Entscheidungen *rein automatisiert* und *rechtlich erheblich* für Personen sind (DSGVO Art. 22) — nicht bei jedem Personenbezug.
- EU AI Act klassifiziert HR/Recruiting-AI explizit als Hochrisiko. Kernpflichten ab August 2026.

---

## Verbesserte Matrix

> Legende: Strukturgrad H=Hoch / M=Mittel / N=Niedrig | Risiko N=Niedrig / M=Mittel / H=Hoch / K=Kritisch | Human Review —=Nicht nötig / E=Empfohlen / P=Pflicht

| Use Case Typ | Typische Inputs | Struktur | Determin. | Risiko | Personen-bezug | Wissens-basis | Empfohlener Ansatz | Human Review | Warum | Typische Red Flags |
|---|---|---|---|---|---|---|---|---|---|---|
| **Rechnungsextraktion (Standardformular)** | PDF mit festen Feldern, Einheitsformat | H | H | N | Nein | Nein | ✅ Klassische Automatisierung (PDF-Parser, OCR-Regex) | — | Feste Felder, keine Ambiguität, deterministisch. LLM wäre 10× teurer ohne Mehrwert. | LLM wegen „könnte auch Ausnahmen" — Ausnahmen separat behandeln |
| **Rechnungsextraktion (verschiedene Layouts)** | PDFs ohne einheitliches Format, verschiedene Lieferanten | M | M | N | Nein | Nein | 🤖 LLM mit Structured Outputs | E | Variabler Input, Feldpositionen unterschiedlich. LLM mit JSON-Schema-Output robust. | Kein Eval-Set vor Deployment; Output landet ohne Validierung im ERP |
| **Reporting / Aggregation** | Datenbankfelder, Zeitreihen, KPIs | H | H | N | Nein | Nein | ✅ SQL / BI (Power BI, Tableau) | — | Aggregation ist deterministisch und performant in SQL. AI fügt Fehlerquellen hinzu. | „KI-Dashboard" wo eine SQL-Query reicht |
| **Freitext-Klassifikation** | E-Mails, Tickets, Formulartexte | N | N | N | Nein | Nein | 🤖 LLM als Klassifikator | — | Kontextabhängig, keine feste Regel formulierbar. Bei >500 gelabelten Beispielen: Classical ML prüfen (günstiger). | LLM für Klassifikation wo einfaches Regelset oder ML reicht |
| **E-Mail-Routing / -Priorisierung** | Eingehende Kunden-E-Mails | N | N | N | Begrenzt | Nein | 🤖 LLM als Klassifikator (oder Classical ML wenn Labels vorhanden) | — | Kontext und Dringlichkeit variieren. Bei historischen Labels: Classical ML ausreichend und günstiger. | Automatisches Antworten ohne Human-in-the-Loop für Kundenkommunikation |
| **Ticketpriorisierung** | IT-Support-Tickets (Betreff + Beschreibung) | M | M | N | Nein | Nein | 🤖 LLM als Klassifikator | — | Freitext, variable Formulierungen, Kontext nötig. | Automatische Zuweisung zu Personen ohne Review bei hochkritischen Tickets |
| **Sentiment-Analyse (Kundenfeedback)** | NPS-Kommentare, Umfragen, Bewertungen | N | N | N | Begrenzt | Nein | 🤖 LLM (oder Classical ML bei >1.000 gelabelten Sätzen) | — | Stimmung ist kontextabhängig, keine Regel formulierbar. Mit Labels: Classical ML (BERT-Fine-Tuning) günstiger. | Sentiment-Score als einzige Entscheidungsgrundlage ohne Kontext |
| **Log-Anomalie-Erkennung** | JSON-Logs, Metriken, Zeitreihen (strukturiert) | H | N | M | Nein | Nein | 📊 Klassisches ML (Isolation Forest, LSTM) oder Regelbasiert | E | Strukturierte Zeitreihendaten → Statistical ML ist günstiger, schneller, erklärbarer als LLM. LLM auf strukturierten Logs ist Overkill. | LLM für Anomalie-Erkennung auf strukturierten Logs — falsche Werkzeugwahl |
| **Fraud Detection (Transaktionen)** | Transaktionsdaten, Beträge, Zeitstempel | H | N | H | Begrenzt | Nein | 📊 Klassisches ML (XGBoost, GNN) | P (bei Sperrung) | Strukturierte Daten, Echtzeit-Anforderung (<200ms), historische Labels vorhanden. LLM zu langsam. | LLM für Fraud Detection; automatische Kontosperrung ohne Review |
| **Compliance-Fragen** | Freitextfragen zu internen Policies | N | N | M | Nein | Intern | 🔍 LLM + RAG | E | Interne Policies als Quelle. Antwort muss auf aktuelle Dokumente basieren. Quellenangabe Pflicht. | RAG auf veralteter oder inkonsistenter Wissensbasis; keine Quellenangabe |
| **FAQ-Bot / internes Wissensportal** | Natürlichsprachige Mitarbeiter-Fragen | N | M | N | Nein | Intern | 🔍 LLM + RAG | — | Interne Doku als Quelle. Klarer Fallback nötig: „Ich bin nicht sicher — wende dich an HR." | Keine Fallback-Logik; KB nicht versioniert; veraltete Dokumente bleiben drin |
| **Vertragsanalyse / -prüfung** | Vertragstexte (PDF, Word), variabel | N | N | H | Teilweise | Tief | 🔍 LLM + RAG + Human Review | P | Juristisches Wissen + interne Standards nötig. Fehler haben Vertragskonsequenzen. Jurist prüft Empfehlung. | Vertragliche Entscheidungen rein automatisiert; keine Quellenangabe in Output |
| **Bewerbungsscreening / CV-Analyse** | Lebensläufe, Anschreiben, Freitext | N | N | K | Erheblich | Tief | 🔍 LLM + RAG + Human Review | **Pflicht (DSGVO Art. 22 + EU AI Act)** | EU AI Act Annex III: Hochrisiko. DSGVO Art. 22: rein automatisiertes Scoring mit Einladungsfolge = verbotene solely-automated decision. DPIA erforderlich. | Automatische Ablehnung ohne substanzielle menschliche Prüfung; kein Bias-Test; kein Audit-Log |
| **Mitarbeiterbefragung-Auswertung (anonym)** | Freitextantworten, aggregiert | N | N | M | Begrenzt | Nein | 🤖 LLM (Themen + Sentiment) | E | Themenextraktion aus Freitext. Wichtig: Anonymität sichern, keine Rückschlüsse auf Personen. | De-anonymisierung durch zu granulare Auswertung; Einzel-Auswertung statt Aggregation |
| **Onboarding Q&A (neue Mitarbeitende)** | Natürlichsprachige Fragen zu Prozessen | N | M | N | Nein | Intern | 🔍 LLM + RAG | — | Interne Handbücher als Quelle. Quellenangabe immer. KB-Aktualität kritisch. | Veraltete KB-Dokumente; Sicherheitsrichtlinien werden falsch beantwortet |
| **RFP-Analyse / Angebotsunterstützung** | PDFs von Ausschreibungen, variabel | N | N | M | Nein | Tief | 🔍 LLM + RAG + Tool Use | E | Interne Referenzprojekte + Kompetenzprofile als KB. Tool Use für CRM-Lookup. Finale Entscheidung: Mensch. | Automatische Go/No-Go ohne menschliche Überprüfung bei >€50k-Projekten |
| **Meeting-Zusammenfassung / Protokoll** | Audio-Transkript oder Text | N | N | N | Begrenzt | Nein | 🤖 LLM | E | Zusammenfassung variabel, Kontext nötig. Protokoll immer von Teilnehmer freizugeben. | Automatische Verteilung ohne menschliche Freigabe; vertrauliche Inhalte in externe Modelle |
| **Code-Generierung / -Review** | Code, Anforderungen in Freitext | N | N | M | Nein | Nein | 🤖 LLM | E (Security) | Etablierter Standard. Security Review bei generiertem Code der in Produktion geht. OWASP: LLM-generierter Code kann Sicherheitslücken enthalten. | Generierter Code ohne Review in Produktion; kein Static-Code-Analysis danach |
| **Datenbankabfrage / CRUD** | Strukturierte Eingaben, feste Felder | H | H | N | Nein | Nein | ✅ Klassische Automatisierung (API, SQL) | — | Deterministisch, performant, günstig. AI bringt keinen Mehrwert. | LLM als „intelligente API" für einfache CRUD-Operationen |
| **Workflow-Automatisierung (RPA)** | Regelbasierte UI-Aktionen, Formulare | H | H | N | Nein | Nein | ✅ RPA / n8n / Workflow-Engine | — | Deterministisch, feste Schritte. LLM würde Zuverlässigkeit reduzieren. | RPA durch LLM Agent ersetzen ohne klaren Mehrwert |
| **Kreditentscheidung** | Finanzdaten, Scores, strukturiert | H | M | K | Erheblich | Nein | 📊 Klassisches ML + Human Review | **Pflicht** | EU AI Act: Credit scoring ist Hochrisiko. DSGVO Art. 22: erhebliche Auswirkung auf Person. Modell-Explainability (SHAP) Pflicht. | Rein automatisierte Ablehnung; kein Erklärungsrecht; kein Audit-Trail |
| **SAP-Daten-Transformation / ETL** | Strukturierte SAP-Exportdaten | H | H | M | Nein | Nein | ✅ Klassische Automatisierung (ETL, SAP APIs) | — | Deterministisch, performant. LLM für Datentransformation ist fehleranfälliger und teurer. | LLM-basierte Datenmigration ohne deterministische Validierungsregeln |
| **Angebotserstellung (komplex)** | Kundenanforderungen, Preismodelle, Referenzen | N | N | H | Nein | Tief | 🤖 AI Agent mit Human Approval | **Pflicht** | Mehrstufig: Research → Entwurf → Kalkulation → Review. Agent entwirft, Mensch genehmigt. Fehlentscheidung hat Vertragsfolgen. | Agent sendet Angebote ohne menschliche Freigabe |

---

## Entscheidungslogik

```
Schritt 1: Inputs vollständig strukturiert UND Logik als Regel formulierbar?
  → Klassische Automatisierung / RPA / SQL/BI
  → Fertig. Kein LLM-Overhead nötig.

Schritt 2: Strukturierte Daten, Muster erkennbar, historische Labels vorhanden (>500)?
  → Klassisches ML (günstiger, deterministischer, erklärbarer als LLM)
  → Echtzeit-Anforderung < 200ms → Klassisch oder ML (LLM zu langsam)

Schritt 3: Unstrukturierter Text, kontextabhängige Logik?
  Wissensabhängigkeit = Nein → LLM (Klassifikator oder Generierung)
  Wissensabhängigkeit = Intern/Tief → LLM + RAG
    ⚠ Nur wenn KB aktuell, konsistent und versioniert ist.

Schritt 4: Mehrstufige Aufgabe, externe Tools, iterative Schritte?
  → LLM + Tool Use (Workflow Automation)
  Irreversible Aktionen (Senden, Buchen, Löschen) → Human Approval Gate zwingend

Schritt 5: Compliance-Overlay (unabhängig von Schritten 1–4)
  DSGVO Art. 22: rein automatisiert + erhebliche Wirkung auf Personen
    → Human Review substanziell Pflicht (kein Rubber-Stamping)
  EU AI Act Hochrisiko (HR, Recruiting, Kredit, kritische Infrastruktur)
    → Compliance Track: Bias-Tests, Audit-Log, Dokumentation, Human Oversight
  Fehlerkonsequenzen irreversibel
    → Human Review immer. Eval-Set vor Deployment zwingend.
```

---

## Wann AI definitiv nicht sinnvoll ist

| Situation | Warum | Besser |
|---|---|---|
| Inputs vollständig strukturiert, Logik als Regel formulierbar | AI fügt Kosten und Fehler hinzu | Regelengine, SQL, RPA |
| Historische Labels verfügbar, strukturierte Daten, Echtzeit-Anforderung | Classical ML ist günstiger, schneller, erklärbarer | XGBoost, Isolation Forest |
| Latenzanforderung < 200ms (Echtzeit) | LLM zu langsam, auch mit Caching | Klassische Algorithmen |
| Keine oder schlechte Wissensbasis | RAG auf schlechter KB = schlechtere Outputs als ohne RAG | KB zuerst aufbauen |
| Prozess nicht definiert oder dokumentiert | AI automatisiert Chaos | Prozess standardisieren |
| Kein messbarer Erfolgsmaßstab definiert | Qualität nicht prüfbar, Deployment nicht vertretbar | Eval-Set zuerst definieren |
| Output geht direkt ohne Validierung in Folgesystem | Fehler pflanzen sich im Downstream fort | Human-in-the-loop oder Validierungsregel |

---

## Typische Fehlentscheidungen (mit Realreferenzen)

| Fehlentscheidung | Was passiert in der Praxis | Besser |
|---|---|---|
| LLM für strukturierte PDF-Formulare (feste Felder) | Teurer, langsamer, gelegentlich falsch — OCR-Regex liefert 99,9% deterministisch | PDF-Parser + Regex |
| LLM für Log-Anomalie-Erkennung (strukturierte JSON-Logs) | Latenz zu hoch, Kosten zu hoch, Isolation Forest liefert besser bei Zeitreihen | Isolation Forest oder Regelbasiert |
| RAG auf veralteter SharePoint-Doku | Halluzinationen basieren auf falschen Quellen — schlimmer als kein RAG | KB zuerst bereinigen und versionieren |
| Agent mit autonomen Aktionen (E-Mail senden, SAP buchen) ohne Human Gate | Einmal deployed: schwer rückgängig zu machen. Erste falsche Buchung → Vertrauensverlust | Human Approval Gate einbauen |
| Fine-Tuning als erster Schritt | Teuer (Zeit + Kosten), selten nötig. Prompt Engineering + RAG löst 95% günstiger | Prompt Engineering zuerst, RAG zweiter Schritt |
| Bewerbungsscreening rein automatisiert | DSGVO Art. 22 + EU AI Act Hochrisiko — direkte Bußgeldgefahr ab August 2026 | Human Review substanziell |
| Bespoke Enterprise Tool für Aufgaben die ChatGPT löst | Ein $50.000-Vertragsanalyse-Tool, das intern genutzt werden soll, verliert gegen ChatGPT in der Nutzerzufriedenheit — Nutzer kehren zum generischen Tool zurück. | Use-Case-Spezifität prüfen: wirklich nötig? |
| LLM-Agent für Datenanalyse | LLM-basierte Agents für Datenanalyse funktionierten in Demos, nicht in Produktion — das Problem war nicht technisch, sondern fehlende Nutzernähe beim Bau. | Nutzer early einbinden, iterieren |

---

## Red Flags — sofort stoppen und prüfen

| Red Flag | Risiko |
|---|---|
| „Wir nutzen LLM, weil es moderner klingt als Regelengine" | Technologiewahl nicht begründet — Mehrkosten ohne Mehrwert |
| Kein Eval-Set definiert vor Deployment | Qualitätsversprechen ohne Nachweis |
| Output geht direkt ohne Validierung in SAP / ERP / CRM | Fehler pflanzen sich downstream fort |
| Human Review = „Chef schaut kurz drüber" | EDPB-Anforderung: Human Review muss substanziell und einflussnehmend sein, nicht Rubber-Stamping |
| Keine Quellenangabe in LLM-Ausgaben die Entscheidungsgrundlage sind | Nicht nachvollziehbar, nicht auditierbar |
| Automatische Aktionen (senden, buchen, löschen) ohne Approval Gate | Irreversibel — besonders kritisch bei Kundenkommunikation |
| KB wird nicht versioniert oder aktuell gehalten | Veraltete Antworten sind schlimmer als keine Antwort |
| Bewerbungsscreening: Ablehnung durch System ohne Jurist oder HR-Review | DSGVO Art. 22 + EU AI Act → direkte Haftungsrisiken |
| Kein Cost-Tracking bei LLM-Calls in Produktion | Budget unkontrollierbar, kein Signal für Routing |
| Genierierter Code geht ohne Review in Produktion | OWASP LLM Top 10: Insecure Code Generation — bekannte Risikokategorie |

---

## Beispielbewertungen: 8 realistische Use Cases

### 1. SAP-Buchungsexport → Excel-Report für Controller

**Ansatz:** Klassische Automatisierung (SAP API + Python)  
**Warum:** Vollständig strukturiert, deterministisch, kein Sprachverständnis nötig.  
**Fehler den man macht:** LLM-Agent der Reports „intelligenter" macht — nicht nötig.

---

### 2. IT-Tickets aus Confluence/Jira automatisch priorisieren

**Ansatz:** LLM als Klassifikator  
**Warum:** Freitext-Beschreibungen, Kontext variiert, Dringlichkeit nicht regelbasiert formulierbar.  
**Red Flag:** Automatische Zuweisung an Personen ohne Review bei Kritisch-Tickets.

---

### 3. Interne Policy-Fragen von Mitarbeitern (HR, IT-Richtlinien)

**Ansatz:** LLM + RAG  
**Warum:** Natürlichsprachige Fragen, Antwort aus internen Dokumenten.  
**Pflicht:** Quellenangabe, Fallback „Frage HR direkt", KB monatlich aktualisiert.

---

### 4. Bewerbungsscreening für offene Beraterstellen

**Ansatz:** LLM + RAG + Human Review (Pflicht)  
**Warum:** EU AI Act Hochrisiko, DSGVO Art. 22 bei automatisierter Bewerbungsablehnung.  
**Pflicht vor Deployment:** DPIA, Betriebsrat-Information, Bias-Tests, Audit-Log.

---

### 5. Transaktions-Anomalie-Erkennung im Buchhaltungssystem

**Ansatz:** Klassisches ML (Isolation Forest) oder Regelbasiert  
**Warum:** Strukturierte Finanzdaten, historische Anomalie-Labels verfügbar, Echtzeit-Anforderung.  
**Fehler den man macht:** LLM auf strukturierten Transaktionsdaten — 10× teurer, gleiche Ergebnisse.

---

### 6. Ausschreibungen (RFPs) auf Eignung prüfen

**Ansatz:** LLM + RAG  
**Warum:** Unstrukturierte PDFs, Eignung hängt von internen Kompetenzprofilen und Referenzprojekten ab.  
**Hinweis:** Finale Go/No-Go bleibt beim Account Manager.

---

### 7. Timesheet-Anomalien erkennen (falsche Projektbuchungen)

**Ansatz:** Klassische Automatisierung + Regelbasiert  
**Warum:** Vollständig strukturierte Daten (Projekt-ID, Datum, Stunden). Klare Regeln: Buchung nach Projektende, >24h/Tag.  
**Fehler den man macht:** LLM für strukturierte Validierungslogik einsetzen.

---

### 8. Angebotsdokument erstellen (komplex, mehrstufig)

**Ansatz:** LLM + RAG + Tool Use mit Human Approval  
**Warum:** Recherche (KB), Entwurf (LLM), Kalkulation (Tool), Freigabe (Mensch). Konsequenzen bei Fehler sind vertraglich.  
**Pflicht:** Jedes Angebot wird von einem Menschen vor Versand geprüft.

---

## Fragen zur weiteren Personalisierung

1. **SAP-Tiefe:** Welche SAP-Module sind im Einsatz (S/4HANA, SAP SuccessFactors, SAP Ariba)? Manche Use Cases (Rechnungs-Extraktion, Zeiterfassung) lassen sich direkt mit SAP-nativen Features lösen, bevor AI überhaupt in Frage kommt.

2. **Betriebsrat:** Gibt es einen Betriebsrat? Falls ja: Welche Use Cases sind bereits kommuniziert? EU AI Act Hochrisiko (HR, Monitoring) erfordert Konsultation vor Einführung.

3. **Dateninfrastruktur:** Wo leben interne Dokumente aktuell — SharePoint, Confluence, lokale Laufwerke? Das bestimmt RAG-Aufwand und KB-Qualität direkt.

4. **Kundenprojekte vs. intern:** Werden AI Use Cases nur intern evaluiert oder auch für Kundenprojekte empfohlen? Bei Letzterem ändert sich der Haftungsrahmen unter EU AI Act (Deployer vs. Provider-Rolle).

5. **Bestehende Automatisierungen:** Welche Automatisierungen gibt es bereits (n8n, Power Automate, SAP-Workflows)? Daraus ergibt sich, welche Use Cases wirklich neu sind und welche nur Optimierungen bestehender Workflows.

---

## Verweise

- [`docs/ai-decision-framework.md`](ai-decision-framework.md) — Scoring-Matrix + Decision Tree
- [`src/aect/domain/ai_vs_automation.py`](../src/aect/domain/ai_vs_automation.py) — Code-Implementierung (Woche 6)
- EU AI Act, Annex III — Hochrisiko-Kategorien
- DSGVO Art. 22 — Automated Decision Making Scope
- OWASP LLM Top 10 (2025) — Insecure Code Generation, Excessive Agency

---

## Was gegenüber v1 verbessert wurde

| Bereich | v1 | v2 |
|---|---|---|
| DSGVO Art. 22 | Falsch: jeder Personenbezug → Human Review | Korrekt: nur solely automated + legal/significant effects |
| EU AI Act | Nicht vorhanden | Recruiting, Kredit als explizit Hochrisiko markiert |
| Classical ML | Fehlte (Lücke zwischen Regeln und LLM) | Eigene Kategorie mit konkreten Use Cases |
| Fraud Detection | Falsch: LLM-Klassifikator | Korrekt: Classical ML (XGBoost) + Echtzeit-Constraint |
| Log-Anomalie | Unklar: „ML oder LLM" | Korrekt: ML/Regelbasiert, LLM ist falsche Werkzeugwahl |
| Kreditentscheidung | Zu simpel: „Klassisch + Human Review" | EU AI Act Hochrisiko, SHAP-Explainability erwähnt |
| Code-Review | „LLM — etablierter Standard" | Security Review Pflicht, OWASP-Referenz |
| Neue Use Cases | 15 generische | 22 Use Cases mit IT-Consulting-Kontext |
| Fehlentscheidungen | Nicht vorhanden | 8 konkrete Fehlentscheidungen mit Realreferenzen |
| Entscheidungslogik | GDPR-Fehler, keine ML-Stufe | 5-Schritte-Logik mit Compliance-Overlay |
