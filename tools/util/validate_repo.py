#!/usr/bin/env python3
"""
validate_repo.py — Spacesim repo structure checker

Run from the repo root:
    python tools/validate_repo.py

Or from anywhere by passing the repo root as an argument:
    python validate_repo.py /path/to/spacesim
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

# ── Palette ──────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"

def ok(s):    return f"{GREEN}✓{RESET}  {s}"
def warn(s):  return f"{YELLOW}~{RESET}  {s}"
def fail(s):  return f"{RED}✗{RESET}  {s}"
def info(s):  return f"{CYAN}·{RESET}  {DIM}{s}{RESET}"
def head(s):  return f"\n{BOLD}{WHITE}{s}{RESET}"

# ── Entry definition ──────────────────────────────────────────────────────────

@dataclass
class Entry:
    path: str                              # Relative to repo root
    kind: Literal["dir", "file"]
    required: bool = True                  # False = optional, shown as warning
    note: str = ""                         # Displayed alongside warn/fail

REQUIRED_DIRS = "dir", True
OPTIONAL_DIR  = "dir", False
REQUIRED_FILE = "file", True
OPTIONAL_FILE = "file", False

# ── The expected structure ────────────────────────────────────────────────────

ENTRIES: list[Entry] = [

    # ── Top-level ─────────────────────────────────────────────────────────────
    Entry("Cargo.toml",         *REQUIRED_FILE, note="Workspace root — must declare [workspace]"),
    Entry("Makefile",           *OPTIONAL_FILE, note="Recommended but not required to start"),
    Entry(".gitignore",         *OPTIONAL_FILE),
    Entry("README.md",          *OPTIONAL_FILE),
    Entry(".env.example",       *OPTIONAL_FILE),
    Entry("rust-toolchain.toml",*OPTIONAL_FILE, note="Pins Rust toolchain version"),

    # ── sim/ crates ───────────────────────────────────────────────────────────
    Entry("sim",                        *REQUIRED_DIRS),
    Entry("sim/types",                  *REQUIRED_DIRS, note="Shared type definitions — no logic, no deps"),
    Entry("sim/types/Cargo.toml",       *REQUIRED_FILE),
    Entry("sim/types/src",              *REQUIRED_DIRS),
    Entry("sim/types/src/lib.rs",       *REQUIRED_FILE),

    Entry("sim/core",                   *REQUIRED_DIRS),
    Entry("sim/core/Cargo.toml",        *REQUIRED_FILE),
    Entry("sim/core/src",               *REQUIRED_DIRS),
    Entry("sim/core/src/lib.rs",        *REQUIRED_FILE),
    Entry("sim/core/src/tick.rs",       *OPTIONAL_FILE),
    Entry("sim/core/src/world",         *OPTIONAL_DIR),
    Entry("sim/core/src/market",        *OPTIONAL_DIR),
    Entry("sim/core/src/agents",        *OPTIONAL_DIR),
    Entry("sim/core/src/events",        *OPTIONAL_DIR),

    Entry("sim/ipc",                    *REQUIRED_DIRS),
    Entry("sim/ipc/Cargo.toml",         *REQUIRED_FILE),
    Entry("sim/ipc/src",                *REQUIRED_DIRS),
    Entry("sim/ipc/src/lib.rs",         *REQUIRED_FILE),

    Entry("sim/bindings",               *REQUIRED_DIRS, note="PyO3 bridge crate"),
    Entry("sim/bindings/Cargo.toml",    *REQUIRED_FILE),
    Entry("sim/bindings/src",           *REQUIRED_DIRS),
    Entry("sim/bindings/src/lib.rs",    *REQUIRED_FILE),

    Entry("sim/cli",                    *REQUIRED_DIRS, note="Headless runner — needed for make run-headless"),
    Entry("sim/cli/Cargo.toml",         *REQUIRED_FILE),
    Entry("sim/cli/src",                *REQUIRED_DIRS),
    Entry("sim/cli/src/main.rs",        *REQUIRED_FILE),

    # ── models/ Python package ────────────────────────────────────────────────
    Entry("models",                             *REQUIRED_DIRS),
    Entry("models/pyproject.toml",              *REQUIRED_FILE),
    Entry("models/spacesim_models",             *REQUIRED_DIRS, note="The importable package"),
    Entry("models/spacesim_models/__init__.py", *REQUIRED_FILE),
    Entry("models/spacesim_models/api.py",      *REQUIRED_FILE, note="The only surface PyO3 calls into"),

    Entry("models/spacesim_models/substrate",           *REQUIRED_DIRS),
    Entry("models/spacesim_models/substrate/__init__.py",*REQUIRED_FILE),
    Entry("models/spacesim_models/personality",         *REQUIRED_DIRS),
    Entry("models/spacesim_models/personality/__init__.py",*REQUIRED_FILE),
    Entry("models/spacesim_models/lifecycle",           *REQUIRED_DIRS),
    Entry("models/spacesim_models/lifecycle/__init__.py",*REQUIRED_FILE),
    Entry("models/spacesim_models/needs",               *REQUIRED_DIRS),
    Entry("models/spacesim_models/needs/__init__.py",   *REQUIRED_FILE),
    Entry("models/spacesim_models/behavior",            *REQUIRED_DIRS),
    Entry("models/spacesim_models/behavior/__init__.py",*REQUIRED_FILE),
    Entry("models/spacesim_models/archetypes",          *REQUIRED_DIRS),
    Entry("models/spacesim_models/archetypes/__init__.py",*REQUIRED_FILE),
    Entry("models/spacesim_models/signals.py",          *REQUIRED_FILE),

    # ── game/ Godot project ───────────────────────────────────────────────────
    Entry("game",                   *REQUIRED_DIRS),
    Entry("game/project.godot",     *REQUIRED_FILE, note="Godot project file"),
    Entry("game/scenes",            *REQUIRED_DIRS),
    Entry("game/scripts",           *REQUIRED_DIRS),
    Entry("game/assets",            *REQUIRED_DIRS),

    Entry("game/scenes/main",               *OPTIONAL_DIR),
    Entry("game/scenes/galaxy_map",         *OPTIONAL_DIR),
    Entry("game/scenes/market",             *OPTIONAL_DIR),
    Entry("game/scenes/population_dashboard",*OPTIONAL_DIR),
    Entry("game/scenes/designer",           *OPTIONAL_DIR),

    Entry("game/scripts/autoloads",         *OPTIONAL_DIR),
    Entry("game/assets/ships",              *OPTIONAL_DIR),
    Entry("game/assets/environments",       *OPTIONAL_DIR),
    Entry("game/assets/ui",                 *OPTIONAL_DIR),

    # ── data/ ─────────────────────────────────────────────────────────────────
    Entry("data",                               *REQUIRED_DIRS),
    Entry("data/species",                       *REQUIRED_DIRS),
    Entry("data/species/standard_human.toml",   *REQUIRED_FILE, note="The Standard Human preset"),
    Entry("data/factions",                      *REQUIRED_DIRS),
    Entry("data/commodities",                   *REQUIRED_DIRS),
    Entry("data/events",                        *OPTIONAL_DIR),
    Entry("data/world",                         *OPTIONAL_DIR),
    Entry("data/designer",                      *OPTIONAL_DIR),

    # ── tools/ ────────────────────────────────────────────────────────────────
    Entry("tools",              *REQUIRED_DIRS),
    Entry("tools/blender",      *OPTIONAL_DIR),

    # ── docs/ ─────────────────────────────────────────────────────────────────
    Entry("docs",                   *REQUIRED_DIRS),
    Entry("docs/index.md",          *OPTIONAL_FILE),
    Entry("docs/adr",               *OPTIONAL_DIR, note="Architecture Decision Records"),
]

# ── Extra content checks ──────────────────────────────────────────────────────

def check_cargo_workspace(root: Path) -> list[str]:
    """Verify Cargo.toml actually declares a workspace and lists expected members."""
    issues = []
    cargo = root / "Cargo.toml"
    if not cargo.exists():
        return issues  # Already caught by structure check
    text = cargo.read_text()
    if "[workspace]" not in text:
        issues.append("Cargo.toml exists but does not contain [workspace] — "
                       "it may be a crate manifest rather than the workspace root")
    expected_members = ["sim/core", "sim/ipc", "sim/bindings", "sim/cli", "sim/types"]
    for m in expected_members:
        if m not in text:
            issues.append(f"Cargo.toml [workspace] does not mention member: {m}")
    return issues


def check_python_importable(root: Path) -> list[str]:
    """Check whether the Python package looks importable."""
    issues = []
    pkg = root / "models" / "spacesim_models"
    if not pkg.exists():
        return issues
    api = pkg / "api.py"
    if api.exists():
        text = api.read_text()
        expected_fns = [
            "get_market_signals",
            "run_demographic_tick",
            "compute_propensities",
            "initialize_population",
        ]
        for fn in expected_fns:
            if fn not in text:
                issues.append(f"api.py is missing expected function: {fn}()")
    return issues


def check_standard_human_toml(root: Path) -> list[str]:
    """Spot-check the standard_human.toml has the expected sections."""
    issues = []
    toml_path = root / "data" / "species" / "standard_human.toml"
    if not toml_path.exists():
        return issues
    text = toml_path.read_text()
    expected_sections = [
        "[cognitive]", "[social]", "[stress]", "[development]", "[heritability]"
    ]
    for sec in expected_sections:
        if sec not in text:
            issues.append(f"standard_human.toml is missing section: {sec}")
    return issues


# ── Runner ────────────────────────────────────────────────────────────────────

def run(root: Path) -> int:
    passed = failed = warned = 0

    print(head("Spacesim Repo Structure Validator"))
    print(f"  {DIM}Root: {root}{RESET}\n")

    # ── Structure check ───────────────────────────────────────────────────────
    sections = {
        "Top-level":            lambda e: "/" not in e.path,
        "sim/ (Rust workspace)":lambda e: e.path.startswith("sim"),
        "models/ (Python)":     lambda e: e.path.startswith("models"),
        "game/ (Godot)":        lambda e: e.path.startswith("game"),
        "data/":                lambda e: e.path.startswith("data"),
        "tools/ & docs/":       lambda e: e.path.startswith("tools") or e.path.startswith("docs"),
    }

    grouped: dict[str, list[Entry]] = {k: [] for k in sections}
    for entry in ENTRIES:
        for label, predicate in sections.items():
            if predicate(entry):
                grouped[label].append(entry)
                break

    for section, entries in grouped.items():
        print(head(section))
        for entry in entries:
            target = root / entry.path
            exists = target.exists()
            is_right_kind = (
                (entry.kind == "dir" and target.is_dir()) or
                (entry.kind == "file" and target.is_file())
            ) if exists else False

            if exists and is_right_kind:
                print(ok(entry.path))
                passed += 1
            elif exists and not is_right_kind:
                wrong = "file" if entry.kind == "dir" else "dir"
                print(fail(f"{entry.path}  {DIM}(exists as {wrong}, expected {entry.kind}){RESET}"))
                failed += 1
            elif entry.required:
                note = f"  {DIM}{entry.note}{RESET}" if entry.note else ""
                print(fail(f"{entry.path}{note}"))
                failed += 1
            else:
                note = f"  {DIM}{entry.note}{RESET}" if entry.note else ""
                print(warn(f"{entry.path}  {DIM}(optional, not yet created){RESET}{note}"))
                warned += 1

    # ── Content checks ────────────────────────────────────────────────────────
    content_checks = [
        ("Cargo.toml workspace declaration", check_cargo_workspace(root)),
        ("api.py function surface",          check_python_importable(root)),
        ("standard_human.toml sections",     check_standard_human_toml(root)),
    ]

    any_content_issues = any(issues for _, issues in content_checks)
    if any_content_issues:
        print(head("Content Checks"))
        for label, issues in content_checks:
            if issues:
                print(f"  {YELLOW}{label}:{RESET}")
                for issue in issues:
                    print(f"    {fail(issue)}")
                    failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print(head("Summary"))
    print(f"  {GREEN}{passed} passed{RESET}   "
          f"{YELLOW}{warned} optional/missing{RESET}   "
          f"{RED}{failed} required/failed{RESET}\n")

    if failed == 0:
        print(f"  {BOLD}{GREEN}Repo structure looks good.{RESET}")
    else:
        print(f"  {BOLD}{RED}{failed} required item(s) need attention.{RESET}")

    print()
    return 0 if failed == 0 else 1


def main():
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        # Assume we're running from somewhere inside the repo;
        # walk up until we find a Cargo.toml or hit the filesystem root
        candidate = Path.cwd()
        while True:
            if (candidate / "Cargo.toml").exists() and (candidate / "sim").exists():
                root = candidate
                break
            parent = candidate.parent
            if parent == candidate:
                # Fell off the top — just use cwd and let checks fail naturally
                root = Path.cwd()
                break
            candidate = parent

    if not root.exists():
        print(f"{RED}Error: {root} does not exist.{RESET}")
        sys.exit(1)

    sys.exit(run(root))


if __name__ == "__main__":
    main()