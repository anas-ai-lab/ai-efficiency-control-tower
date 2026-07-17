"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

import { LEAF_ORIGIN_ATTR } from "@/components/leaf-transition";

// Primaer-Navigation im Header. Client-Komponente nur wegen usePathname
// (aktiver Link) -- das Layout selbst bleibt Server Component. Dezente
// Text-Links auf den Design-Tokens, keine Pill-Nav: aktiv = Tinten-Akzent
// (--ink) + kraeftigeres Gewicht + feine Unterstreichung.
//
// V4-P-Auth: adminOnly-Links (Board, Monitoring) sind nur fuer Angemeldete
// sichtbar -- die Sicherheit erzwingt das Backend (require_admin), die Nav
// blendet sie nur aus. S4: hideForAdmin blendet die Einreicher-Pfade
// (Einreichen, Ideen-Assistent) fuer eingeloggte Admins aus -- ihre Rolle ist
// Pruefen/Entscheiden, nicht Einreichen. Anonymer Zustand unveraendert.
interface NavLink {
  href: string;
  labelKey: string;
  adminOnly: boolean;
  hideForAdmin: boolean;
}

const LINKS: NavLink[] = [
  { href: "/", labelKey: "start", adminOnly: false, hideForAdmin: false },
  { href: "/einreichen", labelKey: "submit", adminOnly: false, hideForAdmin: true },
  { href: "/ideation", labelKey: "ideas", adminOnly: false, hideForAdmin: true },
  { href: "/cases", labelKey: "cases", adminOnly: false, hideForAdmin: false },
  { href: "/board", labelKey: "board", adminOnly: true, hideForAdmin: false },
  { href: "/monitoring", labelKey: "monitoring", adminOnly: true, hideForAdmin: false },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  // /cases aktiv auch auf der Detailseite /cases/[id].
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MainNav({ authenticated }: { authenticated: boolean }) {
  const pathname = usePathname();
  const t = useTranslations("nav");
  const links = LINKS.filter((link) => {
    if (link.adminOnly && !authenticated) return false;
    if (link.hideForAdmin && authenticated) return false;
    return true;
  });

  return (
    // Unter md liegt die Nav als volle Reihe UNTER Wortmarke/Steuerung
    // (order-last + w-full) -- eine Reihe reicht dort nicht, siehe layout.tsx.
    // Ab md steht sie wieder neben der Wortmarke und schiebt per mr-auto die
    // rechte Gruppe an den Rand. overflow-x-auto bleibt als Netz fuer laengere
    // Labels (EN) stehen; die Leiste selbst wird ausgeblendet.
    <nav
      aria-label={t("mainNav")}
      className="order-last flex w-full min-w-0 items-center gap-4 overflow-x-auto [scrollbar-width:none] sm:gap-5 md:order-2 md:mr-auto md:w-auto [&::-webkit-scrollbar]:hidden"
    >
      {links.map((link) => {
        const active = isActive(pathname, link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            // Blatt-Effekt beim Seitenwechsel (v4.2). Der aktive Link wechselt
            // die Seite nicht -- also auch keine Blaetter.
            {...(active ? {} : { [LEAF_ORIGIN_ATTR]: "" })}
            className={
              // shrink-0 + whitespace-nowrap: im Scroll-Kasten darf ein Label
              // weder umbrechen noch gestaucht werden.
              active
                ? "shrink-0 whitespace-nowrap text-[0.8rem] font-semibold text-[var(--ink)] underline decoration-[var(--ink)]/40 decoration-1 underline-offset-[6px]"
                : "shrink-0 whitespace-nowrap text-[0.8rem] font-medium text-muted-foreground underline-offset-[6px] transition-colors hover:text-foreground hover:underline hover:decoration-border"
            }
          >
            {t(link.labelKey)}
          </Link>
        );
      })}
    </nav>
  );
}
