import Link from "next/link";
import {
  ArrowRight,
  ClipboardList,
  Lightbulb,
  ListChecks,
  LayoutGrid,
  Activity,
} from "lucide-react";

import type { StatsResponse } from "@/types/api";
import { formatEUR, formatNumber } from "@/lib/formatters";

// Startseite (V4-P7). Reine Praesentationsschicht -- Server-Komponente, bekommt
// Kennzahlen + Auth-Zustand als Props. Bewusst so geschnitten, dass der
// Design-Pass (V4-P8) nur an den Klassenstrings arbeiten muss: Hero, KPI-Leiste
// und Navigations-Karten sind eigene Bloecke.

interface Kpi {
  label: string;
  value: string;
  hint: string;
}

function statsToKpis(stats: StatsResponse | null): Kpi[] {
  const dash = "—";
  return [
    {
      label: "Eingereichte Ideen",
      value: stats ? formatNumber(stats.eingereicht) : dash,
      hint: "insgesamt erfasst",
    },
    {
      label: "Bewertete Ideen",
      value: stats ? formatNumber(stats.bewertet) : dash,
      hint: "Vorfilter bestanden",
    },
    {
      label: "Umgesetzte Use Cases",
      value: stats ? formatNumber(stats.umgesetzt) : dash,
      hint: "produktiv im Einsatz",
    },
    {
      label: "Netto-Nutzen freigegeben",
      value: stats ? formatEUR(stats.netto_nutzen_freigegeben_eur) : dash,
      hint: "freigegeben + umgesetzt, p.a.",
    },
  ];
}

interface NavCard {
  href: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const PUBLIC_CARDS: NavCard[] = [
  {
    href: "/einreichen",
    title: "Einreichen",
    description: "Beschreibe deinen Use Case in wenigen Schritten.",
    icon: ClipboardList,
  },
  {
    href: "/ideation",
    title: "Ideen-Assistent",
    description:
      "Noch keine fertige Idee? Beschreibe dein Problem — der Assistent macht Entwürfe.",
    icon: Lightbulb,
  },
  {
    href: "/cases",
    title: "Ideenliste",
    description: "Alle eingereichten Ideen und ihr Status — transparent für alle.",
    icon: ListChecks,
  },
];

const ADMIN_CARDS: NavCard[] = [
  {
    href: "/board",
    title: "Board",
    description:
      "Portfolio-Matrix: Nutzen gegen Machbarkeit, jeder Case ein Punkt.",
    icon: LayoutGrid,
  },
  {
    href: "/monitoring",
    title: "Monitoring",
    description:
      "Freigegebene und umgesetzte Use Cases pflegen — Status und Verlaufsnotizen.",
    icon: Activity,
  },
];

function Card({ card }: { card: NavCard }) {
  const Icon = card.icon;
  return (
    <Link
      href={card.href}
      className="group flex flex-col rounded-2xl border border-border bg-card p-5 outline-none transition-colors hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-ring/40"
    >
      <span
        aria-hidden
        className="flex size-9 items-center justify-center rounded-lg bg-[var(--ink-subtle)] text-[var(--ink)]"
      >
        <Icon className="size-4.5" />
      </span>
      <span className="mt-4 flex items-center gap-1.5 text-[0.95rem] font-semibold tracking-tight text-foreground">
        {card.title}
        <ArrowRight className="size-3.5 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
      </span>
      <span className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
        {card.description}
      </span>
    </Link>
  );
}

export function Landing({
  stats,
  authenticated,
}: {
  stats: StatsResponse | null;
  authenticated: boolean;
}) {
  const kpis = statsToKpis(stats);
  const cards = authenticated ? [...PUBLIC_CARDS, ...ADMIN_CARDS] : PUBLIC_CARDS;

  return (
    <main className="mx-auto max-w-5xl px-5 py-14 sm:px-6 sm:py-16">
      {/* Hero: ruhig, praezise, kein Marketing. */}
      <section className="max-w-3xl">
        <p className="eyebrow">AI Efficiency Control Tower</p>
        <h1 className="mt-3 text-pretty text-3xl font-semibold leading-tight tracking-tight text-foreground sm:text-4xl">
          Von der Idee zur belastbaren Entscheidung.
        </h1>
        <p className="mt-4 max-w-prose text-base leading-relaxed text-muted-foreground">
          Reiche deine AI-Idee ein — AECT bewertet Nutzen, Aufwand und Risiko,
          bevor das AI Board entscheidet.
        </p>
      </section>

      {/* KPI-Leiste aus GET /stats. */}
      <section className="mt-10">
        <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-border bg-border lg:grid-cols-4">
          {kpis.map((kpi) => (
            <div key={kpi.label} className="bg-card px-5 py-5">
              <dt className="eyebrow">{kpi.label}</dt>
              <dd className="stat-value mt-2 text-2xl text-foreground sm:text-[1.75rem]">
                {kpi.value}
              </dd>
              <p className="mt-1 text-xs text-muted-foreground">{kpi.hint}</p>
            </div>
          ))}
        </dl>
      </section>

      {/* Navigations-Karten. */}
      <section className="mt-12">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <Card key={card.href} card={card} />
          ))}
        </div>
      </section>

      {/* Dezenter Admin-Login -- nur fuer Anonyme; Eingeloggte sehen Status +
          Logout im Header. */}
      {!authenticated && (
        <section className="mt-10 border-t border-border/70 pt-6">
          <p className="text-sm text-muted-foreground">
            Verwaltest du das Portfolio?{" "}
            <Link
              href="/login"
              className="font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
            >
              Admin-Login
            </Link>{" "}
            — schaltet Board, Monitoring und die Bearbeitungs-Aktionen frei.
          </p>
        </section>
      )}
    </main>
  );
}

export default Landing;
