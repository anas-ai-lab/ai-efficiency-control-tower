"use client"

import { useEffect, useRef, useState } from "react"
import {
  animate,
  motion,
  useInView,
  useMotionValue,
  useReducedMotion,
  useSpring,
} from "motion/react"

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
  // Anteil an den Einreichungen (0..1) oder null/weggelassen fuer die
  // Basis-Karte (Einreichungen -- es gibt dafuer keinen Nenner).
  share?: number | null
  shareLabel?: string | null
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

// Gleiche Feder wie in nav-tile.tsx -- ein Bewegungsgefuehl ueber die ganze
// Startseite, nicht zwei.
const TILT_SPRING = {
  type: "spring" as const,
  stiffness: 300,
  damping: 24,
  mass: 0.5,
}

export function StatCard({
  label,
  value,
  share = null,
  shareLabel = null,
}: StatCardProps) {
  const ref = useRef<HTMLDivElement | null>(null)
  const inView = useInView(ref, { once: true, margin: "-64px" })
  const fmt = useFormat()
  const display = useCountUp(value, inView)
  const reduce = useReducedMotion()

  // Cursor-Tilt + Spotlight, identisches Muster wie NavTile (Begruendung dort,
  // inkl. warum das bewusst nur an der Maus haengt).
  const rawRotateX = useMotionValue(0)
  const rawRotateY = useMotionValue(0)
  const rotateX = useSpring(rawRotateX, TILT_SPRING)
  const rotateY = useSpring(rawRotateY, TILT_SPRING)

  function handleMouseMove(event: React.MouseEvent<HTMLDivElement>) {
    if (reduce) return
    const el = event.currentTarget
    const rect = el.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    el.style.setProperty("--mx", `${(x / rect.width) * 100}%`)
    el.style.setProperty("--my", `${(y / rect.height) * 100}%`)
    rawRotateX.set(-((y - rect.height / 2) / (rect.height / 2)) * 3.5)
    rawRotateY.set(((x - rect.width / 2) / (rect.width / 2)) * 3.5)
  }

  function handleMouseLeave() {
    rawRotateX.set(0)
    rawRotateY.set(0)
  }

  const dash = "—"

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={reduce ? undefined : { rotateX, rotateY, transformPerspective: 800 }}
      className="group relative grid h-full grid-rows-[auto_1fr_auto] overflow-hidden bg-card px-6 py-7"
    >
      {/* Spotlight -- transparent 90% statt 88% wie bei den Nav-Kacheln: die
          drei Karten stehen ohne Fugen direkt nebeneinander, dort faellt eine
          Aufhellung staerker auf als bei den freistehenden Kacheln. Absolut
          positioniert -- belegt keine eigene Grid-Zeile. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(circle at var(--mx,50%) var(--my,50%), color-mix(in oklch, var(--brand-accent), transparent 90%), transparent 60%)",
        }}
      />
      {/* .eyebrow: 0.6875rem font-size * 1 line-height = 0.6875rem je Zeile,
          zwei Zeilen = 1.375rem min-h -- reserviert Platz fuer das laengste
          Label ("Freigegebene Ideen in der Entwicklung"), unabhaengig davon
          ob eine Karte nur eine Zeile braucht. */}
      <p className="eyebrow shrink-0 min-h-[1.375rem]">{label}</p>

      {/* Zahl-Zone: eigene Grid-Zeile, oben ausgerichtet (justify-start statt
          justify-center) -- bei fester Label-Hoehe darueber und fester
          Anteils-Hoehe darunter startet die Zahl auf allen vier Karten an
          derselben Y-Position. Display-Token statt Mono (siehe .kpi-value in
          globals.css), feste Zeilenhoehe (line-height:1) verhindert einen
          Layout-Shift waehrend der Hochzaehl-Animation. */}
      <div className="flex flex-col items-start justify-start">
        <p className="kpi-value tnum text-[3.75rem] text-foreground sm:text-[4.5rem]">
          {value === null ? dash : fmt.number(Math.round(display))}
        </p>
      </div>

      {/* Anteils-Zone: dritte Grid-Zeile, IMMER gerendert -- die vier Zahlen
          sitzen nur dann auf einer Grundlinie, wenn jede Karte dieselben drei
          Zonenhoehen hat. Der reservierte Leerraum auf der Basis-Karte ist
          der Preis fuer die Ausrichtung. Hoehe: Hairline 1px + mt-2 0.5rem +
          text-xs-Zeile (kein eigener Wert in globals.css -- Tailwind-Default
          0.75rem/1rem line-height) = calc(1.5rem + 1px) min-h. */}
      <div
        className="mt-4 max-w-32 min-h-[calc(1.5rem+1px)]"
        aria-hidden={share === null || shareLabel === null ? "true" : undefined}
      >
        {share !== null && shareLabel !== null && (
          <>
            <div
              aria-hidden
              className="h-px w-full overflow-hidden bg-[var(--hairline-rule)]"
            >
              <div
                className="h-full bg-[var(--ink)] transition-[width] duration-700 [transition-timing-function:var(--ease-spring)] motion-reduce:transition-none"
                style={{ width: inView ? `${Math.round(share * 100)}%` : "0%" }}
              />
            </div>
            <p className="tnum mt-2 text-xs text-[var(--muted-foreground)]">
              {shareLabel}
            </p>
          </>
        )}
      </div>
    </motion.div>
  )
}

export default StatCard
