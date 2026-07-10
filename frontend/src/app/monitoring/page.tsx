import type { Metadata } from "next";
import Link from "next/link";

import { checkAuth, listCases } from "@/app/actions";
import { AdminGate } from "@/components/admin-gate";
import { StatusBadge, ZoneBadge } from "@/components/status-badge";
import { formatEUR } from "@/lib/formatters";
import type { CaseSummary } from "@/types/api";

export const metadata: Metadata = {
  title: "Monitoring | AECT",
};

// Immer frisch (wie /cases, /board): nach Statuswechsel + Reload muss die
// gefilterte Liste den neuen Stand zeigen.
export const dynamic = "force-dynamic";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}

export default async function MonitoringPage() {
  // V4-P-Auth: Monitoring ist ein Admin-Bereich -- ohne Anmeldung ausgeblendet.
  if (!(await checkAuth())) {
    return <AdminGate title="Monitoring" />;
  }

  let cases: CaseSummary[] = [];
  let loadError: string | null = null;
  try {
    cases = await listCases();
  } catch (e) {
    loadError =
      e instanceof Error ? e.message : "Die Liste konnte nicht geladen werden.";
  }

  // Nur freigegebene oder umgesetzte Faelle -- Monitoring beginnt nach der
  // Freigabe.
  const monitored = cases.filter(
    (c) => c.status === "approved" || c.status === "implemented",
  );

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Monitoring</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Freigegebene und umgesetzte Use Cases
      </h1>
      <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Manuell gepflegtes Monitoring: Status und Verlaufsnotizen pro
        freigegebenem Use Case — kein automatisches Tracking.
      </p>

      <div className="mt-8">
        {loadError !== null ? (
          <p
            role="alert"
            className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
          >
            {loadError}
          </p>
        ) : monitored.length === 0 ? (
          <div className="rounded-xl border border-border bg-card px-6 py-14 text-center">
            <p className="text-sm text-muted-foreground">
              Noch keine freigegebenen oder umgesetzten Use Cases. Freigaben
              erfolgen im Report oder in der Ideenliste.
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {monitored.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/cases/${c.id}`}
                  className="block rounded-xl border border-border bg-card p-5 outline-none transition-colors hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-ring/40"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="font-medium text-foreground">{c.title}</p>
                      <p className="mt-0.5 text-sm text-muted-foreground">
                        {c.department} · Eingereicht am{" "}
                        {formatDate(c.submitted_at)}
                      </p>
                    </div>
                    <StatusBadge status={c.status} />
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-border pt-3">
                    <div className="flex items-center gap-2">
                      <span className="eyebrow">Zone</span>
                      <ZoneBadge zone={c.zone} />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="eyebrow">Nettonutzen</span>
                      <span className="font-mono text-sm text-foreground tabular-nums">
                        {c.net_expected_benefit_eur === null
                          ? "—"
                          : formatEUR(c.net_expected_benefit_eur)}
                      </span>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
