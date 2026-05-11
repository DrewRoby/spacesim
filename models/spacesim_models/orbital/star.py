"""
spacesim_models.orbital.star
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
StarDefinition — static parameters for a host star loaded from TOML.

All luminosity/temperature/radius values are stored in solar units (Sol = 1.0)
so the math stays clean and TOMLs stay human-readable.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StarDefinition:
    """
    Static parameters of a host star.

    luminosity    : bolometric luminosity in solar units (L/L☉)
    temperature_k : effective surface temperature in Kelvin
    mass_solar    : mass in solar masses
    radius_solar  : radius in solar radii
    age_gyr       : age in gigayears
    metallicity   : heavy-element fraction (Sol ≈ 0.020)
    """
    id:             str
    name:           str
    spectral_class: str
    mass_solar:     float
    radius_solar:   float
    luminosity:     float
    temperature_k:  float
    age_gyr:        float
    metallicity:    float

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def habitable_zone_inner(self) -> float:
        """
        Inner edge of habitable zone in AU (runaway greenhouse limit).
        Simplified Kopparapu-style: d = sqrt(L / S_inner) where S_inner ≈ 1.10.
        """
        return math.sqrt(self.luminosity / 1.10)

    @property
    def habitable_zone_outer(self) -> float:
        """
        Outer edge of habitable zone in AU (maximum greenhouse limit).
        Simplified: d = sqrt(L / S_outer) where S_outer ≈ 0.36.
        """
        return math.sqrt(self.luminosity / 0.36)

    @property
    def uv_flux_at_1au(self) -> float:
        """
        UV flux relative to Sol at 1 AU from this star.

        UV emission scales very steeply with temperature — hotter stars
        are disproportionately more UV-intense. Approximate exponent ~6
        for the near-UV relevant to surface sterilization.
        """
        return ((self.temperature_k / 5778) ** 6) * (self.radius_solar ** 2)

    @property
    def estimated_main_sequence_lifetime_gyr(self) -> float:
        """
        Rough main-sequence lifetime estimate.
        t ≈ 10 Gyr × (M/M☉)^(-2.5)
        """
        return 10.0 * (self.mass_solar ** -2.5)

    def uv_flux_at_distance(self, distance_au: float) -> float:
        """UV flux relative to Earth-at-1AU at a given distance."""
        return self.uv_flux_at_1au / (distance_au ** 2)

    def insolation_at(self, distance_au: float) -> float:
        """Total stellar flux in W/m² at a given distance."""
        return self.luminosity * 1361.0 / (distance_au ** 2)


# ── TOML loader ────────────────────────────────────────────────────────────────

def load_star(toml_path: Path | str) -> StarDefinition:
    """Load a star definition from a TOML file containing a [star] table."""
    path = Path(toml_path)
    with open(path, "rb") as f:
        data = tomllib.load(f)

    e = data["star"]
    return StarDefinition(
        id             = e["id"],
        name           = e["name"],
        spectral_class = e.get("spectral_class", "?"),
        mass_solar     = float(e["mass_solar"]),
        radius_solar   = float(e["radius_solar"]),
        luminosity     = float(e["luminosity"]),
        temperature_k  = float(e["temperature_k"]),
        age_gyr        = float(e.get("age_gyr", 5.0)),
        metallicity    = float(e.get("metallicity", 0.020)),
    )
