// Achsen-Mathematik der Portfolio-Matrix. Reine Funktionen, framework-frei --
// testbar ohne React-/next-intl-Kontext (src/lib/board-format.test.ts).
//
// Die X-Achse des Boards wird aus den Daten selbst skaliert statt auf einen
// festen Maximalwert gepinnt: bei einem Portfolio mit ueberwiegend
// fuenfstelligen Nettonutzen-Werten staucht eine feste Millionen-Achse die
// gesamte Punktwolke an den linken Rand. Damit die Achse trotzdem lesbar
// bleibt, wird das Maximum auf die naechste "runde" Zahl gehoben.

// Erlaubte Mantissen einer Achsengrenze bzw. eines Tick-Schritts, je
// Zehnerpotenz. Bewusst geschlossen: jede andere Rundung erzeugt Achsen-
// beschriftungen, die man nicht im Kopf ueberschlagen kann.
const NICE_STEPS = [1, 2, 2.5, 5, 10] as const;

// Luft ueber dem groessten Datenpunkt, damit die aeusserste Blase nicht am
// Achsenrand klebt.
const HEADROOM = 1.15;

// Portfolio ohne positiven Nettonutzen (leer, oder alle Werte <= 0): die Achse
// braucht trotzdem eine Skala. 100.000 EUR deckt den typischen Wertebereich
// eines Einzel-Cases ab, ohne bei spaeter eintreffenden Werten sofort wieder
// umzuspringen.
const FALLBACK_DOMAIN_MAX = 100_000;

// Kandidaten fuer die Anzahl der Tick-Intervalle, in Praeferenz-Reihenfolge.
// 5 bzw. 4 Intervalle ergeben 6 bzw. 5 Ticks -- fuer jede Stufe der
// NICE_STEPS-Folge geht genau eine der beiden Teilungen glatt auf.
const TICK_DIVISIONS = [5, 4];

// Relative Toleranz fuer Fliesskomma-Vergleiche (10 ** exponent trifft nicht
// jede Zehnerpotenz exakt).
const EPSILON = 1e-9;

function mantissa(value: number): number {
  return value / 10 ** Math.floor(Math.log10(value));
}

function isNiceStep(value: number): boolean {
  if (!(value > 0) || !Number.isFinite(value)) return false;
  const m = mantissa(value);
  return NICE_STEPS.some((step) => Math.abs(m - step) < EPSILON);
}

/**
 * Kleinste Zahl der Folge {1, 2, 2.5, 5, 10} x 10^n, die mindestens das
 * 1,15-fache des uebergebenen Hoechstwerts abdeckt.
 */
export function computeNiceDomainMax(maxValue: number): number {
  if (!Number.isFinite(maxValue) || maxValue <= 0) return FALLBACK_DOMAIN_MAX;
  const target = maxValue * HEADROOM;
  const magnitude = 10 ** Math.floor(Math.log10(target));
  for (const step of NICE_STEPS) {
    const candidate = step * magnitude;
    if (candidate >= target * (1 - EPSILON)) return candidate;
  }
  // Unerreichbar, solange NICE_STEPS mit 10 endet -- 10 x magnitude ist per
  // Konstruktion >= target.
  return 10 * magnitude;
}

/**
 * Tick-Liste von 0 bis domainMax als Vielfache eines runden Schritts.
 * `count` erzwingt eine bestimmte Tick-Anzahl; ohne Angabe wird die Teilung
 * gewaehlt, die einen runden Schritt ergibt (5 oder 6 Ticks).
 */
export function computeAxisTicks(domainMax: number, count?: number): number[] {
  if (!Number.isFinite(domainMax) || domainMax <= 0) return [0];
  const candidates = count === undefined ? TICK_DIVISIONS : [count - 1];
  const divisions =
    candidates.find((d) => d > 0 && isNiceStep(domainMax / d)) ?? candidates[0];
  const step = domainMax / divisions;
  return Array.from({ length: divisions + 1 }, (_, i) => i * step);
}

/**
 * Achsenwert in Millionen, locale-gerecht formatiert. Die Einheit selbst
 * kommt aus dem i18n-Katalog (`board.xAxisTickCompact`), nicht aus dieser
 * Funktion -- hier wird ausschliesslich die Zahl gebildet.
 */
export function formatAxisTickValue(value: number, locale: string): string {
  if (value === 0) return "0";
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(
    value / 1_000_000,
  );
}
