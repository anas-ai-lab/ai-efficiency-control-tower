"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

// Gemeinsamer Filter-State fuer Ideenliste, Board und Monitoring.
//
// Der State liegt in den URL-SearchParams -- nicht in useState, nicht in
// localStorage. Damit ist eine gefilterte Sicht teilbar und ueberlebt einen
// Reload; vor allem aber ist sie IMMER aufloesbar: die URL zeigt, was gefiltert
// ist, und das Entfernen der Params fuehrt zurueck. Der frueher benutzte
// useState-Filter konnte in einen leeren Ergebnisbereich fuehren, aus dem die
// UI keinen Rueckweg mehr anbot.
//
// Geschrieben wird per window.history.replaceState, nicht per router.replace.
// Begruendung: alle drei Views filtern rein clientseitig ueber bereits
// geladene Zeilen -- ein router.replace wuerde auf diesen force-dynamic-Routen
// die komplette RSC-Nutzlast neu holen (auf /cases zusaetzlich
// listSimilarityPairs mit O(n^2)-Cosinus) und daraus dieselben Zeilen liefern.
// Next.js unterstuetzt die History-API im App Router ausdruecklich; ein
// useSearchParams() rendert danach neu. Kein Full-Reload, kein
// router.refresh(), keine zweite State-Quelle.
//
// "Kein Filter" ist die Abwesenheit des Params. Beim Zuruecksetzen werden die
// Params geloescht (delete), nicht auf einen Default-Wert wie "all" gesetzt --
// sonst blieben Filter-Reste in teilbaren Links stehen.

export interface FilterParams<K extends string> {
  /** Aktueller Wert oder null, wenn der Filter nicht gesetzt ist. */
  get: (key: K) => string | null;
  /** Setzt einen Filter; null loescht ihn. */
  set: (key: K, value: string | null) => void;
  /** Loescht einen einzelnen Filter (Chip-Entfernen). */
  remove: (key: K) => void;
  /** Loescht alle von dieser Ansicht verwalteten Filter. */
  reset: () => void;
  /** Die aktuell gesetzten Filter-Keys, in der Reihenfolge von `keys`. */
  activeKeys: K[];
  hasActive: boolean;
}

export function useFilterParams<K extends string>(
  keys: readonly K[],
): FilterParams<K> {
  const searchParams = useSearchParams();
  const pathname = usePathname();

  // searchParams.toString() als Dependency statt des Objekts: die Identitaet
  // des Objekts wechselt bei jedem Render, der String nur bei echter Aenderung.
  const query = searchParams.toString();

  const write = useCallback(
    (mutate: (params: URLSearchParams) => void) => {
      const next = new URLSearchParams(query);
      mutate(next);
      const qs = next.toString();
      window.history.replaceState(null, "", qs ? `${pathname}?${qs}` : pathname);
    },
    [pathname, query],
  );

  const get = useCallback(
    (key: K) => searchParams.get(key),
    [searchParams],
  );

  const set = useCallback(
    (key: K, value: string | null) => {
      write((params) => {
        if (value === null) params.delete(key);
        else params.set(key, value);
      });
    },
    [write],
  );

  const remove = useCallback((key: K) => set(key, null), [set]);

  const reset = useCallback(() => {
    write((params) => {
      for (const key of keys) params.delete(key);
    });
    // keys ist je Ansicht eine Modul-Konstante -- stabile Identitaet, die
    // Dependency loest hier keine Neuberechnung pro Render aus.
  }, [write, keys]);

  const activeKeys = useMemo(
    () => keys.filter((key) => searchParams.get(key) !== null),
    [keys, searchParams],
  );

  return {
    get,
    set,
    remove,
    reset,
    activeKeys,
    hasActive: activeKeys.length > 0,
  };
}

// Liest einen Filter-Param gegen eine Whitelist erlaubter Werte. Ein manipulierter
// oder veralteter Link (?status=quatsch) fuehrt so nicht zu einer dauerhaft
// leeren Liste ohne Ursache, sondern wird wie "kein Filter" behandelt.
export function readEnumParam<T extends string>(
  raw: string | null,
  allowed: readonly T[],
): T | null {
  if (raw === null) return null;
  return (allowed as readonly string[]).includes(raw) ? (raw as T) : null;
}
