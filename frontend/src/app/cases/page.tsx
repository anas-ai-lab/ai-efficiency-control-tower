import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ideenliste | AECT",
};

// Platzhalter -- die sortier-/filterbare Portfolio-Liste wird in P5 gebaut
// (auf listCases() + STATUS_CONFIG). Route ist ab jetzt erreichbar und in der
// Navigation verlinkt.
export default function CasesPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
      <p className="eyebrow">Ideenliste</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Alle eingereichten Use Cases
      </h1>
      <p className="mt-4 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Hier entsteht in P5 die durchsuch- und sortierbare Portfolio-Liste: jeder
        eingereichte Use Case mit Zone, erwartetem Netto-Nutzen und
        Lifecycle-Status. Das Fundament (Server Action, Typen, Status-Semantik)
        steht bereits.
      </p>
    </main>
  );
}
