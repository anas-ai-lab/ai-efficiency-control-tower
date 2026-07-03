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
import StepIndicator from "@/components/step-indicator"

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
      setSharpenError(e instanceof Error ? e.message : "Schärfen fehlgeschlagen")
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
      setSolutionError(e instanceof Error ? e.message : "Lösungsvorschlag fehlgeschlagen")
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
      setComplianceError(e instanceof Error ? e.message : "Compliance-Prüfung fehlgeschlagen")
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

  const INTRO: Record<Step, { eyebrow: string; title: string; subtitle: string }> = {
    form: {
      eyebrow: "Erfassung",
      title: "Use Case einreichen",
      subtitle:
        "Strukturierte Eingabe als Grundlage der KI-gestützten Vorbewertung.",
    },
    triage: {
      eyebrow: "Vorbewertung",
      title: triageResult?.title ?? "Triage-Ergebnis",
      subtitle: "Zone, ROI und Routing auf Basis der Eingaben.",
    },
    sharpened: {
      eyebrow: "Schärfung",
      title: "Geschärfte Fallbeschreibung",
      subtitle: "Original und KI-geschärfte Fassung im Vergleich.",
    },
    solution: {
      eyebrow: "Lösung",
      title: "Lösungsvorschlag",
      subtitle: "Skizze eines tragfähigen Umsetzungswegs.",
    },
    compliance: {
      eyebrow: "Compliance",
      title: "Datenschutz- und Compliance-Hinweise",
      subtitle: "Hinweise mit belegten Quellenangaben.",
    },
    report: {
      eyebrow: "Report",
      title: "Vollständiger Report",
      subtitle: "Entscheider- und technische Sicht in einem Dokument.",
    },
  }

  const intro = INTRO[currentStep]

  return (
    <main className="mx-auto max-w-3xl px-5 py-10 sm:px-6 sm:py-12">
      <StepIndicator steps={STEPS} current={stepIndex} />

      <header className="mt-9 mb-8">
        <p className="eyebrow">{intro.eyebrow}</p>
        <h1 className="mt-2 text-pretty text-[1.65rem] font-semibold leading-tight tracking-tight text-foreground">
          {intro.title}
        </h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          {intro.subtitle}
        </p>
      </header>

      <div key={currentStep} className="animate-view-enter">
        {currentStep === "form" && (
          <IntakeForm onSuccess={handleTriageSuccess} />
        )}

        {currentStep === "triage" && (
          <div className="space-y-5">
            {sharpenError !== null && (
              <p
                role="alert"
                className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
              >
                {sharpenError}
              </p>
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
          <ReportView result={reportResult} triage={triageResult} />
        )}
      </div>
    </main>
  )
}
