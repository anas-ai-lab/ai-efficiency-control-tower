import { Skeleton } from "@/components/ui/skeleton";

// Route-Ladezustand (/cases/[id]): waehrend GET /cases/{id}. Form des Kopfes +
// Eingaben-/Bewertungsbloecke der Fall-Detailseite.
export default function Loading() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Fall-Detail</p>
      <Skeleton className="mt-3 h-8 w-80 max-w-full" />
      <Skeleton className="mt-2 h-4 w-52" />

      <Skeleton className="mt-6 h-16 w-full rounded-xl" />
      <Skeleton className="mt-8 h-48 w-full rounded-xl" />
      <Skeleton className="mt-10 h-64 w-full rounded-2xl" />
    </main>
  );
}
