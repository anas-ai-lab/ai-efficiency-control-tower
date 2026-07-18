# AECT Frontend -- Claude Code Kontext

## Projekt
AI Efficiency Control Tower (AECT) -- Weboberflaechenmodul fuer internen
Use-Case-Intake und KI-Triage. Privates Portfolio-Projekt, kein SaaS.

## Tech Stack
- Next.js 16 (App Router, TypeScript, Turbopack als Default-Bundler)
- Tailwind CSS v4 + shadcn/ui (new-york Style, Zinc-Basis)
- react-hook-form + zod fuer Client-seitige Formular-Validierung
- motion (Framer Motion, v12): NUR nav-tile.tsx (Feder-Hover + Cursor-Tilt/
  Spotlight-Motion-Values), stat-card.tsx (Count-up + Cursor-Tilt/Spotlight),
  pipeline-strip.tsx (Parallax + Legend-Cycle, useState/useEffect ohne
  motion-Lib). Alles andere bleibt CSS. Der Blatt-Effekt beim Seitenwechsel
  laeuft NICHT ueber motion, sondern ueber ein eigenes Canvas
  (leaf-transition.tsx).

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
Redaktionell entsaettigte Semantik ueber --zone-*-Tokens in globals.css,
KEINE Tailwind-*-100/800-Alarmfarben mehr. ZONE_CONFIG liefert je Zone:
labelDE, dot, text, surface, bar (literale Klassenstrings auf die Tokens).
LIKELY_WIN      -> gedaempftes Gruen  (--zone-win-*)
CALCULATED_RISK -> gedaempftes Bernstein (--zone-risk-*)
MARGINAL_GAIN   -> gedaempftes Rot    (--zone-gain-*)

## Design-System (Redesign v2, ab Premium-UI-Pass)
- Theme: HELL als Default, dunkel via .dark-Klasse auf <html>. Toggle:
  components/theme-toggle.tsx (client-only, localStorage 'aect-theme', KEIN
  next-themes). No-FOUC-Init-Skript inline in layout.tsx (<head>).
- EIN Akzent: gedecktes Tinten-Blau --ink (+ --ink-hover/-foreground/-subtle).
  NUR fuer interaktive/aktive Elemente (Fokusring, aktiver Step, Links, Hover
  des Primaerbuttons). Primaeraktion selbst bleibt monochrome Tinte (--primary).
- VERBOTEN weiterhin: Lila/Violett-Verlaeufe, Gradient-Text, Emoji im UI,
  symmetrische 3-Spalten-Hero-Grids, generische Card+CardHeader+CardTitle auf
  jedem Block, Badge-Outline-als-Verdikt.
- Glassmorphism/Frosted-Blur: erlaubt NUR fuer den Sticky-Header
  (bg-background/75 + backdrop-blur-md). Kein generelles Card-/Panel-Muster.
- Farbige Box-Shadow-Bleeds: erlaubt NUR fuer die primaere Hero-CTA
  (color-mix mit --brand-primary). Keine Bleeds an anderen Buttons/Cards.
- Glow/Neon: erlaubt NUR im Pipeline-Visual (sehr geringe Deckkraft, radial,
  --brand-accent). Kein Glow sonst im UI.
- Design-Reset v4.3 (Chat-getrieben, Anas' Entscheidung): Indigo/Moss statt
  Navy/Blau/Gruen als Marken-Akzent, siehe globals.css --brand-*.
- Typografie traegt die Hierarchie: Manrope (Text) + Fraunces (nur H1/H2,
  optical-size Achse) + IBM Plex Mono (Zahlen). Gewechselt im Redesign v4.3.
- Hairlines statt Kaesten: --hairline (Trennung in der Flaeche), --hairline-rule
  (Trennung zwischen Flaechen), --hairline-accent (nur interaktiv, laeuft bei
  Hover/Fokus ein). Neue Trennlinien konsumieren diese Tokens, nicht border-border.
- Layout: grosszuegiger, intentionaler Weissraum auf 4px-Raster. Intake-Form
  nutzt zweispaltiges Editorial-Layout (links Meta, rechts Felder), keine Cards.
- VISUAL_DENSITY: 3 (war 4 -- Dichte-Constraints fuer das Redesign aufgehoben).
- MOTION_INTENSITY: 3. Step-Transitions .animate-view-enter (8px/150-250ms,
  ease-out, nie bouncy). .stagger fuer Kaskaden. LLM-Wartezeiten via
  components/llm-action.tsx (Progress + Skeleton statt blanker Spinner).
  ALLE Motion hinter prefers-reduced-motion (in globals.css gegated).
- EU-AI-Act-Art.-50-Disclaimer bleibt im Footer (layout.tsx) auf jeder View.
- Kein Marketing-Hero, kein "AI revolutioniert alles". Ton: ruhig, praezise.
- Fehler: inline am ausloesenden Element (destructive-Tokens), kein globaler Toast.

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
