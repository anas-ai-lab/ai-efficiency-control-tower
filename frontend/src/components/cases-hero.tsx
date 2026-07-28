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

// Ankerpunkte am Kartenrand, in Container-Koordinaten: "Anfang" = linke
// Kante, "Ende" = rechte Kante, unabhaengig von der vertikalen Position der
// Karte im Flow. Damit ergeben sich fuer 3 Karten vier feste Ankerpunkte --
// Ende Karte 1 -> Anfang Karte 2 -> Ende Karte 2 -> Anfang Karte 3 --, deren
// mittleres Segment (innerhalb Karte 2) von der Karte selbst verdeckt wird
// (die Karten liegen im DOM nach dem SVG und damit optisch darueber).
function leftMid(rect: DOMRect, containerRect: DOMRect): Point {
  return { x: rect.left - containerRect.left, y: rect.top + rect.height / 2 - containerRect.top }
}

function rightMid(rect: DOMRect, containerRect: DOMRect): Point {
  return { x: rect.right - containerRect.left, y: rect.top + rect.height / 2 - containerRect.top }
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

  // Messung ausschliesslich im Effect (nie im Render) -- die Ankerpunkte
  // haengen von echten, gelayouteten Kartenmassen ab, die es vor dem Mount
  // noch nicht gibt. ResizeObserver auf Container UND jeder einzelnen Karte
  // (statt einem globalen window-resize-Listener): eine Karte kann ihre
  // Groesse auch ohne Fensteraenderung wechseln (z. B. Textumbruch nach
  // Sprachwechsel), das faengt nur eine Beobachtung der Karten selbst ab.
  // Zusaetzlich einmal nach document.fonts.ready neu gemessen -- vor dem
  // Font-Load stehen die Karten in der Fallback-Schrift, ihre Breite (und
  // damit die Ankerpunkte) verschiebt sich beim Nachladen.
  useLayoutEffect(() => {
    if (!picked || picked.length < 2) {
      setPathD(null)
      return
    }

    function measure() {
      const container = containerRef.current
      if (!container || !picked) return
      const containerRect = container.getBoundingClientRect()
      const cardRects: DOMRect[] = []
      for (let i = 0; i < picked.length; i++) {
        const el = cardRefs.current[i]
        if (!el) return
        cardRects.push(el.getBoundingClientRect())
      }

      // 3 Karten -> vier feste Ankerpunkte (Ende 1 -> Anfang 2 -> Ende 2 ->
      // Anfang 3). Weniger Karten (Edge-Case bei wenigen Einreichungen) ->
      // einfache Punkt-zu-Punkt-Verbindung ueber Ende/Anfang.
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
  }, [picked])

  if (picked === null) {
    return null
  }
  if (picked.length === 0) {
    return null
  }

  return (
    // mt-8: eine Abstandsstufe zum Lead-Absatz darueber (Ideenliste, /cases) --
    // vorher lag "Top 3 Use Cases" ohne jeden Zwischenraum direkt am Lead-Text.
    <div className="mt-8 hidden sm:block">
      <p className="eyebrow mb-3">{t("heroHeading")}</p>
      <div ref={containerRef} className="animate-view-enter relative mt-8 h-48 w-full">
        {/* Overlay erst nach der ersten Messung: vorher gibt es keine echten
            Ankerpunkte, ein Rendern ohne Pfad wuerde beim Nachziehen der
            Linie sichtbar springen. */}
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
