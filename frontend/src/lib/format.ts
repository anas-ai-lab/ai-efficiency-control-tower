// Locale-abhaengige Zahl-/Datumsformatierung (V4.1-S6). Ersetzt die frueheren
// hart auf "de-DE" gepinnten Intl-Formatter: die aktive Locale (Cookie ->
// next-intl) bestimmt Tausender-/Dezimaltrenner und Datumsreihenfolge. Das
// EUR-Waehrungssymbol bleibt fix -- nur die Formatierung folgt der Sprache.
//
// bindFormat nimmt eine next-intl-Formatter-Instanz (useFormatter im Client,
// getFormatter im Server) und liefert benannte Helfer mit denselben Optionen
// wie zuvor -- so bleibt der Umbau an den Aufrufstellen minimal. Bewusst KEIN
// next-intl-Import hier: dann ist das Modul server- und client-sicher (der
// Client-Hook useFormat lebt in use-format.ts).

interface IntlFormatter {
  number(value: number, options?: Intl.NumberFormatOptions): string;
  dateTime(value: Date | number, options?: Intl.DateTimeFormatOptions): string;
}

const DATE_SHORT: Intl.DateTimeFormatOptions = {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
};

const DATE_TIME_MED: Intl.DateTimeFormatOptions = {
  dateStyle: "medium",
  timeStyle: "short",
};

export function bindFormat(f: IntlFormatter) {
  return {
    // Betrag in EUR, ohne Nachkommastellen. Symbol € fix, Trenner locale-abh.
    eur: (v: number) =>
      f.number(v, {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }),
    // Ganzzahl.
    number: (v: number) => f.number(v, { maximumFractionDigits: 0 }),
    // Score mit einer Nachkommastelle (Board-Aufwand).
    score1: (v: number) => f.number(v, { maximumFractionDigits: 1 }),
    // Anteil (0-1) als ganzzahlige Prozentangabe.
    percent: (v: number) =>
      f.number(v, { style: "percent", maximumFractionDigits: 0 }),
    // Anteil (0-1) als Prozent mit einer Nachkommastelle (Aehnlichkeit).
    percent1: (v: number) =>
      f.number(v, {
        style: "percent",
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      }),
    // Faktor mit zwei Nachkommastellen (Rechenweg).
    factor: (v: number) =>
      f.number(v, { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    // Kurzdatum (TT.MM.JJJJ bzw. locale-Aequivalent).
    dateShort: (v: Date | string | number) =>
      f.dateTime(typeof v === "string" ? new Date(v) : v, DATE_SHORT),
    // Datum + Uhrzeit (Monitoring-Zeitleiste).
    dateTime: (v: Date | string | number) =>
      f.dateTime(typeof v === "string" ? new Date(v) : v, DATE_TIME_MED),
  };
}

export type AppFormat = ReturnType<typeof bindFormat>;
