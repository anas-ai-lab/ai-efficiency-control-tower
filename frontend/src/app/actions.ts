"use server";

import { cookies } from "next/headers";

import type {
  ArchitectureSketchEnvelope,
  ArchitectureSketchResponse,
  CaseDetailResponse,
  CaseStatus,
  CaseSummary,
  ComplianceHintsResponse,
  DecisionResponse,
  IdeationResponse,
  MonitoringEntry,
  ReportResponse,
  SharpenedCaseResponse,
  SharpeningActionResponse,
  SimilarityPairsResponse,
  SolutionProposalResponse,
  StatsResponse,
  StatusUpdateResponse,
  TriageResponse,
  UseCaseInput,
} from "@/types/api";

const BASE_URL = process.env.AECT_API_BASE_URL ?? "http://localhost:8000";

// V4-P-Auth: der Browser authentifiziert sich ausschliesslich ueber das
// Admin-Session-Cookie (aect_session), NICHT mehr ueber einen serverseitig
// injizierten X-API-Key. Anonyme Flows (Einreichung, Ideen-Assistent,
// Ideenliste, Case-Detail-Kopf) laufen ganz ohne Auth; alle mutierenden/
// sensiblen Admin-Routen verlangen ein gueltiges Session-Cookie. Der frueher
// server-seitig verwendete AECT_API_KEY wird bewusst NICHT mehr mitgeschickt --
// sonst waere jeder anonyme Aufruf automatisch Admin (Zwei-Stufen-Modell kaputt).
const SESSION_COOKIE = "aect_session";
// Muss zur Backend-Session-Laufzeit passen (SESSION_TTL_HOURS = 12 h).
const SESSION_MAX_AGE_S = 12 * 3600;

/**
 * Leitet das Session-Cookie des Browsers als Cookie-Header an das Backend
 * weiter. Ohne Cookie (anonym) wird kein Header gesetzt -- Public-Routen
 * funktionieren trotzdem, Admin-Routen antworten dann 401.
 */
async function sessionHeaders(): Promise<Record<string, string>> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  return token ? { Cookie: `${SESSION_COOKIE}=${token}` } : {};
}

/** Liest den Session-Token aus dem Set-Cookie des Backends (Login-Antwort). */
function extractSessionToken(res: Response): string | null {
  const setCookies = res.headers.getSetCookie?.() ?? [];
  for (const raw of setCookies) {
    if (raw.startsWith(`${SESSION_COOKIE}=`)) {
      const first = raw.split(";", 1)[0];
      return first.slice(first.indexOf("=") + 1);
    }
  }
  return null;
}

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
  "Invalid or missing admin credentials":
    "Nicht angemeldet — bitte als Admin einloggen, um diese Aktion auszuführen.",
  "Invalid or missing API key":
    "Nicht angemeldet — bitte als Admin einloggen, um diese Aktion auszuführen.",
  "Admin auth not configured on server":
    "Server-Konfiguration unvollständig: Auf dem Backend ist kein Admin-Zugang hinterlegt.",
  "API key not configured on server":
    "Server-Konfiguration unvollständig: Auf dem Backend ist kein Admin-Zugang hinterlegt.",
  "Request with this Idempotency-Key is already in progress":
    "Diese Einreichung wird bereits verarbeitet. Einen Moment warten und erneut versuchen.",
  "Token budget exceeded for this API key":
    "Stundenbudget für Sprachmodell-Anfragen ist erreicht. Bitte kurz warten und erneut versuchen.",
  "Internal error": "Interner Serverfehler. Bitte später erneut versuchen.",
};

// ApiError traegt den HTTP-Status, damit Aufrufer, die zwischen Status-Codes
// unterscheiden muessen (Architektur-Skizze: 409 = kein Loesungsvorschlag,
// 5xx = KI-Dienst nicht erreichbar), das serverseitig tun koennen. Extends
// Error -> bestehende `e instanceof Error`-Pfade und e.message-Anzeigen bleiben
// unveraendert; der Status ist ein zusaetzliches Feld.
class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

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
    throw new ApiError(res.status, mapped ?? statusMessageDE(res.status));
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
        ...(await sessionHeaders()),
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

// Draft/Accept-Flow (V4): accept uebernimmt den offenen Schaerfungs-Entwurf in
// die regulaeren Felder, reject verwirft ihn. Kein LLM-Call (nur Persistenz) ->
// RULE_TIMEOUT_MS. 409 (kein offener Draft) laeuft durch statusMessageDE.
export async function acceptSharpening(
  caseId: string,
): Promise<SharpeningActionResponse> {
  return apiFetch<SharpeningActionResponse>(
    `/cases/${caseId}/sharpen/accept`,
    RULE_TIMEOUT_MS,
  );
}

export async function rejectSharpening(
  caseId: string,
): Promise<SharpeningActionResponse> {
  return apiFetch<SharpeningActionResponse>(
    `/cases/${caseId}/sharpen/reject`,
    RULE_TIMEOUT_MS,
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

// POST /ideation (P10/P14, ADR-0048): ephemere Use-Case-Entwuerfe aus einer
// Problembeschreibung. Ein einzelner LLM-Call (kein Function-Calling-Loop) ->
// dieselbe LLM_TIMEOUT_MS wie sharpen/compliance-hints. Fehler (503 KI nicht
// erreichbar, 502 unverwertbare Antwort, Timeout) laufen durch dasselbe
// apiFetch/handleResponse-Muster und werden auf Deutsch gemappt.
export async function generateIdeas(
  problemDescription: string,
): Promise<IdeationResponse> {
  return apiFetch<IdeationResponse>(
    "/ideation",
    LLM_TIMEOUT_MS,
    JSON.stringify({ problem_description: problemDescription }),
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

// GET /stats (public, V4-P7): aggregierte Portfolio-Kennzahlen fuer die
// Startseite. Regelbasiert (ein list_all-Durchlauf) -> RULE_TIMEOUT_MS.
export async function getStats(): Promise<StatsResponse> {
  return apiFetch<StatsResponse>("/stats", RULE_TIMEOUT_MS, undefined, "GET");
}

// GET /cases/{id} (public, E9/SDR-0003): vollstaendiger read-only
// Bewertungsstand (Triage + Report). 404 -> null, damit die Detailseite eine
// NotFound-Ansicht zeigt statt zu werfen; andere Fehler propagieren.
export async function getCaseDetail(
  caseId: string,
): Promise<CaseDetailResponse | null> {
  try {
    return await apiFetch<CaseDetailResponse>(
      `/cases/${caseId}`,
      RULE_TIMEOUT_MS,
      undefined,
      "GET",
    );
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export async function listSimilarityPairs(): Promise<SimilarityPairsResponse> {
  // GET ohne Body -- Dedup-View (P9). Regelbasiert (Cosinus auf vorhandenen
  // Embeddings), daher RULE_TIMEOUT_MS. cache: "no-store" (apiFetch) haelt die
  // Paare nach einem Reload konsistent mit der Liste. Fehler laufen durch
  // dasselbe apiFetch/handleResponse-Muster wie listCases -- die Aufrufer
  // (/cases, /cases/{id}) behandeln einen Fehlschlag als "keine Badges/kein
  // Panel", nicht als Blocker.
  return apiFetch<SimilarityPairsResponse>(
    "/cases/similarity-pairs",
    RULE_TIMEOUT_MS,
    undefined,
    "GET",
  );
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

// ---- Architektur-Skizze (/cases/{id}/architecture-sketch, P11/P13) ---------

export async function getArchitectureSketch(
  caseId: string,
): Promise<ArchitectureSketchResponse | null> {
  // GET: liest die persistierte Skizze. Regelbasierter DB-Read (kein LLM-Call)
  // -> RULE_TIMEOUT_MS. Liefert 200 {"sketch": null}, wenn der Case existiert,
  // aber nie eine Skizze erzeugt wurde -> hier zu null verengt.
  const env = await apiFetch<ArchitectureSketchEnvelope>(
    `/cases/${caseId}/architecture-sketch`,
    RULE_TIMEOUT_MS,
    undefined,
    "GET",
  );
  return env.sketch;
}

// Ergebnis von generateArchitectureSketch als DATEN (kein throw): Next.js
// redigiert aus Server Actions geworfene Fehler-Messages in Produktion, und der
// HTTP-Status ueberlebt die Server/Client-Grenze ohnehin nicht. Der Client
// leitet daraus die UI-Zustaende ab: no_proposal -> 409 (kein
// Loesungsvorschlag), unavailable -> 5xx/Timeout (Retry sinnvoll), error ->
// sonstiger Fehler mit deutscher Meldung.
export type SketchGenerateResult =
  | { kind: "ok"; sketch: ArchitectureSketchResponse }
  | { kind: "no_proposal" }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string };

export async function generateArchitectureSketch(
  caseId: string,
): Promise<SketchGenerateResult> {
  // POST: erzeugt/ueberschreibt die Skizze via LLM. Timeout: dieselbe
  // LLM_TIMEOUT_MS wie sharpenCase/generateComplianceHints (ein einzelner
  // LLM-Call, kein Function-Calling-Loop -> nicht LLM_TOOL_LOOP_TIMEOUT_MS).
  try {
    const sketch = await apiFetch<ArchitectureSketchResponse>(
      `/cases/${caseId}/architecture-sketch`,
      LLM_TIMEOUT_MS,
    );
    return { kind: "ok", sketch };
  } catch (e) {
    if (e instanceof ApiError) {
      // 409: Case hat keinen Loesungsvorschlag -- die Skizze braucht einen.
      if (e.status === 409) return { kind: "no_proposal" };
      // 5xx (502 unverwertbare KI-Antwort, 503 KI nicht erreichbar): Retry.
      if (e.status >= 500) return { kind: "unavailable", message: e.message };
      return { kind: "error", message: e.message };
    }
    // Timeout/Verbindungsfehler (apiFetch wirft hier ein einfaches Error):
    // wie "Dienst nicht erreichbar" behandeln -> Retry anbieten.
    return {
      kind: "unavailable",
      message:
        e instanceof Error
          ? e.message
          : "KI-Dienst derzeit nicht erreichbar — bitte später erneut versuchen.",
    };
  }
}

// ---- Admin-Auth (V4-P-Auth): Login/Logout/Status ueber das Session-Cookie ---
// Der Token verlaesst nie den Client-Bundle: Login laeuft server-seitig, das
// Cookie wird als httpOnly gesetzt und ist fuer Browser-JS unsichtbar.

/**
 * Meldet den Admin an. Bei Erfolg wird das vom Backend erzeugte Session-Token
 * als httpOnly-Cookie (aect_session) im Browser gesetzt.
 */
export async function login(
  password: string,
): Promise<{ ok: boolean; error?: string }> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
      cache: "no-store",
      signal: AbortSignal.timeout(RULE_TIMEOUT_MS),
    });
  } catch {
    return {
      ok: false,
      error:
        "Verbindung zum Backend fehlgeschlagen. Läuft der API-Server (Port 8000)?",
    };
  }
  if (!res.ok) {
    if (res.status === 401) return { ok: false, error: "Falsches Passwort." };
    if (res.status === 503) {
      return {
        ok: false,
        error: "Admin-Login ist auf dem Server nicht eingerichtet.",
      };
    }
    if (res.status === 429) {
      return {
        ok: false,
        error: "Zu viele Login-Versuche — bitte kurz warten und erneut versuchen.",
      };
    }
    return { ok: false, error: statusMessageDE(res.status) };
  }
  const token = extractSessionToken(res);
  if (token === null) {
    return { ok: false, error: "Login-Antwort ohne Session-Token." };
  }
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.AECT_SESSION_COOKIE_SECURE === "true",
    path: "/",
    maxAge: SESSION_MAX_AGE_S,
  });
  return { ok: true };
}

/** Meldet den Admin ab (Backend-Session loeschen + lokales Cookie entfernen). */
export async function logout(): Promise<void> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  try {
    await fetch(`${BASE_URL}/auth/logout`, {
      method: "POST",
      headers: token ? { Cookie: `${SESSION_COOKIE}=${token}` } : {},
      cache: "no-store",
      signal: AbortSignal.timeout(RULE_TIMEOUT_MS),
    });
  } catch {
    // Backend nicht erreichbar: das Cookie wird trotzdem lokal entfernt.
  }
  store.delete(SESSION_COOKIE);
}

/** Prueft, ob der aktuelle Aufrufer als Admin authentifiziert ist (GET /auth/me). */
export async function checkAuth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/auth/me`, {
      method: "GET",
      headers: await sessionHeaders(),
      cache: "no-store",
      signal: AbortSignal.timeout(RULE_TIMEOUT_MS),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { authenticated?: boolean };
    return data.authenticated === true;
  } catch {
    return false;
  }
}
