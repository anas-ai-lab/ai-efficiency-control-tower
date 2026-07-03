"use client"

import { SharpenedCaseResponse } from "@/types/api"
import { LlmAction } from "@/components/llm-action"

interface SharpenedViewProps {
  result: SharpenedCaseResponse
  onPropose: () => void
  isProposeLoading: boolean
  proposeError: string | null
}

function Field({
  label,
  value,
  emphasis,
}: {
  label: string
  value: string
  emphasis?: boolean
}) {
  return (
    <div>
      <p className="mb-1 text-xs text-muted-foreground">{label}</p>
      <p
        className={
          emphasis
            ? "text-sm leading-relaxed font-medium text-foreground"
            : "text-sm leading-relaxed text-muted-foreground"
        }
      >
        {value}
      </p>
    </div>
  )
}

export function SharpenedView({
  result,
  onPropose,
  isProposeLoading,
  proposeError,
}: SharpenedViewProps) {
  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow mb-1.5">Was passiert hier</p>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Die KI schärft deine Beschreibung. Das Original bleibt links
          unverändert erhalten, rechts steht die geschärfte Fassung mit
          konkreten Verbesserungsvorschlägen.
        </p>
      </div>

      {result.sharpened_title !== null ? (
        <>
          {/* Original vs. geschaerft als zwei klar getrennte Spuren. */}
          <div className="grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-border bg-border md:grid-cols-2">
            <div className="bg-card p-5 sm:p-6">
              <p className="eyebrow mb-4">Original</p>
              <div className="space-y-4">
                <Field label="Titel" value={result.original_title} />
                <Field label="Ist-Zustand" value={result.original_current_state} />
                <Field label="Soll-Zustand" value={result.original_desired_state} />
              </div>
            </div>
            <div className="relative bg-card p-5 sm:p-6">
              <span
                className="absolute inset-y-0 left-0 hidden w-0.5 bg-[var(--ink)] md:block"
                aria-hidden
              />
              <p className="eyebrow mb-4 text-[var(--ink)]">Geschärft</p>
              <div className="space-y-4">
                <Field label="Titel" value={result.sharpened_title} emphasis />
                <Field
                  label="Ist-Zustand"
                  value={result.sharpened_current_state ?? ""}
                  emphasis
                />
                <Field
                  label="Soll-Zustand"
                  value={result.sharpened_desired_state ?? ""}
                  emphasis
                />
              </div>
            </div>
          </div>

          {result.improvement_suggestions.length > 0 && (
            <section>
              <p className="eyebrow mb-3">Verbesserungsvorschläge</p>
              <ol className="space-y-2.5">
                {result.improvement_suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-[var(--ink-subtle)] text-[0.7rem] font-semibold tnum text-[var(--ink)]">
                      {index + 1}
                    </span>
                    <p className="text-sm leading-relaxed text-foreground/90">
                      {suggestion}
                    </p>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </>
      ) : (
        <>
          <div className="rounded-xl border border-[var(--zone-risk-border)] bg-[var(--zone-risk-surface)] px-4 py-3 text-sm font-medium text-[var(--zone-risk-fg)]">
            Strukturiertes Schärfen nicht verfügbar
          </div>
          {result.raw_text !== null && (
            <pre className="overflow-x-auto rounded-xl border border-border bg-muted/40 p-4 text-sm whitespace-pre-wrap">
              {result.raw_text}
            </pre>
          )}
        </>
      )}

      <div className="border-t border-border pt-6">
        <LlmAction
          onAction={onPropose}
          isLoading={isProposeLoading}
          idleLabel="Lösungsvorschlag generieren"
          loadingLabel="Lösungsvorschlag wird erstellt …"
          hint="KI entwirft einen Umsetzungsweg · 5–30 Sekunden"
          error={proposeError}
        />
      </div>
    </div>
  )
}

export default SharpenedView
