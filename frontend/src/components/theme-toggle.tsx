"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"

const STORAGE_KEY = "aect-theme"

// Kleiner, client-only Theme-Handler ohne next-themes. Das No-FOUC-Skript in
// layout.tsx setzt die .dark-Klasse bereits vor dem ersten Paint; diese
// Komponente haelt nur den Button-Zustand synchron und persistiert die Wahl.
export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setIsDark(document.documentElement.classList.contains("dark"))
  }, [])

  function toggle() {
    const next = !isDark
    setIsDark(next)
    const root = document.documentElement
    root.classList.toggle("dark", next)
    try {
      window.localStorage.setItem(STORAGE_KEY, next ? "dark" : "light")
    } catch {
      /* localStorage nicht verfuegbar -- Wahl gilt nur fuer diese Sitzung. */
    }
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
