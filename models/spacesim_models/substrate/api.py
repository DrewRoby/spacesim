"""
spacesim_models.api
~~~~~~~~~~~~~~~~~~~~
The only surface area visible to Rust via PyO3.

Keep this file small and stable. All complexity lives in the submodules.
Add functions here only when a new Rust call-site genuinely needs one.
"""

from .substrate import SpeciesSubstrate, compute_propensities as _compute


def compute_propensities_from_toml(toml_path: str) -> dict[str, float]:
    """
    Load a species substrate from a TOML file and return its propensities.

    This is the primary entry point called from Rust. The caller passes the
    path to a species TOML file (e.g. data/species/standard_human.toml) and
    receives a flat dict of propensity_name → float [0.0, 1.0].

    Args:
        toml_path: Absolute or repo-relative path to a species TOML file.

    Returns:
        dict with keys matching Propensities.as_dict()
    """
    substrate = SpeciesSubstrate.from_toml(toml_path)
    return _compute(substrate).as_dict()


def compute_propensities(substrate_params: dict) -> dict[str, float]:
    """
    Compute propensities from a substrate parameter dict.

    For cases where Rust has already loaded and owns the substrate data
    and passes it as a serialized dict rather than a file path.

    Args:
        substrate_params: dict matching SpeciesSubstrate.to_dict() schema

    Returns:
        dict with keys matching Propensities.as_dict()
    """
    # For now, delegate to the TOML path if provided.
    # Full from_dict support added when Rust owns substrate mutation.
    if "toml_path" in substrate_params:
        return compute_propensities_from_toml(substrate_params["toml_path"])

    # Stub: return neutral propensities for bare dict calls
    # (will be replaced once SpeciesSubstrate.from_dict() is implemented)
    return {k: 0.5 for k in [
        "short_termism", "tribalism_ceiling", "volatility_under_stress",
        "stratification_tendency", "ideological_susceptibility",
        "cooperative_radius", "generational_memory_depth",
        "innovation_rate_baseline", "political_instability_cycle",
        "loss_aversion_premium",
    ]}


def get_market_signals(population_state: dict) -> dict:
    """Given a population state snapshot from Rust, return a demand vector."""
    # stub
    return {}


def run_demographic_tick(population_state: dict, world_conditions: dict) -> dict:
    """Advance the demographic model one tick. Return updated population state."""
    # stub
    return population_state


def initialize_population(substrate_params: dict, size: int) -> dict:
    """Create a new population from a substrate preset."""
    # stub
    return {
        "node_id": 0,
        "size": size,
        "trait_means": {
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
            "agreeableness": 0.5, "neuroticism": 0.5,
        },
        "trait_stdevs": {k: 0.1 for k in
            ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]},
        "need_urgencies": {
            "survival": 0.2, "security": 0.3, "belonging": 0.3,
            "esteem": 0.4, "transcendence": 0.5,
        },
        "stress_level": 0.1,
    }
