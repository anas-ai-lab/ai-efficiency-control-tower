"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Loader2 } from "lucide-react";

import type { SolutionProposalResponse } from "@/types/api";
import { acceptSolution, proposeSolution, rejectSolution } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { ActionError } from "@/components/action-error";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// "Lösung vorschlagen" (S4-E): erzeugt einen Draft (propose, persistiert
// solution_draft, aendert nichts am Case) und oeffnet ein Modal mit zwei
// vollstaendig lesbaren, scrollbaren Reitern. "Übernehmen" persistiert beide
// Varianten (accept), "Verwerfen" -- ebenso ein Schliessen ueber X/Escape/
// Overlay -- verwirft den Draft serverseitig (reject) und hinterlaesst nichts.
// Damit hat auch die technische Variante einen expliziten Freigabe-Weg.
export function SolutionModal({
  caseId,
  hasSolution,
}: {
  caseId: string;
  hasSolution: boolean;
}) {
  const t = useTranslations("solution");
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState<SolutionProposalResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const acceptedRef = useRef(false);

  async function handlePropose() {
    setLoading(true);
    setError(null);
    acceptedRef.current = false;
    try {
      setDraft(await proposeSolution(caseId));
    } catch (e) {
      setError(
        e instanceof Error ? e.message : t("proposeError"),
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleAccept() {
    setBusy(true);
    setError(null);
    try {
      await acceptSolution(caseId);
      acceptedRef.current = true;
      hardRefresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("acceptError"));
      setBusy(false);
    }
  }

  // Schliessen ohne Übernehmen = Verwerfen: den offenen Draft serverseitig
  // leeren (fire-and-forget; 409 "kein Draft" ist unkritisch).
  function handleOpenChange(open: boolean) {
    if (open) return;
    if (draft !== null && !acceptedRef.current) {
      void rejectSolution(caseId).catch(() => {});
    }
    setDraft(null);
    setBusy(false);
    setError(null);
  }

  return (
    <>
      <Button variant="outline" onClick={handlePropose} disabled={loading}>
        {loading && <Loader2 className="size-4 animate-spin" />}
        {hasSolution ? t("regenerate") : t("propose")}
      </Button>
      {draft === null && <ActionError message={error} className="mt-3" />}

      <Dialog open={draft !== null} onOpenChange={handleOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("title")}</DialogTitle>
            <DialogDescription>{t("description")}</DialogDescription>
          </DialogHeader>

          {draft !== null && (
            <Tabs defaultValue="technical" className="min-h-0 flex-1">
              <TabsList>
                <TabsTrigger value="technical">{t("tabTechnical")}</TabsTrigger>
                <TabsTrigger value="business">{t("tabBusiness")}</TabsTrigger>
              </TabsList>
              <TabsContent
                value="technical"
                className="mt-3 max-h-[45vh] overflow-y-auto rounded-xl border border-border bg-muted/20 p-4"
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
                  {draft.solution_technical}
                </p>
              </TabsContent>
              <TabsContent
                value="business"
                className="mt-3 max-h-[45vh] overflow-y-auto rounded-xl border border-border bg-muted/20 p-4"
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
                  {draft.solution_business}
                </p>
              </TabsContent>
            </Tabs>
          )}

          {draft !== null && <ActionError message={error} className="mt-3" />}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={busy}
            >
              {t("reject")}
            </Button>
            <Button onClick={handleAccept} disabled={busy}>
              {busy ? t("accepting") : t("accept")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default SolutionModal;
