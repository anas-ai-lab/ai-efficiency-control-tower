"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ChevronDown } from "lucide-react";
import {
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import type { CaseStatus, CaseSummary, TriageZone } from "@/types/api";
import { formatEUR, formatNumber, ZONE_CONFIG, type ZoneKey } from "@/lib/formatters";
import { STATUS_CONFIG } from "@/lib/status";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Reihenfolge der Status fuer den Filter (STATUS_CONFIG bleibt die einzige
// Quelle fuer Label und Farbe -- lokale Kopie der Ordnung wie in cases-table,
// bewusst keine vorzeitige Abstraktion ueber zwei Views hinweg).
const STATUS_ORDER: CaseStatus[] = [
  "submitted",
  "in_review",
  "approved",
  "already_exists",
  "integrated",
  "rejected",
  "implemented",
];

type StatusFilter = CaseStatus | "all";

// Quadranten-Trennwerte. WICHTIG: 50.000 EUR ist ein STATISCHER Naeherungswert,
// optisch angelehnt an die LIKELY_WIN-Schwelle in zone_thresholds.yaml, aber
// NICHT aus der Config gelesen -- das Backend exponiert die Schwellen nicht.
// Das ist eine reine Lese-Hilfslinie, KEINE Geschaeftsregel. y = 6 ist die
// Mitte der Composite-Skala (Aufwand-Score 2-10).
const QUADRANT_X = 50_000;
const QUADRANT_Y = 6;

// Punkt fuer die Matrix. Nur Cases mit vollstaendiger Bewertung landen hier
// (zone != null impliziert net/composite/hours != null -- gleiche None-Semantik
// wie in TriageResponse: alle vier fallen bei Vorfilter-Fail gemeinsam auf null).
interface MatrixPoint {
  id: string;
  title: string;
  department: string;
  status: CaseStatus;
  zone: TriageZone;
  x: number; // net_expected_benefit_eur
  y: number; // composite_total (Aufwand-Score 2-10)
  z: number; // hours_per_year (Blasengroesse)
}

function toPoint(c: CaseSummary): MatrixPoint | null {
  if (
    c.zone === null ||
    c.net_expected_benefit_eur === null ||
    c.composite_total === null ||
    c.hours_per_year === null
  ) {
    return null;
  }
  return {
    id: c.id,
    title: c.title,
    department: c.department,
    status: c.status,
    zone: c.zone,
    x: c.net_expected_benefit_eur,
    y: c.composite_total,
    z: c.hours_per_year,
  };
}

// Aufwand-Score mit einer Nachkommastelle, z. B. 6,5.
function formatScore(value: number): string {
  return new Intl.NumberFormat("de-DE", {
    maximumFractionDigits: 1,
  }).format(value);
}

// Chart-Farben aus den --zone-*-Tokens (und dezente Achsen-/Grid-Farben). Die
// Tokens sind CSS custom properties; recharts setzt fill/stroke als
// SVG-Attribut, wo var(--x) NICHT aufgeloest wird -- daher via getComputedStyle
// die konkreten Farbstrings lesen. Re-Resolve bei .dark-Wechsel auf <html>,
// damit die Matrix im Dark-Mode korrekt umschaltet.
interface ThemeTokens {
  LIKELY_WIN: string;
  CALCULATED_RISK: string;
  MARGINAL_GAIN: string;
  border: string;
  muted: string;
}

function readTokens(): ThemeTokens {
  const s = getComputedStyle(document.documentElement);
  const v = (name: string) => s.getPropertyValue(name).trim();
  return {
    LIKELY_WIN: v("--zone-win"),
    CALCULATED_RISK: v("--zone-risk"),
    MARGINAL_GAIN: v("--zone-gain"),
    border: v("--border"),
    muted: v("--muted-foreground"),
  };
}

function useThemeTokens(): ThemeTokens | null {
  const [tokens, setTokens] = useState<ThemeTokens | null>(null);
  useEffect(() => {
    setTokens(readTokens());
    const obs = new MutationObserver(() => setTokens(readTokens()));
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => obs.disconnect();
  }, []);
  return tokens;
}

function MatrixTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: MatrixPoint }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0].payload;
  const zone = ZONE_CONFIG[p.zone as ZoneKey];
  return (
    <div className="max-w-[16rem] rounded-lg border border-border bg-popover px-3 py-2.5 text-xs shadow-md">
      <p className="line-clamp-2 font-medium text-popover-foreground">{p.title}</p>
      <p className="mt-0.5 text-muted-foreground">{p.department}</p>
      <div className="mt-2 flex items-center gap-1.5">
        <span className={cn("size-1.5 rounded-full", zone.dot)} aria-hidden />
        <span className={cn("font-medium", zone.text)}>{zone.labelDE}</span>
      </div>
      <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 tabular-nums">
        <dt className="text-muted-foreground">Nettonutzen</dt>
        <dd className="text-right font-mono text-popover-foreground">
          {formatEUR(p.x)}
        </dd>
        <dt className="text-muted-foreground">Aufwand</dt>
        <dd className="text-right font-mono text-popover-foreground">
          {formatScore(p.y)} / 10
        </dd>
        <dt className="text-muted-foreground">Stunden/Jahr</dt>
        <dd className="text-right font-mono text-popover-foreground">
          {formatNumber(p.z)}
        </dd>
        <dt className="text-muted-foreground">Status</dt>
        <dd className="text-right text-popover-foreground">
          {STATUS_CONFIG[p.status].labelDE}
        </dd>
      </dl>
    </div>
  );
}

export function BoardMatrix({ cases }: { cases: CaseSummary[] }) {
  const router = useRouter();
  const tokens = useThemeTokens();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const filtered = useMemo(
    () =>
      statusFilter === "all"
        ? cases
        : cases.filter((c) => c.status === statusFilter),
    [cases, statusFilter],
  );

  const points = useMemo(
    () => filtered.map(toPoint).filter((p): p is MatrixPoint => p !== null),
    [filtered],
  );

  // Cases ohne Bewertung (Vorfilter nicht bestanden) -- nach demselben Filter.
  const unscoredCount = filtered.length - points.length;

  // x-Domain so waehlen, dass die Quadranten-Hilfslinie bei 50.000 immer sichtbar
  // ist (Nettonutzen kann rechnerisch auch negativ sein -> 0 mit einschliessen).
  const xDomain = useMemo<[number, number]>(() => {
    const xs = points.map((p) => p.x);
    const min = Math.min(0, ...xs);
    const max = Math.max(QUADRANT_X, ...xs);
    const pad = Math.max(1, (max - min) * 0.08);
    return [min === 0 ? 0 : min - pad, max + pad];
  }, [points]);

  return (
    <div>
      {/* Status-Filter */}
      <div className="mb-5 flex flex-wrap items-end gap-4">
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
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_18rem]">
        {/* Matrix */}
        <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
          {points.length === 0 ? (
            <div className="flex h-[520px] items-center justify-center text-center">
              <p className="text-sm text-muted-foreground">
                Keine bewerteten Use Cases fuer diesen Filter.
              </p>
            </div>
          ) : (
            // Achsentitel liegen in eigenen HTML-Guttern AUSSERHALB des SVG
            // (linke Schiene + unteres Band). Sie koennen die recharts-Tick-
            // Labels -- die ausschliesslich im SVG-margin bzw. in der Achsen-
            // breite gezeichnet werden -- strukturell nicht ueberlappen:
            // disjunkte Layout-Boxen, unabhaengig von Label-Laenge/Viewport.
            <div className="grid grid-cols-[1.25rem_1fr] gap-x-1">
              {/* Linke Schiene: vertikaler y-Achsentitel (unter dem x-Band
                  ausgerichtet via pb-6). */}
              <div className="flex items-center justify-center pb-6">
                <span
                  className="text-xs font-medium tracking-wide whitespace-nowrap text-muted-foreground"
                  style={{
                    writingMode: "vertical-rl",
                    transform: "rotate(180deg)",
                  }}
                >
                  Machbarkeit
                </span>
              </div>

              <div>
                {/* relative traegt die absolut positionierten Quadranten-Ecklabels. */}
                <div className="relative h-[440px] w-full sm:h-[520px]">
                  {tokens !== null && (
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart
                        margin={{ top: 12, right: 18, bottom: 8, left: 4 }}
                      >
                        <CartesianGrid stroke={tokens.border} strokeDasharray="3 3" />
                        <XAxis
                          type="number"
                          dataKey="x"
                          name="Nettonutzen"
                          domain={xDomain}
                          height={30}
                          tickMargin={8}
                          tickFormatter={(v: number) => formatEUR(v)}
                          tick={{ fontSize: 11, fill: tokens.muted }}
                          stroke={tokens.border}
                          tickLine={{ stroke: tokens.border }}
                        />
                        <YAxis
                          type="number"
                          dataKey="y"
                          name="Machbarkeit"
                          // Invertiert via reversed (eine absteigende Domain wird von
                          // recharts wieder aufsteigend normalisiert): oben = niedriger
                          // Aufwand-Score 2 = hohe Machbarkeit, unten = 10.
                          reversed
                          domain={[2, 10]}
                          tickCount={5}
                          width={40}
                          tickMargin={6}
                          tick={{ fontSize: 11, fill: tokens.muted }}
                          stroke={tokens.border}
                          tickLine={{ stroke: tokens.border }}
                        />
                        <ZAxis
                          type="number"
                          dataKey="z"
                          range={[60, 400]}
                          name="Stunden/Jahr"
                        />
                        <Tooltip
                          content={<MatrixTooltip />}
                          cursor={{ strokeDasharray: "3 3", stroke: tokens.muted }}
                        />
                        {/* Quadranten-Hilfslinien (siehe QUADRANT_X-Kommentar). */}
                        <ReferenceLine
                          x={QUADRANT_X}
                          stroke={tokens.muted}
                          strokeDasharray="4 4"
                          strokeOpacity={0.5}
                        />
                        <ReferenceLine
                          y={QUADRANT_Y}
                          stroke={tokens.muted}
                          strokeDasharray="4 4"
                          strokeOpacity={0.5}
                        />
                        <Scatter
                          data={points}
                          onClick={(node: unknown) => {
                            const id = (node as { payload?: MatrixPoint })?.payload
                              ?.id;
                            if (id) router.push(`/cases/${id}`);
                          }}
                          className="cursor-pointer"
                        >
                          {points.map((p) => (
                            <Cell
                              key={p.id}
                              fill={tokens[p.zone]}
                              fillOpacity={0.75}
                              stroke={tokens[p.zone]}
                            />
                          ))}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  )}

                  {/* Quadranten-Ecklabels: dezent an den Ecken der Plotflaeche.
                      Naeherung -- sie markieren die vier Quadranten, die die
                      Hilfslinien aufspannen (oben = hohe Machbarkeit). Positionen
                      an die Margins + YAxis-Breite (links ~44px) angepasst. */}
                  <div className="pointer-events-none absolute inset-0 hidden select-none text-[10px] font-medium tracking-wide text-muted-foreground/70 uppercase sm:block">
                    <span className="absolute top-2 left-14">Nice to have</span>
                    <span className="absolute top-2 right-6">Quick Wins</span>
                    <span className="absolute bottom-11 left-14">Vermeiden</span>
                    <span className="absolute right-6 bottom-11 text-right">
                      Strategische Wetten
                    </span>
                  </div>
                </div>

                {/* Unteres Band: x-Achsentitel. */}
                <p className="mt-1.5 text-center text-xs font-medium tracking-wide text-muted-foreground">
                  Erwarteter Nettonutzen / Jahr
                </p>
              </div>
            </div>
          )}

          {/* Achsen-Untertitel + Blasen-Legende */}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-1 text-xs text-muted-foreground">
            <span>Aufwand-Score 2–10, invertiert</span>
            <span>Blasengroesse = eingesparte Stunden/Jahr</span>
          </div>

          {unscoredCount > 0 && (
            <p className="mt-3 text-xs text-muted-foreground">
              {unscoredCount}{" "}
              {unscoredCount === 1 ? "Fall" : "Faelle"} ohne Bewertung (Vorfilter
              nicht bestanden).{" "}
              <Link
                href="/cases"
                className="font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-2 hover:decoration-[var(--ink)]"
              >
                In der Ideenliste ansehen
              </Link>
            </p>
          )}
        </div>

        {/* Erklaer-Panel: auf Mobile aufklappbar (natives details), auf lg
            daneben. */}
        <details
          open
          className="group h-fit rounded-xl border border-border bg-muted/30 p-4 text-sm sm:p-5"
        >
          <summary className="cursor-pointer list-none font-medium text-foreground marker:content-none">
            <span className="flex items-center justify-between gap-2">
              Wie liest sich diese Matrix?
              <ChevronDown
                aria-hidden
                className="size-4 text-muted-foreground transition-transform group-open:rotate-180"
              />
            </span>
          </summary>
          <dl className="mt-4 space-y-3 leading-relaxed text-muted-foreground">
            <div>
              <dt className="font-medium text-foreground">x-Achse</dt>
              <dd>
                Erwarteter Nettonutzen pro Jahr — theoretisches Potenzial x
                Nutzungsfaktor x Evidenzfaktor, abzueglich Lizenzkosten.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">y-Achse</dt>
              <dd>
                Machbarkeit — der Aufwand-Score (Komplexitaet 1–5 + Kosten 1–3 +
                Datenschutz 0–2) invertiert: je hoeher der Punkt, desto geringer
                der Umsetzungsaufwand.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">Blase</dt>
              <dd>Groesse = eingesparte Arbeitsstunden pro Jahr.</dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">Farbe</dt>
              <dd>
                <ul className="mt-1 space-y-1">
                  {(
                    ["LIKELY_WIN", "CALCULATED_RISK", "MARGINAL_GAIN"] as ZoneKey[]
                  ).map((z) => (
                    <li key={z} className="flex items-center gap-2">
                      <span
                        className={cn("size-2 rounded-full", ZONE_CONFIG[z].dot)}
                        aria-hidden
                      />
                      <span className={ZONE_CONFIG[z].text}>
                        {ZONE_CONFIG[z].labelDE}
                      </span>
                    </li>
                  ))}
                </ul>
              </dd>
            </div>
          </dl>
        </details>
      </div>
    </div>
  );
}
