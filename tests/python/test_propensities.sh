#!/usr/bin/env bash
# Tests: compute_propensities() correctness and sensitivity

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Propensities — computation correctness"

assert_python "returns exactly 10 propensities" '
from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
p = compute_propensities(s).as_dict()
assert len(p) == 10, f"expected 10 propensities, got {len(p)}"
'

assert_python "all propensity values are in [0.0, 1.0]" '
from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
for name, val in compute_propensities(s).as_dict().items():
    assert 0.0 <= val <= 1.0, f"{name} = {val} out of range"
'

assert_python "Standard Human tribalism_ceiling > 0.6" '
from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
p = compute_propensities(s)
assert p.tribalism_ceiling > 0.6, f"tribalism_ceiling = {p.tribalism_ceiling}"
'

assert_python "Standard Human cooperative_radius < 0.5" '
from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
s = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
p = compute_propensities(s)
assert p.cooperative_radius < 0.5, f"cooperative_radius = {p.cooperative_radius}"
'

assert_python "api facade compute_propensities_from_toml returns same values" '
from spacesim_models.substrate.species import SpeciesSubstrate
from spacesim_models.substrate.propensities import compute_propensities
from spacesim_models.api import compute_propensities_from_toml
direct = compute_propensities(SpeciesSubstrate.from_toml("data/species/standard_human.toml")).as_dict()
via_api = compute_propensities_from_toml("data/species/standard_human.toml")
for k in direct:
    assert abs(direct[k] - via_api[k]) < 1e-9, f"mismatch on {k}"
'

assert_python "high-anxiety variant has higher volatility_under_stress than Standard Human" '
from spacesim_models.substrate.species import SpeciesSubstrate, OceanHeritability, StressParams
from spacesim_models.substrate.propensities import compute_propensities
human = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
anxious = SpeciesSubstrate(
    heritability=OceanHeritability(neuroticism=0.85),
    stress=StressParams(stress_recovery_rate=0.75, trauma_consolidation_threshold=0.30),
)
assert (compute_propensities(anxious).volatility_under_stress >
        compute_propensities(human).volatility_under_stress)
'

assert_python "cooperative variant has higher cooperative_radius than Standard Human" '
from spacesim_models.substrate.species import SpeciesSubstrate, OceanHeritability, SocialParams
from spacesim_models.substrate.propensities import compute_propensities
human = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
coop = SpeciesSubstrate(
    heritability=OceanHeritability(agreeableness=0.80),
    social=SocialParams(ingroup_detection_sensitivity=0.20, reciprocal_altruism_radius=0.85,
                        dominance_hierarchy_sensitivity=0.30, coalition_formation_instinct=0.40),
)
assert (compute_propensities(coop).cooperative_radius >
        compute_propensities(human).cooperative_radius)
'

assert_python "extreme loss aversion raises loss_aversion_premium" '
from spacesim_models.substrate.species import SpeciesSubstrate, CognitiveParams
from spacesim_models.substrate.propensities import compute_propensities
human = SpeciesSubstrate.from_toml("data/species/standard_human.toml")
miser = SpeciesSubstrate(cognitive=CognitiveParams(loss_aversion_coefficient=5.0))
assert (compute_propensities(miser).loss_aversion_premium >
        compute_propensities(human).loss_aversion_premium)
'

summary
