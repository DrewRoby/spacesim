#!/usr/bin/env bash
# Tests: Rust workspace builds cleanly

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Rust — workspace build"

assert_exit_0 "cargo build succeeds" \
    cargo build --manifest-path "$REPO_ROOT/Cargo.toml"

# Errors only — the one pre-existing unused-import warning in bindings is expected
assert_python "no new errors introduced (Python sanity check of build output)" '
import subprocess, sys
result = subprocess.run(
    ["cargo", "build", "--manifest-path", "Cargo.toml"],
    capture_output=True, text=True
)
errors = [l for l in result.stderr.splitlines() if l.startswith("error")]
if errors:
    print("\n".join(errors))
    sys.exit(1)
'

summary
