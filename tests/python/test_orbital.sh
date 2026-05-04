#!/usr/bin/env bash
# Tests: orbital mechanics, insolation physics, and habitability scoring

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/tests/lib.sh"

begin_suite "Orbital — star/planet loading, insolation, habitability"

# ── TOML loading ──────────────────────────────────────────────────────────────

assert_python "sol.toml loads with correct spectral class and luminosity" '
from spacesim_models.orbital import load_star
sol = load_star("data/bodies/sol.toml")
assert sol.spectral_class == "G2V", "got " + sol.spectral_class
assert sol.luminosity == 1.0, "luminosity=" + str(sol.luminosity)
assert sol.temperature_k == 5778
'

assert_python "earth.toml loads with correct orbital and physical parameters" '
from spacesim_models.orbital import load_planet
earth = load_planet("data/bodies/earth.toml")
assert earth.semi_major_axis == 1.0
assert earth.eccentricity    == 0.0167
assert abs(earth.axial_tilt - 23.44) < 0.01
assert earth.tidally_locked  == False
assert earth.o2_fraction     == 0.21
assert earth.star_id         == "sol"
'

# ── Habitable zone ────────────────────────────────────────────────────────────

assert_python "Sol habitable zone contains 1 AU (Earth is inside HZ)" '
from spacesim_models.orbital import load_star
sol = load_star("data/bodies/sol.toml")
assert sol.habitable_zone_inner < 1.0 < sol.habitable_zone_outer, \
    "HZ=(" + str(round(sol.habitable_zone_inner,3)) + ", " + str(round(sol.habitable_zone_outer,3)) + ")"
'

assert_python "brighter star has wider habitable zone than dimmer star" '
from spacesim_models.orbital import load_star
from spacesim_models.orbital.star import StarDefinition
bright = StarDefinition("b","Bright","F5V",1.3,1.3,2.0,6500,5.0,0.020)
dim    = StarDefinition("d","Dim",   "K5V",0.7,0.7,0.2,4500,8.0,0.015)
assert bright.habitable_zone_outer > dim.habitable_zone_outer
assert bright.habitable_zone_inner > dim.habitable_zone_inner
'

# ── Insolation and equilibrium temperature ────────────────────────────────────

assert_python "Earth equilibrium temperature is near 255 K (±5 K)" '
from spacesim_models.orbital import load_planet, load_star, insolation_at, equilibrium_temperature
earth = load_planet("data/bodies/earth.toml")
sol   = load_star("data/bodies/sol.toml")
s     = insolation_at(sol.luminosity, earth.semi_major_axis)
t_eq  = equilibrium_temperature(s, earth.albedo)
assert abs(t_eq - 255.0) < 5.0, "T_eq=" + str(round(t_eq, 1)) + " K (expected ~255 K)"
'

assert_python "Earth surface temperature is near 288 K / 15 C (±5 K)" '
from spacesim_models.orbital import load_planet, load_star, surface_temperature
earth    = load_planet("data/bodies/earth.toml")
sol      = load_star("data/bodies/sol.toml")
t_surf_c = surface_temperature(earth, sol)
assert abs(t_surf_c - 15.0) < 5.0, "T_surf=" + str(round(t_surf_c,1)) + " C (expected ~15 C)"
'

assert_python "insolation is higher at periapsis than apoapsis for eccentric orbit" '
from spacesim_models.orbital import load_planet, load_star, insolation_at_day
earth = load_planet("data/bodies/earth.toml")
sol   = load_star("data/bodies/sol.toml")
# periapsis ≈ day 3, apoapsis ≈ day 186 (half-year later)
s_periapsis = insolation_at_day(earth, sol, 3)
s_apoapsis  = insolation_at_day(earth, sol, 186)
assert s_periapsis > s_apoapsis, \
    "periapsis=" + str(round(s_periapsis)) + " apoapsis=" + str(round(s_apoapsis))
'

# ── Seasonal temperature range ────────────────────────────────────────────────

assert_python "Earth summer temperature exceeds winter temperature" '
from spacesim_models.orbital import load_planet, load_star, seasonal_temperature_range
earth = load_planet("data/bodies/earth.toml")
sol   = load_star("data/bodies/sol.toml")
t_mean, t_summer, t_winter = seasonal_temperature_range(earth, sol)
assert t_summer > t_winter, str(t_summer) + " > " + str(t_winter)
assert t_summer > t_mean   > t_winter
'

assert_python "higher axial tilt produces larger seasonal amplitude than Earth" '
from spacesim_models.orbital import load_planet, load_star, seasonal_temperature_range
from spacesim_models.orbital.planet import PlanetDefinition
earth    = load_planet("data/bodies/earth.toml")
sol      = load_star("data/bodies/sol.toml")
# Clone earth but with 45-degree tilt
tilted = PlanetDefinition(**{**earth.__dict__, "axial_tilt": 45.0})
_, ts_earth,  tw_earth  = seasonal_temperature_range(earth,  sol)
_, ts_tilted, tw_tilted = seasonal_temperature_range(tilted, sol)
amp_earth  = ts_earth  - tw_earth
amp_tilted = ts_tilted - tw_tilted
assert amp_tilted > amp_earth, \
    "tilt=45 amp=" + str(round(amp_tilted,1)) + " vs tilt=23.44 amp=" + str(round(amp_earth,1))
'

# ── Growing season ────────────────────────────────────────────────────────────

assert_python "Earth growing season fraction is between 0.60 and 0.90" '
from spacesim_models.orbital import load_planet, load_star, compute_seasonal_cycle
earth = load_planet("data/bodies/earth.toml")
sol   = load_star("data/bodies/sol.toml")
cycle = compute_seasonal_cycle(earth, sol)
gsf   = cycle.growing_season_fraction
assert 0.60 <= gsf <= 0.90, "growing_season_fraction=" + str(round(gsf, 3))
'

assert_python "no-tilt planet has 1.0 growing season fraction if temperate" '
from spacesim_models.orbital import load_planet, load_star, compute_seasonal_cycle
from spacesim_models.orbital.planet import PlanetDefinition
earth    = load_planet("data/bodies/earth.toml")
sol      = load_star("data/bodies/sol.toml")
notilt   = PlanetDefinition(**{**earth.__dict__, "axial_tilt": 0.0})
cycle    = compute_seasonal_cycle(notilt, sol)
assert cycle.growing_season_fraction == 1.0, \
    "zero-tilt should be year-round, got " + str(cycle.growing_season_fraction)
'

# ── Habitability scoring ──────────────────────────────────────────────────────

assert_python "Earth orbiting Sol scores > 0.80 overall habitability" '
from spacesim_models.orbital import load_planet, load_star, compute_habitability_score
earth = load_planet("data/bodies/earth.toml")
sol   = load_star("data/bodies/sol.toml")
score = compute_habitability_score(earth, sol)
assert score.overall > 0.80, "Earth overall=" + str(round(score.overall, 3))
'

assert_python "frigid world (far from dim star) scores < 0.20 overall" '
from spacesim_models.orbital import load_planet, load_star, compute_habitability_score
from spacesim_models.orbital.planet import PlanetDefinition
earth    = load_planet("data/bodies/earth.toml")
sol      = load_star("data/bodies/sol.toml")
# Ice world: same body as Earth but at 2.5 AU from Sol (no liquid water, very cold)
ice_world = PlanetDefinition(**{**earth.__dict__,
    "semi_major_axis": 2.5,
    "greenhouse_delta_k": 5.0,  # minimal atmosphere
    "atmospheric_pressure": 0.1,
    "water_fraction": 0.0,
})
score = compute_habitability_score(ice_world, sol)
assert score.overall < 0.20, "ice_world overall=" + str(round(score.overall, 3))
'

assert_python "hotter star has higher UV at same orbital distance as cooler star" '
from spacesim_models.orbital import load_star, surface_uv_flux, load_planet
from spacesim_models.orbital.star import StarDefinition
earth = load_planet("data/bodies/earth.toml")
hot   = StarDefinition("h","Hot","F0V",1.6,1.5,5.0,7200,3.0,0.015)
cool  = StarDefinition("c","Cool","K3V",0.7,0.75,0.25,4800,7.0,0.015)
uv_hot  = surface_uv_flux(earth, hot)
uv_cool = surface_uv_flux(earth, cool)
assert uv_hot > uv_cool, "hot_uv=" + str(round(uv_hot,3)) + " cool_uv=" + str(round(uv_cool,3))
'

assert_python "api facade get_habitability_score returns expected keys" '
from spacesim_models.api import get_habitability_score
score = get_habitability_score("data/bodies/earth.toml", "data/bodies/sol.toml")
expected = {"overall","temperature","gravity","pressure","oxygen","radiation","water","tidal_lock"}
assert set(score.keys()) == expected, "unexpected keys: " + str(set(score.keys()))
assert score["overall"] > 0.80
'

assert_python "api facade compute_seasonal_supply_modifier returns 19 commodity modifiers" '
from spacesim_models.api import compute_seasonal_supply_modifier
mods = compute_seasonal_supply_modifier("data/bodies/earth.toml", "data/bodies/sol.toml", 180)
# 19 commodity modifiers + 4 synthetic keys
assert len(mods) == 23, "got " + str(len(mods)) + " keys: " + str(sorted(mods.keys()))
assert "_t_surface_c" in mods
assert "_growing_season" in mods
'

assert_python "agricultural supply modifier is higher in summer than winter" '
from spacesim_models.api import compute_seasonal_supply_modifier
# Northern hemisphere: summer ~day 180, winter ~day 0/365
summer = compute_seasonal_supply_modifier("data/bodies/earth.toml", "data/bodies/sol.toml", 180)
winter = compute_seasonal_supply_modifier("data/bodies/earth.toml", "data/bodies/sol.toml", 10)
assert summer["grain"] > winter["grain"], \
    "grain summer=" + str(round(summer["grain"],3)) + " winter=" + str(round(winter["grain"],3))
'

summary
