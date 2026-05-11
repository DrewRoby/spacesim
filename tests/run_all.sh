#!/usr/bin/env bash
# tests/run_all.sh — master test runner
#
# Usage:
#   bash tests/run_all.sh           run all suites
#   bash tests/run_all.sh --fast    skip Rust build tests (cargo build is slow)
#
# Exit code: 0 if all suites pass, 1 if any fail.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTS_DIR="$REPO_ROOT/tests"

FAST=0
for arg in "$@"; do
    [ "$arg" = "--fast" ] && FAST=1
done

# ── Color codes ───────────────────────────────────────────────────────────────
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

printf "\n"
printf "${B}══════════════════════════════════════════════════════════════════════${Z}\n"
printf "${B}  SPACESIM TEST SUITE${Z}\n"
[ "$FAST" -eq 1 ] && printf "${D}  --fast: Rust build tests skipped${Z}\n"
printf "${B}══════════════════════════════════════════════════════════════════════${Z}\n"

# ── Python model layer ────────────────────────────────────────────────────────
printf "\n${B}── Python model layer ─────────────────────────────────────────────────${Z}\n"

for script in "$TESTS_DIR"/python/test_*.sh; do
    run_suite "$script"
done

# ── Rust simulation layer ─────────────────────────────────────────────────────
printf "\n${B}── Rust simulation layer ──────────────────────────────────────────────${Z}\n"

if [ "$FAST" -eq 1 ]; then
    printf "  ${D}skipped (--fast)${Z}\n"
else
    for script in "$TESTS_DIR"/rust/test_*.sh; do
        run_suite "$script"
    done
fi

# ── Integration ───────────────────────────────────────────────────────────────
printf "\n${B}── Integration ────────────────────────────────────────────────────────${Z}\n"

if [ "$FAST" -eq 1 ]; then
    printf "  ${D}skipped (--fast)${Z}\n"
else
    for script in "$TESTS_DIR"/integration/test_*.sh; do
        run_suite "$script"
    done
fi

# ── Summary ───────────────────────────────────────────────────────────────────
printf "\n${B}══════════════════════════════════════════════════════════════════════${Z}\n"

if [ "$SUITE_FAIL" -eq 0 ]; then
    printf "  ${B}${G}All ${SUITE_PASS} suites passed.${Z}\n"
    printf "${B}══════════════════════════════════════════════════════════════════════${Z}\n\n"
    exit 0
else
    printf "  ${B}${G}${SUITE_PASS} passed${Z}  ${B}${R}${SUITE_FAIL} failed${Z}\n\n"
    for name in "${FAILED_SUITES[@]}"; do
        printf "  ${R}✗${Z} %s\n" "$name"
    done
    printf "${B}══════════════════════════════════════════════════════════════════════${Z}\n\n"
    exit 1
fi
