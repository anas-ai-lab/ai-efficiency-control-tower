"use client"

import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTransition, useState } from "react"
import { Loader2 } from "lucide-react"
import { submitTriage } from "@/app/actions"
import { TriageResponse } from "@/types/api"
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

const formSchema = z.object({
  title: z.string().min(5).max(200),
  submitter: z.string().min(1).max(100),
  department: z.string().min(1).max(100),
  current_state: z.string().min(30).max(2000),
  desired_state: z.string().min(30).max(2000),
  example_process: z.string().min(20).max(2000),
  time_savings_hours_per_case: z.coerce.number().positive().max(8),
  frequency_per_year: z.coerce.number().int().positive().max(1000000),
  affected_employees_count: z.coerce.number().int().positive().max(50000),
  employee_category: z.enum(["junior", "professional", "senior", "mixed"]),
  evidence_level: z.enum(["pure_estimate", "similar_project", "tested_piloted"]),
  adoption_type: z.enum(["mandatory", "voluntary"]),
  implementation_approach: z.enum([
    "standard_product",
    "custom_build",
    "vendor_solution",
  ]),
  estimated_license_cost_eur: z.coerce.number().min(0).max(10000000),
  implementation_complexity: z.coerce.number().int().min(1).max(5),
  contains_pii: z.boolean(),
  data_classification: z.enum([
    "no_personal_data",
    "pseudonymous",
    "personal",
    "sensitive_personal",
  ]),
  regulatory_pressure: z.boolean(),
  competitive_pressure: z.boolean(),
  strategic_priority: z.boolean(),
})

type FormValues = z.infer<typeof formSchema>

interface IntakeFormProps {
  onSuccess: (result: TriageResponse) => void
}

// Editoriales Abschnitts-Layout: linke Spalte Meta (Nummer, Titel, Erklaerung),
// rechte Spalte Felder. Ersetzt die gestapelten Standard-Cards.
function Section({
  index,
  title,
  description,
  children,
}: {
  index: string
  title: string
  description: string
  children: React.ReactNode
}) {
  return (
    <section className="grid gap-x-10 gap-y-5 py-9 first:pt-0 md:grid-cols-[minmax(0,13rem)_1fr]">
      <div className="md:pt-0.5">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-medium text-foreground/35 tnum">
            {index}
          </span>
          <h2 className="text-[0.95rem] font-semibold tracking-tight text-foreground">
            {title}
          </h2>
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  )
}

export function IntakeForm({ onSuccess }: IntakeFormProps) {
  const [isPending, startTransition] = useTransition()
  const [submitError, setSubmitError] = useState<string | null>(null)

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
      time_savings_hours_per_case: 0,
      frequency_per_year: 0,
      affected_employees_count: 0,
      estimated_license_cost_eur: 0,
      implementation_complexity: 3,
      contains_pii: false,
      regulatory_pressure: false,
      competitive_pressure: false,
      strategic_priority: false,
      evidence_level: "pure_estimate",
    },
  })

  function onSubmit(data: FormValues) {
    setSubmitError(null)
    startTransition(async () => {
      try {
        const result = await submitTriage(data)
        onSuccess(result)
      } catch (e) {
        setSubmitError(e instanceof Error ? e.message : "Unbekannter Fehler")
      }
    })
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <div className="divide-y divide-border">
          {/* 01 Stammdaten */}
          <Section
            index="01"
            title="Stammdaten"
            description="Wer reicht den Use Case ein und wie heißt er?"
          >
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Titel</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Kurzer, prägnanter Titel des Use Cases"
                      {...field}
                    />
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
          </Section>

          {/* 02 Prozessbeschreibung */}
          <Section
            index="02"
            title="Prozessbeschreibung"
            description="Ist-Zustand, Soll-Zustand und ein konkretes Beispiel."
          >
            <FormField
              control={form.control}
              name="current_state"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Ist-Zustand</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Wie läuft der Prozess heute ab?"
                      rows={4}
                      {...field}
                    />
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
                    <Textarea
                      placeholder="Wie soll der Prozess zukünftig ablaufen?"
                      rows={4}
                      {...field}
                    />
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
                  <FormLabel>Beispielprozess</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Konkretes Beispiel eines typischen Durchlaufs"
                      rows={4}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </Section>

          {/* 03 Mengen & Zeit */}
          <Section
            index="03"
            title="Mengen & Zeit"
            description="Quantitative Grundlage der ROI-Berechnung."
          >
            <div className="grid gap-5 sm:grid-cols-3">
              <FormField
                control={form.control}
                name="time_savings_hours_per_case"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Zeit / Fall (Std.)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.1" placeholder="0,5" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="frequency_per_year"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fälle / Jahr</FormLabel>
                    <FormControl>
                      <Input type="number" placeholder="500" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="affected_employees_count"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mitarbeitende</FormLabel>
                    <FormControl>
                      <Input type="number" placeholder="20" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid gap-5 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="employee_category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mitarbeiterkategorie</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Bitte wählen" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="junior">Junior</SelectItem>
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="senior">Senior</SelectItem>
                        <SelectItem value="mixed">Gemischt</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="implementation_complexity"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Implementierungskomplexität</FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(Number(v))}
                      defaultValue={String(field.value)}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Bitte wählen" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">1 – Trivial</SelectItem>
                        <SelectItem value="2">2</SelectItem>
                        <SelectItem value="3">3 – Mittel</SelectItem>
                        <SelectItem value="4">4</SelectItem>
                        <SelectItem value="5">5 – Sehr hoch</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </Section>

          {/* 04 Evidenz & Verbindlichkeit */}
          <Section
            index="04"
            title="Evidenz & Verbindlichkeit"
            description="Belastbarkeit der Annahmen und Art der Nutzung."
          >
            <FormField
              control={form.control}
              name="evidence_level"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Evidenzlevel</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Bitte wählen" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="pure_estimate">Schätzung</SelectItem>
                      <SelectItem value="similar_project">Analogieprojekt</SelectItem>
                      <SelectItem value="tested_piloted">Pilotiert/Gemessen</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-5 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="adoption_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nutzungsverbindlichkeit</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Bitte wählen" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="mandatory">Pflichtnutzung</SelectItem>
                        <SelectItem value="voluntary">Freiwillig</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="implementation_approach"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Implementierungsansatz</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Bitte wählen" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="standard_product">Standard-Produkt</SelectItem>
                        <SelectItem value="custom_build">Eigenentwicklung</SelectItem>
                        <SelectItem value="vendor_solution">Drittanbieter</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </Section>

          {/* 05 Kosten */}
          <Section
            index="05"
            title="Kosten"
            description="Wiederkehrende Lizenzkosten fließen in den Nettonutzen ein."
          >
            <FormField
              control={form.control}
              name="estimated_license_cost_eur"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Geschätzte Lizenzkosten (EUR / Jahr)</FormLabel>
                  <FormControl>
                    <Input type="number" min={0} placeholder="0" {...field} />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    0 = Open Source oder intern
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />
          </Section>

          {/* 06 Datenschutz */}
          <Section
            index="06"
            title="Datenschutz"
            description="Grundlage der DSGVO- und Compliance-Bewertung."
          >
            <FormField
              control={form.control}
              name="contains_pii"
              render={({ field }) => (
                <FormItem>
                  <label className="flex cursor-pointer items-center gap-2.5">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <span className="text-sm font-medium text-foreground">
                      Enthält personenbezogene Daten (PII)
                    </span>
                  </label>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="data_classification"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Datenklassifizierung</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Bitte wählen" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="no_personal_data">
                        Keine personenbezogenen Daten
                      </SelectItem>
                      <SelectItem value="pseudonymous">Pseudonymisiert</SelectItem>
                      <SelectItem value="personal">Personenbezogen</SelectItem>
                      <SelectItem value="sensitive_personal">
                        Besondere Kategorien (Art. 9 DSGVO)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
          </Section>

          {/* 07 Handlungsdruck */}
          <Section
            index="07"
            title="Handlungsdruck"
            description="Externe Faktoren, die eine Bewertung höher einstufen können."
          >
            <FormField
              control={form.control}
              name="regulatory_pressure"
              render={({ field }) => (
                <FormItem>
                  <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/40 has-data-[state=checked]:border-[var(--ink)]/40 has-data-[state=checked]:bg-[var(--ink-subtle)]">
                    <FormControl>
                      <Checkbox
                        className="mt-0.5"
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <span className="grid gap-0.5">
                      <span className="text-sm font-medium text-foreground">
                        Regulatorischer Druck
                      </span>
                      <span className="text-xs leading-relaxed text-muted-foreground">
                        Gesetzliche oder aufsichtsrechtliche Anforderungen
                        erzwingen Handlungsbedarf.
                      </span>
                    </span>
                  </label>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="competitive_pressure"
              render={({ field }) => (
                <FormItem>
                  <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/40 has-data-[state=checked]:border-[var(--ink)]/40 has-data-[state=checked]:bg-[var(--ink-subtle)]">
                    <FormControl>
                      <Checkbox
                        className="mt-0.5"
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <span className="grid gap-0.5">
                      <span className="text-sm font-medium text-foreground">
                        Wettbewerbsdruck
                      </span>
                      <span className="text-xs leading-relaxed text-muted-foreground">
                        Mitbewerber setzen vergleichbare Lösungen bereits ein.
                      </span>
                    </span>
                  </label>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="strategic_priority"
              render={({ field }) => (
                <FormItem>
                  <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/40 has-data-[state=checked]:border-[var(--ink)]/40 has-data-[state=checked]:bg-[var(--ink-subtle)]">
                    <FormControl>
                      <Checkbox
                        className="mt-0.5"
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <span className="grid gap-0.5">
                      <span className="text-sm font-medium text-foreground">
                        Strategische Priorität
                      </span>
                      <span className="text-xs leading-relaxed text-muted-foreground">
                        Der Use Case ist explizit Teil der Unternehmensstrategie
                        oder eines Vorstandsziels.
                      </span>
                    </span>
                  </label>
                  <FormMessage />
                </FormItem>
              )}
            />
          </Section>
        </div>

        <div className="mt-9 space-y-3">
          {submitError && (
            <p
              role="alert"
              className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
            >
              {submitError}
            </p>
          )}
          <Button
            type="submit"
            size="xl"
            disabled={isPending}
            className="w-full"
          >
            {isPending && <Loader2 className="size-4 animate-spin" />}
            {isPending ? "Use Case wird bewertet …" : "Use Case einreichen"}
          </Button>
        </div>
      </form>
    </Form>
  )
}

export default IntakeForm
