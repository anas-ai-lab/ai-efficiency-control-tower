import Link from "next/link";
import {
  ArrowRight,
  ClipboardList,
  Lightbulb,
  ListChecks,
  LayoutGrid,
  Activity,
} from "lucide-react";
import { getTranslations } from "next-intl/server";

import type { StatsResponse } from "@/types/api";
import { formatNumber } from "@/lib/formatters";

// Startseite (V4-P7). Reine Praesentationsschicht -- Server-Komponente, bekommt
// Kennzahlen + Auth-Zustand als Props. Bewusst so geschnitten, dass der
// Design-Pass (V4-P8) nur an den Klassenstrings arbeiten muss: Hero, KPI-Leiste
// und Navigations-Karten sind eigene Bloecke.

interface Kpi {
  label: string;
  value: string;
  hint: string;
}

interface NavCard {
  href: string;
  titleKey: string;
  descKey: string;
  icon: React.ComponentType<{ className?: string }>;
  // Icon-Farbakzent aus der Marken-Palette (Tailwind text-*-Klasse auf einen
  // Token). Kontrast auf --ink-subtle in Light UND Dark geprueft; Gruen laeuft
  // ueber --zone-win-fg (dunkel genug), nicht ueber das helle --brand-positive.
  accent: string;
}

const PUBLIC_CARDS: NavCard[] = [
  {
    href: "/einreichen",
    titleKey: "cardSubmitTitle",
    descKey: "cardSubmitDesc",
    icon: ClipboardList,
    accent: "text-[var(--brand-primary)]",
  },
  {
    href: "/ideation",
    titleKey: "cardIdeasTitle",
    descKey: "cardIdeasDesc",
    icon: Lightbulb,
    accent: "text-[var(--brand-accent)]",
  },
  {
    href: "/cases",
    titleKey: "cardCasesTitle",
    descKey: "cardCasesDesc",
    icon: ListChecks,
    accent: "text-[var(--zone-win-fg)]",
  },
];

const ADMIN_CARDS: NavCard[] = [
  {
    href: "/board",
    titleKey: "cardBoardTitle",
    descKey: "cardBoardDesc",
    icon: LayoutGrid,
    accent: "text-[var(--brand-accent)]",
  },
  {
    href: "/monitoring",
    titleKey: "cardMonitoringTitle",
    descKey: "cardMonitoringDesc",
    icon: Activity,
    accent: "text-[var(--brand-primary)]",
  },
];

function Card({
  card,
  title,
  description,
}: {
  card: NavCard;
  title: string;
  description: string;
}) {
  const Icon = card.icon;
  return (
    <Link
      href={card.href}
      // Hover (S2): Karte hebt 4px, Border -> --brand-accent, Schatten sm -> lg,
      // 200ms ease-out. Transform nur motion-safe -> reduced-motion zeigt reinen
      // Farbwechsel. Tastatur-Fokus gleichwertig: Ring in --brand-accent.
      className="group flex flex-col rounded-2xl border border-border bg-card p-5 shadow-sm outline-none transition-[transform,box-shadow,border-color,background-color] duration-200 ease-out hover:border-[var(--brand-accent)] focus-visible:border-[var(--brand-accent)] focus-visible:ring-2 focus-visible:ring-[var(--brand-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-safe:hover:-translate-y-1 motion-safe:hover:shadow-lg"
    >
      <span
        aria-hidden
        className={`flex size-9 items-center justify-center rounded-lg bg-[var(--ink-subtle)] ${card.accent}`}
      >
        <Icon className="size-4.5" />
      </span>
      <span className="mt-4 flex items-center gap-1.5 text-[0.95rem] font-semibold tracking-tight text-foreground">
        {title}
        <ArrowRight className="size-3.5 text-muted-foreground transition-transform motion-safe:group-hover:translate-x-0.5" />
      </span>
      <span className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
        {description}
      </span>
    </Link>
  );
}

export async function Landing({
  stats,
  authenticated,
}: {
  stats: StatsResponse | null;
  authenticated: boolean;
}) {
  const t = await getTranslations("landing");
  const dash = "—";
  // Netto-Nutzen bewusst NICHT auf der Startseite (S2): der Wert bleibt in
  // Ideenliste und Board, hier nur die Mengen-Kennzahlen.
  const kpis: Kpi[] = [
    {
      label: t("kpiSubmittedLabel"),
      value: stats ? formatNumber(stats.eingereicht) : dash,
      hint: t("kpiSubmittedHint"),
    },
    {
      label: t("kpiEvaluatedLabel"),
      value: stats ? formatNumber(stats.bewertet) : dash,
      hint: t("kpiEvaluatedHint"),
    },
    {
      label: t("kpiImplementedLabel"),
      value: stats ? formatNumber(stats.umgesetzt) : dash,
      hint: t("kpiImplementedHint"),
    },
  ];
  const cards = authenticated ? [...PUBLIC_CARDS, ...ADMIN_CARDS] : PUBLIC_CARDS;

  return (
    <main className="mx-auto max-w-5xl px-5 py-14 sm:px-6 sm:py-16">
      {/* Hero: ruhig, praezise, kein Marketing. Der Gradient laeuft nur auf einer
          begrenzten, dekorativen Akzentflaeche (rechts, ab sm) -- kein
          Full-Screen-Farbrausch. */}
      <section className="grid items-center gap-8 lg:grid-cols-[minmax(0,1fr)_auto]">
        <div className="max-w-2xl">
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1 className="mt-3 text-pretty text-3xl font-semibold leading-tight tracking-tight text-foreground sm:text-4xl">
            {t("heroTitle")}
          </h1>
          <p className="mt-4 max-w-prose text-base leading-relaxed text-muted-foreground">
            {t("heroLead")}
          </p>
        </div>

        {/* Gradient-Akzentflaeche: dekorativ (aria-hidden), traegt nur das
            Monogramm. Feste, kleine Kachel -> deutlich unter 30% Viewport; auf
            Mobile ausgeblendet, damit die Seite ruhig startet. */}
        <div
          aria-hidden
          className="relative hidden h-40 w-56 shrink-0 items-center justify-center overflow-hidden rounded-3xl border border-border/40 shadow-sm [background-image:var(--gradient-hero)] sm:flex"
        >
          <span className="stat-value select-none text-[3.25rem] font-semibold tracking-tight text-[var(--gradient-hero-fg)]">
            AE
          </span>
        </div>
      </section>

      {/* KPI-Leiste aus GET /stats (drei Mengen-Kennzahlen; Netto-Nutzen bewusst
          nicht mehr hier). */}
      <section className="mt-10">
        <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-3">
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
            <Card
              key={card.href}
              card={card}
              title={t(card.titleKey)}
              description={t(card.descKey)}
            />
          ))}
        </div>
      </section>

      {/* Dezenter Admin-Login -- nur fuer Anonyme; Eingeloggte sehen Status +
          Logout im Header. */}
      {!authenticated && (
        <section className="mt-10 border-t border-border/70 pt-6">
          <p className="text-sm text-muted-foreground">
            {t("adminPrompt")}{" "}
            <Link
              href="/login"
              className="font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
            >
              {t("adminLink")}
            </Link>{" "}
            {t("adminSuffix")}
          </p>
        </section>
      )}
    </main>
  );
}

export default Landing;
