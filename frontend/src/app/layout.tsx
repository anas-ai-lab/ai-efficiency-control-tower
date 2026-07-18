import type { Metadata } from "next";
import Link from "next/link";
import { Manrope, Fraunces, IBM_Plex_Mono } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages, getTranslations } from "next-intl/server";
import "./globals.css";
import { ThemeToggle } from "@/components/theme-toggle";
import { LangToggle } from "@/components/lang-toggle";
import { UnsavedGuardProvider } from "@/components/unsaved-guard";
import { MainNav } from "@/components/main-nav";
import { AuthControl } from "@/components/auth-control";
import { LeafTransition } from "@/components/leaf-transition";
import { checkAuth } from "@/app/actions";

// Schrift-Trio des Design-Resets v4.3 (vorher Geist / Source Serif 4 / Geist
// Mono). Die Konstanten- und CSS-Variablennamen bleiben absichtlich unveraendert
// (--font-geist-sans / --font-source-serif / --font-geist-mono): der
// @theme-inline-Block in globals.css bindet gegen diese Namen, ein Rename waere
// eine Aenderung an jeder Stelle, die Typografie konsumiert, ohne Gegenwert.
//
// Body-Schrift: Manrope. Offenere Punzen und etwas mehr Laufweite als Geist.
// ACHTUNG -- die Begruendung der Geist-Paarung (angeglichene Ziffernbreiten
// zwischen Fliesstext und den .stat-value/.tnum-Zahlen) traegt hier NICHT mehr:
// Manrope und IBM Plex Mono stammen aus verschiedenen Familien. Siehe
// frontend/CLAUDE.md, "visuell gegenpruefen".
const geistSans = Manrope({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

// Display-Schrift NUR fuer H1/H2 (siehe globals.css h1,h2-Regel). Fraunces
// ersetzt Source Serif 4; die optical-size-Achse laesst die Serife in grossen
// Graden staerker kontrastieren, ohne im Kleinen zu zerfallen. Weiterhin
// Editorial-/Governance-Anmutung -- kein "AI-Look", kein Marketing.
const sourceSerif = Fraunces({
  variable: "--font-source-serif",
  subsets: ["latin"],
  axes: ["opsz"],
  display: "swap",
});

// Mono mit tabular-nums fuer alle Zahlen und Betraege. IBM Plex Mono ist ein
// statischer Schnitt -- weight ist im next/font-Typ Pflicht, nicht optional.
const geistMono = IBM_Plex_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("metadata");
  return {
    title: t("title"),
    description: t("description"),
  };
}

// Setzt die .dark-Klasse vor dem ersten Paint (kein Theme-Flackern). Default
// ist hell; dunkel nur, wenn die Person es ausdruecklich gewaehlt hat.
const themeInitScript = `(function(){try{var t=localStorage.getItem('aect-theme');if(t==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // V4-P-Auth: Auth-Zustand serverseitig ermitteln -> steuert Nav-Sichtbarkeit
  // und den Login/Logout-Schalter. Die eigentliche Kontrolle erzwingt das
  // Backend; die UI blendet nur aus.
  const authenticated = await checkAuth();

  // i18n (V4.1-S6): aktive Locale + Messages serverseitig -- der Provider stellt
  // sie den Client-Komponenten zur Verfuegung. lang am <html> folgt der Wahl.
  const locale = await getLocale();
  const messages = await getMessages();
  const t = await getTranslations("footer");

  return (
    <html
      lang={locale}
      suppressHydrationWarning
      className={`${geistSans.variable} ${sourceSerif.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="flex min-h-full flex-col bg-background">
        <NextIntlClientProvider messages={messages}>
        <UnsavedGuardProvider>
        {/* Blatt-Overlay: liegt im Layout (nicht in children), damit der Schwarm
            den Seitenwechsel ueberlebt. Beruehrt die Theme-Transition nicht --
            siehe Architektur-Notiz in leaf-transition.tsx. */}
        <LeafTransition />
        <header className="sticky top-0 z-40 border-b border-[var(--hairline-rule)] bg-background/75 backdrop-blur-md transition-colors supports-[backdrop-filter]:bg-background/60">
          {/* Rahmenbreite = Inhaltsbreite der Seiten (max-w-5xl). Vorher
              max-w-3xl -- die Wortmarke stand dadurch sichtbar nach innen
              versetzt gegen den Hero, den sie rahmen soll. /board lief zuletzt
              als einzige Seite auf 6xl und ragte damit unter dem Rahmen
              hervor; seit v4.2 liegt es ebenfalls auf 5xl, der Rahmen deckt
              jetzt ueberall. */}
          {/* Unter 768px passt die Zeile nicht: Wortmarke (~97px) + Nav (bis
              ~308px im anonymen Zustand) + rechte Gruppe (~212px) + Abstaende
              liegen ueber der Breite. Vorher lief die Nav darum sichtbar UEBER
              Abmelden/Sprache. Darum umbricht die Leiste dort in zwei Reihen
              (Wortmarke + Steuerung oben, Nav darunter); ab md ist es wieder
              exakt eine Reihe. Die Schwelle ist md und nicht sm, weil die
              anonyme Nav bei 640px noch ~25px zu breit ist (gemessen, nicht
              geschaetzt). Die order-/ml-auto-Paare stellen beide Faelle her,
              ohne die Reihenfolge im DOM zu drehen. */}
          <div className="mx-auto flex min-h-14 max-w-5xl flex-wrap items-center gap-x-4 max-md:py-2 px-5 sm:px-6 md:h-14 md:flex-nowrap md:gap-6">
            <Link
              href="/"
              className="order-1 flex shrink-0 items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-accent)]"
            >
              <span
                aria-hidden
                className="flex size-7 items-center justify-center rounded-md bg-primary font-mono text-[0.7rem] font-semibold tracking-tight text-primary-foreground"
              >
                AE
              </span>
              <span className="hidden text-sm font-semibold tracking-tight text-foreground sm:inline">
                AECT
              </span>
            </Link>
            <MainNav authenticated={authenticated} />
            {/* shrink-0: die rechte Gruppe behaelt ihre Breite. ml-auto schiebt
                sie unter md in Reihe 1 nach rechts; ab md uebernimmt das
                mr-auto der Nav. */}
            <div className="order-2 ml-auto flex shrink-0 items-center gap-3 sm:gap-4 md:order-3 md:ml-0">
              <AuthControl authenticated={authenticated} />
              <LangToggle />
              <ThemeToggle />
            </div>
          </div>
        </header>

        <div className="flex-1">{children}</div>

        <footer className="mt-auto border-t border-[var(--hairline-rule)]">
          <div className="mx-auto flex max-w-5xl items-start gap-3 px-5 py-6 sm:px-6">
            <span
              aria-hidden
              className="mt-px font-mono text-[0.6rem] font-semibold tracking-wider text-muted-foreground/70"
            >
              {t("badge")}
            </span>
            <p className="max-w-prose text-xs leading-relaxed text-muted-foreground">
              {t("disclaimer")}
            </p>
          </div>
        </footer>
        </UnsavedGuardProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
