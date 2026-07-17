import Link from "next/link";
import {
  ClipboardList,
  Lightbulb,
  ListChecks,
  LayoutGrid,
  Activity,
} from "lucide-react";
import { getFormatter, getTranslations } from "next-intl/server";

import type { StatsResponse } from "@/types/api";
import { bindFormat } from "@/lib/format";
import { NavTile } from "@/components/nav-tile";
import { StatCard } from "@/components/stat-card";

// Startseite. Server-Komponente, bekommt Kennzahlen + Auth-Zustand als Props.
// Der Gestaltungs-Pass v4.2 hat die Praesentation in zwei Client-Komponenten
// verschoben (StatCard: Zaehl-Animation, NavTile: Feder-Hover) -- diese Datei
// bleibt reine Komposition und Text-Zuordnung.
//
// Die Gradient-Kachel mit dem AE-Monogramm rechts im Hero ist entfallen: sie war
// das einzige Element, das Flaeche fuer sich beanspruchte, ohne etwas zu sagen.
// Der Hero traegt jetzt nur noch Text -- die Marke steht im Header.

interface NavCardDef {
  href: string;
  titleKey: string;
  descKey: string;
  // Fertiges Element statt Komponenten-Referenz -- siehe Begruendung an
  // NavTileProps.icon (RSC-Grenze).
  icon: React.ReactNode;
}

// Einheitliche Icon-Groesse an genau einer Stelle: gleicher Strichstil, gleiche
// optische Gewichtung ueber alle Kacheln.
const ICON_CLASS = "size-[1.15rem]";

// Ikonografie: durchgehend Lucide, gleicher Strichstil, gleiche Groesse, alle
// im Tinten-Ton (--ink). Frueher trug jede Kachel einen eigenen Farbakzent --
// drei Akzentfarben nebeneinander sind Dekoration, keine Information.
const PUBLIC_CARDS: NavCardDef[] = [
  {
    href: "/einreichen",
    titleKey: "cardSubmitTitle",
    descKey: "cardSubmitDesc",
    icon: <ClipboardList className={ICON_CLASS} />,
  },
  {
    href: "/ideation",
    titleKey: "cardIdeasTitle",
    descKey: "cardIdeasDesc",
    icon: <Lightbulb className={ICON_CLASS} />,
  },
  {
    href: "/cases",
    titleKey: "cardCasesTitle",
    descKey: "cardCasesDesc",
    icon: <ListChecks className={ICON_CLASS} />,
  },
];

const ADMIN_CARDS: NavCardDef[] = [
  {
    href: "/board",
    titleKey: "cardBoardTitle",
    descKey: "cardBoardDesc",
    icon: <LayoutGrid className={ICON_CLASS} />,
  },
  {
    href: "/monitoring",
    titleKey: "cardMonitoringTitle",
    descKey: "cardMonitoringDesc",
    icon: <Activity className={ICON_CLASS} />,
  },
];

export async function Landing({
  stats,
  authenticated,
}: {
  stats: StatsResponse | null;
  authenticated: boolean;
}) {
  const t = await getTranslations("landing");
  const fmt = bindFormat(await getFormatter());

  // Trichter-Anteil aus echten Staenden abgeleitet -- siehe Begruendung in
  // stat-card.tsx. Ohne Einreichungen gibt es keinen Nenner und damit keinen
  // Anteil (null statt einer Division durch 0).
  const base = stats?.eingereicht ?? 0;
  const shareOf = (v: number): number | null =>
    base > 0 ? Math.min(v / base, 1) : null;
  const shareLabel = (v: number): string | null => {
    const share = shareOf(v);
    return share === null ? null : t("kpiShare", { percent: fmt.percent(share) });
  };

  const cards = authenticated ? [...PUBLIC_CARDS, ...ADMIN_CARDS] : PUBLIC_CARDS;

  return (
    <main className="mx-auto max-w-5xl px-5 py-20 sm:px-6 sm:py-24">
      {/* Hero: einspaltig, viel Luft, kein dekoratives Gegengewicht. Die Breite
          ist bewusst auf ~2/3 begrenzt -- eine Zeile, die ueber die volle
          Kachelbreite laeuft, liest sich nicht mehr. */}
      <section className="max-w-2xl">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1 className="mt-4 text-pretty text-4xl leading-[1.12] font-semibold tracking-tight text-foreground sm:text-[3.25rem]">
          {t("heroTitle")}
        </h1>
        <p className="mt-6 max-w-prose text-lg leading-relaxed text-muted-foreground">
          {t("heroLead")}
        </p>
      </section>

      {/* Kennzahlen. Ein Hairline-Raster traegt die drei Karten: die Fugen sind
          die Linien (gap-px auf der Rule-Farbe), kein Kasten um jede Karte. */}
      <section className="mt-20">
        <div className="grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-[var(--hairline-rule)] bg-[var(--hairline-rule)] sm:grid-cols-3">
          <StatCard
            label={t("kpiSubmittedLabel")}
            value={stats ? stats.eingereicht : null}
            hint={t("kpiSubmittedHint")}
            share={null}
            shareLabel={null}
          />
          <StatCard
            label={t("kpiEvaluatedLabel")}
            value={stats ? stats.bewertet : null}
            hint={t("kpiEvaluatedHint")}
            share={stats ? shareOf(stats.bewertet) : null}
            shareLabel={stats ? shareLabel(stats.bewertet) : null}
          />
          <StatCard
            label={t("kpiImplementedLabel")}
            value={stats ? stats.umgesetzt : null}
            hint={t("kpiImplementedHint")}
            share={stats ? shareOf(stats.umgesetzt) : null}
            shareLabel={stats ? shareLabel(stats.umgesetzt) : null}
          />
        </div>
      </section>

      {/* Navigations-Kacheln. */}
      <section className="mt-20">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <NavTile
              key={card.href}
              href={card.href}
              title={t(card.titleKey)}
              description={t(card.descKey)}
              icon={card.icon}
            />
          ))}
        </div>
      </section>

      {/* Dezenter Admin-Login -- nur fuer Anonyme; Eingeloggte sehen Status +
          Logout im Header. */}
      {!authenticated && (
        <section className="mt-20 border-t border-[var(--hairline)] pt-8">
          <p className="text-sm text-muted-foreground">
            {t("adminPrompt")}{" "}
            <Link
              href="/login"
              className="rounded-sm font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 outline-none hover:decoration-[var(--ink)] focus-visible:ring-2 focus-visible:ring-ring/40"
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
