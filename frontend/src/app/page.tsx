import AectApp from "@/components/aect-app"
import { checkAuth } from "@/app/actions"

// Einreichung + Triage-Ergebnis sind public. Die anschliessenden Admin-Aktionen
// (Schaerfen etc.) blendet AectApp anhand des Auth-Zustands aus.
export const dynamic = "force-dynamic"

export default async function Page() {
  const authenticated = await checkAuth()
  return <AectApp authenticated={authenticated} />
}
