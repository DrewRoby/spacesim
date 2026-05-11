#!/usr/bin/env bash
# Tests: SpeciesSubstrate TOML loading and validation

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Substrate — TOML loading and validation"

assert_python "standard_human.toml loads without error" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
'

assert_python "species name reads correctly from TOML" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
assert s.name == "Standard Human", f"expected Standard Human, got {s.name}"
'

assert_python "all cognitive params are in valid ranges" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
c = s.cognitive
assert 0 <= c.temporal_discounting_rate <= 1
assert 0 <= c.apophenia_coefficient <= 1
assert 1 <= c.loss_aversion_coefficient <= 6
assert c.dunbar_number >= 5
'

assert_python "fight+flight+freeze weights sum to 1.0" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
st = s.stress
total = st.fight_weight + st.flight_weight + st.freeze_weight
assert abs(total - 1.0) < 0.01, f"weights sum to {total}"
'

assert_python "stage proportions sum to 1.0" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
d = s.development
total = d.stage_development + d.stage_youth + d.stage_adult + d.stage_elder + d.stage_terminal
assert abs(total - 1.0) < 0.01, f"stages sum to {total}"
'

assert_python "validation rejects loss_aversion out of range" '
import sys
from spacesim_models.substrate.species import SpeciesSubstrate, CognitiveParams
try:
    SpeciesSubstrate(cognitive=CognitiveParams(loss_aversion_coefficient=9.0))
    sys.exit(1)  # should not reach here
except ValueError:
    pass
'

assert_python "heritability coefficients all in [0,1]" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
for trait, val in s.heritability.as_dict().items():
    assert 0 <= val <= 1, f"heritability.{trait} = {val} out of range"
'

summary
