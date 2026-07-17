"use client"

import { useEffect, useRef, useState } from "react"
import { animate, useInView, useReducedMotion } from "motion/react"

import { useFormat } from "@/lib/use-format"

// Kennzahl-Karte der Startseite (v4.2). Loest die fruehere dreispaltige
// dl-Leiste ab.
//
// KONTEXTELEMENT -- bewusst KEIN Trend-Delta:
// Ein "+12 % zum Vormonat" waere eine erfundene Zahl (CLAUDE.md: "Keine
// erfundenen Zahlen"); das Backend liefert ueber GET /stats nur die drei
// Mengen-Staende, keine Historie. Das Kontextelement ist deshalb ein aus genau
// diesen Staenden ABGELEITETER Trichter-Anteil: wie viel der Einreichungen die
// jeweilige Stufe erreicht hat. Die erste Karte (Einreichungen) ist die Basis
// und traegt daher keinen Anteil -- nur ihren Hinweis.
export interface StatCardProps {
  label: string
  value: number | null
  hint: string
  // Anteil an den Einreichungen (0..1) oder null fuer die Basis-Karte.
  share: number | null
  shareLabel: string | null
}

// Zaehl-Animation beim ersten Sichtbarwerden. Laeuft genau einmal (once: true) --
// ein Zaehler, der bei jedem Scroll neu hochlaeuft, ist Spielerei, kein Signal.
function useCountUp(value: number | null, inView: boolean): number {
  const [display, setDisplay] = useState(0)
  const reduce = useReducedMotion()

  useEffect(() => {
    if (value === null || !inView) return
    // reduced-motion: Endwert sofort, kein Hochzaehlen.
    if (reduce) {
      setDisplay(value)
      return
    }
    const controls = animate(0, value, {
      duration: 0.9,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(v),
    })
    return () => controls.stop()
  }, [value, inView, reduce])

  return display
}

export function StatCard({ label, value, hint, share, shareLabel }: StatCardProps) {
  const ref = useRef<HTMLDivElement | null>(null)
  const inView = useInView(ref, { once: true, margin: "-64px" })
  const fmt = useFormat()
  const display = useCountUp(value, inView)

  const dash = "—"

  return (
    <div ref={ref} className="flex flex-col justify-between bg-card px-6 py-7">
      <div>
        <p className="eyebrow">{label}</p>
        {/* Zahl-Hierarchie: die Kennzahl ist das lauteste Element der Karte --
            gross, Mono, tabular-nums, damit die Ziffern beim Hochzaehlen nicht
            springen. Label und Hinweis bleiben deutlich darunter. */}
        <p className="stat-value tnum mt-3 text-[2.5rem] text-foreground sm:text-[2.75rem]">
          {value === null ? dash : fmt.number(Math.round(display))}
        </p>
      </div>

      <div className="mt-5">
        {/* Kontext-Hairline: der Anteil an den Einreichungen als feine Linie,
            keine Ampel, kein Balkendiagramm. Die Grundlinie ist immer da, der
            gefuellte Teil waechst beim Sichtbarwerden mit. */}
        {share !== null && shareLabel !== null && (
          <div className="mb-3">
            <div
              aria-hidden
              className="h-px w-full overflow-hidden bg-[var(--hairline-rule)]"
            >
              <div
                className="h-full bg-[var(--ink)] transition-[width] duration-700 [transition-timing-function:var(--ease-spring)] motion-reduce:transition-none"
                style={{ width: inView ? `${Math.round(share * 100)}%` : "0%" }}
              />
            </div>
            <p className="tnum mt-2 text-xs text-muted-foreground">{shareLabel}</p>
          </div>
        )}
        <p className="text-xs leading-relaxed text-muted-foreground">{hint}</p>
      </div>
    </div>
  )
}

export default StatCard
