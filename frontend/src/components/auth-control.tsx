"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";

import { logout } from "@/app/actions";

// Header-Auth-Steuerung (V4-P-Auth): angemeldet -> Logout-Button, sonst ein
// dezenter Login-Link. Der Logout ruft die Server-Action (Cookie + Backend-
// Session weg) und laesst danach die Server-Komponenten neu auswerten.
export function AuthControl({ authenticated }: { authenticated: boolean }) {
  const router = useRouter();
  const pathname = usePathname();
  const [pending, startTransition] = useTransition();

  if (!authenticated) {
    // Auf /login selbst keinen weiteren Login-Link zeigen.
    if (pathname === "/login") return null;
    return (
      <Link
        href="/login"
        className="text-[0.8rem] font-medium text-muted-foreground underline-offset-[6px] transition-colors hover:text-foreground hover:underline hover:decoration-border"
      >
        Admin-Login
      </Link>
    );
  }

  function handleLogout() {
    startTransition(async () => {
      await logout();
      router.push("/");
      router.refresh();
    });
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={pending}
      className="text-[0.8rem] font-medium text-muted-foreground underline-offset-[6px] transition-colors hover:text-foreground hover:underline hover:decoration-border disabled:opacity-60"
    >
      {pending ? "Abmelden …" : "Abmelden"}
    </button>
  );
}

export default AuthControl;
