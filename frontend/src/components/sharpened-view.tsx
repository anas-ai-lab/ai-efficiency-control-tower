"use client"

import { SharpenedCaseResponse } from "@/types/api"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Loader2 } from "lucide-react"

interface SharpenedViewProps {
  result: SharpenedCaseResponse
  onPropose: () => void
  isProposeLoading: boolean
  proposeError: string | null
}

export function SharpenedView({
  result,
  onPropose,
  isProposeLoading,
  proposeError,
}: SharpenedViewProps) {
  return (
    <div className="space-y-4">
      {result.sharpened_title !== null ? (
        <>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="mb-3 text-xs uppercase tracking-widest text-muted-foreground">
                ORIGINAL
              </p>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Titel</p>
                  <p className="text-sm font-medium text-muted-foreground">
                    {result.original_title}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Ist-Zustand</p>
                  <p className="text-sm text-muted-foreground">
                    {result.original_current_state}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Soll-Zustand</p>
                  <p className="text-sm text-muted-foreground">
                    {result.original_desired_state}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <p className="mb-3 border-l-2 border-primary pl-2 text-xs uppercase tracking-widest text-muted-foreground">
                GESCHAERFT
              </p>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Titel</p>
                  <p className="text-sm font-medium text-foreground">
                    {result.sharpened_title}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Ist-Zustand</p>
                  <p className="text-sm font-medium text-foreground">
                    {result.sharpened_current_state ?? ""}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Soll-Zustand</p>
                  <p className="text-sm font-medium text-foreground">
                    {result.sharpened_desired_state ?? ""}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {result.improvement_suggestions.length > 0 && (
            <>
              <Separator />
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                VERBESSERUNGSVORSCHLAEGE
              </p>
              <div className="space-y-2">
                {result.improvement_suggestions.map((suggestion, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {index + 1}
                    </span>
                    <p className="text-sm">{suggestion}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      ) : (
        <>
          <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm font-medium text-yellow-900">
            Strukturierte Schaerfen nicht verfuegbar
          </div>
          {result.raw_text !== null && (
            <pre className="mt-2 whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">
              {result.raw_text}
            </pre>
          )}
        </>
      )}

      <Separator />

      {proposeError !== null && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {proposeError}
        </div>
      )}

      <Button onClick={onPropose} disabled={isProposeLoading} className="w-full">
        {isProposeLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isProposeLoading ? "Wird generiert..." : "Loesungsvorschlag generieren (KI)"}
      </Button>

      <p className="mt-2 text-center text-xs text-muted-foreground">
        Dauert 5-30 Sekunden, LLM-Call
      </p>
    </div>
  )
}
export default SharpenedView
