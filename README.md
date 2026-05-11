# spacesim
A generic-y persistent-y shooter-y space-sim-thingy.

OR

A space exploration and economic simulation where human psychology drives
everything downstream. Rather than scripting economic behaviors directly,
populations are modeled as distributions of psychological traits. Markets,
factions, political structures, and exploration incentives emerge from the
aggregate wants, fears, and values of simulated people — not from hand-authored
rules.

The player operates in this world as a real actor with real leverage, but not
omnipotent control. Moving a market means moving the people behind it.

---

## Design Philosophy

This project is built to be explored as much as played. The major architectural
decisions were made to answer big questions with systems and leave room within
those systems to experiment:

**Answer big questions with systems.** While the story mode will have pre-
determined races and worlds, their interactions and most events (  ;D  ) will
be determined by a living, breathing market system. In the creative mode, of course,
there is no end of customization. Rather than deciding what factions will
exist, we model the psychology that produces factions. Rather than scripting
market behavior, we model the needs that drive demand. The interesting content
is meant to emerge, not be authored.

**Leave room to experiment.** Every component of the behavioral model is
designed to be independently swappable — a modular synthesizer rather than a
fixed instrument. Personality modules, need curves, decision models, and
demographic engines are all defined at clean interfaces so any of them can be
replaced, tuned, or mocked without touching the rest of the system.

**Defer decisions you don't have to make yet.** The architecture commits to
clear boundaries between layers, but leaves the logic within each layer open.
Stub implementations are first-class citizens during development — they let the
whole pipeline run while individual components are still being designed.

---

## Stack

| Layer | Technology | Role |
|---|---|---|
| Behavioral modeling | Python | Personality math, needs engine, orbital physics, demographic model |
| Simulation engine | Rust | Tick loop, market clearing, world state, agent decisions |
| Game frontend | Godot 4 | Rendering, UI, input, IPC client |
| Asset pipeline | Meshy → Blender → Godot | AI-generated 3D assets, cleanup, import |
| Game data | TOML | Species, stellar bodies, commodities, events — owned by nobody, read by everyone |

The three layers are independently runnable. The Python model runs and tests
without Rust. The Rust sim runs headless without Godot. Godot can display mock
data without a live sim.

---

## Repository Layout

```
spacesim/
├── sim/                    # Rust workspace (5 crates)
│   ├── types/              # Shared types — no logic, imported by everything
│   ├── core/               # Tick engine, world state, market clearing
│   ├── ipc/                # IPC TCP server (Rust ↔ Godot, port 7777)
│   ├── bindings/           # PyO3 bindings (Rust ↔ Python bridge)
│   └── cli/                # Headless runner — dev, test, and IPC host tool
├── models/                 # Python behavioral model package
│   └── spacesim_models/
│       ├── substrate/      # Species biological substrate + propensity math
│       ├── needs/          # Maslow-derived needs hierarchy and urgency curves
│       ├── commodities/    # Commodity loading and satisfaction profiles
│       ├── orbital/        # Orbital mechanics, insolation physics, seasonal cycles
│       │   ├── star.py     # StarDefinition, habitable zone, UV flux
│       │   ├── planet.py   # PlanetDefinition, derived orbital parameters
│       │   ├── insolation.py  # Kepler solver, T_eq, habitability scoring
│       │   ├── season.py   # SeasonalCycle, supply modifiers by commodity category
│       │   └── pressure.py # EvolutionaryPressure → SpeciesSubstrate mapping
│       └── api.py          # The only surface Rust calls into
├── game/                   # Godot 4 project
│   ├── scenes/             # Main.tscn, MarketBoard.tscn, NeedsPanel.tscn
│   └── scripts/            # SimClient.gd (autoload), MarketBoard.gd, NeedsPanel.gd, Main.gd
├── data/                   # Shared game configuration (TOML)
│   ├── species/            # standard_human, terminator_dweller, feast_famine_dweller
│   ├── bodies/             # sol, earth, red_dwarf, terminator_world,
│   │                       #   orange_dwarf, feast_famine_world
│   ├── commodities/        # 19 commodities across 6 category files
│   ├── needs/              # biological_needs.toml (7 needs, 2 tiers)
│   └── events/             # Probabilistic event templates (not yet implemented)
├── tests/                  # Shell-based test suite
│   ├── lib.sh              # assert_python helper
│   ├── run_all.sh          # Runs all suites
│   └── python/             # 8 test suites, ~100 assertions
└── docs/                   # Design documents
```

---

## The Model

### Layer 0: Orbital Physics → Evolutionary Pressure

Before species, planets have physics. The `orbital` package computes:

- **Stellar parameters:** luminosity, habitable zone bounds, UV flux
- **Planetary parameters:** equilibrium temperature, surface temperature,
  seasonal amplitude, growing season fraction
- **Habitability score:** geometric mean of 7 Gaussian subscores (temperature,
  gravity, pressure, oxygen, radiation, water, tidal lock) — Earth ≈ 1.0
- **Seasonal supply modifiers:** per-commodity multipliers each tick based on
  whether the planet is in growing season (agricultural drops to 0.20× floor
  in deep winter; baseline goods are always 1.0×)
- **Evolutionary pressure:** 6-dimensional vector (resource\_volatility,
  thermal\_danger, survival\_scarcity, cognitive\_demand, group\_dependence,
  predation\_proxy) derived from orbital parameters, used to seed species
  substrate values via calibrated linear formulas

Reference bodies: `sol.toml` + `earth.toml`. Included variants:
- **Red dwarf + terminator world** — tidally locked M4V rocky world at 0.065 AU;
  low seasonal volatility, high group dependence, year-round growing strip
- **Orange dwarf + feast-famine world** — high-eccentricity K3V super-Earth;
  43% growing season, brutal winters, near-maximum apophenia pressure

### Layer 1: Biological Substrate

Each species has a fixed biological substrate — the hardware that psychology
runs on. Defined in `data/species/*.toml`. Parameters:

- **Cognitive:** temporal discounting rate, cognitive load ceiling, apophenia
  coefficient, loss aversion coefficient, Dunbar number
- **Social:** in-group detection sensitivity, reciprocal altruism radius,
  dominance hierarchy sensitivity, coalition formation instinct
- **Stress:** fight/flight/freeze weights, stress recovery rate, trauma
  consolidation threshold
- **Development:** lifespan, stage proportions, critical period sensitivity,
  intergenerational trauma coefficient
- **Heritability:** per-trait OCEAN heritability coefficients and genetic
  covariance matrix

Included presets: `standard_human`, `terminator_dweller` (patient, wide
altruism, Dunbar 207), `feast_famine_dweller` (urgent, high loss aversion,
near-max apophenia). New presets can be authored by hand or derived
automatically from a planet+star pair via `generate_species_from_environment()`.

### Layer 2: Second-Order Propensities

Substrate parameters are transformed into ten readable civilizational
propensities: short-termism, tribalism ceiling, volatility under stress,
stratification tendency, ideological susceptibility, cooperative radius,
generational memory depth, innovation rate baseline, political instability
cycle, and loss aversion premium.

Propensities are outputs, not inputs. Moving a substrate slider changes the
propensity readout. This is the designer feedback loop.

### Layer 3: Needs and Demand

Seven biological needs (hydration, calories, protein, lipids, carbohydrates,
fiber, micronutrients) across two tiers (survival, security). Each need has a
continuous satiation state, a non-linear urgency curve (sigmoid parameterized
by steepness and midpoint), and a `decay_rate_per_day`. The demand vector is
the urgency-weighted need signal combined with the commodity satisfaction table.

### Layer 4: Market Clearing

Prices update each tick via:

```
price_next = price × (1 + α × price_sensitivity × (demand − supply))
           × (1 + speculation_premium × demand)
           × (1 − cooperation_discount × (1 − demand))
```

where `α` is the base elasticity and the three multipliers come from species
behavior modifiers. Price history is retained (rolling 104-week buffer) for
charting. The market clearing formula is structurally complete — the parameters
and weights need calibration work as more game context accumulates.

### Layer 5: OCEAN and Lifecycle

Defined in types but not yet implemented in the tick loop. The architecture
is in place; the demographic model is the major remaining gap in the simulation
core.

---

## Current Status

### Working end-to-end

- **Rust → Python bridge** (PyO3): fully operational; Rust calls Python each
  tick for need decay, satisfaction, and demand computation
- **Headless sim runner**: ticks correctly with species, config, and all 19
  commodities (`cargo run -p spacesim-cli -- --ticks N --species ...`)
- **Orbital physics pipeline**: star loading, planet loading, insolation,
  equilibrium temperature, seasonal temperature range, growing season fraction,
  habitability scoring — all validated against Earth reference values
- **Seasonal supply modifiers**: per-commodity multipliers applied each tick
  based on day-of-year and planet parameters
- **Evolutionary pressure → substrate**: `compute_evolutionary_pressure()` +
  `pressure_to_substrate_params()` maps physical world parameters to species
  substrate values; handles tidal lock edge case correctly
- **Needs engine**: 7 needs, urgency curves, decay, satisfaction from supply,
  full demand vector computation
- **Market clearing engine**: price discovery formula is implemented and running;
  produces plausible convergent behavior — needs calibration and richer dynamics
- **IPC TCP server**: `sim/ipc` broadcasts newline-delimited JSON `MarketUpdate`
  messages to all connected Godot clients each tick; `Ping/Pong` works;
  `TradeOrder` is received and logged (queue integration pending)
- **Godot project scaffold**: `game/` is a valid Godot 4 project with
  `SimClient.gd` autoload (TCP reconnect, signal dispatch), `MarketBoard`
  (live price table, color-coded, trend arrows), `NeedsPanel` (satiation bars),
  and `Main` root scene
- **Test suite**: 12 suites, ~100 assertions — all passing

### Done in form, needs significant work

- **Market clearing**: the formula runs and produces convergent prices, but
  price elasticity, speculation premium, cooperation discount, and hoarding
  coefficients are not yet calibrated against meaningful gameplay targets.
  Multi-node trade routing, supply shocks, and player intervention mechanics
  are not yet modeled.
- **Godot UI**: the scaffold connects and displays live data, but has no
  styling, no price history charts, no world map, no player interaction beyond
  the structural `send_trade_order()` call, and no scene beyond the single
  market/needs dashboard.

### Not yet started

- World graph (star systems, trade routes, node topology)
- OCEAN trait distributions and per-population state
- Lifecycle and demographic model
- Faction agent logic
- Archetype clustering
- Player interaction mechanics (trade orders queued into world state)
- `WorldSnapshot` message carrying explicit satiation state (NeedsPanel
  currently uses demand as a satiation proxy)
- Event system

---

## Getting Started

### Prerequisites

- Rust (via rustup)
- Python 3.11+
- Godot 4.3+ — for the game frontend only

### Bootstrap

```bash
# Install Python package
pip install -e models/

# Build Rust workspace
cargo build

# Run headless sim (10 weekly ticks, standard human species)
cargo run -p spacesim-cli -- --ticks 10 --species data/species/standard_human.toml

# Run with IPC server for Godot (runs indefinitely at ~1 tick/second)
cargo run -p spacesim-cli -- --ipc --species data/species/standard_human.toml

# Then open the Godot project (in a second terminal or the Godot editor)
godot --path game/

# Run full test suite
bash tests/run_all.sh
```

### Modding

All game data lives in `data/`. No code required for most changes:

- **New star:** copy `data/bodies/sol.toml`, adjust `luminosity`, `temperature_k`
- **New planet:** copy `data/bodies/earth.toml`, adjust `semi_major_axis`,
  `axial_tilt`, `eccentricity`; `tidally_locked = true` collapses seasons
- **New species:** copy `data/species/standard_human.toml`, or derive one
  automatically from a planet+star pair:

```python
from spacesim_models.api import generate_species_from_environment
result = generate_species_from_environment("data/bodies/my_planet.toml",
                                           "data/bodies/my_star.toml")
# result["pressures"] shows the six intermediate evolutionary pressure values
# result["cognitive"], result["social"], result["stress"], result["development"]
# contain the derived substrate parameters
```

- **New commodity:** add a `[[commodity]]` block to any file in
  `data/commodities/`; add it to `COMMODITY_CATEGORIES` in
  `models/spacesim_models/orbital/season.py` to give it seasonal behavior

The key chain: `axial_tilt` + `eccentricity` → `growing_season_fraction` →
agricultural supply modifier → commodity prices → demand pressure → needs
satiation. See the modder's chain in the docs for the full variable map.

---

## Design Documents

All design documents live in `/docs` under version control alongside the code.

| Document | Contents |
|---|---|
| `behavioral_model_design.md` | OCEAN system, needs hierarchy, modular synthesizer architecture |
| `lifecycle_heritability_design.md` | Lifecycle stages, trait inheritance, demographic model |
| `substrate_standard_human_design.md` | Biological substrate layer, Standard Human parameters |
| `repo_architecture.md` | Repository layout, crate map, tooling |

---

## Key Open Questions

- **Simulation scale:** Individual named NPCs, anonymous population buckets,
  or a hybrid? This shapes the Rust data model at a fundamental level.
- **Player role:** Ship captain, faction leader, or detached economic actor?
  Shapes the entire UI and progression system.
- **Trait plasticity:** Should OCEAN scores drift under sustained conditions,
  or remain fixed within a generation?
- **Player psychology inference:** Should the game observe the player's
  behavior over time and build a psychological model of them that NPCs respond
  to?
- **Win conditions:** Emergent sandbox or authored campaign?
- **Market dynamics depth:** The current clearing formula is a single-node
  model. When does multi-node trade routing become load-bearing for gameplay?

---

*Built with Rust, Python, and Godot. Inspired by behavioral economics,
population genetics, and the idea that the most interesting game content
is the kind that surprises its own designer.*
