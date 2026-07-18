import Link from "next/link";
import {
  Activity,
  ArrowRight,
  ClipboardList,
  LayoutGrid,
  Lightbulb,
  ListChecks,
} from "lucide-react";
import { getFormatter, getTranslations } from "next-intl/server";

import type { StatsResponse } from "@/types/api";
import { bindFormat } from "@/lib/format";
import { LEAF_ORIGIN_ATTR } from "@/components/leaf-transition";
import { NavTile } from "@/components/nav-tile";
import { PipelineStrip } from "@/components/pipeline-strip";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";

// Startseite. Server-Komponente, bekommt Kennzahlen + Auth-Zustand als Props.
// Der Gestaltungs-Pass v4.2 hat die Praesentation in zwei Client-Komponenten
// verschoben (StatCard: Zaehl-Animation, NavTile: Feder-Hover) -- diese Datei
// bleibt reine Komposition und Text-Zuordnung.
//
// Die Gradient-Kachel mit dem AE-Monogramm rechts im Hero bleibt entfallen: sie
// war das einzige Element, das Flaeche fuer sich beanspruchte, ohne etwas zu
// sagen. Die Pipeline-Leiste ist ausdruecklich KEIN Ersatz dafuer -- sie fuellt
// keine Luecke im Layout, sondern traegt den Leitsatz aus aect-context.md
// ("AI fuer Ambiguitaet, Regeln fuer Klarheit, Menschen fuer Verantwortung")
// als Inhalt: die vier Stationen Regeln -> RAG -> LLM -> Mensch sind die
// tatsaechliche Verarbeitungskette des Systems. Der Unterschied ist der
// Pruefstein fuer kuenftige Ergaenzungen im Hero: eine Aussage darf bleiben,
// eine Flaeche nicht.
//
// Seit dem KPI-Umbau auf 2x2 steht die Pipeline-Leiste neben statt unter dem
// Fliesstext -- aus reinem Kompositions-/Blickfolge-Grund (sie schliesst das
// KPI-Raster rechts ab), nicht als neue Design-Ausnahme.

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
          Kachelbreite laeuft, liest sich nicht mehr.

          DESIGN-RESET v4.3: Der Mockup-Entwurf aus dem Chat wird vollstaendig
          uebernommen -- Marken-Akzent Indigo/Moss, Schrift-Trio Manrope /
          Fraunces / IBM Plex Mono, Glas-Header, farbiger Schatten unter der
          Hero-CTA, ausgebautes Pipeline-Visual. Das ist eine ausdrueckliche
          Entscheidung des Projektinhabers, keine aus dem Bestand abgeleitete:
          die vorherige Runde war zurueckhaltender, und die drei neu erlaubten
          Effekte (Glas, farbiger Schatten, Glow) sind in frontend/CLAUDE.md
          jeweils auf GENAU EINE Stelle begrenzt worden -- Header, Hero-CTA,
          Pipeline. Ausserhalb dieser drei Stellen bleiben sie verboten.

          EINE bewusste Abweichung vom Mockup: die KPI-Karten bekommen KEINE
          Trend-Zahl und KEINE Sparkline. Der Entwurf zeigt dort ein Delta
          ("+12 % zum Vormonat"); GET /stats liefert aber nur die vier
          Mengen-Staende, keine Historie. Jede Kurve und jedes Delta an dieser
          Stelle waere erfunden -- siehe CLAUDE.md, "Keine erfundenen Zahlen".
          Was die Karten stattdessen tragen, ist der aus denselben Staenden
          ABGELEITETE Trichter-Anteil (Begruendung in stat-card.tsx). */}
      <section className="max-w-2xl">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1 className="mt-4 text-pretty text-4xl leading-[1.12] font-semibold tracking-tight text-foreground sm:text-[3.25rem]">
          {t("heroTitle")}
        </h1>
        <p className="mt-6 max-w-prose text-lg leading-relaxed text-muted-foreground">
          {t("heroLead")}
        </p>
        <div className="mt-8">
          {/* Der farbige Schatten ist laut CLAUDE.md ausschliesslich hier
              erlaubt -- er markiert die eine primaere Aktion der Startseite.
              color-mix gegen --brand-primary statt einer festen Farbe, damit
              der Schatten dem Marken-Token folgt (auch im Dark-Theme). */}
          <Button
            asChild
            size="lg"
            className="shadow-[0_10px_24px_-10px_color-mix(in_oklch,var(--brand-primary),transparent_45%)] transition-shadow hover:shadow-[0_16px_30px_-12px_color-mix(in_oklch,var(--brand-primary),transparent_38%)]"
          >
            <Link href="/einreichen" {...{ [LEAF_ORIGIN_ATTR]: "" }}>
              {t("heroCtaLabel")}
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Kennzahlen + Pipeline-Leiste. Ab lg zweispaltig: 2x2-Raster links,
          Pipeline-Leiste rechts als eigene Spalte (siehe Kommentar oben). Auf
          kleineren Breiten stapeln beide Bloecke untereinander. Ein
          Hairline-Raster traegt die vier Karten: die Fugen sind die Linien
          (gap-px auf der Rule-Farbe), kein Kasten um jede Karte. */}
      <section className="mt-20">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px] lg:items-stretch">
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-[var(--hairline-rule)] bg-[var(--hairline-rule)]">
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
              label={t("kpiApprovedLabel")}
              value={stats ? stats.freigegeben : null}
              hint={t("kpiApprovedHint")}
              share={stats ? shareOf(stats.freigegeben) : null}
              shareLabel={stats ? shareLabel(stats.freigegeben) : null}
            />
            <StatCard
              label={t("kpiImplementedLabel")}
              value={stats ? stats.umgesetzt : null}
              hint={t("kpiImplementedHint")}
              share={stats ? shareOf(stats.umgesetzt) : null}
              shareLabel={stats ? shareLabel(stats.umgesetzt) : null}
            />
          </div>
          <PipelineStrip
            steps={[
              t("pipelineRule"),
              t("pipelineRag"),
              t("pipelineLlm"),
              t("pipelineHuman"),
            ]}
            caption={t("pipelineCaption")}
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
