import type { CaseStatus } from "@/types/api";

// Case-Lifecycle-Status-Semantik (Lifecycle-ADR). Einzige Quelle fuer die
// Status-Darstellung in P5-P7 -- analog ZONE_CONFIG in formatters.ts. Farben
// kommen ausschliesslich aus den bestehenden Design-Tokens (--ink, --zone-*),
// keine Alarm-/Ampelfarben. Klassenstrings sind literal, damit Tailwind sie
// beim Scan erfasst.
//
// Farbzuordnung (bewusst, nicht willkuerlich):
//   submitted       neutral        -- eingegangen, noch nicht bewertet
//   in_review       --ink          -- aktiv in Bearbeitung (Akzentfarbe)
//   approved        --zone-win      -- positiv freigegeben
//   already_exists  neutral/muted  -- kein Fortschritt, Dublette
//   rejected        --zone-gain     -- negatives Verdikt (gedaempftes Rot)
//   implemented     --zone-win      -- Ziel erreicht, kraeftiger als approved
export interface StatusStyle {
  labelDE: string;
  dot: string;
  text: string;
  surface: string;
}

export const STATUS_CONFIG: Record<CaseStatus, StatusStyle> = {
  submitted: {
    labelDE: "Eingereicht",
    dot: "bg-muted-foreground/50",
    text: "text-muted-foreground",
    surface: "border-border bg-muted/40",
  },
  in_review: {
    labelDE: "In Prüfung",
    dot: "bg-[var(--ink)]",
    text: "text-[var(--ink)]",
    surface: "border-[var(--ink)]/25 bg-[var(--ink-subtle)]",
  },
  approved: {
    labelDE: "Freigegeben",
    dot: "bg-[var(--zone-win)]",
    text: "text-[var(--zone-win-fg)]",
    surface: "border-[var(--zone-win-border)] bg-[var(--zone-win-surface)]",
  },
  already_exists: {
    labelDE: "Existiert bereits",
    dot: "bg-muted-foreground/35",
    text: "text-muted-foreground/80",
    surface: "border-border/70 bg-muted/25",
  },
  rejected: {
    labelDE: "Abgelehnt",
    dot: "bg-[var(--zone-gain)]",
    text: "text-[var(--zone-gain-fg)]",
    surface: "border-[var(--zone-gain-border)] bg-[var(--zone-gain-surface)]",
  },
  implemented: {
    labelDE: "Umgesetzt",
    // Kraeftiger als approved: gefuellter Punkt + saturierte Textfarbe (--zone-win
    // statt des weicheren -fg), damit "erreicht" visuell staerker wirkt.
    dot: "bg-[var(--zone-win)]",
    text: "text-[var(--zone-win)]",
    surface: "border-[var(--zone-win)]/35 bg-[var(--zone-win-surface)]",
  },
};

export type StatusKey = keyof typeof STATUS_CONFIG;

// Vor-Bewertungs-Zustand (evaluation_pending, V4.1/ADR-0050): eigene
// Darstellungs-Kategorie, KEIN CaseStatus und KEINE Zone -- deshalb bewusst
// nicht in STATUS_CONFIG/ZONE_CONFIG. Zentrale Quelle fuer Label + Tooltip,
// damit Listen-Badge (cases-table) und Detail-Pending-Box denselben Wortlaut
// teilen. Neutral gehalten: kein Fehler-Rot, kein Zonen-Farbton.
export const EVALUATION_PENDING_DISPLAY = {
  labelDE: "Bewertung ausstehend",
  tooltip:
    "Kein Implementierungsansatz angegeben — Bewertung erfolgt nach Ergänzung durch einen Admin.",
} as const;
