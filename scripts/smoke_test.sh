#!/usr/bin/env bash
# Smoke test for the running Sèvo runtime API.
#   ./scripts/smoke_test.sh [BASE_URL]   (default http://localhost:8000)
# Teaches a CP node through the API, checks the GENUINE verdict, then proves the
# brain state survives a save → reload on the mounted volume.
set -euo pipefail
BASE="${1:-http://localhost:8000}"
NODE="fr.CP.lecture_mots_reguliers"
json='content-type: application/json'

echo "health:        $(curl -fsS "$BASE/health")"
for _ in $(seq 1 6); do
  curl -fsS -X POST "$BASE/replay" -H "$json" -d "{\"node_id\":\"$NODE\"}" >/dev/null
done
curl -fsS -X POST "$BASE/consolidate" -H "$json" -d '{"mode":"sleep","advance_days":1}' >/dev/null

echo "evaluate:      $(curl -fsS -X POST "$BASE/evaluate" -H "$json" -d "{\"node_id\":\"$NODE\"}")"
echo "audit:         $(curl -fsS -X POST "$BASE/audit" -H "$json" -d "{\"node_id\":\"$NODE\"}")"
echo "metrics:       $(curl -fsS "$BASE/metrics")"
verdict=$(curl -fsS "$BASE/diff" | python3 -c "import sys,json;print(json.load(sys.stdin)['genuine_learning']['verdict'])")
echo "diff verdict:  $verdict"

echo "save:          $(curl -fsS -X POST "$BASE/save" -H "$json" -d '{"path":"/data/brain.json"}')"
echo "load:          $(curl -fsS -X POST "$BASE/load" -H "$json" -d '{"path":"/data/brain.json"}')"
echo "reload eval:   $(curl -fsS -X POST "$BASE/evaluate" -H "$json" -d "{\"node_id\":\"$NODE\"}")"

[ "$verdict" = "GENUINE" ] && echo "SMOKE TEST: PASS" || { echo "SMOKE TEST: FAIL (verdict=$verdict)"; exit 1; }
