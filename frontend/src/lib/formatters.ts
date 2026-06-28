export function formatEUR(value: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("de-DE", {
    maximumFractionDigits: 0,
  }).format(value);
}

// Zonen-Semantik. Farben kommen aus den --zone-*-Tokens in globals.css
// (redaktionell entsaettigte Versionen, keine Alarmbanner). Die Klassenstrings
// sind literal, damit Tailwind sie beim Scan erfasst.
export const ZONE_CONFIG = {
  LIKELY_WIN: {
    labelDE: "Vielversprechend",
    summaryDE: "Klarer Wirkungshebel, geringes Umsetzungsrisiko.",
    dot: "bg-[var(--zone-win)]",
    text: "text-[var(--zone-win-fg)]",
    surface: "border-[var(--zone-win-border)] bg-[var(--zone-win-surface)]",
    bar: "bg-[var(--zone-win)]",
  },
  CALCULATED_RISK: {
    labelDE: "Kalkuliertes Risiko",
    summaryDE: "Tragfähig, aber an Bedingungen und Aufwand geknüpft.",
    dot: "bg-[var(--zone-risk)]",
    text: "text-[var(--zone-risk-fg)]",
    surface: "border-[var(--zone-risk-border)] bg-[var(--zone-risk-surface)]",
    bar: "bg-[var(--zone-risk)]",
  },
  MARGINAL_GAIN: {
    labelDE: "Geringer Nutzen",
    summaryDE: "Nutzen steht in keinem klaren Verhältnis zum Aufwand.",
    dot: "bg-[var(--zone-gain)]",
    text: "text-[var(--zone-gain-fg)]",
    surface: "border-[var(--zone-gain-border)] bg-[var(--zone-gain-surface)]",
    bar: "bg-[var(--zone-gain)]",
  },
} as const;

export type ZoneKey = keyof typeof ZONE_CONFIG;
