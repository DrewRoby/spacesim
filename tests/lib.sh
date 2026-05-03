#!/usr/bin/env bash
# tests/lib.sh — shared helpers for all test scripts
#
# Usage in a test script:
#   source "$REPO_ROOT/tests/lib.sh"
#   begin_suite "Suite Name"
#   assert_exit_0   "description"  some_command arg1 arg2
#   assert_python   "description"  'python expression that is truthy or raises'
#   assert_has      "description"  "expected substring"  some_command arg1
#   summary  # prints results and exits 1 if any failures

# ── Counters (per-script) ─────────────────────────────────────────────────────
PASS_COUNT=0
FAIL_COUNT=0

# ── Color codes ───────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    _GREEN='\033[0;32m'
    _RED='\033[0;31m'
    _YELLOW='\033[0;33m'
    _BOLD='\033[1m'
    _DIM='\033[2m'
    _RESET='\033[0m'
else
    _GREEN=''; _RED=''; _YELLOW=''; _BOLD=''; _DIM=''; _RESET=''
fi

# ── Primitives ────────────────────────────────────────────────────────────────

_pass() {
    echo -e "  ${_GREEN}✓${_RESET} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

_fail() {
    echo -e "  ${_RED}✗${_RESET} $1"
    [ -n "${2:-}" ] && echo -e "    ${_DIM}$2${_RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

begin_suite() {
    echo ""
    echo -e "${_BOLD}$1${_RESET}"
}

# ── Assert functions ──────────────────────────────────────────────────────────

# assert_exit_0 "description" cmd [args...]
# Pass if command exits 0.
assert_exit_0() {
    local desc="$1"; shift
    local output
    if output=$("$@" 2>&1); then
        _pass "$desc"
    else
        _fail "$desc" "command failed: $*"
    fi
}

# assert_fails "description" cmd [args...]
# Pass if command exits non-zero (tests that bad input is rejected).
assert_fails() {
    local desc="$1"; shift
    if ! "$@" >/dev/null 2>&1; then
        _pass "$desc"
    else
        _fail "$desc" "expected failure but command succeeded: $*"
    fi
}

# assert_python "description" "python code"
# Pass if python3 -c "code" exits 0. Code should raise or call sys.exit(1) to fail.
# Run from REPO_ROOT so relative data paths work.
assert_python() {
    local desc="$1"
    local code="$2"
    local output
    if output=$(cd "$REPO_ROOT" && python3 -c "$code" 2>&1); then
        _pass "$desc"
    else
        _fail "$desc" "$output"
    fi
}

# assert_has "description" "pattern" cmd [args...]
# Pass if command output contains pattern (grep -q).
assert_has() {
    local desc="$1"
    local pattern="$2"
    shift 2
    local output
    output=$("$@" 2>&1)
    if echo "$output" | grep -qi "$pattern"; then
        _pass "$desc"
    else
        _fail "$desc" "expected '${pattern}' in output"
    fi
}

# ── Summary ───────────────────────────────────────────────────────────────────

summary() {
    echo ""
    local status
    if [ "$FAIL_COUNT" -eq 0 ]; then
        echo -e "  ${_BOLD}${_GREEN}${PASS_COUNT} passed${_RESET}"
        return 0
    else
        echo -e "  ${_BOLD}${_GREEN}${PASS_COUNT} passed${_RESET}  ${_RED}${FAIL_COUNT} failed${_RESET}"
        return 1
    fi
}
