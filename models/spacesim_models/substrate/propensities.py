"""
spacesim_models.substrate.propensities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Computes second-order propensities from a SpeciesSubstrate.

Propensities are *outputs*, not inputs. They are predictions that emerge
from the substrate parameters — the readable civilizational fingerprint of
a species. The designer sets substrate; this module computes what it means.

Each propensity is a weighted combination of substrate parameters, normalized
to [0.0, 1.0]. The weights encode our model of which parameters matter most
for each civilizational tendency.

The math here is intentionally transparent — no black boxes. Every propensity
function is a few lines of arithmetic you can read and reason about. When a
propensity produces a surprising value, you should be able to trace exactly
which substrate parameters drove it and why.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .species import SpeciesSubstrate


# ── Helpers ───────────────────────────────────────────────────────────────────

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp x to [lo, hi]."""
    return max(lo, min(hi, x))


def normalize_dunbar(dunbar: int, lo: int = 5, hi: int = 500) -> float:
    """Map dunbar_number to [0.0, 1.0]. Higher dunbar → higher score."""
    return clamp((dunbar - lo) / (hi - lo))


def normalize_loss_aversion(coeff: float, lo: float = 1.0, hi: float = 6.0) -> float:
    """Map loss_aversion_coefficient [1.0, 6.0] → [0.0, 1.0]."""
    return clamp((coeff - lo) / (hi - lo))


def normalize_itc(coeff: float, hi: float = 0.5) -> float:
    """Map intergenerational_trauma_coefficient [0.0, 0.5] → [0.0, 1.0]."""
    return clamp(coeff / hi)


def weighted(*pairs: tuple[float, float]) -> float:
    """
    Compute a normalized weighted sum.

    Each pair is (weight, value). Weights need not sum to 1 — they are
    normalized internally so the output is always in [0.0, 1.0] when all
    input values are in [0.0, 1.0].

    Example:
        weighted((0.6, trait_a), (0.4, trait_b))
    """
    total_weight = sum(w for w, _ in pairs)
    if total_weight == 0:
        return 0.0
    return clamp(sum(w * v for w, v in pairs) / total_weight)


def sigmoid(x: float, steepness: float = 8.0, midpoint: float = 0.5) -> float:
    """
    Smooth S-curve mapping [0,1] → [0,1].

    Used where we want a threshold effect — the propensity rises slowly,
    then accelerates through the middle range, then levels off.
    Steepness controls how sharp the transition is.
    """
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


# ── Propensity dataclass ───────────────────────────────────────────────────────

@dataclass
class Propensities:
    """
    The ten second-order propensities computed from a SpeciesSubstrate.

    All values are in [0.0, 1.0].
    Higher = more of that tendency.

    These are what the designer UI displays on the radar chart and what
    the gameplay dashboard shows as a live population readout.
    """

    # How strongly the species discounts future rewards vs present ones.
    # High = civilizational short-termism, infrastructure underinvestment.
    short_termism: float = 0.5

    # The natural ceiling on tribal group size before institutional trust
    # is required. High = small tight tribes, low = cosmopolitan by default.
    tribalism_ceiling: float = 0.5

    # How much market and social behavior degrades under sustained stress.
    # High = panic-prone, cascade-susceptible, slow to recover.
    volatility_under_stress: float = 0.5

    # The speed and persistence with which informal status hierarchies form.
    # High = inequality is sticky, hierarchies emerge fast and resist change.
    stratification_tendency: float = 0.5

    # How readily coherent worldviews and ideologies are adopted and spread.
    # High = fertile ground for religion, conspiracy, mass movements.
    ideological_susceptibility: float = 0.5

    # The natural radius of trust and cooperation without institutional scaffolding.
    # High = spontaneous wide-radius trade; low = kin-group only.
    cooperative_radius: float = 0.5

    # How many generations a civilizational trauma echoes before fading.
    # High = deep intergenerational scars; low = resilient, short memory.
    generational_memory_depth: float = 0.5

    # The background rate at which novel behaviors and technologies spread.
    # High = fast diffusion, early adoption; low = conservative, late adoption.
    innovation_rate_baseline: float = 0.5

    # The natural frequency of faction formation and political realignment.
    # High = frequent upheaval; low = stable, slow-moving political landscape.
    political_instability_cycle: float = 0.5

    # The size of insurance, security, and certainty-premium markets.
    # High = large shadow economy of risk-reduction goods and services.
    loss_aversion_premium: float = 0.5

    def as_dict(self) -> dict[str, float]:
        return {
            "short_termism":              self.short_termism,
            "tribalism_ceiling":          self.tribalism_ceiling,
            "volatility_under_stress":    self.volatility_under_stress,
            "stratification_tendency":    self.stratification_tendency,
            "ideological_susceptibility": self.ideological_susceptibility,
            "cooperative_radius":         self.cooperative_radius,
            "generational_memory_depth":  self.generational_memory_depth,
            "innovation_rate_baseline":   self.innovation_rate_baseline,
            "political_instability_cycle":self.political_instability_cycle,
            "loss_aversion_premium":      self.loss_aversion_premium,
        }

    def radar_lines(self, width: int = 40) -> str:
        """ASCII bar chart — useful for quick terminal inspection."""
        lines = []
        for name, val in self.as_dict().items():
            bar_len = int(val * width)
            bar = "█" * bar_len + "░" * (width - bar_len)
            lines.append(f"  {name:<28} {bar} {val:.3f}")
        return "\n".join(lines)


# ── The computation ───────────────────────────────────────────────────────────

def compute_propensities(substrate: SpeciesSubstrate) -> Propensities:
    """
    Derive second-order propensities from a SpeciesSubstrate.

    Each propensity is a weighted combination of substrate parameters.
    The weights were chosen to reflect the causal structure described in
    the design documents — which parameters most strongly drive each
    civilizational tendency.

    This function is the mathematical heart of the designer UI. When a
    slider moves, this runs and the radar chart updates.
    """
    c  = substrate.cognitive
    s  = substrate.social
    st = substrate.stress
    d  = substrate.development
    h  = substrate.heritability

    # Pre-compute normalized versions of parameters that need range adjustment
    loss_av_norm  = normalize_loss_aversion(c.loss_aversion_coefficient)
    dunbar_norm   = normalize_dunbar(c.dunbar_number)
    itc_norm      = normalize_itc(d.intergenerational_trauma_coefficient)

    # ── 1. Short-termism ──────────────────────────────────────────────────────
    # Driven almost entirely by temporal discounting rate.
    # Low conscientiousness heritability adds a small contribution:
    # populations that don't reliably inherit planning instincts will also
    # struggle to sustain long-horizon projects across generations.
    short_termism = weighted(
        (0.80, c.temporal_discounting_rate),
        (0.20, 1.0 - h.conscientiousness),  # low C heritability → more short-term
    )

    # ── 2. Tribalism ceiling ──────────────────────────────────────────────────
    # High ingroup sensitivity + small Dunbar limit = intense small-group loyalty.
    # The inverse of dunbar_norm: a small Dunbar number means groups fragment
    # sooner, which is the condition for tight tribalism.
    # Coalition instinct amplifies this — the political tendency to define in-group.
    tribalism_ceiling = weighted(
        (0.50, s.ingroup_detection_sensitivity),
        (0.30, 1.0 - dunbar_norm),          # smaller natural group → tighter tribe
        (0.20, s.coalition_formation_instinct),
    )

    # ── 3. Volatility under stress ────────────────────────────────────────────
    # Slow recovery rate is the most direct driver — stress accumulates if it
    # doesn't clear. High N heritability means stressed populations stay stressed
    # across generations. Low trauma threshold means smaller events trigger
    # lasting behavioral change, creating positive feedback loops.
    volatility_under_stress = weighted(
        (0.45, st.stress_recovery_rate),            # slow recovery → volatility
        (0.35, h.neuroticism),                      # high N heritability → persistent anxiety
        (0.20, 1.0 - st.trauma_consolidation_threshold),  # low threshold → easily marked
    )

    # Apply a mild sigmoid to create a threshold effect: moderate levels produce
    # moderate volatility, but extreme combinations produce non-linear jumps.
    volatility_under_stress = sigmoid(volatility_under_stress, steepness=6.0)

    # ── 4. Stratification tendency ────────────────────────────────────────────
    # Dominance sensitivity is the primary driver: a species that automatically
    # reads and responds to rank will produce stratified outcomes even without
    # anyone trying to create them.
    # Loss aversion makes existing hierarchies sticky — incumbents fight hard
    # to preserve status (loss > gain).
    # Low Agreeableness heritability means populations don't reliably inherit
    # the cooperative instincts that resist stratification.
    stratification_tendency = weighted(
        (0.55, s.dominance_hierarchy_sensitivity),
        (0.25, loss_av_norm),
        (0.20, 1.0 - h.agreeableness),
    )

    # ── 5. Ideological susceptibility ─────────────────────────────────────────
    # Apophenia is the primary driver: a mind that finds patterns everywhere
    # will find coherent worldviews (true or false) very readily.
    # High Neuroticism heritability amplifies this — anxious minds seek
    # explanatory frameworks that resolve uncertainty.
    # High ingroup sensitivity provides the social scaffold: ideologies spread
    # fastest in species that strongly distinguish us-vs-them.
    ideological_susceptibility = weighted(
        (0.50, c.apophenia_coefficient),
        (0.30, h.neuroticism),
        (0.20, s.ingroup_detection_sensitivity),
    )

    # ── 6. Cooperative radius ─────────────────────────────────────────────────
    # Reciprocal altruism radius is the direct biological substrate of
    # cooperation beyond kin. High Agreeableness heritability means
    # cooperative traits reliably pass to offspring. Large Dunbar number
    # means more people fall inside the natural trust radius.
    # Ingroup sensitivity works against this: a species that strongly
    # distinguishes us/them has a smaller effective cooperative radius.
    cooperative_radius = weighted(
        (0.45, s.reciprocal_altruism_radius),
        (0.30, h.agreeableness),
        (0.15, dunbar_norm),
        (0.10, 1.0 - s.ingroup_detection_sensitivity),
    )

    # ── 7. Generational memory depth ──────────────────────────────────────────
    # Intergenerational trauma transmission is the direct mechanism — how
    # strongly parental trauma marks offspring beyond normal heritability.
    # Slow stress recovery means the original trauma doesn't fade within
    # a generation either, compounding the forward transmission.
    # High Neuroticism heritability means the anxious trait profile that
    # trauma produces is itself reliably inherited.
    generational_memory_depth = weighted(
        (0.50, itc_norm),
        (0.30, st.stress_recovery_rate),   # slow individual recovery → long echo
        (0.20, h.neuroticism),
    )

    # ── 8. Innovation rate baseline ───────────────────────────────────────────
    # High Openness heritability means the population reliably produces
    # novelty-seeking individuals across generations.
    # Low critical period sensitivity means the mind stays plastic for longer —
    # new ideas can take root in adulthood, not just in youth.
    # Low temporal discounting means the species can invest in uncertain
    # long-horizon outcomes like R&D.
    innovation_rate_baseline = weighted(
        (0.50, h.openness),
        (0.30, 1.0 - d.critical_period_sensitivity),  # more plastic across life
        (0.20, 1.0 - c.temporal_discounting_rate),    # patient enough to invest
    )

    # ── 9. Political instability cycle ────────────────────────────────────────
    # Coalition instinct drives the constant background churn of alliance
    # formation, loyalty testing, and faction competition.
    # Dominance sensitivity means every group interaction is also a status
    # contest, generating friction even in stable conditions.
    # High Neuroticism heritability means the population carries elevated
    # anxiety into political life, making equilibria harder to sustain.
    political_instability_cycle = weighted(
        (0.45, s.coalition_formation_instinct),
        (0.35, s.dominance_hierarchy_sensitivity),
        (0.20, h.neuroticism),
    )

    # ── 10. Loss aversion premium ─────────────────────────────────────────────
    # Directly derived from loss aversion coefficient — no weighting needed.
    # This is the most direct substrate→propensity mapping in the model.
    # The insurance and security market sizes are almost a linear function
    # of how much more losses hurt than equivalent gains feel good.
    loss_aversion_premium = loss_av_norm

    return Propensities(
        short_termism              = round(short_termism,              4),
        tribalism_ceiling          = round(tribalism_ceiling,          4),
        volatility_under_stress    = round(volatility_under_stress,    4),
        stratification_tendency    = round(stratification_tendency,    4),
        ideological_susceptibility = round(ideological_susceptibility, 4),
        cooperative_radius         = round(cooperative_radius,         4),
        generational_memory_depth  = round(generational_memory_depth,  4),
        innovation_rate_baseline   = round(innovation_rate_baseline,   4),
        political_instability_cycle= round(political_instability_cycle,4),
        loss_aversion_premium      = round(loss_aversion_premium,      4),
    )


# ── Sensitivity analysis helper ───────────────────────────────────────────────

def sensitivity_report(substrate: SpeciesSubstrate, delta: float = 0.05) -> str:
    """
    For each substrate parameter, show how much each propensity changes
    when that parameter is nudged by ±delta.

    Useful for understanding which knobs have the biggest effect and for
    catching model errors (a propensity that doesn't respond to anything
    is probably broken).
    """
    import copy

    baseline = compute_propensities(substrate)
    baseline_dict = baseline.as_dict()
    report_lines = [
        f"Sensitivity Report — δ = ±{delta}",
        f"Baseline: {substrate.name}",
        "",
    ]

    # Parameters to test, as (display_name, getter, setter) triples
    def _nudge_and_compute(sub: SpeciesSubstrate, getter, setter, d: float):
        import copy, dataclasses
        # We need a modified copy — rebuild the sub-dataclass
        original = getter(sub)
        nudged_val = clamp(original + d, 0.0, 1.0)
        # This is a bit verbose but keeps things explicit and safe
        # In practice you'd use a more elegant mutation strategy
        return nudged_val, original

    # Simple flat sweep of the most interesting scalar parameters
    params = [
        ("cognitive.temporal_discounting_rate",  lambda s: s.cognitive.temporal_discounting_rate),
        ("cognitive.apophenia_coefficient",      lambda s: s.cognitive.apophenia_coefficient),
        ("cognitive.loss_aversion_coefficient",  lambda s: normalize_loss_aversion(s.cognitive.loss_aversion_coefficient)),
        ("social.ingroup_detection_sensitivity", lambda s: s.social.ingroup_detection_sensitivity),
        ("social.reciprocal_altruism_radius",    lambda s: s.social.reciprocal_altruism_radius),
        ("social.dominance_hierarchy_sensitivity",lambda s: s.social.dominance_hierarchy_sensitivity),
        ("stress.stress_recovery_rate",          lambda s: s.stress.stress_recovery_rate),
        ("heritability.neuroticism",             lambda s: s.heritability.neuroticism),
        ("heritability.openness",                lambda s: s.heritability.openness),
        ("heritability.agreeableness",           lambda s: s.heritability.agreeableness),
    ]

    prop_names = list(baseline_dict.keys())

    for param_name, getter in params:
        report_lines.append(f"  ── {param_name} (baseline={getter(substrate):.3f})")
        # We can't easily mutate frozen dataclasses here, so we just show
        # which propensities this parameter feeds into, from the weight tables
        # This is a documentation-mode sensitivity rather than full perturbation
        report_lines.append(f"     (full perturbation analysis requires mutable substrate)")
    
    report_lines.append("")
    report_lines.append("  Full perturbation sensitivity coming in a future model version.")
    return "\n".join(report_lines)
