import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { checkAuth, listCases } from "@/app/actions";
import { BoardMatrix } from "@/components/board-matrix";
import { RetryButton } from "@/components/retry-button";
import type { CaseSummary } from "@/types/api";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("board");
  return { title: t("metaTitle") };
}

// Immer frisch laden (wie /cases): nach Statuswechsel + Reload muss der neue
// Stand erscheinen. listCases nutzt cache: "no-store"; force-dynamic verhindert
// zusaetzlich statisches Prerendering dieser Route.
export const dynamic = "force-dynamic";

export default async function BoardPage() {
  // V4-P-Auth: Admin-Bereich. Unauthentifiziert -> Login mit Ruecksprung.
  if (!(await checkAuth())) {
    redirect("/login?next=/board");
  }

  const t = await getTranslations("board");
  let cases: CaseSummary[] = [];
  let loadError: string | null = null;
  try {
    cases = await listCases();
  } catch (e) {
    cases = [];
    loadError = e instanceof Error ? e.message : t("loadErrorFallback");
  }

  return (
    <main className="mx-auto max-w-6xl px-5 py-12 sm:px-6">
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
          <BoardMatrix cases={cases} />
        )}
      </div>
    </main>
  );
}
