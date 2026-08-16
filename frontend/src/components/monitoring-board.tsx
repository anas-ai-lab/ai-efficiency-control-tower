"use client"

import Link from "next/link"
import { useState } from "react"
import { useTranslations } from "next-intl"
import { ChevronDown, Loader2 } from "lucide-react"

import type { CaseStatus, CaseSummary, MonitoringEntry } from "@/types/api"
import { listMonitoringEntries } from "@/app/actions"
import { ActiveFilters, EmptyResult } from "@/components/filter-bar"
import { DiscontinueControl } from "@/components/discontinue-control"
import { MonitoringTimeline } from "@/components/monitoring-timeline"
import { StatusBadge, ZoneBadge } from "@/components/status-badge"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { STATUS_CONFIG } from "@/lib/status"
import { readEnumParam, useFilterParams } from "@/lib/use-filter-params"
import { useFormat } from "@/lib/use-format"
import { cn } from "@/lib/utils"

// Monitoring-Bereich (V4-P7): eine Zeile pro freigegebenem/umgesetztem Case mit
// Status-Badge und aufklappbarer append-only Zeitleiste. Die
// Zeitleiste wird erst beim Aufklappen geladen (listMonitoringEntries), damit
// die Seite nicht N Requests beim ersten Rendern absetzt. Der Case-Name verlinkt
// die Fall-Detailseite (nicht die Ideenliste).

// Die beiden Filter-Dimensionen des Monitorings. Beide liegen als
// SearchParam in der URL (lib/use-filter-params), keiner in React-State:
//   status   -- Lifecycle innerhalb der beobachteten Menge
//   tracking -- Beobachtungs-Flag (discontinued), unabhaengig vom Lifecycle
const FILTER_KEYS = ["status", "tracking"] as const
// Nur diese beiden Status erreichen das Monitoring ueberhaupt (die Seite
// filtert serverseitig darauf vor) -- ein Filter auf "rejected" waere hier
// per Konstruktion immer leer und steht deshalb nicht zur Wahl.
const MONITORED_STATUS: CaseStatus[] = ["approved", "implemented"]
const TRACKING_VALUES = ["active", "discontinued"] as const
type TrackingFilter = (typeof TRACKING_VALUES)[number]

function MonitoringRow({ c }: { c: CaseSummary }) {
  const t = useTranslations("monitoring")
  const fmt = useFormat()
  const [expanded, setExpanded] = useState(false)
  const [entries, setEntries] = useState<MonitoringEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // discontinued (V4.1-S7): eigener State statt direktem c.discontinued-Zugriff,
  // damit DiscontinueControl den vom Server bestaetigten Wert zurueckmelden
  // kann -- Badge und Hervorhebung unten lesen denselben State.
  const [discontinued, setDiscontinued] = useState(c.discontinued)

  async function load() {
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

  async function toggle() {
    const next = !expanded
    setExpanded(next)
    // Beim ersten Aufklappen einmalig laden.
    if (next && entries === null && !loading) {
      await load()
    }
  }

  // Einstellen/Reaktivieren erzeugt serverseitig einen Verlaufseintrag
  // (V4.1-S10). Eine bereits geladene Zeitleiste wuesste sonst nichts davon und
  // zeigte einen Verlauf, in dem der eben ausgefuehrte Akt fehlt.
  async function handleEventLogged() {
    if (entries !== null) await load()
  }

  return (
    <div
      className={cn(
        "border-b border-border last:border-b-0",
        discontinued && "border-l-2 border-l-destructive/60 bg-destructive/5",
      )}
    >
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 px-5 py-4">
        {/* basis-full unter sm: Titel + Abteilung bekommen eine eigene Zeile,
            statt sich mit den Badges um dieselbe zu druecken. Ab sm traegt
            flex-1 den Rest der Breite.

            min-w-[14rem] ist die Untergrenze, nicht Kosmetik: ohne sie druecken
            die shrink-0-Geschwister den Titel bei langem Text auf ~200px, er
            bricht auf fuenf Zeilen um, und das vertikal zentrierte Badge landet
            MITTEN im Titelblock -- optisch genau die Ueberlappung, die hier
            behoben werden soll (im Screenshot-Durchlauf bei 768px und 1280px
            gesehen). Mit der Untergrenze weichen stattdessen die Geschwister in
            die naechste Zeile aus (flex-wrap), der Titel bleibt zweizeilig. */}
        <div className="min-w-0 basis-full sm:min-w-[14rem] sm:flex-1 sm:basis-0">
          <Link
            href={`/cases/${c.id}`}
            className="font-medium text-foreground underline-offset-2 hover:underline"
          >
            {c.title}
          </Link>
          <p className="mt-0.5 text-xs text-muted-foreground">{c.department}</p>
        </div>
        {/* Zustands-Badge und Zone sitzen als Geschwister in EINEM gap-Container
            (frueher: Badge inline im Abteilungs-Absatz, wo es bei knapper Breite
            in die Zone lief). Geschwister in einem flex-gap koennen sich
            strukturell nicht ueberlappen -- auf keinem Breakpoint. shrink-0
            haelt sie zusammen, wenn der Titel lang wird. */}
        <div className="flex shrink-0 items-center gap-3">
          {discontinued && (
            <Badge variant="destructive">{t("discontinuedBadge")}</Badge>
          )}
          <div className="hidden sm:block">
            <ZoneBadge zone={c.zone} />
          </div>
        </div>
        <div className="hidden font-mono text-sm tabular-nums text-foreground/85 md:block">
          {c.net_expected_benefit_eur === null
            ? "—"
            : fmt.eur(c.net_expected_benefit_eur)}
        </div>
        <StatusBadge status={c.status} />
        <DiscontinueControl
          caseId={c.id}
          discontinued={discontinued}
          onDiscontinuedChange={setDiscontinued}
          onEventLogged={handleEventLogged}
        />
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
            <MonitoringTimeline
              caseId={c.id}
              initialEntries={entries ?? []}
              discontinued={discontinued}
            />
          )}
        </div>
      )}
    </div>
  )
}

export function MonitoringBoard({ cases }: { cases: CaseSummary[] }) {
  const t = useTranslations("monitoring")
  const ts = useTranslations("status")
  const tf = useTranslations("filters")
  const filters = useFilterParams(FILTER_KEYS)

  const statusFilter = readEnumParam(filters.get("status"), MONITORED_STATUS)
  const trackingFilter = readEnumParam<TrackingFilter>(
    filters.get("tracking"),
    TRACKING_VALUES,
  )

  const visible = cases.filter((c) => {
    if (statusFilter !== null && c.status !== statusFilter) return false
    if (trackingFilter === "active" && c.discontinued) return false
    if (trackingFilter === "discontinued" && !c.discontinued) return false
    return true
  })

  const chips = [
    statusFilter !== null && {
      key: "status",
      label: t("filterStatus"),
      value: ts(statusFilter),
    },
    trackingFilter !== null && {
      key: "tracking",
      label: t("filterTracking"),
      value:
        trackingFilter === "active"
          ? t("trackingActive")
          : t("trackingDiscontinued"),
    },
  ].filter((c) => c !== false)

  // Die Toolbar steht ausserhalb jeder Ergebnis-Bedingung: sie rendert auch
  // dann, wenn `visible` oder `cases` leer ist. Genau der Early-Return an
  // dieser Stelle war der Grund, warum ein leeres Ergebnis frueher keinen
  // Rueckweg mehr hatte.
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="eyebrow">{t("filterStatus")}</span>
          <Select
            // "all" ist der Anzeige-Wert fuer "kein Param" -- in die URL wandert
            // er nie (set(..., null) loescht den Param).
            value={statusFilter ?? "all"}
            onValueChange={(v) =>
              filters.set("status", v === "all" ? null : v)
            }
          >
            <SelectTrigger size="sm" className="w-[11rem]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allStatus")}</SelectItem>
              {MONITORED_STATUS.map((s) => (
                <SelectItem key={s} value={s}>
                  <span
                    className={cn("size-1.5 rounded-full", STATUS_CONFIG[s].dot)}
                    aria-hidden
                  />
                  {ts(s)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="eyebrow">{t("filterTracking")}</span>
          <Select
            value={trackingFilter ?? "all"}
            onValueChange={(v) =>
              filters.set("tracking", v === "all" ? null : v)
            }
          >
            <SelectTrigger size="sm" className="w-[11rem]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allTracking")}</SelectItem>
              <SelectItem value="active">{t("trackingActive")}</SelectItem>
              <SelectItem value="discontinued">
                {t("trackingDiscontinued")}
              </SelectItem>
            </SelectContent>
          </Select>
        </label>
      </div>

      <ActiveFilters
        chips={chips}
        resultLabel={tf("results", {
          count: visible.length,
          total: cases.length,
        })}
        onRemove={(key) => filters.remove(key as (typeof FILTER_KEYS)[number])}
        onReset={filters.reset}
      />

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        {visible.length === 0 ? (
          <EmptyResult
            message={filters.hasActive ? t("emptyFiltered") : t("empty")}
            onReset={filters.hasActive ? filters.reset : undefined}
          />
        ) : (
          visible.map((c) => <MonitoringRow key={c.id} c={c} />)
        )}
      </div>
    </div>
  )
}

export default MonitoringBoard
