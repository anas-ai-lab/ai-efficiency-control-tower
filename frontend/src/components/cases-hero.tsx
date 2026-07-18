"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"

import { ZoneBadge } from "@/components/status-badge"
import { isAdminSummary } from "@/lib/case-view"
import type { CaseSummaryView } from "@/types/api"

// Rein dekoratives Hero-Visual fuer /cases: SVG-Flow-Linie mit 3 schwebenden
// Idea-Karten aus den echten, bereits von cases/page.tsx geladenen Cases.
//
// Die Zufallsauswahl passiert bewusst erst nach dem Mount (useEffect), nicht
// im ersten Render: Server und Client wuerden sonst unterschiedliche Werte
// wuerfeln und einen Hydration-Mismatch ausloesen.

function shuffle<T>(items: T[]): T[] {
  const result = [...items]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

// Kartenpositionen im Container, prozentual an dieselbe Kurve angelehnt
// (links unten -> rechts oben).
const CARD_POSITIONS = [
  { left: "2%", top: "48%" },
  { left: "36%", top: "18%" },
  { left: "68%", top: "0%" },
]

interface Point {
  x: number
  y: number
}

// Ankerpunkt am Kartenrand, in Container-Koordinaten -- Richtung des
// Rands haengt von der Position der Karte im Flow ab (unten links -> rechts
// Rand, Mitte -> untere Kante, oben rechts -> linker Rand).
function cardAnchor(index: number, rect: DOMRect, containerRect: DOMRect): Point {
  if (index === 0) {
    return { x: rect.right - containerRect.left, y: rect.top + rect.height / 2 - containerRect.top }
  }
  if (index === 1) {
    return { x: rect.left + rect.width / 2 - containerRect.left, y: rect.bottom - containerRect.top }
  }
  return { x: rect.left - containerRect.left, y: rect.top + rect.height / 2 - containerRect.top }
}

// Catmull-Rom-Tangente je Punkt, aus den beiden Nachbarn abgeleitet (an den
// Enden wird der jeweils einzige Nachbar verwendet) -- ergibt eine glatte,
// durchgehende Kurve durch alle Punkte ohne harte Ecken.
function tangentAt(points: Point[], i: number): Point {
  const prev = points[i - 1] ?? points[i]
  const next = points[i + 1] ?? points[i]
  return { x: (next.x - prev.x) / 2, y: (next.y - prev.y) / 2 }
}

// Baut eine kubische Bezier-Kette durch beliebig viele Punkte (mind. 2).
function buildSmoothPath(points: Point[]): string {
  const tangents = points.map((_, i) => tangentAt(points, i))
  let d = `M ${points[0].x} ${points[0].y}`
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i]
    const p1 = points[i + 1]
    const t0 = tangents[i]
    const t1 = tangents[i + 1]
    const c1x = p0.x + t0.x / 3
    const c1y = p0.y + t0.y / 3
    const c2x = p1.x - t1.x / 3
    const c2y = p1.y - t1.y / 3
    d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p1.x} ${p1.y}`
  }
  return d
}

function IdeaCard({
  caseItem,
  index,
  authenticated,
  setCardRef,
}: {
  caseItem: CaseSummaryView
  index: number
  authenticated: boolean
  setCardRef: (el: HTMLAnchorElement | null) => void
}) {
  const cardRef = useRef<HTMLAnchorElement | null>(null)

  function handleMouseMove(event: React.MouseEvent<HTMLAnchorElement>) {
    const el = cardRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty("--mx", `${event.clientX - rect.left}px`)
    el.style.setProperty("--my", `${event.clientY - rect.top}px`)
  }

  // Callback-Ref setzt BEIDE Referenzen auf demselben Element: cardRef fuer
  // den Mirror-Mousemove-Effekt, setCardRef fuer die Positions-Messung im
  // Parent (Linienberechnung).
  const handleRef = useCallback(
    (el: HTMLAnchorElement | null) => {
      cardRef.current = el
      setCardRef(el)
    },
    [setCardRef],
  )

  const zone =
    authenticated && isAdminSummary(caseItem) && !caseItem.evaluation_pending
      ? caseItem.zone
      : null

  return (
    <Link
      ref={handleRef}
      href={`/cases/${caseItem.id}`}
      onMouseMove={handleMouseMove}
      className="mirror idea-float absolute block w-52 cursor-pointer rounded-xl border border-border bg-card p-3 shadow-sm outline-none transition-colors hover:border-[var(--brand-accent)] focus-visible:ring-2 focus-visible:ring-[var(--brand-accent)]"
      style={{
        left: CARD_POSITIONS[index].left,
        top: CARD_POSITIONS[index].top,
        animationDelay: `${index * 0.6}s`,
      }}
    >
      <p className="line-clamp-2 text-[13px] font-medium leading-snug text-foreground">
        {caseItem.title}
      </p>
      {zone !== null ? (
        <div className="mt-2">
          <ZoneBadge zone={zone} />
        </div>
      ) : null}
    </Link>
  )
}

export function CasesHero({
  cases,
  authenticated,
}: {
  cases: CaseSummaryView[]
  authenticated: boolean
}) {
  const t = useTranslations("cases")
  const [picked, setPicked] = useState<CaseSummaryView[] | null>(null)
  const [pathD, setPathD] = useState<string | null>(null)
  const [dims, setDims] = useState({ width: 0, height: 0 })
  const containerRef = useRef<HTMLDivElement | null>(null)
  const cardRefs = useRef<(HTMLAnchorElement | null)[]>([])

  useEffect(() => {
    setPicked(shuffle(cases).slice(0, 3))
  }, [cases])

  useLayoutEffect(() => {
    if (!picked || picked.length < 2) {
      setPathD(null)
      return
    }

    function measure() {
      const container = containerRef.current
      if (!container || !picked) return
      const containerRect = container.getBoundingClientRect()
      const points: Point[] = []
      for (let i = 0; i < picked.length; i++) {
        const el = cardRefs.current[i]
        if (!el) return
        points.push(cardAnchor(i, el.getBoundingClientRect(), containerRect))
      }
      setDims({ width: containerRect.width, height: containerRect.height })
      setPathD(buildSmoothPath(points))
    }

    measure()

    let resizeTimer: ReturnType<typeof setTimeout> | undefined
    function handleResize() {
      if (resizeTimer) clearTimeout(resizeTimer)
      resizeTimer = setTimeout(measure, 100)
    }
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
      if (resizeTimer) clearTimeout(resizeTimer)
    }
  }, [picked])

  if (picked === null) {
    return null
  }
  if (picked.length === 0) {
    return null
  }

  return (
    <div className="hidden sm:block">
      <p className="eyebrow mb-3">{t("heroHeading")}</p>
      <div ref={containerRef} className="animate-view-enter relative mt-8 h-48 w-full">
        <div className="pipeline-glow" aria-hidden />
        <svg viewBox={`0 0 ${dims.width} ${dims.height}`} className="size-full overflow-visible">
          {pathD !== null ? (
            <path
              className="pipeline-path"
              fill="none"
              stroke="var(--brand-accent)"
              strokeWidth="1.4"
              d={pathD}
            />
          ) : null}
        </svg>
        {picked.map((caseItem, i) => (
          <IdeaCard
            key={caseItem.id}
            caseItem={caseItem}
            index={i}
            authenticated={authenticated}
            setCardRef={(el) => {
              cardRefs.current[i] = el
            }}
          />
        ))}
      </div>
    </div>
  )
}

export default CasesHero
