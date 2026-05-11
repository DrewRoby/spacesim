"""
spacesim_models.orbital.planet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PlanetDefinition — static parameters for a planet loaded from TOML.

Physical quantities are stored in SI-friendly normalized units where possible
(Earth = 1.0 for mass, radius; AU for distance; atm for pressure) so TOML
files are human-readable without scientific notation.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlanetDefinition:
    """
    Static parameters of a planet.

    Orbital parameters determine insolation and seasonal cycles.
    Physical parameters determine what life is possible and at what cost.
    Atmospheric parameters determine actual surface temperature and breathability.
    """
    id:              str
    name:            str
    star_id:         str   # matches StarDefinition.id

    # ── Orbital ──────────────────────────────────────────────────────────────
    semi_major_axis:  float   # AU
    eccentricity:     float   # [0, 1)
    axial_tilt:       float   # degrees; 0 = no seasons
    orbital_period:   float   # days
    rotation_period:  float   # hours
    tidally_locked:   bool
    periapsis_day:    int     # day of year when planet is nearest star

    # ── Physical ─────────────────────────────────────────────────────────────
    mass_earth:      float   # M/M⊕
    radius_earth:    float   # R/R⊕
    surface_gravity: float   # m/s²
    magnetic_field:  float   # relative to Earth (0 = none, 1 = Earth-like)
    albedo:          float   # Bond albedo [0, 1]

    # ── Atmosphere ────────────────────────────────────────────────────────────
    atmospheric_pressure: float   # atm
    o2_fraction:          float   # mole fraction [0, 1]
    co2_ppm:              float   # CO₂ concentration
    greenhouse_delta_k:   float   # K of surface warming above T_eq

    # ── Surface ───────────────────────────────────────────────────────────────
    water_fraction:  float   # fraction of surface with liquid water or ice
    land_fraction:   float

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def o2_partial_pressure(self) -> float:
        """O₂ partial pressure in atm."""
        return self.o2_fraction * self.atmospheric_pressure

    @property
    def orbital_period_years(self) -> float:
        return self.orbital_period / 365.25

    @property
    def gravity_g(self) -> float:
        """Surface gravity in units of Earth g."""
        return self.surface_gravity / 9.81

    @classmethod
    def derived_gravity(cls, mass_earth: float, radius_earth: float) -> float:
        """Compute surface gravity in m/s² from mass and radius in Earth units."""
        return 9.81 * mass_earth / (radius_earth ** 2)

    @classmethod
    def derived_orbital_period(cls, semi_major_axis: float, star_mass_solar: float) -> float:
        """
        Kepler's Third Law: P = 365.25 × sqrt(a³ / M_star) days.
        a in AU, M_star in solar masses.
        """
        return 365.25 * math.sqrt((semi_major_axis ** 3) / star_mass_solar)


# ── TOML loader ────────────────────────────────────────────────────────────────

def load_planet(toml_path: Path | str) -> PlanetDefinition:
    """Load a planet definition from a TOML file containing a [planet] table."""
    path = Path(toml_path)
    with open(path, "rb") as f:
        data = tomllib.load(f)

    e = data["planet"]

    mass_earth   = float(e["mass_earth"])
    radius_earth = float(e["radius_earth"])

    # surface_gravity: stored directly, or derived from mass/radius
    surface_gravity = float(e.get(
        "surface_gravity",
        PlanetDefinition.derived_gravity(mass_earth, radius_earth),
    ))

    return PlanetDefinition(
        id                   = e["id"],
        name                 = e["name"],
        star_id              = e.get("star_id", "unknown"),
        semi_major_axis      = float(e["semi_major_axis"]),
        eccentricity         = float(e.get("eccentricity", 0.0)),
        axial_tilt           = float(e.get("axial_tilt", 0.0)),
        orbital_period       = float(e.get("orbital_period", 365.25)),
        rotation_period      = float(e.get("rotation_period", 24.0)),
        tidally_locked       = bool(e.get("tidally_locked", False)),
        periapsis_day        = int(e.get("periapsis_day", 3)),
        mass_earth           = mass_earth,
        radius_earth         = radius_earth,
        surface_gravity      = surface_gravity,
        magnetic_field       = float(e.get("magnetic_field", 1.0)),
        albedo               = float(e.get("albedo", 0.30)),
        atmospheric_pressure = float(e.get("atmospheric_pressure", 1.0)),
        o2_fraction          = float(e.get("o2_fraction", 0.21)),
        co2_ppm              = float(e.get("co2_ppm", 400.0)),
        greenhouse_delta_k   = float(e.get("greenhouse_delta_k", 33.0)),
        water_fraction       = float(e.get("water_fraction", 0.0)),
        land_fraction        = float(e.get("land_fraction", 1.0)),
    )
