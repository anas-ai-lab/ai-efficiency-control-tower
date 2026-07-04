import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Monitoring | AECT",
};

// Platzhalter -- die fallübergreifende Monitoring-Zeitleiste (append-only
// Notizen mit Status-Snapshot) wird in P7 gebaut.
export default function MonitoringPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
      <p className="eyebrow">Monitoring</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Beobachtungen entlang der Zeit
      </h1>
      <p className="mt-4 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Hier entsteht in P7 die Monitoring-Ansicht: die append-only
        Beobachtungsnotizen zu den Use Cases, jeweils mit dem Status-Snapshot zum
        Zeitpunkt des Eintrags. Server Action und Typen sind vorbereitet.
      </p>
    </main>
  );
}
