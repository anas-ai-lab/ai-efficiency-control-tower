import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeToggle } from "@/components/theme-toggle";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AECT | AI Efficiency Control Tower",
  description: "Intelligenter Vorbewertungs-Layer für KI-Use-Case-Intake",
};

// Setzt die .dark-Klasse vor dem ersten Paint (kein Theme-Flackern). Default
// ist hell; dunkel nur, wenn die Person es ausdruecklich gewaehlt hat.
const themeInitScript = `(function(){try{var t=localStorage.getItem('aect-theme');if(t==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="de"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="flex min-h-full flex-col bg-background">
        <header className="sticky top-0 z-40 border-b border-border/70 bg-background">
          <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-5 sm:px-6">
            <div className="flex items-center gap-2.5">
              <span
                aria-hidden
                className="flex size-7 items-center justify-center rounded-md bg-primary font-mono text-[0.7rem] font-semibold tracking-tight text-primary-foreground"
              >
                AE
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold tracking-tight text-foreground">
                  AECT
                </span>
                <span className="hidden text-xs text-muted-foreground sm:inline">
                  AI Efficiency Control Tower
                </span>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex-1">{children}</div>

        <footer className="mt-auto border-t border-border/70">
          <div className="mx-auto flex max-w-3xl items-start gap-3 px-5 py-5 sm:px-6">
            <span
              aria-hidden
              className="mt-px font-mono text-[0.6rem] font-semibold tracking-wider text-muted-foreground/70"
            >
              EU AI ACT · ART. 50
            </span>
            <p className="max-w-prose text-xs leading-relaxed text-muted-foreground">
              Diese Anwendung nutzt ein KI-System (Azure OpenAI). Alle Ausgaben
              sind unverbindliche Hinweise zur fachlichen Prüfung, kein
              rechtsverbindliches Urteil.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
