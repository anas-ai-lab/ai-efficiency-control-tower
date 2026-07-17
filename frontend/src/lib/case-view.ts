import type {
  CaseDetailResponse,
  CaseDetailView,
  CaseSummary,
  CaseSummaryView,
} from "@/types/api"

// Schema-Split public/admin (V4.1-S8): GET /cases und GET /cases/{id} liefern je
// nach Aufrufer ein anderes Schema -- fuer Nicht-Admins ohne die
// Bewertungsfelder (siehe adapters/api/routes/cases.py). Diese Guards sind die
// EINZIGE Stelle, an der das Frontend von der schmalen auf die volle Sicht
// schliesst: sie pruefen die Anwesenheit eines Bewertungsfeldes, statt aus dem
// Login-Zustand zu raten. Die Antwort entscheidet, nicht die Erwartung.

export function isAdminSummary(c: CaseSummaryView): c is CaseSummary {
  return "zone" in c
}

export function isAdminDetail(d: CaseDetailView): d is CaseDetailResponse {
  return "triage" in d
}

// Fuer die reinen Admin-Seiten (Board, Monitoring): sie sind per checkAuth
// gegated und rechnen mit der vollen Sicht. Kommt trotzdem die schmale an
// (Session abgelaufen, Cookie nicht durchgereicht), ist das ein Fehler und kein
// Grund, eine halbe Matrix zu zeichnen -- fail loud statt stiller Leeransicht.
export function adminSummaries(cases: CaseSummaryView[]): CaseSummary[] {
  const admin = cases.filter(isAdminSummary)
  if (admin.length !== cases.length) {
    throw new Error(
      "Ideenliste ohne Bewertungsfelder erhalten -- Admin-Sicht erwartet. " +
        "Vermutlich ist die Session abgelaufen.",
    )
  }
  return admin
}
