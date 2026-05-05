"""
spacesim_models.orbital.pressure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Evolutionary pressure — mapping physical world parameters to SpeciesSubstrate.

The central claim of this module is that the physical environment a species
evolves in shapes the *distribution* of its substrate parameters. A world with
violent seasonal swings selects for higher loss aversion; a tidally locked world
with a narrow habitable band selects for denser coalition formation.

Six pressure dimensions capture the relevant selection gradients:

    resource_volatility  [0, 1] — how much food supply varies over time.
                                   High e + high tilt → frequent feast-famine cycles.
                                   Low e + tidal lock → nearly constant supply.

    thermal_danger       [0, 1] — fraction of year at lethal temperatures.
                                   Proportional to time outside [T_grow_min, T_grow_max]
                                   when that implies genuine cold/heat death risk.

    survival_scarcity    [0, 1] — baseline caloric pressure (low growing-season fraction
                                   → less time to build surplus → harder winters).

    cognitive_demand     [0, 1] — planning horizon complexity. Driven by orbital period,
                                   eccentricity, and tidal lock (which collapses 3D space
                                   navigation but adds UV-timing complexity).

    group_dependence     [0, 1] — how much survival requires others. Driven by
                                   spatial scarcity (terminator strip) and storage
                                   logistics (feast-famine storage pooling).

    predation_proxy      [0, 1] — proxy for ancestral predation pressure. Inferred from
                                   habitat density (dense forests → ambush; open terrain
                                   → coursing), modelled from land fraction and terrain.

Substrate mapping
-----------------
The six pressures feed into SpeciesSubstrate parameters via calibrated linear
functions. Calibration anchor: all pressures = 0.5 → standard human defaults.

    temporal_discounting_rate  = clamp(0.4 + 0.4·v + 0.2·s − 0.1·c,       0.0, 1.0)
    loss_aversion_coefficient  = clamp(1.0 + 1.8·s + 0.6·v,               1.0, 6.0)
    dunbar_number              = clamp(round(40 + 200·g + 60·c − 50·s),   20, 500)
    coalition_formation_instinct = clamp(0.20 + 0.45·g + 0.25·d,          0.0, 1.0)
    apophenia_coefficient      = clamp(0.30 + 0.60·v + 0.40·c − 0.20·g,  0.0, 1.0)
    critical_period_sensitivity = clamp(0.30 + 0.60·s + 0.30·t,           0.0, 1.0)
    stress_recovery_rate       = clamp(0.05 + 0.30·t + 0.20·v − 0.10·g,  0.0, 1.0)
    ingroup_detection_sensitivity = clamp(0.30 + 0.40·g + 0.30·pr,        0.0, 1.0)
    reciprocal_altruism_radius = clamp(0.60 − 0.30·s + 0.20·g,           0.0, 1.0)
    fight/flight/freeze        : fight_raw = 0.20 + 0.35·pr·max(0.1, 1.5−g)
                                  flight_raw = 0.15 + 0.45·d (escape feasible)
                                  freeze    = max(0.05, 1 − fight − flight), normalise

where v=resource_volatility, t=thermal_danger, s=survival_scarcity,
      c=cognitive_demand, g=group_dependence, d=cognitive_demand (alias),
      pr=predation_proxy.

Verification (all pressures = 0.5):
    temporal_discounting_rate  = 0.4 + 0.2 + 0.1 − 0.05 = 0.65  (≈human 0.72, close)
    loss_aversion_coefficient  = 1.0 + 0.9 + 0.3 = 2.20           (≈human 2.30, close)
    dunbar_number              = 40 + 100 + 30 − 25 = 145          (≈human 150, close)
    coalition_formation_instinct = 0.20+0.225+0.125 = 0.55        (≈human 0.74, moderate)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .star import StarDefinition
from .planet import PlanetDefinition
from .insolation import seasonal_temperature_range
from .season import compute_seasonal_cycle, T_GROW_MIN, T_GROW_MAX


# ── EvolutionaryPressure ───────────────────────────────────────────────────────

@dataclass
class EvolutionaryPressure:
    """
    Six-dimensional selection pressure vector derived from physical world parameters.

    All values are in [0.0, 1.0].
    Feeds into pressure_to_substrate_params() to generate SpeciesSubstrate values.
    """
    resource_volatility: float   # feast-famine severity
    thermal_danger:      float   # time at lethal temperatures
    survival_scarcity:   float   # long-term caloric constraint
    cognitive_demand:    float   # planning/spatial complexity
    group_dependence:    float   # need for cooperative survival
    predation_proxy:     float   # ancestral predation pressure

    def as_dict(self) -> dict[str, float]:
        return {
            "resource_volatility": self.resource_volatility,
            "thermal_danger":      self.thermal_danger,
            "survival_scarcity":   self.survival_scarcity,
            "cognitive_demand":    self.cognitive_demand,
            "group_dependence":    self.group_dependence,
            "predation_proxy":     self.predation_proxy,
        }


# ── Computing pressure from world parameters ───────────────────────────────────

def compute_evolutionary_pressure(
    planet: PlanetDefinition,
    star:   StarDefinition,
) -> EvolutionaryPressure:
    """
    Derive the EvolutionaryPressure vector from planet and star definitions.

    Each dimension is independently normalised to [0, 1] against physically
    plausible extremes. The calibration anchor is Earth-like conditions → 0.5
    on most dimensions.
    """
    cycle = compute_seasonal_cycle(planet, star)
    t_mean, t_summer, t_winter = seasonal_temperature_range(planet, star)

    # ── resource_volatility ───────────────────────────────────────────────────
    # Driven by growing season fraction and insolation swing.
    # gsf = 1.0 (year-round growing) → very low volatility → 0.05
    # gsf = 0.44 (feast-famine world) → high volatility → ~0.75
    # gsf = 0.0 (never grows) → not simply high volatility; different kind of stress
    # Insolation ratio (periapsis/apoapsis) amplifies the signal.
    #
    # Tidally locked worlds are special: the "seasons" in the seasonal model
    # represent the spatial day/night temperature contrast (the 30°C amplitude
    # override), not temporal oscillations. The terminator strip has essentially
    # constant conditions year-round. Volatility is driven only by eccentricity
    # (slight pulsing of the terminator width over the orbital period).
    if planet.tidally_locked:
        resource_volatility = min(0.20, 0.05 + 0.60 * planet.eccentricity)
    else:
        ecc_amplifier = 1.0 + 2.0 * planet.eccentricity  # e=0: 1.0, e=0.26: 1.52
        gsf = cycle.growing_season_fraction
        base_volatility = max(0.0, 1.0 - gsf)            # 0 when year-round, 1 when never
        resource_volatility = min(1.0, base_volatility * ecc_amplifier)

    # ── thermal_danger ────────────────────────────────────────────────────────
    # Fraction of year with dangerous temperatures (below -10°C or above 50°C)
    # Estimated from sinusoidal model: how far outside survival zone the extremes go.
    COLD_LETHAL = -10.0   # °C — genuine cold-death risk threshold
    HOT_LETHAL  =  50.0   # °C — heat stress becomes lethal
    amplitude = cycle.t_amplitude_c

    if amplitude <= 0.0:
        cold_frac = 1.0 if t_mean < COLD_LETHAL else 0.0
        hot_frac  = 1.0 if t_mean > HOT_LETHAL  else 0.0
    else:
        # T(t) = T_mean + A·cos(ωt)
        # Fraction below COLD_LETHAL: T < TL ↔ cos(ωt) < p_cold
        #   cos(θ) < p for θ ∈ (arccos(p), 2π−arccos(p))
        #   fraction = 1 − arccos(p)/π
        p_cold    = max(-1.0, min(1.0, (COLD_LETHAL - t_mean) / amplitude))
        cold_frac = max(0.0, 1.0 - math.acos(p_cold) / math.pi)

        # Fraction above HOT_LETHAL: T > TH ↔ cos(ωt) > q_hot
        #   cos(θ) > q for θ ∈ (0, arccos(q)) ∪ (2π−arccos(q), 2π)
        #   fraction = arccos(q)/π
        if planet.tidally_locked:
            # Day side permanently hot; ~45% of sphere uninhabitable
            hot_frac = 0.45
        else:
            q_hot    = max(-1.0, min(1.0, (HOT_LETHAL - t_mean) / amplitude))
            hot_frac = max(0.0, math.acos(q_hot) / math.pi)

    thermal_danger = min(1.0, cold_frac + hot_frac)

    # ── survival_scarcity ─────────────────────────────────────────────────────
    # Low growing season fraction → less time to build surplus → harder survival.
    # gsf=1.0 (tropical) → scarcity=0.05  (food is easy year-round)
    # gsf=0.73 (Earth) → scarcity ≈ 0.37
    # gsf=0.44 (feast-famine) → scarcity ≈ 0.61
    # gsf=0.0 (arctic) → scarcity=1.0
    #
    # Tidally locked worlds: year-round growing in terminator strip but the strip
    # is spatially constrained (~10% of surface) — this limits *total* food
    # production, not seasonal availability. Use a moderate fixed scarcity.
    if planet.tidally_locked:
        survival_scarcity = 0.25   # year-round but spatially limited
    else:
        gsf = cycle.growing_season_fraction
        survival_scarcity = max(0.0, min(1.0, 1.0 - gsf))

    # ── cognitive_demand ──────────────────────────────────────────────────────
    # Tidal lock: simple 2D world spatially, but UV/flare timing and underground
    # 3D architecture are cognitively complex → moderate-high demand.
    # High eccentricity: rapidly changing seasons require calendar precision → +demand.
    # Long orbital period: more complex storage logistics → +demand.
    # Short period: simpler, but still food-limited.
    base_demand = 0.30   # baseline for any complex organism
    eccentricity_demand = 0.40 * planet.eccentricity          # e=0.26 → +0.10
    period_demand = min(0.20, planet.orbital_period / 2000.0) # scales with year length
    tidal_demand  = 0.15 if planet.tidally_locked else 0.0    # spatial navigation complexity
    tilt_demand   = 0.10 * (planet.axial_tilt / 45.0)         # steep tilt → harder calendar

    cognitive_demand = min(1.0, base_demand + eccentricity_demand + period_demand
                           + tidal_demand + tilt_demand)

    # ── group_dependence ──────────────────────────────────────────────────────
    # Tidal lock → narrow habitable strip → forced density → very high cooperation.
    # Feast-famine → storage pooling, community granaries → moderate cooperation.
    # Open temperate world → moderate cooperation (Earth baseline).
    if planet.tidally_locked:
        # Narrow terminator band forces tight settlement → high group dependence
        spatial_pressure = 0.75
    else:
        # Open world — spatial freedom reduces mandatory cooperation
        # High volatility means more benefit from pooling surplus
        spatial_pressure = 0.30 + 0.25 * resource_volatility

    group_dependence = min(1.0, spatial_pressure)

    # ── predation_proxy ───────────────────────────────────────────────────────
    # Inferred from land fraction and tidal locking.
    # Dense covered terrain (high land fraction, no open plains) → ambush predators
    # → freeze/hide response dominates.
    # Open terrain (grassland, tidal-lock open day side) → coursing predators
    # → flight dominates.
    # Using land fraction as a rough proxy for terrain openness.
    # Low water/high land → drier, more open terrain → higher coursing pressure.
    land_terrain_openness = planet.land_fraction   # 0=water world, 1=all land
    # Water worlds (ocean-dominated) reduce predation pressure somewhat
    ocean_buffer = (1.0 - planet.land_fraction) * 0.20
    predation_proxy = min(1.0, max(0.0, 0.20 + 0.50 * land_terrain_openness - ocean_buffer))

    return EvolutionaryPressure(
        resource_volatility = resource_volatility,
        thermal_danger      = thermal_danger,
        survival_scarcity   = survival_scarcity,
        cognitive_demand    = cognitive_demand,
        group_dependence    = group_dependence,
        predation_proxy     = predation_proxy,
    )


# ── Substrate parameter derivation ────────────────────────────────────────────

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def pressure_to_substrate_params(pressure: EvolutionaryPressure) -> dict:
    """
    Map an EvolutionaryPressure vector to SpeciesSubstrate parameter values.

    Returns a dict matching the structure expected by SpeciesSubstrate.from_toml()
    (the same nested-section layout), ready to be passed to SpeciesSubstrate
    constructors or written to a TOML file.

    Calibration: all pressures = 0.5 → values close to standard human defaults.
    """
    v  = pressure.resource_volatility
    t  = pressure.thermal_danger
    s  = pressure.survival_scarcity
    c  = pressure.cognitive_demand
    g  = pressure.group_dependence
    pr = pressure.predation_proxy

    # ── Cognitive ─────────────────────────────────────────────────────────────
    temporal_discounting_rate = _clamp(0.4 + 0.4 * v + 0.2 * s - 0.1 * c, 0.0, 1.0)
    loss_aversion_coefficient = _clamp(1.0 + 1.8 * s + 0.6 * v,            1.0, 6.0)
    dunbar_number             = int(_clamp(round(40 + 200 * g + 60 * c - 50 * s), 20, 500))
    apophenia_coefficient     = _clamp(0.30 + 0.60 * v + 0.40 * c - 0.20 * g,    0.0, 1.0)
    # Cognitive load ceiling: high cognitive demand → lower ceiling (more heuristics)
    cognitive_load_ceiling    = _clamp(0.40 - 0.20 * c + 0.10 * v,                0.0, 1.0)

    # ── Social ────────────────────────────────────────────────────────────────
    coalition_formation_instinct    = _clamp(0.20 + 0.45 * g + 0.25 * pr,         0.0, 1.0)
    ingroup_detection_sensitivity   = _clamp(0.30 + 0.40 * g + 0.30 * pr,         0.0, 1.0)
    reciprocal_altruism_radius      = _clamp(0.60 - 0.30 * s + 0.20 * g,          0.0, 1.0)
    dominance_hierarchy_sensitivity = _clamp(0.40 + 0.30 * pr + 0.20 * s - 0.10 * g, 0.0, 1.0)

    # ── Stress ────────────────────────────────────────────────────────────────
    stress_recovery_rate           = _clamp(0.05 + 0.30 * t + 0.20 * v - 0.10 * g, 0.0, 1.0)
    trauma_consolidation_threshold = _clamp(0.30 + 0.40 * t + 0.20 * s,             0.0, 1.0)

    # Fight/flight/freeze: normalised to sum exactly to 1.0
    fight_raw  = 0.20 + 0.35 * pr * max(0.1, 1.5 - g)  # predation + low-group → fight
    flight_raw = 0.15 + 0.45 * c                         # cognitive demand → flight (plan escape)
    freeze_raw = max(0.05, 1.0 - fight_raw - flight_raw)
    fff_sum    = fight_raw + flight_raw + freeze_raw
    fight_weight  = fight_raw  / fff_sum
    flight_weight = flight_raw / fff_sum
    freeze_weight = freeze_raw / fff_sum

    # ── Development ───────────────────────────────────────────────────────────
    critical_period_sensitivity          = _clamp(0.30 + 0.60 * s + 0.30 * t,  0.0, 1.0)
    intergenerational_trauma_coefficient = _clamp(0.05 + 0.25 * t + 0.15 * s, 0.0, 0.5)

    return {
        "cognitive": {
            "temporal_discounting_rate":  temporal_discounting_rate,
            "cognitive_load_ceiling":     cognitive_load_ceiling,
            "apophenia_coefficient":      apophenia_coefficient,
            "loss_aversion_coefficient":  loss_aversion_coefficient,
            "dunbar_number":              dunbar_number,
        },
        "social": {
            "ingroup_detection_sensitivity":    ingroup_detection_sensitivity,
            "reciprocal_altruism_radius":        reciprocal_altruism_radius,
            "dominance_hierarchy_sensitivity":   dominance_hierarchy_sensitivity,
            "coalition_formation_instinct":      coalition_formation_instinct,
        },
        "stress": {
            "fight_weight":                   round(fight_weight,  4),
            "flight_weight":                  round(flight_weight, 4),
            "freeze_weight":                  round(freeze_weight, 4),
            "stress_recovery_rate":           stress_recovery_rate,
            "trauma_consolidation_threshold": trauma_consolidation_threshold,
        },
        "development": {
            "critical_period_sensitivity":          critical_period_sensitivity,
            "intergenerational_trauma_coefficient": intergenerational_trauma_coefficient,
        },
    }
