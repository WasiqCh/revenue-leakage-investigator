#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Frontend smoke test — proves pages actually render content, without a browser.
#
# Plain-English: a screen can "build" successfully and still show an empty page.
# This checks each page returns HTTP 200 AND contains a label that should be
# there. That catches the empty-render failure that AI-generated UI hits often.
#
# Usage:  bash scripts/smoke_routes.sh [base-url]
#         BASE defaults to http://localhost:3000
# Called by `make verify`. Exits non-zero on any failure.
# ---------------------------------------------------------------------------
set -uo pipefail

BASE="${1:-${BASE_URL:-http://localhost:3000}}"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/artifacts"
mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/route-smoke.txt"

# route | label that must appear in the rendered HTML
ROUTES=(
  "/|Potential leakage"
  "/cases|Confidence"
  "/analytics|Leakage"
  "/ledger|Recovered"
  "/simulator|Time to detect"
)

pass=0
fail=0
: > "$REPORT"

echo "Frontend route smoke test against $BASE" | tee -a "$REPORT"
echo "--------------------------------------------" | tee -a "$REPORT"

for entry in "${ROUTES[@]}"; do
  route="${entry%%|*}"
  label="${entry##*|}"

  body="$(mktemp)"
  code="$(curl -s -o "$body" -w '%{http_code}' --max-time 20 "$BASE$route" || echo 000)"

  if [ "$code" != "200" ]; then
    echo "FAIL  $route  (HTTP $code)" | tee -a "$REPORT"
    fail=$((fail + 1))
  elif ! grep -qF "$label" "$body"; then
    echo "FAIL  $route  (HTTP 200 but missing label: $label)" | tee -a "$REPORT"
    fail=$((fail + 1))
  else
    echo "ok    $route  (HTTP 200, found: $label)" | tee -a "$REPORT"
    pass=$((pass + 1))
  fi

  rm -f "$body"
done

echo "--------------------------------------------" | tee -a "$REPORT"
echo "passed: $pass   failed: $fail" | tee -a "$REPORT"

[ "$fail" -eq 0 ]
