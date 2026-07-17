import { getFormatter, getTranslations } from "next-intl/server"
import { CheckCircle2, XCircle } from "lucide-react"

import type { CaseDecision } from "@/types/api"
import { bindFormat } from "@/lib/format"

// Die Board-Entscheidung read-only fuer Nicht-Admins (V4.1-S8) -- das einzige
// Ergebnis der Board-Arbeit, das der Einreicher sieht: was entschieden wurde,
// warum, und wann. Bewusst KEINE Kennzahl, kein Score, kein Report; die
// Begruendung traegt den Fall.
//
// Abgrenzung zu case-decision.tsx: dort das Admin-Steuerelement (Freigeben/
// Ablehnen + Notizfeld), hier reine Praesentation ohne State und ohne Aktion.
// decision ist nie null -- die Detailseite rendert vorher den Wartezustand.

export async function BoardDecisionNotice({
  decision,
}: {
  decision: CaseDecision
}) {
  const t = await getTranslations("boardDecision")
  const td = await getTranslations("decision")
  const fmt = bindFormat(await getFormatter())

  const approved = decision.reviewer_decision === "approved"
  const Icon = approved ? CheckCircle2 : XCircle
  const tone = approved ? "text-[var(--zone-win)]" : "text-destructive"

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center gap-2.5">
        <Icon className={`size-5 ${tone}`} aria-hidden />
        <span className="text-base font-medium text-foreground">
          {td(approved ? "approved" : "rejected")}
        </span>
      </div>

      {decision.decided_at !== null && (
        <p className="mt-1.5 text-xs text-muted-foreground">
          {t("decidedOn", { date: fmt.dateShort(decision.decided_at) })}
        </p>
      )}

      <div className="mt-5 border-t border-border pt-4">
        <p className="eyebrow mb-2">{t("rationale")}</p>
        {decision.reviewer_note !== null && decision.reviewer_note.length > 0 ? (
          <p className="max-w-prose text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
            {decision.reviewer_note}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">{t("noRationale")}</p>
        )}
      </div>
    </div>
  )
}

export default BoardDecisionNotice
