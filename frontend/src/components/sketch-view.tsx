"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
} from "react";
import { useTranslations } from "next-intl";
import {
  Loader2,
  Maximize,
  Maximize2,
  Minimize,
  RefreshCw,
  RotateCcw,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

import {
  generateArchitectureSketch,
  type SketchGenerateResult,
} from "@/app/actions";
import { LlmAction } from "@/components/llm-action";
import { useTrackLlmCall } from "@/components/llm-busy";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useFormat } from "@/lib/use-format";
import type { ArchitectureSketchResponse } from "@/types/api";

// Zoom-Grenzen der Grossansicht. 0.5x zeigt auch eine breite Skizze ganz,
// 4x reicht bis auf Label-Ebene -- darueber hinaus wird die SVG nur unscharf
// skaliert, ohne mehr Information zu tragen.
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 4;
const ZOOM_STEP = 0.25;

function clampZoom(value: number): number {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));
}

// Liest das aktive App-Theme aus der .dark-Klasse auf <html> und reagiert auf
// Wechsel. Der ThemeToggle togglet nur diese Klasse (kein next-themes, kein
// Context) -- dieselbe MutationObserver-Bruecke wie in board-matrix.tsx.
// Wird GENAU EINMAL je Skizze aufgerufen (in SketchDiagram) und als Wert an
// Inline- und Modal-Ansicht durchgereicht: zwei Beobachter fuer dieselbe
// Klasse waeren doppelte Arbeit an derselben Wahrheit.
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
// Theme kommt als Wert von aussen (siehe useIsDark); bei Wechsel wird neu
// gezeichnet. Wirft mermaid beim Parsen/Rendern, faellt die Anzeige auf den
// Quelltext zurueck (Zustand e).
//
// Die erzeugte SVG bekommt preserveAspectRatio="xMidYMid meet" per Attribut
// gesetzt (nicht per String-Ersetzung an der sanitisierten Ausgabe) und traegt
// per CSS !important die volle Container-Breite: mermaid schreibt ein
// max-width in Pixeln als Inline-Style, das eine normale Klasse nicht schlagen
// wuerde.
function MermaidDiagram({
  source,
  isDark,
  className,
}: {
  source: string;
  isDark: boolean;
  className?: string;
}) {
  const t = useTranslations("sketch");
  const rawId = useId();
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const renderSeq = useRef(0);
  const hostRef = useRef<HTMLDivElement>(null);

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

  // Skalierungsregel der SVG selbst: mittig einpassen, nichts abschneiden.
  useEffect(() => {
    hostRef.current
      ?.querySelector("svg")
      ?.setAttribute("preserveAspectRatio", "xMidYMid meet");
  }, [svg]);

  if (failed) {
    return (
      <div className={className}>
        <div className="overflow-x-auto rounded-xl border border-border bg-muted/30 p-4">
          <pre className="text-xs leading-relaxed text-foreground/90">
            {source}
          </pre>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {t("renderFailed")}
        </p>
      </div>
    );
  }

  if (svg === null) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center gap-2.5 px-4 py-6 text-sm text-muted-foreground"
      >
        <Loader2 className="size-4 animate-spin text-[var(--ink)]" />
        {t("drawing")}
      </div>
    );
  }

  return (
    <div
      ref={hostRef}
      className={`mermaid-diagram [&_svg]:!h-full [&_svg]:!w-full [&_svg]:!max-w-full ${className ?? ""}`}
      // securityLevel "strict" -> mermaid liefert bereits sanitisierte SVG.
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

// Werkzeugleiste der Grossansicht. Sitzt IM Diagramm-Container, nicht im
// Dialog-Rahmen: der Container ist das Vollbild-Element, eine Leiste
// ausserhalb waere im Vollbild unsichtbar -- und damit auch der Weg zurueck.
function ZoomToolbar({
  zoom,
  onZoomIn,
  onZoomOut,
  onReset,
  fullscreenAvailable,
  isFullscreen,
  onToggleFullscreen,
}: {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  fullscreenAvailable: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
}) {
  const t = useTranslations("sketch");
  return (
    <div className="absolute top-3 right-3 z-10 flex items-center gap-1 rounded-xl border border-border bg-background/95 p-1 shadow-sm">
      <span
        aria-live="polite"
        className="px-2 text-xs text-muted-foreground tnum"
      >
        {t("zoomLevel", { percent: Math.round(zoom * 100) })}
      </span>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-11"
        aria-label={t("zoomOut")}
        title={t("zoomOut")}
        disabled={zoom <= MIN_ZOOM}
        onClick={onZoomOut}
      >
        <ZoomOut aria-hidden />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-11"
        aria-label={t("zoomIn")}
        title={t("zoomIn")}
        disabled={zoom >= MAX_ZOOM}
        onClick={onZoomIn}
      >
        <ZoomIn aria-hidden />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-11"
        aria-label={t("zoomReset")}
        title={t("zoomReset")}
        onClick={onReset}
      >
        <RotateCcw aria-hidden />
      </Button>
      {fullscreenAvailable && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-11"
          aria-label={t(isFullscreen ? "fullscreenExit" : "fullscreenEnter")}
          title={t(isFullscreen ? "fullscreenExit" : "fullscreenEnter")}
          onClick={onToggleFullscreen}
        >
          {isFullscreen ? <Minimize aria-hidden /> : <Maximize aria-hidden />}
        </Button>
      )}
    </div>
  );
}

// Skizze mit Inline-Ansicht und Grossansicht im Modal.
//
// Zoom und Pan laufen ausschliesslich ueber ein CSS-Transform auf einem
// Wrapper um die fertige SVG -- mermaid.render() laeuft dabei NICHT erneut.
// Das ist der Grund fuer den Zuschnitt: ein Rerender je Zoomschritt waere ein
// vollstaendiger Layout-Lauf (dagre) pro Mausrad-Tick.
export function SketchDiagram({ source }: { source: string }) {
  const t = useTranslations("sketch");
  const isDark = useIsDark();
  const [open, setOpen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [fullscreenAvailable, setFullscreenAvailable] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const dragOriginRef = useRef<{ x: number; y: number } | null>(null);

  const resetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  // Vollbild-Verfuegbarkeit erst im Browser lesen (kein document beim SSR).
  // Ist sie false, wird der Knopf gar nicht erst gerendert -- ein Knopf, der
  // nur eine Fehlermeldung produzieren kann, ist kein Angebot.
  useEffect(() => {
    setFullscreenAvailable(document.fullscreenEnabled);
    const onChange = () => setIsFullscreen(document.fullscreenElement !== null);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  // Mausrad-Zoom als nativer Listener mit { passive: false }: React haengt
  // wheel am Root passiv ein, ein preventDefault() im onWheel-Prop bliebe
  // wirkungslos (und die Seite hinter dem Modal wuerde mitscrollen).
  useEffect(() => {
    const viewport = viewportRef.current;
    if (viewport === null) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      setZoom((current) => clampZoom(current - event.deltaY * 0.002 * current));
    };
    viewport.addEventListener("wheel", onWheel, { passive: false });
    return () => viewport.removeEventListener("wheel", onWheel);
  }, [open]);

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) {
      resetView();
      dragOriginRef.current = null;
      setIsDragging(false);
      if (document.fullscreenElement !== null) {
        void document.exitFullscreen().catch(() => {});
      }
    }
  }

  function toggleFullscreen() {
    const stage = stageRef.current;
    if (stage === null) return;
    if (document.fullscreenElement !== null) {
      void document.exitFullscreen().catch(() => {});
    } else {
      void stage.requestFullscreen().catch(() => {});
    }
  }

  function handleMouseDown(event: ReactMouseEvent<HTMLDivElement>) {
    dragOriginRef.current = { x: event.clientX, y: event.clientY };
    setIsDragging(true);
  }

  // Der Versatz wird durch den Zoom geteilt: translate steht INNERHALB des
  // scale(), ein Pixel Mausweg ist dort nur 1/zoom Einheiten.
  function handleMouseMove(event: ReactMouseEvent<HTMLDivElement>) {
    const origin = dragOriginRef.current;
    if (origin === null) return;
    const dx = event.clientX - origin.x;
    const dy = event.clientY - origin.y;
    dragOriginRef.current = { x: event.clientX, y: event.clientY };
    setPan((current) => ({
      x: current.x + dx / zoom,
      y: current.y + dy / zoom,
    }));
  }

  function endDrag() {
    dragOriginRef.current = null;
    setIsDragging(false);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <div className="w-full">
        {/* Das Diagramm selbst oeffnet die Grossansicht. Als <button>, damit
            es per Tastatur erreichbar ist und Radix den Fokus danach wieder
            dorthin zurueckgibt. */}
        <button
          type="button"
          aria-label={t("enlargeAria")}
          onClick={() => setOpen(true)}
          className="block w-full cursor-zoom-in rounded-xl border border-border bg-card p-4 text-left outline-none focus-visible:ring-3 focus-visible:ring-ring/35"
        >
          {/* Feste Buehnenhoehe statt mitwachsender SVG: zusammen mit
              preserveAspectRatio="xMidYMid meet" fuellt die Skizze die Flaeche
              mittig aus, egal ob sie breit oder hoch geraten ist. */}
          <MermaidDiagram
            source={source}
            isDark={isDark}
            className="h-[420px] w-full"
          />
        </button>
        <div className="mt-2 flex justify-end">
          <DialogTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              <Maximize2 aria-hidden />
              {t("enlarge")}
            </Button>
          </DialogTrigger>
        </div>
      </div>

      <DialogContent
        className="max-h-[90vh] w-[90vw] max-w-[90vw] overflow-y-auto"
        // Im Vollbild schliesst Escape ZUERST das Vollbild, nicht das Modal.
        // Radix wuerde sonst beides auf einmal beenden; ein Druck, zwei
        // verlorene Zustaende.
        onEscapeKeyDown={(event) => {
          if (document.fullscreenElement !== null) {
            event.preventDefault();
            void document.exitFullscreen().catch(() => {});
          }
        }}
      >
        <DialogTitle className="pr-10 text-sm font-medium">
          {t("modalTitle")}
        </DialogTitle>
        <DialogDescription className="text-xs">
          {t("modalHint")}
        </DialogDescription>

        <div
          ref={stageRef}
          className="relative mt-3 h-[70vh] min-h-[420px] overflow-hidden rounded-xl border border-border bg-card [&:fullscreen]:mt-0 [&:fullscreen]:h-screen [&:fullscreen]:rounded-none [&:fullscreen]:border-0"
        >
          <ZoomToolbar
            zoom={zoom}
            onZoomIn={() => setZoom((z) => clampZoom(z + ZOOM_STEP))}
            onZoomOut={() => setZoom((z) => clampZoom(z - ZOOM_STEP))}
            onReset={resetView}
            fullscreenAvailable={fullscreenAvailable}
            isFullscreen={isFullscreen}
            onToggleFullscreen={toggleFullscreen}
          />
          <div
            ref={viewportRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={endDrag}
            onMouseLeave={endDrag}
            // Kein touch-action: none -- die nativen Pinch-Gesten auf dem
            // Handy bleiben damit erhalten.
            className={`flex h-full items-center justify-center p-4 ${
              isDragging ? "cursor-grabbing" : "cursor-grab"
            }`}
          >
            <div
              className="h-full w-full origin-center"
              style={{
                transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
              }}
            >
              <MermaidDiagram
                source={source}
                isDark={isDark}
                className="h-full w-full"
              />
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SectionShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations("sketch");
  return (
    <section className="mt-10">
      <p className="eyebrow mb-3">{t("section")}</p>
      {children}
    </section>
  );
}

interface SketchViewProps {
  caseId: string;
  // Persistierte Skizze aus dem GET beim Seitenaufbau (null = nie erzeugt).
  initialSketch: ArchitectureSketchResponse | null;
  // S4-D: die Skizze setzt einen uebernommenen Loesungsvorschlag voraus (Backend
  // 409 NoProposalForSketchError). Ist keiner vorhanden, ist der Button vorab
  // deaktiviert + Grund -- kein roher 409 mehr in der UI.
  hasSolution: boolean;
}

// Abschnitt "Architektur-Skizze" der Detail-Seite (P13). Fuenf Zustaende:
// a) Skizze vorhanden -> rendern + "Neu erzeugen"; b) keine, erzeugbar ->
// Button + Ladezustand; c) 409 (kein Loesungsvorschlag) -> Button deaktiviert +
// Hinweis; d) 5xx -> Fehlertext + Retry; e) Render-Fehler -> Quelltext-Fallback
// (in MermaidDiagram). Ob ein Loesungsvorschlag existiert, verraet einzig der
// 409 des POST -- CaseSummary fuehrt das nicht; darum wird Zustand c) LAZY aus
// einem Fehlversuch abgeleitet (kein neues Backend-Feld, kein Vorab-Deaktivieren).
export function SketchView({
  caseId,
  initialSketch,
  hasSolution,
}: SketchViewProps) {
  const t = useTranslations("sketch");
  const fmt = useFormat();
  const trackLlmCall = useTrackLlmCall();
  const [sketch, setSketch] = useState<ArchitectureSketchResponse | null>(
    initialSketch,
  );
  const [isLoading, setIsLoading] = useState(false);
  const [noProposal, setNoProposal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runGenerate(isRegen: boolean): Promise<void> {
    if (isRegen && !window.confirm(t("confirmRegen"))) {
      return;
    }
    setIsLoading(true);
    setError(null);
    let result: SketchGenerateResult;
    try {
      result = await trackLlmCall(() => generateArchitectureSketch(caseId));
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
        <SketchDiagram source={sketch.mermaid_source} />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs leading-relaxed text-muted-foreground">
            {t("generatedAt", { date: fmt.dateShort(sketch.generated_at) })}
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
            {isLoading ? t("regenerating") : t("regenerate")}
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

  // Zustand c) -- kein (uebernommener) Loesungsvorschlag: Button vorab
  // deaktiviert + Grund (S4-D). hasSolution kommt vom Detail-Page; noProposal ist
  // der defensive Fallback, falls ein 409 doch noch durchkommt.
  if (!hasSolution || noProposal) {
    return (
      <SectionShell>
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="text-sm leading-relaxed text-muted-foreground">
            {t("noProposal")}
          </p>
          <Button
            type="button"
            size="xl"
            className="mt-4 w-full"
            disabled
            title={t("noProposalTooltip")}
          >
            {t("generate")}
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
        {t("intro")}
      </p>
      <LlmAction
        onAction={() => runGenerate(false)}
        isLoading={isLoading}
        idleLabel={t("generate")}
        loadingLabel={t("generating")}
        hint={t("hint")}
        error={error}
      />
    </SectionShell>
  );
}

export default SketchView;
