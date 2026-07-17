"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"

import { discontinueCase, reinstateCase } from "@/app/actions"
import { ActionError } from "@/components/action-error"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

// Einstellen/Reaktivieren im Monitoring (V4.1-S7, Begruendungspflicht S8):
// reines Zusatzflag, unabhaengig vom CaseStatus-Lifecycle (kein Statuswechsel).
//
// Kein optimistisches Update mehr (Stand S7): der Akt braucht seit S8 zwei
// Pflichtangaben und damit einen Dialog -- der Nutzer wartet ohnehin auf das
// Absenden, und ein vorweggenommener Zustandswechsel waere hier eine Behauptung
// ueber einen Request, den der Server wegen der 422 noch ablehnen kann.
//
// discontinued/onDiscontinuedChange bleiben kontrolliert (statt eigenem State):
// die umgebende Zeile (MonitoringRow) braucht denselben Wert fuer die
// Hervorhebung -- eine einzige Quelle der Wahrheit statt zweier Kopien.
//
// onEventLogged meldet der Zeile, dass ein neuer Verlaufseintrag existiert;
// eine offene Zeitleiste laedt dann nach, statt den Akt zu verschweigen.
const REASON_MAX = 2000
const ACTOR_MAX = 200

export function DiscontinueControl({
  caseId,
  discontinued,
  onDiscontinuedChange,
  onEventLogged,
}: {
  caseId: string
  discontinued: boolean
  onDiscontinuedChange: (next: boolean) => void
  onEventLogged?: () => void
}) {
  const t = useTranslations("monitoring")
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState("")
  const [actorName, setActorName] = useState("")
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Das Ziel des Akts: ein eingestellter Case wird reaktiviert und umgekehrt.
  const next = !discontinued
  const canSubmit =
    reason.trim().length > 0 && actorName.trim().length > 0 && !pending

  function handleOpenChange(nextOpen: boolean) {
    // Waehrend des Absendens nicht schliessen -- sonst verlöre der Nutzer die
    // Fehlermeldung eines gescheiterten Requests.
    if (pending) return
    setOpen(nextOpen)
    if (!nextOpen) {
      setReason("")
      setActorName("")
      setError(null)
    }
  }

  async function handleSubmit() {
    if (!canSubmit) return
    setPending(true)
    setError(null)

    try {
      const res = next
        ? await discontinueCase(caseId, reason.trim(), actorName.trim())
        : await reinstateCase(caseId, reason.trim(), actorName.trim())
      onDiscontinuedChange(res.discontinued)
      onEventLogged?.()
      setPending(false)
      handleOpenChange(false)
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : t(next ? "discontinueError" : "reinstateError"),
      )
      setPending(false)
    }
  }

  return (
    <>
      <Button
        type="button"
        size="sm"
        variant={discontinued ? "outline" : "destructive"}
        onClick={() => setOpen(true)}
        title={t(discontinued ? "reinstateTooltip" : "discontinueTooltip")}
      >
        {t(discontinued ? "reinstate" : "discontinue")}
      </Button>

      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t(next ? "discontinueDialogTitle" : "reinstateDialogTitle")}
            </DialogTitle>
            <DialogDescription>
              {t(next ? "discontinueDialogDesc" : "reinstateDialogDesc")}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={`reason-${caseId}`}>
                {t("reasonLabel")}
                <span aria-hidden className="text-destructive">
                  *
                </span>
              </Label>
              <Textarea
                id={`reason-${caseId}`}
                required
                rows={3}
                maxLength={REASON_MAX}
                placeholder={t("reasonPlaceholder")}
                value={reason}
                disabled={pending}
                onChange={(e) => setReason(e.target.value.slice(0, REASON_MAX))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`actor-${caseId}`}>
                {t("actorLabel")}
                <span aria-hidden className="text-destructive">
                  *
                </span>
              </Label>
              <Input
                id={`actor-${caseId}`}
                required
                maxLength={ACTOR_MAX}
                placeholder={t("actorPlaceholder")}
                value={actorName}
                disabled={pending}
                onChange={(e) => setActorName(e.target.value.slice(0, ACTOR_MAX))}
              />
            </div>
            <p className="text-xs text-muted-foreground">{t("fieldsRequired")}</p>
          </div>

          <ActionError message={error} className="mt-3" />

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={pending}
            >
              {t("cancel")}
            </Button>
            <Button
              variant={next ? "destructive" : "default"}
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              {pending
                ? t("saving")
                : t(next ? "discontinueConfirm" : "reinstateConfirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default DiscontinueControl
