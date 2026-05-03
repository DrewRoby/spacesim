# spacesim_models/api.py
# The only surface Rust calls into. Keep it small and stable.
# All complexity lives in the submodules behind this facade.

from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
from spacesim_models.needs import (
    load_need_definitions,
    PopulationNeeds,
    compute_demand_vector,
)
from spacesim_models.commodities import load_commodity_dir
from pathlib import Path


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


def compute_demand_from_needs(
    needs_toml: str,
    commodities_dir: str,
    satiation_state: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute commodity demand vector from biological need states.

    needs_toml      : path to a needs definition TOML (e.g. data/needs/biological_needs.toml)
    commodities_dir : directory of commodity TOML files (e.g. data/commodities/)
    satiation_state : {need_id: satiation} overrides; defaults to 0.5 for all needs

    Returns {commodity_id: demand_pressure} in [0.0, 1.0].
    Called by Rust via PyO3 each tick to drive market clearing.
    """
    definitions  = load_need_definitions(needs_toml)
    commodities  = load_commodity_dir(commodities_dir)
    pop_needs    = PopulationNeeds.default(definitions, satiation=0.5)

    if satiation_state:
        for need_id, satiation in satiation_state.items():
            if need_id in pop_needs.states:
                pop_needs.states[need_id].satiation = max(0.0, min(1.0, satiation))

    return compute_demand_vector(pop_needs, commodities)


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
