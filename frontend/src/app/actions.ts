"use server";

import type {
  CaseStatus,
  CaseSummary,
  ComplianceHintsResponse,
  DecisionResponse,
  MonitoringEntry,
  ReportResponse,
  SharpenedCaseResponse,
  SolutionProposalResponse,
  StatusUpdateResponse,
  TriageResponse,
  UseCaseInput,
} from "@/types/api";

const BASE_URL = process.env.AECT_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = process.env.AECT_API_KEY ?? "";

// Request-Timeouts (F-014): ohne AbortSignal wartet ein Server-Action-Fetch
// unbegrenzt. Regelbasierte Endpunkte (Triage, Report) antworten in
// Millisekunden; LLM-Endpunkte sind durch die Backend-Gesamtdeadline von
// 60 s pro LLM-Call gedeckelt (ResilientLLMAdapter) — das Frontend wartet
// etwas länger, damit im Fehlerfall die präzisere Server-Antwort gewinnt.
// propose-solution kann im Function-Calling-Loop zwei LLM-Calls machen.
const RULE_TIMEOUT_MS = 15_000;
const LLM_TIMEOUT_MS = 75_000;
const LLM_TOOL_LOOP_TIMEOUT_MS = 135_000;

// F-025: Das Backend liefert englische detail-Strings (API-Vertrag bleibt
// Englisch), die UI zeigt e.message direkt an. Bekannte Details werden hier
// auf Deutsch gemappt; alles Unbekannte fällt auf eine deutsche
// Status-Meldung zurück — kein rohes Englisch in der deutschen Oberfläche.
const ERROR_MESSAGES_DE: Record<string, string> = {
  "Case not found":
    "Der Fall wurde nicht gefunden. Bitte die Triage erneut starten.",
  "Invalid or missing API key":
    "Authentifizierung fehlgeschlagen — API-Key in frontend/.env.local prüfen.",
  "API key not configured on server":
    "Server-Konfiguration unvollständig: Auf dem Backend ist kein API-Key hinterlegt.",
  "Request with this Idempotency-Key is already in progress":
    "Diese Einreichung wird bereits verarbeitet. Einen Moment warten und erneut versuchen.",
  "Token budget exceeded for this API key":
    "Stundenbudget für Sprachmodell-Anfragen ist erreicht. Bitte kurz warten und erneut versuchen.",
  "Internal error": "Interner Serverfehler. Bitte später erneut versuchen.",
};

function statusMessageDE(status: number): string {
  if (status === 401 || status === 403) {
    return "Zugriff verweigert — Authentifizierung prüfen.";
  }
  if (status === 404) {
    return "Die angeforderte Ressource wurde nicht gefunden.";
  }
  if (status === 409) {
    return "Konflikt: Die Anfrage kollidiert mit einer laufenden Verarbeitung.";
  }
  if (status === 422) {
    return "Die Eingabe ist ungültig oder unvollständig.";
  }
  if (status === 429) {
    return "Zu viele Anfragen — bitte kurz warten und erneut versuchen.";
  }
  if (status >= 500) {
    return "Serverfehler. Bitte später erneut versuchen.";
  }
  return `Anfrage fehlgeschlagen (HTTP ${status}).`;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body.detail;
    } catch {
      // JSON-Parsing gescheitert, HTTP-Status reicht als Fehlermeldung
    }
    const mapped = detail ? ERROR_MESSAGES_DE[detail] : undefined;
    throw new Error(mapped ?? statusMessageDE(res.status));
  }
  return res.json() as Promise<T>;
}

async function apiFetch<T>(
  path: string,
  timeoutMs: number,
  body?: string,
  method: "GET" | "POST" = "POST",
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
      },
      body,
      // cache: "no-store" -- Lese-Actions (listCases/listMonitoringEntries)
      // duerfen nie aus dem Next.js Data Cache bedient werden: nach einem
      // Statuswechsel + router.refresh muss die Liste sofort den neuen Stand
      // zeigen. Schreib-Actions (POST) sind ohnehin nie cachebar; das Flag
      // hier schadet ihnen nicht und macht die Absicht explizit.
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (e) {
    // AbortSignal.timeout wirft DOMException name="TimeoutError" (F-014);
    // alles andere ist ein Verbindungsfehler (Backend nicht erreichbar).
    if (e instanceof Error && e.name === "TimeoutError") {
      throw new Error(
        "Zeitüberschreitung: Der Server hat nicht rechtzeitig geantwortet. Bitte erneut versuchen.",
      );
    }
    throw new Error(
      "Verbindung zum Backend fehlgeschlagen. Läuft der API-Server (uvicorn, Port 8000)?",
    );
  }
  return handleResponse<T>(res);
}

export async function submitTriage(
  input: UseCaseInput,
): Promise<TriageResponse> {
  return apiFetch<TriageResponse>(
    "/triage",
    RULE_TIMEOUT_MS,
    JSON.stringify(input),
  );
}

export async function sharpenCase(
  caseId: string,
): Promise<SharpenedCaseResponse> {
  return apiFetch<SharpenedCaseResponse>(
    `/cases/${caseId}/sharpen`,
    LLM_TIMEOUT_MS,
  );
}

export async function proposeSolution(
  caseId: string,
): Promise<SolutionProposalResponse> {
  return apiFetch<SolutionProposalResponse>(
    `/cases/${caseId}/propose-solution`,
    LLM_TOOL_LOOP_TIMEOUT_MS,
  );
}

export async function generateComplianceHints(
  caseId: string,
): Promise<ComplianceHintsResponse> {
  return apiFetch<ComplianceHintsResponse>(
    `/cases/${caseId}/compliance-hints`,
    LLM_TIMEOUT_MS,
  );
}

export async function generateReport(caseId: string): Promise<ReportResponse> {
  return apiFetch<ReportResponse>(
    `/cases/${caseId}/report`,
    RULE_TIMEOUT_MS,
    JSON.stringify({}),
  );
}

export async function recordDecision(
  caseId: string,
  decision: "approved" | "rejected",
  note: string | null,
): Promise<DecisionResponse> {
  return apiFetch<DecisionResponse>(
    `/cases/${caseId}/decision`,
    RULE_TIMEOUT_MS,
    JSON.stringify({ decision, note }),
  );
}

// ---- Portfolio / Lifecycle / Monitoring (v3, regelbasiert) -----------------
// Alle vier sind regelbasiert (kein LLM-Call) -> RULE_TIMEOUT_MS. Fehler laufen
// durch dasselbe apiFetch/handleResponse-Muster und werden ueber
// ERROR_MESSAGES_DE bzw. statusMessageDE auf Deutsch gemappt (z. B. "Case not
// found" -> deutscher Text, 422 -> "Die Eingabe ist ungueltig...").

export async function listCases(): Promise<CaseSummary[]> {
  // GET ohne Body. cache: "no-store" (apiFetch) haelt die Liste nach einem
  // Statuswechsel + router.refresh sofort aktuell.
  return apiFetch<CaseSummary[]>("/cases", RULE_TIMEOUT_MS, undefined, "GET");
}

export async function updateCaseStatus(
  caseId: string,
  status: CaseStatus,
): Promise<StatusUpdateResponse> {
  return apiFetch<StatusUpdateResponse>(
    `/cases/${caseId}/status`,
    RULE_TIMEOUT_MS,
    JSON.stringify({ status }),
  );
}

export async function addMonitoringNote(
  caseId: string,
  note: string,
): Promise<MonitoringEntry> {
  return apiFetch<MonitoringEntry>(
    `/cases/${caseId}/monitoring`,
    RULE_TIMEOUT_MS,
    JSON.stringify({ note }),
  );
}

export async function listMonitoringEntries(
  caseId: string,
): Promise<MonitoringEntry[]> {
  // GET ohne Body -- chronologisch aufsteigende Zeitleiste, ungecacht.
  return apiFetch<MonitoringEntry[]>(
    `/cases/${caseId}/monitoring`,
    RULE_TIMEOUT_MS,
    undefined,
    "GET",
  );
}
