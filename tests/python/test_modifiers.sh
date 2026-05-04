#!/usr/bin/env bash
# Tests: BehaviorModifiers derivation from propensities

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "BehaviorModifiers — propensity-to-modifier mapping"

assert_python "modifiers are derived from propensity dict" '
from spacesim_models.substrate.modifiers import propensities_to_modifiers
props = {
    "loss_aversion_premium":   0.5,
    "stratification_tendency": 0.5,
    "volatility_under_stress": 0.5,
    "cooperative_radius":      0.5,
    "short_termism":           0.5,
}
m = propensities_to_modifiers(props)
assert m.demand_amplifier    == 1.25
assert m.supply_hoarding     == 0.20
assert m.price_sensitivity   == 1.25
assert m.cooperation_discount == 0.15
assert m.speculation_premium  == 0.075
'

assert_python "high stratification increases supply hoarding" '
from spacesim_models.substrate.modifiers import propensities_to_modifiers
low  = propensities_to_modifiers({"stratification_tendency": 0.1})
high = propensities_to_modifiers({"stratification_tendency": 0.9})
assert high.supply_hoarding > low.supply_hoarding, \
    "high=" + str(high.supply_hoarding) + " low=" + str(low.supply_hoarding)
'

assert_python "high volatility increases price sensitivity" '
from spacesim_models.substrate.modifiers import propensities_to_modifiers
low  = propensities_to_modifiers({"volatility_under_stress": 0.1})
high = propensities_to_modifiers({"volatility_under_stress": 0.9})
assert high.price_sensitivity > low.price_sensitivity
'

assert_python "high loss aversion amplifies demand above 1.0" '
from spacesim_models.substrate.modifiers import propensities_to_modifiers
m = propensities_to_modifiers({"loss_aversion_premium": 0.9})
assert m.demand_amplifier > 1.0, "demand_amplifier=" + str(m.demand_amplifier)
'

assert_python "high cooperative radius increases cooperation discount" '
from spacesim_models.substrate.modifiers import propensities_to_modifiers
low  = propensities_to_modifiers({"cooperative_radius": 0.1})
high = propensities_to_modifiers({"cooperative_radius": 0.9})
assert high.cooperation_discount > low.cooperation_discount
'

assert_python "all modifier values stay in their defined ranges" '
from spacesim_models.substrate.modifiers import propensities_to_modifiers
for val in [0.0, 0.25, 0.5, 0.75, 1.0]:
    m = propensities_to_modifiers({
        "loss_aversion_premium":   val,
        "stratification_tendency": val,
        "volatility_under_stress": val,
        "cooperative_radius":      val,
        "short_termism":           val,
    })
    assert 1.0  <= m.demand_amplifier    <= 1.5,  "demand_amplifier=" + str(m.demand_amplifier)
    assert 0.0  <= m.supply_hoarding     <= 0.4,  "supply_hoarding=" + str(m.supply_hoarding)
    assert 0.5  <= m.price_sensitivity   <= 2.0,  "price_sensitivity=" + str(m.price_sensitivity)
    assert 0.0  <= m.cooperation_discount <= 0.3, "cooperation_discount=" + str(m.cooperation_discount)
    assert 0.0  <= m.speculation_premium <= 0.15, "speculation_premium=" + str(m.speculation_premium)
'

assert_python "get_behavior_modifiers_from_toml returns 5 keys for standard_human" '
from spacesim_models.api import get_behavior_modifiers_from_toml
m = get_behavior_modifiers_from_toml("data/species/standard_human.toml")
expected = {"demand_amplifier","supply_hoarding","price_sensitivity","cooperation_discount","speculation_premium"}
assert set(m.keys()) == expected, "unexpected keys: " + str(set(m.keys()))
'

summary
