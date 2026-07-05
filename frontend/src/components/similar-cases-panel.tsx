import Link from "next/link";

import type { SimilarityPair } from "@/types/api";

// Aehnlichkeit als Prozent mit einer Nachkommastelle (de-DE): 0.873 -> "87,3 %".
function formatSimilarity(score: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(score);
}

// Aehnlichkeits-Panel der Detail-Seite (P12/C). Kein Per-Case-Endpoint
// vorhanden -- die Detail-Seite ruft dieselbe volle Paar-Liste ab und filtert
// client-/server-seitig auf Paare, die diese case_id enthalten. Wird nur
// gerendert, wenn es solche Paare gibt (Aufrufer prueft das ebenfalls).
export function SimilarCasesPanel({
  caseId,
  pairs,
}: {
  caseId: string;
  pairs: SimilarityPair[];
}) {
  const related = pairs.filter(
    (p) => p.case_a_id === caseId || p.case_b_id === caseId,
  );
  if (related.length === 0) return null;

  return (
    <section className="mt-8 rounded-xl border border-border bg-card p-5">
      <p className="eyebrow mb-3">Ähnliche Use Cases</p>
      <ul className="flex flex-col gap-3">
        {related.map((p) => {
          const isA = p.case_a_id === caseId;
          const otherId = isA ? p.case_b_id : p.case_a_id;
          const otherTitle = isA ? p.case_b_title : p.case_a_title;
          return (
            <li
              key={otherId}
              className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1"
            >
              <Link
                href={`/cases/${otherId}`}
                className="font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
              >
                {otherTitle}
              </Link>
              <span className="flex items-baseline gap-3 text-sm">
                <span className="font-mono text-foreground tabular-nums">
                  {formatSimilarity(p.similarity_score)}
                </span>
                {p.suggest_combine && (
                  <span className="text-[var(--ink)]">
                    Zusammenführung prüfen
                  </span>
                )}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="mt-4 border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
        Ähnlichkeit basiert auf Text-Embeddings von Titel und Ist-Beschreibung —
        kein inhaltliches Urteil.
      </p>
    </section>
  );
}
