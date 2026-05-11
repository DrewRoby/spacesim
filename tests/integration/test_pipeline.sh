#!/usr/bin/env bash
# Tests: full TOML → Python model → Rust display pipeline

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

SPECIES="$REPO_ROOT/data/species/standard_human.toml"

begin_suite "Integration — TOML → Python → Rust pipeline"

assert_exit_0 "pipeline exits 0 with --species flag" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --species "$SPECIES" --ticks 5

assert_has "species name appears in output" "standard human" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --species "$SPECIES" --ticks 5

assert_has "all ten propensity bars are rendered" "tribalism_ceiling" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --species "$SPECIES" --ticks 5

assert_has "tick count is reported" "5 ticks completed" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --species "$SPECIES" --ticks 5

assert_has "propensities are computed (not skipped)" "Propensities computed successfully" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --species "$SPECIES" --ticks 5

summary
