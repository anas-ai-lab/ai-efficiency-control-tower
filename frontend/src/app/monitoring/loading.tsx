import { Skeleton } from "@/components/ui/skeleton";

// Route-Ladezustand (/monitoring): waehrend GET /cases fuer die freigegebenen
// und umgesetzten Faelle.
export default function Loading() {
  return (
    <main className="mx-auto max-w-4xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Monitoring</p>
      <Skeleton className="mt-3 h-8 w-96 max-w-full" />
      <Skeleton className="mt-3 h-4 w-full max-w-prose" />

      <div className="mt-8 overflow-hidden rounded-xl border border-border">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-6 border-b border-border bg-card px-5 py-4 last:border-b-0"
          >
            <div className="min-w-0 flex-1 space-y-1.5">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="hidden h-5 w-28 sm:block" />
            <Skeleton className="h-8 w-40" />
          </div>
        ))}
      </div>
    </main>
  );
}
