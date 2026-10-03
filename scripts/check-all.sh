#!/usr/bin/env bash
# Run the same checks CI runs, for every track (or TRACKS="python" for one).
#   scripts/check-all.sh          lint + unit tests (+ the dashboard's tests)
#   scripts/check-all.sh --full   + data tests with the coverage gate, the report (notebook / SQL report /
#                                 R Markdown) and the parity check of every track's answers.json
# Optional speed-up for maintainers (used by scripts/verify-tags.sh):
#   PY_VENV=/path/to/venv   reuse an existing virtualenv for the Python and SQL tracks and the dashboard
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FULL=0
[ "${1:-}" = "--full" ] && FULL=1
TRACKS="${TRACKS:-python sql r}"
RESULTS=()
FAILED=0
ANSWERS=()

step() { # step <label> <command...>
  local label="$1"; shift
  echo; echo "──── $label"
  if "$@"; then RESULTS+=("PASS  $label"); else RESULTS+=("FAIL  $label"); FAILED=$((FAILED + 1)); fi
}

venv() { # a .venv for a Python-based folder
  [ -e .venv ] && return 0
  if [ -n "${PY_VENV:-}" ]; then ln -s "$PY_VENV" .venv; else make -s install; fi
}

for track in $TRACKS; do
  dir="$ROOT/tracks/$track"
  [ -d "$dir" ] || { RESULTS+=("SKIP  $track (no tracks/$track)"); continue; }
  cd "$dir" || exit 1
  [ "$track" = r ] || venv
  step "$track: lint" make -s lint
  step "$track: unit tests" make -s test
  if [ "$FULL" = 1 ]; then
    step "$track: unit + data tests + coverage gate" make -s coverage
    step "$track: answers.json" make -s run OUT=out
    step "$track: report" make -s report OUT=out
    ANSWERS+=("$dir/out/answers.json")
  fi
done

if [ -d "$ROOT/dashboard" ] && [ -z "${SKIP_DASHBOARD:-}" ]; then
  cd "$ROOT/dashboard" || exit 1
  venv
  step "dashboard: lint" make -s lint
  step "dashboard: tests" make -s test
fi

if [ "$FULL" = 1 ] && [ ${#ANSWERS[@]} -gt 1 ]; then
  step "parity: every track's answers.json is identical (1e-9)" python3 "$ROOT/scripts/parity.py" "${ANSWERS[@]}"
fi

echo; echo "════ Summary"
printf '%s\n' "${RESULTS[@]}"
[ "$FAILED" -eq 0 ]
