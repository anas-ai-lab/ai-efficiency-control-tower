import { Skeleton } from "@/components/ui/skeleton";

// Route-Ladezustand (/board): waehrend GET /cases fuer die Portfolio-Matrix.
export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-12 sm:px-6">
      <p className="eyebrow">Board</p>
      <Skeleton className="mt-3 h-8 w-96 max-w-full" />
      <Skeleton className="mt-3 h-4 w-full max-w-prose" />

      <div className="mt-8">
        <Skeleton className="mb-5 h-8 w-40" />
        <div className="grid gap-6 lg:grid-cols-[1fr_18rem]">
          <Skeleton className="h-[440px] w-full rounded-xl sm:h-[520px]" />
          <Skeleton className="hidden h-72 w-full rounded-xl lg:block" />
        </div>
      </div>
    </main>
  );
}
