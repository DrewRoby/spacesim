"""
CV signal types — the Python mirror of sim/types/src/signals.rs.

All signals are normalized floats. Trait signals: [0.0, 1.0].
Signed signals (e.g. emotional valence): [-1.0, 1.0].

These dataclasses are the currency that all behavioral modules exchange.
Any module output can feed any module input as long as it speaks this language.
"""

from dataclasses import dataclass, field
from typing import NewType

# A single normalized control-voltage signal
Cv = NewType("Cv", float)


@dataclass
class OceanSignals:
    """The five OCEAN trait signals output by a TraitModule."""
    openness:          Cv = Cv(0.5)
    conscientiousness: Cv = Cv(0.5)
    extraversion:      Cv = Cv(0.5)
    agreeableness:     Cv = Cv(0.5)
    neuroticism:       Cv = Cv(0.5)

    def as_dict(self) -> dict[str, float]:
        return {
            "openness":          self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion":      self.extraversion,
            "agreeableness":     self.agreeableness,
            "neuroticism":       self.neuroticism,
        }


@dataclass
class NeedUrgencies:
    """Urgency signals from the NeedsEngine — one per Maslow tier."""
    survival:      Cv = Cv(0.0)
    security:      Cv = Cv(0.0)
    belonging:     Cv = Cv(0.0)
    esteem:        Cv = Cv(0.0)
    transcendence: Cv = Cv(0.0)


@dataclass
class DemandVector:
    """
    Market demand signal produced by the Priority Mixer.
    Maps commodity id → normalized demand pressure [0.0, 1.0].
    """
    commodities: dict[str, Cv] = field(default_factory=dict)
