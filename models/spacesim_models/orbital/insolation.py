"""
spacesim_models.orbital.insolation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Physics of stellar energy delivery and planetary surface conditions.

All math is analytic or iteratively solved — no external dependencies.

Key quantities:
    insolation     : stellar flux at a given point in W/m²
    T_eq           : equilibrium temperature — what the planet would be without atmosphere
    T_surface      : actual mean surface temperature after greenhouse warming
    seasonal range : summer/winter temperature extremes for temperate zone
    habitability   : composite score [0, 1] measuring livability without life support

Reference values (Earth at 1 AU from Sol):
    Insolation      : 1361 W/m²  (the "solar constant")
    T_eq            : 255 K      (-18 °C, before greenhouse)
    T_surface mean  : 288 K      (+15 °C, after +33 K greenhouse)
    UV flux         : 1.0        (normalized)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .star import StarDefinition
from .planet import PlanetDefinition

# ── Constants ──────────────────────────────────────────────────────────────────

SOLAR_CONSTANT   = 1361.0    # W/m² — solar flux at Earth (1 AU from Sol)
STEFAN_BOLTZMANN = 5.6704e-8 # W m⁻² K⁻⁴


# ── Orbital geometry ──────────────────────────────────────────────────────────

def solve_kepler(mean_anomaly: float, eccentricity: float, tol: float = 1e-9) -> float:
    """
    Solve Kepler's equation M = E - e·sin(E) for eccentric anomaly E.

    Newton–Raphson iteration. Converges in <10 steps for e < 0.9.
    """
    # Normalise M to [0, 2π]
    M = mean_anomaly % (2 * math.pi)
    E = M  # initial guess: good for small eccentricity
    for _ in range(50):
        dE = (M - E + eccentricity * math.sin(E)) / (1.0 - eccentricity * math.cos(E))
        E += dE
        if abs(dE) < tol:
            break
    return E


def true_anomaly(eccentric_anomaly: float, eccentricity: float) -> float:
    """Convert eccentric anomaly E to true anomaly ν."""
    e   = eccentricity
    E   = eccentric_anomaly
    return 2.0 * math.atan2(
        math.sqrt(1.0 + e) * math.sin(E / 2.0),
        math.sqrt(1.0 - e) * math.cos(E / 2.0),
    )


def orbital_radius(semi_major_axis: float, eccentricity: float, nu: float) -> float:
    """
    Distance from star at true anomaly ν.

    r(ν) = a(1 − e²) / (1 + e·cos ν)
    """
    a, e = semi_major_axis, eccentricity
    return a * (1.0 - e ** 2) / (1.0 + e * math.cos(nu))


def day_to_true_anomaly(
    day_of_year:         float,
    orbital_period_days: float,
    eccentricity:        float,
    periapsis_day:       int = 3,
) -> float:
    """
    True anomaly (radians) for a given day of the year.

    periapsis_day: day when planet is closest to star (Earth ≈ day 3, early January).
    """
    elapsed  = (day_of_year - periapsis_day) % orbital_period_days
    M        = 2.0 * math.pi * elapsed / orbital_period_days
    E        = solve_kepler(M, eccentricity)
    return true_anomaly(E, eccentricity)


# ── Insolation and temperature ────────────────────────────────────────────────

def insolation_at(luminosity: float, distance_au: float) -> float:
    """Stellar flux in W/m² at distance_au from a star of given luminosity (L/L☉)."""
    return luminosity * SOLAR_CONSTANT / (distance_au ** 2)


def equilibrium_temperature(flux: float, albedo: float) -> float:
    """
    Planetary equilibrium temperature in K.

    Assumes the planet re-radiates as a blackbody from the whole surface
    (factor of 4 between hemisphere-absorbed and full-sphere-emitted flux).

        T_eq = (S × (1 − A) / (4σ))^(1/4)

    Earth: (1361 × 0.694 / (4 × 5.67e-8))^0.25 ≈ 255 K  ✓
    """
    return (flux * (1.0 - albedo) / (4.0 * STEFAN_BOLTZMANN)) ** 0.25


def surface_temperature(planet: PlanetDefinition, star: StarDefinition) -> float:
    """
    Mean annual surface temperature in °C.

        T_surface = T_eq + greenhouse_delta_k
    """
    s    = insolation_at(star.luminosity, planet.semi_major_axis)
    t_eq = equilibrium_temperature(s, planet.albedo)
    return (t_eq + planet.greenhouse_delta_k) - 273.15


def seasonal_temperature_range(
    planet: PlanetDefinition,
    star:   StarDefinition,
) -> tuple[float, float, float]:
    """
    Approximate temperate-zone temperature range over one orbital year.

    Returns (T_mean_c, T_summer_c, T_winter_c) in °C.

    The seasonal amplitude is proportional to axial tilt and eccentricity.
    Calibrated so Earth (tilt=23.44°, e=0.017) → amplitude ≈ 15°C,
    producing T_summer ≈ +30°C, T_winter ≈ 0°C in temperate zones.

    Note: this is a whole-planet temperate-zone average, not latitude-specific.
    A full treatment would integrate over latitude bands.
    """
    t_mean = surface_temperature(planet, star)

    # Amplitude driven by tilt (primary) and eccentricity (secondary)
    tilt_factor = (
        math.sin(math.radians(planet.axial_tilt)) /
        math.sin(math.radians(23.44))              # normalised to Earth tilt
    )
    ecc_factor  = 1.0 + 1.5 * planet.eccentricity

    # 15°C is the Earth-calibrated temperate zone amplitude at tilt=23.44°, e=0.017
    amplitude = 15.0 * tilt_factor * ecc_factor

    # Tidal lock: day side is perpetually hot, night side perpetually cold.
    # We report the *terminator zone* mean, which is approximately T_mean.
    # Summer/winter lose meaning; use +/- 30°C as a proxy for terminator vs
    # exposed poles.
    if planet.tidally_locked:
        amplitude = max(amplitude, 30.0)

    return t_mean, t_mean + amplitude, t_mean - amplitude


def insolation_at_day(
    planet: PlanetDefinition,
    star:   StarDefinition,
    day_of_year: float,
) -> float:
    """
    Instantaneous stellar flux at a specific day of the planet's year.

    Accounts for eccentricity (varying orbital radius). Ignores latitude —
    returns the flux intercepted by a disc perpendicular to the star direction,
    i.e., the "top of atmosphere" instantaneous flux.
    """
    nu = day_to_true_anomaly(
        day_of_year, planet.orbital_period, planet.eccentricity, planet.periapsis_day,
    )
    r = orbital_radius(planet.semi_major_axis, planet.eccentricity, nu)
    return insolation_at(star.luminosity, r)


def time_mean_insolation(
    planet: PlanetDefinition,
    star:   StarDefinition,
    n_samples: int = 365,
) -> float:
    """
    Time-averaged insolation over a full orbit, sampled evenly in time.

    Analytically, <S> = S_0 / sqrt(1 − e²) where S_0 = L/a².
    This numerical version agrees to <0.1% and handles any eccentricity.
    """
    total = sum(
        insolation_at_day(planet, star, day)
        for day in (i * planet.orbital_period / n_samples for i in range(n_samples))
    )
    return total / n_samples


def surface_uv_flux(planet: PlanetDefinition, star: StarDefinition) -> float:
    """
    UV flux at the planet's surface relative to Earth's surface UV.

    Accounts for:
      - stellar UV output (scales steeply with T_eff)
      - orbital distance
      - atmospheric and magnetic shielding
    """
    # UV from the star at this planet's distance, relative to Sol at 1 AU
    uv_toa = star.uv_flux_at_distance(planet.semi_major_axis)

    # Shielding: ozone + magnetic field together block roughly 99% on Earth.
    # We model shielding as: shield = min(1.0, magnetic_field × 0.75 + 0.24)
    #   → Earth (B=1.0): 0.75 + 0.24 = 0.99 → 1% reaches surface
    #   → No field (B=0): 0.24 → 24% reaches surface (thin ozone only)
    shielding_fraction = min(1.0, planet.magnetic_field * 0.75 + 0.24)
    transmitted        = 1.0 - shielding_fraction

    return uv_toa * transmitted


# ── Habitability score ────────────────────────────────────────────────────────

def _gaussian_score(value: float, mu: float, sigma: float) -> float:
    """Gaussian score centred on mu with width sigma. Returns 1.0 at ideal, →0 at extremes."""
    return math.exp(-0.5 * ((value - mu) / sigma) ** 2)


@dataclass
class HabitabilityScore:
    """
    Composite habitability score for a planet.

    overall     : geometric-mean product of all subscores [0.0, 1.0]
                  1.0 = Earth   0.5 = livable with stress   0.0 = lethal

    Each subscore is 1.0 at the Earth-calibrated optimum and falls smoothly
    to 0 outside the viable range.
    """
    overall:     float
    temperature: float   # surface mean temperature vs 15°C
    gravity:     float   # surface gravity vs 9.81 m/s²
    pressure:    float   # atmospheric pressure vs 1.0 atm
    oxygen:      float   # O₂ partial pressure vs 0.21 atm
    radiation:   float   # UV + cosmic ray exposure
    water:       float   # liquid water availability
    tidal_lock:  float   # 1.0 if free-rotating, 0.5 if tidally locked

    def as_dict(self) -> dict[str, float]:
        return {
            "overall":     self.overall,
            "temperature": self.temperature,
            "gravity":     self.gravity,
            "pressure":    self.pressure,
            "oxygen":      self.oxygen,
            "radiation":   self.radiation,
            "water":       self.water,
            "tidal_lock":  self.tidal_lock,
        }


def compute_habitability_score(
    planet: PlanetDefinition,
    star:   StarDefinition,
) -> HabitabilityScore:
    """
    Compute the composite habitability score for a planet orbiting a given star.

    Subscores are computed independently then combined as a geometric mean,
    so a single fatal flaw (zero oxygen, no liquid water) collapses the total.
    A minimum floor of 0.01 is applied per subscore to distinguish "requires
    life support" from "immediately lethal".

    Calibrated so Earth orbiting Sol returns overall ≈ 1.0.
    """
    t_mean, _, _ = seasonal_temperature_range(planet, star)

    # Temperature: ideal 15°C, σ=20°C (covers −25 to +55 at 0.5 score)
    temp_score = _gaussian_score(t_mean, mu=15.0, sigma=20.0)

    # Gravity: ideal 9.81 m/s² (1g), σ=3.5 m/s²
    grav_score = _gaussian_score(planet.surface_gravity, mu=9.81, sigma=3.5)

    # Pressure: ideal 1.0 atm, σ=0.45 atm (Mars ~0.006 scores near 0)
    press_score = _gaussian_score(planet.atmospheric_pressure, mu=1.0, sigma=0.45)

    # Oxygen partial pressure: ideal 0.21 atm, σ=0.08 atm
    o2_score = _gaussian_score(planet.o2_partial_pressure, mu=0.21, sigma=0.08)

    # Radiation: combines UV flux and magnetic shielding
    # Earth-normalised UV at surface ≈ 1.0 → ideal
    uv = surface_uv_flux(planet, star)
    rad_score = _gaussian_score(uv, mu=1.0, sigma=2.0)

    # Water: binary, with partial credit for small amounts
    water_score = min(1.0, planet.water_fraction * 3.0) if planet.water_fraction > 0 else 0.05

    # Tidal lock: free rotation = 1.0; locked = 0.5 (habitable terminator strip)
    lock_score = 0.5 if planet.tidally_locked else 1.0

    # Apply floor: 0.01 = extreme life support needed but not literally impossible
    scores = [
        max(0.01, temp_score),
        max(0.01, grav_score),
        max(0.01, press_score),
        max(0.01, o2_score),
        max(0.01, rad_score),
        max(0.01, water_score),
        lock_score,
    ]

    # Geometric mean — everyone must be close to 1.0 for overall to be high
    overall = math.prod(scores) ** (1.0 / len(scores))

    return HabitabilityScore(
        overall     = overall,
        temperature = temp_score,
        gravity     = grav_score,
        pressure    = press_score,
        oxygen      = o2_score,
        radiation   = rad_score,
        water       = water_score,
        tidal_lock  = lock_score,
    )
