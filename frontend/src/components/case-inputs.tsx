import type { UseCaseInput } from "@/types/api"
import {
  ADOPTION_TYPE_LABELS,
  COUNTRY_LABELS,
  DATA_CLASSIFICATION_LABELS,
  EMPLOYEE_CATEGORY_LABELS,
  EVIDENCE_LEVEL_LABELS,
} from "@/lib/labels"
import { formatEUR } from "@/lib/formatters"
import { ImplementationApproachEditor } from "@/components/implementation-approach-editor"

// Rohe Eingaben des Einreichers (UseCaseInput) read-only auf der Fall-
// Detailseite. Erklaerbarkeit: sichtbar machen, auf welchen Daten die Bewertung
// beruht. Alle Enum-Anzeigen laufen ueber die zentrale Label-Map -- nie ein
// roher Enum-Wert im UI. Server-sichere Praesentationskomponente (kein State).

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-1 gap-0.5 py-2 sm:grid-cols-[13rem_1fr] sm:gap-4">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm whitespace-pre-wrap text-foreground/90">
        {value.length > 0 ? value : "—"}
      </dd>
    </div>
  )
}

function Group({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="px-5">
      <p className="eyebrow border-b border-border py-3">{title}</p>
      <dl className="divide-y divide-border/60">{children}</dl>
    </div>
  )
}

function druckLabel(e: UseCaseInput): string {
  const parts = [
    e.regulatory_pressure && "Regulatorisch",
    e.competitive_pressure && "Wettbewerb",
    e.strategic_priority && "Strategisch",
  ].filter(Boolean)
  return parts.length > 0 ? parts.join(", ") : "keiner"
}

export function CaseInputs({
  eingaben: e,
  caseId,
  isAdmin = false,
}: {
  eingaben: UseCaseInput
  caseId: string
  isAdmin?: boolean
}) {
  return (
    <section>
      <p className="eyebrow mb-3">Erfasste Eingaben</p>
      <p className="mb-4 max-w-prose text-xs leading-relaxed text-muted-foreground">
        Die beim Einreichen erfassten Rohdaten — Grundlage der Bewertung. So ist
        nachvollziehbar, worauf Zone, Nutzen und Aufwand beruhen.
      </p>

      <div className="divide-y divide-border rounded-xl border border-border bg-card py-1">
        <Group title="Beschreibung">
          <Row label="Titel" value={e.title} />
          <Row label="Ist-Zustand" value={e.current_state} />
          <Row label="Soll-Zustand" value={e.desired_state} />
          <Row label="Beispiel (Ist)" value={e.example_process} />
          <Row label="Beispiel (Soll)" value={e.desired_example_process ?? ""} />
        </Group>

        <Group title="Stammdaten">
          <Row label="Einreicher" value={e.submitter} />
          <Row label="Abteilung" value={e.department} />
          <Row label="Land" value={COUNTRY_LABELS[e.country]} />
          <Row
            label="Mitarbeiterlevel"
            value={EMPLOYEE_CATEGORY_LABELS[e.employee_category]}
          />
        </Group>

        <Group title="Zeit & Häufigkeit">
          <Row
            label="Zeit / Vorgang heute"
            value={`${e.time_per_case_hours_current} Std.`}
          />
          <Row
            label="Zeit / Vorgang mit AI"
            value={`${e.time_per_case_hours_with_ai} Std.`}
          />
          <Row
            label="Vorgänge / Mitarbeiter / Jahr"
            value={String(e.occurrences_per_employee_per_year)}
          />
          <Row
            label="Betroffene Mitarbeiter"
            value={String(e.affected_employees_count)}
          />
        </Group>

        <Group title="Umsetzung">
          <ImplementationApproachEditor
            caseId={caseId}
            approach={e.implementation_approach}
            isAdmin={isAdmin}
          />
          <Row
            label="Implementierungskosten"
            value={formatEUR(e.implementation_cost_eur)}
          />
          <Row
            label="Lizenzkosten / Jahr"
            value={formatEUR(e.estimated_license_cost_eur)}
          />
        </Group>

        <Group title="Daten & Verbindlichkeit">
          <Row
            label="Datenschutzklasse"
            value={DATA_CLASSIFICATION_LABELS[e.data_classification]}
          />
          <Row
            label="Personenbezogene Daten"
            value={e.contains_pii ? "Ja" : "Nein"}
          />
          <Row
            label="Verbindlichkeit"
            value={ADOPTION_TYPE_LABELS[e.adoption_type]}
          />
          <Row label="Evidenzlevel" value={EVIDENCE_LEVEL_LABELS[e.evidence_level]} />
          <Row label="Handlungsdruck" value={druckLabel(e)} />
        </Group>

        {e.notes && e.notes.length > 0 && (
          <Group title="Anmerkungen">
            <Row label="Anmerkungen" value={e.notes} />
          </Group>
        )}
      </div>
    </section>
  )
}

export default CaseInputs
