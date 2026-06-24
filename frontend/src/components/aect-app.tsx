"use client"

import { useState } from "react"
import { TriageResponse, SharpenedCaseResponse, SolutionProposalResponse } from "@/types/api"
import { sharpenCase, proposeSolution } from "@/app/actions"
import IntakeForm from "@/components/intake-form"
import TriageResult from "@/components/triage-result"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

type Step = "form" | "triage" | "sharpened" | "solution" | "compliance" | "report"

const STEPS: { key: Step; label: string }[] = [
  { key: "form", label: "Einreichung" },
  { key: "triage", label: "Bewertung" },
  { key: "sharpened", label: "Schaerfen" },
  { key: "solution", label: "Loesung" },
  { key: "compliance", label: "Compliance" },
  { key: "report", label: "Report" },
]

export default function AectApp() {
  const [currentStep, setCurrentStep] = useState<Step>("form")
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null)
  const [sharpenedResult, setSharpenedResult] = useState<SharpenedCaseResponse | null>(null)
  const [solutionResult, setSolutionResult] = useState<SolutionProposalResponse | null>(null)

  const [isSharpenLoading, setIsSharpenLoading] = useState(false)
  const [isSolutionLoading, setIsSolutionLoading] = useState(false)

  const [sharpenError, setSharpenError] = useState<string | null>(null)
  const [solutionError, setSolutionError] = useState<string | null>(null)

  function handleTriageSuccess(result: TriageResponse) {
    setTriageResult(result)
    setCurrentStep("triage")
  }

  async function handleSharpen() {
    if (!triageResult) return
    setSharpenError(null)
    setIsSharpenLoading(true)
    try {
      const result = await sharpenCase(triageResult.id)
      setSharpenedResult(result)
      setCurrentStep("sharpened")
    } catch (e) {
      setSharpenError(e instanceof Error ? e.message : "Schaerfen fehlgeschlagen")
    } finally {
      setIsSharpenLoading(false)
    }
  }

  async function handlePropose() {
    if (!triageResult) return
    setSolutionError(null)
    setIsSolutionLoading(true)
    try {
      const result = await proposeSolution(triageResult.id)
      setSolutionResult(result)
    } catch (e) {
      setSolutionError(e instanceof Error ? e.message : "Loesungsvorschlag fehlgeschlagen")
    } finally {
      setIsSolutionLoading(false)
    }
  }

  const stepIndex = STEPS.findIndex((s) => s.key === currentStep)

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <header>
        <h1 className="text-xl font-bold tracking-tight">
          AECT | AI Efficiency Control Tower
        </h1>
        <nav className="mt-2 flex items-center text-sm">
          {STEPS.map((step, i) => (
            <span key={step.key} className="flex items-center">
              {i > 0 && (
                <span className="mx-1 text-muted-foreground">›</span>
              )}
              <span
                className={
                  i === stepIndex
                    ? "font-semibold text-primary"
                    : i < stepIndex
                      ? "text-muted-foreground"
                      : "text-muted-foreground opacity-50"
                }
              >
                {step.label}
              </span>
            </span>
          ))}
        </nav>
      </header>

      {currentStep === "form" && (
        <IntakeForm onSuccess={handleTriageSuccess} />
      )}

      {currentStep === "triage" && (
        <div className="space-y-4">
          {sharpenError !== null && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              {sharpenError}
            </div>
          )}
          <TriageResult
            result={triageResult!}
            onSharpen={handleSharpen}
            isSharpenLoading={isSharpenLoading}
          />
        </div>
      )}

      {currentStep === "sharpened" && sharpenedResult !== null && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Geschaerfte Beschreibung</CardTitle>
            </CardHeader>
            <CardContent>
              {sharpenedResult.sharpened_title !== null ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Original
                      </p>
                      <div className="space-y-3">
                        <div>
                          <p className="text-xs text-muted-foreground">Titel</p>
                          <p className="text-sm">{sharpenedResult.original_title}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Ist-Zustand</p>
                          <p className="text-sm">{sharpenedResult.original_current_state}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Soll-Zustand</p>
                          <p className="text-sm">{sharpenedResult.original_desired_state}</p>
                        </div>
                      </div>
                    </div>
                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Geschaerft
                      </p>
                      <div className="space-y-3">
                        <div>
                          <p className="text-xs text-muted-foreground">Titel</p>
                          <p className="text-sm font-medium">
                            {sharpenedResult.sharpened_title}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Ist-Zustand</p>
                          <p className="text-sm">
                            {sharpenedResult.sharpened_current_state ?? ""}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Soll-Zustand</p>
                          <p className="text-sm">
                            {sharpenedResult.sharpened_desired_state ?? ""}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  {sharpenedResult.improvement_suggestions.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Verbesserungsvorschlaege
                      </p>
                      <ol className="list-decimal space-y-1 pl-5">
                        {sharpenedResult.improvement_suggestions.map((s, i) => (
                          <li key={i} className="text-sm">
                            {s}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm font-medium text-yellow-900">
                    Strukturierte Schaerfen nicht verfuegbar
                  </div>
                  {sharpenedResult.raw_text !== null && (
                    <pre className="rounded-md bg-muted p-3 text-sm whitespace-pre-wrap">
                      {sharpenedResult.raw_text}
                    </pre>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {solutionResult !== null ? (
            <Card>
              <CardHeader>
                <CardTitle>Loesungsvorschlag</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{solutionResult.proposal_text}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {solutionError !== null && (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                  {solutionError}
                </div>
              )}
              <Button
                onClick={handlePropose}
                disabled={isSolutionLoading}
                className="w-full"
              >
                {isSolutionLoading && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {isSolutionLoading
                  ? "Wird generiert..."
                  : "Loesungsvorschlag generieren (KI)"}
              </Button>
            </div>
          )}
        </div>
      )}

      {currentStep === "solution" && (
        <div>Naechster Schritt: solution wird in Tag 74 implementiert.</div>
      )}

      {currentStep === "compliance" && (
        <div>Naechster Schritt: compliance wird in Tag 74 implementiert.</div>
      )}

      {currentStep === "report" && (
        <div>Naechster Schritt: report wird in Tag 74 implementiert.</div>
      )}
    </main>
  )
}
