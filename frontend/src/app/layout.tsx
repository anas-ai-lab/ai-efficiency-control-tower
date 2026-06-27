import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

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
  description: "Intelligenter Vorbewertungs-Layer fuer KI-Use-Case-Intake",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="de"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <footer className="mt-auto border-t px-4 py-3 text-center text-xs text-muted-foreground">
          Diese Anwendung nutzt ein KI-System (Azure OpenAI). Alle Ausgaben sind
          unverbindliche Hinweise zur fachlichen Prüfung, kein rechtsverbindliches
          Urteil (EU AI Act Art. 50 Transparenzhinweis).
        </footer>
      </body>
    </html>
  );
}
