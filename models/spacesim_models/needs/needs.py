"""
spacesim_models.needs.needs
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Biological need definitions and per-need satiation state.

A NeedDefinition is the static spec loaded from data/needs/*.toml.
A NeedState is the runtime satiation *distribution* for one need across a
population — a mean and variance rather than a single scalar.

Why a distribution? Different individuals within a population satisfy their
needs at different rates depending on income, location, OCEAN traits, and
luck. Modeling the spread matters: a population where half are dehydrated
and half are fine produces much higher water urgency than one where everyone
is at 50% satiation, even though the means are identical.

Urgency is computed as the expected urgency across the distribution using a
second-order Taylor expansion — analytically exact for the sigmoid, no
external dependencies required.

    E[f(s)] ≈ f(μ) + ½f″(μ)σ²

where f(s) = sigmoid(1−s, steepness, midpoint).
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


# ── Urgency math ──────────────────────────────────────────────────────────────

def _sigmoid(x: float, steepness: float, midpoint: float) -> float:
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


def urgency_from_distribution(
    mean: float,
    variance: float,
    steepness: float,
    midpoint: float,
) -> float:
    """
    Expected urgency for a population whose satiation is distributed N(mean, variance).

    Uses a second-order Taylor expansion around the mean:
        E[urgency(s)] ≈ urgency(mean) + ½ · urgency″(mean) · variance

    The second derivative of sigmoid(1−s, k, m) with respect to s is:
        f″ = k² · f · (1−f) · (2f−1)

    The variance term is positive when mean urgency is below 0.5 (most of the
    population comfortable) and flips sign above 0.5 — correctly inflating
    urgency for heterogeneous populations under duress.

    Clamps to [0, 1].
    """
    u = 1.0 - mean  # transform: urgency rises as satiation falls
    s = _sigmoid(u, steepness, midpoint)

    # Second derivative of sigmoid w.r.t. input, then chain rule for 1-mean
    # d/ds sigmoid(1-s) = -k·s·(1-s)
    # d²/ds² sigmoid(1-s) = k²·s·(1-s)·(2s-1)
    second_derivative = steepness ** 2 * s * (1.0 - s) * (2.0 * s - 1.0)

    expected = s + 0.5 * second_derivative * variance
    return max(0.0, min(1.0, expected))


# ── Static need definition ────────────────────────────────────────────────────

@dataclass(frozen=True)
class NeedDefinition:
    """Static spec for one biological need. Loaded from TOML, never mutated."""
    id:                 str
    name:               str
    tier:               str   # "survival" | "security" | ...
    description:        str
    steepness:          float
    midpoint:           float
    decay_rate_per_day: float  # mean satiation lost per day at zero supply

    def urgency(self, mean: float, variance: float) -> float:
        return urgency_from_distribution(mean, variance, self.steepness, self.midpoint)


# ── Runtime need state ────────────────────────────────────────────────────────

@dataclass
class NeedState:
    """
    Runtime satiation *distribution* for one biological need across a population.

    mean     : average satiation across the population [0.0, 1.0]
    variance : spread of satiation across individuals [0.0, 0.25]
               0.0 = everyone identical
               0.25 = maximum meaningful spread (σ = 0.5 on a [0,1] scale)

    A mean of 0.5 with variance 0.1 means most people are around half-satisfied,
    with a standard deviation of ~0.32 — some hungry, some comfortable.

    A mean of 0.5 with variance 0.0 means every person is at exactly 50%.

    The urgency signal integrates across the distribution, so a heterogeneous
    population (high variance) under deprivation (low mean) produces stronger
    demand than the mean alone would suggest.
    """
    definition: NeedDefinition
    mean:       float = 0.5
    variance:   float = 0.10

    def __post_init__(self):
        self.mean     = max(0.0, min(1.0, self.mean))
        self.variance = max(0.0, min(0.25, self.variance))

    @property
    def urgency(self) -> float:
        return self.definition.urgency(self.mean, self.variance)

    def satisfy(self, amount: float) -> None:
        """Shift the mean up by amount. Variance narrows slightly as people converge."""
        self.mean     = min(1.0, self.mean + amount)
        self.variance = max(0.0, self.variance * 0.95)

    def decay(self, rate: float) -> None:
        """Shift the mean down by rate. Variance widens as people deplete unevenly."""
        self.mean     = max(0.0, self.mean - rate)
        self.variance = min(0.25, self.variance * 1.02)


# ── Population need profile ───────────────────────────────────────────────────

@dataclass
class PopulationNeeds:
    """
    All biological need states for a population at one tick.

    Keyed by need id (matches NeedDefinition.id and commodity satisfies keys).
    """
    states: dict[str, NeedState] = field(default_factory=dict)

    @classmethod
    def default(
        cls,
        definitions: list[NeedDefinition],
        mean: float = 0.5,
        variance: float = 0.10,
    ) -> "PopulationNeeds":
        """Create a population need profile at uniform mean and variance."""
        return cls(states={
            d.id: NeedState(d, mean, variance) for d in definitions
        })

    def urgency_vector(self) -> dict[str, float]:
        """Return {need_id: urgency} for all needs."""
        return {nid: s.urgency for nid, s in self.states.items()}


# ── TOML loader ───────────────────────────────────────────────────────────────

def load_need_definitions(toml_path: Path | str) -> list[NeedDefinition]:
    """Load need definitions from a TOML file (e.g. data/needs/biological_needs.toml)."""
    path = Path(toml_path)
    with open(path, "rb") as f:
        data = tomllib.load(f)

    definitions = []
    for entry in data.get("need", []):
        definitions.append(NeedDefinition(
            id                 = entry["id"],
            name               = entry["name"],
            tier               = entry["tier"],
            description        = entry.get("description", ""),
            steepness          = float(entry["steepness"]),
            midpoint           = float(entry["midpoint"]),
            decay_rate_per_day = float(entry.get("decay_rate_per_day", 0.03)),
        ))
    return definitions
