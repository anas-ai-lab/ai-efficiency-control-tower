import type { Metadata } from "next"

import { IntakeWizard } from "@/components/intake-wizard"

export const metadata: Metadata = {
  title: "Use Case einreichen | AECT",
}

// Einreichen-Wizard (V4-P7): public. Mehrschritt-Formular ohne Score-/
// Zonen-Vorschau -- das Ergebnis lebt auf der Fall-Detailseite.
export default function EinreichenPage() {
  return (
    <main className="mx-auto max-w-2xl px-5 py-10 sm:px-6 sm:py-12">
      <header className="mb-8">
        <p className="eyebrow">Erfassung</p>
        <h1 className="mt-2 text-2xl font-semibold leading-tight tracking-tight text-foreground">
          Use Case einreichen
        </h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          Beschreibe deinen Use Case in wenigen Schritten. AECT bewertet ihn
          anschließend automatisch.
        </p>
      </header>

      <IntakeWizard />
    </main>
  )
}
