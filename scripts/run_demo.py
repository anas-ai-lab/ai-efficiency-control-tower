"""AECT Demo-Skript -- vollstaendiger Triage-Flow via HTTP (Phase F).

Zeigt: Einreichung -> Triage -> Schaerfung -> Loesung -> Compliance -> Report.

Starten (zwei Terminals):
  Terminal 1:
    AECT_API_KEY=aect-demo-key uv run uvicorn \
      aect.adapters.api.app:app --port 8080 --log-level warning

  Terminal 2 (nach "Application startup complete"):
    AECT_API_KEY=aect-demo-key uv run python scripts/run_demo.py

Mit echtem Azure-LLM: AECT_AZURE_OPENAI_* in .env setzen.
Mit ChromaDB:         AECT_CHROMA_HOST=127.0.0.1 in .env setzen +
                      docker compose up -d.

Ohne diese Env-Vars laufen LLM und Retrieval als Mock (kein Azure-Call).
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path

import httpx

from aect.application.eval.loader import load_eval_cases

REPO_ROOT = Path(__file__).parent.parent
BASE_URL = os.getenv("AECT_DEMO_URL", "http://localhost:8080")
API_KEY = os.getenv("AECT_API_KEY", "aect-demo-key")
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def _sep(label: str) -> None:
    width = 62
    print(f"\n{'=' * width}")
    print(f"  {label}")
    print(f"{'=' * width}")


def _check_server() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except httpx.ConnectError:
        return False


def _load_demo_case() -> dict[str, object]:
    """Laedt golden-002 (IT-Ticket-Kategorisierung) als Demo-Case.

    Verwendet load_eval_cases() statt hartkodierter Felder -- vermeidet
    Interface-Raterei (session-protocol v3 SS6 Punkt 1).
    """
    cases = load_eval_cases(REPO_ROOT / "evals" / "golden" / "use_cases.jsonl")
    demo = next(c for c in cases if c.case_id == "golden-002")
    return json.loads(demo.use_case.model_dump_json())


def main() -> None:
    if not _check_server():
        print(f"\n[FEHLER] Server nicht erreichbar unter {BASE_URL}")
        print("\nStarten mit:")
        print(
            f"  AECT_API_KEY={API_KEY} uv run uvicorn "
            "aect.adapters.api.app:app --port 8080 --log-level warning"
        )
        sys.exit(1)

    print("\nAECT -- AI Efficiency Control Tower")
    print("Demo-Flow: Einreichung -> Triage -> Schaerfung -> Report")

    demo_payload = _load_demo_case()
    _sep("SCHRITT 1: Use Case einreichen  POST /triage")
    print(f"  Titel: {demo_payload['title']}")

    r = httpx.post(f"{BASE_URL}/triage", headers=HEADERS, json=demo_payload, timeout=30)
    if r.status_code not in (200, 201):
        print(f"[FEHLER] {r.status_code}: {r.text}")
        sys.exit(1)

    triage = r.json()
    case_id = triage["id"]
    zone = triage.get("zone") or {}
    roi = triage.get("roi") or {}
    composite = triage.get("composite") or {}

    print(f"\n  Case-ID:         {case_id}")
    print(f"  Zone:            {zone.get('final_zone', 'n/a')}")
    print(
        f"  Vorfilter:       {'BESTANDEN' if triage['passed_vorfilter'] else 'NICHT BESTANDEN'}"
    )
    if roi:
        print(
            f"  Erw. Nutzen:     {roi.get('expected_benefit_eur', 0):>12,.0f} EUR/Jahr"
        )
        print(
            f"  Netto-Nutzen:    {roi.get('net_expected_benefit_eur', 0):>12,.0f} EUR/Jahr"
        )
    if composite:
        print(
            f"  Composite-Score: {composite.get('total', 'n/a')} "
            f"({composite.get('effort_label', '')})"
        )
    if zone.get("reason"):
        print(
            f"\n  {textwrap.fill(zone['reason'], width=58, initial_indent='  Begruendung: ', subsequent_indent='               ')}"
        )

    _sep("SCHRITT 2: Use Case schaerfen  POST /cases/{id}/sharpen")
    sharpened_text = None
    try:
        r = httpx.post(
            f"{BASE_URL}/cases/{case_id}/sharpen", headers=HEADERS, timeout=15
        )
    except httpx.ReadTimeout:
        print("  [Timeout -- kein Azure-LLM konfiguriert, Mock haengt. Weiter.]")
        r = None
    if r is not None and r.status_code == 200:
        sh = r.json()
        if sh.get("sharpened_title"):
            print(f"\n  Titel:    {sh['sharpened_title']}")
            if sh.get("improvement_suggestions"):
                print("\n  Verbesserungsvorschlaege:")
                for s in sh["improvement_suggestions"][:3]:
                    print(f"    - {textwrap.shorten(s, 72)}")
        elif sh.get("raw_text"):
            print(f"  [Mock] raw_text: {textwrap.shorten(sh['raw_text'], 80)}")
    else:
        print(f"  [Schaerfung: {r.status_code}]")

    _sep("SCHRITT 3: Loesungsvorschlag  POST /cases/{id}/propose-solution")
    proposal_text = None
    try:
        r = httpx.post(
            f"{BASE_URL}/cases/{case_id}/propose-solution", headers=HEADERS, timeout=15
        )
    except httpx.ReadTimeout:
        print("  [Timeout -- kein Azure-LLM konfiguriert. Weiter.]")
        r = None
    if r is not None and r.status_code == 200:
        prop = r.json()
        proposal_text = prop.get("proposal_text", "")
        print(f"\n  {textwrap.shorten(proposal_text, 200)}")
    else:
        print(f"  [Loesung: {r.status_code}]")

    _sep("SCHRITT 4: Compliance-Hinweise  POST /cases/{id}/compliance-hints")
    try:
        r = httpx.post(
            f"{BASE_URL}/cases/{case_id}/compliance-hints", headers=HEADERS, timeout=15
        )
    except httpx.ReadTimeout:
        print("  [Timeout -- kein Azure-LLM konfiguriert. Weiter.]")
        r = None
    if r is not None and r.status_code == 200:
        ch = r.json()
        if ch.get("hint_text"):
            print(f"\n  {textwrap.shorten(ch['hint_text'], 260)}")
            if ch.get("citations"):
                print("\n  Quellen:")
                for c in ch["citations"]:
                    url_part = f" -- {c['url']}" if c.get("url") else ""
                    print(f"    [{c['number']}] {c['citation']}{url_part}")
        else:
            print("  [Graceful Degradation: kein Retrieval-Treffer]")
    else:
        print(f"  [Compliance: {r.status_code}]")

    _sep("SCHRITT 5: Report  POST /cases/{id}/report")
    r = httpx.post(
        f"{BASE_URL}/cases/{case_id}/report",
        headers=HEADERS,
        json={},
        timeout=30,
    )
    if r.status_code == 200:
        rep = r.json()
        bs = rep.get("business_summary", {})
        td = rep.get("technical_detail", {})
        print("\n  BUSINESS SUMMARY")
        print(f"  Zone:            {bs.get('zone', 'n/a')}")
        print(f"  Handlungsfaehig: {bs.get('is_actionable', False)}")
        print(f"  Empfehlung:      {bs.get('recommendation', 'n/a')}")
        if bs.get("expected_benefit_eur") is not None:
            print(f"  Nutzen:          {bs['expected_benefit_eur']:>12,.0f} EUR/Jahr")
        if bs.get("summary_text"):
            print(
                f"\n  {textwrap.fill(bs['summary_text'], 58, initial_indent='  ', subsequent_indent='  ')}"
            )
        print("\n  TECHNICAL DETAIL")
        print(f"  Vorfilter:       {'OK' if td.get('passed_vorfilter') else 'FEHLT'}")
        print(
            f"  Composite:       {td.get('composite_total', 'n/a')} "
            f"({td.get('composite_effort_label', '')})"
        )
        if td.get("risk_flags"):
            print(f"  Risk-Flags:      {', '.join(td['risk_flags'])}")
    else:
        print(f"  [Report: {r.status_code}]")

    _sep("DEMO ABGESCHLOSSEN")
    print(f"  Case-ID:   {case_id}")
    print(f"  API-Docs:  {BASE_URL}/docs")
    print()


if __name__ == "__main__":
    main()
