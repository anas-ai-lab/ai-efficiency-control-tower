"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

// Geteilter "es laeuft gerade ein LLM-Call"-Zustand der Case-Detailseite.
//
// Grund (Hang-Befund): Next.js fuehrt Server Actions SERIALISIERT aus. Wer
// "Freigeben" klickt, waehrend Schaerfen/Compliance/Loesung/Skizze noch laufen,
// haengt recordDecision hinter den belegten Slot -- der Button stand die volle
// Restdauer des LLM-Calls (real bis 75 s, propose-solution bis 135 s) auf "Wird
// gespeichert …", obwohl gar nichts gespeichert wurde. Das las sich wie ein
// Haenger und log ueber den Grund.
//
// Die Werkzeuge (CaseTools, SolutionModal, SketchView) melden ihre laufenden
// LLM-Calls hier an; CaseDecision liest den Zustand und sperrt die Entscheidung
// MIT sichtbarer Begruendung, statt sie stumm in die Warteschlange zu haengen.
//
// Zaehler statt Boolean: es koennen mehrere Werkzeuge parallel laufen -- erst
// wenn der letzte Call aufgeloest ist, ist die Entscheidung wieder frei.
type LlmBusyValue = {
  busy: boolean;
  begin: () => void;
  end: () => void;
};

const LlmBusyContext = createContext<LlmBusyValue | null>(null);

export function LlmBusyProvider({ children }: { children: ReactNode }) {
  const [running, setRunning] = useState(0);
  const begin = useCallback(() => setRunning((n) => n + 1), []);
  const end = useCallback(() => setRunning((n) => Math.max(0, n - 1)), []);
  const value = useMemo(
    () => ({ busy: running > 0, begin, end }),
    [running, begin, end],
  );
  return (
    <LlmBusyContext.Provider value={value}>{children}</LlmBusyContext.Provider>
  );
}

/** True, solange ein angemeldeter LLM-Call laeuft. Ohne Provider: immer false. */
export function useLlmBusy(): boolean {
  return useContext(LlmBusyContext)?.busy ?? false;
}

/**
 * Klammert einen LLM-Call und meldet ihn fuer dessen Dauer als laufend an.
 * Ohne Provider laeuft fn unveraendert durch -- die Werkzeuge bleiben damit
 * auch ausserhalb der Detailseite eigenstaendig nutzbar.
 */
export function useTrackLlmCall(): <T>(fn: () => Promise<T>) => Promise<T> {
  const ctx = useContext(LlmBusyContext);
  return useCallback(
    async <T,>(fn: () => Promise<T>): Promise<T> => {
      ctx?.begin();
      try {
        return await fn();
      } finally {
        ctx?.end();
      }
    },
    [ctx],
  );
}
