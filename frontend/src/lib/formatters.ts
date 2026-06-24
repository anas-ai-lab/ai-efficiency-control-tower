export function formatEUR(value: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export const ZONE_CONFIG = {
  LIKELY_WIN: {
    labelDE: "Vielversprechend",
    badgeClass:
      "bg-green-100 text-green-800 border border-green-300 font-semibold",
  },
  CALCULATED_RISK: {
    labelDE: "Kalkuliertes Risiko",
    badgeClass:
      "bg-yellow-100 text-yellow-800 border border-yellow-300 font-semibold",
  },
  MARGINAL_GAIN: {
    labelDE: "Geringer Nutzen",
    badgeClass:
      "bg-red-100 text-red-800 border border-red-300 font-semibold",
  },
} as const;

export type ZoneKey = keyof typeof ZONE_CONFIG;
