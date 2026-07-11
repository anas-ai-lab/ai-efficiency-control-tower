"use client"

import { useState } from "react"
import { diffWords } from "diff"
import { Check, Sparkles, X } from "lucide-react"

import type { SharpenedCaseResponse } from "@/types/api"
import { acceptSharpening, rejectSharpening } from "@/app/actions"
import { CASE_FIELD_LABELS } from "@/lib/labels"
import { Button } from "@/components/ui/button"

// Admin-Diff-Ansicht fuer einen Schaerfungs-Entwurf (V4). Original vs. Entwurf
// feldweise als Inline-Wort-Diff (jsdiff): entfernte Woerter durchgestrichen,
// neue Woerter hervorgehoben. Uebernehmen/Verwerfen rufen accept/reject; danach
// meldet onResolved dem Elternteil, dass der Draft weg ist (router.refresh).

function WordDiff({ original, sharpened }: { original: string; sharpened: string }) {
  const parts = diffWords(original, sharpened)
  return (
    <p className="text-sm leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) => {
        if (part.added) {
          return (
            <span
              key={i}
              className="rounded-sm bg-[var(--zone-win-surface)] text-[var(--zone-win-fg)]"
            >
              {part.value}
            </span>
          )
        }
        if (part.removed) {
          return (
            <span
              key={i}
              className="rounded-sm bg-[var(--zone-gain-surface)] text-[var(--zone-gain-fg)] line-through decoration-1"
            >
              {part.value}
            </span>
          )
        }
        return (
          <span key={i} className="text-foreground/90">
            {part.value}
          </span>
        )
      })}
    </p>
  )
}

function DiffField({
  label,
  original,
  sharpened,
}: {
  label: string
  original: string
  sharpened: string
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
      <p className="eyebrow mb-3">{label}</p>
      <WordDiff original={original} sharpened={sharpened} />
    </div>
  )
}

export function SharpeningReview({
  sharpened,
  onResolved,
}: {
  sharpened: SharpenedCaseResponse
  onResolved: () => void
}) {
  const [pending, setPending] = useState<"accept" | "reject" | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function resolve(action: "accept" | "reject") {
    setPending(action)
    setError(null)
    try {
      if (action === "accept") {
        await acceptSharpening(sharpened.case_id)
      } else {
        await rejectSharpening(sharpened.case_id)
      }
      onResolved()
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Aktion konnte nicht ausgeführt werden.",
      )
      setPending(null)
    }
  }

  return (
    <section className="rounded-2xl border border-[var(--ink)]/25 bg-[var(--ink-subtle)]/40 p-5">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-[var(--ink)]" />
        <p className="text-sm font-semibold text-foreground">
          Schärfungs-Entwurf — bitte prüfen
        </p>
      </div>
      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
        Grün = neu vorgeschlagen, durchgestrichen = entfernt. Der Entwurf wird
        erst nach „Übernehmen“ gespeichert.
      </p>

      <div className="mt-4 space-y-3">
        <DiffField
          label="Titel"
          original={sharpened.original_title}
          sharpened={sharpened.sharpened_title}
        />
        <DiffField
          label="Ist-Zustand"
          original={sharpened.original_current_state}
          sharpened={sharpened.sharpened_current_state}
        />
        <DiffField
          label="Soll-Zustand"
          original={sharpened.original_desired_state}
          sharpened={sharpened.sharpened_desired_state}
        />
      </div>

      {/* Verbesserungsvorschlaege: Bezugsfeld-Badge + Vorschlag + Hebel. */}
      {sharpened.improvement_suggestions.length > 0 && (
        <div className="mt-5">
          <p className="eyebrow mb-2">Vorschläge</p>
          <ul className="space-y-2.5">
            {sharpened.improvement_suggestions.map((s, i) => (
              <li key={i} className="rounded-xl border border-border bg-card p-4">
                <span className="inline-flex items-center rounded-md border border-[var(--ink)]/25 bg-[var(--ink-subtle)] px-2 py-0.5 text-xs font-medium text-[var(--ink)]">
                  {CASE_FIELD_LABELS[s.bezugsfeld] ?? s.bezugsfeld}
                </span>
                <p className="mt-2 text-sm leading-relaxed text-foreground/90">
                  {s.vorschlag}
                </p>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                  <span className="font-medium text-foreground/70">Hebel:</span>{" "}
                  {s.hebel}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {error !== null && (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      <div className="mt-5 flex flex-wrap gap-2">
        <Button onClick={() => resolve("accept")} disabled={pending !== null}>
          <Check className="size-4" />
          {pending === "accept" ? "Wird übernommen …" : "Übernehmen"}
        </Button>
        <Button
          variant="outline"
          onClick={() => resolve("reject")}
          disabled={pending !== null}
        >
          <X className="size-4" />
          {pending === "reject" ? "Wird verworfen …" : "Verwerfen"}
        </Button>
      </div>
    </section>
  )
}

export default SharpeningReview
