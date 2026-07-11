"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { RotateCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Retry fuer serverseitig gefangene Ladefehler: router.refresh() rendert die
// Server-Komponente neu und stoesst den fehlgeschlagenen Fetch erneut an. In
// eine useTransition gehuellt, damit der Button waehrend des erneuten Ladens
// deaktiviert ist (kein Doppelklick, sichtbares Pending).
export function RetryButton({
  label = "Erneut versuchen",
  className,
}: {
  label?: string;
  className?: string;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      disabled={isPending}
      onClick={() => startTransition(() => router.refresh())}
      className={cn(className)}
    >
      <RotateCw
        aria-hidden
        className={cn(isPending && "motion-safe:animate-spin")}
      />
      {isPending ? "Wird geladen …" : label}
    </Button>
  );
}

export default RetryButton;
