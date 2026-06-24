"use server";

import type {
  ComplianceHintsResponse,
  ReportResponse,
  SharpenedCaseResponse,
  SolutionProposalResponse,
  TriageResponse,
  UseCaseInput,
} from "@/types/api";

const BASE_URL = process.env.AECT_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = process.env.AECT_API_KEY ?? "";

function buildHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // JSON-Parsing gescheitert, HTTP-Status reicht als Fehlermeldung
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function submitTriage(
  input: UseCaseInput,
): Promise<TriageResponse> {
  const res = await fetch(`${BASE_URL}/triage`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(input),
  });
  return handleResponse<TriageResponse>(res);
}

export async function sharpenCase(
  caseId: string,
): Promise<SharpenedCaseResponse> {
  const res = await fetch(`${BASE_URL}/cases/${caseId}/sharpen`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse<SharpenedCaseResponse>(res);
}

export async function proposeSolution(
  caseId: string,
): Promise<SolutionProposalResponse> {
  const res = await fetch(`${BASE_URL}/cases/${caseId}/propose-solution`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse<SolutionProposalResponse>(res);
}

export async function generateComplianceHints(
  caseId: string,
): Promise<ComplianceHintsResponse> {
  const res = await fetch(`${BASE_URL}/cases/${caseId}/compliance-hints`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse<ComplianceHintsResponse>(res);
}

export async function generateReport(
  caseId: string,
): Promise<ReportResponse> {
  const res = await fetch(`${BASE_URL}/cases/${caseId}/report`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({}),
  });
  return handleResponse<ReportResponse>(res);
}
