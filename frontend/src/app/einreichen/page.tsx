import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"

import { ContactCard } from "@/components/contact-card"
import { IntakeWizard } from "@/components/intake-wizard"

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("intake.page")
  return { title: t("metaTitle") }
}

// Einreichen-Wizard (V4-P7): public. Mehrschritt-Formular ohne Score-/
// Zonen-Vorschau -- das Ergebnis lebt auf der Fall-Detailseite.
export default async function EinreichenPage() {
  const t = await getTranslations("intake.page")
  return (
    <main className="mx-auto max-w-2xl px-5 py-10 sm:px-6 sm:py-12">
      <ContactCard />
      <header className="mb-8">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1 className="mt-2 text-2xl font-semibold leading-tight tracking-tight text-foreground">
          {t("title")}
        </h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          {t("lead")}
        </p>
      </header>

      <IntakeWizard />
    </main>
  )
}
