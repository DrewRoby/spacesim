"""
spacesim_models.orbital.season
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SeasonalCycle — maps orbital mechanics to market supply modifiers.

The orbital model produces a temperature curve over the year. This module
converts that curve into supply modifiers for commodity categories, connecting
the physical layer to the market clearing layer.

Supply modifier categories
--------------------------
agricultural  : food produced by farming (grains, vegetables, fruit, tubers,
                legumes); falls sharply outside the growing-temperature window
perishable    : animal products (meat, fish, eggs, milk) sensitive to temperature;
                modest seasonal variation from spoilage vs preservation effects
staple        : processed/storable goods (bread, pasta, oil, nuts) — minimal
                seasonal variation, assumed to reflect stored agricultural surplus
baseline      : water and shelf-stable processed goods — no seasonal modifier

Growing season model
--------------------
A temperate-zone crop grows when the mean surface temperature is in
[T_GROW_MIN, T_GROW_MAX].  The temperature follows a sinusoidal annual cycle:

    T(t) = T_mean + T_amplitude × cos(2π(t − t_summer) / P_year)

where t_summer is the day of peak temperature (quarter-orbit after periapsis).

The growing_season_fraction is the fraction of the year with T ∈ [T_min, T_max],
derived analytically from arccos:

    fraction = (arccos(p) − arccos(q)) / π
    p = (T_GROW_MIN − T_mean) / T_amplitude   (clamp to [−1, 1])
    q = (T_GROW_MAX − T_mean) / T_amplitude   (clamp to [−1, 1])
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from .star import StarDefinition
from .planet import PlanetDefinition
from .insolation import seasonal_temperature_range

# ── Constants ──────────────────────────────────────────────────────────────────

T_GROW_MIN   = 5.0    # °C — crops stop growing below this
T_GROW_MAX   = 40.0   # °C — heat stress above this
T_COMFORT    = 18.0   # °C — baseline comfort temperature for heating/cooling demand
WINTER_FLOOR = 0.20   # fraction of base supply available from stores in deep winter
HEAT_COEFF   = 0.04   # heating demand increase per °C below T_COMFORT
COOL_COEFF   = 0.03   # cooling demand increase per °C above T_COMFORT

CommodityCategory = Literal["agricultural", "perishable", "staple", "baseline"]

COMMODITY_CATEGORIES: dict[str, CommodityCategory] = {
    # Agricultural — fully seasonal
    "grain":       "agricultural",
    "rice":        "agricultural",
    "vegetables":  "agricultural",
    "fruit":       "agricultural",
    "tubers":      "agricultural",
    "legumes":     "agricultural",
    # Perishable — modest seasonal effect
    "meat":        "perishable",
    "fish":        "perishable",
    "eggs":        "perishable",
    "milk":        "perishable",
    # Staple — processed, mostly shelf-stable
    "bread":       "staple",
    "pasta":       "staple",
    "cooking_oil": "staple",
    "butter":      "staple",
    "nuts":        "staple",
    "cheese":      "staple",
    # Baseline — no seasonal adjustment
    "water":       "baseline",
    "broth":       "baseline",
    "fruit_juice": "baseline",
}


# ── Growing season math ────────────────────────────────────────────────────────

def _growing_season_fraction(t_mean: float, t_amplitude: float) -> float:
    """
    Fraction of the year with temperature in [T_GROW_MIN, T_GROW_MAX].

    Derived analytically from the cosine temperature model.
    Returns 1.0 if the full year is in range, 0.0 if never.
    """
    if t_amplitude <= 0.0:
        # No seasons — constant temperature
        return 1.0 if T_GROW_MIN <= t_mean <= T_GROW_MAX else 0.0

    # Normalise thresholds to cos-space.  Temperature model: T(t) = T_mean + A·cos(ωt)
    # T ∈ [T_min, T_max]  ⟺  cos(ωt) ∈ [p, q]
    # Fraction = (arccos(p) − arccos(q)) / π  after clamping both to [−1, 1].
    p = max(-1.0, min(1.0, (T_GROW_MIN - t_mean) / t_amplitude))
    q = max(-1.0, min(1.0, (T_GROW_MAX - t_mean) / t_amplitude))
    return max(0.0, min(1.0, (math.acos(p) - math.acos(q)) / math.pi))


def _growing_season_start_end(
    t_mean: float,
    t_amplitude: float,
    orbital_period: float,
    periapsis_day: int,
) -> tuple[int, int]:
    """
    Approximate day-of-year for growing season start and end.

    Summer peak is at periapsis_day + orbital_period/4 for a prograde orbit
    (Northern Hemisphere summer is aphelion-adjacent on Earth — we approximate
    peak warmth as a quarter-orbit after periapsis).
    """
    # Day of peak temperature (summer solstice proxy)
    summer_day = (periapsis_day + orbital_period / 2) % orbital_period

    if t_amplitude <= 0.0:
        return 0, int(orbital_period)

    p = max(-1.0, min(1.0, (T_GROW_MIN - t_mean) / t_amplitude))
    if p <= -1.0:
        return 0, int(orbital_period)

    # Half-angle in days when T >= T_GROW_MIN
    half_season_days = math.acos(p) / (2 * math.pi) * orbital_period
    start = int((summer_day - half_season_days) % orbital_period)
    end   = int((summer_day + half_season_days) % orbital_period)
    return start, end


# ── SeasonalCycle ─────────────────────────────────────────────────────────────

@dataclass
class SeasonalCycle:
    """
    Pre-computed seasonal parameters for one planet–star pair.

    Consumed by supply_modifier() to scale commodity supply each tick.
    """
    planet_name:              str
    orbital_period_days:      float
    t_mean_c:                 float   # mean annual surface temperature °C
    t_summer_c:               float   # peak summer temperature °C
    t_winter_c:               float   # peak winter temperature °C
    t_amplitude_c:            float   # half the annual range
    growing_season_fraction:  float   # [0, 1] fraction of year crops can grow
    growing_season_start_day: int     # day of year growing season begins
    growing_season_end_day:   int     # day of year growing season ends
    periapsis_day:            int

    def temperature_at_day(self, day_of_year: float) -> float:
        """
        Sinusoidal temperature estimate for a given day.

        T(t) = T_mean + A × cos(2π(t − t_summer) / P)
        where t_summer = periapsis_day + P/4 (peak warmth quarter-orbit after perihelion).
        """
        t_summer = (self.periapsis_day + self.orbital_period_days / 2) % self.orbital_period_days
        phase    = 2.0 * math.pi * (day_of_year - t_summer) / self.orbital_period_days
        return self.t_mean_c + self.t_amplitude_c * math.cos(phase)

    def supply_modifier(self, day_of_year: float, commodity_id: str) -> float:
        """
        Supply modifier for a commodity on a given day of the year.

        Returns a multiplier on base_supply:
            1.0 = normal supply
            > 1.0 = surplus (peak harvest)
            < 1.0 = reduced supply (winter storage, off-season)
        """
        category = COMMODITY_CATEGORIES.get(commodity_id, "baseline")
        t = self.temperature_at_day(day_of_year)

        if category == "baseline":
            return 1.0

        elif category == "agricultural":
            if T_GROW_MIN <= t <= T_GROW_MAX:
                # In-season: slight peak at midsummer
                peak_factor = 1.0 + 0.2 * math.sin(
                    math.pi * (t - T_GROW_MIN) / (T_GROW_MAX - T_GROW_MIN)
                )
                return peak_factor
            elif t < T_GROW_MIN:
                # Winter: stored supply, declining with cold
                cold_ratio = max(0.0, (t - (T_GROW_MIN - 20.0)) / 20.0)
                return max(WINTER_FLOOR, cold_ratio)
            else:
                # Heat stress above T_GROW_MAX
                heat_ratio = max(0.0, 1.0 - (t - T_GROW_MAX) / 15.0)
                return max(0.3, heat_ratio)

        elif category == "perishable":
            # Modest effect: cold preserves, extreme heat causes spoilage
            if t < 0.0:
                return 0.85   # cold storage reduces fresh availability
            elif t > 30.0:
                return max(0.7, 1.0 - (t - 30.0) * 0.015)
            else:
                return 1.0

        elif category == "staple":
            # Processed goods: weakly correlated with agricultural supply
            # Reflect multi-month lag from harvest to shelf
            if self.growing_season_fraction >= 0.9:
                return 1.0  # year-round harvest → constant supply
            in_season = T_GROW_MIN <= t <= T_GROW_MAX
            return 1.0 if in_season else max(0.6, WINTER_FLOOR + 0.4)

        return 1.0

    def heating_demand_modifier(self, day_of_year: float) -> float:
        """
        Multiplier on heating fuel demand relative to a comfortable day.

        > 1.0 in winter (high demand), ≈ 1.0 in comfortable weather, slightly < 1.0 in summer.
        """
        t = self.temperature_at_day(day_of_year)
        if t < T_COMFORT:
            return 1.0 + HEAT_COEFF * (T_COMFORT - t)
        return max(0.5, 1.0 - 0.02 * (t - T_COMFORT))

    def cooling_demand_modifier(self, day_of_year: float) -> float:
        """
        Multiplier on cooling/refrigeration energy demand.

        > 1.0 in summer, ≈ 1.0 in comfortable weather.
        """
        t = self.temperature_at_day(day_of_year)
        if t > T_COMFORT:
            return 1.0 + COOL_COEFF * (t - T_COMFORT)
        return max(0.5, 1.0 - 0.02 * (T_COMFORT - t))


# ── Factory ────────────────────────────────────────────────────────────────────

def compute_seasonal_cycle(
    planet: PlanetDefinition,
    star:   StarDefinition,
) -> SeasonalCycle:
    """Build a SeasonalCycle from planet and star definitions."""
    t_mean, t_summer, t_winter = seasonal_temperature_range(planet, star)
    amplitude = (t_summer - t_winter) / 2.0

    gsf         = _growing_season_fraction(t_mean, amplitude)
    gs_start, gs_end = _growing_season_start_end(
        t_mean, amplitude, planet.orbital_period, planet.periapsis_day,
    )

    return SeasonalCycle(
        planet_name              = planet.name,
        orbital_period_days      = planet.orbital_period,
        t_mean_c                 = t_mean,
        t_summer_c               = t_summer,
        t_winter_c               = t_winter,
        t_amplitude_c            = amplitude,
        growing_season_fraction  = gsf,
        growing_season_start_day = gs_start,
        growing_season_end_day   = gs_end,
        periapsis_day            = planet.periapsis_day,
    )
