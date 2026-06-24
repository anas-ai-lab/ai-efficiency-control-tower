# AECT Frontend -- Claude Code Kontext

## Projekt
AI Efficiency Control Tower (AECT) -- Weboberflaechenmodul fuer internen
Use-Case-Intake und KI-Triage. Privates Portfolio-Projekt, kein SaaS.

## Tech Stack
- Next.js 15 (App Router, TypeScript)
- Tailwind CSS v4 + shadcn/ui (new-york Style, Zinc-Basis)
- react-hook-form + zod fuer Client-seitige Formular-Validierung
- KEINE Framer Motion in diesem Tag -- erst nach expliziter Anforderung

## Sicherheitsregel (NICHT BRECHEN)
- AECT_API_KEY liegt ausschliesslich in frontend/.env.local
- Kein NEXT_PUBLIC_ Prefix -- API-Key darf NIE im Browser-Bundle landen
- Alle API-Calls AUSSCHLIESSLICH ueber src/app/actions.ts (Server Actions)
- Kein fetch() mit X-API-Key-Header im Client-Code
- Kein console.log() mit Werten aus den API-Responses die PII enthalten koennten

## Backend-API
Base URL (Server-seitig): process.env.AECT_API_BASE_URL
Auth Header: X-API-Key: process.env.AECT_API_KEY
Typen: src/types/api.ts -- BEREITS ANGELEGT, niemals duplizieren
Server Actions: src/app/actions.ts -- BEREITS ANGELEGT, bei Bedarf erweitern

## Endpoints (Referenz)
POST /triage                        -> TriageResponse    (Status 201 neu / 200 Replay)
POST /cases/{id}/sharpen            -> SharpenedCaseResponse
POST /cases/{id}/propose-solution   -> SolutionProposalResponse
POST /cases/{id}/compliance-hints   -> ComplianceHintsResponse
POST /cases/{id}/report             -> ReportResponse
GET  /health                        -> { status, version } (kein API-Key)

## User Flow (genau so implementieren)
1. Intake-Formular (IntakeForm) -> Submit -> submitTriage() Server Action
2. Triage-Ergebnis (TriageResult) anzeigen: Zone gross, ROI-Karten, Routing
3. Button "Use Case schaerfen" -> sharpenCase() -> SharpenedView
4. Button "Loesungsvorschlag" -> proposeSolution() -> SolutionView
5. Button "Compliance-Pruefung" -> generateComplianceHints() -> ComplianceView
6. Button "Vollstaendiger Report" -> generateReport() -> ReportView (Tabs)

## Komponenten-Ziel
src/
  app/
    page.tsx              # Server Component: rendert <AectApp />
    actions.ts            # BEREITS ANGELEGT
  components/
    aect-app.tsx          # Client Component: haelt den gesamten App-State
    intake-form.tsx       # Client Component: Formular mit allen UseCaseInput-Feldern
    triage-result.tsx     # Triage-Ergebnis: Zone, ROI, Routing, Buttons
    sharpened-view.tsx    # Original vs. Geschaerft (2-Spalten-Grid)
    solution-view.tsx     # Proposal-Text-Anzeige
    compliance-view.tsx   # Hinweis-Text + Quellen aufklappbar (Accordion)
    report-view.tsx       # Tabs: Entscheider | Technisch
  types/
    api.ts                # BEREITS ANGELEGT
  lib/
    formatters.ts         # BEREITS ANGELEGT: formatEUR(), ZONE_CONFIG

## Zone-Farben (aus ZONE_CONFIG in formatters.ts)
LIKELY_WIN      -> gruen  (bg-green-100 text-green-800)
CALCULATED_RISK -> gelb   (bg-yellow-100 text-yellow-800)
MARGINAL_GAIN   -> rot    (bg-red-100 text-red-800)

## Design-Prinzipien
- UI-Sprache: Deutsch (alle Labels, Buttons, Ueberschriften, Fehlermeldungen)
- VISUAL_DENSITY: 4 (Enterprise-Intranet-Tool, kein Landing-Page-Weissraum)
- MOTION_INTENSITY: 2 (Loading-Spinner bei async Operationen -- das war es)
- Kein Hero-Section, kein Marketing-Text, kein "AI revolutioniert alles"
- Fehler: inline in der Naeheaes ausloesenden Elements, kein globaler Toast

## State-Modell in aect-app.tsx
type Step = "form" | "triage" | "sharpened" | "solution" | "compliance" | "report"
- currentStep: Step
- triageResult: TriageResponse | null
- sharpenedResult: SharpenedCaseResponse | null
- solutionResult: SolutionProposalResponse | null
- complianceResult: ComplianceHintsResponse | null
- reportResult: ReportResponse | null
- Jedes async Ergebnis hat eigenen isLoading-State und error: string | null

## Verbotene Muster
- Kein NEXT_PUBLIC_AECT_API_KEY
- Kein direktes fetch() im Browser
- Keine Demo-Daten hartkodiert im Code
- Kein useEffect fuer initiales Datenladen (Server Components verwenden)
- Keine Kommentare ueber fehlende Funktionen ("TODO: Compliance implementieren")
