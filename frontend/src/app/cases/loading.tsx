import { Skeleton } from "@/components/ui/skeleton";

// Route-Ladezustand (/cases): waehrend GET /cases laeuft. Schimmerndes Skeleton
// in der Form der Ideenliste -- klar unterscheidbar vom "wird geprueft"-
// Fachzustand (ruhiges Badge, kein Schimmern) in der Tabelle selbst.
export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Ideenliste</p>
      <Skeleton className="mt-3 h-8 w-72" />
      <Skeleton className="mt-3 h-4 w-full max-w-prose" />

      <div className="mt-8">
        <div className="mb-4 flex flex-wrap items-end gap-4">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-8 w-44" />
          <Skeleton className="ml-auto h-8 w-36" />
        </div>
        <div className="space-y-px overflow-hidden rounded-xl border border-border">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 bg-card px-4 py-3.5">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="ml-auto h-5 w-28" />
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
