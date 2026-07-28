// CI-faehiger Paritaets-Check (V4.1-S6): vergleicht die Schluesselstruktur von
// messages/de.json und messages/en.json rekursiv. Fehlt ein Schluessel in einer
// Sprache -- oder ist ein Blatt vs. Objekt unterschiedlich getypt -- schlaegt der
// Check fehl (Exit 1). Fuehrt fail-loud statt stiller Default-Uebersetzung.
//
// Zusaetzlich zur Struktur werden die Werte geprueft:
//   - leerer oder nicht-string Wert -> fail (Exit 1). Ein Key, der weg soll,
//     wird entfernt, nicht auf "" gesetzt.
//   - in de und en identisch UND laenger als drei Woerter -> Warnung, kein
//     fail: kurze Werte sind legitim gleich, ganze Saetze selten.
//
// Aufruf: node scripts/check-i18n-parity.mjs  (npm run i18n:check)

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const messagesDir = join(here, "..", "messages");

function load(locale) {
  return JSON.parse(readFileSync(join(messagesDir, `${locale}.json`), "utf8"));
}

// Sammelt alle Blattpfade (dot-notation) eines verschachtelten Objekts auf
// ihren Wert. Map statt Array: die Werte braucht der Leer- und der
// Gleichheits-Check weiter unten.
function leafEntries(obj, prefix = "", out = new Map()) {
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      leafEntries(value, path, out);
    } else {
      out.set(path, value);
    }
  }
  return out;
}

const deEntries = leafEntries(load("de"));
const enEntries = leafEntries(load("en"));

const missingInEn = [...deEntries.keys()].filter((p) => !enEntries.has(p)).sort();
const missingInDe = [...enEntries.keys()].filter((p) => !deEntries.has(p)).sort();

// Leerer Wert = fail. Ein Key, der nicht mehr gebraucht wird, gehoert entfernt,
// nicht auf "" gesetzt: next-intl rendert "" stillschweigend als Luecke im UI.
const empty = [];
for (const [locale, entries] of [
  ["de", deEntries],
  ["en", enEntries],
]) {
  for (const [path, value] of entries) {
    if (typeof value !== "string" || value.trim() === "") {
      empty.push({ locale, path, value });
    }
  }
}

// Identischer Wert in beiden Sprachen bei mehr als drei Woertern = Warnung,
// KEIN fail: kurze Werte (Eigennamen, Einheiten, "OK") sind legitim gleich,
// ganze Saetze deuten dagegen auf eine vergessene Uebersetzung hin.
const untranslated = [];
for (const [path, deValue] of deEntries) {
  const enValue = enEntries.get(path);
  if (typeof deValue !== "string" || deValue !== enValue) continue;
  if (deValue.trim().split(/\s+/).length <= 3) continue;
  untranslated.push({ path, value: deValue });
}

if (untranslated.length > 0) {
  console.warn(
    `\nHinweis: ${untranslated.length} Wert(e) in de/en identisch und laenger ` +
      `als drei Woerter -- moeglicherweise nicht uebersetzt:`
  );
  for (const u of untranslated.sort((a, b) => a.path.localeCompare(b.path))) {
    console.warn(`  - ${u.path}: "${u.value}"`);
  }
}

if (missingInEn.length === 0 && missingInDe.length === 0 && empty.length === 0) {
  console.log(`i18n parity OK — ${deEntries.size} keys in de/en.`);
  process.exit(0);
}

if (missingInEn.length > 0) {
  console.error(`\nFehlt in en.json (${missingInEn.length}):`);
  for (const p of missingInEn) console.error(`  - ${p}`);
}
if (missingInDe.length > 0) {
  console.error(`\nFehlt in de.json (${missingInDe.length}):`);
  for (const p of missingInDe) console.error(`  - ${p}`);
}
if (empty.length > 0) {
  console.error(`\nLeerer oder nicht-string Wert (${empty.length}):`);
  for (const e of empty.sort((a, b) => a.path.localeCompare(b.path))) {
    console.error(`  - [${e.locale}] ${e.path}: ${JSON.stringify(e.value)}`);
  }
}
process.exit(1);
