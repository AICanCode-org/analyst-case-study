#!/usr/bin/env bash
# Smoke test a running FunnelLens dashboard.   scripts/smoke-test.sh [BASE_URL]   (default http://localhost:8501)
# EXPECT_FALLBACK=true  also requires the narrative to be the template fallback (AI provider unreachable).
set -euo pipefail
BASE=${1:-http://localhost:8501}
EXPECT_FALLBACK=${EXPECT_FALLBACK:-}
pass=0
fail=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

check() {  # check NAME COMMAND...
  local name=$1
  shift
  if "$@" >"$TMP/out" 2>&1; then
    pass=$((pass + 1))
    echo "ok   $name"
  else
    fail=$((fail + 1))
    echo "FAIL $name: $(head -c 300 "$TMP/out")"
  fi
}

status_is() {  # status_is CODE PATH
  local got
  got=$(curl -s -o "$TMP/body" -w '%{http_code}' "$BASE$2")
  [ "$got" = "$1" ] || { echo "HTTP $got for $2"; return 1; }
}

json_check() {  # json_check PATH PYTHON_EXPR (d = the parsed JSON)
  curl -sf "$BASE$1" -o "$TMP/json" || { echo "cannot fetch $1"; return 1; }
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert $2, d" "$TMP/json"
}

check "health" status_is 200 /_stcore/health
check "app page" status_is 200 /
check "app page is Streamlit" grep -qi "streamlit" "$TMP/body"
check "answers.json valid" json_check /app/static/answers.json \
  "d['schema'] == 'funnellens-answers' and d['decision']['recommendation'] in ('run_targeted_experiment', 'rebuild_checkout', 'no_checkout_gap_found')"
check "answers are aggregates only" json_check /app/static/answers.json \
  "not __import__('re').search(r'\"[SO]\\d{6}\"|\"(user|session|order)_id\":', json.dumps(d))"
check "narrative.json" json_check /app/static/narrative.json \
  "d['source'] in ('template', 'llm') and len(d['text']) > 100 and '[F' in d['text']"
if [ "$EXPECT_FALLBACK" = true ]; then
  check "narrative fell back to the template" json_check /app/static/narrative.json \
    "d['source'] == 'template' and d['fallback'] is True and d['reason'].startswith('provider unreachable')"
fi
check "one-pager" status_is 200 /app/static/onepager.md
check "one-pager has the recommendation" grep -q "^## Recommendation: " "$TMP/body"
check "unknown static file is 404" status_is 404 /app/static/does-not-exist.json
echo "smoke: $pass passed, $fail failed ($BASE)"
[ "$fail" -eq 0 ]
