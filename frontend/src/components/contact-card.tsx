import { useTranslations } from "next-intl"
import { Mail } from "lucide-react"

// Ansprechpartner-Karte fuer die drei oeffentlichen Seiten (Einreichen,
// Ideen-Assistent, Ideenliste) -- V4.1-S8. Eine Quelle, drei Einbindungen:
// aendert sich der Kontakt, aendert er sich hier.
//
// Gestaltung nach dem Brand-Token-Design: ruhige Card-Flaeche, der einzige
// Akzent ist der Tinten-Ton (--ink) am interaktiven Element (mailto-Link) --
// kein farbiger Block, keine zweite Akzentfarbe, kein Emoji. Die Karte ist
// Beiwerk, nicht Botschaft: sie steht ueber dem Seitenkopf und bleibt dezent.
//
// Kontaktdaten bewusst als Konstanten im Code, nicht im Sprachkatalog: Name und
// Adresse sind in DE wie EN identisch -- uebersetzt wird nur, was sie einordnet.
const CONTACT_NAME = "Anas Lab"
const CONTACT_MAIL = "anas.ai.lab@github.com"

// useTranslations statt getTranslations, und daher NICHT async: die Karte haengt
// im Ideen-Assistenten in einem Client-Baum ("use client") und auf den anderen
// beiden Seiten in einem Server-Baum. useTranslations traegt beide; eine async
// Server-Komponente liesse sich im Client-Baum nicht rendern.
export function ContactCard() {
  const t = useTranslations("contact")

  return (
    <aside className="mb-8 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-border bg-card px-5 py-3.5">
      <span
        aria-hidden
        className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground"
      >
        <Mail className="size-4" />
      </span>
      <div className="min-w-0">
        <p className="eyebrow">{t("role")}</p>
        <p className="mt-0.5 text-sm text-foreground">
          <span className="font-medium">{CONTACT_NAME}</span>
          <span className="mx-1.5 text-border" aria-hidden>
            ·
          </span>
          <a
            href={`mailto:${CONTACT_MAIL}`}
            className="rounded-sm text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 outline-none hover:decoration-[var(--ink)] focus-visible:ring-2 focus-visible:ring-ring/40"
          >
            {CONTACT_MAIL}
          </a>
        </p>
      </div>
      <p className="ml-auto hidden max-w-xs text-xs leading-relaxed text-muted-foreground sm:block">
        {t("hint")}
      </p>
    </aside>
  )
}

export default ContactCard
