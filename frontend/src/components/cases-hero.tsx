"use client"

import { useEffect, useRef, useState } from "react"

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

// Kurve mit 3 statt 4 Stationen (Design-Reset-Pipeline-Visual als Vorlage,
// siehe pipeline-strip.tsx).
const PIPELINE_PATH = "M14 150 C 70 128, 100 78, 160 70 S 260 30, 300 30"

// Kartenpositionen im Container, prozentual an dieselbe Kurve angelehnt
// (links unten -> rechts oben).
const CARD_POSITIONS = [
  { left: "2%", top: "48%" },
  { left: "36%", top: "18%" },
  { left: "68%", top: "0%" },
]

function IdeaCard({
  caseItem,
  index,
  authenticated,
}: {
  caseItem: CaseSummaryView
  index: number
  authenticated: boolean
}) {
  const cardRef = useRef<HTMLDivElement | null>(null)

  function handleMouseMove(event: React.MouseEvent<HTMLDivElement>) {
    const el = cardRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty("--mx", `${event.clientX - rect.left}px`)
    el.style.setProperty("--my", `${event.clientY - rect.top}px`)
  }

  const zone =
    authenticated && isAdminSummary(caseItem) && !caseItem.evaluation_pending
      ? caseItem.zone
      : null

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      className="mirror idea-float absolute w-52 rounded-xl border border-border bg-card p-3 shadow-sm"
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
    </div>
  )
}

export function CasesHero({
  cases,
  authenticated,
}: {
  cases: CaseSummaryView[]
  authenticated: boolean
}) {
  const [picked, setPicked] = useState<CaseSummaryView[] | null>(null)

  useEffect(() => {
    setPicked(shuffle(cases).slice(0, 3))
  }, [cases])

  if (picked === null) {
    return null
  }
  if (picked.length === 0) {
    return null
  }

  return (
    <div className="animate-view-enter relative mt-8 hidden h-48 w-full sm:block">
      <div className="pipeline-glow" aria-hidden />
      <svg viewBox="0 0 320 190" preserveAspectRatio="none" className="size-full overflow-visible">
        <path
          className="pipeline-path"
          fill="none"
          stroke="var(--brand-accent)"
          strokeWidth="1.4"
          d={PIPELINE_PATH}
        />
      </svg>
      {picked.map((caseItem, i) => (
        <IdeaCard
          key={caseItem.id}
          caseItem={caseItem}
          index={i}
          authenticated={authenticated}
        />
      ))}
    </div>
  )
}

export default CasesHero
