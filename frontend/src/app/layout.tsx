import type { Metadata } from "next";
import Link from "next/link";
import { Inter, Source_Serif_4, Geist_Mono } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages, getTranslations } from "next-intl/server";
import "./globals.css";
import { ThemeToggle } from "@/components/theme-toggle";
import { LangToggle } from "@/components/lang-toggle";
import { UnsavedGuardProvider } from "@/components/unsaved-guard";
import { MainNav } from "@/components/main-nav";
import { AuthControl } from "@/components/auth-control";
import { checkAuth } from "@/app/actions";

// Body-Schrift: Inter -- neutraler Grotesk-Workhorse (ruhig, hohe Lesbarkeit).
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

// Display-Schrift NUR fuer H1/H2 (siehe globals.css h1,h2-Regel). Eine
// zurueckhaltende Serife setzt die Hierarchie und gibt der Oberflaeche die
// Editorial-/Governance-Anmutung -- kein "AI-Look", kein Marketing.
const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  display: "swap",
});

// Mono mit tabular-nums fuer alle Zahlen und Betraege.
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
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
      className={`${inter.variable} ${sourceSerif.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="flex min-h-full flex-col bg-background">
        <NextIntlClientProvider messages={messages}>
        <UnsavedGuardProvider>
        <header className="sticky top-0 z-40 border-b border-border/70 bg-background">
          <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-4 px-5 sm:px-6">
            <div className="flex min-w-0 items-center gap-4 sm:gap-6">
              <Link
                href="/"
                className="flex items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-accent)]"
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
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <AuthControl authenticated={authenticated} />
              <LangToggle />
              <ThemeToggle />
            </div>
          </div>
        </header>

        <div className="flex-1">{children}</div>

        <footer className="mt-auto border-t border-border/70">
          <div className="mx-auto flex max-w-3xl items-start gap-3 px-5 py-5 sm:px-6">
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
