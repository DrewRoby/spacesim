# spacesim_models/api.py
# The only surface Rust calls into. Keep it small and stable.
# All complexity lives in the submodules behind this facade.

from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities


def compute_propensities_from_toml(toml_path: str) -> dict[str, float]:
    """Load a species TOML file and return computed second-order propensities.

    This is the primary entry point called by the Rust CLI via PyO3.
    Returns a flat dict with all ten propensity values in [0.0, 1.0].
    """
    substrate = SpeciesSubstrate.from_toml(toml_path)
    props = compute_propensities(substrate)
    return props.as_dict()


def compute_propensities_from_dict(substrate_params: dict) -> dict[str, float]:
    """Given a substrate parameter dict, return computed second-order propensities."""
    # Stub — implement when Rust needs to pass substrate state directly
    raise NotImplementedError("compute_propensities_from_dict not yet implemented")


def get_market_signals(population_state: dict) -> dict:
    """Given a population state snapshot, return a demand vector."""
    # Stub — implement when needs engine is wired up
    raise NotImplementedError("get_market_signals not yet implemented")


def run_demographic_tick(population_state: dict, world_conditions: dict) -> dict:
    """Advance the demographic model one tick. Return updated population state."""
    # Stub — implement when lifecycle model is wired up
    raise NotImplementedError("run_demographic_tick not yet implemented")


def initialize_population(substrate_params: dict, size: int) -> dict:
    """Create a new population from a substrate preset."""
    # Stub — implement when demographic model is wired up
    raise NotImplementedError("initialize_population not yet implemented")
