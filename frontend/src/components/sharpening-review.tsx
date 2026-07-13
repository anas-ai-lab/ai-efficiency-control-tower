"use client"

import { useMemo, useState } from "react"
import { diffWords, type Change } from "diff"
import { AlignLeft, Check, Columns2, Sparkles, X } from "lucide-react"

import type { SharpenedCaseResponse } from "@/types/api"
import { acceptSharpening, rejectSharpening } from "@/app/actions"
import { CASE_FIELD_LABELS } from "@/lib/labels"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// Admin-Diff-Ansicht fuer einen Schaerfungs-Entwurf (V4). Feldweise Original vs.
// Entwurf. Zwei Darstellungen:
//   - "inline": interleaved Wort-Diff (jsdiff) -- gut bei punktuellen Aenderungen.
//   - "split": zwei ruhige Spalten (Vorher | Nachher) -- jede Spalte liest sich
//     als zusammenhaengender Text. Notwendig, weil ein fast vollstaendiger
//     Rewrite im Inline-Diff zum unlesbaren Farbteppich wird ("wall of colour").
// Der Startmodus wird automatisch gewaehlt: uebersteigt der Aenderungsanteil
// (churn) eines Feldes REWRITE_THRESHOLD, startet die Ansicht in "split".

type DiffMode = "inline" | "split"

// Ab diesem Aenderungsanteil (geaenderte Zeichen / Gesamtzeichen) gilt ein Feld
// als starker Rewrite -> Nebeneinander-Ansicht ist dann per Default aktiv.
const REWRITE_THRESHOLD = 0.5

interface FieldDiff {
  parts: Change[]
  churn: number
}

function computeDiff(original: string, sharpened: string): FieldDiff {
  const parts = diffWords(original, sharpened)
  let changed = 0
  for (const part of parts) {
    if (part.added || part.removed) changed += part.value.length
  }
  const total = original.length + sharpened.length
  return { parts, churn: total > 0 ? changed / total : 0 }
}

// Inline: entfernte Woerter durchgestrichen (Rot-Token), neue Woerter
// hervorgehoben (Gruen-Token), Unveraendertes ruhig.
function InlineDiff({ parts }: { parts: Change[] }) {
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

// Split: zwei Spalten. Links der Original-Text (Loeschungen markiert, Rest
// gedaempft), rechts der Entwurf (Einfuegungen markiert, Rest voll). Jede Spalte
// enthaelt nur ihre eigene Fassung -- kein interleaving, daher auch bei einem
// kompletten Rewrite lesbar. Auf Mobile untereinander (Vorher ueber Nachher).
function SplitDiff({ parts }: { parts: Change[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <div className="rounded-lg border border-border bg-muted/20 p-3.5">
        <p className="eyebrow mb-2">Vorher</p>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {parts.map((part, i) => {
            if (part.added) return null
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
              <span key={i} className="text-muted-foreground">
                {part.value}
              </span>
            )
          })}
        </p>
      </div>
      <div className="rounded-lg border border-[var(--zone-win-border)] bg-[var(--zone-win-surface)]/40 p-3.5">
        <p className="eyebrow mb-2">Nachher</p>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {parts.map((part, i) => {
            if (part.removed) return null
            if (part.added) {
              return (
                <span
                  key={i}
                  className="rounded-sm bg-[var(--zone-win-surface)] font-medium text-[var(--zone-win-fg)]"
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
      </div>
    </div>
  )
}

function DiffField({
  label,
  diff,
  mode,
}: {
  label: string
  diff: FieldDiff
  mode: DiffMode
}) {
  const strongRewrite = diff.churn >= REWRITE_THRESHOLD
  return (
    <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="eyebrow">{label}</p>
        {strongRewrite && (
          <span className="font-mono text-[0.6875rem] text-muted-foreground tabular-nums">
            {Math.round(diff.churn * 100)} % überarbeitet
          </span>
        )}
      </div>
      {mode === "split" ? (
        <SplitDiff parts={diff.parts} />
      ) : (
        <InlineDiff parts={diff.parts} />
      )}
    </div>
  )
}

// Segmentierter Schalter Inline <-> Nebeneinander (aktiver Zustand in Tinte).
function ModeToggle({
  mode,
  onChange,
}: {
  mode: DiffMode
  onChange: (mode: DiffMode) => void
}) {
  const options: { value: DiffMode; label: string; icon: typeof AlignLeft }[] = [
    { value: "inline", label: "Inline", icon: AlignLeft },
    { value: "split", label: "Nebeneinander", icon: Columns2 },
  ]
  return (
    <div className="inline-flex rounded-lg border border-border bg-background p-0.5">
      {options.map((option) => {
        const Icon = option.icon
        const active = mode === option.value
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            aria-pressed={active}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring/40",
              active
                ? "bg-[var(--ink-subtle)] text-[var(--ink)]"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon className="size-3.5" aria-hidden />
            {option.label}
          </button>
        )
      })}
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

  // S4: Schaerfung nur ueber die Soll-Felder -> nur diese im Diff.
  const fields = useMemo(
    () => [
      {
        label: "Soll-Zustand",
        diff: computeDiff(
          sharpened.original_desired_state,
          sharpened.sharpened_desired_state,
        ),
      },
      {
        label: "Soll-Beispiel",
        diff: computeDiff(
          sharpened.original_desired_example_process,
          sharpened.sharpened_desired_example_process,
        ),
      },
    ],
    [sharpened],
  )

  // Staerkster Rewrite ueber alle Felder entscheidet ueber den Startmodus.
  const maxChurn = Math.max(...fields.map((f) => f.diff.churn))
  const autoSplit = maxChurn >= REWRITE_THRESHOLD
  const [mode, setMode] = useState<DiffMode>(autoSplit ? "split" : "inline")

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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-[var(--ink)]" />
          <p className="text-sm font-semibold text-foreground">
            Schärfungs-Entwurf — bitte prüfen
          </p>
        </div>
        <ModeToggle mode={mode} onChange={setMode} />
      </div>
      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
        Grün = neu vorgeschlagen, durchgestrichen = entfernt. Der Entwurf wird
        erst nach „Übernehmen“ gespeichert.
        {autoSplit && (
          <>
            {" "}
            Starke Überarbeitung erkannt — Nebeneinander-Ansicht ist
            voreingestellt.
          </>
        )}
      </p>

      <div className="mt-4 space-y-3">
        {fields.map((f) => (
          <DiffField key={f.label} label={f.label} diff={f.diff} mode={mode} />
        ))}
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
