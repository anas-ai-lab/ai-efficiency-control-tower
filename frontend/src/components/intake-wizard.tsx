"use client"

import Link from "next/link"
import { useForm, type Resolver, type Path } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTranslations } from "next-intl"
import { useTransition, useState, useEffect, useMemo } from "react"
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2 } from "lucide-react"

import { submitTriage } from "@/app/actions"
import type { TriageResponse } from "@/types/api"
import { IDEATION_PREFILL_KEY } from "@/lib/ideation-prefill"
import {
  ADOPTION_TYPE_OPTIONS,
  COUNTRY_OPTIONS,
  DATA_CLASSIFICATION_OPTIONS,
  EMPLOYEE_CATEGORY_OPTIONS,
  EVIDENCE_LEVEL_OPTIONS,
  IMPLEMENTATION_APPROACH_OPTIONS,
} from "@/lib/labels"
import { StepIndicator } from "@/components/step-indicator"
import { useReportUnsaved } from "@/components/unsaved-guard"
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
import { useFormat } from "@/lib/use-format"
import { cn } from "@/lib/utils"

// Werte exakt aus src/types/api.ts gespiegelt -- nicht aus dem Gedaechtnis.
// Schema als Factory (V4.1-S6): die drei benutzersichtbaren Enum-Fehlertexte
// kommen aus dem Sprachkatalog. Die zod-Default-Meldungen (min/max) bleiben
// zod-eigen (sprachneutral/englisch, auch bisher).
type ErrText = (key: string) => string

function makeSchema(tErr: ErrText) {
  return z.object({
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
      { error: tErr("evidence") },
    ),
    adoption_type: z.enum(
      ["voluntary", "recommended_standard", "fixed_process_step"],
      { error: tErr("adoption") },
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
      { error: tErr("data") },
    ),
    regulatory_pressure: z.boolean(),
    competitive_pressure: z.boolean(),
    strategic_priority: z.boolean(),
    notes: z.string().max(2000).optional(),
  })
}

type FormValues = z.infer<ReturnType<typeof makeSchema>>

const STEP_KEYS = ["idee", "menge", "umsetzung", "daten", "pruefen"] as const

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

// Erklaersatz ueber jedem Schritt: was dieser Abschnitt erfasst und wozu.
// Ersetzt den frueheren pauschalen Untertitel auf der Seite.
function SectionIntro({ children }: { children: React.ReactNode }) {
  return (
    <p className="max-w-prose border-l-2 border-border pl-3.5 text-sm leading-relaxed text-muted-foreground">
      {children}
    </p>
  )
}

// Ein Select mit Optionsliste + optionalem Erklaersatz zur aktuellen Auswahl.
// enumKey: Namespace unter enums.* fuer die Options-Labels; helpKey: Namespace
// unter intake.help.* fuer den Erklaersatz zur Auswahl (beide sprachabhaengig).
function SelectField({
  form,
  name,
  label,
  placeholder,
  options,
  enumKey,
  helpKey,
  note,
}: {
  form: ReturnType<typeof useForm<FormValues>>
  name: Path<FormValues>
  label: string
  placeholder: string
  options: { value: string; label: string }[]
  enumKey: string
  helpKey?: string
  note?: string
}) {
  const te = useTranslations("enums")
  const th = useTranslations("intake.help")
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
                    {te(`${enumKey}.${opt.value}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {helpKey && selected && (
              <HelpText>{th(`${helpKey}.${selected}`)}</HelpText>
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

// Ein Abschnitt der Zusammenfassung: Titel + Sprung zurueck in den zugehoerigen
// Schritt zum Korrigieren (die Navigations-Buttons unten bleiben zusaetzlich).
function ReviewSection({
  title,
  editLabel,
  onEdit,
  children,
}: {
  title: string
  editLabel: string
  onEdit: () => void
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-border bg-card px-5 py-1">
      <div className="flex items-center justify-between gap-3 border-b border-border py-3">
        <h3 className="eyebrow">{title}</h3>
        <button
          type="button"
          onClick={onEdit}
          className="text-xs font-medium text-[var(--ink)] underline-offset-4 hover:underline"
        >
          {editLabel}
        </button>
      </div>
      <dl className="divide-y divide-border">{children}</dl>
    </section>
  )
}

export function IntakeWizard() {
  const t = useTranslations("intake")
  const tf = useTranslations("intake.fields")
  const tr = useTranslations("intake.review")
  const te = useTranslations("enums")
  const tc = useTranslations("common")
  const tErr = useTranslations("intake.errors")
  const fmt = useFormat()

  const [step, setStep] = useState(0)
  // Richtung des letzten Schrittwechsels -- steuert nur, aus welcher Richtung
  // die neue Ansicht hereinkommt (vor: von rechts, zurueck: von links).
  const [dir, setDir] = useState<1 | -1>(1)
  const [isPending, startTransition] = useTransition()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState<TriageResponse | null>(null)
  // Ein uebernommener Ideation-Entwurf traegt Inhalt, aber form.reset() setzt
  // isDirty wieder auf false -- darum ein eigener Marker fuer den Waechter.
  const [prefilled, setPrefilled] = useState(false)

  // Schema an die aktive Sprache gebunden (Enum-Fehlertexte). Bei einem
  // Sprachwechsel mitten im Formular bleiben die zod-Meldungen bis zum naechsten
  // Mount in der Ausgangssprache -- die Feld-Labels/Hilfetexte wechseln sofort.
  const schema = useMemo(() => makeSchema(tErr), [tErr])

  const form = useForm<FormValues>({
    resolver: zodResolver(schema) as Resolver<FormValues>,
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

  // Datenverlust-Schutz beim Sprachwechsel (Task 8): meldet dem Ungespeichert-
  // Waechter, ob das Formular Inhalt traegt. Zwei Quellen: eigene Eingaben
  // (isDirty) ODER ein uebernommener Ideation-Entwurf (prefilled) -- letzterer
  // laesst isDirty nach form.reset() bei false, traegt aber Inhalt. Nach dem
  // Absenden (submitted gesetzt) ist der Case persistiert -> nichts geht
  // verloren, also kein Warndialog mehr. Der Sprachumschalter fragt diesen
  // Zustand vor dem harten Reload ab.
  useReportUnsaved(submitted === null && (prefilled || form.formState.isDirty))

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
        setPrefilled(true)
      }
    } catch {
      // kaputter/manipulierter Wert -- still ohne Prefill starten.
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function goNext() {
    const valid = await form.trigger(STEP_FIELDS[step])
    if (!valid) return
    setDir(1)
    setStep((s) => Math.min(s + 1, STEP_KEYS.length - 1))
  }

  function goBack() {
    setDir(-1)
    setStep((s) => Math.max(s - 1, 0))
  }

  // Sprung aus der Zusammenfassung zurueck in einen Abschnitt zum Korrigieren.
  function goToStep(target: number) {
    setDir(target > step ? 1 : -1)
    setStep(target)
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
        setSubmitError(e instanceof Error ? e.message : tErr("unknown"))
      }
    })
  }

  // --- Bestaetigung nach dem Absenden (kein Score/keine Zone). ---
  if (submitted !== null) {
    return (
      // stagger laesst Haken, Titel, Text und Aktionen nacheinander auflaufen;
      // beides (stagger + success-mark) haengt in globals.css hinter
      // prefers-reduced-motion -- ohne Bewegung steht alles sofort da.
      <div
        role="status"
        className="stagger rounded-2xl border border-border bg-card px-6 py-10 text-center sm:px-10"
      >
        <span
          aria-hidden
          className="animate-success-mark mx-auto flex size-12 items-center justify-center rounded-full bg-[var(--zone-win-surface)]"
        >
          <CheckCircle2 className="size-6 text-[var(--zone-win)]" />
        </span>
        <h2 className="mt-5 text-xl font-semibold tracking-tight text-foreground">
          {t("confirm.title")}
        </h2>
        <p className="mx-auto mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          {t("confirm.body", { title: submitted.title })}
        </p>
        <p className="mx-auto mt-4 max-w-prose border-t border-border pt-4 text-sm leading-relaxed text-muted-foreground">
          {t("confirm.next")}
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button asChild size="lg">
            <Link href={`/cases/${submitted.id}`}>{t("confirm.toCase")}</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/cases">{t("confirm.toList")}</Link>
          </Button>
        </div>
      </div>
    )
  }

  const v = form.getValues()
  const isLast = step === STEP_KEYS.length - 1
  const steps = STEP_KEYS.map((key) => ({ key, label: t(`steps.${key}`) }))
  const placeholder = t("selectPlaceholder")

  return (
    <Form {...form}>
      <StepIndicator steps={steps} current={step} />

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
        {/* key={step} erzwingt einen Remount pro Schritt -- nur so laeuft die
            Eintritts-Animation bei jedem Wechsel erneut an. */}
        <div
          key={step}
          className={cn(
            "space-y-6",
            dir === 1 ? "animate-step-forward" : "animate-step-back"
          )}
        >
          {/* --- Schritt 1: Idee --- */}
          {step === 0 && (
            <>
              <SectionIntro>{t("sectionIntro.idee")}</SectionIntro>
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{tf("titleLabel")}</FormLabel>
                    <FormControl>
                      <Input placeholder={tf("titlePlaceholder")} {...field} />
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
                      <FormLabel>{tf("submitterLabel")}</FormLabel>
                      <FormControl>
                        <Input placeholder={tf("submitterPlaceholder")} {...field} />
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
                      <FormLabel>{tf("departmentLabel")}</FormLabel>
                      <FormControl>
                        <Input placeholder={tf("departmentPlaceholder")} {...field} />
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
                    <FormLabel>{tf("currentStateLabel")}</FormLabel>
                    <FormControl>
                      <Textarea placeholder={tf("currentStatePlaceholder")} rows={4} {...field} />
                    </FormControl>
                    <HelpText>{tf("currentStateHelp")}</HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="desired_state"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{tf("desiredStateLabel")}</FormLabel>
                    <FormControl>
                      <Textarea placeholder={tf("desiredStatePlaceholder")} rows={4} {...field} />
                    </FormControl>
                    <HelpText>{tf("desiredStateHelp")}</HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="example_process"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{tf("exampleLabel")}</FormLabel>
                    <FormControl>
                      <Textarea placeholder={tf("examplePlaceholder")} rows={3} {...field} />
                    </FormControl>
                    <HelpText>{tf("exampleHelp")}</HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="desired_example_process"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{tf("desiredExampleLabel")}</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder={tf("desiredExamplePlaceholder")}
                        rows={3}
                        {...field}
                      />
                    </FormControl>
                    <HelpText>{tf("desiredExampleHelp")}</HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </>
          )}

          {/* --- Schritt 2: Zeit & Häufigkeit --- */}
          {step === 1 && (
            <>
              <SectionIntro>{t("sectionIntro.menge")}</SectionIntro>
              <div className="grid gap-5 sm:grid-cols-2">
                <SelectField
                  form={form}
                  name="country"
                  label={tf("countryLabel")}
                  placeholder={placeholder}
                  options={COUNTRY_OPTIONS}
                  enumKey="country"
                />
                <SelectField
                  form={form}
                  name="employee_category"
                  label={tf("employeeCategoryLabel")}
                  placeholder={placeholder}
                  options={EMPLOYEE_CATEGORY_OPTIONS}
                  enumKey="employeeCategory"
                  note={tf("employeeCategoryHelp")}
                />
              </div>
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="time_per_case_hours_current"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{tf("timeCurrentLabel")}</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.1" placeholder={tf("timeCurrentPlaceholder")} {...field} />
                      </FormControl>
                      <HelpText>{tf("timeCurrentHelp")}</HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="time_per_case_hours_with_ai"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{tf("timeAiLabel")}</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.1" placeholder={tf("timeAiPlaceholder")} {...field} />
                      </FormControl>
                      <HelpText>{tf("timeAiHelp")}</HelpText>
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
                      <FormLabel>{tf("occurrencesLabel")}</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder={tf("occurrencesPlaceholder")} {...field} />
                      </FormControl>
                      <HelpText>{tf("occurrencesHelp")}</HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="affected_employees_count"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{tf("employeesLabel")}</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder={tf("employeesPlaceholder")} {...field} />
                      </FormControl>
                      <HelpText>{tf("employeesHelp")}</HelpText>
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
              <SectionIntro>{t("sectionIntro.umsetzung")}</SectionIntro>
              <SelectField
                form={form}
                name="implementation_approach"
                label={tf("approachLabel")}
                placeholder={placeholder}
                options={IMPLEMENTATION_APPROACH_OPTIONS}
                enumKey="implementationApproach"
                helpKey="approach"
                note={t("noteOptionalApproach")}
              />
              <div className="grid gap-5 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="implementation_cost_eur"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{tf("implCostLabel")}</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} placeholder={tf("implCostPlaceholder")} {...field} />
                      </FormControl>
                      <HelpText>{tf("implCostHelp")}</HelpText>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="estimated_license_cost_eur"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{tf("licenseCostLabel")}</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} placeholder={tf("licenseCostPlaceholder")} {...field} />
                      </FormControl>
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
              <SectionIntro>{t("sectionIntro.daten")}</SectionIntro>
              <SelectField
                form={form}
                name="data_classification"
                label={tf("dataClassLabel")}
                placeholder={placeholder}
                options={DATA_CLASSIFICATION_OPTIONS}
                enumKey="dataClassification"
                helpKey="data"
                note={t("noteRequired")}
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
                        {tf("piiLabel")}
                      </span>
                    </label>
                    <HelpText>{tf("piiHelp")}</HelpText>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <SelectField
                form={form}
                name="adoption_type"
                label={tf("adoptionLabel")}
                placeholder={placeholder}
                options={ADOPTION_TYPE_OPTIONS}
                enumKey="adoptionType"
                helpKey="adoption"
                note={t("noteRequired")}
              />
              <SelectField
                form={form}
                name="evidence_level"
                label={tf("evidenceLabel")}
                placeholder={placeholder}
                options={EVIDENCE_LEVEL_OPTIONS}
                enumKey="evidenceLevel"
                helpKey="evidence"
                note={t("noteRequired")}
              />

              <fieldset className="space-y-3 border-t border-border pt-5">
                <legend className="eyebrow mb-1">{t("pressure.legend")}</legend>
                {(
                  [
                    ["regulatory_pressure", t("pressure.regulatoryLabel"), t("pressure.regulatoryHint")],
                    ["competitive_pressure", t("pressure.competitiveLabel"), t("pressure.competitiveHint")],
                    ["strategic_priority", t("pressure.strategicLabel"), t("pressure.strategicHint")],
                  ] as const
                ).map(([name, label, hint]) => (
                  <FormField
                    key={name}
                    control={form.control}
                    name={name as Path<FormValues>}
                    render={({ field }) => (
                      <FormItem>
                        <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/40 has-data-[state=checked]:border-[var(--ink)]/40 has-data-[state=checked]:bg-[var(--ink-subtle)]">
                          <FormControl>
                            <Checkbox className="mt-0.5" checked={Boolean(field.value)} onCheckedChange={field.onChange} />
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
                    <FormLabel>{tf("notesLabel")}</FormLabel>
                    <FormControl>
                      <Textarea placeholder={tf("notesPlaceholder")} rows={3} {...field} />
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
              <SectionIntro>{t("sectionIntro.pruefen")}</SectionIntro>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {t("review.intro")}
              </p>

              <div className="space-y-4">
                <ReviewSection
                  title={tr("sectionIdee")}
                  editLabel={tr("editSection")}
                  onEdit={() => goToStep(0)}
                >
                  <ReviewRow label={tr("rowTitle")} value={v.title} />
                  <ReviewRow label={tr("rowSubmitter")} value={v.submitter} />
                  <ReviewRow label={tr("rowDepartment")} value={v.department} />
                  <ReviewRow label={tr("rowCurrentState")} value={v.current_state} />
                  <ReviewRow label={tr("rowDesiredState")} value={v.desired_state} />
                  <ReviewRow label={tr("rowExample")} value={v.example_process} />
                  <ReviewRow label={tr("rowDesiredExample")} value={v.desired_example_process ?? ""} />
                </ReviewSection>

                <ReviewSection
                  title={tr("sectionMenge")}
                  editLabel={tr("editSection")}
                  onEdit={() => goToStep(1)}
                >
                  <ReviewRow label={tr("rowCountry")} value={v.country ? te(`country.${v.country}`) : ""} />
                  <ReviewRow
                    label={tr("rowEmployeeCategory")}
                    value={v.employee_category ? te(`employeeCategory.${v.employee_category}`) : ""}
                  />
                  <ReviewRow label={tr("rowTimeCurrent")} value={`${v.time_per_case_hours_current} ${tr("hoursUnit")}`} />
                  <ReviewRow label={tr("rowTimeAi")} value={`${v.time_per_case_hours_with_ai} ${tr("hoursUnit")}`} />
                  <ReviewRow label={tr("rowOccurrences")} value={String(v.occurrences_per_employee_per_year)} />
                  <ReviewRow label={tr("rowEmployees")} value={String(v.affected_employees_count)} />
                </ReviewSection>

                <ReviewSection
                  title={tr("sectionUmsetzung")}
                  editLabel={tr("editSection")}
                  onEdit={() => goToStep(2)}
                >
                  <ReviewRow
                    label={tr("rowApproach")}
                    value={v.implementation_approach ? te(`implementationApproach.${v.implementation_approach}`) : ""}
                  />
                  <ReviewRow label={tr("rowImplCost")} value={fmt.eur(v.implementation_cost_eur || 0)} />
                  <ReviewRow label={tr("rowLicenseCost")} value={fmt.eur(v.estimated_license_cost_eur || 0)} />
                </ReviewSection>

                <ReviewSection
                  title={tr("sectionDaten")}
                  editLabel={tr("editSection")}
                  onEdit={() => goToStep(3)}
                >
                  <ReviewRow
                    label={tr("rowDataClass")}
                    value={v.data_classification ? te(`dataClassification.${v.data_classification}`) : ""}
                  />
                  <ReviewRow label={tr("rowPii")} value={v.contains_pii ? tr("yes") : tr("no")} />
                  <ReviewRow
                    label={tr("rowAdoption")}
                    value={v.adoption_type ? te(`adoptionType.${v.adoption_type}`) : ""}
                  />
                  <ReviewRow
                    label={tr("rowEvidence")}
                    value={v.evidence_level ? te(`evidenceLevel.${v.evidence_level}`) : ""}
                  />
                  <ReviewRow
                    label={tr("rowPressure")}
                    value={
                      [
                        v.regulatory_pressure && tr("pressureRegulatory"),
                        v.competitive_pressure && tr("pressureCompetitive"),
                        v.strategic_priority && tr("pressureStrategic"),
                      ]
                        .filter(Boolean)
                        .join(", ") || tr("pressureNone")
                    }
                  />
                  {v.notes && v.notes.length > 0 && (
                    <ReviewRow label={tr("rowNotes")} value={v.notes} />
                  )}
                </ReviewSection>
              </div>

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
            {tc("back")}
          </Button>

          {isLast ? (
            <Button type="submit" size="lg" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isPending ? t("submitting") : t("submit")}
            </Button>
          ) : (
            <Button type="button" size="lg" onClick={goNext}>
              {tc("next")}
              <ArrowRight className="size-4" />
            </Button>
          )}
        </div>
      </form>
    </Form>
  )
}

export default IntakeWizard
