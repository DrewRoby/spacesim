# spacesim_models/api.py
# The only surface Rust calls into. Keep it small and stable.
# All complexity lives in the submodules behind this facade.

from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
from spacesim_models.substrate.modifiers import propensities_to_modifiers
from spacesim_models.needs import (
    load_need_definitions,
    NeedState,
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
    satiation_state: dict[str, float | tuple[float, float]] | None = None,
) -> dict[str, float]:
    """Compute commodity demand vector from biological need states.

    needs_toml      : path to a needs definition TOML (e.g. data/needs/biological_needs.toml)
    commodities_dir : directory of commodity TOML files (e.g. data/commodities/)
    satiation_state : per-need overrides; each value is either:
                        float         → mean satiation, default variance (0.10)
                        (float, float) → (mean, variance)
                      defaults to mean=0.5, variance=0.10 for all needs

    Returns {commodity_id: demand_pressure} in [0.0, 1.0].
    Called by Rust via PyO3 each tick to drive market clearing.
    """
    definitions = load_need_definitions(needs_toml)
    commodities = load_commodity_dir(commodities_dir)
    pop_needs   = PopulationNeeds.default(definitions, mean=0.5, variance=0.10)

    if satiation_state:
        for need_id, override in satiation_state.items():
            if need_id not in pop_needs.states:
                continue
            if isinstance(override, tuple):
                mean, variance = override
            else:
                mean, variance = override, 0.10
            state          = pop_needs.states[need_id]
            state.mean     = max(0.0, min(1.0, mean))
            state.variance = max(0.0, min(0.25, variance))

    return compute_demand_vector(pop_needs, commodities)


def get_behavior_modifiers_from_toml(toml_path: str) -> dict[str, float]:
    """Load species TOML, compute propensities, and map them to market behavior modifiers.

    Returns a flat dict with five modifier values:
        demand_amplifier, supply_hoarding, price_sensitivity,
        cooperation_discount, speculation_premium
    """
    substrate = SpeciesSubstrate.from_toml(toml_path)
    props     = compute_propensities(substrate)
    mods      = propensities_to_modifiers(props.as_dict())
    return {
        "demand_amplifier":     mods.demand_amplifier,
        "supply_hoarding":      mods.supply_hoarding,
        "price_sensitivity":    mods.price_sensitivity,
        "cooperation_discount": mods.cooperation_discount,
        "speculation_premium":  mods.speculation_premium,
    }


def load_base_supplies(commodities_dir: str) -> dict[str, float]:
    """Return {commodity_id: base_supply_per_day} for all commodities in a directory.

    Called once by Rust at startup to populate WorldState.base_supply.
    """
    commodities = load_commodity_dir(commodities_dir)
    return {c.id: c.base_supply for c in commodities}


def run_market_tick(
    needs_toml:       str,
    commodities_dir:  str,
    satiation_state:  dict[str, tuple[float, float]],
    effective_supply: dict[str, float],
    tick_days:        int,
) -> tuple[dict[str, tuple[float, float]], dict[str, float]]:
    """Advance biological needs one tick and compute commodity demand.

    Called by Rust each simulation tick via PyO3.

    satiation_state  : {need_id: (mean, variance)} — current satiation distribution
    effective_supply : {commodity_id: supply_per_day} — base_supply × (1 - hoarding)
    tick_days        : days this tick represents

    Tick sequence:
        1. Decay all needs by decay_rate_per_day × tick_days
        2. Satisfy needs: for each commodity in effective_supply, compute
           satisfy_amount = supply × tick_days × satisfies[need], apply to need
        3. Compute demand vector from updated need states

    Returns (new_satiation_state, demand_vector) where:
        new_satiation_state = {need_id: (new_mean, new_variance)}
        demand_vector       = {commodity_id: demand [0.0, 1.0]}
    """
    definitions   = load_need_definitions(needs_toml)
    commodities   = load_commodity_dir(commodities_dir)
    commodity_map = {c.id: c for c in commodities}

    pop_needs = PopulationNeeds(states={
        d.id: NeedState(
            d,
            *satiation_state.get(d.id, (0.5, 0.10)),
        )
        for d in definitions
    })

    # 1. Decay
    for state in pop_needs.states.values():
        state.decay(state.definition.decay_rate_per_day * tick_days)

    # 2. Satisfy from effective supply
    for commodity_id, supply_per_day in effective_supply.items():
        if supply_per_day <= 0.0:
            continue
        commodity = commodity_map.get(commodity_id)
        if commodity is None:
            continue
        for need_id, satisfaction_value in commodity.satisfies.items():
            need_state = pop_needs.states.get(need_id)
            if need_state is None:
                continue
            amount = supply_per_day * tick_days * satisfaction_value
            need_state.satisfy(amount)

    # 3. Demand vector
    demand = compute_demand_vector(pop_needs, commodities)

    new_satiation = {
        nid: (s.mean, s.variance) for nid, s in pop_needs.states.items()
    }
    return new_satiation, demand


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
