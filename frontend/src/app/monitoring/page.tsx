import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { checkAuth, listCases } from "@/app/actions";
import { MonitoringBoard } from "@/components/monitoring-board";
import { RetryButton } from "@/components/retry-button";
import type { CaseSummary } from "@/types/api";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("monitoring");
  return { title: t("metaTitle") };
}

// Immer frisch: nach Statuswechsel/neuer Notiz + Reload muss der neue Stand
// erscheinen.
export const dynamic = "force-dynamic";

export default async function MonitoringPage() {
  // V4-P-Auth: Admin-Bereich. Unauthentifiziert -> Login mit Ruecksprung.
  if (!(await checkAuth())) {
    redirect("/login?next=/monitoring");
  }

  const t = await getTranslations("monitoring");
  let cases: CaseSummary[] = [];
  let loadError: string | null = null;
  try {
    cases = await listCases();
  } catch (e) {
    loadError = e instanceof Error ? e.message : t("loadErrorFallback");
  }

  // Monitoring beginnt nach der Freigabe: nur freigegebene oder umgesetzte Faelle.
  const monitored = cases.filter(
    (c) => c.status === "approved" || c.status === "implemented",
  );

  return (
    <main className="mx-auto max-w-4xl px-5 py-12 sm:px-6">
      <p className="eyebrow">{t("pageEyebrow")}</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        {t("pageTitle")}
      </h1>
      <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
        {t("pageLead")}
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
          <MonitoringBoard cases={monitored} />
        )}
      </div>
    </main>
  );
}
