import type { Metadata } from "next";
import Link from "next/link";

import {
  checkAuth,
  getArchitectureSketch,
  listCases,
  listMonitoringEntries,
  listSimilarityPairs,
} from "@/app/actions";
import { CaseStatusControl } from "@/components/case-status-control";
import { MonitoringTimeline } from "@/components/monitoring-timeline";
import { SimilarCasesPanel } from "@/components/similar-cases-panel";
import { SketchView } from "@/components/sketch-view";
import { StatusBadge, ZoneBadge } from "@/components/status-badge";
import { formatEUR } from "@/lib/formatters";
import type {
  ArchitectureSketchResponse,
  CaseSummary,
  MonitoringEntry,
  SimilarityPair,
} from "@/types/api";

export const metadata: Metadata = {
  title: "Fall-Detail | AECT",
};

// Immer frisch (wie /cases, /board): nach Statuswechsel/neuer Notiz + Reload
// muss der neue Stand erscheinen.
export const dynamic = "force-dynamic";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}

// Kleiner Kennzahlen-Block im Kopf (Nettonutzen, Aufwand).
function HeadStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p className="stat-value mt-1 text-lg text-foreground">{value}</p>
    </div>
  );
}

function NotFound({ id }: { id: string }) {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
      <p className="eyebrow">Fall-Detail</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Use Case nicht gefunden
      </h1>
      <p className="mt-4 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Zum angefragten Fall{" "}
        <span className="font-mono text-foreground">{id}</span> gibt es keinen
        Eintrag. Möglicherweise wurde er gelöscht.
      </p>
      <Link
        href="/cases"
        className="mt-4 inline-block text-sm font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
      >
        Zurück zur Ideenliste
      </Link>
    </main>
  );
}

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // V4-P-Auth: Kopf (Zone/Nutzen/Aufwand/Status) ist read-only public. Die
  // Admin-Panels (Status wechseln, Aehnlichkeit, Skizze, Monitoring) laden und
  // rendern nur fuer angemeldete Admins -- ihre Endpoints sind require_admin.
  const authenticated = await checkAuth();

  // GET /cases/{id} als Detail-Endpoint existiert nicht -- CaseSummary aus der
  // Liste (public) reicht fuer den Kopf.
  let cases: CaseSummary[] = [];
  let loadError: string | null = null;
  try {
    cases = await listCases();
  } catch (e) {
    loadError =
      e instanceof Error ? e.message : "Die Liste konnte nicht geladen werden.";
  }

  if (loadError !== null) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
        <p className="eyebrow">Fall-Detail</p>
        <p
          role="alert"
          className="mt-4 rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {loadError}
        </p>
      </main>
    );
  }

  const found = cases.find((c) => c.id === id);
  if (found === undefined) {
    return <NotFound id={id} />;
  }

  // Admin-Panels nur fuer Angemeldete laden -- fuer Anonyme wuerden die
  // require_admin-Endpoints ohnehin 401 liefern (kein 401-Rauschen im Log).
  let entries: MonitoringEntry[] = [];
  let timelineError: string | null = null;
  let similarityPairs: SimilarityPair[] = [];
  let initialSketch: ArchitectureSketchResponse | null = null;

  if (authenticated) {
    // Monitoring erst laden, wenn der Fall existiert (sonst 404 vom Backend).
    try {
      entries = await listMonitoringEntries(id);
    } catch (e) {
      timelineError =
        e instanceof Error
          ? e.message
          : "Die Monitoring-Einträge konnten nicht geladen werden.";
    }

    // Aehnlichkeits-Paare optional laden (kein Per-Case-Endpoint -- volle Liste,
    // auf diese id gefiltert). Fehlschlag = kein Panel, kein Blocker.
    try {
      similarityPairs = (await listSimilarityPairs()).pairs;
    } catch (e) {
      console.error(
        "listSimilarityPairs fehlgeschlagen -- Detail ohne Aehnlichkeits-Panel:",
        e,
      );
    }

    // Persistierte Architektur-Skizze optional laden (P13). null = nie erzeugt.
    try {
      initialSketch = await getArchitectureSketch(id);
    } catch (e) {
      console.error(
        "getArchitectureSketch fehlgeschlagen -- Detail ohne persistierte Skizze:",
        e,
      );
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-6">
      {/* --- Kopf --- */}
      <p className="eyebrow">Fall-Detail</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        {found.title}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {found.department} · Eingereicht am {formatDate(found.submitted_at)}
      </p>

      <div className="mt-6 rounded-xl border border-border bg-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-center gap-2">
            <span className="eyebrow">Zone</span>
            <ZoneBadge zone={found.zone} />
          </div>
          <HeadStat
            label="Nettonutzen"
            value={
              found.net_expected_benefit_eur === null
                ? "—"
                : formatEUR(found.net_expected_benefit_eur)
            }
          />
          <HeadStat
            label="Aufwand"
            value={
              found.composite_total === null
                ? "—"
                : `${found.composite_total} / 10`
            }
          />
        </div>
        <div className="mt-5 border-t border-border pt-4">
          <p className="eyebrow mb-2">Status</p>
          {authenticated ? (
            <CaseStatusControl caseId={found.id} initialStatus={found.status} />
          ) : (
            // Anonym: Status read-only (kein Wechsel-Select).
            <StatusBadge status={found.status} />
          )}
        </div>
      </div>

      {authenticated ? (
        <>
          {/* --- Aehnliche Use Cases (P12/C): rendert sich selbst nur, wenn
               Paare fuer diese id existieren (sonst null, kein Leerraum). --- */}
          <SimilarCasesPanel caseId={found.id} pairs={similarityPairs} />

          {/* --- Architektur-Skizze (P13): On-Demand-Graph, client-seitig via
               mermaid gerendert. Zustaende in SketchView. --- */}
          <SketchView caseId={found.id} initialSketch={initialSketch} />

          {/* --- Monitoring-Zeitleiste --- */}
          <div className="mt-10">
            {timelineError !== null ? (
              <p
                role="alert"
                className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
              >
                {timelineError}
              </p>
            ) : (
              <MonitoringTimeline caseId={found.id} initialEntries={entries} />
            )}
          </div>
        </>
      ) : (
        // Anonym: read-only Fall-Detail. Aehnlichkeit, Skizze und Monitoring
        // sind Admin-Ansichten und bleiben ausgeblendet.
        <p className="mt-8 rounded-xl border border-border bg-muted/40 px-4 py-3.5 text-sm text-muted-foreground">
          Weitere Ansichten (Ähnlichkeit, Architektur-Skizze, Monitoring) sowie
          der Statuswechsel sind angemeldeten Admins vorbehalten.{" "}
          <Link
            href="/login"
            className="font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
          >
            Admin-Login
          </Link>
        </p>
      )}
    </main>
  );
}
