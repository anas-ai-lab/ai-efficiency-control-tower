"use client"

import { useEffect, useRef } from "react"

// Seitenwechsel-Effekt (v4.2): beim Klick auf einen Navigations-Link oder eine
// Startseiten-Kachel wehen einige wenige, stilisierte Blaetter vom Klickpunkt
// aus ueber den Screen, waehrend die Zielseite oeffnet.
//
// ARCHITEKTUR -- bewusst NEBEN der View Transitions API, nicht darin:
// Der Theme-Toggle (components/theme-toggle.tsx) besitzt startViewTransition und
// die ::view-transition-*(root)-Regeln in globals.css exklusiv. Wuerde die
// Navigation ebenfalls eine View Transition starten, teilten sich beide
// denselben Pseudo-Element-Baum -- der Kreis-Reveal des Themes wuerde dann auch
// bei jedem Seitenwechsel laufen. Stattdessen liegt hier ein eigenes,
// unabhaengiges Canvas-Overlay im Root-Layout: es ueberlebt die Navigation (das
// Layout bleibt montiert, nur children tauschen) und beruehrt die
// Theme-Mechanik an keiner Stelle.
//
// Ausloeser ist ein data-Attribut, kein Pfad-Vergleich: alles mit
// data-leaf-origin sendet Blaetter, alles andere (Theme-Toggle, Sprach-Toggle,
// Logout, Formular-Buttons) nicht.
export const LEAF_ORIGIN_ATTR = "data-leaf-origin"

// Performance-Budget: wenige, grosse Partikel statt vieler kleiner. 14 Blaetter
// x ~1.4s bleiben auf Mittelklasse-Mobile weit unter einem Frame-Budget; der
// Loop haelt an, sobald das letzte Blatt durch ist (kein Dauer-rAF).
const LEAF_COUNT = 14
const LIFETIME_MS = 1500
const MAX_DPR = 2

interface Leaf {
  x: number
  y: number
  vx: number
  vy: number
  rot: number
  vrot: number
  size: number
  born: number
  // Phase/Tempo des seitlichen Flatterns -- pro Blatt verschieden, damit der
  // Schwarm nicht im Gleichtakt schwingt.
  swayPhase: number
  swaySpeed: number
}

// Ein stilisiertes Blatt: zwei gespiegelte Bezier-Kurven (Linsenform) plus
// Mittelrippe. Bewusst keine botanische Silhouette und keine Assets -- eine
// reine Kurvenkonstruktion, monochrom im Theme-Ton.
function drawLeaf(ctx: CanvasRenderingContext2D, leaf: Leaf, alpha: number, color: string) {
  const s = leaf.size
  ctx.save()
  ctx.translate(leaf.x, leaf.y)
  ctx.rotate(leaf.rot)
  ctx.globalAlpha = alpha
  ctx.fillStyle = color

  ctx.beginPath()
  ctx.moveTo(0, -s)
  ctx.bezierCurveTo(s * 0.72, -s * 0.4, s * 0.72, s * 0.4, 0, s)
  ctx.bezierCurveTo(-s * 0.72, s * 0.4, -s * 0.72, -s * 0.4, 0, -s)
  ctx.fill()

  // Mittelrippe: nimmt dem Blatt die Vollton-Schwere, macht die Drehung lesbar.
  ctx.globalAlpha = alpha * 0.35
  ctx.strokeStyle = color === "#ffffff" ? "#000000" : "#ffffff"
  ctx.lineWidth = Math.max(0.6, s * 0.06)
  ctx.beginPath()
  ctx.moveTo(0, -s * 0.82)
  ctx.lineTo(0, s * 0.82)
  ctx.stroke()

  ctx.restore()
}

export function LeafTransition() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const leavesRef = useRef<Leaf[]>([])
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // reduced-motion: Effekt komplett aus. Kein Listener, kein Canvas-Betrieb --
    // der Seitenwechsel laeuft dann nur ueber den Opazitaets-Fade in globals.css.
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)")

    let dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR)

    function resize() {
      if (!canvas || !ctx) return
      dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR)
      canvas.width = Math.floor(window.innerWidth * dpr)
      canvas.height = Math.floor(window.innerHeight * dpr)
      canvas.style.width = `${window.innerWidth}px`
      canvas.style.height = `${window.innerHeight}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    // Der Blatt-Ton kommt aus dem Token --leaf und wird pro Schwarm einmal
    // gelesen. Gleiches Muster wie board-matrix: Canvas/SVG loesen var() nicht
    // auf, der berechnete Wert muss aktiv geholt werden.
    function leafColor(): string {
      const raw = getComputedStyle(document.documentElement)
        .getPropertyValue("--leaf")
        .trim()
      return raw || "#000000"
    }

    function tick() {
      if (!canvas || !ctx) return
      const now = performance.now()
      const color = leafColor()
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)

      const alive: Leaf[] = []
      for (const leaf of leavesRef.current) {
        const age = now - leaf.born
        const p = age / LIFETIME_MS
        if (p >= 1) continue

        // Bewegung: Trift nach oben-aussen, leichte Schwerkraft, Luftwiderstand,
        // dazu ein seitliches Flattern -- ein fallendes Blatt, kein Funkenflug.
        leaf.vy += 0.02
        leaf.vx *= 0.992
        leaf.vy *= 0.992
        leaf.swayPhase += leaf.swaySpeed
        leaf.x += leaf.vx + Math.sin(leaf.swayPhase) * 0.7
        leaf.y += leaf.vy
        leaf.rot += leaf.vrot

        // Ausklang: volle Deckkraft am Anfang, weiches Verschwinden zum Ende.
        // Deckel bei 0.5 -- die Blaetter sind Beiwerk, nie Vordergrund.
        const alpha = (p < 0.15 ? p / 0.15 : 1 - (p - 0.15) / 0.85) * 0.5
        drawLeaf(ctx, leaf, Math.max(0, alpha), color)
        alive.push(leaf)
      }
      leavesRef.current = alive

      if (alive.length > 0) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        rafRef.current = null
      }
    }

    function spawn(x: number, y: number) {
      const now = performance.now()
      const fresh: Leaf[] = []
      for (let i = 0; i < LEAF_COUNT; i++) {
        // Fanne die Blaetter in einem Halbkreis nach oben auf; die Streuung ist
        // deterministisch genug, dass kein Blatt sofort nach unten faellt.
        const angle = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 1.1
        const speed = 2.5 + Math.random() * 5
        fresh.push({
          x,
          y,
          vx: Math.cos(angle) * speed * 1.4,
          vy: Math.sin(angle) * speed,
          rot: Math.random() * Math.PI * 2,
          vrot: (Math.random() - 0.5) * 0.12,
          size: 4 + Math.random() * 5,
          born: now + i * 18,
          swayPhase: Math.random() * Math.PI * 2,
          swaySpeed: 0.04 + Math.random() * 0.05,
        })
      }
      // Kappen statt anhaeufen: schnelle Mehrfach-Klicks duerfen das Budget nicht
      // vervielfachen.
      leavesRef.current = [...leavesRef.current, ...fresh].slice(-LEAF_COUNT * 2)
      if (rafRef.current === null) {
        rafRef.current = requestAnimationFrame(tick)
      }
    }

    function onClick(event: MouseEvent) {
      if (motionQuery.matches) return
      const target = event.target
      if (!(target instanceof Element)) return
      if (!target.closest(`[${LEAF_ORIGIN_ATTR}]`)) return
      // Modifier-Klicks oeffnen einen neuen Tab -- diese Seite wechselt gar
      // nicht, also auch keine Blaetter.
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return
      spawn(event.clientX, event.clientY)
    }

    resize()
    window.addEventListener("resize", resize)
    document.addEventListener("click", onClick)

    return () => {
      window.removeEventListener("resize", resize)
      document.removeEventListener("click", onClick)
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 z-50"
    />
  )
}

export default LeafTransition
