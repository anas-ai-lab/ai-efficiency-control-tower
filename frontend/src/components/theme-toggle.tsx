"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"

const STORAGE_KEY = "aect-theme"

// startViewTransition ist noch nicht in allen lib.dom-Versionen typisiert.
type DocumentWithViewTransition = Document & {
  startViewTransition?: (callback: () => void) => unknown
}

// Kleiner, client-only Theme-Handler ohne next-themes. Das No-FOUC-Skript in
// layout.tsx setzt die .dark-Klasse bereits vor dem ersten Paint; diese
// Komponente haelt nur den Button-Zustand synchron und persistiert die Wahl.
// Neu (S2): der WECHSELMOMENT wird animiert -- Kreis-Reveal (View Transitions)
// bzw. weicher Fade im Fallback. Die Mechanik (Klasse/localStorage) bleibt.
export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setIsDark(document.documentElement.classList.contains("dark"))
  }, [])

  // Die eigentliche Zustandsaenderung -- als Callback fuer startViewTransition
  // wiederverwendbar (der Snapshot davor/danach ergibt den Reveal).
  function applyTheme(next: boolean) {
    setIsDark(next)
    document.documentElement.classList.toggle("dark", next)
    try {
      window.localStorage.setItem(STORAGE_KEY, next ? "dark" : "light")
    } catch {
      /* localStorage nicht verfuegbar -- Wahl gilt nur fuer diese Sitzung. */
    }
  }

  function toggle(event: React.MouseEvent<HTMLButtonElement>) {
    const next = !isDark
    const root = document.documentElement

    const reduceMotion =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches

    // Reduced Motion: direkter Wechsel, keine Animation.
    if (reduceMotion) {
      applyTheme(next)
      return
    }

    const doc = document as DocumentWithViewTransition

    // Chromium: kreisfoermiger clip-path-Reveal aus der Klickposition. Radius =
    // Distanz zur entferntesten Viewport-Ecke, damit der Kreis voll deckt.
    if (typeof doc.startViewTransition === "function") {
      const x = event.clientX
      const y = event.clientY
      const radius = Math.hypot(
        Math.max(x, window.innerWidth - x),
        Math.max(y, window.innerHeight - y),
      )
      root.style.setProperty("--vt-x", `${x}px`)
      root.style.setProperty("--vt-y", `${y}px`)
      root.style.setProperty("--vt-r", `${radius}px`)
      doc.startViewTransition(() => applyTheme(next))
      return
    }

    // Fallback (Firefox/aeltere Safari): weicher CSS-Fade der Basisflaechen.
    root.classList.add("theme-transition")
    applyTheme(next)
    window.setTimeout(() => root.classList.remove("theme-transition"), 320)
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={mounted && isDark ? "Helles Design aktivieren" : "Dunkles Design aktivieren"}
      title={mounted && isDark ? "Helles Design" : "Dunkles Design"}
      className="group relative inline-flex size-9 items-center justify-center rounded-lg border border-border bg-transparent text-muted-foreground outline-none transition-colors duration-150 ease-out hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/35"
    >
      <Sun
        className="size-[1.05rem] rotate-0 scale-100 transition-all duration-200 ease-out dark:-rotate-90 dark:scale-0"
        aria-hidden
      />
      <Moon
        className="absolute size-[1.05rem] rotate-90 scale-0 transition-all duration-200 ease-out dark:rotate-0 dark:scale-100"
        aria-hidden
      />
    </button>
  )
}

export default ThemeToggle
