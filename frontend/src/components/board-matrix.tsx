"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
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
import {
  computeAxisTicks,
  computeNiceDomainMax,
  formatAxisTickValue,
} from "@/lib/board-format";
import { ZONE_CONFIG, type ZoneKey } from "@/lib/formatters";
import { STATUS_CONFIG } from "@/lib/status";
import { readEnumParam, useFilterParams } from "@/lib/use-filter-params";
import { useFormat } from "@/lib/use-format";
import { ActiveFilters, EmptyResult } from "@/components/filter-bar";
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
  "rejected",
  "implemented",
];

// Filter-State in den URL-SearchParams (lib/use-filter-params), nicht in
// useState -- gleiches Muster wie Ideenliste und Monitoring.
const FILTER_KEYS = ["status"] as const;

// Machbarkeits-Mittellinie: y = 5 ist die Mitte der Composite-Skala
// (Aufwand-Score 1-9, zones.py _COMPOSITE_MIN/MAX). Reine Lese-Hilfslinie,
// KEINE Geschaeftsregel -- die Triage-Zone transportiert die Punktfarbe.
// Ein Gegenstueck auf der x-Achse gibt es bewusst nicht mehr: bei realer
// Wertverteilung (ueberwiegend fuenfstellige Nettonutzen) lagen praktisch alle
// Punkte auf einer Seite der frueheren 50.000-EUR-Linie, womit drei der vier
// aufgespannten Quadranten dauerhaft leer blieben.
const QUADRANT_Y = 5;

// Ab dieser Achsengrenze werden die Ticks in Millionen verkuerzt; darunter
// bleibt der volle EUR-Betrag lesbar.
const COMPACT_TICK_THRESHOLD = 1_000_000;

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
  y: number; // composite_total (Aufwand-Score 1-9)
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
  return <TooltipBody p={p} />;
}

function TooltipBody({ p }: { p: MatrixPoint }) {
  const t = useTranslations("board");
  const tz = useTranslations("zones");
  const ts = useTranslations("status");
  const fmt = useFormat();
  const zone = ZONE_CONFIG[p.zone as ZoneKey];
  return (
    <div className="max-w-[16rem] rounded-lg border border-border bg-popover px-3 py-2.5 text-xs shadow-md">
      <p className="line-clamp-2 font-medium text-popover-foreground">
        {p.title}
      </p>
      <p className="mt-0.5 text-muted-foreground">{p.department}</p>
      <div className="mt-2 flex items-center gap-1.5">
        <span className={cn("size-1.5 rounded-full", zone.dot)} aria-hidden />
        <span className={cn("font-medium", zone.text)}>
          {tz(`${p.zone}.label`)}
        </span>
      </div>
      <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 tabular-nums">
        <dt className="text-muted-foreground">{t("tipNet")}</dt>
        <dd className="text-right font-mono text-popover-foreground">
          {fmt.eur(p.x)}
        </dd>
        <dt className="text-muted-foreground">{t("tipEffort")}</dt>
        <dd className="text-right font-mono text-popover-foreground">
          {fmt.score1(p.y)} / 9
        </dd>
        <dt className="text-muted-foreground">{t("tipHours")}</dt>
        <dd className="text-right font-mono text-popover-foreground">
          {fmt.number(p.z)}
        </dd>
        <dt className="text-muted-foreground">{t("tipStatus")}</dt>
        <dd className="text-right text-popover-foreground">{ts(p.status)}</dd>
      </dl>
    </div>
  );
}

export function BoardMatrix({ cases }: { cases: CaseSummary[] }) {
  const t = useTranslations("board");
  const ts = useTranslations("status");
  const tz = useTranslations("zones");
  const fmt = useFormat();
  const locale = useLocale();
  const router = useRouter();
  const tokens = useThemeTokens();
  const tf = useTranslations("filters");
  const filters = useFilterParams(FILTER_KEYS);
  const statusFilter = readEnumParam(filters.get("status"), STATUS_ORDER);

  const filtered = useMemo(
    () =>
      statusFilter === null
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

  // x-Achse: Obergrenze auf die naechste runde Zahl ueber dem hoechsten Wert,
  // Untergrenze 0 (Nettonutzen kann rechnerisch negativ sein -> dann der
  // kleinste Wert). Datenbasis sind ALLE Cases, nicht die gefilterte
  // Teilmenge: eine Achse, die bei jedem Filterklick neu skaliert, veraendert
  // die optische Distanz zwischen zwei Punkten, ohne dass sich deren Werte
  // geaendert haben -- und verzerrt damit genau die Portfolio-Einordnung, fuer
  // die das Chart da ist.
  const { xDomain, xTicks } = useMemo(() => {
    const xs = cases
      .map((c) => c.net_expected_benefit_eur)
      .filter((v): v is number => v !== null);
    const max = computeNiceDomainMax(Math.max(0, ...xs));
    return {
      xDomain: [Math.min(0, ...xs), max] as [number, number],
      xTicks: computeAxisTicks(max),
    };
  }, [cases]);

  return (
    <div>
      {/* Status-Filter -- steht immer, unabhaengig vom Ergebnis. */}
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="eyebrow">{t("status")}</span>
          <Select
            // "all" ist Anzeige-Wert fuer "kein Param"; in die URL wandert er nie.
            value={statusFilter ?? "all"}
            onValueChange={(v) => filters.set("status", v === "all" ? null : v)}
          >
            <SelectTrigger size="sm" className="w-[10rem]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allStatus")}</SelectItem>
              {STATUS_ORDER.map((s) => (
                <SelectItem key={s} value={s}>
                  <span
                    className={cn(
                      "size-1.5 rounded-full",
                      STATUS_CONFIG[s].dot,
                    )}
                    aria-hidden
                  />
                  {ts(s)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
      </div>

      <ActiveFilters
        chips={
          statusFilter !== null
            ? [{ key: "status", label: t("status"), value: ts(statusFilter) }]
            : []
        }
        resultLabel={tf("results", {
          count: filtered.length,
          total: cases.length,
        })}
        onRemove={(key) => filters.remove(key as (typeof FILTER_KEYS)[number])}
        onReset={filters.reset}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_18rem]">
        {/* Matrix */}
        <div className="min-w-0 rounded-xl border border-border bg-card p-4 sm:p-5">
          {points.length === 0 ? (
            // Empty-State im Ergebnisbereich (im Matrix-Rahmen), mit Rueckweg,
            // sobald ein Filter aktiv ist.
            <div className="flex h-[520px] items-center justify-center">
              <EmptyResult
                message={t("emptyFiltered")}
                onReset={filters.hasActive ? filters.reset : undefined}
              />
            </div>
          ) : (
            // Achsentitel liegen in eigenen HTML-Guttern AUSSERHALB des SVG
            // (linke Schiene + unteres Band). Sie koennen die recharts-Tick-
            // Labels -- die ausschliesslich im SVG-margin bzw. in der Achsen-
            // breite gezeichnet werden -- strukturell nicht ueberlappen:
            // disjunkte Layout-Boxen, unabhaengig von Label-Laenge/Viewport.
            <div className="overflow-x-auto">
              <div className="grid min-w-[42rem] grid-cols-[1.25rem_1fr] gap-x-1 md:min-w-0">
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
                    {t("yAxisTitle")}
                  </span>
                </div>

                <div>
                  <div className="h-[440px] w-full sm:h-[520px]">
                    {tokens !== null && (
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart
                          margin={{ top: 12, right: 18, bottom: 8, left: 4 }}
                        >
                          <CartesianGrid
                            stroke={tokens.border}
                            strokeDasharray="3 3"
                          />
                          <XAxis
                            type="number"
                            dataKey="x"
                            name="Nettonutzen"
                            domain={xDomain}
                            ticks={xTicks}
                            height={30}
                            tickMargin={8}
                            // Millionen-Kurzform erst, wenn die Achse selbst dort
                            // liegt -- bei fuenfstelligen Portfolios waere "0,1 Mio"
                            // schlechter lesbar als der volle Betrag.
                            tickFormatter={(v: number) =>
                              xDomain[1] >= COMPACT_TICK_THRESHOLD
                                ? t("xAxisTickCompact", {
                                    value: formatAxisTickValue(v, locale),
                                  })
                                : fmt.eur(v)
                            }
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
                            // Aufwand-Score 1 = hohe Machbarkeit, unten = 9.
                            reversed
                            domain={[1, 9]}
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
                            cursor={{
                              strokeDasharray: "3 3",
                              stroke: tokens.muted,
                            }}
                          />
                          {/* Machbarkeits-Mittellinie (siehe QUADRANT_Y-Kommentar). */}
                          <ReferenceLine
                            y={QUADRANT_Y}
                            stroke={tokens.muted}
                            strokeDasharray="4 4"
                            strokeOpacity={0.5}
                          />
                          <Scatter
                            data={points}
                            onClick={(node: unknown) => {
                              const id = (node as { payload?: MatrixPoint })
                                ?.payload?.id;
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
                  </div>

                  {/* Unteres Band: x-Achsentitel. */}
                  <p className="mt-1.5 text-center text-xs font-medium tracking-wide text-muted-foreground">
                    {t("xAxisTitle")}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Horizontale Zonenfarb-Legende -- gleiche Farbquelle (ZONE_CONFIG)
              wie die vertikale Liste im "How to read"-Panel, dort bleibt sie
              zusaetzlich bestehen. */}
          <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs">
            {(
              ["LIKELY_WIN", "CALCULATED_RISK", "MARGINAL_GAIN"] as ZoneKey[]
            ).map((z) => (
              <div key={z} className="flex items-center gap-1.5">
                <span
                  className={cn("size-2 rounded-full", ZONE_CONFIG[z].dot)}
                  aria-hidden
                />
                <span className={ZONE_CONFIG[z].text}>{tz(`${z}.label`)}</span>
              </div>
            ))}
          </div>

          {/* Achsen-Untertitel + Blasen-Legende */}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-1 text-xs text-muted-foreground">
            <span>{t("effortScoreNote")}</span>
            <span>{t("bubbleNote")}</span>
          </div>

          {unscoredCount > 0 && (
            <p className="mt-3 text-xs text-muted-foreground">
              {t("unscored", { count: unscoredCount })}{" "}
              <Link
                href="/cases"
                className="font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-2 hover:decoration-[var(--ink)]"
              >
                {t("viewInList")}
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
              {t("howToRead")}
              <ChevronDown
                aria-hidden
                className="size-4 text-muted-foreground transition-transform group-open:rotate-180"
              />
            </span>
          </summary>
          <dl className="mt-4 space-y-3 leading-relaxed text-muted-foreground">
            <div>
              <dt className="font-medium text-foreground">{t("xAxis")}</dt>
              <dd>{t("xAxisDesc")}</dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">{t("yAxis")}</dt>
              <dd>{t("yAxisDesc")}</dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">{t("bubble")}</dt>
              <dd>{t("bubbleDesc")}</dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">{t("color")}</dt>
              <dd>
                <ul className="mt-1 space-y-1">
                  {(
                    [
                      "LIKELY_WIN",
                      "CALCULATED_RISK",
                      "MARGINAL_GAIN",
                    ] as ZoneKey[]
                  ).map((z) => (
                    <li key={z} className="flex items-center gap-2">
                      <span
                        className={cn(
                          "size-2 rounded-full",
                          ZONE_CONFIG[z].dot,
                        )}
                        aria-hidden
                      />
                      <span className={ZONE_CONFIG[z].text}>
                        {tz(`${z}.label`)}
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
