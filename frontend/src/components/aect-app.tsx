"use client"

import { useState } from "react"
import type {
  TriageResponse,
  SharpenedCaseResponse,
  SolutionProposalResponse,
  ComplianceHintsResponse,
  ReportResponse,
} from "@/types/api"
import {
  sharpenCase,
  proposeSolution,
  generateComplianceHints,
  generateReport,
} from "@/app/actions"
import IntakeForm from "@/components/intake-form"
import TriageResult from "@/components/triage-result"
import SharpenedView from "@/components/sharpened-view"
import SolutionView from "@/components/solution-view"
import ComplianceView from "@/components/compliance-view"
import ReportView from "@/components/report-view"

type Step = "form" | "triage" | "sharpened" | "solution" | "compliance" | "report"

const STEPS: { key: Step; label: string }[] = [
  { key: "form", label: "Einreichung" },
  { key: "triage", label: "Bewertung" },
  { key: "sharpened", label: "Schärfen" },
  { key: "solution", label: "Lösung" },
  { key: "compliance", label: "Compliance" },
  { key: "report", label: "Report" },
]

export default function AectApp() {
  const [currentStep, setCurrentStep] = useState<Step>("form")
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null)
  const [sharpenedResult, setSharpenedResult] = useState<SharpenedCaseResponse | null>(null)
  const [solutionResult, setSolutionResult] = useState<SolutionProposalResponse | null>(null)
  const [complianceResult, setComplianceResult] = useState<ComplianceHintsResponse | null>(null)
  const [reportResult, setReportResult] = useState<ReportResponse | null>(null)

  const [isSharpenLoading, setIsSharpenLoading] = useState(false)
  const [isProposeLoading, setIsProposeLoading] = useState(false)
  const [isComplianceLoading, setIsComplianceLoading] = useState(false)
  const [isReportLoading, setIsReportLoading] = useState(false)

  const [sharpenError, setSharpenError] = useState<string | null>(null)
  const [solutionError, setSolutionError] = useState<string | null>(null)
  const [complianceError, setComplianceError] = useState<string | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)

  function handleTriageSuccess(result: TriageResponse): void {
    setTriageResult(result)
    setCurrentStep("triage")
  }

  async function handleSharpen(): Promise<void> {
    setSharpenError(null)
    setIsSharpenLoading(true)
    try {
      const result = await sharpenCase(triageResult!.id)
      setSharpenedResult(result)
      setCurrentStep("sharpened")
    } catch (e) {
      setSharpenError(e instanceof Error ? e.message : "Schaerfen fehlgeschlagen")
    } finally {
      setIsSharpenLoading(false)
    }
  }

  async function handlePropose(): Promise<void> {
    setSolutionError(null)
    setIsProposeLoading(true)
    try {
      const result = await proposeSolution(triageResult!.id)
      setSolutionResult(result)
      setCurrentStep("solution")
    } catch (e) {
      setSolutionError(e instanceof Error ? e.message : "Loesungsvorschlag fehlgeschlagen")
    } finally {
      setIsProposeLoading(false)
    }
  }

  async function handleCompliance(): Promise<void> {
    setComplianceError(null)
    setIsComplianceLoading(true)
    try {
      const result = await generateComplianceHints(triageResult!.id)
      setComplianceResult(result)
      setCurrentStep("compliance")
    } catch (e) {
      setComplianceError(e instanceof Error ? e.message : "Compliance-Pruefung fehlgeschlagen")
    } finally {
      setIsComplianceLoading(false)
    }
  }

  async function handleReport(): Promise<void> {
    setReportError(null)
    setIsReportLoading(true)
    try {
      const result = await generateReport(triageResult!.id)
      setReportResult(result)
      setCurrentStep("report")
    } catch (e) {
      setReportError(e instanceof Error ? e.message : "Report-Generierung fehlgeschlagen")
    } finally {
      setIsReportLoading(false)
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
            <div className="rounded-md border border-red-200 bg-red-50
                            p-3 text-sm text-red-800">
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
        <SharpenedView
          result={sharpenedResult}
          onPropose={handlePropose}
          isProposeLoading={isProposeLoading}
          proposeError={solutionError}
        />
      )}

      {currentStep === "solution" && solutionResult !== null && (
        <SolutionView
          result={solutionResult}
          onCompliance={handleCompliance}
          isComplianceLoading={isComplianceLoading}
          complianceError={complianceError}
        />
      )}

      {currentStep === "compliance" && complianceResult !== null && (
        <ComplianceView
          result={complianceResult}
          onReport={handleReport}
          isReportLoading={isReportLoading}
          reportError={reportError}
        />
      )}

      {currentStep === "report" && reportResult !== null && (
        <ReportView result={reportResult} />
      )}
    </main>
  )
}
