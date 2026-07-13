// CI-faehiger Paritaets-Check (V4.1-S6): vergleicht die Schluesselstruktur von
// messages/de.json und messages/en.json rekursiv. Fehlt ein Schluessel in einer
// Sprache -- oder ist ein Blatt vs. Objekt unterschiedlich getypt -- schlaegt der
// Check fehl (Exit 1). Fuehrt fail-loud statt stiller Default-Uebersetzung.
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

// Sammelt alle Blattpfade (dot-notation) eines verschachtelten Objekts.
function leafPaths(obj, prefix = "") {
  const out = [];
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      out.push(...leafPaths(value, path));
    } else {
      out.push(path);
    }
  }
  return out;
}

const de = load("de");
const en = load("en");

const deSet = new Set(leafPaths(de));
const enSet = new Set(leafPaths(en));

const missingInEn = [...deSet].filter((p) => !enSet.has(p)).sort();
const missingInDe = [...enSet].filter((p) => !deSet.has(p)).sort();

if (missingInEn.length === 0 && missingInDe.length === 0) {
  console.log(`i18n parity OK — ${deSet.size} keys in de/en.`);
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
process.exit(1);
