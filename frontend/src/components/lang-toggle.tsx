"use client"

import { useLocale, useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import { useTransition } from "react"

import { setLocale } from "@/i18n/actions"
import { locales, type Locale } from "@/i18n/config"

// Sprachumschalter (V4.1-S6): segmentiertes DE|EN neben dem Theme-Toggle. Setzt
// das NEXT_LOCALE-Cookie serverseitig (setLocale) und ruft router.refresh() --
// die Server-Komponenten rendern in der neuen Sprache neu, der Client-State
// (z. B. offener Intake-Wizard) bleibt erhalten (kein Remount bei refresh).
export function LangToggle() {
  const active = useLocale() as Locale
  const t = useTranslations("common")
  const router = useRouter()
  const [pending, startTransition] = useTransition()

  function switchTo(next: Locale) {
    if (next === active || pending) return
    startTransition(async () => {
      await setLocale(next)
      router.refresh()
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
