"use client"

import Link from "next/link"
import { useForm, type Resolver, type Path } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTransition, useState, useEffect } from "react"
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2 } from "lucide-react"

import { submitTriage } from "@/app/actions"
import type { TriageResponse } from "@/types/api"
import { IDEATION_PREFILL_KEY } from "@/lib/ideation-prefill"
import {
  ADOPTION_TYPE_LABELS,
  ADOPTION_TYPE_OPTIONS,
  COUNTRY_LABELS,
  COUNTRY_OPTIONS,
  DATA_CLASSIFICATION_LABELS,
  DATA_CLASSIFICATION_OPTIONS,
  EMPLOYEE_CATEGORY_LABELS,
  EMPLOYEE_CATEGORY_OPTIONS,
  EVIDENCE_LEVEL_LABELS,
  EVIDENCE_LEVEL_OPTIONS,
  IMPLEMENTATION_APPROACH_LABELS,
  IMPLEMENTATION_APPROACH_OPTIONS,
} from "@/lib/labels"
import { StepIndicator } from "@/components/step-indicator"
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { formatEUR } from "@/lib/formatters"

// Werte exakt aus src/types/api.ts gespiegelt -- nicht aus dem Gedaechtnis.
const formSchema = z.object({
  title: z.string().min(5).max(200),
  submitter: z.string().min(1).max(100),
  department: z.string().min(1).max(100),
  country: z.enum([
    "de", "at", "ch", "no", "gb", "es", "it", "tr", "ro", "pl", "eg", "in",
  ]),
  current_state: z.string().min(30).max(2000),
  desired_state: z.string().min(30).max(2000),
  example_process: z.string().min(20).max(2000),
  desired_example_process: z.string().max(2000).optional(),
  time_per_case_hours_current: z.coerce.number().positive().max(8),
  time_per_case_hours_with_ai: z.coerce.number().min(0).max(8),
  occurrences_per_employee_per_year: z.coerce.number().int().positive().max(1000000),
  affected_employees_count: z.coerce.number().int().positive().max(50000),
  employee_category: z.enum([
    "junior", "professional", "consultant", "senior", "management",
  ]),
  evidence_level: z.enum(
    ["pure_estimate", "similar_project", "tested_piloted"],
    { error: "Bitte das Evidenzlevel auswählen." },
  ),
  adoption_type: z.enum(
    ["voluntary", "recommended_standard", "fixed_process_step"],
    { error: "Bitte die Verbindlichkeit der Nutzung auswählen." },
  ),
  // Optional (V4.1, ADR-0050): ohne Ansatz landet der Case im Zustand
  // "Bewertung ausstehend"; ein Admin ergänzt ihn später.
  implementation_approach: z
    .enum([
      "simple_integration",
      "development_on_existing",
      "api_integration",
      "custom_development",
      "new_tool",
    ])
    .optional(),
  estimated_license_cost_eur: z.coerce.number().min(0).max(10000000),
  implementation_cost_eur: z.coerce.number().min(0).max(10000000),
  contains_pii: z.boolean(),
  data_classification: z.enum(
    ["no_personal_data", "pseudonymous", "personal", "sensitive_personal"],
    { error: "Bitte die Datenschutzklasse auswählen." },
  ),
  regulatory_pressure: z.boolean(),
  competitive_pressure: z.boolean(),
  strategic_priority: z.boolean(),
  notes: z.string().max(2000).optional(),
})

type FormValues = z.infer<typeof formSchema>

// Feste Erklaersaetze fuer die Auswahl-Enums (kein LLM). Reihenfolge egal --
// per Key nachgeschlagen.
const APPROACH_HELP: Record<string, string> = {
  simple_integration:
    "Anbindung in eine bestehende Umgebung, minimaler Entwicklungsaufwand.",
  development_on_existing:
    "Entwicklung/Erweiterung auf einer bereits vorhandenen Plattform.",
  api_integration:
    "Externe Dienste über deren Schnittstelle (API) einbinden.",
  custom_development: "Eine neue Lösung selbst entwickeln.",
  new_tool: "Ein neues Werkzeug oder eine neue Plattform einführen (hoher Aufwand).",
}
const DATA_HELP: Record<string, string> = {
  no_personal_data: "Rein operative oder anonyme Daten.",
  pseudonymous:
    "Personenbezug nur mit Zusatzinfo herstellbar (Art. 4 Nr. 5 DSGVO) — bleibt DSGVO-relevant.",
  personal: "Direkt einer Person zuordenbar (Art. 4 Nr. 1 DSGVO).",
  sensitive_personal:
    "Gesundheit, Herkunft, Biometrie etc. — höchste Schutzstufe (Art. 9 DSGVO).",
}
const EVIDENCE_HELP: Record<string, string> = {
  pure_estimate: "Bauchgefühl ohne Datenbasis.",
  similar_project: "Eigene Erfahrung oder ein vergleichbares Projekt.",
  tested_piloted: "Mit realen Beispielen getestet oder gemessen.",
}
const ADOPTION_HELP: Record<string, string> = {
  voluntary: "Opt-in — niemand ist zur Nutzung verpflichtet.",
  recommended_standard: "Empfohlener Teamstandard.",
  fixed_process_step: "Verbindlicher Schritt im Prozess.",
}

const STEPS = [
  { key: "idee", label: "Idee" },
  { key: "menge", label: "Zeit & Häufigkeit" },
  { key: "umsetzung", label: "Umsetzung" },
  { key: "daten", label: "Daten & Verbindlichkeit" },
  { key: "pruefen", label: "Prüfen & Absenden" },
] as const

// Welche Felder jeder Schritt validiert, bevor "Weiter" freigibt.
// implementation_approach ist NICHT dabei (V4.1, ADR-0050): optional, blockiert
// den Schritt nicht.
const STEP_FIELDS: Path<FormValues>[][] = [
  ["title", "submitter", "department", "current_state", "desired_state", "example_process"],
  [
    "country",
    "employee_category",
    "time_per_case_hours_current",
    "time_per_case_hours_with_ai",
    "occurrences_per_employee_per_year",
    "affected_employees_count",
  ],
  ["implementation_cost_eur", "estimated_license_cost_eur"],
  ["data_classification", "adoption_type", "evidence_level"],
  [],
]

// P14-Prefill-Whitelist: nur qualitative Felder aus dem Ideen-Assistenten.
const PREFILL_FIELDS = [
  "title",
  "current_state",
  "desired_state",
  "example_process",
] as const

function HelpText({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs leading-relaxed text-muted-foreground">{children}</p>
  )
}

// Ein Select mit Optionsliste + optionalem Erklaersatz zur aktuellen Auswahl.
function SelectField({
  form,
  name,
  label,
  placeholder,
  options,
  help,
  note,
}: {
  form: ReturnType<typeof useForm<FormValues>>
  name: Path<FormValues>
  label: string
  placeholder: string
  options: { value: string; label: string }[]
  help?: Record<string, string>
  // Statische Zeile unter dem Label -- z. B. "Pflichtfeld" oder der
  // Optional-Hinweis beim Implementierungsansatz (V4.1, ADR-0050).
  note?: string
}) {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => {
        const selected = typeof field.value === "string" ? field.value : ""
        return (
          <FormItem>
            <FormLabel>{label}</FormLabel>
            {note && <HelpText>{note}</HelpText>}
            <Select value={selected || undefined} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={placeholder} />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {options.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {help && selected && help[selected] && (
              <HelpText>{help[selected]}</HelpText>
            )}
            <FormMessage />
          </FormItem>
        )
      }}
    />
  )
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-1 gap-0.5 py-2 sm:grid-cols-[13rem_1fr] sm:gap-4">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm whitespace-pre-wrap text-foreground/90">
        {value.length > 0 ? value : "—"}
      </dd>
    </div>
  )
}

export function IntakeWizard() {
  const [step, setStep] = useState(0)
  const [isPending, startTransition] = useTransition()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState<TriageResponse | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema) as Resolver<FormValues>,
    mode: "onBlur",
    defaultValues: {
      title: "",
      submitter: "",
      department: "",
      current_state: "",
      desired_state: "",
      example_process: "",
      desired_example_process: "",
      time_per_case_hours_current: 0,
      time_per_case_hours_with_ai: 0,
      occurrences_per_employee_per_year: 0,
      affected_employees_count: 0,
      estimated_license_cost_eur: 0,
      implementation_cost_eur: 0,
      contains_pii: false,
      regulatory_pressure: false,
      competitive_pressure: false,
      strategic_priority: false,
      notes: "",
    },
  })

  // P14-Prefill (D16/D17): einmalig beim Mount lesen, nur qualitative Felder
  // uebernehmen, Key sofort loeschen (read-once). Defensiver JSON.parse.
  useEffect(() => {
    let raw: string | null
    try {
      raw = sessionStorage.getItem(IDEATION_PREFILL_KEY)
      if (raw !== null) sessionStorage.removeItem(IDEATION_PREFILL_KEY)
    } catch {
      return
    }
    if (raw === null) return
    try {
      const parsed = JSON.parse(raw) as Record<string, unknown>
      const prefill: Partial<FormValues> = {}
      for (const key of PREFILL_FIELDS) {
        const value = parsed[key]
        if (typeof value === "string") prefill[key] = value
      }
      if (Object.keys(prefill).length > 0) {
        form.reset({ ...form.getValues(), ...prefill })
      }
    } catch {
      // kaputter/manipulierter Wert -- still ohne Prefill starten.
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function goNext() {
    const valid = await form.trigger(STEP_FIELDS[step])
    if (valid) setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  function goBack() {
    setStep((s) => Math.max(s - 1, 0))
  }

  function onSubmit(data: FormValues) {
    setSubmitError(null)
    startTransition(async () => {
      try {
        // implementation_approach ist optional (V4.1, ADR-0050): fehlt die
        // Auswahl, geht null ans Backend -> Case landet im Zustand "Bewertung
        // ausstehend".
        const result = await submitTriage({
          ...data,
          implementation_approach: data.implementation_approach ?? null,
        })
        setSubmitted(result)
      } catch (e) {
        setSubmitError(e instanceof Error ? e.message : "Unbekannter Fehler")
      }
    })
  }

  // --- Bestaetigung nach dem Absenden (kein Score/keine Zone). ---
  if (submitted !== null) {
    return (
      <div className="animate-view-enter rounded-2xl border border-border bg-card px-6 py-10 text-center sm:px-10">
        <span
          aria-hidden
          className="mx-auto flex size-12 items-center justify-center rounded-full bg-[var(--zone-win-surface)]"
        >
          <CheckCircle2 className="size-6 text-[var(--zone-win)]" />
        </span>
        <h2 className="mt-5 text-xl font-semibold tracking-tight text-foreground">
          Use Case eingereicht
        </h2>
        <p className="mx-auto mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          „{submitted.title}“ wurde erfasst und bewertet. Den vollständigen
          Bewertungsstand siehst du auf der Fall-Detailseite.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button asChild size="lg">
            <Link href={`/cases/${submitted.id}`}>Zum Fall</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/cases">Zur Ideenliste</Link>
          </Button>
        </div>
      </div>
    )
  }

  const v = form.getValues()
  const isLast = step === STEPS.length - 1

  return (
    <Form {...form}>
      <StepIndicator steps={STEPS as unknown as { key: string; label: string }[]} current={step} />

      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="mt-8"
        // Enter soll nicht vorzeitig absenden, ausser im letzten Schritt.
        onKeyDown={(e) => {
          if (e.key === "Enter" && !isLast && e.target instanceof HTMLElement && e.target.tagName !== "TEXTAREA") {
            e.preventDefault()
          }
        }}
      >
        <div key={step} className="animate-view-enter space-y-6">
          {/* --- Schritt 1: Idee --- */}
          {step === 0 && (
            <>
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Titel</FormLabel>
                    <FormControl>
                      <Input placeholder="Kurzer, prägnanter Titel des Use Cases" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="submitter"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Einreicher</FormLabel>
                      <FormControl>
                        <Input placeholder="Name der einreichenden Person" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="department"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Abteilung</FormLabel>
                      <FormControl>
                        <Input placeholder="Organisationseinheit" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <FormField
                control={form.control}
                name="current_state"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ist-Zustand</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Wie läuft der Prozess heute ab?" rows={4} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="desired_state"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Soll-Zustand</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Wie soll der Prozess zukünftig ablaufen?" rows={4} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="example_process"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Beispiel (Ist-Zustand)</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Ein konkreter, typischer Durchlauf heute" rows={3} {...field} />
                    </FormControl>
                    <HelpText>
                      Beschreibe, wie dieser Prozess oder diese Aufgabe heute
                      tatsächlich abläuft — Schritt für Schritt.
                    </HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="desired_example_process"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Beispiel (Soll-Zustand)</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Wie derselbe Vorgang nach AI-Einsatz aussehen soll"
                        rows={3}
                        {...field}
                      />
                    </FormControl>
                    <HelpText>Optional — wie der Vorgang nach AI-Einsatz aussehen soll.</HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </>
          )}

          {/* --- Schritt 2: Zeit & Häufigkeit --- */}
          {step === 1 && (
            <>
              <div className="grid gap-5 sm:grid-cols-2">
                <SelectField
                  form={form}
                  name="country"
                  label="Land"
                  placeholder="Bitte wählen"
                  options={COUNTRY_OPTIONS}
                />
                <SelectField
                  form={form}
                  name="employee_category"
                  label="Mitarbeiterlevel"
                  placeholder="Bitte wählen"
                  options={EMPLOYEE_CATEGORY_OPTIONS}
                />
              </div>
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="time_per_case_hours_current"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Zeit / Vorgang heute (Std.)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.1" placeholder="0,5" {...field} />
                      </FormControl>
                      <HelpText>
                        Wie viele Stunden dauert der Vorgang heute — einmalig, ohne
                        KI? (0,5 = 30 Minuten)
                      </HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="time_per_case_hours_with_ai"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Zeit / Vorgang mit AI (Std.)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.1" placeholder="0,1" {...field} />
                      </FormControl>
                      <HelpText>
                        Wie viele Stunden würde derselbe Vorgang mit der KI-Lösung
                        schätzungsweise dauern?
                      </HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="occurrences_per_employee_per_year"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Vorgänge / Jahr</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder="500" {...field} />
                      </FormControl>
                      <HelpText>
                        Wie oft führt EIN Mitarbeiter diesen Vorgang pro Jahr aus?
                      </HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="affected_employees_count"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Betroffene Mitarbeiter</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder="20" {...field} />
                      </FormControl>
                      <HelpText>
                        Wie viele Mitarbeiter führen diesen Vorgang regelmäßig aus?
                      </HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </>
          )}

          {/* --- Schritt 3: Umsetzung --- */}
          {step === 2 && (
            <>
              <SelectField
                form={form}
                name="implementation_approach"
                label="Implementierungsansatz"
                placeholder="Bitte wählen"
                options={IMPLEMENTATION_APPROACH_OPTIONS}
                help={APPROACH_HELP}
                note="Optional — kann später vom Admin ergänzt werden."
              />
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="implementation_cost_eur"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Implementierungskosten (einmalig, €)</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} placeholder="0" {...field} />
                      </FormControl>
                      <HelpText>Einmalige Setup-/Integrationskosten.</HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="estimated_license_cost_eur"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Lizenzkosten (wiederkehrend, € / Jahr)</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} placeholder="0" {...field} />
                      </FormControl>
                      <HelpText>0 = Open Source oder intern.</HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </>
          )}

          {/* --- Schritt 4: Daten & Verbindlichkeit --- */}
          {step === 3 && (
            <>
              <SelectField
                form={form}
                name="data_classification"
                label="Datenschutzklasse"
                placeholder="Bitte wählen"
                options={DATA_CLASSIFICATION_OPTIONS}
                help={DATA_HELP}
                note="Pflichtfeld"
              />
              <FormField
                control={form.control}
                name="contains_pii"
                render={({ field }) => (
                  <FormItem>
                    <label className="flex cursor-pointer items-center gap-2.5">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <span className="text-sm font-medium text-foreground">
                        Enthält personenbezogene Daten (PII)
                      </span>
                    </label>
                    <HelpText>
                      Löst zusammen mit regulatorischem Druck die Empfehlung zu
                      DSFA und menschlicher Prüfung aus. Die Datenschutzklasse
                      oben steuert stattdessen den Aufwands-Score.
                    </HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <SelectField
                form={form}
                name="adoption_type"
                label="Verbindlichkeit der Nutzung"
                placeholder="Bitte wählen"
                options={ADOPTION_TYPE_OPTIONS}
                help={ADOPTION_HELP}
                note="Pflichtfeld"
              />
              <SelectField
                form={form}
                name="evidence_level"
                label="Evidenzlevel"
                placeholder="Bitte wählen"
                options={EVIDENCE_LEVEL_OPTIONS}
                help={EVIDENCE_HELP}
                note="Pflichtfeld"
              />

              <fieldset className="space-y-3 border-t border-border pt-5">
                <legend className="eyebrow mb-1">Handlungsdruck (optional)</legend>
                {(
                  [
                    ["regulatory_pressure", "Regulatorischer Druck", "Gesetzliche oder aufsichtsrechtliche Anforderungen."],
                    ["competitive_pressure", "Wettbewerbsdruck", "Mitbewerber setzen vergleichbare Lösungen bereits ein."],
                    ["strategic_priority", "Strategische Priorität", "Teil der Unternehmensstrategie oder eines Vorstandsziels."],
                  ] as const
                ).map(([name, label, hint]) => (
                  <FormField
                    key={name}
                    control={form.control}
                    name={name}
                    render={({ field }) => (
                      <FormItem>
                        <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/40 has-data-[state=checked]:border-[var(--ink)]/40 has-data-[state=checked]:bg-[var(--ink-subtle)]">
                          <FormControl>
                            <Checkbox className="mt-0.5" checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <span className="grid gap-0.5">
                            <span className="text-sm font-medium text-foreground">{label}</span>
                            <span className="text-xs leading-relaxed text-muted-foreground">{hint}</span>
                          </span>
                        </label>
                      </FormItem>
                    )}
                  />
                ))}
              </fieldset>

              <FormField
                control={form.control}
                name="notes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Anmerkungen (optional)</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Zusätzliche Infos für die Bewertung" rows={3} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </>
          )}

          {/* --- Schritt 5: Pruefen & Absenden (KEINE Berechnung/Score/Zone). --- */}
          {step === 4 && (
            <div className="space-y-6">
              <p className="text-sm leading-relaxed text-muted-foreground">
                Bitte prüfe deine Eingaben. Nach dem Absenden bewertet AECT den Use
                Case; das Ergebnis siehst du auf der Fall-Detailseite.
              </p>
              <dl className="divide-y divide-border rounded-xl border border-border bg-card px-5 py-1">
                <ReviewRow label="Titel" value={v.title} />
                <ReviewRow label="Einreicher" value={v.submitter} />
                <ReviewRow label="Abteilung" value={v.department} />
                <ReviewRow label="Ist-Zustand" value={v.current_state} />
                <ReviewRow label="Soll-Zustand" value={v.desired_state} />
                <ReviewRow label="Beispiel (Ist)" value={v.example_process} />
                <ReviewRow label="Beispiel (Soll)" value={v.desired_example_process ?? ""} />
                <ReviewRow label="Land" value={v.country ? COUNTRY_LABELS[v.country] : ""} />
                <ReviewRow
                  label="Mitarbeiterlevel"
                  value={v.employee_category ? EMPLOYEE_CATEGORY_LABELS[v.employee_category] : ""}
                />
                <ReviewRow label="Zeit / Vorgang heute" value={`${v.time_per_case_hours_current} Std.`} />
                <ReviewRow label="Zeit / Vorgang mit AI" value={`${v.time_per_case_hours_with_ai} Std.`} />
                <ReviewRow label="Vorgänge / Jahr" value={String(v.occurrences_per_employee_per_year)} />
                <ReviewRow label="Betroffene Mitarbeiter" value={String(v.affected_employees_count)} />
                <ReviewRow
                  label="Implementierungsansatz"
                  value={v.implementation_approach ? IMPLEMENTATION_APPROACH_LABELS[v.implementation_approach] : ""}
                />
                <ReviewRow label="Implementierungskosten" value={formatEUR(v.implementation_cost_eur || 0)} />
                <ReviewRow label="Lizenzkosten / Jahr" value={formatEUR(v.estimated_license_cost_eur || 0)} />
                <ReviewRow
                  label="Datenschutzklasse"
                  value={v.data_classification ? DATA_CLASSIFICATION_LABELS[v.data_classification] : ""}
                />
                <ReviewRow label="Personenbezogene Daten" value={v.contains_pii ? "Ja" : "Nein"} />
                <ReviewRow
                  label="Verbindlichkeit"
                  value={v.adoption_type ? ADOPTION_TYPE_LABELS[v.adoption_type] : ""}
                />
                <ReviewRow
                  label="Evidenzlevel"
                  value={v.evidence_level ? EVIDENCE_LEVEL_LABELS[v.evidence_level] : ""}
                />
                <ReviewRow
                  label="Handlungsdruck"
                  value={
                    [
                      v.regulatory_pressure && "Regulatorisch",
                      v.competitive_pressure && "Wettbewerb",
                      v.strategic_priority && "Strategisch",
                    ]
                      .filter(Boolean)
                      .join(", ") || "keiner"
                  }
                />
                {v.notes && v.notes.length > 0 && (
                  <ReviewRow label="Anmerkungen" value={v.notes} />
                )}
              </dl>

              {submitError && (
                <p
                  role="alert"
                  className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
                >
                  {submitError}
                </p>
              )}
            </div>
          )}
        </div>

        {/* --- Navigation --- */}
        <div className="mt-9 flex items-center justify-between gap-3 border-t border-border pt-6">
          <Button
            type="button"
            variant="ghost"
            onClick={goBack}
            disabled={step === 0 || isPending}
            className={step === 0 ? "invisible" : ""}
          >
            <ArrowLeft className="size-4" />
            Zurück
          </Button>

          {isLast ? (
            <Button type="submit" size="lg" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isPending ? "Wird eingereicht …" : "Use Case einreichen"}
            </Button>
          ) : (
            <Button type="button" size="lg" onClick={goNext}>
              Weiter
              <ArrowRight className="size-4" />
            </Button>
          )}
        </div>
      </form>
    </Form>
  )
}

export default IntakeWizard
