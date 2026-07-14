"use client"

"use client"

import { useTranslations } from "next-intl"

import type { ROIResult } from "@/types/api"
import { useFormat } from "@/lib/use-format"

// Deterministische Begruendungs-Bausteine, geteilt zwischen Triage-Ergebnis und
// Report. Alle Texte werden aus vorhandenen Zahlenfeldern getemplatet -- kein
// LLM, keine erfundenen Werte. Nur Ist-Werte aus der TriageResponse.

// --- 1a: Nettonutzen-Erklaerung + aufklappbarer Rechenweg --------------------

export function NetBenefitRationale({ roi }: { roi: ROIResult }) {
  const t = useTranslations("rationale")
  const fmt = useFormat()
  const usageReduces = roi.usage_factor < 1
  const evidenceReduces = roi.evidence_factor < 1
  const hasLicense = roi.license_cost_annual_eur > 0

  // Faktoren, die die Luecke zum theoretischen Potenzial erklaeren, werden im
  // Satz und im Rechenweg hervorgehoben.
  const mark = "font-medium text-[var(--zone-risk-fg)]"

  const rows: {
    op: string
    label: string
    value: string
    highlight: boolean
  }[] = [
    {
      op: "",
      label: t("theoreticalPotential"),
      value: fmt.eur(roi.theoretical_potential_eur),
      highlight: false,
    },
    {
      op: "×",
      label: t("usageFactor"),
      value: fmt.factor(roi.usage_factor),
      highlight: usageReduces,
    },
    {
      op: "×",
      label: t("evidenceFactor"),
      value: fmt.factor(roi.evidence_factor),
      highlight: evidenceReduces,
    },
  ]
  if (hasLicense) {
    rows.push({
      op: "−",
      label: t("licenseCostPa"),
      value: fmt.eur(roi.license_cost_annual_eur),
      highlight: false,
    })
  }

  return (
    <div>
      <p className="text-[0.8125rem] leading-relaxed text-muted-foreground">
        {t.rich(hasLicense ? "sentenceLicense" : "sentence", {
          potential: fmt.eur(roi.theoretical_potential_eur),
          net: fmt.eur(roi.net_expected_benefit_eur),
          usage: fmt.percent(roi.usage_factor),
          evidence: fmt.percent(roi.evidence_factor),
          license: hasLicense ? fmt.eur(roi.license_cost_annual_eur) : "",
          netTag: (chunks) => (
            <span className="font-medium text-foreground">{chunks}</span>
          ),
          usageTag: (chunks) => (
            <span className={usageReduces ? mark : "text-foreground/80"}>
              {chunks}
            </span>
          ),
          evidenceTag: (chunks) => (
            <span className={evidenceReduces ? mark : "text-foreground/80"}>
              {chunks}
            </span>
          ),
        })}
      </p>

      <details className="group mt-3">
        <summary className="inline-flex cursor-pointer list-none items-center gap-1 rounded text-xs font-medium text-[var(--ink)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-background">
          <span className="transition-transform group-open:rotate-90" aria-hidden>
            ›
          </span>
          {t("calcPath")}
        </summary>
        <div className="mt-3 rounded-lg border border-border bg-muted/40 px-4 py-3 text-[0.8125rem]">
          {rows.map((row) => (
            <div
              key={row.label}
              className="grid grid-cols-[1.25rem_1fr_auto] items-baseline gap-x-2 py-0.5"
            >
              <span
                className="text-right font-mono text-muted-foreground"
                aria-hidden
              >
                {row.op}
              </span>
              <span
                className={
                  row.highlight ? mark : "text-muted-foreground"
                }
              >
                {row.label}
              </span>
              <span
                className={`text-right font-mono tnum ${
                  row.highlight ? mark : "text-foreground/85"
                }`}
              >
                {row.value}
              </span>
            </div>
          ))}
          <div className="mt-1 grid grid-cols-[1.25rem_1fr_auto] items-baseline gap-x-2 border-t border-border pt-2">
            <span className="text-right font-mono text-muted-foreground" aria-hidden>
              =
            </span>
            <span className="font-medium text-foreground">
              {t("expectedNetBenefit")}
            </span>
            <span className="text-right font-mono tnum font-medium text-foreground">
              {fmt.eur(roi.net_expected_benefit_eur)}
            </span>
          </div>
        </div>
      </details>
    </div>
  )
}

// --- 1f: Routing-Begruendung -- die tragenden Signale sichtbar machen --------

function SignalList({
  title,
  signals,
}: {
  title: string
  signals: string[]
}) {
  if (signals.length === 0) return null
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground">{title}</p>
      <ul className="mt-2 space-y-1.5">
        {signals.map((signal, i) => (
          <li
            key={i}
            className="flex gap-2 text-[0.8125rem] leading-snug text-foreground/85"
          >
            <span className="mt-1.5 size-1 shrink-0 rounded-full bg-[var(--ink)]" aria-hidden />
            {signal}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function RoutingRationale({
  recommendation,
  automationSignals,
  aiSignals,
}: {
  recommendation: string
  automationSignals: string[]
  aiSignals: string[]
}) {
  const t = useTranslations("rationale")
  // Welche Signale die Empfehlung tragen, haengt an der Empfehlung selbst.
  // Bei Grenzfaellen zeigen beide Seiten -- das IST die Begruendung.
  const aiLeaning = recommendation === "AI_RECOMMENDED"
  const autoLeaning = recommendation === "AUTOMATION_RECOMMENDED"

  const showAI = aiLeaning || (!autoLeaning && aiSignals.length > 0)
  const showAuto = autoLeaning || (!aiLeaning && automationSignals.length > 0)

  const ai = showAI ? aiSignals : []
  const auto = showAuto ? automationSignals : []

  if (ai.length === 0 && auto.length === 0) return null

  const both = ai.length > 0 && auto.length > 0

  return (
    <div
      className={
        both ? "grid grid-cols-1 gap-4 sm:grid-cols-2" : "space-y-4"
      }
    >
      <SignalList title={t("aiSupports")} signals={ai} />
      <SignalList title={t("autoSupports")} signals={auto} />
    </div>
  )
}
