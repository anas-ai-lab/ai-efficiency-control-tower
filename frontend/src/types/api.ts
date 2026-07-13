// Abgeleitet aus: domain/types.py, domain/models.py,
// adapters/api/routes/triage.py, adapters/api/routes/cases.py,
// adapters/api/routes/stats.py
// Aenderungen hier muessen mit den Python-Schemas synchron bleiben
// (Gegencheck: src/types/api.generated.ts aus openapi.json).

export type EmployeeCategory =
  | "junior"
  | "professional"
  | "consultant"
  | "senior"
  | "management";
// Land der betroffenen Mitarbeiter (steuert Stundensatz-Lookup im Backend).
// Werte exakt aus api.generated.ts (Country) gespiegelt.
export type Country =
  | "de"
  | "at"
  | "ch"
  | "no"
  | "gb"
  | "es"
  | "it"
  | "tr"
  | "ro"
  | "pl"
  | "eg"
  | "in";
export type EvidenceLevel =
  | "pure_estimate"
  | "similar_project"
  | "tested_piloted";
export type AdoptionType =
  | "voluntary"
  | "recommended_standard"
  | "fixed_process_step";
export type ImplementationApproach =
  | "simple_integration"
  | "development_on_existing"
  | "api_integration"
  | "custom_development"
  | "new_tool";
export type DataClassification =
  | "no_personal_data"
  | "pseudonymous"
  | "personal"
  | "sensitive_personal";
export type TriageZone =
  | "LIKELY_WIN"
  | "CALCULATED_RISK"
  | "MARGINAL_GAIN";
// Human-in-the-Loop Decision-Record (ADR-0043): PENDING ist der
// Ausgangszustand vor jeder manuellen Entscheidung, kein gueltiger
// Request-Wert fuer POST /cases/{id}/decision (nur approved/rejected).
export type ReviewerDecision = "pending" | "approved" | "rejected";

// Case-Lifecycle-Status (Lifecycle-ADR / P1). Werte exakt aus api.generated.ts
// (StatusUpdateRequest.status) gespiegelt. Keine Transitions-Matrix: jeder
// Zustand ist aus jedem setzbar (menschliche Autoritaet, Single-User-Build).
export type CaseStatus =
  | "submitted"
  | "in_review"
  | "approved"
  | "already_exists"
  | "rejected"
  | "implemented";

// ---- Request ---------------------------------------------------------------

export interface UseCaseInput {
  // Stammdaten
  title: string; // 5-200
  submitter: string; // 1-100
  department: string; // 1-100
  country: Country; // required, kein Default (steuert Stundensatz-Lookup)
  // Ist / Soll / Beispiel
  current_state: string; // 30-2000
  desired_state: string; // 30-2000
  example_process: string; // 20-2000 (Ist-Beispiel)
  desired_example_process?: string | null; // optional, max 2000 (Soll-Beispiel)
  // Quantitativ (V4: person-basierte Zeit-Semantik, SDR-0003)
  time_per_case_hours_current: number; // 0 < x <= 8 (Zeit/Vorgang heute)
  time_per_case_hours_with_ai: number; // 0 <= x <= 8 (Zeit/Vorgang mit AI)
  occurrences_per_employee_per_year: number; // integer, 0 < x <= 1000000 (pro MA)
  affected_employees_count: number; // integer, 0 < x <= 50000
  employee_category: EmployeeCategory;
  // Evidenz & Verbindlichkeit
  evidence_level: EvidenceLevel;
  adoption_type: AdoptionType;
  // Optional (V4.1, ADR-0050): ohne Ansatz landet der Case im Zustand
  // "Bewertung ausstehend"; ein Admin ergaenzt ihn spaeter. Komplexitaet 1-5
  // wird im Backend aus dem Ansatz abgeleitet.
  implementation_approach: ImplementationApproach | null;
  // Kosten
  estimated_license_cost_eur: number; // 0 - 10000000 (wiederkehrend, EUR/Jahr)
  implementation_cost_eur: number; // 0 - 10000000 (einmalig), default 0
  // Datenschutz
  contains_pii: boolean;
  data_classification: DataClassification;
  // Handlungsdruck
  regulatory_pressure: boolean;
  competitive_pressure: boolean;
  strategic_priority: boolean;
  // Anmerkungen
  notes?: string | null; // optional, max 2000
}

// ---- Triage Response (/triage POST, GET /cases/{id}.triage) ----------------

export interface VorfilterResult {
  passes: boolean;
  failed_criteria: string[];
  details: Record<string, boolean>;
}

export interface ROIResult {
  theoretical_potential_eur: number;
  expected_benefit_eur: number;
  net_expected_benefit_eur: number;
  hours_per_year: number;
  time_saved_per_case_hours: number; // Zeit_ist - Zeit_ai (auch <= 0 moeglich)
  usage_factor: number;
  evidence_factor: number;
  license_cost_annual_eur: number;
  passes_prefilter: boolean;
  prefilter_fail_reason: string | null;
}

export interface RoutingResult {
  recommendation: string;
  // Empfehlung als deutscher Satz (V4-P6) -- das Enum bleibt maschinenlesbar
  // daneben (recommendation).
  recommendation_text: string;
  confidence: string;
  automation_signals: string[];
  ai_signals: string[];
  risk_flags: string[];
  requires_human_review: boolean;
}

export interface FeasibilityResult {
  is_feasible: boolean;
  flags: string[];
  recommendation: string | null;
}

export interface CompositeResult {
  complexity_score: number;
  cost_score: number;
  data_protection_score: number;
  total: number;
  effort_label: string;
}

// Konfidenz als Begruendung statt Zahl (V4-P6): level + deterministische
// Gruende (Evidenzlage, Zonengrenz-Naehe mit Kipp-Hebel).
export interface ConfidenceReasoning {
  level: string; // "hoch" | "mittel" | "niedrig"
  gruende: string[];
}

export interface ZoneResult {
  base_zone: TriageZone;
  final_zone: TriageZone;
  handlungsdruck_elevated: boolean;
  reason: string;
  // Additiver Konfidenz-Score (ADR-0036): Abstand zur naechsten Zonengrenze.
  confidence_score: number; // 0.5 - 1.0
  confidence_label: string; // "hoch" | "mittel" | "niedrig"
  confidence_reasoning: ConfidenceReasoning; // V4-P6
}

// Eine Aufwandscore-Komponente mit deterministischer Begruendung (V4-P6).
export interface ScoreComponent {
  key: string;
  label: string;
  wert: number;
  max: number;
  begruendung: string;
}

// Herkunft des Aufwandscores (V4-P6): Komponenten + Gesamtzeile + Machbarkeit.
export interface ScoreBreakdown {
  components: ScoreComponent[];
  total: number;
  max_total: number;
  effort_label: string;
  total_line: string;
  feasibility_score: number; // = 10 - total
  feasibility_definition: string;
}

// Management-Ebene der Ergebnisdarstellung (V4.1-S5, Ebene 1): zwei Klartext-
// Saetze ohne interne Codes/Faktoren/Scores. null bei Vorfilter-Fail.
export interface ManagementView {
  zonen_satz: string;
  empfehlung_satz: string;
}

// Eine Zeile der Berechnungs-Ebene (V4.1-S5, Ebene 2, "Wie wurde das
// berechnet?"): Label, formatierter Wert, ein Satz Alltagssprache.
export interface BerechnungsZeile {
  label: string;
  wert: string;
  erklaerung: string;
}

// L-3 Dedup (ADR-0039): Hinweis auf einen aehnlichen, bereits erfassten Case.
export interface SimilarityWarning {
  similar_case_id: string;
  similar_case_title: string;
  similarity_score: number; // Cosinus [0, 1]
  suggest_combine: boolean; // true ab >= 0.90 ("zusammenlegen?")
}

export interface TriageResponse {
  id: string;
  submitted_at: string;
  title: string;
  // Vor-Bewertungs-Zustand (V4.1, ADR-0050): ohne Implementierungsansatz ist
  // der Case noch nicht bewertet -- vorfilter/routing/feasibility/roi/composite/
  // zone/score_breakdown sind dann alle null.
  evaluation_pending: boolean;
  passed_vorfilter: boolean;
  is_actionable: boolean;
  vorfilter: VorfilterResult | null;
  routing: RoutingResult | null;
  feasibility: FeasibilityResult | null;
  roi: ROIResult | null;
  composite: CompositeResult | null;
  zone: ZoneResult | null;
  // Score-Herkunft (V4-P6): None bei Vorfilter-Fail (kein Composite).
  score_breakdown: ScoreBreakdown | null;
  // Zweischichtige Ergebnisdarstellung (V4.1-S5): management = Ebene 1
  // (Klartext), berechnung = Ebene 2 (Herkunft je Komponente). null bei
  // Vorfilter-Fail.
  management?: ManagementView | null;
  berechnung?: BerechnungsZeile[] | null;
  similarity_warning?: SimilarityWarning | null;
}

// ---- Dedup / Similarity-Pairs (/cases/similarity-pairs GET, P9) ------------
export interface SimilarityPair {
  case_a_id: string;
  case_a_title: string;
  case_b_id: string;
  case_b_title: string;
  similarity_score: number; // Cosinus [0, 1], 4 Nachkommastellen
  suggest_combine: boolean; // true ab >= 0.90 ("zusammenlegen?")
}

export interface SimilarityPairsResponse {
  pairs: SimilarityPair[]; // absteigend nach score
  cases_without_embedding: number; // Cases ohne Embedding, fliessen nicht ein
}

// ---- Schaerfung (/cases/{id}/sharpen POST, V4 Draft/Accept-Flow) -----------

// Ein Verbesserungsvorschlag mit Feldbezug und Hebel (V4). bezugsfeld ist der
// CaseField.value, an dem das Frontend das Formularfeld verlinkt.
export interface SharpenSuggestion {
  bezugsfeld: string;
  vorschlag: string;
  hebel: string;
}

// Draft-Ergebnis: Original + geschaerfte Fassung. Der Client baut daraus die
// Diff-Ansicht und uebernimmt/verwirft via /sharpen/accept bzw. /reject. Alle
// sharpened_*-Felder sind bei Erfolg gesetzt (422 statt Teilantwort im Backend).
// S4: Schaerfung nur noch ueber die Soll-Felder (Soll-Zustand + Soll-Beispiel).
export interface SharpenedCaseResponse {
  case_id: string;
  original_desired_state: string;
  original_desired_example_process: string;
  sharpened_desired_state: string;
  sharpened_desired_example_process: string;
  improvement_suggestions: SharpenSuggestion[];
  prompt_version: string;
}

// Bestaetigung fuer accept/reject eines Schaerfungs-Drafts (V4).
export interface SharpeningActionResponse {
  case_id: string;
  status: string; // "accepted" | "rejected"
}

// Bestaetigung fuer accept/reject eines Loesungs-Drafts (S4).
export interface SolutionActionResponse {
  case_id: string;
  status: string; // "accepted" | "rejected"
}

// ---- Loesungsvorschlag (/cases/{id}/propose-solution POST, V4-P6) ----------
// Zweigeteilt: solution_business (technikfrei) + solution_technical.
export interface SolutionProposalResponse {
  case_id: string;
  solution_business: string;
  solution_technical: string;
  prompt_version: string;
}

// ---- Compliance-Hinweise (/cases/{id}/compliance-hints POST, ADR-0024) -----
export interface ComplianceCitation {
  number: number;
  source_id: string;
  citation: string;
  url: string | null;
}

export interface ComplianceHintsResponse {
  case_id: string;
  hint_text: string | null;
  citations: ComplianceCitation[];
  prompt_version: string;
}

// ---- Report (/cases/{id}/report POST, GET /cases/{id}.report, V4-P6) -------

// Aufwand als Kennzahl im Entscheider-Report: Wert von max mit Label.
export interface AufwandKennzahl {
  wert: number;
  max: number;
  label: string;
}

// Harte Kennzahlen des Entscheider-Reports (null bei Vorfilter-Fail).
export interface DecisionKennzahlen {
  netto_eur: number | null;
  stunden_pro_jahr: number | null;
  aufwand: AufwandKennzahl | null;
  zone_label: string | null;
}

// Ausklappbare Details des Entscheider-Reports.
export interface DecisionDetails {
  sharpened_text: string | null;
  solution_business: string | null;
  compliance_hint_text: string | null;
}

// Entscheider-Report v2 (V4-P6) -- ersetzt die alte summary_text-Zeile.
export interface DecisionReport {
  empfehlung_satz: string;
  kennzahlen: DecisionKennzahlen;
  zu_entscheiden: string;
  contra_punkte: string[];
  details: DecisionDetails;
}

// Technischer Report in Abschnitten statt Textwueste (V4-P6).
export interface TechnicalReport {
  architektur_kurzfassung: string;
  datenlage: string;
  risiken: string;
  offene_technische_fragen: string;
}

export interface BusinessSummary {
  title: string;
  zone: TriageZone | null;
  is_actionable: boolean;
  recommendation: string;
  expected_benefit_eur: number | null;
  decision_report: DecisionReport; // V4-P6
  solution_business: string | null; // V4-P6, null solange nicht erzeugt
  sharpened_text: string | null;
  compliance_hint_text: string | null;
  compliance_citations: ComplianceCitation[];
  // Human-in-the-Loop Decision-Record (ADR-0043)
  reviewer_decision: ReviewerDecision;
  reviewer_note: string | null;
  decided_at: string | null;
}

export interface TechnicalDetail {
  passed_vorfilter: boolean;
  vorfilter_failed_criteria: string[];
  composite_total: number | null;
  composite_effort_label: string | null;
  feasibility_flags: string[];
  feasibility_recommendation: string | null;
  automation_signals: string[];
  ai_signals: string[];
  risk_flags: string[];
  requires_human_review: boolean;
  roi_theoretical_potential_eur: number | null;
  roi_net_expected_benefit_eur: number | null;
  technical_report: TechnicalReport; // V4-P6
  proposal_text: string | null;
}

export interface ReportResponse {
  case_id: string;
  business_summary: BusinessSummary;
  technical_detail: TechnicalDetail;
}

// ---- Case-Detail (GET /cases/{id}, public read-only, E9/SDR-0003) ----------
// Read-only Bewertungsstand mit ABGESTUFTER Sichtbarkeit (V4-P7-Korrektur):
// eingaben (rohe Felder) sind immer da; triage + report liefert das Backend nur
// nach der Board-Entscheidung (ReviewerDecision != PENDING) -- oder wenn der
// Aufrufer selbst Admin ist. Davor sind beide null ("wird vom AI Board
// geprueft"). status ist stets ein CaseStatus-Wert (Backend liefert String,
// hier verengt).
export interface CaseDetailResponse {
  id: string;
  submitted_at: string;
  status: CaseStatus;
  // Vor-Bewertungs-Zustand (V4.1, ADR-0050): ohne Implementierungsansatz sind
  // triage/report immer null (auch fuer Admins). Ein Admin ergaenzt den Ansatz.
  evaluation_pending: boolean;
  eingaben: UseCaseInput;
  triage: TriageResponse | null;
  report: ReportResponse | null;
}

// Portfolio-Read (P2): erweiterte Listansicht. zone/net_expected_benefit_eur/
// composite_total/hours_per_year sind null bei Vorfilter-Fail (gleiche
// None-Semantik wie TriageResponse). feasibility_score = 10 - composite_total
// (V4-P6, null bei Vorfilter-Fail); feasibility_definition ist der zentrale
// Definitions-String.
export interface CaseSummary {
  id: string;
  submitted_at: string;
  title: string;
  department: string;
  status: CaseStatus;
  zone: TriageZone | null;
  net_expected_benefit_eur: number | null;
  composite_total: number | null;
  hours_per_year: number | null;
  is_actionable: boolean;
  // Vor-Bewertungs-Zustand (V4.1, ADR-0050): ohne Implementierungsansatz noch
  // nicht bewertet -- zone/composite/etc. sind dann null.
  evaluation_pending: boolean;
  feasibility_score: number | null;
  feasibility_definition: string;
  // V4-P7: False, wenn zone/net fuer diesen Aufrufer verborgen sind (anonym +
  // Board-Entscheidung ausstehend) -> "wird geprueft" statt "—" (das "—" bleibt
  // dem echten Vorfilter-Fail vorbehalten). Fuer Admins immer True.
  assessment_visible: boolean;
}

// ---- Decision Response (/cases/{id}/decision POST) -------------------------

export interface DecisionResponse {
  case_id: string;
  reviewer_decision: ReviewerDecision;
  reviewer_note: string | null;
  decided_at: string | null;
}

// ---- Lifecycle-Status (/cases/{id}/status POST, P1) ------------------------

export interface StatusUpdateRequest {
  status: CaseStatus;
}

export interface StatusUpdateResponse {
  case_id: string;
  status: CaseStatus;
  updated_at: string | null;
}

// ---- Monitoring-Zeitleiste (/cases/{id}/monitoring, P3) --------------------

// Append-only Eintrag. status_snapshot ist der Case-Status zum Zeitpunkt des
// Eintrags (Momentaufnahme, kein Live-Verweis) -- Backend liefert einen String,
// der stets ein CaseStatus-Wert ist, hier auf die Union verengt.
export interface MonitoringEntry {
  id: string;
  case_id: string;
  created_at: string;
  note: string;
  status_snapshot: CaseStatus;
}

export interface MonitoringNoteRequest {
  note: string;
}

// ---- Architektur-Skizze (/cases/{id}/architecture-sketch, P11, ADR-0049) ---
export type SketchNodeKind =
  | "user"
  | "system"
  | "ai_service"
  | "data_store"
  | "external";

export interface SketchNode {
  id: string;
  label: string;
  kind: string; // SketchNodeKind als String serialisiert (StrEnum.value)
}

export interface SketchEdge {
  source: string;
  target: string;
  label: string | null;
}

export interface ArchitectureSketchResponse {
  case_id: string;
  nodes: SketchNode[];
  edges: SketchEdge[];
  mermaid_source: string;
  generated_at: string; // ISO 8601, aendert sich bei jedem Regenerieren
  prompt_version: string;
}

// GET-Antwort: sketch ist null, wenn der Case existiert, aber nie eine Skizze
// erzeugt wurde (200 {"sketch": null}) -- unterschieden vom 404 (Case fehlt).
export interface ArchitectureSketchEnvelope {
  sketch: ArchitectureSketchResponse | null;
}

// ---- Ideation (/ideation POST, P10/P14, ADR-0048) --------------------------
// Ephemer (D16): kein Case, keine Persistenz. Die qualitativen Felder tragen
// exakt die UseCaseInput-Feldnamen (P14-Prefill). Quantitative Angaben werden
// bewusst NICHT erfunden (D17); die Luecken tragen die open_questions.
export interface IdeationDraft {
  title: string;
  current_state: string;
  desired_state: string;
  example_process: string;
  rationale: string;
  open_questions: string[];
}

export interface IdeationRequest {
  problem_description: string; // 20-2000
}

// flagged_input: true, wenn im Input ein Injection-Muster erkannt wurde
// (flag-not-block, D21) -- der Client sieht den Befund, die Antwort ist
// trotzdem valide (1-3 Entwuerfe).
export interface IdeationResponse {
  drafts: IdeationDraft[];
  flagged_input: boolean;
}

// ---- Portfolio-Kennzahlen (GET /stats, public, V4-P7) ----------------------
// Aggregierter Funnel fuer die Startseite. bewertet = Cases mit bestandenem
// Vorfilter; umgesetzt = Status implemented; netto_nutzen_freigegeben_eur =
// Summe Netto-Nutzen ueber approved + implemented.
export interface StatsResponse {
  eingereicht: number;
  bewertet: number;
  umgesetzt: number;
  netto_nutzen_freigegeben_eur: number;
}
