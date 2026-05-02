"""
spacesim_models.substrate
~~~~~~~~~~~~~~~~~~~~~~~~~~
Species biological substrate — the hardware layer beneath OCEAN.
"""

from .species import (
    SpeciesSubstrate,
    CognitiveParams,
    SocialParams,
    StressParams,
    DevelopmentParams,
    OceanHeritability,
    OceanCovariance,
)
from .propensities import (
    Propensities,
    compute_propensities,
)

__all__ = [
    "SpeciesSubstrate",
    "CognitiveParams",
    "SocialParams",
    "StressParams",
    "DevelopmentParams",
    "OceanHeritability",
    "OceanCovariance",
    "Propensities",
    "compute_propensities",
]
