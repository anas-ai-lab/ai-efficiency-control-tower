"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { Loader2, Info } from "lucide-react"

import { generateIdeas } from "@/app/actions"
import { ContactCard } from "@/components/contact-card"
import type { IdeationDraft, IdeationResponse } from "@/types/api"
import {
  IDEATION_PREFILL_KEY,
  type IdeationPrefill,
} from "@/lib/ideation-prefill"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"

const MIN_LEN = 20
const MAX_LEN = 2000

// Einzelne Entwurfs-Karte. Ist/Soll/Beispiel werden per Default gekuerzt
// (line-clamp) und pro Karte gemeinsam aufgeklappt -- die Volltexte koennen je
// bis 2000 Zeichen lang sein und wuerden die Liste sonst unlesbar strecken.
function DraftCard({
  draft,
  onAdopt,
}: {
  draft: IdeationDraft
  onAdopt: (draft: IdeationDraft) => void
}) {
  const t = useTranslations("ideation")
  const [expanded, setExpanded] = useState(false)

  const fields: { label: string; text: string }[] = [
    { label: t("fieldCurrentState"), text: draft.current_state },
    { label: t("fieldDesiredState"), text: draft.desired_state },
    { label: t("fieldExample"), text: draft.example_process },
  ]

  return (
    <article className="rounded-xl border border-border bg-card p-5">
      <h3 className="text-base font-semibold tracking-tight text-foreground">
        {draft.title}
      </h3>

      <dl className="mt-4 space-y-3">
        {fields.map((f) => (
          <div key={f.label}>
            <dt className="text-xs font-medium text-muted-foreground">
              {f.label}
            </dt>
            <dd
              className={
                expanded
                  ? "mt-0.5 text-sm leading-relaxed whitespace-pre-line text-foreground"
                  : "mt-0.5 line-clamp-2 text-sm leading-relaxed text-foreground"
              }
            >
              {f.text}
            </dd>
          </div>
        ))}
      </dl>

      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="mt-2 text-xs font-medium text-[var(--ink)] underline-offset-4 hover:underline"
      >
        {expanded ? t("showLess") : t("showMore")}
      </button>

      <p className="mt-4 border-t border-border/60 pt-3 text-sm leading-relaxed text-muted-foreground">
        {draft.rationale}
      </p>

      {draft.open_questions.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-semibold tracking-tight text-foreground">
            {t("openQuestions")}
          </h4>
          <ul className="mt-1.5 space-y-1">
            {draft.open_questions.map((q, i) => (
              <li
                key={i}
                className="flex gap-2 text-sm leading-relaxed text-muted-foreground"
              >
                <span aria-hidden className="mt-2 size-1 shrink-0 rounded-full bg-muted-foreground/50" />
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onAdopt(draft)}
        >
          {t("adopt")}
        </Button>
      </div>
    </article>
  )
}

export function IdeationView() {
  const t = useTranslations("ideation")
  const tHint = useTranslations("llmAction")
  const router = useRouter()

  const [problem, setProblem] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<IdeationResponse | null>(null)
  // Zaehlt jeden abgeschlossenen Lauf -- dient nur als React-key, damit die
  // Stagger-Kaskade bei einem zweiten Klick erneut anlaeuft (gleiche Anzahl
  // Karten wuerde sonst nur re-rendern, nicht neu mounten).
  const [runId, setRunId] = useState(0)

  const length = problem.length
  const tooShort = problem.trim().length < MIN_LEN
  const canSubmit = !isLoading && !tooShort && length <= MAX_LEN

  async function handleGenerate() {
    if (!canSubmit) return
    setError(null)
    setIsLoading(true)
    try {
      // Neuer Klick ersetzt die Karten vollstaendig (D16, kein Verlauf).
      const res = await generateIdeas(problem)
      setResult(res)
      setRunId((n) => n + 1)
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"))
    } finally {
      setIsLoading(false)
    }
  }

  // Handoff ins Intake-Formular: NUR die qualitativen Felder in sessionStorage
  // ablegen (Whitelist -- keine Zahlen, D17). setItem ueberschreibt einen ggf.
  // vorhandenen Key vollstaendig (kein Merge): zwei Karten nacheinander ohne
  // Navigation dazwischen -> es gilt ausschliesslich der letzte Klick.
  function handleAdopt(draft: IdeationDraft) {
    const prefill: IdeationPrefill = {
      title: draft.title,
      current_state: draft.current_state,
      desired_state: draft.desired_state,
      example_process: draft.example_process,
    }
    try {
      sessionStorage.setItem(IDEATION_PREFILL_KEY, JSON.stringify(prefill))
    } catch {
      // sessionStorage nicht verfuegbar -> ohne Prefill weiter (Formular leer).
    }
    // Handoff in den Einreichen-Wizard (liest den Prefill-Key beim Mount, D16).
    router.push("/einreichen")
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10 sm:px-6 sm:py-12">
      <ContactCard />
      <header className="mb-8">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1 className="mt-2 text-pretty text-[1.65rem] font-semibold leading-tight tracking-tight text-foreground">
          {t("title")}
        </h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          {t("lead")}
        </p>
      </header>

      <div className="space-y-3">
        <div className="relative">
          <Textarea
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            maxLength={MAX_LEN}
            rows={6}
            disabled={isLoading}
            placeholder={t("placeholder")}
            aria-label={t("ariaProblem")}
          />
          <div className="mt-1.5 flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              {tooShort ? t("minChars", { min: MIN_LEN }) : t("hint")}
            </p>
            <p className="font-mono text-xs text-muted-foreground tabular-nums">
              {length} / {MAX_LEN}
            </p>
          </div>
        </div>

        {error != null && (
          <p
            role="alert"
            className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
          >
            {error}
          </p>
        )}

        {isLoading ? (
          <div
            role="status"
            aria-live="polite"
            className="overflow-hidden rounded-xl border border-border bg-card"
          >
            <div className="flex items-center gap-2.5 px-5 pt-4 pb-3 text-sm font-medium text-foreground">
              <Loader2 className="size-4 animate-spin text-[var(--ink)]" />
              {t("generating")}
            </div>
            <div
              className="progress-bar relative h-0.5 w-full overflow-hidden bg-border/60"
              aria-hidden
            />
            <div className="space-y-2.5 px-5 py-4">
              <Skeleton className="h-3 w-[92%]" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-[78%]" />
            </div>
            <p className="px-5 pb-4 text-xs text-muted-foreground tnum">
              {tHint("durationHint")}
            </p>
          </div>
        ) : (
          <Button
            type="button"
            size="xl"
            onClick={handleGenerate}
            disabled={!canSubmit}
            className="w-full"
          >
            {t("generate")}
          </Button>
        )}
      </div>

      {result != null && (
        <section className="mt-9">
          {result.flagged_input && (
            <p className="mb-4 flex items-start gap-2.5 rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm leading-relaxed text-muted-foreground">
              <Info aria-hidden className="mt-0.5 size-4 shrink-0" />
              <span>{t("flagged")}</span>
            </p>
          )}

          {result.drafts.length === 0 ? (
            <p className="text-sm leading-relaxed text-muted-foreground">
              {t("emptyResult")}
            </p>
          ) : (
            <>
              {/* stagger laesst die Entwuerfe nacheinander auflaufen -- so ist
                  sichtbar, dass mehrere erzeugt wurden. key an den Lauf
                  gebunden: ein neuer Klick spielt die Kaskade erneut ab.
                  Hinter prefers-reduced-motion (globals.css) gegatet. */}
              <div key={runId} className="stagger space-y-4">
                {result.drafts.map((draft, i) => (
                  <DraftCard key={i} draft={draft} onAdopt={handleAdopt} />
                ))}
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                {t("notSaved")}
              </p>
            </>
          )}
        </section>
      )}
    </main>
  )
}

export default IdeationView
