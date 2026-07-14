"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react"

// Leichter Waechter fuer ungespeicherte Formular-Eingaben (V4.1-S6, Task 8).
//
// Der Sprachumschalter (components/lang-toggle) laedt beim Wechsel HART neu
// (window.location.reload) -- ein offener Intake-Wizard verliert dabei seinen
// Zwischenstand. Der Wizard meldet ueber useReportUnsaved seinen "hat
// Eingaben"-Zustand an diesen Waechter; der Umschalter fragt vor dem Reload
// useUnsavedGuard() ab und zeigt bei true einen Bestaetigungsdialog. Leerer
// Formularstate -> direkter Wechsel wie bisher.
//
// Bewusst ein Ref statt State: das Tippen im Formular soll den Header (mit dem
// Umschalter) nicht bei jedem Anschlag neu rendern. Der Umschalter liest den
// aktuellen Wert erst beim Klick.
type UnsavedGuard = {
  report: (hasUnsaved: boolean) => void
  hasUnsaved: () => boolean
}

const UnsavedGuardContext = createContext<UnsavedGuard | null>(null)

export function UnsavedGuardProvider({ children }: { children: ReactNode }) {
  const dirtyRef = useRef(false)
  const value = useMemo<UnsavedGuard>(
    () => ({
      report: (hasUnsaved: boolean) => {
        dirtyRef.current = hasUnsaved
      },
      hasUnsaved: () => dirtyRef.current,
    }),
    [],
  )
  return (
    <UnsavedGuardContext.Provider value={value}>
      {children}
    </UnsavedGuardContext.Provider>
  )
}

// Ein Formular meldet seinen Ungespeichert-Zustand. Beim Unmount (Wegnavigieren)
// wird zurueckgesetzt, damit ein verlassenes Formular den Waechter nicht
// "schmutzig" hinterlaesst.
export function useReportUnsaved(hasUnsaved: boolean): void {
  const guard = useContext(UnsavedGuardContext)
  useEffect(() => {
    if (!guard) return
    guard.report(hasUnsaved)
    return () => guard.report(false)
  }, [guard, hasUnsaved])
}

// Der Umschalter liest den aktuellen Zustand (kein Re-Render-Abo). Ohne Provider
// (kein Wizard im Baum) meldet die Funktion stets false -> Wechsel wie bisher.
export function useUnsavedGuard(): () => boolean {
  const guard = useContext(UnsavedGuardContext)
  return useCallback(() => guard?.hasUnsaved() ?? false, [guard])
}
