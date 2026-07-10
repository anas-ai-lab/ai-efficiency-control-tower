import type { Metadata } from "next";

import { LoginForm } from "@/components/login-form";

export const metadata: Metadata = {
  title: "Admin-Login | AECT",
};

export default function LoginPage() {
  return (
    <main className="mx-auto max-w-md px-5 py-16 sm:px-6">
      <p className="eyebrow">Admin</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        Anmelden
      </h1>
      <p className="mt-2 mb-8 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Einreichung, Ideen-Assistent und Ideenliste sind ohne Anmeldung nutzbar.
        Der Login schaltet die Admin-Funktionen frei (Board, Monitoring,
        Schärfen, Lösung, Compliance, Report, Statuswechsel).
      </p>
      <LoginForm />
    </main>
  );
}
