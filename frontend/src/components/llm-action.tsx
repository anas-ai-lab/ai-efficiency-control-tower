"use client"

import { Loader2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

interface LlmActionProps {
  onAction: () => void
  isLoading: boolean
  idleLabel: string
  loadingLabel: string
  hint: string
  error?: string | null
}

// Gemeinsame CTA fuer alle LLM-Schritte. Im Leerlauf: Primaerbutton mit Hinweis.
// Waehrend des Calls wird der Button durch ein Arbeits-Panel ersetzt --
// indeterminierte Fortschrittsleiste plus Skelett-Zeilen -- damit die
// Sekunden Wartezeit wie ein Prozess wirken, nicht wie ein Haenger.
export function LlmAction({
  onAction,
  isLoading,
  idleLabel,
  loadingLabel,
  hint,
  error,
}: LlmActionProps) {
  const t = useTranslations("llmAction")
  return (
    <div className="space-y-3">
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
            {loadingLabel}
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
            {t("durationHint")}
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          <Button
            type="button"
            size="xl"
            onClick={onAction}
            className="w-full"
          >
            {idleLabel}
          </Button>
          <p className="text-center text-xs text-muted-foreground">{hint}</p>
        </div>
      )}
    </div>
  )
}

export default LlmAction
