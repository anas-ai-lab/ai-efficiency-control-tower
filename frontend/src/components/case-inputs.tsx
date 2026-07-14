import { getFormatter, getTranslations } from "next-intl/server"

import type { UseCaseInput } from "@/types/api"
import { bindFormat } from "@/lib/format"
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

export async function CaseInputs({
  eingaben: e,
  caseId,
  isAdmin = false,
}: {
  eingaben: UseCaseInput
  caseId: string
  isAdmin?: boolean
}) {
  const t = await getTranslations("caseInputs")
  const te = await getTranslations("enums")
  const fmt = bindFormat(await getFormatter())

  const druck =
    [
      e.regulatory_pressure && t("pressureRegulatory"),
      e.competitive_pressure && t("pressureCompetitive"),
      e.strategic_priority && t("pressureStrategic"),
    ]
      .filter(Boolean)
      .join(", ") || t("pressureNone")

  return (
    <section>
      <p className="eyebrow mb-3">{t("title")}</p>
      <p className="mb-4 max-w-prose text-xs leading-relaxed text-muted-foreground">
        {t("intro")}
      </p>

      <div className="divide-y divide-border rounded-xl border border-border bg-card py-1">
        <Group title={t("groupDescription")}>
          <Row label={t("rowTitle")} value={e.title} />
          <Row label={t("rowCurrentState")} value={e.current_state} />
          <Row label={t("rowDesiredState")} value={e.desired_state} />
          <Row label={t("rowExample")} value={e.example_process} />
          <Row label={t("rowDesiredExample")} value={e.desired_example_process ?? ""} />
        </Group>

        <Group title={t("groupMaster")}>
          <Row label={t("rowSubmitter")} value={e.submitter} />
          <Row label={t("rowDepartment")} value={e.department} />
          <Row label={t("rowCountry")} value={te(`country.${e.country}`)} />
          <Row
            label={t("rowEmployeeCategory")}
            value={te(`employeeCategory.${e.employee_category}`)}
          />
        </Group>

        <Group title={t("groupTime")}>
          <Row
            label={t("rowTimeCurrent")}
            value={`${e.time_per_case_hours_current} ${t("hoursUnit")}`}
          />
          <Row
            label={t("rowTimeAi")}
            value={`${e.time_per_case_hours_with_ai} ${t("hoursUnit")}`}
          />
          <Row
            label={t("rowOccurrences")}
            value={String(e.occurrences_per_employee_per_year)}
          />
          <Row
            label={t("rowEmployees")}
            value={String(e.affected_employees_count)}
          />
        </Group>

        <Group title={t("groupImpl")}>
          <ImplementationApproachEditor
            caseId={caseId}
            approach={e.implementation_approach}
            isAdmin={isAdmin}
          />
          <Row
            label={t("rowImplCost")}
            value={fmt.eur(e.implementation_cost_eur)}
          />
          <Row
            label={t("rowLicenseCost")}
            value={fmt.eur(e.estimated_license_cost_eur)}
          />
        </Group>

        <Group title={t("groupData")}>
          <Row
            label={t("rowDataClass")}
            value={te(`dataClassification.${e.data_classification}`)}
          />
          <Row
            label={t("rowPii")}
            value={e.contains_pii ? t("yes") : t("no")}
          />
          <Row
            label={t("rowAdoption")}
            value={te(`adoptionType.${e.adoption_type}`)}
          />
          <Row label={t("rowEvidence")} value={te(`evidenceLevel.${e.evidence_level}`)} />
          <Row label={t("rowPressure")} value={druck} />
        </Group>

        {e.notes && e.notes.length > 0 && (
          <Group title={t("groupNotes")}>
            <Row label={t("rowNotes")} value={e.notes} />
          </Group>
        )}
      </div>
    </section>
  )
}

export default CaseInputs
