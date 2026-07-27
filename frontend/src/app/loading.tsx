import { Skeleton } from "@/components/ui/skeleton";

// Route-Ladezustand der Startseite. Sie ist force-dynamic und wartet beim
// Rendern auf checkAuth() + GET /stats -- ohne diese Datei gibt es fuer den
// Seitenwechsel nach "/" keine Suspense-Grenze, der Browser bleibt bis zum
// Eintreffen der Server-Antwort auf der alten Seite stehen (sichtbar als
// haengende Adresszeile, bei mehrfachem Klicken als Mehrfach-Laden). Die vier
// uebrigen dynamischen Routen (/board, /cases, /cases/[id], /monitoring) haben
// ihre loading.tsx bereits; /ideation braucht keine (rein client-seitig, kein
// Server-Fetch).
//
// Die Struktur spiegelt components/landing.tsx: Hero (Eyebrow, H1, Fliesstext,
// CTA), das 2x2-Hairline-Raster der Kennzahlen mit der Pipeline-Leiste daneben,
// darunter die Navigations-Kacheln. Radien, Abstaende und Rahmen sind aus dem
// echten Layout uebernommen, damit beim Umschalten nichts springt.
//
// Kein Text -- reine Platzhalter-Flaechen. Damit ist der Ladezustand
// sprachneutral und braucht keinen i18n-Katalog.
//
// Kachelzahl: drei Navigations-Kacheln (der anonyme Fall). Der Auth-Zustand
// steht hier noch nicht fest; die drei oeffentlichen Kacheln sind in beiden
// Faellen vorhanden, die zwei Admin-Kacheln nur im angemeldeten.
export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-20 sm:px-6 sm:py-24">
      {/* Hero */}
      <section className="max-w-2xl">
        <Skeleton className="h-3 w-36" />
        <Skeleton className="mt-4 h-10 w-full sm:h-12" />
        <Skeleton className="mt-3 h-10 w-4/5 sm:h-12" />
        <Skeleton className="mt-6 h-4 w-full max-w-prose" />
        <Skeleton className="mt-2.5 h-4 w-11/12 max-w-prose" />
        <Skeleton className="mt-8 h-9 w-48 rounded-lg" />
      </section>

      {/* Kennzahlen (2x2-Hairline-Raster) + Pipeline-Leiste */}
      <section className="mt-20">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px] lg:items-stretch">
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-[var(--hairline-rule)] bg-[var(--hairline-rule)]">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="flex flex-col justify-between bg-card px-6 py-7"
              >
                <div>
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="mt-3 h-9 w-20" />
                </div>
                <Skeleton className="mt-5 h-3 w-4/5" />
              </div>
            ))}
          </div>

          {/* mt-10 wie am echten PipelineStrip -- der Versatz gegen das
              KPI-Raster gehoert zum Layout, nicht zum Ladezustand. */}
          <div className="mt-10 rounded-2xl border border-[var(--hairline-rule)] bg-card p-6">
            <Skeleton className="h-44 w-full rounded-xl" />
            <div className="mt-3 flex justify-between gap-2 border-t border-[var(--hairline-rule)] pt-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-3 w-12" />
              ))}
            </div>
            <Skeleton className="mt-5 h-4 w-full" />
            <Skeleton className="mt-2 h-4 w-2/3" />
          </div>
        </div>
      </section>

      {/* Navigations-Kacheln */}
      <section className="mt-20">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flex flex-col rounded-2xl border border-[var(--hairline-rule)] bg-card p-6"
            >
              <Skeleton className="size-10 rounded-xl" />
              <Skeleton className="mt-5 h-4 w-32" />
              <Skeleton className="mt-3 h-3 w-full" />
              <Skeleton className="mt-2 h-3 w-3/4" />
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
