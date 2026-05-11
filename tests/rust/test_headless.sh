#!/usr/bin/env bash
# Tests: headless simulation runner executes and completes ticks

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Rust — headless runner"

assert_exit_0 "cargo run --ticks 5 exits 0" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --ticks 5

assert_has "output reports correct tick count" "5 ticks completed" \
    cargo run --manifest-path "$REPO_ROOT/Cargo.toml" \
        -p spacesim-cli -- --ticks 5

summary
