import type { Metadata } from "next";
import Link from "next/link";
import { getFormatter, getTranslations } from "next-intl/server";
import { Clock } from "lucide-react";

import {
  checkAuth,
  getArchitectureSketch,
  getCaseDetail,
  listSimilarityPairs,
} from "@/app/actions";
import { bindFormat } from "@/lib/format";
import { CaseDecision } from "@/components/case-decision";
import { CaseInputs } from "@/components/case-inputs";
import { CaseReport } from "@/components/case-report";
import { CaseResult } from "@/components/case-result";
import { CaseStatusControl } from "@/components/case-status-control";
import { CaseTools } from "@/components/case-tools";
import { LlmBusyProvider } from "@/components/llm-busy";
import { SimilarCasesPanel } from "@/components/similar-cases-panel";
import { RetryButton } from "@/components/retry-button";
import { SketchView } from "@/components/sketch-view";
import { StatusBadge } from "@/components/status-badge";
import type {
  ArchitectureSketchResponse,
  CaseDetailResponse,
  SimilarityPair,
} from "@/types/api";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("detailPage");
  return { title: t("metaTitle") };
}

// Immer frisch: nach Admin-Aktionen (Schaerfen/Loesung/Compliance/Entscheidung/
// Statuswechsel) muss GET /cases/{id} den neuen Stand liefern.
export const dynamic = "force-dynamic";

// Ein Bereich der Detailseite (S4): drei klar getrennte Segmente statt einer
// langen Sektionsliste. Trennlinie + kraeftige Ueberschrift grenzen sie ab.
function AreaSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12 border-t border-border pt-8">
      <h2 className="text-lg font-semibold tracking-tight text-foreground">
        {title}
      </h2>
      <div className="mt-6">{children}</div>
    </section>
  );
}

// Ruhiger Zwischenzustand (Pending / "wird geprueft") -- Uhr-Icon + zwei Zeilen.
function StatusBox({ heading, body }: { heading: string; body: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-muted/30 px-6 py-8 text-center">
      <span
        aria-hidden
        className="mx-auto flex size-9 items-center justify-center rounded-full bg-muted text-muted-foreground"
      >
        <Clock className="size-4.5" />
      </span>
      <p className="mt-3 text-sm font-medium text-foreground">{heading}</p>
      <p className="mx-auto mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
        {body}
      </p>
    </div>
  );
}

async function NotFound({ id }: { id: string }) {
  const t = await getTranslations("detailPage");
  return (
    <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
      <p className="eyebrow">{t("eyebrow")}</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        {t("notFoundTitle")}
      </h1>
      <p className="mt-4 max-w-prose text-sm leading-relaxed text-muted-foreground">
        {t("notFoundBody", { id })}
      </p>
      <Link
        href="/cases"
        className="mt-4 inline-block text-sm font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
      >
        {t("backToList")}
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
  const t = await getTranslations("detailPage");
  const ts = await getTranslations("status");
  const fmt = bindFormat(await getFormatter());

  // GET /cases/{id} (public): vollstaendiger read-only Bewertungsstand. 404 ->
  // null -> NotFound. Andere Fehler propagieren (Next.js-Error-Boundary).
  let detail: CaseDetailResponse | null;
  try {
    detail = await getCaseDetail(id);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
        <p className="eyebrow">{t("eyebrow")}</p>
        <div
          role="alert"
          className="mt-4 rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3.5 text-sm text-destructive"
        >
          <p>{e instanceof Error ? e.message : t("loadError")}</p>
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
  // ruhiger Zwischenzustand statt Score/Report.
  const { eingaben, triage, report } = detail;

  // Admin-Panels nur fuer Angemeldete laden -- die Endpoints sind require_admin.
  let similarityPairs: SimilarityPair[] = [];
  let initialSketch: ArchitectureSketchResponse | null = null;

  if (authenticated) {
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

  const evaluated = !detail.evaluation_pending;
  const summary = report?.business_summary ?? null;

  // LlmBusyProvider klammert Bereich 2 (Werkzeuge) und Bereich 3
  // (Entscheidung): die Werkzeuge melden ihre laufenden LLM-Calls an, die
  // Entscheidung sperrt solange mit sichtbarem Grund (s. llm-busy.tsx). Die
  // Kinder bleiben Server-Komponenten -- der Provider reicht sie nur durch.
  return (
    <LlmBusyProvider>
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-6">
        {/* --- Kopf --- */}
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
          {eingaben.title}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {t("submittedLine", {
            department: eingaben.department,
            date: fmt.dateShort(detail.submitted_at),
          })}
        </p>
        {/* Status zur Orientierung (read-only); die Steuerung lebt in Bereich 3. */}
        <div className="mt-4 flex items-center gap-2">
          <span className="eyebrow">{t("status")}</span>
          <StatusBadge status={detail.status} />
        </div>

        {/* ===== Bereich 1: Use Case ===== */}
        <AreaSection title={t("areaUseCase")}>
          <CaseInputs eingaben={eingaben} caseId={detail.id} isAdmin={authenticated} />
        </AreaSection>

        {/* ===== Bereich 2: Analyse & Empfehlung ===== */}
        <AreaSection title={t("areaAnalysis")}>
          {detail.evaluation_pending ? (
            <StatusBox
              heading={ts("evaluationPending")}
              body={t("pendingBody")}
            />
          ) : triage !== null ? (
            <CaseResult triage={triage} />
          ) : (
            <StatusBox
              heading={t("reviewingHeading")}
              body={t("reviewingBody", { date: fmt.dateShort(detail.submitted_at) })}
            />
          )}

          {/* Admin-Werkzeuge + Skizze nur fuer angemeldete Admins mit
              ausgewertetem Case (report != null). */}
          {authenticated && evaluated && report !== null && summary !== null && (
            <div className="mt-8 space-y-6">
              <CaseTools
                caseId={detail.id}
                hasSolution={summary.solution_business !== null}
                hasCompliance={summary.compliance_hint_text !== null}
              />
              <SketchView
                caseId={detail.id}
                initialSketch={initialSketch}
                hasSolution={summary.solution_business !== null}
              />
            </div>
          )}

          {authenticated && (
            <div className="mt-8">
              <SimilarCasesPanel caseId={detail.id} pairs={similarityPairs} />
            </div>
          )}
        </AreaSection>

        {/* ===== Bereich 3: Entscheidung & Report ===== */}
        {report !== null && summary !== null && (
          <AreaSection title={t("areaDecision")}>
            {authenticated && (
              <div className="space-y-6">
                <div>
                  <p className="eyebrow mb-2">{t("status")}</p>
                  <CaseStatusControl
                    caseId={detail.id}
                    initialStatus={detail.status}
                  />
                </div>
                <CaseDecision
                  caseId={detail.id}
                  reviewerDecision={summary.reviewer_decision}
                  reviewerNote={summary.reviewer_note}
                />
              </div>
            )}
            <div className={authenticated ? "mt-10" : ""}>
              <p className="eyebrow mb-3">{t("report")}</p>
              <CaseReport report={report} />
            </div>
          </AreaSection>
        )}
      </main>
    </LlmBusyProvider>
  );
}
