"use client";

import { useTranslations } from "next-intl";
import { X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

// Gemeinsame Filter-Bausteine fuer Ideenliste, Board und Monitoring.
//
// Zwei Regeln tragen das hier, beide aus dem Defekt "leeres Ergebnis, kein
// Rueckweg":
//   1. Die Toolbar der jeweiligen Ansicht steht IMMER, unabhaengig vom
//      Ergebnis. Kein Early-Return vor ihr.
//   2. Der Empty-State liegt INNERHALB des Ergebnisbereichs und traegt selbst
//      den Weg heraus (Filter zuruecksetzen).
//
// Bestehendes visuelles Vokabular: shadcn Badge (outline) + Button (ghost),
// Marken-Tokens, keine neue Abhaengigkeit, kein neues Icon-Set (lucide ist im
// Projekt gesetzt).

export interface ActiveFilterChip {
  /** SearchParam-Key -- identifiziert den Chip beim Entfernen. */
  key: string;
  /** Dimension, z. B. "Status". */
  label: string;
  /** Gewaehlter Wert in Klartext, z. B. "Freigegeben". */
  value: string;
}

// Zeile unter der Filter-Leiste: aktive Filter als entfernbare Chips, daneben
// die Trefferzahl und ein Reset. Ohne aktive Filter rendert nur die Trefferzahl
// -- die Zeile verschwindet nicht, damit die Toolbar-Hoehe nicht springt.
export function ActiveFilters({
  chips,
  resultLabel,
  onRemove,
  onReset,
}: {
  chips: ActiveFilterChip[];
  resultLabel: string;
  onRemove: (key: string) => void;
  onReset: () => void;
}) {
  const t = useTranslations("filters");
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {chips.map((chip) => (
        <Badge
          key={chip.key}
          variant="outline"
          className="h-6 gap-1.5 py-0 pr-1 pl-2"
        >
          <span className="text-muted-foreground">{chip.label}:</span>
          <span className="text-foreground">{chip.value}</span>
          <button
            type="button"
            onClick={() => onRemove(chip.key)}
            aria-label={t("removeChip", { label: chip.label })}
            className="inline-flex size-4 items-center justify-center rounded-full text-muted-foreground outline-none transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/40"
          >
            <X className="size-3" aria-hidden />
          </button>
        </Badge>
      ))}
      <span className="text-xs text-muted-foreground tabular-nums">
        {resultLabel}
      </span>
      {chips.length > 0 && (
        <Button type="button" variant="ghost" size="xs" onClick={onReset}>
          {t("reset")}
        </Button>
      )}
    </div>
  );
}

// Empty-State fuer einen leeren Ergebnisbereich. Er unterscheidet die beiden
// Faelle, die frueher als ein einziger toter Zustand erschienen sind:
//   onReset gesetzt  -> ein Filter ist aktiv: Hinweis + Rueckweg.
//   onReset undefined -> es gibt wirklich nichts: Hinweis + ggf. eigene Aktion
//                        (children, z. B. der Einreichen-Link der Ideenliste).
// Der Aufrufer waehlt den Text, weil "leer" je Ansicht etwas anderes heisst.
export function EmptyResult({
  message,
  onReset,
  children,
}: {
  message: string;
  onReset?: () => void;
  children?: React.ReactNode;
}) {
  const t = useTranslations("filters");
  return (
    <div className="px-6 py-14 text-center">
      <p className="text-sm text-muted-foreground">{message}</p>
      {onReset !== undefined ? (
        <div className="mt-4">
          <Button type="button" variant="outline" size="sm" onClick={onReset}>
            {t("reset")}
          </Button>
        </div>
      ) : (
        children
      )}
    </div>
  );
}
