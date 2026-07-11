"use client"

import type { ROIResult, CompositeResult } from "@/types/api"
import { formatEUR, formatPercent, formatFactor } from "@/lib/formatters"

// Deterministische Begruendungs-Bausteine, geteilt zwischen Triage-Ergebnis und
// Report. Alle Texte werden aus vorhandenen Zahlenfeldern getemplatet -- kein
// LLM, keine erfundenen Werte. Nur Ist-Werte aus der TriageResponse.

// Konfidenz-Score (ADR-0036) in Klartext. Der Score misst den Abstand zur
// naechsten Zonengrenze; diese Saetze uebersetzen ihn fuer Entscheider.
export const CONFIDENCE_INTERPRETATION: Record<string, string> = {
  hoch: "Klar in der Zone — robuste Einstufung.",
  mittel: "Nahe an einer Zonengrenze — Einstufung mit Vorbehalt.",
  niedrig:
    "Direkt an der Zonengrenze — schon kleine Änderungen kippen die Zone.",
}

// Bedeutung des Aufwand-Labels als ganzer Satz.
const EFFORT_MEANING: Record<string, string> = {
  NIEDRIG: "geringer Umsetzungsaufwand",
  MITTEL: "mittlerer Aufwand, planbar",
  HOCH: "hoher Aufwand, kritisch prüfen",
}

// --- 1a: Nettonutzen-Erklaerung + aufklappbarer Rechenweg --------------------

export function NetBenefitRationale({ roi }: { roi: ROIResult }) {
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
      label: "Theoret. Potenzial",
      value: formatEUR(roi.theoretical_potential_eur),
      highlight: false,
    },
    {
      op: "×",
      label: "Nutzungsfaktor",
      value: formatFactor(roi.usage_factor),
      highlight: usageReduces,
    },
    {
      op: "×",
      label: "Evidenzfaktor",
      value: formatFactor(roi.evidence_factor),
      highlight: evidenceReduces,
    },
  ]
  if (hasLicense) {
    rows.push({
      op: "−",
      label: "Lizenzkosten p.a.",
      value: formatEUR(roi.license_cost_annual_eur),
      highlight: false,
    })
  }

  return (
    <div>
      <p className="text-[0.8125rem] leading-relaxed text-muted-foreground">
        Vom theoretischen Potenzial ({formatEUR(roi.theoretical_potential_eur)})
        {" "}bleiben{" "}
        <span className="font-medium text-foreground">
          {formatEUR(roi.net_expected_benefit_eur)}
        </span>
        : Nutzung{" "}
        <span className={usageReduces ? mark : "text-foreground/80"}>
          {formatPercent(roi.usage_factor)}
        </span>{" "}
        × Evidenz{" "}
        <span className={evidenceReduces ? mark : "text-foreground/80"}>
          {formatPercent(roi.evidence_factor)}
        </span>
        {hasLicense && (
          <>
            , abzüglich {formatEUR(roi.license_cost_annual_eur)} Lizenzkosten
          </>
        )}
        .
      </p>

      <details className="group mt-3">
        <summary className="inline-flex cursor-pointer list-none items-center gap-1 rounded text-xs font-medium text-[var(--ink)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-background">
          <span className="transition-transform group-open:rotate-90" aria-hidden>
            ›
          </span>
          Rechenweg
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
              Erwarteter Nettonutzen
            </span>
            <span className="text-right font-mono tnum font-medium text-foreground">
              {formatEUR(roi.net_expected_benefit_eur)}
            </span>
          </div>
        </div>
      </details>
    </div>
  )
}

// --- 1b: Aufwand-Score mit gelabelten Subscores + segmentierter Leiste -------

export function CompositeBreakdown({
  composite,
}: {
  composite: CompositeResult
}) {
  // Segmentbreiten auf der 0-9-Skala (Aufwand-Range 1-9, CompositeScore.total):
  // die gefuellte Leiste zeigt total/9, aufgeteilt nach Beitrag jeder Dimension.
  // Der Rest bleibt sichtbar leer.
  const segments = [
    {
      label: "Komplexität",
      score: composite.complexity_score,
      max: 5,
      color: "var(--ink)",
    },
    {
      label: "Kosten",
      score: composite.cost_score,
      max: 2,
      color: "var(--zone-risk)",
    },
    {
      label: "Datenschutz",
      score: composite.data_protection_score,
      max: 2,
      color: "var(--zone-gain)",
    },
  ]
  const meaning = EFFORT_MEANING[composite.effort_label] ?? ""

  return (
    <div>
      <p className="text-sm text-foreground/85">
        <span className="tnum">Komplexität {composite.complexity_score}/5</span>{" "}
        · <span className="tnum">Kosten {composite.cost_score}/2</span> ·{" "}
        <span className="tnum">
          Datenschutz {composite.data_protection_score}/2
        </span>{" "}
        ={" "}
        <span className="font-medium text-foreground tnum">
          {composite.total}/9
        </span>{" "}
        ({composite.effort_label})
      </p>

      <div
        className="mt-3 flex h-2 w-full overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`Aufwand ${composite.total} von 9: Komplexität ${composite.complexity_score}, Kosten ${composite.cost_score}, Datenschutz ${composite.data_protection_score}`}
      >
        {segments.map((seg) => (
          <div
            key={seg.label}
            className="h-full"
            style={{
              width: `${(seg.score / 9) * 100}%`,
              backgroundColor: seg.color,
            }}
          />
        ))}
      </div>

      <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {segments.map((seg) => (
          <span key={seg.label} className="inline-flex items-center gap-1.5">
            <span
              className="size-2 rounded-sm"
              style={{ backgroundColor: seg.color }}
              aria-hidden
            />
            {seg.label}
          </span>
        ))}
      </div>

      {meaning !== "" && (
        <p className="mt-2.5 text-[0.8125rem] leading-relaxed text-muted-foreground">
          {meaning}.
        </p>
      )}
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
      <SignalList title="Wofür KI spricht" signals={ai} />
      <SignalList title="Wofür Automatisierung spricht" signals={auto} />
    </div>
  )
}
