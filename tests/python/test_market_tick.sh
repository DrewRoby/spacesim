#!/usr/bin/env bash
# Tests: run_market_tick — one tick of the needs engine + demand computation

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Market tick — needs decay, satisfaction, and demand output"

assert_python "run_market_tick returns two dicts" '
from spacesim_models.api import run_market_tick
new_sat, demand = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    {},
    {},
    7,
)
assert isinstance(new_sat, dict)
assert isinstance(demand, dict)
'

assert_python "new satiation state has all 7 needs" '
from spacesim_models.api import run_market_tick
new_sat, _ = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    {},
    {},
    7,
)
expected = {"hydration","calories","protein","lipids","carbohydrates","fiber","micronutrients"}
assert set(new_sat.keys()) == expected, "got " + str(set(new_sat.keys()))
'

assert_python "demand vector has all 19 commodities" '
from spacesim_models.api import run_market_tick
from spacesim_models.commodities import load_commodity_dir
_, demand = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    {},
    {},
    7,
)
ids = {c.id for c in load_commodity_dir("data/commodities/")}
assert set(demand.keys()) == ids, "demand keys mismatch"
'

assert_python "all demand values remain in [0, 1]" '
from spacesim_models.api import run_market_tick
_, demand = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    {},
    {},
    7,
)
for cid, val in demand.items():
    assert 0.0 <= val <= 1.0, cid + "=" + str(val)
'

assert_python "satiation decays below starting value when no supply provided" '
from spacesim_models.api import run_market_tick
start = {"hydration": (0.8, 0.05)}
new_sat, _ = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    start,
    {},   # no supply — needs should decay
    7,
)
assert new_sat["hydration"][0] < 0.8, \
    "hydration mean should decay without supply, got " + str(new_sat["hydration"][0])
'

assert_python "satiation rises above starting value with generous supply" '
from spacesim_models.api import run_market_tick
start = {"hydration": (0.2, 0.05)}
new_sat, _ = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    start,
    {"water": 0.50},  # abundant water supply
    7,
)
assert new_sat["hydration"][0] > 0.2, \
    "hydration mean should rise with supply, got " + str(new_sat["hydration"][0])
'

assert_python "water supply elevates hydration demand above protein demand for dehydrated population" '
from spacesim_models.api import run_market_tick
# Severely dehydrated population, no supply for any need
start = {"hydration": (0.1, 0.05), "protein": (0.9, 0.02)}
_, demand = run_market_tick(
    "data/needs/biological_needs.toml",
    "data/commodities/",
    start,
    {},
    7,
)
assert demand["water"] > demand["meat"], \
    "water demand=" + str(round(demand["water"],3)) + " meat demand=" + str(round(demand["meat"],3))
'

assert_python "load_base_supplies returns a dict with 19 entries" '
from spacesim_models.api import load_base_supplies
supplies = load_base_supplies("data/commodities/")
assert len(supplies) == 19, "expected 19 commodities, got " + str(len(supplies))
'

assert_python "all base_supply values are non-negative" '
from spacesim_models.api import load_base_supplies
for cid, val in load_base_supplies("data/commodities/").items():
    assert val >= 0.0, cid + " base_supply=" + str(val)
'

summary
