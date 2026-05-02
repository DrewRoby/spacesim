#!/usr/bin/env python3
"""
run_propensities.py — First real model output.

Run from the repo root:
    python tools/run_propensities.py

What this does:
  1. Loads the Standard Human substrate from data/species/standard_human.toml
  2. Computes all ten second-order propensities
  3. Prints a radar-style bar chart
  4. Then demonstrates the model's sensitivity by running three
     comparison species: one with very high Neuroticism heritability,
     one with very high Agreeableness, and one with extreme loss aversion.

This is the model working for the first time. Every number you see
was computed from the substrate parameters you defined.
"""

import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
# Allow running from repo root without installing the package
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "models"))

from spacesim_models.substrate.species import (
    SpeciesSubstrate, CognitiveParams, SocialParams,
    StressParams, DevelopmentParams, OceanHeritability, OceanCovariance,
)
from spacesim_models.substrate.propensities import compute_propensities

# ── Palette ───────────────────────────────────────────────────────────────────
RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"
CYAN  = "\033[36m"; MAGENTA = "\033[35m"; WHITE = "\033[37m"

BAR_WIDTH = 36

PROPENSITY_COLORS = {
    "short_termism":               YELLOW,
    "tribalism_ceiling":           RED,
    "volatility_under_stress":     RED,
    "stratification_tendency":     YELLOW,
    "ideological_susceptibility":  MAGENTA,
    "cooperative_radius":          GREEN,
    "generational_memory_depth":   CYAN,
    "innovation_rate_baseline":    GREEN,
    "political_instability_cycle": YELLOW,
    "loss_aversion_premium":       MAGENTA,
}

def render_bar(name: str, value: float, width: int = BAR_WIDTH) -> str:
    filled = int(value * width)
    empty  = width - filled
    color  = PROPENSITY_COLORS.get(name, WHITE)
    bar    = f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"
    label  = f"{name:<28}"
    return f"  {label} {bar} {BOLD}{value:.3f}{RESET}"


def print_species(substrate: SpeciesSubstrate):
    props = compute_propensities(substrate)
    print(f"\n{BOLD}{WHITE}{'─' * 70}{RESET}")
    print(f"  {BOLD}{substrate.name}{RESET}")
    if substrate.description:
        print(f"  {DIM}{substrate.description}{RESET}")
    print(f"{BOLD}{WHITE}{'─' * 70}{RESET}")
    for name, value in props.as_dict().items():
        print(render_bar(name, value))


def compare_delta(base: SpeciesSubstrate, variant: SpeciesSubstrate, label: str):
    """Print a diff showing how propensities changed between two species."""
    base_props    = compute_propensities(base).as_dict()
    variant_props = compute_propensities(variant).as_dict()

    print(f"\n{BOLD}  Δ vs Standard Human — {label}{RESET}")
    for name in base_props:
        delta = variant_props[name] - base_props[name]
        if abs(delta) < 0.005:
            continue
        arrow = f"{GREEN}▲{RESET}" if delta > 0 else f"{RED}▼{RESET}"
        print(f"    {name:<28} {arrow} {abs(delta):.3f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    toml_path = repo_root / "data" / "species" / "standard_human.toml"

    print(f"\n{BOLD}{WHITE}{'═' * 70}")
    print(f"  SPACESIM — Propensity Model  ·  First Run")
    print(f"{'═' * 70}{RESET}")

    # ── Standard Human ────────────────────────────────────────────────────────
    if toml_path.exists():
        human = SpeciesSubstrate.from_toml(toml_path)
        print(f"\n  {DIM}Loaded from {toml_path}{RESET}")
    else:
        print(f"\n  {YELLOW}standard_human.toml not found — using hardcoded defaults{RESET}")
        human = SpeciesSubstrate(name="Standard Human",
                                 description="Baseline homo sapiens substrate parameters.")

    print_species(human)

    # ── Variant 1: High-Anxiety Species ───────────────────────────────────────
    # Crank Neuroticism heritability way up, slow stress recovery to a crawl.
    # This is a species that evolved in a high-threat environment and carries
    # that anxiety in its genome. What does civilizational behavior look like?
    anxious = SpeciesSubstrate(
        name        = "High-Anxiety Variant",
        description = "N heritability 0.48→0.85, stress_recovery_rate 0.18→0.75",
        heritability = OceanHeritability(
            openness=0.57, conscientiousness=0.49, extraversion=0.54,
            agreeableness=0.42,
            neuroticism=0.85,       # ← way up from 0.48
        ),
        stress = StressParams(
            stress_recovery_rate=0.75,          # ← very slow recovery
            trauma_consolidation_threshold=0.30, # ← easily marked
        ),
    )
    print_species(anxious)
    compare_delta(human, anxious, anxious.description)

    # ── Variant 2: Cooperative Hive-Adjacent Species ───────────────────────────
    # High Agreeableness heritability, low ingroup sensitivity, wide altruism
    # radius. Not a true hive mind — individuals still exist — but a species
    # where cooperation is the deep biological default.
    cooperative = SpeciesSubstrate(
        name        = "Cooperative Variant",
        description = "A heritability 0.42→0.80, ingroup sensitivity 0.68→0.20",
        heritability = OceanHeritability(
            openness=0.57, conscientiousness=0.49, extraversion=0.54,
            agreeableness=0.80,     # ← strongly heritable cooperation
            neuroticism=0.48,
        ),
        social = SocialParams(
            ingroup_detection_sensitivity=0.20,  # ← barely distinguishes us/them
            reciprocal_altruism_radius=0.85,     # ← wide natural trust radius
            dominance_hierarchy_sensitivity=0.30, # ← relatively flat
            coalition_formation_instinct=0.40,
        ),
    )
    print_species(cooperative)
    compare_delta(human, cooperative, cooperative.description)

    # ── Variant 3: Extreme Loss Aversion ─────────────────────────────────────
    # Push loss aversion from 2.3 to 5.0. A species where losses hurt five
    # times as much as equivalent gains feel good. Every economic decision is
    # dominated by what might be taken away. What kind of civilization does
    # this produce?
    loss_averse = SpeciesSubstrate(
        name        = "Extreme Loss Aversion Variant",
        description = "loss_aversion_coefficient 2.3→5.0",
        cognitive = CognitiveParams(
            temporal_discounting_rate=0.72,
            cognitive_load_ceiling=0.28,
            apophenia_coefficient=0.76,
            loss_aversion_coefficient=5.0,  # ← extreme
            dunbar_number=150,
        ),
    )
    print_species(loss_averse)
    compare_delta(human, loss_averse, loss_averse.description)

    # ── Summary note ──────────────────────────────────────────────────────────
    print(f"\n{BOLD}{WHITE}{'─' * 70}{RESET}")
    print(f"  {DIM}All values computed from substrate parameters.")
    print(f"  Edit data/species/standard_human.toml and re-run to see changes.")
    print(f"  Next: wire compute_propensities() into api.py and call from Rust.{RESET}")
    print(f"{BOLD}{WHITE}{'─' * 70}{RESET}\n")


if __name__ == "__main__":
    main()
