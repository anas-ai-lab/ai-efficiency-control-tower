"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Primaer-Navigation im Header. Client-Komponente nur wegen usePathname
// (aktiver Link) -- das Layout selbst bleibt Server Component. Dezente
// Text-Links auf den Design-Tokens, keine Pill-Nav: aktiv = Tinten-Akzent
// (--ink) + kraeftigeres Gewicht + feine Unterstreichung.
//
// V4-P-Auth: adminOnly-Links (Board, Monitoring) sind nur fuer Angemeldete
// sichtbar -- die Sicherheit erzwingt das Backend (require_admin), die Nav
// blendet sie nur aus.
const LINKS = [
  { href: "/", label: "Einreichen", adminOnly: false },
  { href: "/ideation", label: "Ideen-Assistent", adminOnly: false },
  { href: "/cases", label: "Ideenliste", adminOnly: false },
  { href: "/board", label: "Board", adminOnly: true },
  { href: "/monitoring", label: "Monitoring", adminOnly: true },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  // /cases aktiv auch auf der Detailseite /cases/[id].
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MainNav({ authenticated }: { authenticated: boolean }) {
  const pathname = usePathname();
  const links = LINKS.filter((link) => authenticated || !link.adminOnly);

  return (
    <nav aria-label="Hauptnavigation" className="flex items-center gap-4 sm:gap-5">
      {links.map((link) => {
        const active = isActive(pathname, link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            className={
              active
                ? "text-[0.8rem] font-semibold text-[var(--ink)] underline decoration-[var(--ink)]/40 decoration-1 underline-offset-[6px]"
                : "text-[0.8rem] font-medium text-muted-foreground underline-offset-[6px] transition-colors hover:text-foreground hover:underline hover:decoration-border"
            }
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
