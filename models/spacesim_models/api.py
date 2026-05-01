# spacesim_models/api.py
# This is the surface area of the Python layer as seen from Rust.
# Keep it small. Keep it stable. All complexity lives behind it.

def get_market_signals(population_state: dict) -> dict:
    """Given a population state snapshot, return a demand vector."""
    ...

def run_demographic_tick(population_state: dict, world_conditions: dict) -> dict:
    """Advance the demographic model one tick. Return updated population state."""
    ...

def compute_propensities(substrate_params: dict) -> dict:
    """Given substrate parameters, return computed second-order propensities."""
    ...

def initialize_population(substrate_params: dict, size: int) -> dict:
    """Create a new population from a substrate preset."""
    ...
