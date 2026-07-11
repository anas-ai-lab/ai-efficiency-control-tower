"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowDown, ArrowUp, ChevronsUpDown, Download } from "lucide-react";

import type {
  CaseStatus,
  CaseSummary,
  SimilarityPair,
  TriageZone,
} from "@/types/api";
import { updateCaseStatus } from "@/app/actions";
import { formatEUR, ZONE_CONFIG, type ZoneKey } from "@/lib/formatters";
import { STATUS_CONFIG } from "@/lib/status";
import { downloadCasesCsv } from "@/lib/csv";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Reihenfolge der Status/Zonen fuer Filter + Status-Select (STATUS_CONFIG /
// ZONE_CONFIG bleiben die einzige Quelle fuer Label und Farbe).
const STATUS_ORDER: CaseStatus[] = [
  "submitted",
  "in_review",
  "approved",
  "already_exists",
  "integrated",
  "rejected",
  "implemented",
];
const ZONE_ORDER: TriageZone[] = [
  "LIKELY_WIN",
  "CALCULATED_RISK",
  "MARGINAL_GAIN",
];

type StatusFilter = CaseStatus | "all";
type ZoneFilter = TriageZone | "none" | "all";
type SortKey = "date" | "net";
type SortDir = "asc" | "desc";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}

// Nullwerte ("—") sortieren IMMER ans Ende, unabhaengig von asc/desc.
function compareNullable(a: number | null, b: number | null, dir: SortDir): number {
  const aNull = a === null || Number.isNaN(a);
  const bNull = b === null || Number.isNaN(b);
  if (aNull && bNull) return 0;
  if (aNull) return 1;
  if (bNull) return -1;
  const cmp = a - b;
  return dir === "asc" ? cmp : -cmp;
}

function ZoneBadge({ zone }: { zone: TriageZone | null }) {
  if (zone === null) {
    return <span className="text-muted-foreground">—</span>;
  }
  const c = ZONE_CONFIG[zone as ZoneKey];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        c.surface,
        c.text,
      )}
    >
      <span className={cn("size-1.5 rounded-full", c.dot)} aria-hidden />
      {c.labelDE}
    </span>
  );
}

// Dedup-Hinweis je Case (P9/P12): Titel der Partner-Cases + ob mindestens ein
// Paar zur Zusammenfuehrung vorgeschlagen wird (suggest_combine).
interface SimilarityInfo {
  partnerTitles: string[];
  suggestCombine: boolean;
}

// Baut aus der flachen Paar-Liste einen Index case_id -> SimilarityInfo. Ein
// Paar taucht fuer beide beteiligten Cases auf (jeweils mit dem Titel des
// anderen). Faellt listSimilarityPairs() aus, ist pairs leer -> leerer Index,
// keine Badges, Tabelle bleibt voll funktionsfaehig.
function buildSimilarityIndex(
  pairs: SimilarityPair[],
): Map<string, SimilarityInfo> {
  const index = new Map<string, SimilarityInfo>();
  const add = (id: string, partnerTitle: string, suggest: boolean) => {
    const cur = index.get(id) ?? { partnerTitles: [], suggestCombine: false };
    cur.partnerTitles.push(partnerTitle);
    cur.suggestCombine = cur.suggestCombine || suggest;
    index.set(id, cur);
  };
  for (const p of pairs) {
    add(p.case_a_id, p.case_b_title, p.suggest_combine);
    add(p.case_b_id, p.case_a_title, p.suggest_combine);
  }
  return index;
}

// Dezenter Hinweis neben dem Titel: "N ähnlich". Bei mindestens einem
// suggest_combine-Paar staerkere Variante in Tinten-Akzent (--ink) -- ein
// Hinweis, KEIN Fehler, daher bewusst nicht rot. Der Tooltip nennt die Titel
// der aehnlichen Cases.
function SimilarityBadge({ info }: { info: SimilarityInfo }) {
  const n = info.partnerTitles.length;
  return (
    <span
      title={`Ähnlich zu: ${info.partnerTitles.join(" · ")}`}
      className={cn(
        "inline-flex shrink-0 items-center rounded-full border px-1.5 py-0.5 text-[0.6875rem] font-medium whitespace-nowrap",
        info.suggestCombine
          ? "border-[var(--ink)]/25 bg-[var(--ink-subtle)] text-[var(--ink)]"
          : "border-border bg-muted/50 text-muted-foreground",
      )}
    >
      {n} ähnlich
    </span>
  );
}

// Status-Select je Zeile: zeigt den aktuellen Status als Badge (Dot + Label aus
// STATUS_CONFIG) und bietet die 7 deutschen Labels zur Auswahl. Radix
// SelectValue spiegelt die Kinder des gewaehlten Items -> Dot + Label erscheinen
// im Trigger wie im Dropdown.
function StatusSelect({
  value,
  disabled,
  onChange,
}: {
  value: CaseStatus;
  disabled: boolean;
  onChange: (next: CaseStatus) => void;
}) {
  return (
    <Select
      value={value}
      disabled={disabled}
      onValueChange={(v) => onChange(v as CaseStatus)}
    >
      <SelectTrigger size="sm" className="w-[9.75rem]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {STATUS_ORDER.map((s) => (
          <SelectItem key={s} value={s}>
            <span
              className={cn("size-1.5 rounded-full", STATUS_CONFIG[s].dot)}
              aria-hidden
            />
            {STATUS_CONFIG[s].labelDE}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

interface SortableHeaderProps {
  label: string;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
  align?: "left" | "right";
}

function SortableHeader({ label, active, dir, onClick, align }: SortableHeaderProps) {
  const Icon = !active ? ChevronsUpDown : dir === "asc" ? ArrowUp : ArrowDown;
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 rounded-sm text-xs font-medium tracking-wide text-muted-foreground uppercase outline-none transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/40",
        align === "right" && "flex-row-reverse",
        active && "text-foreground",
      )}
      aria-label={`Nach ${label} sortieren`}
    >
      {label}
      <Icon className={cn("size-3.5", !active && "opacity-60")} aria-hidden />
    </button>
  );
}

export function CasesTable({
  cases,
  pairs = [],
  authenticated = false,
}: {
  cases: CaseSummary[];
  pairs?: SimilarityPair[];
  // V4-P-Auth: der Statuswechsel ist eine Admin-Aktion. Anonyme sehen den Status
  // read-only als Badge, kein Select (das Backend wuerde POST /status ohnehin
  // mit 401 ablehnen).
  authenticated?: boolean;
}) {
  const router = useRouter();
  const [rows, setRows] = useState<CaseSummary[]>(cases);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [zoneFilter, setZoneFilter] = useState<ZoneFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [pending, setPending] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const similarityIndex = useMemo(() => buildSimilarityIndex(pairs), [pairs]);

  const visible = useMemo(() => {
    const filtered = rows.filter((c) => {
      if (statusFilter !== "all" && c.status !== statusFilter) return false;
      if (zoneFilter === "none" && c.zone !== null) return false;
      if (zoneFilter !== "all" && zoneFilter !== "none" && c.zone !== zoneFilter) {
        return false;
      }
      return true;
    });
    const sorted = [...filtered].sort((a, b) => {
      if (sortKey === "net") {
        return compareNullable(
          a.net_expected_benefit_eur,
          b.net_expected_benefit_eur,
          sortDir,
        );
      }
      return compareNullable(
        Date.parse(a.submitted_at),
        Date.parse(b.submitted_at),
        sortDir,
      );
    });
    return sorted;
  }, [rows, statusFilter, zoneFilter, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  async function handleStatusChange(id: string, next: CaseStatus) {
    const prev = rows.find((r) => r.id === id)?.status;
    if (prev === undefined || prev === next) return;

    // Optimistisches Update: sofort in der UI setzen ...
    setRows((rs) => rs.map((r) => (r.id === id ? { ...r, status: next } : r)));
    setPending((p) => ({ ...p, [id]: true }));
    setErrors((e) => ({ ...e, [id]: null }));

    try {
      const res = await updateCaseStatus(id, next);
      setRows((rs) =>
        rs.map((r) => (r.id === id ? { ...r, status: res.status } : r)),
      );
    } catch (e) {
      // ... bei Fehlschlag Rollback auf den vorherigen Status + Fehlertext.
      setRows((rs) => rs.map((r) => (r.id === id ? { ...r, status: prev } : r)));
      setErrors((er) => ({
        ...er,
        [id]:
          e instanceof Error ? e.message : "Statuswechsel fehlgeschlagen.",
      }));
    } finally {
      setPending((p) => ({ ...p, [id]: false }));
    }
  }

  function goToCase(id: string) {
    router.push(`/cases/${id}`);
  }

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card px-6 py-14 text-center">
        <p className="text-sm text-muted-foreground">
          Noch keine Use Cases eingereicht.
        </p>
        <Link
          href="/einreichen"
          className="mt-3 inline-block text-sm font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
        >
          Ersten Use Case einreichen
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Filter */}
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="eyebrow">Status</span>
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as StatusFilter)}
          >
            <SelectTrigger size="sm" className="w-[10rem]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Alle Status</SelectItem>
              {STATUS_ORDER.map((s) => (
                <SelectItem key={s} value={s}>
                  <span
                    className={cn("size-1.5 rounded-full", STATUS_CONFIG[s].dot)}
                    aria-hidden
                  />
                  {STATUS_CONFIG[s].labelDE}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="eyebrow">Zone</span>
          <Select
            value={zoneFilter}
            onValueChange={(v) => setZoneFilter(v as ZoneFilter)}
          >
            <SelectTrigger size="sm" className="w-[11rem]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Alle Zonen</SelectItem>
              {ZONE_ORDER.map((z) => (
                <SelectItem key={z} value={z}>
                  <span
                    className={cn("size-1.5 rounded-full", ZONE_CONFIG[z].dot)}
                    aria-hidden
                  />
                  {ZONE_CONFIG[z].labelDE}
                </SelectItem>
              ))}
              <SelectItem value="none">Ohne Bewertung</SelectItem>
            </SelectContent>
          </Select>
        </label>

        {/* Export der AKTUELL gefilterten und sortierten Sicht (visible),
            client-seitig, ohne Dependency. */}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="ml-auto"
          onClick={() => downloadCasesCsv(visible)}
          disabled={visible.length === 0}
        >
          <Download aria-hidden />
          CSV exportieren
        </Button>
      </div>

      {/* Tabelle */}
      <div className="overflow-x-auto rounded-xl border border-border bg-card">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              <th className="px-4 py-3 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                Titel
              </th>
              <th className="px-4 py-3 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                Abteilung
              </th>
              <th className="px-4 py-3">
                <SortableHeader
                  label="Eingereicht"
                  active={sortKey === "date"}
                  dir={sortDir}
                  onClick={() => toggleSort("date")}
                />
              </th>
              <th className="px-4 py-3 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                Zone
              </th>
              <th className="px-4 py-3 text-right">
                <SortableHeader
                  label="Nettonutzen"
                  active={sortKey === "net"}
                  dir={sortDir}
                  onClick={() => toggleSort("net")}
                  align="right"
                />
              </th>
              <th className="px-4 py-3 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {visible.map((c) => (
              <tr
                key={c.id}
                role="link"
                tabIndex={0}
                onClick={() => goToCase(c.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    goToCase(c.id);
                  }
                }}
                className="cursor-pointer border-b border-border/60 outline-none transition-colors last:border-0 hover:bg-muted/40 focus-visible:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring/40"
              >
                <td className="max-w-xs px-4 py-3">
                  <div className="flex items-start gap-2">
                    <span className="line-clamp-2 font-medium text-foreground">
                      {c.title}
                    </span>
                    {similarityIndex.has(c.id) && (
                      <SimilarityBadge info={similarityIndex.get(c.id)!} />
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {c.department}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-muted-foreground tabular-nums">
                  {formatDate(c.submitted_at)}
                </td>
                <td className="px-4 py-3">
                  <ZoneBadge zone={c.zone} />
                </td>
                <td className="px-4 py-3 text-right font-mono text-foreground tabular-nums">
                  {c.net_expected_benefit_eur === null ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    formatEUR(c.net_expected_benefit_eur)
                  )}
                </td>
                {/* Status-Zelle: Klick/Tastatur hier navigiert NICHT (stopPropagation).
                    Nur Admins wechseln den Status; Anonyme sehen die Badge. */}
                <td
                  className="px-4 py-3"
                  onClick={(e) => e.stopPropagation()}
                  onKeyDown={(e) => e.stopPropagation()}
                >
                  {authenticated ? (
                    <>
                      <StatusSelect
                        value={c.status}
                        disabled={pending[c.id] ?? false}
                        onChange={(next) => handleStatusChange(c.id, next)}
                      />
                      {errors[c.id] != null && (
                        <p
                          role="alert"
                          className="mt-1.5 max-w-[12rem] text-xs text-destructive"
                        >
                          {errors[c.id]}
                        </p>
                      )}
                    </>
                  ) : (
                    <StatusBadge status={c.status} />
                  )}
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-10 text-center text-sm text-muted-foreground"
                >
                  Keine Use Cases entsprechen den Filtern.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Anzahl */}
      <p className="mt-3 text-xs text-muted-foreground tabular-nums">
        {rows.length} {rows.length === 1 ? "Use Case" : "Use Cases"} ·{" "}
        {visible.length} gefiltert
      </p>
    </div>
  );
}
