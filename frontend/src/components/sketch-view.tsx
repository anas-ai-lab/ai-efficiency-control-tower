"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";

import {
  generateArchitectureSketch,
  type SketchGenerateResult,
} from "@/app/actions";
import { LlmAction } from "@/components/llm-action";
import { Button } from "@/components/ui/button";
import type { ArchitectureSketchResponse } from "@/types/api";

function formatGeneratedAt(iso: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}

// Liest das aktive App-Theme aus der .dark-Klasse auf <html> und reagiert auf
// Wechsel. Der ThemeToggle togglet nur diese Klasse (kein next-themes, kein
// Context) -- dieselbe MutationObserver-Bruecke wie in board-matrix.tsx.
function useIsDark(): boolean {
  const [isDark, setIsDark] = useState(false);
  useEffect(() => {
    const read = () => document.documentElement.classList.contains("dark");
    setIsDark(read());
    const obs = new MutationObserver(() => setIsDark(read()));
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => obs.disconnect();
  }, []);
  return isDark;
}

// Rendert eine Mermaid-Quelle client-seitig zu SVG. mermaid wird lazy und nur
// im Browser geladen (dynamic import IN diesem Effect -- nie im Server-Bundle).
// Theme folgt dem App-Theme; bei Wechsel wird neu gezeichnet. Wirft mermaid
// beim Parsen/Rendern, faellt die Anzeige auf den Quelltext zurueck (Zustand e).
function MermaidDiagram({ source }: { source: string }) {
  const isDark = useIsDark();
  const rawId = useId();
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const renderSeq = useRef(0);

  useEffect(() => {
    let cancelled = false;
    const seq = ++renderSeq.current;
    setFailed(false);

    void (async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        // securityLevel "strict": mermaid sanitisiert die erzeugte SVG selbst
        // (DOMPurify) -- Voraussetzung fuer das dangerouslySetInnerHTML unten.
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: isDark ? "dark" : "neutral",
        });
        // mermaid nutzt die id als DOM-/CSS-Selektor -- useId() liefert Doppel-
        // punkte, die dort brechen; daher auf alphanumerisch reduzieren. seq
        // haelt die id je Render eindeutig (Theme-Wechsel = neuer Lauf).
        const id = `sketch-${rawId.replace(/[^a-zA-Z0-9]/g, "")}-${seq}`;
        const rendered = await mermaid.render(id, source);
        if (!cancelled) setSvg(rendered.svg);
      } catch {
        // Kein Stack-Trace/kein Wert loggen (koennte Case-Text enthalten).
        if (!cancelled) {
          setFailed(true);
          setSvg(null);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [source, isDark, rawId]);

  if (failed) {
    return (
      <div>
        <div className="overflow-x-auto rounded-xl border border-border bg-muted/30 p-4">
          <pre className="text-xs leading-relaxed text-foreground/90">
            {source}
          </pre>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Die Skizze konnte nicht gezeichnet werden — hier der zugrunde liegende
          Mermaid-Quelltext.
        </p>
      </div>
    );
  }

  if (svg === null) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center gap-2.5 rounded-xl border border-border bg-card px-4 py-6 text-sm text-muted-foreground"
      >
        <Loader2 className="size-4 animate-spin text-[var(--ink)]" />
        Skizze wird gezeichnet …
      </div>
    );
  }

  return (
    <div
      className="mermaid-diagram overflow-x-auto rounded-xl border border-border bg-card p-4 [&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full"
      // securityLevel "strict" -> mermaid liefert bereits sanitisierte SVG.
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

function SectionShell({ children }: { children: React.ReactNode }) {
  return (
    <section className="mt-10">
      <p className="eyebrow mb-3">Architektur-Skizze</p>
      {children}
    </section>
  );
}

interface SketchViewProps {
  caseId: string;
  // Persistierte Skizze aus dem GET beim Seitenaufbau (null = nie erzeugt).
  initialSketch: ArchitectureSketchResponse | null;
}

// Abschnitt "Architektur-Skizze" der Detail-Seite (P13). Fuenf Zustaende:
// a) Skizze vorhanden -> rendern + "Neu erzeugen"; b) keine, erzeugbar ->
// Button + Ladezustand; c) 409 (kein Loesungsvorschlag) -> Button deaktiviert +
// Hinweis; d) 5xx -> Fehlertext + Retry; e) Render-Fehler -> Quelltext-Fallback
// (in MermaidDiagram). Ob ein Loesungsvorschlag existiert, verraet einzig der
// 409 des POST -- CaseSummary fuehrt das nicht; darum wird Zustand c) LAZY aus
// einem Fehlversuch abgeleitet (kein neues Backend-Feld, kein Vorab-Deaktivieren).
export function SketchView({ caseId, initialSketch }: SketchViewProps) {
  const [sketch, setSketch] = useState<ArchitectureSketchResponse | null>(
    initialSketch,
  );
  const [isLoading, setIsLoading] = useState(false);
  const [noProposal, setNoProposal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runGenerate(isRegen: boolean): Promise<void> {
    if (
      isRegen &&
      !window.confirm(
        "Die bestehende Skizze wird durch einen neuen Entwurf ersetzt. Fortfahren?",
      )
    ) {
      return;
    }
    setIsLoading(true);
    setError(null);
    let result: SketchGenerateResult;
    try {
      result = await generateArchitectureSketch(caseId);
    } finally {
      setIsLoading(false);
    }
    switch (result.kind) {
      case "ok":
        setSketch(result.sketch);
        setNoProposal(false);
        break;
      case "no_proposal":
        setNoProposal(true);
        break;
      case "unavailable":
      case "error":
        setError(result.message);
        break;
    }
  }

  // Zustand a) -- Skizze vorhanden. "Neu erzeugen" ueberschreibt den Entwurf,
  // daher mit Bestaetigung. Ein Fehler beim Neu-Erzeugen laesst die bestehende
  // Skizze stehen und zeigt die Meldung darunter.
  if (sketch !== null) {
    return (
      <SectionShell>
        <MermaidDiagram source={sketch.mermaid_source} />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs leading-relaxed text-muted-foreground">
            Erzeugt am {formatGeneratedAt(sketch.generated_at)} · KI-generierter
            Entwurf — zu prüfen, kein verbindliches Zielbild.
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => runGenerate(true)}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="animate-spin" />
            ) : (
              <RefreshCw />
            )}
            {isLoading ? "Wird neu erzeugt …" : "Neu erzeugen"}
          </Button>
        </div>
        {error !== null && (
          <p
            role="alert"
            className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
          >
            {error}
          </p>
        )}
      </SectionShell>
    );
  }

  // Zustand c) -- 409: kein Loesungsvorschlag. Button deaktiviert + Hinweis.
  if (noProposal) {
    return (
      <SectionShell>
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="text-sm leading-relaxed text-muted-foreground">
            Eine Architektur-Skizze braucht einen Lösungsvorschlag als Grundlage
            — für diesen Use Case liegt keiner vor.
          </p>
          <Button type="button" size="xl" className="mt-4 w-full" disabled>
            Skizze erzeugen
          </Button>
        </div>
      </SectionShell>
    );
  }

  // Zustand b) -- keine Skizze, aber erzeugbar (Loesungsvorschlag-Existenz noch
  // unbekannt). LlmAction traegt Leerlauf/Ladezustand/Fehler; ein
  // unavailable/error-Ergebnis zeigt die Meldung und laesst den Button als
  // Retry stehen. Zustand d) (503) faellt hier mit deutschem Fehlertext hinein.
  return (
    <SectionShell>
      <p className="mb-3 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Eine generische Architektur-Skizze aus dem Lösungsvorschlag — fünf
        Bausteintypen als Entwurf, kein verbindliches Zielbild.
      </p>
      <LlmAction
        onAction={() => runGenerate(false)}
        isLoading={isLoading}
        idleLabel="Skizze erzeugen"
        loadingLabel="Skizze wird erzeugt …"
        hint="Dauert einige Sekunden · LLM-Call"
        error={error}
      />
    </SectionShell>
  );
}

export default SketchView;
