import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Fall-Detail | AECT",
};

// Platzhalter -- die Detailansicht eines Use Case (Report, Status setzen,
// Monitoring-Zeitleiste) wird in P5 gebaut. params ist in Next 16 ein Promise.
export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
      <p className="eyebrow">Fall-Detail</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Use Case im Detail
      </h1>
      <p className="mt-4 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Die Detailansicht mit Report, Status-Wechsel und Monitoring-Zeitleiste
        entsteht in P5. Angefragter Fall:{" "}
        <span className="font-mono text-foreground">{id}</span>.
      </p>
    </main>
  );
}
