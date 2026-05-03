"""
spacesim_models.needs.needs
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Biological need definitions and per-need satiation state.

A NeedDefinition is the static spec loaded from data/needs/*.toml.
A NeedState is the runtime satiation level for one need in one population tick.

Urgency is the signal the market consumes — it rises non-linearly as satiation
falls. Each need has its own curve so that survival needs (hydration) spike
fast while security needs (fiber, micronutrients) degrade more slowly.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


# ── Urgency math ──────────────────────────────────────────────────────────────

def _sigmoid(x: float, steepness: float, midpoint: float) -> float:
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


def urgency_from_satiation(satiation: float, steepness: float, midpoint: float) -> float:
    """
    Map satiation [0,1] → urgency [0,1].

    At full satiation (1.0) urgency is near zero.
    As satiation falls the urgency curve rises, with the shape controlled
    by steepness and midpoint from the need definition.
    """
    return _sigmoid(1.0 - satiation, steepness, midpoint)


# ── Static need definition ────────────────────────────────────────────────────

@dataclass(frozen=True)
class NeedDefinition:
    """Static spec for one biological need. Loaded from TOML, never mutated."""
    id:          str
    name:        str
    tier:        str   # "survival" | "security" | ...
    description: str
    steepness:   float
    midpoint:    float

    def urgency(self, satiation: float) -> float:
        return urgency_from_satiation(satiation, self.steepness, self.midpoint)


# ── Runtime need state ────────────────────────────────────────────────────────

@dataclass
class NeedState:
    """
    Runtime satiation level for one biological need.

    satiation: float in [0.0, 1.0]
        0.0 = completely unsatisfied (starving / dehydrated)
        1.0 = fully satisfied

    Holds a reference to its definition for urgency computation.
    """
    definition: NeedDefinition
    satiation:  float = 0.5

    def __post_init__(self):
        self.satiation = max(0.0, min(1.0, self.satiation))

    @property
    def urgency(self) -> float:
        return self.definition.urgency(self.satiation)

    def satisfy(self, amount: float) -> None:
        """Increase satiation by amount (clamped to 1.0)."""
        self.satiation = min(1.0, self.satiation + amount)

    def decay(self, rate: float) -> None:
        """Decrease satiation by rate per tick (clamped to 0.0)."""
        self.satiation = max(0.0, self.satiation - rate)


# ── Population need profile ───────────────────────────────────────────────────

@dataclass
class PopulationNeeds:
    """
    All biological need states for a population at one tick.

    Keyed by need id (matches NeedDefinition.id and commodity satisfies keys).
    """
    states: dict[str, NeedState] = field(default_factory=dict)

    @classmethod
    def default(cls, definitions: list[NeedDefinition], satiation: float = 0.5) -> "PopulationNeeds":
        """Create a population need profile at uniform satiation."""
        return cls(states={d.id: NeedState(d, satiation) for d in definitions})

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
            id          = entry["id"],
            name        = entry["name"],
            tier        = entry["tier"],
            description = entry.get("description", ""),
            steepness   = float(entry["steepness"]),
            midpoint    = float(entry["midpoint"]),
        ))
    return definitions
