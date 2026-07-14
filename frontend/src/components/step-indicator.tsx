"use client"

import { Check } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

export interface StepIndicatorProps {
  steps: { key: string; label: string }[]
  current: number
}

// Echtes Fortschritts-System: nummerierte Knoten auf einer Schiene, deren
// Verbindungslinien sich bei abgeschlossenen Schritten fuellen. Abgeschlossen
// (Haken, Tinte gefuellt), aktiv (Tinten-Rand) und ausstehend (gedaempft) sind
// visuell klar getrennt -- nicht nur eingefaerbter Text.
export function StepIndicator({ steps, current }: StepIndicatorProps) {
  const total = steps.length
  const t = useTranslations("intake")

  return (
    <nav aria-label={t("progressAria")} className="w-full">
      {/* Mobile: kompakte Zeile statt gedraengter Knotenkette. */}
      <div className="flex items-baseline justify-between sm:hidden">
        <p className="text-sm font-medium text-foreground">
          {steps[current]?.label}
        </p>
        <p className="text-xs text-muted-foreground tnum">
          {t("progressStep", { current: current + 1, total })}
        </p>
      </div>
      <div
        className="mt-2 h-1 w-full overflow-hidden rounded-full bg-border sm:hidden"
        role="presentation"
      >
        <div
          className="h-full rounded-full bg-[var(--ink)] transition-[width] duration-300 ease-out"
          style={{ width: `${((current + 1) / total) * 100}%` }}
        />
      </div>

      {/* Desktop: vollstaendige Schiene mit Knoten und Labels. */}
      <ol className="relative hidden items-center pb-7 sm:flex">
        {steps.map((step, i) => {
          const state =
            i < current ? "done" : i === current ? "active" : "todo"
          const isLast = i === total - 1
          return (
            <li
              key={step.key}
              className={cn("flex items-center", !isLast && "flex-1")}
              aria-current={state === "active" ? "step" : undefined}
            >
              <div className="relative flex flex-col items-center">
                <span
                  className={cn(
                    "flex size-7 items-center justify-center rounded-full border text-xs font-semibold tnum transition-colors duration-200 ease-out",
                    state === "done" &&
                      "border-transparent bg-[var(--ink)] text-[var(--ink-foreground)]",
                    state === "active" &&
                      "border-[var(--ink)] bg-background text-[var(--ink)] shadow-[0_0_0_3px_var(--ink-subtle)]",
                    state === "todo" &&
                      "border-border bg-background text-muted-foreground"
                  )}
                >
                  {state === "done" ? (
                    <Check className="size-3.5" strokeWidth={2.75} />
                  ) : (
                    i + 1
                  )}
                </span>
                <span
                  className={cn(
                    "absolute top-full left-1/2 mt-2 -translate-x-1/2 text-xs whitespace-nowrap transition-colors duration-200",
                    state === "active" && "font-medium text-foreground",
                    state === "done" && "text-muted-foreground",
                    state === "todo" && "text-muted-foreground/55"
                  )}
                >
                  {step.label}
                </span>
              </div>
              {!isLast && (
                <span className="mx-2 h-px flex-1 overflow-hidden rounded-full bg-border">
                  <span
                    className={cn(
                      "block h-full origin-left bg-[var(--ink)] transition-transform duration-300 ease-out",
                      i < current ? "scale-x-100" : "scale-x-0"
                    )}
                  />
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export default StepIndicator
