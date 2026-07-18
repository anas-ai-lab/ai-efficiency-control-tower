"use client"

import { useEffect, useRef, useState } from "react"

// Pipeline-Visual der Startseite (Design-Reset v4.3): die vier Stationen
// Regeln -> RAG -> LLM -> Mensch als steigende Kurve, darunter die zyklisch
// hervorgehobene Legende und der Leitsatz.
//
// Anders als die v4.2-Fassung ist das hier eine Client-Komponente: der
// Legenden-Zyklus braucht einen Timer und der Parallax eine Mausposition.
// Beides ist reine Praesentation -- es wandert kein Datenpfad ins Bundle.
//
// Der Parallax schreibt direkt auf innerRef.style.transform statt ueber
// useState: eine Zustands-Aktualisierung pro mousemove-Event waere ein
// Re-Render pro Frame.
//
// Der Glow ist laut frontend/CLAUDE.md ausschliesslich an dieser Stelle
// erlaubt (radial, sehr geringe Deckkraft, --brand-accent).
export function PipelineStrip({
  steps,
  caption,
}: {
  steps: [string, string, string, string]
  caption: string
}) {
  const innerRef = useRef<HTMLDivElement | null>(null)
  const [activeIdx, setActiveIdx] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setActiveIdx((i) => (i + 1) % steps.length)
    }, 800)
    return () => clearInterval(id)
  }, [steps.length])

  function handleMouseMove(event: React.MouseEvent<HTMLDivElement>) {
    const el = event.currentTarget
    const rect = el.getBoundingClientRect()
    const relX = (event.clientX - rect.left) / rect.width - 0.5
    const relY = (event.clientY - rect.top) / rect.height - 0.5
    if (innerRef.current) {
      innerRef.current.style.transform = `translate(${relX * 10}px, ${relY * 7}px)`
    }
  }

  function handleMouseLeave() {
    if (innerRef.current) innerRef.current.style.transform = "translate(0,0)"
  }

  // Knoten-Koordinaten im viewBox-Raum, in Reihenfolge der vier Stationen.
  // Sie MUESSEN auf der Kurve des d-Attributs unten liegen -- die beiden
  // mittleren Werte lagen zuerst daneben (6 bzw. 14 Einheiten, am Bildschirm
  // sichtbar). Bei Aenderungen am Pfad gegen path.getPointAtLength() pruefen,
  // nicht schaetzen.
  const nodes: [number, number][] = [
    [14, 150],
    [132, 84],
    [222, 60],
    [300, 34],
  ]

  return (
    <div className="mt-10 rounded-2xl border border-[var(--hairline-rule)] bg-card p-6">
      <div
        className="relative h-44"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div className="pipeline-glow" aria-hidden />
        <div ref={innerRef} className="relative size-full">
          <svg viewBox="0 0 320 190" className="size-full overflow-visible">
            <path
              className="pipeline-path"
              fill="none"
              stroke="var(--brand-accent)"
              strokeWidth="1.4"
              d="M14 150 C 70 132, 90 82, 150 82 S 240 34, 300 34"
            />
            {nodes.map(([cx, cy], i) => (
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
        </div>
      </div>
      <div className="mt-3 flex justify-between border-t border-[var(--hairline-rule)] pt-3">
        {steps.map((label, i) => (
          <span
            key={label}
            className={
              i === activeIdx
                ? "font-mono text-[11px] font-medium text-[var(--brand-accent)] transition-colors"
                : "font-mono text-[11px] text-muted-foreground transition-colors"
            }
          >
            {label}
          </span>
        ))}
      </div>
      <p className="mt-5 max-w-prose border-l-2 border-[var(--hairline-accent)] pl-4 text-[15px] italic leading-relaxed text-foreground/80">
        {caption}
      </p>
    </div>
  )
}

export default PipelineStrip
