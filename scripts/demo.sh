#!/usr/bin/env bash
# scripts/demo.sh -- AECT End-to-End Demo (Rule Engine + LLM + RAG)
#
# Voraussetzung:
#   Terminal 1: uv run uvicorn aect.adapters.api.app:app --reload
#   Terminal 2: docker compose up -d  (fuer ChromaDB + RAG)
#   Env:        export AECT_API_KEY=<dein-key>  (aus .env)
#
# Mock-Modus (ohne Azure + Chroma): Rule Engine + Triage laufen vollstaendig.
# LLM-Schritte (sharpen, propose-solution, compliance-hints) liefern Platzhalter.
set -euo pipefail

BASE_URL="${AECT_BASE_URL:-http://localhost:8000}"
API_KEY="${AECT_API_KEY:?Bitte AECT_API_KEY exportieren}"
PAYLOAD_FILE="${1:-scripts/demo_payload.json}"

h() { printf "\n\033[1;34m=== %s ===\033[0m\n" "$*"; }
ok() { printf "\033[0;32m[OK]\033[0m %s\n" "$*"; }
err() { printf "\033[0;31m[ERR]\033[0m %s\n" "$*" >&2; exit 1; }

h "1. Health Check -- Backend erreichbar?"
curl -fs "$BASE_URL/health" -H "X-API-Key: $API_KEY" | python3 -m json.tool \
  || err "Backend nicht erreichbar. uvicorn gestartet?"
echo ""

h "2. POST /triage -- Intake einreichen"
[ -f "$PAYLOAD_FILE" ] || err "Payload-Datei nicht gefunden: $PAYLOAD_FILE"
TRIAGE=$(curl -fs -X POST "$BASE_URL/triage" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary "@$PAYLOAD_FILE")
echo "$TRIAGE" | python3 -m json.tool
CASE_ID=$(echo "$TRIAGE" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
[ -n "$CASE_ID" ] || err "Kein id in Response. Payload korrekt? (GET $BASE_URL/docs)"
ok "Case ID: $CASE_ID"

h "3. POST /cases/$CASE_ID/sharpen -- Use-Case-Schaerfung"
curl -fs -X POST "$BASE_URL/cases/$CASE_ID/sharpen" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool

h "4. POST /cases/$CASE_ID/propose-solution -- Stack-Loesungsvorschlag"
curl -fs -X POST "$BASE_URL/cases/$CASE_ID/propose-solution" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool

h "5. POST /cases/$CASE_ID/compliance-hints -- RAG-Compliance-Hinweise"
curl -fs -X POST "$BASE_URL/cases/$CASE_ID/compliance-hints" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool

h "6. POST /cases/$CASE_ID/report -- Zweischichtiger Report"
curl -fs -X POST "$BASE_URL/cases/$CASE_ID/report" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool

h "Demo abgeschlossen"
echo "  OpenAPI-Doku:  $BASE_URL/docs"
echo "  Frontend-UI:   http://localhost:3000  (npm run dev in frontend/)"
echo "  Case-ID:       $CASE_ID"
