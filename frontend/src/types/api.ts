// Abgeleitet aus: domain/types.py, domain/models.py,
// adapters/api/routes/triage.py, adapters/api/routes/cases.py
// Aenderungen hier muessen mit den Python-Schemas synchron bleiben.

export type EmployeeCategory = "junior" | "professional" | "senior" | "mixed";
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

// ---- Request ---------------------------------------------------------------

export interface UseCaseInput {
  // Stammdaten
  title: string; // 5-200
  submitter: string; // 1-100
  department: string; // 1-100
  // Ist / Soll / Beispiel
  current_state: string; // 30-2000
  desired_state: string; // 30-2000
  example_process: string; // 20-2000
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
  estimated_license_cost_eur: number; // 0 - 10000000
  implementation_complexity: number; // integer 1-5
  // Datenschutz
  contains_pii: boolean;
  data_classification: DataClassification;
  // Handlungsdruck
  regulatory_pressure: boolean;
  competitive_pressure: boolean;
  strategic_priority: boolean;
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

export interface CaseSummary {
  id: string;
  submitted_at: string;
  title: string;
}
