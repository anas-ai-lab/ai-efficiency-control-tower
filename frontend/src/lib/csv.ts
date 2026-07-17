import type { CaseSummaryView } from "@/types/api";
import { isAdminSummary } from "@/lib/case-view";
import { ZONE_CONFIG, type ZoneKey } from "@/lib/formatters";
import { STATUS_CONFIG } from "@/lib/status";

// CSV-Export der Ideenliste (D15). Ziel ist deutsches Excel:
//   - Trennzeichen Semikolon (de-Excel erwartet ";", nicht ",")
//   - UTF-8 mit BOM, damit Umlaute korrekt erkannt werden
//   - Zeilenende CRLF
//   - Zahlen mit Dezimal-KOMMA, ohne Tausenderpunkte (Rohwert bleibt maschinell
//     weiterverwendbar), leere Werte als leeres Feld -- nicht "—"
//   - Datum als ISO (YYYY-MM-DD): eindeutig und sortierbar
// Kein externes Paket -- reine String-Erzeugung.

const DELIMITER = ";";
const NEWLINE = "\r\n";
const BOM = "﻿";

// Grundspalten -- in jedem Export. Die Bewertungsspalten dahinter kommen nur in
// den Admin-Export (V4.1-S8): der anonymen Ideenliste liefert das Backend die
// Werte gar nicht, ein Export mit leeren Zone-/Nutzen-Spalten waere nur eine
// Einladung, sie fuer "noch nicht berechnet" zu halten.
const BASE_COLUMNS = ["id", "Titel", "Abteilung", "Eingereicht", "Status"] as const;
const ASSESSMENT_COLUMNS = [
  "Zone",
  "Nettonutzen EUR",
  "Aufwand (2-10)",
  "Stunden/Jahr",
] as const;

// Formel-Trigger am Feldanfang (OWASP CSV-Injection, H-038): Excel/LibreOffice
// werten ein Feld, das mit = + - @ oder Tab/CR beginnt, als Formel aus (bis hin
// zu DDE/RCE). Ausnahme: reine Zahlen (optional negativ, Dezimal-KOMMA) sind
// keine Formel und muessen maschinell weiterverwendbar bleiben -- ein legitimer
// negativer Nettonutzen (-1500,50) darf NICHT zu Text werden.
const FORMULA_TRIGGERS = new Set(["=", "+", "-", "@", "\t", "\r"]);
const PURE_NUMBER = /^-?\d+(,\d+)?$/;

function neutralizeFormula(value: string): string {
  if (
    value.length > 0 &&
    FORMULA_TRIGGERS.has(value[0]) &&
    !PURE_NUMBER.test(value)
  ) {
    return `'${value}`;
  }
  return value;
}

// Zuerst Formel-Trigger neutralisieren, dann quoten: ein Feld nur dann quoten,
// wenn es Semikolon, Anfuehrungszeichen oder einen Zeilenumbruch enthaelt.
// Innere Anfuehrungszeichen werden verdoppelt.
export function escapeCsvField(value: string): string {
  const safe = neutralizeFormula(value);
  if (
    safe.includes(DELIMITER) ||
    safe.includes('"') ||
    safe.includes("\n") ||
    safe.includes("\r")
  ) {
    return `"${safe.replace(/"/g, '""')}"`;
  }
  return safe;
}

// Rohwert mit Dezimal-KOMMA, ohne Tausenderpunkte. null/NaN -> leeres Feld.
function numberField(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "";
  return String(value).replace(".", ",");
}

// submitted_at (ISO-Zeitstempel) auf das Kalenderdatum in lokaler Zeitzone
// reduzieren -- konsistent mit der in der Tabelle angezeigten de-DE-Anzeige,
// ohne UTC-Verschiebung.
function isoDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function rowFor(c: CaseSummaryView, withAssessment: boolean): string[] {
  const base = [
    c.id,
    c.title,
    c.department,
    isoDate(c.submitted_at),
    STATUS_CONFIG[c.status].labelDE,
  ];
  if (!withAssessment || !isAdminSummary(c)) return base;
  return [
    ...base,
    c.zone === null ? "" : ZONE_CONFIG[c.zone as ZoneKey].labelDE,
    numberField(c.net_expected_benefit_eur),
    numberField(c.composite_total),
    numberField(c.hours_per_year),
  ];
}

// Erzeugt den vollstaendigen CSV-Text (inkl. BOM) fuer die uebergebene --
// bereits gefilterte und sortierte -- Sicht. Reihenfolge der Zeilen bleibt
// unveraendert. withAssessment: Bewertungsspalten mitschreiben (Admin-Export).
export function buildCasesCsv(
  cases: CaseSummaryView[],
  withAssessment: boolean,
): string {
  const columns = withAssessment
    ? [...BASE_COLUMNS, ...ASSESSMENT_COLUMNS]
    : BASE_COLUMNS;
  const lines = [columns.join(DELIMITER)];
  for (const c of cases) {
    lines.push(rowFor(c, withAssessment).map(escapeCsvField).join(DELIMITER));
  }
  return BOM + lines.join(NEWLINE) + NEWLINE;
}

// Dateiname aect-ideenliste-YYYY-MM-DD.csv mit dem heutigen Datum.
export function csvFilename(now: Date = new Date()): string {
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `aect-ideenliste-${y}-${m}-${day}.csv`;
}

// Loest den Download client-seitig aus (Blob + Object-URL + Klick).
export function downloadCasesCsv(
  cases: CaseSummaryView[],
  withAssessment: boolean,
): void {
  const csv = buildCasesCsv(cases, withAssessment);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = csvFilename();
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
