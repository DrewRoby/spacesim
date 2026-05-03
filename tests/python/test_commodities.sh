#!/usr/bin/env bash
# Tests: commodity TOML loading and satisfaction profile integrity

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Commodities — TOML loading and satisfaction profiles"

assert_python "load_commodity_dir loads all 19 commodities" '
from spacesim_models.commodities import load_commodity_dir
commodities = load_commodity_dir("data/commodities/")
assert len(commodities) == 19, "expected 19 commodities, got " + str(len(commodities))
'

assert_python "all commodity ids are unique" '
from spacesim_models.commodities import load_commodity_dir
ids = [c.id for c in load_commodity_dir("data/commodities/")]
dupes = [x for x in ids if ids.count(x) > 1]
assert not dupes, "duplicate ids: " + str(dupes)
'

assert_python "all satisfaction values are in [0.0, 1.0]" '
from spacesim_models.commodities import load_commodity_dir
for c in load_commodity_dir("data/commodities/"):
    for need, val in c.satisfies.items():
        assert 0.0 <= val <= 1.0, c.id + "." + need + " = " + str(val)
'

assert_python "water satisfies only hydration at 1.0" '
from spacesim_models.commodities import load_commodity_dir
commodities = {c.id: c for c in load_commodity_dir("data/commodities/")}
water = commodities["water"]
assert water.satisfies.get("hydration") == 1.0
assert water.satisfies.get("calories", 0.0) == 0.0
'

assert_python "cooking_oil has highest lipid satisfaction" '
from spacesim_models.commodities import load_commodity_dir
commodities = {c.id: c for c in load_commodity_dir("data/commodities/")}
assert commodities["cooking_oil"].satisfies.get("lipids", 0) == 1.0
'

assert_python "meat has protein satisfaction > 0.8" '
from spacesim_models.commodities import load_commodity_dir
commodities = {c.id: c for c in load_commodity_dir("data/commodities/")}
val = commodities["meat"].satisfies.get("protein", 0)
assert val > 0.8, "meat protein = " + str(val)
'

assert_python "legumes have fiber > 0.5 (distinguishes them from meat)" '
from spacesim_models.commodities import load_commodity_dir
commodities = {c.id: c for c in load_commodity_dir("data/commodities/")}
val = commodities["legumes"].satisfies.get("fiber", 0)
assert val > 0.5, "legumes fiber = " + str(val)
'

assert_python "vegetables lead all commodities on micronutrients" '
from spacesim_models.commodities import load_commodity_dir
commodities = load_commodity_dir("data/commodities/")
veg = next(c for c in commodities if c.id == "vegetables")
veg_micro = veg.satisfies.get("micronutrients", 0)
for c in commodities:
    if c.id == "vegetables":
        continue
    other = c.satisfies.get("micronutrients", 0)
    assert veg_micro >= other, c.id + " micronutrients=" + str(other) + " exceeds vegetables=" + str(veg_micro)
'

assert_python "hydrating commodities (water, broth, juice) all satisfy hydration > 0.5" '
from spacesim_models.commodities import load_commodity_dir
commodities = {c.id: c for c in load_commodity_dir("data/commodities/")}
for cid in ["water", "broth", "fruit_juice"]:
    val = commodities[cid].satisfies.get("hydration", 0)
    assert val > 0.5, cid + " hydration = " + str(val)
'

summary
