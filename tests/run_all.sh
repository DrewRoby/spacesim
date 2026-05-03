#!/usr/bin/env bash
# tests/run_all.sh — master test runner
#
# Usage:
#   ./tests/run_all.sh          run all suites
#   ./tests/run_all.sh --fast   skip Rust build tests (cargo build is slow)
#
# Exit code: 0 if all suites pass, 1 if any fail.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTS_DIR="$REPO_ROOT/tests"

FAST=0
for arg in "${@:-}"; do
    [ "$arg" = "--fast" ] && FAST=1
done

# ── Color codes (duplicated from lib.sh — runner doesn't source it) ───────────
if [ -t 1 ]; then
    G='\033[0;32m'; R='\033[0;31m'; B='\033[1m'; D='\033[2m'; Z='\033[0m'
else
    G=''; R=''; B=''; D=''; Z=''
fi

# ── Runner ────────────────────────────────────────────────────────────────────

SUITE_PASS=0
SUITE_FAIL=0
FAILED_SUITES=()

run_suite() {
    local script="$1"
    local label
    label=$(basename "$script" .sh | sed 's/_/ /g')

    if bash "$script"; then
        SUITE_PASS=$((SUITE_PASS + 1))
    else
        SUITE_FAIL=$((SUITE_FAIL + 1))
        FAILED_SUITES+=("$label")
    fi
}

# ── Header ────────────────────────────────────────────────────────────────────

echo ""
echo -e "${B}══════════════════════════════════════════════════════════════════════${Z}"
echo -e "${B}  SPACESIM TEST SUITE${Z}"
[ "$FAST" -eq 1 ] && echo -e "${D}  --fast: Rust build tests skipped${Z}"
echo -e "${B}══════════════════════════════════════════════════════════════════════${Z}"

# ── Python model layer ────────────────────────────────────────────────────────
echo ""
echo -e "${B}── Python model layer ─────────────────────────────────────────────────${Z}"

for script in "$TESTS_DIR"/python/test_*.sh; do
    run_suite "$script"
done

# ── Rust simulation layer ─────────────────────────────────────────────────────
echo ""
echo -e "${B}── Rust simulation layer ──────────────────────────────────────────────${Z}"

if [ "$FAST" -eq 1 ]; then
    echo -e "  ${D}skipped (--fast)${Z}"
else
    for script in "$TESTS_DIR"/rust/test_*.sh; do
        run_suite "$script"
    done
fi

# ── Integration ───────────────────────────────────────────────────────────────
echo ""
echo -e "${B}── Integration ────────────────────────────────────────────────────────${Z}"

if [ "$FAST" -eq 1 ]; then
    echo -e "  ${D}skipped (--fast)${Z}"
else
    for script in "$TESTS_DIR"/integration/test_*.sh; do
        run_suite "$script"
    done
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${B}══════════════════════════════════════════════════════════════════════${Z}"

if [ "$SUITE_FAIL" -eq 0 ]; then
    echo -e "  ${B}${G}All ${SUITE_PASS} suites passed.${Z}"
    echo -e "${B}══════════════════════════════════════════════════════════════════════${Z}"
    echo ""
    exit 0
else
    echo -e "  ${B}${G}${SUITE_PASS} passed${Z}  ${B}${R}${SUITE_FAIL} failed${Z}"
    echo ""
    for name in "${FAILED_SUITES[@]}"; do
        echo -e "  ${R}✗${Z} $name"
    done
    echo -e "${B}══════════════════════════════════════════════════════════════════════${Z}"
    echo ""
    exit 1
fi
