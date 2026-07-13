import type { Metadata } from "next";

import { checkAuth, listCases, listSimilarityPairs } from "@/app/actions";
import { CasesTable } from "@/components/cases-table";
import { RetryButton } from "@/components/retry-button";
import type { CaseSummary, SimilarityPair } from "@/types/api";

export const metadata: Metadata = {
  title: "Ideenliste | AECT",
};

// Immer frisch laden: nach einem Statuswechsel + Reload muss der neue Stand
// erscheinen (listCases nutzt cache: "no-store"; force-dynamic verhindert
// zusaetzlich statisches Prerendering dieser Route).
export const dynamic = "force-dynamic";

export default async function CasesPage() {
  let cases: CaseSummary[] = [];
  let loadError: string | null = null;
  let pairs: SimilarityPair[] = [];

  // Beide Calls parallel anstossen. Die Dedup-Paare sind optional: .catch()
  // wird sofort angehaengt (kein unhandled rejection), ein Fehlschlag laesst
  // die Kernliste unberuehrt -- die Ideenliste rendert dann nur ohne Badges.
  const pairsPromise = listSimilarityPairs().catch((e) => {
    console.error(
      "listSimilarityPairs fehlgeschlagen -- Ideenliste ohne Ähnlichkeits-Badges:",
      e,
    );
    return null;
  });

  try {
    cases = await listCases();
  } catch (e) {
    cases = [];
    loadError =
      e instanceof Error ? e.message : "Die Liste konnte nicht geladen werden.";
  }

  pairs = (await pairsPromise)?.pairs ?? [];

  // V4-P-Auth: der Statuswechsel in der Zeile ist Admin-only (read-only Badge
  // fuer Anonyme).
  const authenticated = await checkAuth();

  return (
    <main className="mx-auto max-w-5xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Ideenliste</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Alle eingereichten Use Cases
      </h1>
      <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Das gesamte Portfolio auf einen Blick: filtern nach Status und Zone,
        sortieren nach Nettonutzen oder Einreichdatum, den Lifecycle-Status
        direkt in der Zeile setzen.
      </p>

      <div className="mt-8">
        {loadError !== null ? (
          <div
            role="alert"
            className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3.5 text-sm text-destructive"
          >
            <p>{loadError}</p>
            <div className="mt-3">
              <RetryButton />
            </div>
          </div>
        ) : (
          <CasesTable cases={cases} pairs={pairs} authenticated={authenticated} />
        )}
      </div>
    </main>
  );
}
