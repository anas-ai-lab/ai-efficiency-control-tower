"use client"

import { useEffect, useRef, useState } from "react"
import { useLocale } from "next-intl"

import { ZoneBadge } from "@/components/status-badge"
import type { TriageZone } from "@/types/api"

// Rein dekoratives Hero-Visual fuer /cases: SVG-Flow-Linie mit 3 schwebenden
// fiktiven Idea-Karten. Kein Datenpfad, kein Case-Bezug -- die Titel kommen
// aus IDEA_POOL (aect-context.md §5: nie echte Cases oeffentlich).
//
// Die Zufallsauswahl passiert bewusst erst nach dem Mount (useEffect), nicht
// im ersten Render: Server und Client wuerden sonst unterschiedliche Werte
// wuerfeln und einen Hydration-Mismatch ausloesen.

interface FictionalIdea {
  titleDe: string
  titleEn: string
  zone: TriageZone
}

const IDEA_POOL: FictionalIdea[] = [
  {
    titleDe: "Automatisierte Vertragspruefung",
    titleEn: "Automated contract review",
    zone: "LIKELY_WIN",
  },
  {
    titleDe: "Intelligente Ticket-Vorklassifizierung",
    titleEn: "Intelligent ticket pre-classification",
    zone: "LIKELY_WIN",
  },
  {
    titleDe: "KI-gestuetzte Angebotspruefung",
    titleEn: "AI-assisted quote review",
    zone: "CALCULATED_RISK",
  },
  {
    titleDe: "Automatisierte Protokollzusammenfassung",
    titleEn: "Automated meeting minutes summary",
    zone: "MARGINAL_GAIN",
  },
  {
    titleDe: "Vorpruefung von Onboarding-Unterlagen",
    titleEn: "Pre-check of onboarding documents",
    zone: "LIKELY_WIN",
  },
  {
    titleDe: "Intelligentes Rechnungs-Matching",
    titleEn: "Intelligent invoice matching",
    zone: "CALCULATED_RISK",
  },
  {
    titleDe: "KI-Vorsortierung von Bewerbungen",
    titleEn: "AI pre-sorting of applications",
    zone: "MARGINAL_GAIN",
  },
  {
    titleDe: "Automatisierte Report-Zusammenfassung",
    titleEn: "Automated report summarization",
    zone: "CALCULATED_RISK",
  },
]

function shuffle<T>(items: T[]): T[] {
  const result = [...items]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

// Kurve mit 3 statt 4 Stationen (Design-Reset-Pipeline-Visual als Vorlage,
// siehe pipeline-strip.tsx). Alle 3 Knoten sind Segment-Anker (M-Start,
// C-Ende, S-Ende) und liegen dadurch per Konstruktion exakt auf dem Pfad --
// kein Nachmessen per getPointAtLength noetig (anders als die interpolierten
// Zwischen-Knoten im Original).
const PIPELINE_PATH = "M14 150 C 70 128, 100 78, 160 70 S 260 30, 300 30"
const NODES: [number, number][] = [
  [14, 150],
  [160, 70],
  [300, 30],
]

// Kartenpositionen im Container, prozentual an dieselbe Kurve angelehnt
// (links unten -> rechts oben).
const CARD_POSITIONS = [
  { left: "2%", top: "48%" },
  { left: "36%", top: "18%" },
  { left: "68%", top: "0%" },
]

function IdeaCard({
  idea,
  index,
  label,
}: {
  idea: FictionalIdea
  index: number
  label: string
}) {
  const cardRef = useRef<HTMLDivElement | null>(null)

  function handleMouseMove(event: React.MouseEvent<HTMLDivElement>) {
    const el = cardRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty("--mx", `${event.clientX - rect.left}px`)
    el.style.setProperty("--my", `${event.clientY - rect.top}px`)
  }

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
      <p className="text-[13px] font-medium leading-snug text-foreground">
        {label}
      </p>
      <div className="mt-2">
        <ZoneBadge zone={idea.zone} />
      </div>
    </div>
  )
}

export function CasesHero() {
  const locale = useLocale()
  const [picked, setPicked] = useState<FictionalIdea[] | null>(null)

  useEffect(() => {
    setPicked(shuffle(IDEA_POOL).slice(0, 3))
  }, [])

  if (picked === null) {
    return null
  }

  return (
    <div className="animate-view-enter relative mt-8 hidden h-48 w-full sm:block">
      <div className="pipeline-glow" aria-hidden />
      <svg viewBox="0 0 320 190" className="size-full overflow-visible">
        <path
          className="pipeline-path"
          fill="none"
          stroke="var(--brand-accent)"
          strokeWidth="1.4"
          d={PIPELINE_PATH}
        />
        {NODES.map(([cx, cy], i) => (
          <g key={i}>
            <circle
              className="pipeline-ring"
              cx={cx}
              cy={cy}
              r="6"
              fill="none"
              stroke="var(--brand-accent)"
              strokeWidth="1.2"
              style={{ animationDelay: `${i * 0.8}s` }}
            />
            <circle cx={cx} cy={cy} r="4.5" fill="var(--brand-accent)" />
          </g>
        ))}
      </svg>
      {picked.map((idea, i) => (
        <IdeaCard
          key={idea.titleDe}
          idea={idea}
          index={i}
          label={locale === "de" ? idea.titleDe : idea.titleEn}
        />
      ))}
    </div>
  )
}

export default CasesHero
