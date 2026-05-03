#!/usr/bin/env bash
# Tests: NeedDefinition loading, NeedState distribution math, urgency curves

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Needs — definitions and distribution urgency"

assert_python "biological_needs.toml loads 7 need definitions" '
from spacesim_models.needs import load_need_definitions
defs = load_need_definitions("data/needs/biological_needs.toml")
assert len(defs) == 7, "expected 7 needs, got " + str(len(defs))
'

assert_python "expected need ids are present" '
from spacesim_models.needs import load_need_definitions
ids = {d.id for d in load_need_definitions("data/needs/biological_needs.toml")}
expected = {"hydration","calories","protein","lipids","carbohydrates","fiber","micronutrients"}
missing = expected - ids
assert not missing, "missing need ids: " + str(missing)
'

assert_python "hydration and calories are survival tier" '
from spacesim_models.needs import load_need_definitions
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
assert defs["hydration"].tier == "survival"
assert defs["calories"].tier  == "survival"
'

assert_python "fiber and micronutrients are security tier" '
from spacesim_models.needs import load_need_definitions
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
assert defs["fiber"].tier          == "security"
assert defs["micronutrients"].tier == "security"
'

assert_python "hydration has highest steepness (fastest-spiking urgency)" '
from spacesim_models.needs import load_need_definitions
defs = load_need_definitions("data/needs/biological_needs.toml")
steepnesses = {d.id: d.steepness for d in defs}
max_val = max(steepnesses.values())
assert steepnesses["hydration"] == max_val, \
    "hydration steepness " + str(steepnesses["hydration"]) + " is not max: " + str(steepnesses)
'

# At satiation=0, urgency is bounded by the sigmoid midpoint — not literally 1.0.
# With hydration midpoint=0.35, sigmoid(1.0, 4.0, 0.35) ≈ 0.93.
assert_python "urgency is high (> 0.90) when satiation is 0.0" '
from spacesim_models.needs import load_need_definitions, NeedState
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
state = NeedState(defs["hydration"], mean=0.0, variance=0.0)
assert state.urgency > 0.90, "urgency at satiation=0 was " + str(state.urgency)
'

# At satiation=1, baseline urgency ~0.20 due to sigmoid midpoint — this is
# intentional: there is always some background demand signal even when fed.
assert_python "urgency is low (< 0.25) when satiation is 1.0" '
from spacesim_models.needs import load_need_definitions, NeedState
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
state = NeedState(defs["hydration"], mean=1.0, variance=0.0)
assert state.urgency < 0.25, "urgency at satiation=1 was " + str(state.urgency)
'

assert_python "higher variance raises urgency under deprivation" '
from spacesim_models.needs import load_need_definitions, NeedState
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
low_var  = NeedState(defs["hydration"], mean=0.2, variance=0.02)
high_var = NeedState(defs["hydration"], mean=0.2, variance=0.20)
assert high_var.urgency > low_var.urgency, \
    "high_var=" + str(round(high_var.urgency,4)) + " should exceed low_var=" + str(round(low_var.urgency,4))
'

assert_python "satisfy() raises mean and narrows variance" '
from spacesim_models.needs import load_need_definitions, NeedState
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
state = NeedState(defs["hydration"], mean=0.3, variance=0.15)
before_mean, before_var = state.mean, state.variance
state.satisfy(0.2)
assert state.mean > before_mean
assert state.variance < before_var
'

assert_python "decay() lowers mean and widens variance" '
from spacesim_models.needs import load_need_definitions, NeedState
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
state = NeedState(defs["hydration"], mean=0.7, variance=0.10)
before_mean, before_var = state.mean, state.variance
state.decay(0.1)
assert state.mean < before_mean
assert state.variance > before_var
'

assert_python "mean is clamped to [0, 1]" '
from spacesim_models.needs import load_need_definitions, NeedState
defs = {d.id: d for d in load_need_definitions("data/needs/biological_needs.toml")}
s1 = NeedState(defs["hydration"], mean=1.5, variance=0.0)
assert s1.mean == 1.0, "expected 1.0, got " + str(s1.mean)
s2 = NeedState(defs["hydration"], mean=-0.5, variance=0.0)
assert s2.mean == 0.0, "expected 0.0, got " + str(s2.mean)
'

summary
