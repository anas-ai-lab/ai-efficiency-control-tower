"use client"

import { useLocale, useTranslations } from "next-intl"
import { useTransition } from "react"

import { setLocale } from "@/i18n/actions"
import { locales, type Locale } from "@/i18n/config"

// Sprachumschalter (V4.1-S6): segmentiertes DE|EN neben dem Theme-Toggle. Setzt
// das NEXT_LOCALE-Cookie serverseitig (setLocale) und laedt danach HART neu
// (window.location.reload). Ein blosses router.refresh() aktualisiert nur die
// aktuelle Route -- die im Next.js-Router-Cache VORGELADENEN anderen Routen
// bleiben in der alten Sprache (der Cache variiert NICHT nach Cookie; dieselbe
// App-Router-Cache-Grenze, die das Projekt schon via lib/reload.hardRefresh
// umgeht). Der harte Reload bustet den gesamten Cache -> die ganze App rendert
// konsistent in der neuen Sprache, ohne deutschen Rest bei Soft-Navigation.
// Kosten: ein offener Intake-Wizard verliert seinen Zwischenstand (dokumentiert).
export function LangToggle() {
  const active = useLocale() as Locale
  const t = useTranslations("common")
  const [pending, startTransition] = useTransition()

  function switchTo(next: Locale) {
    if (next === active || pending) return
    startTransition(async () => {
      await setLocale(next)
      window.location.reload()
    })
  }

  return (
    <div
      role="group"
      aria-label={t("languageSwitcher")}
      className="inline-flex items-center rounded-lg border border-border p-0.5"
    >
      {locales.map((loc) => {
        const isActive = loc === active
        return (
          <button
            key={loc}
            type="button"
            onClick={() => switchTo(loc)}
            aria-pressed={isActive}
            disabled={pending}
            className={
              isActive
                ? "rounded-[0.4rem] bg-muted px-2 py-1 font-mono text-xs font-semibold text-foreground"
                : "rounded-[0.4rem] px-2 py-1 font-mono text-xs font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-60"
            }
          >
            {loc.toUpperCase()}
          </button>
        )
      })}
    </div>
  )
}

export default LangToggle
