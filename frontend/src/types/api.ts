// Abgeleitet aus: domain/types.py, domain/models.py,
// adapters/api/routes/triage.py, adapters/api/routes/cases.py
// Aenderungen hier muessen mit den Python-Schemas synchron bleiben.

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
export type AdoptionType = "mandatory" | "voluntary";
export type ImplementationApproach =
  | "standard_product"
  | "custom_build"
  | "vendor_solution";
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
  | "integrated"
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
  // Quantitativ
  time_savings_hours_per_case: number; // 0 < x <= 8
  frequency_per_year: number; // integer, 0 < x <= 1000000
  affected_employees_count: number; // integer, 0 < x <= 50000
  employee_category: EmployeeCategory;
  // Evidenz & Verbindlichkeit
  evidence_level: EvidenceLevel;
  adoption_type: AdoptionType;
  implementation_approach: ImplementationApproach;
  // Kosten
  estimated_license_cost_eur: number; // 0 - 10000000 (wiederkehrend, EUR/Jahr)
  implementation_complexity: number; // integer 1-5
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

// ---- Triage Response (/triage POST) ----------------------------------------

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
  usage_factor: number;
  evidence_factor: number;
  license_cost_annual_eur: number;
  passes_prefilter: boolean;
  prefilter_fail_reason: string | null;
}

export interface RoutingResult {
  recommendation: string;
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

export interface ZoneResult {
  base_zone: TriageZone;
  final_zone: TriageZone;
  handlungsdruck_elevated: boolean;
  reason: string;
  // Additiver Konfidenz-Score (ADR-0036): Abstand zur naechsten Zonengrenze.
  confidence_score: number; // 0.5 - 1.0
  confidence_label: string; // "hoch" | "mittel" | "niedrig"
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
  passed_vorfilter: boolean;
  is_actionable: boolean;
  vorfilter: VorfilterResult;
  routing: RoutingResult;
  feasibility: FeasibilityResult;
  roi: ROIResult | null;
  composite: CompositeResult | null;
  zone: ZoneResult | null;
  similarity_warning: SimilarityWarning | null;
}

// ---- Dedup / Similarity-Pairs (/cases/similarity-pairs GET, P9) ------------
// Aggregierte Dedup-View ueber alle Cases (ADR-0039). Gespiegelt aus
// api.generated.ts (SimilarityPairResponse / SimilarityPairsResponse).
// case_a/case_b sind deterministisch nach id sortiert (case_a_id < case_b_id).
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

// ---- Cases Responses (/cases/... POST) -------------------------------------

export interface SharpenedCaseResponse {
  case_id: string;
  original_title: string;
  original_current_state: string;
  original_desired_state: string;
  sharpened_title: string | null;
  sharpened_current_state: string | null;
  sharpened_desired_state: string | null;
  improvement_suggestions: string[];
  raw_text: string | null;
  prompt_version: string;
}

export interface SolutionProposalResponse {
  case_id: string;
  proposal_text: string;
  prompt_version: string;
}

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

export interface BusinessSummary {
  title: string;
  zone: string | null;
  is_actionable: boolean;
  recommendation: string;
  expected_benefit_eur: number | null;
  summary_text: string;
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
  proposal_text: string | null;
}

export interface ReportResponse {
  case_id: string;
  business_summary: BusinessSummary;
  technical_detail: TechnicalDetail;
}

// Portfolio-Read (P2): erweiterte Listansicht. zone/net_expected_benefit_eur/
// composite_total/hours_per_year sind null bei Vorfilter-Fail (gleiche
// None-Semantik wie TriageResponse). status ist immer ein CaseStatus-Wert
// (Backend liefert ihn als String, hier auf die Union verengt).
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
