"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import type {
  ComplianceHintsResponse,
  SharpenedCaseResponse,
} from "@/types/api";
import { generateComplianceHints, sharpenCase } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { ActionError } from "@/components/action-error";
import { SharpeningReview } from "@/components/sharpening-review";
import { SolutionModal } from "@/components/solution-modal";
import { Button } from "@/components/ui/button";

// Admin-Werkzeuge (Bereich 2 "Analyse & Empfehlung", S4): die mutierenden
// LLM-Trigger fuer einen bereits bewerteten Case. Schaerfen (Draft -> Diff),
// Loesung (Modal mit Draft/Accept, s. SolutionModal) und -- im abgesetzten
// Management-Teil -- die Compliance-Pruefung, deren Ergebnis INLINE darunter
// rendert (kein Popup, kein Seitenwechsel). Sicherheit erzwingt das Backend
// (require_admin); die Leiste erscheint nur fuer angemeldete Admins mit
// ausgewertetem Case.

interface Props {
  caseId: string;
  hasSolution: boolean;
  hasCompliance: boolean;
}

export function CaseTools({ caseId, hasSolution, hasCompliance }: Props) {
  const [sharpenBusy, setSharpenBusy] = useState(false);
  const [sharpenError, setSharpenError] = useState<string | null>(null);
  const [draft, setDraft] = useState<SharpenedCaseResponse | null>(null);

  const [complianceBusy, setComplianceBusy] = useState(false);
  const [complianceError, setComplianceError] = useState<string | null>(null);
  const [compliance, setCompliance] = useState<ComplianceHintsResponse | null>(
    null,
  );

  async function handleSharpen() {
    setSharpenBusy(true);
    setSharpenError(null);
    try {
      setDraft(await sharpenCase(caseId));
    } catch (e) {
      setSharpenError(e instanceof Error ? e.message : "Schärfen fehlgeschlagen.");
    } finally {
      setSharpenBusy(false);
    }
  }

  function handleDraftResolved() {
    setDraft(null);
    hardRefresh();
  }

  async function handleCompliance() {
    setComplianceBusy(true);
    setComplianceError(null);
    try {
      // Ergebnis inline anzeigen (kein hardRefresh): die Detailseite bleibt
      // stehen, der Report zieht die persistierte Fassung bei naechster
      // Navigation (revalidateCase in der Action).
      setCompliance(await generateComplianceHints(caseId));
    } catch (e) {
      setComplianceError(
        e instanceof Error ? e.message : "Compliance-Prüfung fehlgeschlagen.",
      );
    } finally {
      setComplianceBusy(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-muted/30 p-5">
      <p className="eyebrow">Admin-Werkzeuge</p>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="outline"
          onClick={handleSharpen}
          disabled={sharpenBusy || draft !== null}
        >
          {sharpenBusy && <Loader2 className="size-4 animate-spin" />}
          Schärfen
        </Button>
        <SolutionModal caseId={caseId} hasSolution={hasSolution} />
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Schärfen und Lösung sind LLM-Aktionen · 5–30 Sekunden.
      </p>

      <ActionError message={sharpenError} className="mt-3" />

      {draft !== null && (
        <div className="mt-5">
          <SharpeningReview sharpened={draft} onResolved={handleDraftResolved} />
        </div>
      )}

      {/* Management-Teil: Compliance-Pruefung mit Inline-Ergebnis. */}
      <div className="mt-6 border-t border-border pt-5">
        <p className="eyebrow">Management</p>
        <div className="mt-3">
          <Button
            variant="outline"
            onClick={handleCompliance}
            disabled={complianceBusy}
          >
            {complianceBusy && <Loader2 className="size-4 animate-spin" />}
            {hasCompliance || compliance !== null
              ? "Compliance neu prüfen"
              : "Compliance-Prüfung"}
          </Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          RAG-gestützte Hinweise (EU AI Act Art. 50, ggf. DSGVO Art. 35) · LLM-Aktion.
        </p>

        {complianceBusy && (
          <p
            role="status"
            aria-live="polite"
            className="mt-3 flex items-center gap-2 text-sm text-muted-foreground"
          >
            <Loader2 className="size-4 animate-spin text-[var(--ink)]" />
            Compliance-Hinweise werden geprüft …
          </p>
        )}

        <ActionError message={complianceError} className="mt-3" />

        {compliance !== null && !complianceBusy && (
          <div className="mt-3 rounded-xl border border-border bg-card p-4">
            {compliance.hint_text !== null ? (
              <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
                {compliance.hint_text}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Keine spezifischen Compliance-Hinweise für diesen Fall.
              </p>
            )}
            {compliance.citations.length > 0 && (
              <ul className="mt-3 space-y-1.5 border-t border-border pt-3">
                {compliance.citations.map((c) => (
                  <li key={c.number} className="text-xs text-muted-foreground">
                    <span className="font-mono text-foreground/70">[{c.number}]</span>{" "}
                    {c.citation}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default CaseTools;
