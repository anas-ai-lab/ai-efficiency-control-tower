import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Board | AECT",
};

// Platzhalter -- das Lifecycle-Board (Spalten je CaseStatus, Verteilungs-Chart)
// wird in P6 gebaut (recharts ist bereits als Dependency vorhanden).
export default function BoardPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16 sm:px-6">
      <p className="eyebrow">Board</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Use Cases nach Lifecycle-Status
      </h1>
      <p className="mt-4 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Hier entsteht in P6 das Board: die Use Cases gruppiert nach ihrem
        Lifecycle-Status, mit einer ruhigen Verteilungs-Visualisierung. Die
        Status-Semantik und die nötigen Server Actions stehen bereits.
      </p>
    </main>
  );
}
