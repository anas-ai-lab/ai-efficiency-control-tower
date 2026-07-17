"use client"

import { useTranslations } from "next-intl"

import type { ManagementSolution, TechnicalSolution } from "@/types/api"

// Strukturierte Anzeige beider Loesungs-Ebenen (ADR-0054). Ersetzt den frueheren
// Fliesstext-Dump: Summary oben, darunter Stichpunkte als Liste.
//
// Geteilt zwischen dem Draft-Modal (solution-modal) und der Report-Ansicht
// (case-report) -- beide zeigen dieselbe Loesung, einmal vor und einmal nach dem
// Uebernehmen; sie duerfen nicht auseinanderlaufen.
//
// Legacy-Cases (vor ADR-0054, Klartext in der Spalte) liefern leere Listen. Jede
// Liste rendert dann gar nicht -- kein Abschnitt mit leerer Ueberschrift.

function Summary({ text }: { text: string }) {
  return (
    <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
      {text}
    </p>
  )
}

function BulletSection({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <section className="mt-4">
      <p className="eyebrow mb-2">{title}</p>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li
            key={i}
            className="flex gap-2 text-sm leading-relaxed text-foreground/90"
          >
            <span
              className="mt-1.5 size-1 shrink-0 rounded-full bg-[var(--ink)]"
              aria-hidden
            />
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}

export function ManagementSolutionView({
  solution,
}: {
  solution: ManagementSolution
}) {
  const t = useTranslations("solution")
  return (
    <div>
      <Summary text={solution.summary} />
      <BulletSection title={t("benefits")} items={solution.benefits} />
    </div>
  )
}

export function TechnicalSolutionView({
  solution,
}: {
  solution: TechnicalSolution
}) {
  const t = useTranslations("solution")
  return (
    <div>
      <Summary text={solution.architecture_summary} />
      <BulletSection title={t("components")} items={solution.components} />
      <BulletSection title={t("dataFlow")} items={solution.data_flow} />
      <BulletSection
        title={t("integrationPoints")}
        items={solution.integration_points}
      />
      <BulletSection
        title={t("openAssumptions")}
        items={solution.open_assumptions}
      />
    </div>
  )
}
