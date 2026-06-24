"use client"

import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTransition, useState } from "react"
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
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

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
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {/* Card 1: Stammdaten */}
        <Card>
          <CardHeader>
            <CardTitle>Stammdaten</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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
          </CardContent>
        </Card>

        {/* Card 2: Prozessbeschreibung */}
        <Card>
          <CardHeader>
            <CardTitle>Prozessbeschreibung</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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
          </CardContent>
        </Card>

        {/* Card 3: Mengen & Zeit */}
        <Card>
          <CardHeader>
            <CardTitle>Mengen &amp; Zeit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="time_savings_hours_per_case"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Zeitersparnis pro Fall (Stunden)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.1" placeholder="z.B. 0.5" {...field} />
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
                  <FormLabel>Häufigkeit pro Jahr</FormLabel>
                  <FormControl>
                    <Input type="number" placeholder="z.B. 500" {...field} />
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
                  <FormLabel>Betroffene Mitarbeitende</FormLabel>
                  <FormControl>
                    <Input type="number" placeholder="z.B. 20" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="employee_category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mitarbeiterkategorie</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Bitte waehlen" />
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
                        <SelectValue placeholder="Bitte waehlen" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="1">1 - Trivial</SelectItem>
                      <SelectItem value="2">2</SelectItem>
                      <SelectItem value="3">3 - Mittel</SelectItem>
                      <SelectItem value="4">4</SelectItem>
                      <SelectItem value="5">5 - Sehr hoch</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Card 4: Evidenz & Verbindlichkeit */}
        <Card>
          <CardHeader>
            <CardTitle>Evidenz &amp; Verbindlichkeit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="evidence_level"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Evidenzlevel</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Bitte waehlen" />
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
            <FormField
              control={form.control}
              name="adoption_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nutzungsverbindlichkeit</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Bitte waehlen" />
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
                        <SelectValue placeholder="Bitte waehlen" />
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
          </CardContent>
        </Card>

        {/* Card 5: Kosten */}
        <Card>
          <CardHeader>
            <CardTitle>Kosten</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="estimated_license_cost_eur"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Geschätzte Lizenzkosten (EUR/Jahr)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min={0}
                      placeholder="0"
                      {...field}
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    0 = Open Source oder intern
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Card 6: Datenschutz */}
        <Card>
          <CardHeader>
            <CardTitle>Datenschutz</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="contains_pii"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center gap-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <FormLabel className="font-normal">
                      Enthält personenbezogene Daten (PII)
                    </FormLabel>
                  </div>
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
                        <SelectValue placeholder="Bitte waehlen" />
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
          </CardContent>
        </Card>

        {/* Card 7: Handlungsdruck */}
        <Card>
          <CardHeader>
            <CardTitle>Handlungsdruck</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="regulatory_pressure"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-start gap-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="grid gap-0.5">
                      <FormLabel className="font-normal">
                        Regulatorischer Druck
                      </FormLabel>
                      <p className="text-xs text-muted-foreground">
                        Gesetzliche oder aufsichtsrechtliche Anforderungen erzwingen Handlungsbedarf.
                      </p>
                    </div>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="competitive_pressure"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-start gap-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="grid gap-0.5">
                      <FormLabel className="font-normal">
                        Wettbewerbsdruck
                      </FormLabel>
                      <p className="text-xs text-muted-foreground">
                        Mitbewerber setzen vergleichbare Lösungen bereits ein.
                      </p>
                    </div>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="strategic_priority"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-start gap-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="grid gap-0.5">
                      <FormLabel className="font-normal">
                        Strategische Priorität
                      </FormLabel>
                      <p className="text-xs text-muted-foreground">
                        Der Use Case ist explizit Teil der Unternehmensstrategie oder eines Vorstandsziels.
                      </p>
                    </div>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {submitError && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {submitError}
          </div>
        )}

        <Button type="submit" disabled={isPending} className="w-full">
          {isPending ? "Wird bewertet..." : "Use Case einreichen"}
        </Button>
      </form>
    </Form>
  )
}

export default IntakeForm
