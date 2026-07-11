import { checkAuth, getStats } from "@/app/actions"
import { Landing } from "@/components/landing"
import type { StatsResponse } from "@/types/api"

// Startseite (V4-P7): public. KPI-Leiste aus GET /stats, Navigations-Karten,
// Admin-Karten nur fuer Angemeldete. Immer frisch -- die Kennzahlen sollen nach
// neuen Einreichungen/Status-Wechseln aktuell sein.
export const dynamic = "force-dynamic"

export default async function Page() {
  const authenticated = await checkAuth()

  // Fehlschlag (Backend nicht erreichbar) darf die Startseite nicht sprengen --
  // die KPI-Leiste zeigt dann Platzhalter statt Zahlen.
  let stats: StatsResponse | null = null
  try {
    stats = await getStats()
  } catch {
    stats = null
  }

  return <Landing stats={stats} authenticated={authenticated} />
}
