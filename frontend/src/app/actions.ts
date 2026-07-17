"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { getLocale, getTranslations } from "next-intl/server";

import type {
  ArchitectureSketchEnvelope,
  ArchitectureSketchResponse,
  CaseDetailView,
  CaseStatus,
  CaseSummaryView,
  ComplianceHintsResponse,
  DecisionResponse,
  DiscontinuedResponse,
  IdeationResponse,
  ImplementationApproach,
  MonitoringEntry,
  ReportResponse,
  SharpenedCaseResponse,
  SharpeningActionResponse,
  SimilarityPairsResponse,
  SolutionActionResponse,
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

// Bekannte englische Backend-Details (generische Vertrags-Fehler wie
// "Case not found", die im API-Vertrag englisch bleiben) -> stabiler
// apiErrors-Katalogschluessel (V4.1-S6, sprachabhaengig). Aktionsspezifische
// Details (z. B. "Kein offener Loesungs-Entwurf ...") liefert das Backend bereits
// in der angeforderten Sprache (lang) und erklaerend -- sie werden direkt
// gerendert. Nicht-String/fehlende Details fallen auf eine Status-Meldung zurueck.
const ERROR_KEY_BY_DETAIL: Record<string, string> = {
  "Case not found": "caseNotFound",
  "Invalid or missing admin credentials": "notLoggedIn",
  "Invalid or missing API key": "notLoggedIn",
  "Admin auth not configured on server": "adminNotConfigured",
  "API key not configured on server": "adminNotConfigured",
  "Request with this Idempotency-Key is already in progress": "alreadyProcessing",
  "Token budget exceeded for this API key": "tokenBudget",
  "Internal error": "internalError",
};

// ApiError traegt den HTTP-Status, damit Aufrufer, die zwischen Status-Codes
// unterscheiden muessen (Architektur-Skizze: 409 = kein Loesungsvorschlag,
// 5xx = KI-Dienst nicht erreichbar), das serverseitig tun koennen.
class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Schmaler Aufruf-Typ fuer den apiErrors-Translator (key + optionale Werte) --
// vermeidet die strikten next-intl-Key-Generics in den Fehler-Helfern.
type ApiErrorT = (
  key: string,
  values?: Record<string, string | number>,
) => string;

function statusMessageKey(status: number): string {
  if (status === 401 || status === 403) return "status401";
  if (status === 404) return "status404";
  if (status === 409) return "status409";
  if (status === 422) return "status422";
  if (status === 429) return "status429";
  if (status >= 500) return "status5xx";
  return "statusDefault";
}

// Leitet die anzuzeigende (sprachabhaengige) Fehlermeldung aus dem Backend-detail
// ab. String-Details: bekannte englische Vertrags-Fehler auf den Katalog mappen,
// alles andere (bereits lokalisierte, aktionsspezifische Backend-Texte) direkt
// uebernehmen. Strukturierte Guard-Details ({reason, message, violations}) tragen
// die (lokalisierte) Begruendung im message-Feld. Nicht-String/fehlend -> Status.
function messageFromDetail(
  detail: unknown,
  status: number,
  t: ApiErrorT,
): string {
  if (typeof detail === "string" && detail.length > 0) {
    const key = ERROR_KEY_BY_DETAIL[detail];
    return key ? t(key) : detail;
  }
  if (
    detail !== null &&
    typeof detail === "object" &&
    "message" in detail &&
    typeof (detail as { message: unknown }).message === "string"
  ) {
    return (detail as { message: string }).message;
  }
  return t(statusMessageKey(status), { status });
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const t = (await getTranslations("apiErrors")) as unknown as ApiErrorT;
    let detail: unknown;
    try {
      const body = (await res.json()) as { detail?: unknown };
      detail = body.detail;
    } catch {
      // JSON-Parsing gescheitert, HTTP-Status reicht als Fehlermeldung
    }
    throw new ApiError(res.status, messageFromDetail(detail, res.status, t));
  }
  return res.json() as Promise<T>;
}

// Haengt die aktive UI-Sprache als lang-Query an (V4.1-S6). Das Backend liefert
// generierte Klartexte (Score-Erklaerungen, Report, darstellbare Fehler) in
// dieser Sprache; Endpoints ohne lang-Parameter ignorieren die Query. Der Wert
// kommt aus dem NEXT_LOCALE-Cookie (next-intl getLocale), nie vom Client-Bundle.
async function withLang(path: string): Promise<string> {
  const locale = await getLocale();
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}lang=${locale}`;
}

async function apiFetch<T>(
  path: string,
  timeoutMs: number,
  body?: string,
  method: "GET" | "POST" = "POST",
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${await withLang(path)}`, {
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
    const t = await getTranslations("apiErrors");
    if (e instanceof Error && e.name === "TimeoutError") {
      throw new Error(t("timeout"));
    }
    throw new Error(t("connectionFailed"));
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

// Nach einer mutierenden Case-Aktion den Case-Detail-Pfad (und die Ideenliste,
// deren Zellen sich mitaendern) revalidieren. Ohne das greift router.refresh()
// im Prod-Build NICHT durch: die Server-Komponente rendert /cases/[id] aus dem
// Full-Route-/Router-Cache statt aus frischen Backend-Daten -- der stale
// Pending-Box-Befund nach dem Ansatz-Nachtrag (200 vom Backend, UI blieb
// pending). revalidatePath invalidiert den Cache-Eintrag serverseitig, sodass
// der anschliessende refresh/Navigation den neuen Stand zieht.
function revalidateCase(caseId: string): void {
  revalidatePath(`/cases/${caseId}`);
  revalidatePath("/cases");
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
  const res = await apiFetch<SharpeningActionResponse>(
    `/cases/${caseId}/sharpen/accept`,
    RULE_TIMEOUT_MS,
  );
  revalidateCase(caseId);
  return res;
}

export async function rejectSharpening(
  caseId: string,
): Promise<SharpeningActionResponse> {
  return apiFetch<SharpeningActionResponse>(
    `/cases/${caseId}/sharpen/reject`,
    RULE_TIMEOUT_MS,
  );
}

// S4 Draft/Accept: propose liefert nur einen Vorschlags-Entwurf (persistiert
// als solution_draft, ueberschreibt nichts am Case). Kein revalidateCase --
// erst acceptSolution traegt beide Varianten in den Case.
export async function proposeSolution(
  caseId: string,
): Promise<SolutionProposalResponse> {
  return apiFetch<SolutionProposalResponse>(
    `/cases/${caseId}/propose-solution`,
    LLM_TOOL_LOOP_TIMEOUT_MS,
  );
}

// Uebernimmt bzw. verwirft den offenen Loesungs-Draft (S4, Muster wie
// acceptSharpening). Kein LLM-Call -> RULE_TIMEOUT_MS. 409 (kein offener Draft)
// laeuft durch statusMessageDE.
export async function acceptSolution(
  caseId: string,
): Promise<SolutionActionResponse> {
  const res = await apiFetch<SolutionActionResponse>(
    `/cases/${caseId}/propose-solution/accept`,
    RULE_TIMEOUT_MS,
  );
  revalidateCase(caseId);
  return res;
}

export async function rejectSolution(
  caseId: string,
): Promise<SolutionActionResponse> {
  return apiFetch<SolutionActionResponse>(
    `/cases/${caseId}/propose-solution/reject`,
    RULE_TIMEOUT_MS,
  );
}

export async function generateComplianceHints(
  caseId: string,
): Promise<ComplianceHintsResponse> {
  const res = await apiFetch<ComplianceHintsResponse>(
    `/cases/${caseId}/compliance-hints`,
    LLM_TIMEOUT_MS,
  );
  revalidateCase(caseId);
  return res;
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
  const res = await apiFetch<DecisionResponse>(
    `/cases/${caseId}/decision`,
    RULE_TIMEOUT_MS,
    JSON.stringify({ decision, note }),
  );
  revalidateCase(caseId);
  return res;
}

// ---- Portfolio / Lifecycle / Monitoring (v3, regelbasiert) -----------------
// Alle vier sind regelbasiert (kein LLM-Call) -> RULE_TIMEOUT_MS. Fehler laufen
// durch dasselbe apiFetch/handleResponse-Muster und werden ueber
// ERROR_MESSAGES_DE bzw. statusMessageDE auf Deutsch gemappt (z. B. "Case not
// found" -> deutscher Text, 422 -> "Die Eingabe ist ungueltig...").

export async function listCases(): Promise<CaseSummaryView[]> {
  // GET ohne Body. cache: "no-store" (apiFetch) haelt die Liste nach einem
  // Statuswechsel + router.refresh sofort aktuell.
  // Schema-Split (V4.1-S8): mit Session-Cookie kommt CaseSummary (inkl.
  // Bewertung), ohne PublicCaseSummary (Grunddaten + Status). Welche der beiden
  // vorliegt, klaeren die Guards in lib/case-view -- nicht diese Action.
  return apiFetch<CaseSummaryView[]>("/cases", RULE_TIMEOUT_MS, undefined, "GET");
}

// GET /stats (public, V4-P7): aggregierte Portfolio-Kennzahlen fuer die
// Startseite. Regelbasiert (ein list_all-Durchlauf) -> RULE_TIMEOUT_MS.
export async function getStats(): Promise<StatsResponse> {
  return apiFetch<StatsResponse>("/stats", RULE_TIMEOUT_MS, undefined, "GET");
}

// GET /cases/{id} (public, E9/SDR-0003): read-only Sicht auf einen Case.
// Schema-Split (V4.1-S8): mit Session-Cookie CaseDetailResponse (inkl. triage +
// report), ohne PublicCaseDetailResponse (Grunddaten, Status, Board-
// Entscheidung). 404 -> null, damit die Detailseite eine NotFound-Ansicht zeigt
// statt zu werfen; andere Fehler propagieren.
export async function getCaseDetail(
  caseId: string,
): Promise<CaseDetailView | null> {
  try {
    return await apiFetch<CaseDetailView>(
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
  const res = await apiFetch<StatusUpdateResponse>(
    `/cases/${caseId}/status`,
    RULE_TIMEOUT_MS,
    JSON.stringify({ status }),
  );
  revalidateCase(caseId);
  return res;
}

// discontinued-Flag (Monitoring, V4.1-S7): reines Zusatzflag "wird nicht mehr
// aktiv beobachtet", unabhaengig vom CaseStatus-Lifecycle. Kein Request-Body
// (analog sharpen/accept) -- der Endpoint-Name traegt die Bedeutung.
export async function discontinueCase(
  caseId: string,
): Promise<DiscontinuedResponse> {
  const res = await apiFetch<DiscontinuedResponse>(
    `/cases/${caseId}/discontinue`,
    RULE_TIMEOUT_MS,
  );
  revalidateCase(caseId);
  return res;
}

export async function reinstateCase(
  caseId: string,
): Promise<DiscontinuedResponse> {
  const res = await apiFetch<DiscontinuedResponse>(
    `/cases/${caseId}/reinstate`,
    RULE_TIMEOUT_MS,
  );
  revalidateCase(caseId);
  return res;
}

// Traegt den Implementierungsansatz eines Vor-Bewertungs-Case nach und loest
// die vollstaendige Neubewertung aus (V4.1, ADR-0050). Admin-only (Session);
// die Response ist das neu berechnete Triage-Ergebnis.
export async function setImplementationApproach(
  caseId: string,
  approach: ImplementationApproach,
): Promise<TriageResponse> {
  const res = await apiFetch<TriageResponse>(
    `/cases/${caseId}/implementation-approach`,
    RULE_TIMEOUT_MS,
    JSON.stringify({ implementation_approach: approach }),
  );
  revalidateCase(caseId);
  return res;
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
    const t = await getTranslations("apiErrors");
    return {
      kind: "unavailable",
      message: e instanceof Error ? e.message : t("aiUnavailable"),
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
  const t = (await getTranslations("apiErrors")) as unknown as ApiErrorT;
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
    return { ok: false, error: t("connectionFailed") };
  }
  if (!res.ok) {
    if (res.status === 401) return { ok: false, error: t("wrongPassword") };
    if (res.status === 503) {
      return { ok: false, error: t("loginNotConfigured") };
    }
    if (res.status === 429) {
      return { ok: false, error: t("tooManyLogins") };
    }
    return { ok: false, error: t(statusMessageKey(res.status), { status: res.status }) };
  }
  const token = extractSessionToken(res);
  if (token === null) {
    return { ok: false, error: t("noSessionToken") };
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
