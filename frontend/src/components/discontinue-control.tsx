"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"

import { discontinueCase, reinstateCase } from "@/app/actions"
import { ActionError } from "@/components/action-error"
import { Button } from "@/components/ui/button"

// discontinued-Toggle im Monitoring (V4.1-S7): reines Zusatzflag, unabhaengig
// vom CaseStatus-Lifecycle (kein Statuswechsel). Optimistisches Update mit
// Rollback + Fehlertext -- gleiches Muster wie CaseStatusControl.
//
// discontinued/onDiscontinuedChange sind kontrolliert (statt eigenem State):
// die umgebende Zeile (MonitoringRow) braucht denselben Wert fuer die rote
// Hervorhebung -- eine einzige Quelle der Wahrheit statt zweier Kopien, die
// auseinanderlaufen koennten.
export function DiscontinueControl({
  caseId,
  discontinued,
  onDiscontinuedChange,
}: {
  caseId: string
  discontinued: boolean
  onDiscontinuedChange: (next: boolean) => void
}) {
  const t = useTranslations("monitoring")
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function toggle() {
    const prev = discontinued
    const next = !prev
    onDiscontinuedChange(next)
    setPending(true)
    setError(null)

    try {
      const res = next
        ? await discontinueCase(caseId)
        : await reinstateCase(caseId)
      onDiscontinuedChange(res.discontinued)
    } catch (e) {
      onDiscontinuedChange(prev)
      setError(
        e instanceof Error
          ? e.message
          : t(next ? "discontinueError" : "reinstateError"),
      )
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Button
        type="button"
        size="sm"
        variant={discontinued ? "outline" : "destructive"}
        disabled={pending}
        onClick={toggle}
        title={t(discontinued ? "reinstateTooltip" : "discontinueTooltip")}
      >
        {t(discontinued ? "reinstate" : "discontinue")}
      </Button>
      <ActionError message={error} />
    </div>
  )
}

export default DiscontinueControl
