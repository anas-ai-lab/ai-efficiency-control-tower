// CI-faehiger Verwendungs-Check: sammelt alle im Code referenzierten
// Message-Keys und prueft sie gegen messages/de.json UND messages/en.json.
// Richtung Code -> Katalog, komplementaer zu check-i18n-parity.mjs (Katalog ->
// Katalog). Ein Katalog-Cleanup, der einen noch referenzierten Schluessel
// entfernt, schlaegt hier fehl (Exit 1) -- next-intl selbst wirft nicht, es
// rendert den Pfad als Text.
//
// Warum AST statt Grep: der Namespace haengt an der Bindung
// (const t = useTranslations("result")), und dieselbe Variable kann in einer
// Datei zwei Namespaces tragen (case-result.tsx: "result.scoring" in der einen
// Funktion, "result" in der naechsten). Ein dateiweiter Grep-Map wuerde falsch
// aufloesen. Der TypeScript-Compiler ist ohnehin devDependency.
//
// Aufruf: node scripts/check-i18n-usage.mjs  (Teil von npm run i18n:check)

import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";
import ts from "typescript";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const srcDir = join(root, "src");
const messagesDir = join(root, "messages");

// Methoden am Translator, deren erstes Argument ein Message-Key ist.
// .has() bewusst NICHT: das ist eine Existenz-Probe, ein fehlender Key dort
// ist erlaubt.
const KEY_METHODS = new Set(["rich", "markup", "raw"]);

function collectSourceFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...collectSourceFiles(full));
    } else if (/\.tsx?$/.test(entry.name) && !/\.d\.ts$/.test(entry.name)) {
      out.push(full);
    }
  }
  return out;
}

// Sammelt alle Blattpfade (dot-notation) und alle Zwischenknoten-Pfade.
function catalogPaths(obj, prefix = "", leaves = new Set(), nodes = new Set()) {
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      nodes.add(path);
      catalogPaths(value, path, leaves, nodes);
    } else {
      leaves.add(path);
    }
  }
  return { leaves, nodes };
}

// Schaelt as-Casts, Klammern und await ab: (await getTranslations("x")) as T
function unwrap(node) {
  let current = node;
  for (;;) {
    if (
      ts.isAwaitExpression(current) ||
      ts.isParenthesizedExpression(current) ||
      ts.isAsExpression(current) ||
      ts.isNonNullExpression(current) ||
      ts.isSatisfiesExpression(current)
    ) {
      current = current.expression;
      continue;
    }
    return current;
  }
}

// Liefert den Namespace-String, wenn der Initializer ein Translator-Factory-
// Aufruf ist. useTranslations() ohne Argument -> "" (Root-Namespace).
function translatorNamespace(initializer) {
  if (!initializer) return undefined;
  const call = unwrap(initializer);
  if (!ts.isCallExpression(call)) return undefined;
  const callee = call.expression;
  if (!ts.isIdentifier(callee)) return undefined;
  if (callee.text !== "useTranslations" && callee.text !== "getTranslations") {
    return undefined;
  }
  const [arg] = call.arguments;
  if (arg === undefined) return "";
  if (ts.isStringLiteralLike(arg)) return arg.text;
  return undefined;
}

// Statische Key-Kandidaten eines Ausdrucks.
//   "a.b"                     -> exakter Key
//   `x.${v}`                  -> Praefix-Anforderung "x" (Zwischenknoten)
//   cond ? "a" : "b"          -> beide Zweige
function keyCandidates(node) {
  if (node === undefined) return [{ kind: "unresolved" }];
  const expr = unwrap(node);

  if (ts.isStringLiteralLike(expr) && !ts.isTemplateExpression(expr)) {
    return [{ kind: "exact", value: expr.text }];
  }
  if (ts.isConditionalExpression(expr)) {
    return [...keyCandidates(expr.whenTrue), ...keyCandidates(expr.whenFalse)];
  }
  if (ts.isTemplateExpression(expr)) {
    // Statischer Kopf bis zum ersten ${...}. `enums.country.${c}` -> Praefix
    // "enums.country" muss als Objektknoten existieren. Einzelne Mitglieder
    // kann dieser Check nicht pruefen -- der Wert ist erst zur Laufzeit da.
    const head = expr.head.text;
    const dot = head.lastIndexOf(".");
    if (dot <= 0) return [{ kind: "unresolved" }];
    return [{ kind: "prefix", value: head.slice(0, dot) }];
  }
  return [{ kind: "unresolved" }];
}

const usages = [];
const unresolved = [];

function scan(sourceFile) {
  const file = relative(root, sourceFile.fileName);

  // env: Map<variablenName, namespace>. Wird pro Scope kopiert, damit eine
  // innere Bindung die aeussere nur lokal ueberschreibt.
  function walk(node, env) {
    let scopeEnv = env;

    // Bindungen dieses Scopes zuerst einsammeln, dann Kinder besuchen. Reicht
    // fuer const-Bindungen am Funktionskopf -- die Form, die next-intl vorgibt.
    if (ts.isBlock(node) || ts.isSourceFile(node) || ts.isCaseClause(node)) {
      for (const stmt of node.statements) {
        if (!ts.isVariableStatement(stmt)) continue;
        for (const decl of stmt.declarationList.declarations) {
          if (!ts.isIdentifier(decl.name)) continue;
          const ns = translatorNamespace(decl.initializer);
          if (ns === undefined) continue;
          if (scopeEnv === env) scopeEnv = new Map(env);
          scopeEnv.set(decl.name.text, ns);
        }
      }
    }

    if (ts.isCallExpression(node)) {
      const callee = node.expression;
      let binding;
      if (ts.isIdentifier(callee)) {
        binding = scopeEnv.get(callee.text);
      } else if (
        ts.isPropertyAccessExpression(callee) &&
        ts.isIdentifier(callee.expression) &&
        KEY_METHODS.has(callee.name.text)
      ) {
        binding = scopeEnv.get(callee.expression.text);
      }

      if (binding !== undefined) {
        const line =
          sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile))
            .line + 1;
        for (const cand of keyCandidates(node.arguments[0])) {
          if (cand.kind === "unresolved") {
            unresolved.push({ file, line });
            continue;
          }
          usages.push({
            file,
            line,
            kind: cand.kind,
            path: binding ? `${binding}.${cand.value}` : cand.value,
          });
        }
      }
    }

    ts.forEachChild(node, (child) => walk(child, scopeEnv));
  }

  walk(sourceFile, new Map());
}

for (const file of collectSourceFiles(srcDir)) {
  scan(
    ts.createSourceFile(
      file,
      readFileSync(file, "utf8"),
      ts.ScriptTarget.Latest,
      /* setParentNodes */ true,
      file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS
    )
  );
}

const catalogs = {};
for (const locale of ["de", "en"]) {
  catalogs[locale] = catalogPaths(
    JSON.parse(readFileSync(join(messagesDir, `${locale}.json`), "utf8"))
  );
}

const missing = [];
for (const usage of usages) {
  for (const locale of ["de", "en"]) {
    const { leaves, nodes } = catalogs[locale];
    const found =
      usage.kind === "exact" ? leaves.has(usage.path) : nodes.has(usage.path);
    if (!found) missing.push({ ...usage, locale });
  }
}

if (unresolved.length > 0) {
  console.warn(
    `\nHinweis: ${unresolved.length} Translator-Aufruf(e) mit nicht statisch ` +
      `aufloesbarem Key -- nicht geprueft:`
  );
  for (const u of unresolved) console.warn(`  - ${u.file}:${u.line}`);
}

if (missing.length === 0) {
  const exact = usages.filter((u) => u.kind === "exact").length;
  console.log(
    `i18n usage OK — ${exact} exakte Keys + ${usages.length - exact} ` +
      `Praefixe aus dem Code in de/en vorhanden.`
  );
  process.exit(0);
}

console.error(`\nIm Code referenziert, aber im Katalog nicht vorhanden (${missing.length}):`);
for (const m of missing.sort((a, b) => a.path.localeCompare(b.path))) {
  const what = m.kind === "exact" ? "Key" : "Namespace-Praefix";
  console.error(`  - [${m.locale}] ${what} "${m.path}"  (${m.file}:${m.line})`);
}
process.exit(1);
