import type { Metadata } from "next";

import { listCases } from "@/app/actions";
import { BoardMatrix } from "@/components/board-matrix";
import type { CaseSummary } from "@/types/api";

export const metadata: Metadata = {
  title: "Board | AECT",
};

// Immer frisch laden (wie /cases): nach Statuswechsel + Reload muss der neue
// Stand erscheinen. listCases nutzt cache: "no-store"; force-dynamic verhindert
// zusaetzlich statisches Prerendering dieser Route.
export const dynamic = "force-dynamic";

export default async function BoardPage() {
  let cases: CaseSummary[] = [];
  let loadError: string | null = null;
  try {
    cases = await listCases();
  } catch (e) {
    cases = [];
    loadError =
      e instanceof Error ? e.message : "Die Liste konnte nicht geladen werden.";
  }

  return (
    <main className="mx-auto max-w-6xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Board</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Portfolio-Matrix: Nutzen gegen Machbarkeit
      </h1>
      <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Jeder bewertete Use Case als Punkt: erwarteter Nettonutzen (x),
        Machbarkeit (y, invertierter Aufwand-Score) und eingesparte Stunden pro
        Jahr (Blasengroesse). Die Farbe zeigt die Triage-Zone. Klick auf einen
        Punkt oeffnet den Fall.
      </p>

      <div className="mt-8">
        {loadError !== null ? (
          <p
            role="alert"
            className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
          >
            {loadError}
          </p>
        ) : (
          <BoardMatrix cases={cases} />
        )}
      </div>
    </main>
  );
}
