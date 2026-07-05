"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Primaer-Navigation im Header. Client-Komponente nur wegen usePathname
// (aktiver Link) -- das Layout selbst bleibt Server Component. Dezente
// Text-Links auf den Design-Tokens, keine Pill-Nav: aktiv = Tinten-Akzent
// (--ink) + kraeftigeres Gewicht + feine Unterstreichung.
const LINKS = [
  { href: "/", label: "Einreichen" },
  { href: "/ideation", label: "Ideen-Assistent" },
  { href: "/cases", label: "Ideenliste" },
  { href: "/board", label: "Board" },
  { href: "/monitoring", label: "Monitoring" },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  // /cases aktiv auch auf der Detailseite /cases/[id].
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MainNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Hauptnavigation" className="flex items-center gap-4 sm:gap-5">
      {LINKS.map((link) => {
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
