import Link from "next/link";

// Server-Komponente: Platzhalter fuer Admin-Only-Seiten (Board, Monitoring),
// wenn der Aufrufer nicht angemeldet ist. Die eigentliche Zugriffskontrolle
// erzwingt das Backend (require_admin) -- diese Ansicht blendet nur aus und
// verweist auf den Login.
export function AdminGate({ title }: { title: string }) {
  return (
    <main className="mx-auto max-w-md px-5 py-16 sm:px-6">
      <p className="eyebrow">Admin-Bereich</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        {title}
      </h1>
      <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
        Dieser Bereich ist den angemeldeten Admins vorbehalten. Bitte melde dich
        an, um fortzufahren.
      </p>
      <Link
        href="/login"
        className="mt-4 inline-block text-sm font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
      >
        Zum Admin-Login
      </Link>
    </main>
  );
}

export default AdminGate;
