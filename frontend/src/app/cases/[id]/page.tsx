import type { Metadata } from "next";
import Link from "next/link";

import {
  checkAuth,
  getArchitectureSketch,
  getCaseDetail,
  listMonitoringEntries,
  listSimilarityPairs,
} from "@/app/actions";
import { CaseAdminActions } from "@/components/case-admin-actions";
import { CaseInputs } from "@/components/case-inputs";
import { CaseReport } from "@/components/case-report";
import { CaseResult } from "@/components/case-result";
import { CaseStatusControl } from "@/components/case-status-control";
import { MonitoringTimeline } from "@/components/monitoring-timeline";
import { SimilarCasesPanel } from "@/components/similar-cases-panel";
import { SketchView } from "@/components/sketch-view";
import { StatusBadge, ZoneBadge } from "@/components/status-badge";
import type {
  ArchitectureSketchResponse,
  CaseDetailResponse,
  MonitoringEntry,
  SimilarityPair,
} from "@/types/api";

export const metadata: Metadata = {
  title: "Fall-Detail | AECT",
};

// Immer frisch: nach Admin-Aktionen (Schaerfen/Loesung/Compliance/Entscheidung/
// Statuswechsel) + router.refresh muss GET /cases/{id} den neuen Stand liefern.
export const dynamic = "force-dynamic";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
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

  // GET /cases/{id} (public): vollstaendiger read-only Bewertungsstand. 404 ->
  // null -> NotFound. Andere Fehler propagieren (Next.js-Error-Boundary).
  let detail: CaseDetailResponse | null;
  try {
    detail = await getCaseDetail(id);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
        <p className="eyebrow">Fall-Detail</p>
        <p
          role="alert"
          className="mt-4 rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {e instanceof Error
            ? e.message
            : "Der Bewertungsstand konnte nicht geladen werden."}
        </p>
      </main>
    );
  }
  if (detail === null) {
    return <NotFound id={id} />;
  }

  const authenticated = await checkAuth();
  const { eingaben, triage, report } = detail;
  const bs = report.business_summary;

  // Admin-Panels nur fuer Angemeldete laden -- die Endpoints sind require_admin.
  let entries: MonitoringEntry[] = [];
  let timelineError: string | null = null;
  let similarityPairs: SimilarityPair[] = [];
  let initialSketch: ArchitectureSketchResponse | null = null;

  if (authenticated) {
    try {
      entries = await listMonitoringEntries(id);
    } catch (e) {
      timelineError =
        e instanceof Error
          ? e.message
          : "Die Monitoring-Einträge konnten nicht geladen werden.";
    }
    try {
      similarityPairs = (await listSimilarityPairs()).pairs;
    } catch (e) {
      console.error("listSimilarityPairs fehlgeschlagen:", e);
    }
    try {
      initialSketch = await getArchitectureSketch(id);
    } catch (e) {
      console.error("getArchitectureSketch fehlgeschlagen:", e);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-6">
      {/* --- Kopf --- */}
      <p className="eyebrow">Fall-Detail</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        {triage.title}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {eingaben.department} · Eingereicht am {formatDate(detail.submitted_at)}
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 rounded-xl border border-border bg-card px-5 py-4">
        <div className="flex items-center gap-2">
          <span className="eyebrow">Zone</span>
          <ZoneBadge zone={triage.zone?.final_zone ?? null} />
        </div>
        <div className="flex items-center gap-2">
          <span className="eyebrow">Status</span>
          {authenticated ? (
            <CaseStatusControl caseId={detail.id} initialStatus={detail.status} />
          ) : (
            <StatusBadge status={detail.status} />
          )}
        </div>
      </div>

      {/* --- Erfasste Eingaben (Erklaerbarkeit: Grundlage der Bewertung). --- */}
      <div className="mt-8">
        <CaseInputs eingaben={eingaben} />
      </div>

      {/* --- Ergebnis (ScoreBreakdown / Konfidenz-Saetze). --- */}
      <div className="mt-10">
        <CaseResult triage={triage} />
      </div>

      {/* --- Report (Entscheider / Technisch, Loesung, Compliance). --- */}
      <div className="mt-10">
        <p className="eyebrow mb-3">Report</p>
        <CaseReport report={report} />
      </div>

      {authenticated ? (
        <>
          <CaseAdminActions
            caseId={detail.id}
            reviewerDecision={bs.reviewer_decision}
            reviewerNote={bs.reviewer_note}
            hasSolution={bs.solution_business !== null}
            hasCompliance={bs.compliance_hint_text !== null}
          />

          <SimilarCasesPanel caseId={detail.id} pairs={similarityPairs} />
          <SketchView caseId={detail.id} initialSketch={initialSketch} />

          <div className="mt-10">
            {timelineError !== null ? (
              <p
                role="alert"
                className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
              >
                {timelineError}
              </p>
            ) : (
              <MonitoringTimeline caseId={detail.id} initialEntries={entries} />
            )}
          </div>
        </>
      ) : (
        <p className="mt-8 rounded-xl border border-border bg-muted/40 px-4 py-3.5 text-sm text-muted-foreground">
          Bearbeitung (Schärfen, Lösung, Compliance, Entscheidung, Statuswechsel)
          sowie Ähnlichkeit, Architektur-Skizze und Monitoring sind angemeldeten
          Admins vorbehalten.{" "}
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
