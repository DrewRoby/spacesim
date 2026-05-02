"""
spacesim_models.substrate.species
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The SpeciesSubstrate dataclass — a validated, typed container for all
biological substrate parameters defined in a species TOML file.

This is the single source of truth for what a species *is* at the hardware
level. Everything in the behavioral model downstream receives one of these.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


# ── Heritability matrix ────────────────────────────────────────────────────────

@dataclass
class OceanHeritability:
    """
    Per-trait heritability coefficients [0.0, 1.0].

    A heritability of 0.57 for Openness means that 57% of the variance in
    Openness scores across a population is attributable to genetic differences.
    The rest is environment and noise.
    """
    openness:          float = 0.57
    conscientiousness: float = 0.49
    extraversion:      float = 0.54
    agreeableness:     float = 0.42
    neuroticism:       float = 0.48

    def as_dict(self) -> dict[str, float]:
        return {
            "openness":          self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion":      self.extraversion,
            "agreeableness":     self.agreeableness,
            "neuroticism":       self.neuroticism,
        }


@dataclass
class OceanCovariance:
    """
    Genetic covariance between OCEAN trait pairs (upper triangle).

    Positive value: traits tend to co-occur genetically.
    Negative value: traits tend to be inversely related genetically.

    The most important entry is `an` (Agreeableness–Neuroticism): -0.30.
    This means anxious populations tend toward hostility — not culturally,
    but as a biological tendency baked into the heritability structure.
    """
    oc: float = -0.10   # Openness–Conscientiousness
    oe: float =  0.05   # Openness–Extraversion
    oa: float =  0.10   # Openness–Agreeableness
    on: float = -0.05   # Openness–Neuroticism
    ce: float =  0.05   # Conscientiousness–Extraversion
    ca: float =  0.10   # Conscientiousness–Agreeableness
    cn: float = -0.15   # Conscientiousness–Neuroticism
    ea: float =  0.20   # Extraversion–Agreeableness
    en: float = -0.10   # Extraversion–Neuroticism
    an: float = -0.30   # Agreeableness–Neuroticism  ← most load-bearing


# ── Sub-sections ──────────────────────────────────────────────────────────────

@dataclass
class CognitiveParams:
    temporal_discounting_rate:  float = 0.72  # 0=patient, 1=extreme hyperbolic
    cognitive_load_ceiling:     float = 0.28  # 0=high capacity, 1=heuristic-dominant
    apophenia_coefficient:      float = 0.76  # 0=literal, 1=pattern-saturated
    loss_aversion_coefficient:  float = 2.30  # 1.0=symmetric; humans ~2.3
    dunbar_number:              int   = 150   # hard social tracking limit


@dataclass
class SocialParams:
    ingroup_detection_sensitivity:  float = 0.68  # 0=cosmopolitan, 1=hair-trigger tribal
    reciprocal_altruism_radius:     float = 0.45  # 0=kin-only, 1=diffuse altruism
    dominance_hierarchy_sensitivity: float = 0.71 # 0=rank-blind, 1=rank-saturated
    coalition_formation_instinct:   float = 0.74  # 0=transactional, 1=identity-fused


@dataclass
class StressParams:
    fight_weight:                   float = 0.38
    flight_weight:                  float = 0.42
    freeze_weight:                  float = 0.20
    stress_recovery_rate:           float = 0.18  # 0=instant, 1=permanent accumulation
    trauma_consolidation_threshold: float = 0.55  # 0=resilient, 1=easily marked


@dataclass
class DevelopmentParams:
    lifespan_years:                      int   = 80
    critical_period_sensitivity:         float = 0.72  # 0=even, 1=early years are destiny
    intergenerational_trauma_coefficient: float = 0.15  # 0=none, 0.5=strong echo

    # Stage proportions must sum to 1.0
    stage_development: float = 0.15
    stage_youth:       float = 0.15
    stage_adult:       float = 0.40
    stage_elder:       float = 0.20
    stage_terminal:    float = 0.10


# ── Top-level species substrate ───────────────────────────────────────────────

@dataclass
class SpeciesSubstrate:
    """
    Complete biological substrate for a species.

    This is the hardware. OCEAN distributions are the software running on it.
    Every individual of this species shares these parameters; they differ only
    in their position within the trait space the substrate defines.

    Instantiate from a TOML file with SpeciesSubstrate.from_toml(path),
    or build programmatically for testing.
    """
    name:        str = "Unnamed Species"
    version:     str = "0.1.0"
    description: str = ""

    cognitive:   CognitiveParams   = field(default_factory=CognitiveParams)
    social:      SocialParams      = field(default_factory=SocialParams)
    stress:      StressParams      = field(default_factory=StressParams)
    development: DevelopmentParams = field(default_factory=DevelopmentParams)
    heritability: OceanHeritability = field(default_factory=OceanHeritability)
    covariance:  OceanCovariance   = field(default_factory=OceanCovariance)

    # ── Validation ─────────────────────────────────────────────────────────────

    def __post_init__(self):
        self._validate()

    def _validate(self):
        c = self.cognitive
        s = self.social
        st = self.stress
        d = self.development
        h = self.heritability

        errors: list[str] = []

        def bounded(name, val, lo, hi):
            if not (lo <= val <= hi):
                errors.append(f"{name} = {val} is outside [{lo}, {hi}]")

        # Cognitive
        bounded("temporal_discounting_rate",  c.temporal_discounting_rate,  0.0, 1.0)
        bounded("cognitive_load_ceiling",     c.cognitive_load_ceiling,     0.0, 1.0)
        bounded("apophenia_coefficient",      c.apophenia_coefficient,      0.0, 1.0)
        bounded("loss_aversion_coefficient",  c.loss_aversion_coefficient,  1.0, 6.0)
        if c.dunbar_number < 5:
            errors.append(f"dunbar_number = {c.dunbar_number} is implausibly low (< 5)")

        # Social
        bounded("ingroup_detection_sensitivity",   s.ingroup_detection_sensitivity,   0.0, 1.0)
        bounded("reciprocal_altruism_radius",      s.reciprocal_altruism_radius,      0.0, 1.0)
        bounded("dominance_hierarchy_sensitivity", s.dominance_hierarchy_sensitivity, 0.0, 1.0)
        bounded("coalition_formation_instinct",    s.coalition_formation_instinct,    0.0, 1.0)

        # Stress
        bounded("stress_recovery_rate",           st.stress_recovery_rate,           0.0, 1.0)
        bounded("trauma_consolidation_threshold", st.trauma_consolidation_threshold, 0.0, 1.0)
        weight_sum = st.fight_weight + st.flight_weight + st.freeze_weight
        if not (0.99 <= weight_sum <= 1.01):
            errors.append(
                f"fight+flight+freeze weights sum to {weight_sum:.3f}, expected 1.0"
            )

        # Development
        bounded("critical_period_sensitivity",          d.critical_period_sensitivity,         0.0, 1.0)
        bounded("intergenerational_trauma_coefficient", d.intergenerational_trauma_coefficient, 0.0, 0.5)
        stage_sum = (d.stage_development + d.stage_youth + d.stage_adult
                     + d.stage_elder + d.stage_terminal)
        if not (0.99 <= stage_sum <= 1.01):
            errors.append(f"Stage proportions sum to {stage_sum:.3f}, expected 1.0")

        # Heritability
        for trait, val in h.as_dict().items():
            bounded(f"heritability.{trait}", val, 0.0, 1.0)

        if errors:
            raise ValueError(
                f"SpeciesSubstrate '{self.name}' failed validation:\n"
                + "\n".join(f"  · {e}" for e in errors)
            )

    # ── Factory methods ────────────────────────────────────────────────────────

    @classmethod
    def from_toml(cls, path: Path | str) -> "SpeciesSubstrate":
        """Load a species substrate from a TOML file (e.g. standard_human.toml)."""
        path = Path(path)
        with open(path, "rb") as f:
            data = tomllib.load(f)

        meta = data.get("meta", {})
        cog  = data.get("cognitive", {})
        soc  = data.get("social", {})
        st   = data.get("stress", {})
        dev  = data.get("development", {})
        her  = data.get("heritability", {})
        cov  = her.get("covariance", {})

        stage_props = dev.get("stage_proportions", {})

        return cls(
            name        = meta.get("name", path.stem),
            version     = meta.get("version", "0.1.0"),
            description = meta.get("description", ""),
            cognitive = CognitiveParams(
                temporal_discounting_rate  = cog.get("temporal_discounting_rate", 0.72),
                cognitive_load_ceiling     = cog.get("cognitive_load_ceiling",    0.28),
                apophenia_coefficient      = cog.get("apophenia_coefficient",     0.76),
                loss_aversion_coefficient  = cog.get("loss_aversion_coefficient", 2.30),
                dunbar_number              = int(cog.get("dunbar_number",         150)),
            ),
            social = SocialParams(
                ingroup_detection_sensitivity   = soc.get("ingroup_detection_sensitivity",   0.68),
                reciprocal_altruism_radius      = soc.get("reciprocal_altruism_radius",      0.45),
                dominance_hierarchy_sensitivity = soc.get("dominance_hierarchy_sensitivity", 0.71),
                coalition_formation_instinct    = soc.get("coalition_formation_instinct",    0.74),
            ),
            stress = StressParams(
                fight_weight                   = st.get("fight_weight",                   0.38),
                flight_weight                  = st.get("flight_weight",                  0.42),
                freeze_weight                  = st.get("freeze_weight",                  0.20),
                stress_recovery_rate           = st.get("stress_recovery_rate",           0.18),
                trauma_consolidation_threshold = st.get("trauma_consolidation_threshold", 0.55),
            ),
            development = DevelopmentParams(
                lifespan_years                      = int(dev.get("lifespan_years", 80)),
                critical_period_sensitivity         = dev.get("critical_period_sensitivity",         0.72),
                intergenerational_trauma_coefficient= dev.get("intergenerational_trauma_coefficient",0.15),
                stage_development = stage_props.get("development", 0.15),
                stage_youth       = stage_props.get("youth",       0.15),
                stage_adult       = stage_props.get("adult",       0.40),
                stage_elder       = stage_props.get("elder",       0.20),
                stage_terminal    = stage_props.get("terminal",    0.10),
            ),
            heritability = OceanHeritability(
                openness          = her.get("openness",          0.57),
                conscientiousness = her.get("conscientiousness", 0.49),
                extraversion      = her.get("extraversion",      0.54),
                agreeableness     = her.get("agreeableness",     0.42),
                neuroticism       = her.get("neuroticism",       0.48),
            ),
            covariance = OceanCovariance(
                oc = cov.get("oc", -0.10),
                oe = cov.get("oe",  0.05),
                oa = cov.get("oa",  0.10),
                on = cov.get("on", -0.05),
                ce = cov.get("ce",  0.05),
                ca = cov.get("ca",  0.10),
                cn = cov.get("cn", -0.15),
                ea = cov.get("ea",  0.20),
                en = cov.get("en", -0.10),
                an = cov.get("an", -0.30),
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to a flat dict suitable for passing to Python api functions."""
        c = self.cognitive
        s = self.social
        st = self.stress
        d = self.development
        h = self.heritability
        cv = self.covariance
        return {
            "name": self.name,
            "cognitive": {
                "temporal_discounting_rate":  c.temporal_discounting_rate,
                "cognitive_load_ceiling":     c.cognitive_load_ceiling,
                "apophenia_coefficient":      c.apophenia_coefficient,
                "loss_aversion_coefficient":  c.loss_aversion_coefficient,
                "dunbar_number":              c.dunbar_number,
            },
            "social": {
                "ingroup_detection_sensitivity":   s.ingroup_detection_sensitivity,
                "reciprocal_altruism_radius":      s.reciprocal_altruism_radius,
                "dominance_hierarchy_sensitivity": s.dominance_hierarchy_sensitivity,
                "coalition_formation_instinct":    s.coalition_formation_instinct,
            },
            "stress": {
                "fight_weight":                   st.fight_weight,
                "flight_weight":                  st.flight_weight,
                "freeze_weight":                  st.freeze_weight,
                "stress_recovery_rate":           st.stress_recovery_rate,
                "trauma_consolidation_threshold": st.trauma_consolidation_threshold,
            },
            "development": {
                "lifespan_years":                       d.lifespan_years,
                "critical_period_sensitivity":          d.critical_period_sensitivity,
                "intergenerational_trauma_coefficient": d.intergenerational_trauma_coefficient,
            },
            "heritability": h.as_dict(),
            "covariance": {
                "oc": cv.oc, "oe": cv.oe, "oa": cv.oa, "on": cv.on,
                "ce": cv.ce, "ca": cv.ca, "cn": cv.cn,
                "ea": cv.ea, "en": cv.en, "an": cv.an,
            },
        }
