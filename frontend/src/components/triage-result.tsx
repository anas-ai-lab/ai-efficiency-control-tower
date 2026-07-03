"use client"

import type { TriageResponse } from "@/types/api"
import {
  formatEUR,
  formatNumber,
  ZONE_CONFIG,
  ZoneKey,
} from "@/lib/formatters"
import { LlmAction } from "@/components/llm-action"
import {
  NetBenefitRationale,
  CompositeBreakdown,
  RoutingRationale,
  CONFIDENCE_INTERPRETATION,
} from "@/components/decision-rationale"
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
} from "lucide-react"

// Routing-Empfehlung als deutsche Bezeichnung plus dezenter Statuspunkt.
const ROUTING: Record<string, { labelDE: string; dot: string }> = {
  AI_RECOMMENDED: { labelDE: "KI empfohlen", dot: "bg-[var(--ink)]" },
  AUTOMATION_RECOMMENDED: {
    labelDE: "Automatisierung empfohlen",
    dot: "bg-[var(--zone-win)]",
  },
  HUMAN_REVIEW_REQUIRED: {
    labelDE: "Menschliche Prüfung",
    dot: "bg-[var(--zone-risk)]",
  },
  BORDERLINE: { labelDE: "Grenzfall", dot: "bg-[var(--zone-risk)]" },
}

const CONFIDENCE_DE: Record<string, string> = {
  high: "Hoch",
  medium: "Mittel",
  low: "Niedrig",
}

// Zonen-Konfidenz (ADR-0036): entsaettigte Semantik-Tokens, keine Alarmfarben.
// hoch = ruhiges Gruen, mittel = Bernstein, niedrig = gedaempftes Rot.
const ZONE_CONFIDENCE: Record<string, string> = {
  hoch: "text-[var(--zone-win-fg)]",
  mittel: "text-[var(--zone-risk-fg)]",
  niedrig: "text-[var(--zone-gain-fg)]",
}

interface TriageResultProps {
  result: TriageResponse
  onSharpen: () => void
  isSharpenLoading: boolean
}

export function TriageResult({
  result,
  onSharpen,
  isSharpenLoading,
}: TriageResultProps) {
  const zone = result.zone
  const zoneConfig = zone ? ZONE_CONFIG[zone.final_zone as ZoneKey] : null
  const warning = result.similarity_warning
  const routing =
    ROUTING[result.routing.recommendation] ?? {
      labelDE: result.routing.recommendation,
      dot: "bg-muted-foreground",
    }
  const confidence =
    CONFIDENCE_DE[result.routing.confidence.toLowerCase()] ??
    result.routing.confidence

  return (
    <div className="stagger space-y-5">
      {/* Dedup-Hinweis (L-3, ADR-0039) -- nur bei aehnlichem Bestandsfall. */}
      {warning !== null && (
        <div className="flex items-start gap-3 rounded-xl border border-[var(--zone-risk-border)] bg-[var(--zone-risk-surface)] px-4 py-3.5">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-[var(--zone-risk-fg)]" />
          <div className="space-y-1 text-sm">
            <p className="font-medium text-[var(--zone-risk-fg)]">
              {warning.suggest_combine
                ? "Möglicher Doppel-Eintrag"
                : "Ähnlicher Use Case gefunden"}
            </p>
            <p className="leading-relaxed text-foreground/80">
              Ähnelt dem bereits erfassten Fall „{warning.similar_case_title}“
              {" "}({Math.round(warning.similarity_score * 100)} %
              Übereinstimmung).
              {warning.suggest_combine
                ? " Bitte prüfen, ob die Fälle zusammengelegt werden sollten."
                : " Bitte prüfen, ob es sich um denselben Vorgang handelt."}
            </p>
          </div>
        </div>
      )}

      {/* Verdikt: die Bewertungszone als Headline, Begruendung prominent darunter. */}
      {zone !== null && zoneConfig !== null && (
        <section
          className={`rounded-2xl border px-6 py-6 sm:px-7 ${zoneConfig.surface}`}
        >
          <div className="flex items-start gap-4">
            <span
              className={`mt-2.5 size-2.5 shrink-0 rounded-full ${zoneConfig.dot}`}
              aria-hidden
            />
            <div className="min-w-0">
              <p className="eyebrow">Bewertungszone</p>
              <h2
                className={`mt-1.5 text-2xl font-bold tracking-tight ${zoneConfig.text}`}
              >
                {zoneConfig.labelDE}
              </h2>
              {/* Begruendung PROMINENT direkt unter dem Verdikt, keine Fussnote. */}
              <p className="mt-2 max-w-prose text-[0.9375rem] leading-relaxed text-foreground/90">
                {zone.reason}
              </p>
              {/* Konfidenz-Score (ADR-0036) mit Klartext-Interpretation. */}
              <div className="mt-3 border-t border-current/10 pt-3">
                <p className="text-xs text-muted-foreground">
                  Konfidenz:{" "}
                  <span
                    className={`font-medium ${
                      ZONE_CONFIDENCE[zone.confidence_label] ??
                      "text-foreground"
                    }`}
                  >
                    {Math.round(zone.confidence_score * 100)} % (
                    {zone.confidence_label})
                  </span>
                </p>
                {CONFIDENCE_INTERPRETATION[zone.confidence_label] && (
                  <p className="mt-1 text-[0.8125rem] leading-relaxed text-muted-foreground">
                    {CONFIDENCE_INTERPRETATION[zone.confidence_label]}
                  </p>
                )}
              </div>
              {zone.handlungsdruck_elevated && (
                <span
                  className={`mt-3 inline-flex items-center gap-1.5 rounded-full border border-current/25 px-2.5 py-1 text-[0.7rem] font-medium tracking-wide ${zoneConfig.text}`}
                >
                  <ArrowRight className="size-3" />
                  Hochgestuft wegen Handlungsdruck
                </span>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ROI: Kennzahlen im Dashboard-Stil plus getemplatete Nutzen-Erklaerung. */}
      {result.roi !== null && (
        <section className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-[1.4fr_1fr_1fr] sm:divide-x sm:divide-y-0">
            <div className="px-6 py-5">
              <p className="eyebrow">Erwarteter Nettonutzen</p>
              <p className="stat-value mt-2.5 text-[2rem] text-foreground">
                {formatEUR(result.roi.net_expected_benefit_eur)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">pro Jahr</p>
            </div>
            <div className="px-6 py-5">
              <p className="eyebrow">Theoret. Potenzial</p>
              <p className="stat-value mt-2.5 text-2xl text-foreground/80">
                {formatEUR(result.roi.theoretical_potential_eur)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">Obergrenze</p>
            </div>
            <div className="px-6 py-5">
              <p className="eyebrow">Stunden / Jahr</p>
              <p className="stat-value mt-2.5 text-2xl text-foreground/80">
                {formatNumber(result.roi.hours_per_year)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">
                eingespart
              </p>
            </div>
          </div>
          {/* 1a: warum net < theoretisch, plus aufklappbarer Rechenweg. */}
          <div className="border-t border-border px-6 py-4">
            <NetBenefitRationale roi={result.roi} />
          </div>
        </section>
      )}

      {/* 1b: Aufwand-Score nie nackt -- immer die drei gelabelten Subscores. */}
      {result.composite !== null && (
        <section className="rounded-2xl border border-border bg-card px-6 py-5">
          <p className="eyebrow mb-3">Aufwand-Score</p>
          <CompositeBreakdown composite={result.composite} />
        </section>
      )}

      {/* 1e: Vorfilter mit Begruendung statt nacktem bestanden/nicht bestanden. */}
      {result.passed_vorfilter === true ? (
        <div className="rounded-xl border border-border bg-card px-4 py-3.5 text-sm">
          <div className="flex items-center gap-2.5 font-medium text-foreground">
            <CheckCircle2 className="size-4 shrink-0 text-[var(--zone-win)]" />
            <span>Alle Vorfilter-Kriterien erfüllt</span>
          </div>
          {result.roi !== null && (
            <dl className="mt-3 grid grid-cols-1 gap-2 border-t border-border pt-3 text-xs sm:grid-cols-3">
              <div className="flex items-baseline justify-between gap-3 sm:flex-col sm:justify-start sm:gap-1">
                <dt className="text-muted-foreground">Theoret. Potenzial</dt>
                <dd className="font-mono tnum text-foreground/85">
                  {formatEUR(result.roi.theoretical_potential_eur)}
                </dd>
              </div>
              <div className="flex items-baseline justify-between gap-3 sm:flex-col sm:justify-start sm:gap-1">
                <dt className="text-muted-foreground">Stunden / Jahr</dt>
                <dd className="font-mono tnum text-foreground/85">
                  {formatNumber(result.roi.hours_per_year)}
                </dd>
              </div>
              <div className="flex items-baseline justify-between gap-3 sm:flex-col sm:justify-start sm:gap-1">
                <dt className="text-muted-foreground">Netto-Nutzen</dt>
                <dd className="font-mono tnum text-foreground/85">
                  {formatEUR(result.roi.net_expected_benefit_eur)}
                </dd>
              </div>
            </dl>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3.5 text-sm">
          <div className="flex items-center gap-2.5 font-medium text-destructive">
            <XCircle className="size-4 shrink-0" />
            <span>Vorfilter nicht bestanden</span>
          </div>
          {result.vorfilter.failed_criteria.length > 0 && (
            <ul className="mt-2.5 space-y-1 pl-6 text-foreground/80">
              {result.vorfilter.failed_criteria.map((criterion, i) => (
                <li key={i} className="list-disc">
                  {criterion}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* 1f: Routing mit sichtbarer Begruendung -- die Signale tragen die Empfehlung. */}
      <section className="rounded-xl border border-border bg-card p-5">
        <p className="eyebrow">Routing-Empfehlung</p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground">
            <span className={`size-2 rounded-full ${routing.dot}`} aria-hidden />
            {routing.labelDE}
          </span>
          <span className="text-xs text-muted-foreground">
            Konfidenz:{" "}
            <span className="font-medium text-foreground">{confidence}</span>
          </span>
        </div>

        <div className="mt-4">
          <RoutingRationale
            recommendation={result.routing.recommendation}
            automationSignals={result.routing.automation_signals}
            aiSignals={result.routing.ai_signals}
          />
        </div>

        {result.routing.risk_flags.length > 0 && (
          <div className="mt-4 border-t border-border pt-4">
            <p className="text-xs text-muted-foreground">Risiko-Signale</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {result.routing.risk_flags.map((flag, i) => (
                <span
                  key={i}
                  className="rounded-md border border-[var(--zone-gain-border)] bg-[var(--zone-gain-surface)] px-2 py-0.5 text-xs font-medium text-[var(--zone-gain-fg)]"
                >
                  {flag}
                </span>
              ))}
            </div>
          </div>
        )}
        {result.routing.requires_human_review === true && (
          <p className="mt-4 flex items-center gap-2 text-sm font-medium text-[var(--zone-risk-fg)]">
            <AlertTriangle className="size-3.5" />
            Menschliche Prüfung empfohlen
          </p>
        )}
      </section>

      {/* 1g: Machbarkeit -- Empfehlung als Satz prominent, Flags sekundaer. */}
      <section className="rounded-xl border border-border bg-card p-5">
        <p className="eyebrow">Machbarkeit</p>
        <div className="mt-3 flex items-center gap-2 text-sm">
          {result.feasibility.is_feasible ? (
            <>
              <CheckCircle2 className="size-4 text-[var(--zone-win)]" />
              <span className="font-medium text-foreground">Machbar</span>
            </>
          ) : (
            <>
              <XCircle className="size-4 text-destructive" />
              <span className="font-medium text-foreground">
                Nicht machbar
              </span>
            </>
          )}
        </div>
        {result.feasibility.recommendation !== null && (
          <p className="mt-3 text-[0.9375rem] leading-relaxed text-foreground/90">
            {result.feasibility.recommendation}
          </p>
        )}
        {result.feasibility.flags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {result.feasibility.flags.map((flag, i) => (
              <span
                key={i}
                className="rounded-md border border-border bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground"
              >
                {flag}
              </span>
            ))}
          </div>
        )}
      </section>

      {/* Naechster Schritt: KI-Schaerfung. */}
      <div className="pt-1">
        <LlmAction
          onAction={onSharpen}
          isLoading={isSharpenLoading}
          idleLabel="Use Case schärfen"
          loadingLabel="Use Case wird geschärft …"
          hint="KI-gestützte Schärfung der Beschreibung · 5–30 Sekunden"
        />
      </div>
    </div>
  )
}

export default TriageResult
