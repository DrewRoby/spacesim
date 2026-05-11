"""
spacesim_models.needs.demand
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Computes the demand vector from population need states and commodity profiles.

The demand signal for a commodity is the dot product of the population's
urgency vector with that commodity's satisfaction profile — how urgently
do people need the things this commodity provides?

This is the bridge between the behavioral model and the market: it takes
biological states and produces the economic pressure that drives prices.
"""

from __future__ import annotations

from .needs import PopulationNeeds
from ..commodities.loader import CommodityProfile


def compute_demand_vector(
    needs: PopulationNeeds,
    commodities: list[CommodityProfile],
) -> dict[str, float]:
    """
    Compute demand pressure for each commodity given current population need states.

    Returns {commodity_id: demand_pressure} where demand_pressure is in [0.0, 1.0].

    A commodity scores high when:
      - it satisfies needs that have high urgency (people are deprived)
      - it satisfies those needs strongly (high satisfaction values)

    A commodity scores low when:
      - the needs it satisfies are already well-fed (low urgency)
      - it only partially satisfies any given need
    """
    urgencies = needs.urgency_vector()

    demand: dict[str, float] = {}
    for commodity in commodities:
        signal = 0.0
        total_weight = 0.0
        for need_id, satisfaction in commodity.satisfies.items():
            urgency = urgencies.get(need_id, 0.0)
            signal       += urgency * satisfaction
            total_weight += satisfaction

        # Normalize by total satisfaction capacity so a commodity satisfying
        # one need perfectly scores the same as one satisfying two needs at 0.5
        # when both urgencies are equal — prevents multi-need commodities from
        # always outscoring single-need ones.
        demand[commodity.id] = signal / total_weight if total_weight > 0 else 0.0

    return demand


def demand_report(
    needs: PopulationNeeds,
    commodities: list[CommodityProfile],
    width: int = 36,
) -> str:
    """ASCII bar chart of the current demand vector — for terminal inspection."""
    demand = compute_demand_vector(needs, commodities)
    urgencies = needs.urgency_vector()

    lines = ["", "  Need urgencies:", ""]
    for nid, u in sorted(urgencies.items(), key=lambda x: -x[1]):
        bar = "█" * int(u * width) + "░" * (width - int(u * width))
        lines.append(f"    {nid:<20} {bar} {u:.3f}")

    lines += ["", "  Commodity demand:", ""]
    for cid, d in sorted(demand.items(), key=lambda x: -x[1]):
        bar = "█" * int(d * width) + "░" * (width - int(d * width))
        # Look up the commodity name
        name = next((c.name for c in commodities if c.id == cid), cid)
        lines.append(f"    {name:<20} {bar} {d:.3f}")

    return "\n".join(lines)
