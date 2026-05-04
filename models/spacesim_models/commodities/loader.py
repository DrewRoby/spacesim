"""
spacesim_models.commodities.loader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Loads commodity profiles from TOML files.

A CommodityProfile is the static definition of what a commodity satisfies
and by how much per unit consumed. It is the other half of the demand
matrix — need states provide the urgency row, commodity profiles provide
the satisfaction column.

Moddability: point load_commodity_dir() at any directory of *.toml files
that follow the [[commodity]] format and they will be loaded without code
changes.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CommodityProfile:
    """
    Static definition of one commodity.

    satisfies      maps need_id → satisfaction per unit [0.0, 1.0].
    base_supply    daily per-capita supply in normalized units [0.0, 1.0].
                   Used by market clearing to compute equilibrium prices.
    """
    id:          str
    name:        str
    description: str
    satisfies:   dict[str, float] = field(default_factory=dict)
    base_supply: float = 0.0


def load_commodity_file(toml_path: Path | str) -> list[CommodityProfile]:
    """Load all [[commodity]] entries from a single TOML file."""
    path = Path(toml_path)
    with open(path, "rb") as f:
        data = tomllib.load(f)

    profiles = []
    for entry in data.get("commodity", []):
        profiles.append(CommodityProfile(
            id          = entry["id"],
            name        = entry["name"],
            description = entry.get("description", ""),
            satisfies   = {k: float(v) for k, v in entry.get("satisfies", {}).items()},
            base_supply = float(entry.get("base_supply", 0.0)),
        ))
    return profiles


def load_commodity_dir(directory: Path | str) -> list[CommodityProfile]:
    """Load all *.toml files from a directory as commodity profiles."""
    directory = Path(directory)
    profiles: list[CommodityProfile] = []
    for toml_file in sorted(directory.glob("*.toml")):
        profiles.extend(load_commodity_file(toml_file))
    return profiles
