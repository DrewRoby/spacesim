#!/usr/bin/env bash
# Tests: demand vector computation — directionality and distribution effects

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Demand vector — computation and distribution effects"

assert_python "demand vector has an entry for every commodity" '
from spacesim_models.api import compute_demand_from_needs
from spacesim_models.commodities import load_commodity_dir
demand = compute_demand_from_needs("data/needs/biological_needs.toml", "data/commodities/")
ids    = {c.id for c in load_commodity_dir("data/commodities/")}
assert set(demand.keys()) == ids
'

assert_python "all demand values are in [0.0, 1.0]" '
from spacesim_models.api import compute_demand_from_needs
demand = compute_demand_from_needs("data/needs/biological_needs.toml", "data/commodities/")
for cid, val in demand.items():
    assert 0.0 <= val <= 1.0, cid + " demand = " + str(val)
'

assert_python "severe dehydration makes water the highest-demand commodity" '
from spacesim_models.api import compute_demand_from_needs
demand = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"hydration": (0.1, 0.05)},
)
top = max(demand, key=demand.get)
assert top == "water", "expected water to lead, got " + top + " (water=" + str(round(demand["water"],3)) + ")"
'

assert_python "dehydration elevates all hydrating commodities above dry-food baseline" '
from spacesim_models.api import compute_demand_from_needs
demand = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"hydration": (0.1, 0.05)},
)
hydrating = ["water", "broth", "fruit_juice"]
dry       = ["grain", "meat", "cooking_oil"]
min_h = min(demand[c] for c in hydrating)
max_d = max(demand[c] for c in dry)
assert min_h > max_d, "min hydrating=" + str(round(min_h,3)) + " should exceed max dry=" + str(round(max_d,3))
'

# Sigmoid midpoints mean there is always background urgency; even at 95% satiation
# some demand remains. Threshold is set to account for this intentional floor.
assert_python "well-fed population demand is meaningfully reduced (< 0.40)" '
from spacesim_models.api import compute_demand_from_needs
need_ids = ["hydration","calories","protein","lipids","carbohydrates","fiber","micronutrients"]
demand = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={n: (0.95, 0.02) for n in need_ids},
)
max_d = max(demand.values())
assert max_d < 0.40, "max demand in well-fed population = " + str(round(max_d,3))
'

assert_python "higher variance at deprivation produces higher demand than lower variance" '
from spacesim_models.api import compute_demand_from_needs
low_var  = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"hydration": (0.2, 0.02)},
)
high_var = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"hydration": (0.2, 0.20)},
)
assert high_var["water"] > low_var["water"], \
    "high_var water=" + str(round(high_var["water"],4)) + " should exceed low_var=" + str(round(low_var["water"],4))
'

assert_python "protein deficiency elevates meat and legumes above hydrating commodities" '
from spacesim_models.api import compute_demand_from_needs
demand = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"protein": (0.05, 0.05), "hydration": (0.9, 0.02)},
)
assert demand["meat"]    > demand["water"], \
    "meat=" + str(round(demand["meat"],3)) + " water=" + str(round(demand["water"],3))
assert demand["legumes"] > demand["water"], \
    "legumes=" + str(round(demand["legumes"],3)) + " water=" + str(round(demand["water"],3))
'

assert_python "float shorthand and (float, float) tuple produce identical results" '
from spacesim_models.api import compute_demand_from_needs
d_float = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"hydration": 0.4},
)
d_tuple = compute_demand_from_needs(
    "data/needs/biological_needs.toml", "data/commodities/",
    satiation_state={"hydration": (0.4, 0.10)},
)
assert d_float == d_tuple, "float shorthand and explicit (mean, 0.10) tuple differ"
'

summary
