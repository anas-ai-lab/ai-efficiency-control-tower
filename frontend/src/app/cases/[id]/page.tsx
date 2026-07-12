import type { Metadata } from "next";
import Link from "next/link";
import { Clock } from "lucide-react";

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
import { RetryButton } from "@/components/retry-button";
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
        <div
          role="alert"
          className="mt-4 rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3.5 text-sm text-destructive"
        >
          <p>
            {e instanceof Error
              ? e.message
              : "Der Bewertungsstand konnte nicht geladen werden."}
          </p>
          <div className="mt-3">
            <RetryButton />
          </div>
        </div>
      </main>
    );
  }
  if (detail === null) {
    return <NotFound id={id} />;
  }

  const authenticated = await checkAuth();
  // Bewertung ist bedingt sichtbar (V4-P7): das Backend liefert triage/report
  // erst nach der Board-Entscheidung -- oder fuer Admins. Davor beide null ->
  // ruhiger Zwischenzustand statt Score/Report. Die Null-Checks stehen inline
  // im JSX (TS-Narrowing).
  const { eingaben, triage, report } = detail;

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
        {eingaben.title}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {eingaben.department} · Eingereicht am {formatDate(detail.submitted_at)}
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 rounded-xl border border-border bg-card px-5 py-4">
        {/* Zone erst nach Freigabe der Bewertung (V4-P7). */}
        {triage !== null && (
          <div className="flex items-center gap-2">
            <span className="eyebrow">Zone</span>
            <ZoneBadge zone={triage.zone?.final_zone ?? null} />
          </div>
        )}
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
        <CaseInputs eingaben={eingaben} caseId={detail.id} isAdmin={authenticated} />
      </div>

      {/* --- Bewertung: Vor-Bewertungs-Zustand > Bewertung > "wird geprueft". --- */}
      {detail.evaluation_pending ? (
        <div className="mt-10 rounded-xl border border-border bg-muted/30 px-6 py-8 text-center">
          <span
            aria-hidden
            className="mx-auto flex size-9 items-center justify-center rounded-full bg-muted text-muted-foreground"
          >
            <Clock className="size-4.5" />
          </span>
          <p className="mt-3 text-sm font-medium text-foreground">
            Bewertung ausstehend
          </p>
          <p className="mx-auto mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
            Für diesen Fall wurde noch kein Implementierungsansatz gewählt. Sobald
            ein Admin ihn oben ergänzt, wird der Fall vollständig bewertet (Nutzen,
            Aufwand, Risiko).
          </p>
        </div>
      ) : triage !== null && report !== null ? (
        <>
          <div className="mt-10">
            <CaseResult triage={triage} />
          </div>
          <div className="mt-10">
            <p className="eyebrow mb-3">Report</p>
            <CaseReport report={report} />
          </div>
        </>
      ) : (
        <div className="mt-10 rounded-xl border border-border bg-muted/30 px-6 py-8 text-center">
          <span
            aria-hidden
            className="mx-auto flex size-9 items-center justify-center rounded-full bg-muted text-muted-foreground"
          >
            <Clock className="size-4.5" />
          </span>
          <p className="mt-3 text-sm font-medium text-foreground">
            Wird vom AI Board geprüft
          </p>
          <p className="mx-auto mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
            Eingereicht am {formatDate(detail.submitted_at)}. Die Bewertung
            (Nutzen, Aufwand, Risiko) wird sichtbar, sobald das AI Board über den
            Use Case entschieden hat.
          </p>
        </div>
      )}

      {authenticated && (
        <>
          {report !== null && (
            <CaseAdminActions
              caseId={detail.id}
              reviewerDecision={report.business_summary.reviewer_decision}
              reviewerNote={report.business_summary.reviewer_note}
              hasSolution={report.business_summary.solution_business !== null}
              hasCompliance={report.business_summary.compliance_hint_text !== null}
            />
          )}

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
      )}
    </main>
  );
}
