"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { useCallback, useLayoutEffect, useRef, useState } from "react"

import type { TopCaseResponse } from "@/types/api"

// Rein dekoratives Hero-Visual fuer /cases: SVG-Flow-Linie mit den (bis zu) 3
// Cases mit dem hoechsten Netto-Nutzen, geliefert vom oeffentlichen GET
// /cases/top (Ticket 4b) -- der Geldwert selbst kommt dort nie mit, siehe
// TopCaseResponse. Die Auswahl ist server-seitig deterministisch sortiert --
// anders als die fruehere Zufallsauswahl braucht es keinen Post-Mount-Pick
// mehr, die Karten rendern direkt aus der Prop, auch schon bei SSR.

const CARD_POSITIONS = [
  { left: "2%", top: "48%" },
  { left: "36%", top: "18%" },
  { left: "68%", top: "0%" },
]

interface Point {
  x: number
  y: number
}

// Ankerpunkte am Kartenrand, in Container-Koordinaten: "Anfang" = linke
// Kante, "Ende" = rechte Kante, unabhaengig von der vertikalen Position der
// Karte im Flow.
function leftMid(rect: DOMRect, containerRect: DOMRect): Point {
  return { x: rect.left - containerRect.left, y: rect.top + rect.height / 2 - containerRect.top }
}

function rightMid(rect: DOMRect, containerRect: DOMRect): Point {
  return { x: rect.right - containerRect.left, y: rect.top + rect.height / 2 - containerRect.top }
}

function tangentAt(points: Point[], i: number): Point {
  const prev = points[i - 1] ?? points[i]
  const next = points[i + 1] ?? points[i]
  return { x: (next.x - prev.x) / 2, y: (next.y - prev.y) / 2 }
}

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
  setCardRef,
}: {
  caseItem: TopCaseResponse
  index: number
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

  const handleRef = useCallback(
    (el: HTMLAnchorElement | null) => {
      cardRef.current = el
      setCardRef(el)
    },
    [setCardRef],
  )

  return (
    <Link
      ref={handleRef}
      href={`/cases/${caseItem.case_id}`}
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
    </Link>
  )
}

export function CasesHero({ topCases }: { topCases: TopCaseResponse[] }) {
  const t = useTranslations("cases")
  const [pathD, setPathD] = useState<string | null>(null)
  const [dims, setDims] = useState({ width: 0, height: 0 })
  const containerRef = useRef<HTMLDivElement | null>(null)
  const cardRefs = useRef<(HTMLAnchorElement | null)[]>([])

  useLayoutEffect(() => {
    if (topCases.length < 2) {
      setPathD(null)
      return
    }

    function measure() {
      const container = containerRef.current
      if (!container) return
      const containerRect = container.getBoundingClientRect()
      const cardRects: DOMRect[] = []
      for (let i = 0; i < topCases.length; i++) {
        const el = cardRefs.current[i]
        if (!el) return
        cardRects.push(el.getBoundingClientRect())
      }

      const points: Point[] =
        cardRects.length >= 3
          ? [
              rightMid(cardRects[0], containerRect),
              leftMid(cardRects[1], containerRect),
              rightMid(cardRects[1], containerRect),
              leftMid(cardRects[2], containerRect),
            ]
          : [rightMid(cardRects[0], containerRect), leftMid(cardRects[1], containerRect)]

      setDims({ width: containerRect.width, height: containerRect.height })
      setPathD(buildSmoothPath(points))
    }

    measure()

    const container = containerRef.current
    const observer = new ResizeObserver(() => measure())
    if (container) observer.observe(container)
    for (const el of cardRefs.current) {
      if (el) observer.observe(el)
    }

    let cancelled = false
    document.fonts.ready.then(() => {
      if (!cancelled) measure()
    })

    return () => {
      cancelled = true
      observer.disconnect()
    }
  }, [topCases])

  if (topCases.length === 0) {
    return null
  }

  return (
    <div className="mt-8 hidden sm:block">
      <p className="eyebrow mb-3">{t("heroHeading")}</p>
      <div ref={containerRef} className="animate-view-enter relative mt-8 h-48 w-full">
        {pathD !== null && (
          <>
            <div className="pipeline-glow" aria-hidden />
            <svg viewBox={`0 0 ${dims.width} ${dims.height}`} className="size-full overflow-visible">
              <path
                className="pipeline-path"
                fill="none"
                stroke="var(--brand-accent)"
                strokeWidth="1.4"
                d={pathD}
              />
            </svg>
          </>
        )}
        {topCases.map((caseItem, i) => (
          <IdeaCard
            key={caseItem.case_id}
            caseItem={caseItem}
            index={i}
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
