"use client"

import Link from "next/link"
import { useState } from "react"
import { useTranslations } from "next-intl"
import { ChevronDown, Loader2 } from "lucide-react"

import type { CaseSummary, MonitoringEntry } from "@/types/api"
import { listMonitoringEntries } from "@/app/actions"
import { CaseStatusControl } from "@/components/case-status-control"
import { MonitoringTimeline } from "@/components/monitoring-timeline"
import { ZoneBadge } from "@/components/status-badge"
import { useFormat } from "@/lib/use-format"
import { cn } from "@/lib/utils"

// Monitoring-Bereich (V4-P7): eine Zeile pro freigegebenem/umgesetztem Case mit
// direkt pflegbarem Status-Select und aufklappbarer append-only Zeitleiste. Die
// Zeitleiste wird erst beim Aufklappen geladen (listMonitoringEntries), damit
// die Seite nicht N Requests beim ersten Rendern absetzt. Der Case-Name verlinkt
// die Fall-Detailseite (nicht die Ideenliste).

function MonitoringRow({ c }: { c: CaseSummary }) {
  const t = useTranslations("monitoring")
  const fmt = useFormat()
  const [expanded, setExpanded] = useState(false)
  const [entries, setEntries] = useState<MonitoringEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function toggle() {
    const next = !expanded
    setExpanded(next)
    // Beim ersten Aufklappen einmalig laden.
    if (next && entries === null && !loading) {
      setLoading(true)
      setError(null)
      try {
        setEntries(await listMonitoringEntries(c.id))
      } catch (e) {
        setError(e instanceof Error ? e.message : t("entriesLoadError"))
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div className="border-b border-border last:border-b-0">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 px-5 py-4">
        <div className="min-w-0 flex-1">
          <Link
            href={`/cases/${c.id}`}
            className="font-medium text-foreground underline-offset-2 hover:underline"
          >
            {c.title}
          </Link>
          <p className="mt-0.5 text-xs text-muted-foreground">{c.department}</p>
        </div>
        <div className="hidden sm:block">
          <ZoneBadge zone={c.zone} />
        </div>
        <div className="hidden font-mono text-sm tabular-nums text-foreground/85 md:block">
          {c.net_expected_benefit_eur === null
            ? "—"
            : fmt.eur(c.net_expected_benefit_eur)}
        </div>
        <CaseStatusControl caseId={c.id} initialStatus={c.status} />
        <button
          type="button"
          onClick={toggle}
          aria-expanded={expanded}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-[var(--ink)] outline-none transition-colors hover:bg-[var(--ink-subtle)] focus-visible:ring-2 focus-visible:ring-ring/40"
        >
          {t("history")}
          <ChevronDown
            className={cn(
              "size-3.5 transition-transform",
              expanded && "rotate-180",
            )}
          />
        </button>
      </div>

      {expanded && (
        <div className="border-t border-border bg-muted/20 px-5 py-5">
          {loading ? (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              {t("historyLoading")}
            </p>
          ) : error !== null ? (
            <p
              role="alert"
              className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
            >
              {error}
            </p>
          ) : (
            <MonitoringTimeline caseId={c.id} initialEntries={entries ?? []} />
          )}
        </div>
      )}
    </div>
  )
}

export function MonitoringBoard({ cases }: { cases: CaseSummary[] }) {
  const t = useTranslations("monitoring")
  if (cases.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card px-6 py-14 text-center">
        <p className="text-sm text-muted-foreground">{t("empty")}</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      {cases.map((c) => (
        <MonitoringRow key={c.id} c={c} />
      ))}
    </div>
  )
}

export default MonitoringBoard
