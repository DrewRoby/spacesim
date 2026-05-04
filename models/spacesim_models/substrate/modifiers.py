"""
spacesim_models.substrate.modifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Maps second-order civilizational propensities to economic behavior modifiers.

BehaviorModifiers are derived from propensities and influence how a population
interacts with markets — how much they hoard, how sensitive prices are to
demand shocks, how much speculation inflates prices, etc.

This is the bridge between the biological/psychological model and the
market mechanics. The same basic needs can produce radically different
market dynamics depending on the species' propensity profile.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BehaviorModifiers:
    """
    Economic behavior modifiers derived from species propensities.

    demand_amplifier    : scales demand signal [1.0, 1.5]
                          driven by loss_aversion_premium — fearful populations
                          demand more aggressively than their satiation suggests

    supply_hoarding     : fraction of supply withheld from market [0.0, 0.4]
                          driven by stratification_tendency — elite capture
                          of supply reduces effective market availability

    price_sensitivity   : multiplier on price_elasticity [0.5, 2.0]
                          driven by volatility_under_stress — unstable societies
                          react sharply to imbalances, amplifying price swings

    cooperation_discount: price discount applied when demand is low [0.0, 0.3]
                          driven by cooperative_radius — cooperative societies
                          use mutual aid to dampen deflation in slack markets

    speculation_premium : extra premium added when demand is high [0.0, 0.15]
                          driven by short_termism — short-horizon societies
                          generate speculative bubbles above clearing price
    """
    demand_amplifier:     float = 1.25
    supply_hoarding:      float = 0.20
    price_sensitivity:    float = 1.25
    cooperation_discount: float = 0.15
    speculation_premium:  float = 0.075


def propensities_to_modifiers(props: dict[str, float]) -> BehaviorModifiers:
    """
    Derive BehaviorModifiers from a propensity dict.

    props should be the dict returned by compute_propensities_from_toml().
    All propensity values are in [0.0, 1.0].
    """
    return BehaviorModifiers(
        demand_amplifier     = 1.0  + 0.5  * props.get("loss_aversion_premium",      0.5),
        supply_hoarding      = 0.4  *        props.get("stratification_tendency",     0.5),
        price_sensitivity    = 0.5  + 1.5  * props.get("volatility_under_stress",    0.5),
        cooperation_discount = 0.3  *        props.get("cooperative_radius",          0.5),
        speculation_premium  = 0.15 *        props.get("short_termism",               0.5),
    )
