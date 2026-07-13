"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import type { SharpenedCaseResponse } from "@/types/api";
import {
  generateComplianceHints,
  proposeSolution,
  sharpenCase,
} from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { SharpeningReview } from "@/components/sharpening-review";
import { Button } from "@/components/ui/button";

// Admin-Werkzeuge (Bereich 2 "Analyse & Empfehlung", S4): die mutierenden
// LLM-Trigger fuer einen bereits bewerteten Case. Aus der frueheren
// CaseAdminActions herausgeloest (Entscheidung lebt jetzt in Bereich 3). Nach
// jeder persistierenden Aktion hardRefresh() -> die Server-Komponente laedt
// GET /cases/{id} neu. Sicherheit erzwingt das Backend (require_admin); diese
// Leiste erscheint nur fuer angemeldete Admins mit ausgewertetem Case.

interface Props {
  caseId: string;
  hasSolution: boolean;
  hasCompliance: boolean;
}

export function CaseTools({ caseId, hasSolution, hasCompliance }: Props) {
  const [busy, setBusy] = useState<"sharpen" | "solution" | "compliance" | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<SharpenedCaseResponse | null>(null);

  async function handleSharpen() {
    setBusy("sharpen");
    setError(null);
    try {
      setDraft(await sharpenCase(caseId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Schärfen fehlgeschlagen.");
    } finally {
      setBusy(null);
    }
  }

  async function handleSolution() {
    setBusy("solution");
    setError(null);
    try {
      await proposeSolution(caseId);
      hardRefresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lösungsvorschlag fehlgeschlagen.");
      setBusy(null);
    }
  }

  async function handleCompliance() {
    setBusy("compliance");
    setError(null);
    try {
      await generateComplianceHints(caseId);
      hardRefresh();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Compliance-Prüfung fehlgeschlagen.",
      );
      setBusy(null);
    }
  }

  function handleDraftResolved() {
    setDraft(null);
    hardRefresh();
  }

  return (
    <section className="rounded-2xl border border-border bg-muted/30 p-5">
      <p className="eyebrow">Admin-Werkzeuge</p>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="outline"
          onClick={handleSharpen}
          disabled={busy !== null || draft !== null}
        >
          {busy === "sharpen" && <Loader2 className="size-4 animate-spin" />}
          Schärfen
        </Button>
        <Button variant="outline" onClick={handleSolution} disabled={busy !== null}>
          {busy === "solution" && <Loader2 className="size-4 animate-spin" />}
          {hasSolution ? "Lösung neu erzeugen" : "Lösungsvorschlag"}
        </Button>
        <Button variant="outline" onClick={handleCompliance} disabled={busy !== null}>
          {busy === "compliance" && <Loader2 className="size-4 animate-spin" />}
          {hasCompliance ? "Compliance neu prüfen" : "Compliance-Prüfung"}
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Schärfen, Lösung und Compliance sind LLM-Aktionen · 5–30 Sekunden.
      </p>

      {error !== null && (
        <p
          role="alert"
          className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      {draft !== null && (
        <div className="mt-5">
          <SharpeningReview sharpened={draft} onResolved={handleDraftResolved} />
        </div>
      )}
    </section>
  );
}

export default CaseTools;
