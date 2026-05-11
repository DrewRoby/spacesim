#!/usr/bin/env bash
# Tests: evolutionary pressure computation and environment-to-substrate mapping

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Evolutionary pressure — world-to-substrate mapping"

# ── New body loading ───────────────────────────────────────────────────────────

assert_python "red_dwarf.toml loads as M4V with luminosity 0.004" '
from spacesim_models.orbital import load_star
s = load_star("data/bodies/red_dwarf.toml")
assert s.spectral_class == "M4V", "got " + s.spectral_class
assert abs(s.luminosity - 0.004) < 1e-6, "luminosity=" + str(s.luminosity)
assert s.temperature_k == 3200
'

assert_python "terminator_world.toml loads as tidally locked planet" '
from spacesim_models.orbital import load_planet
p = load_planet("data/bodies/terminator_world.toml")
assert p.tidally_locked == True, "expected tidally_locked"
assert abs(p.semi_major_axis - 0.065) < 1e-6
assert p.star_id == "red_dwarf"
'

assert_python "orange_dwarf.toml loads as K3V star" '
from spacesim_models.orbital import load_star
s = load_star("data/bodies/orange_dwarf.toml")
assert s.spectral_class == "K3V", "got " + s.spectral_class
assert abs(s.luminosity - 0.32) < 1e-6
'

assert_python "feast_famine_world.toml loads with high eccentricity and steep tilt" '
from spacesim_models.orbital import load_planet
p = load_planet("data/bodies/feast_famine_world.toml")
assert p.eccentricity == 0.26, "eccentricity=" + str(p.eccentricity)
assert p.axial_tilt   == 34.0, "tilt=" + str(p.axial_tilt)
assert p.tidally_locked == False
'

# ── Terminator world physics ───────────────────────────────────────────────────

assert_python "terminator world is inside red dwarf habitable zone" '
from spacesim_models.orbital import load_star, load_planet
star   = load_star("data/bodies/red_dwarf.toml")
planet = load_planet("data/bodies/terminator_world.toml")
assert star.habitable_zone_inner < planet.semi_major_axis < star.habitable_zone_outer, \
    "a=" + str(planet.semi_major_axis) + " not in HZ=(" + str(round(star.habitable_zone_inner,4)) + ", " + str(round(star.habitable_zone_outer,4)) + ")"
'

assert_python "feast-famine world is inside orange dwarf habitable zone" '
from spacesim_models.orbital import load_star, load_planet
star   = load_star("data/bodies/orange_dwarf.toml")
planet = load_planet("data/bodies/feast_famine_world.toml")
assert star.habitable_zone_inner < planet.semi_major_axis < star.habitable_zone_outer, \
    "a=" + str(planet.semi_major_axis) + " not in HZ=(" + str(round(star.habitable_zone_inner,4)) + ", " + str(round(star.habitable_zone_outer,4)) + ")"
'

assert_python "feast-famine world has short growing season (< 0.50)" '
from spacesim_models.orbital import load_star, load_planet, compute_seasonal_cycle
star   = load_star("data/bodies/orange_dwarf.toml")
planet = load_planet("data/bodies/feast_famine_world.toml")
cycle  = compute_seasonal_cycle(planet, star)
assert cycle.growing_season_fraction < 0.50, \
    "expected gsf < 0.50, got " + str(round(cycle.growing_season_fraction, 3))
'

assert_python "terminator world has temperate mean temperature (0-25 C)" '
from spacesim_models.orbital import load_star, load_planet, compute_seasonal_cycle
star   = load_star("data/bodies/red_dwarf.toml")
planet = load_planet("data/bodies/terminator_world.toml")
cycle  = compute_seasonal_cycle(planet, star)
assert 0.0 <= cycle.t_mean_c <= 25.0, \
    "t_mean=" + str(round(cycle.t_mean_c, 1)) + " not in expected [0, 25] C"
'

# ── Evolutionary pressure ordering ────────────────────────────────────────────

assert_python "feast-famine world has higher resource_volatility than Earth" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure
sol    = load_star("data/bodies/sol.toml")
earth  = load_planet("data/bodies/earth.toml")
star   = load_star("data/bodies/orange_dwarf.toml")
planet = load_planet("data/bodies/feast_famine_world.toml")
ep_earth = compute_evolutionary_pressure(earth, sol)
ep_ff    = compute_evolutionary_pressure(planet, star)
assert ep_ff.resource_volatility > ep_earth.resource_volatility, \
    "feast-famine=" + str(round(ep_ff.resource_volatility, 3)) + " earth=" + str(round(ep_earth.resource_volatility, 3))
'

assert_python "terminator world has lower resource_volatility than feast-famine world" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure
star_rd = load_star("data/bodies/red_dwarf.toml")
planet_tw = load_planet("data/bodies/terminator_world.toml")
star_od = load_star("data/bodies/orange_dwarf.toml")
planet_ff = load_planet("data/bodies/feast_famine_world.toml")
ep_tw = compute_evolutionary_pressure(planet_tw, star_rd)
ep_ff = compute_evolutionary_pressure(planet_ff, star_od)
assert ep_tw.resource_volatility < ep_ff.resource_volatility, \
    "terminator=" + str(round(ep_tw.resource_volatility, 3)) + " feast-famine=" + str(round(ep_ff.resource_volatility, 3))
'

assert_python "terminator world has higher group_dependence than feast-famine world" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure
ep_tw = compute_evolutionary_pressure(
    load_planet("data/bodies/terminator_world.toml"),
    load_star("data/bodies/red_dwarf.toml"),
)
ep_ff = compute_evolutionary_pressure(
    load_planet("data/bodies/feast_famine_world.toml"),
    load_star("data/bodies/orange_dwarf.toml"),
)
assert ep_tw.group_dependence > ep_ff.group_dependence, \
    "terminator=" + str(round(ep_tw.group_dependence, 3)) + " feast-famine=" + str(round(ep_ff.group_dependence, 3))
'

assert_python "all evolutionary pressure values are in [0, 1]" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure
for star_toml, planet_toml in [
    ("data/bodies/sol.toml",          "data/bodies/earth.toml"),
    ("data/bodies/red_dwarf.toml",    "data/bodies/terminator_world.toml"),
    ("data/bodies/orange_dwarf.toml", "data/bodies/feast_famine_world.toml"),
]:
    ep = compute_evolutionary_pressure(load_planet(planet_toml), load_star(star_toml))
    for name, val in ep.as_dict().items():
        assert 0.0 <= val <= 1.0, f"{planet_toml}: {name}={val} outside [0,1]"
'

# ── Substrate mapping correctness ──────────────────────────────────────────────

assert_python "feast-famine temporal_discounting_rate higher than terminator world" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure, pressure_to_substrate_params
p_tw = pressure_to_substrate_params(compute_evolutionary_pressure(
    load_planet("data/bodies/terminator_world.toml"),
    load_star("data/bodies/red_dwarf.toml"),
))
p_ff = pressure_to_substrate_params(compute_evolutionary_pressure(
    load_planet("data/bodies/feast_famine_world.toml"),
    load_star("data/bodies/orange_dwarf.toml"),
))
tw_tdr = p_tw["cognitive"]["temporal_discounting_rate"]
ff_tdr = p_ff["cognitive"]["temporal_discounting_rate"]
assert ff_tdr > tw_tdr, \
    "feast-famine=" + str(round(ff_tdr, 3)) + " terminator=" + str(round(tw_tdr, 3))
'

assert_python "terminator world dunbar_number higher than feast-famine world" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure, pressure_to_substrate_params
p_tw = pressure_to_substrate_params(compute_evolutionary_pressure(
    load_planet("data/bodies/terminator_world.toml"),
    load_star("data/bodies/red_dwarf.toml"),
))
p_ff = pressure_to_substrate_params(compute_evolutionary_pressure(
    load_planet("data/bodies/feast_famine_world.toml"),
    load_star("data/bodies/orange_dwarf.toml"),
))
assert p_tw["cognitive"]["dunbar_number"] > p_ff["cognitive"]["dunbar_number"], \
    "terminator=" + str(p_tw["cognitive"]["dunbar_number"]) + " feast-famine=" + str(p_ff["cognitive"]["dunbar_number"])
'

assert_python "feast-famine loss_aversion_coefficient higher than terminator world" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure, pressure_to_substrate_params
p_tw = pressure_to_substrate_params(compute_evolutionary_pressure(
    load_planet("data/bodies/terminator_world.toml"),
    load_star("data/bodies/red_dwarf.toml"),
))
p_ff = pressure_to_substrate_params(compute_evolutionary_pressure(
    load_planet("data/bodies/feast_famine_world.toml"),
    load_star("data/bodies/orange_dwarf.toml"),
))
assert p_ff["cognitive"]["loss_aversion_coefficient"] > p_tw["cognitive"]["loss_aversion_coefficient"], \
    "ff=" + str(round(p_ff["cognitive"]["loss_aversion_coefficient"], 3)) + " tw=" + str(round(p_tw["cognitive"]["loss_aversion_coefficient"], 3))
'

assert_python "fight+flight+freeze weights sum to 1.0" '
from spacesim_models.orbital import load_star, load_planet
from spacesim_models.orbital.pressure import compute_evolutionary_pressure, pressure_to_substrate_params
for star_toml, planet_toml in [
    ("data/bodies/sol.toml",          "data/bodies/earth.toml"),
    ("data/bodies/red_dwarf.toml",    "data/bodies/terminator_world.toml"),
    ("data/bodies/orange_dwarf.toml", "data/bodies/feast_famine_world.toml"),
]:
    params = pressure_to_substrate_params(compute_evolutionary_pressure(
        load_planet(planet_toml), load_star(star_toml)
    ))
    s = params["stress"]
    total = s["fight_weight"] + s["flight_weight"] + s["freeze_weight"]
    assert abs(total - 1.0) < 0.01, f"{planet_toml}: FFF sum={total:.4f}"
'

# ── API facade ────────────────────────────────────────────────────────────────

assert_python "get_evolutionary_pressure returns 6 keys all in [0,1]" '
from spacesim_models.api import get_evolutionary_pressure
ep = get_evolutionary_pressure("data/bodies/feast_famine_world.toml", "data/bodies/orange_dwarf.toml")
expected = {"resource_volatility","thermal_danger","survival_scarcity","cognitive_demand","group_dependence","predation_proxy"}
assert set(ep.keys()) == expected, "unexpected keys: " + str(set(ep.keys()))
assert all(0.0 <= v <= 1.0 for v in ep.values()), "values out of range: " + str(ep)
'

assert_python "generate_species_from_environment returns pressures + 4 substrate sections" '
from spacesim_models.api import generate_species_from_environment
result = generate_species_from_environment("data/bodies/terminator_world.toml", "data/bodies/red_dwarf.toml")
assert "pressures"   in result
assert "cognitive"   in result
assert "social"      in result
assert "stress"      in result
assert "development" in result
assert "dunbar_number" in result["cognitive"]
assert "coalition_formation_instinct" in result["social"]
'

# ── Species TOML loading ───────────────────────────────────────────────────────

assert_python "terminator_dweller.toml loads and validates" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/terminator_dweller.toml")
assert s.name == "Terminator Dweller"
assert s.cognitive.dunbar_number > 150, "expected dunbar > 150, got " + str(s.cognitive.dunbar_number)
assert s.cognitive.temporal_discounting_rate < 0.60, \
    "expected tdr < 0.60 (patient), got " + str(s.cognitive.temporal_discounting_rate)
assert s.social.reciprocal_altruism_radius > 0.60, \
    "expected wide altruism > 0.60, got " + str(s.social.reciprocal_altruism_radius)
'

assert_python "feast_famine_dweller.toml loads and validates" '
from spacesim_models.substrate.species import SpeciesSubstrate
s = SpeciesSubstrate.from_toml("data/species/feast_famine_dweller.toml")
assert s.name == "Feast-Famine Dweller"
assert s.cognitive.temporal_discounting_rate > 0.70, \
    "expected high tdr > 0.70, got " + str(s.cognitive.temporal_discounting_rate)
assert s.cognitive.loss_aversion_coefficient > 2.30, \
    "expected high loss aversion, got " + str(s.cognitive.loss_aversion_coefficient)
assert s.cognitive.apophenia_coefficient > 0.90, \
    "expected near-max apophenia, got " + str(s.cognitive.apophenia_coefficient)
'

assert_python "terminator dweller is more patient than feast-famine dweller" '
from spacesim_models.substrate.species import SpeciesSubstrate
tw = SpeciesSubstrate.from_toml("data/species/terminator_dweller.toml")
ff = SpeciesSubstrate.from_toml("data/species/feast_famine_dweller.toml")
assert tw.cognitive.temporal_discounting_rate < ff.cognitive.temporal_discounting_rate, \
    "terminator=" + str(tw.cognitive.temporal_discounting_rate) + " feast-famine=" + str(ff.cognitive.temporal_discounting_rate)
'

assert_python "feast-famine dweller loses more to loss aversion than terminator dweller" '
from spacesim_models.substrate.species import SpeciesSubstrate
tw = SpeciesSubstrate.from_toml("data/species/terminator_dweller.toml")
ff = SpeciesSubstrate.from_toml("data/species/feast_famine_dweller.toml")
assert ff.cognitive.loss_aversion_coefficient > tw.cognitive.loss_aversion_coefficient, \
    "ff=" + str(ff.cognitive.loss_aversion_coefficient) + " tw=" + str(tw.cognitive.loss_aversion_coefficient)
'

summary
