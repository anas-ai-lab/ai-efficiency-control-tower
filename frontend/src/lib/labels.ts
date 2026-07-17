// Zentrale deutsche Label-Map fuer die kontrollierten Vokabular-Enums des
// UseCaseInput (V4-Modell). Einzige Quelle der deutschen Beschriftungen im UI --
// keine Enum-Rohwerte (z. B. "fixed_process_step") duerfen in Komponenten
// erscheinen. Die Enum-Werte selbst sind exakt aus src/types/api.ts gespiegelt
// (StrEnum.value aus domain/types.py); Reihenfolge = fachlich aufsteigend.

import type {
  AdoptionType,
  Country,
  DataClassification,
  EmployeeCategory,
  EvidenceLevel,
  ImplementationApproach,
} from "@/types/api"

// Ein Select-Eintrag: technischer Wert + angezeigtes deutsches Label.
export interface LabelOption<T extends string> {
  value: T
  label: string
}

// Hilfstyp: vollstaendige Zuordnung Enum-Wert -> deutsches Label.
type LabelMap<T extends string> = Record<T, string>

export const COUNTRY_LABELS: LabelMap<Country> = {
  de: "Deutschland",
  at: "Österreich",
  ch: "Schweiz",
  no: "Norwegen",
  gb: "Vereinigtes Königreich",
  es: "Spanien",
  it: "Italien",
  tr: "Türkei",
  ro: "Rumänien",
  pl: "Polen",
  eg: "Ägypten",
  in: "Indien",
}

export const EMPLOYEE_CATEGORY_LABELS: LabelMap<EmployeeCategory> = {
  junior: "Junior",
  professional: "Professional",
  consultant: "Consultant",
  senior: "Senior",
  management: "Management",
}

export const EVIDENCE_LEVEL_LABELS: LabelMap<EvidenceLevel> = {
  pure_estimate: "Schätzung",
  similar_project: "Analogieprojekt",
  tested_piloted: "Pilotiert / Gemessen",
}

// Verbindlichkeit der Nutzung (aufsteigend). V4: drei Stufen statt zwei.
export const ADOPTION_TYPE_LABELS: LabelMap<AdoptionType> = {
  voluntary: "Freiwillig",
  recommended_standard: "Empfohlener Standard",
  fixed_process_step: "Fester Prozessschritt",
}

// Geplanter Umsetzungsansatz (aufsteigende Komplexitaet 1-5, V4). Die
// Komplexitaet wird im Backend deterministisch aus dem Ansatz abgeleitet --
// es gibt kein separates Komplexitaets-Eingabefeld mehr.
export const IMPLEMENTATION_APPROACH_LABELS: LabelMap<ImplementationApproach> = {
  simple_integration: "Einfache Integration (Bestand)",
  development_on_existing: "Entwicklung auf Bestand",
  api_integration: "API-Anbindung (Bestand)",
  custom_development: "Eigenentwicklung",
  new_tool: "Einführung neues Tool",
}

export const DATA_CLASSIFICATION_LABELS: LabelMap<DataClassification> = {
  no_personal_data: "Keine personenbezogenen Daten",
  pseudonymous: "Pseudonymisiert",
  personal: "Personenbezogen",
  sensitive_personal: "Besondere Kategorien (Art. 9 DSGVO)",
}

// Geordnete Options-Listen fuer die <Select>-Felder. Reihenfolge = Reihenfolge
// der Label-Map-Definition (Object.entries erhaelt Einfuegereihenfolge fuer
// String-Keys). toOptions haelt Wert und Label an einer Stelle synchron.
function toOptions<T extends string>(map: LabelMap<T>): LabelOption<T>[] {
  return (Object.entries(map) as [T, string][]).map(([value, label]) => ({
    value,
    label,
  }))
}

// Routing-Empfehlung (RoutingRecommendation.value) als deutsches Label. Das
// Backend liefert zusaetzlich recommendation_text als ganzen Satz (V4-P6) --
// diese Map traegt nur die kurze Badge-Beschriftung. Rohe Enum-Strings im UI
// sind ein Fehler; jede Anzeige laeuft ueber diese Map.
export const ROUTING_LABELS: Record<string, string> = {
  AI_RECOMMENDED: "KI empfohlen",
  AUTOMATION_RECOMMENDED: "Automatisierung empfohlen",
  HUMAN_REVIEW_REQUIRED: "Menschliche Prüfung",
  BORDERLINE: "Grenzfall",
}

// Routing-Konfidenz (routing.confidence, "HIGH" | "MEDIUM" | "LOW").
export const CONFIDENCE_LABELS: Record<string, string> = {
  HIGH: "Hoch",
  MEDIUM: "Mittel",
  LOW: "Niedrig",
}

export const COUNTRY_OPTIONS = toOptions(COUNTRY_LABELS)
export const EMPLOYEE_CATEGORY_OPTIONS = toOptions(EMPLOYEE_CATEGORY_LABELS)
export const EVIDENCE_LEVEL_OPTIONS = toOptions(EVIDENCE_LEVEL_LABELS)
export const ADOPTION_TYPE_OPTIONS = toOptions(ADOPTION_TYPE_LABELS)
export const IMPLEMENTATION_APPROACH_OPTIONS = toOptions(
  IMPLEMENTATION_APPROACH_LABELS,
)
export const DATA_CLASSIFICATION_OPTIONS = toOptions(DATA_CLASSIFICATION_LABELS)
