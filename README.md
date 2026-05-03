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

**Answer big questions with systems.** Rather than deciding what factions will
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
| Behavioral modeling | Python | Personality math, needs engine, demographic model |
| Simulation engine | Rust | Tick loop, market clearing, world state, agent decisions |
| Game frontend | Godot 4 (.NET) | Rendering, UI, input, IPC client |
| Asset pipeline | Meshy → Blender → Godot | AI-generated 3D assets, cleanup, import |
| Game data | TOML | Species, factions, commodities, events — owned by nobody, read by everyone |

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
│   ├── ipc/                # IPC server (Rust ↔ Godot bridge)
│   ├── bindings/           # PyO3 bindings (Rust ↔ Python bridge)
│   └── cli/                # Headless runner — dev and test tool
├── models/                 # Python behavioral model package
│   └── spacesim_models/
│       ├── substrate/      # Species biological substrate + propensity math
│       ├── personality/    # OCEAN trait system
│       ├── lifecycle/      # Lifecycle stages, demographic model, heritability
│       ├── needs/          # Maslow-derived needs hierarchy
│       ├── behavior/       # Decision modules, stress, memory, social
│       ├── archetypes/     # Emergent clustering (not yet implemented)
│       └── api.py          # The only surface Rust calls into
├── game/                   # Godot 4 project
│   ├── scenes/             # UI scenes (galaxy map, market, designer, dashboard)
│   ├── scripts/            # GDScript + C# source
│   └── assets/             # Ships, stations, environments, UI
├── data/                   # Shared game configuration (TOML)
│   ├── species/            # Species substrate presets
│   ├── factions/           # Faction definitions
│   ├── commodities/        # Commodity table
│   └── events/             # Probabilistic event templates
├── tools/                  # Developer utilities
│   ├── validate_repo.py    # Structure checker
│   ├── bootstrap_stubs.py  # Stub file generator
│   └── run_propensities.py # Standalone Python model runner
└── docs/                   # Design documents
```

---

## The Model

### Layer 0: Biological Substrate

Before personality, each species has a fixed biological substrate — the
hardware that psychology runs on. Standard Human values are defined in
`data/species/standard_human.toml`. Substrate parameters include:

- **Cognitive:** temporal discounting rate, cognitive load ceiling, apophenia
  coefficient, loss aversion coefficient, Dunbar number
- **Social:** in-group detection sensitivity, reciprocal altruism radius,
  dominance hierarchy sensitivity, coalition formation instinct
- **Stress:** fight/flight/freeze weights, stress recovery rate, trauma
  consolidation threshold
- **Development:** lifespan, stage proportions, critical period sensitivity,
  intergenerational trauma transmission coefficient
- **Heritability:** per-trait OCEAN heritability coefficients and genetic
  covariance matrix

These parameters are what differ between species (races) in the game. A species
with a loss aversion coefficient of 5.0 instead of 2.3 produces a fundamentally
different civilization even with identical OCEAN distributions.

### Layer 1: Second-Order Propensities

Substrate parameters are not displayed raw — they are transformed into ten
readable civilizational propensities that describe what the species is *like*:
short-termism, tribalism ceiling, volatility under stress, stratification
tendency, ideological susceptibility, cooperative radius, generational memory
depth, innovation rate baseline, political instability cycle, and loss aversion
premium.

Propensities are outputs, not inputs. Moving a substrate slider changes the
propensity readout in real time. This is the designer UI's feedback loop.

### Layer 2: OCEAN Trait Distributions

On top of the substrate, each population has a distribution of OCEAN
(Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
scores — a mean and variance per trait, plus genetic correlation structure.
This distribution evolves over generations through the lifecycle model.

### Layer 3: Needs Hierarchy

OCEAN traits modulate a five-tier needs hierarchy (survival, security,
belonging, esteem, transcendence). Each tier has a continuous satiation state
and a non-linear urgency curve. Urgency signals combine in a priority mixer
that produces the demand vector consumed by the market.

### Layer 4: Lifecycle and Heritability

Populations evolve through births, development, mate selection, and death.
Trait inheritance is modeled with per-trait heritability coefficients, genetic
covariance, environmental developmental effects, and genuine stochastic noise.
Assortative mating causes trait distributions to cluster over generations —
economic classes emerge from the math rather than being authored.

---

## Current Status

### Working

- Rust workspace builds cleanly — 5 crates, full dependency graph
- Headless sim runner ticks correctly (`cargo run -p spacesim-cli -- --ticks N`)
- Python package structure with all submodule directories
- `SpeciesSubstrate` dataclass with full validation and TOML loading
- `compute_propensities()` with real weighted math across all ten propensities
- `tools/run_propensities.py` produces colored terminal output against Standard
  Human and comparison variant species
- `data/species/standard_human.toml` — complete Standard Human parameter preset

### In Progress

- **Rust → Python bridge:** PyO3 integration in `sim/cli` is written but
  blocked on Python environment configuration. The bridge calls
  `spacesim_models.api.compute_propensities_from_toml()` and renders the
  result in Rust. Likely fix: trim `pyproject.toml` to stdlib-only dependencies
  until each heavy package is actually needed.

- **`sim/types/src/propensities.rs`:** Rust `Propensities` struct is written
  and awaits a clean build to integrate.

### Not Yet Started

- IPC server (Rust ↔ Godot bridge)
- Market clearing engine
- World graph (star systems, trade routes)
- Commodity definitions
- Godot frontend (requires Godot 4 .NET build)
- Lifecycle and demographic model implementation
- Needs engine implementation
- Archetype clustering
- Faction agent logic

---

## Getting Started

### Prerequisites

- Rust (via rustup — `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- Python 3.11+
- Godot 4.2+ (.NET build) — for the game frontend only

### Bootstrap

```bash
# 1. Validate repo structure
python tools/validate_repo.py

# 2. Install Python package (minimal — no heavy ML deps yet)
pip install -e models/ --no-deps

# 3. Verify Python model works independently
python tools/run_propensities.py

# 4. Build Rust workspace
cargo build

# 5. Run headless sim
cargo run -p spacesim-cli -- --ticks 10

# 6. Run headless sim with species (once PyO3 bridge is green)
cargo run -p spacesim-cli -- --species data/species/standard_human.toml --ticks 10
```

Steps 1–5 work without Godot. The game frontend is the last layer, not the
first.

### Developer Tools

```bash
# Check repo structure against expected layout
python tools/validate_repo.py

# Generate any missing stub files
python tools/bootstrap_stubs.py

# Run the behavioral model standalone (no Rust required)
python tools/run_propensities.py
```

---

## Design Documents

All design documents live in `/docs` under version control alongside the code.

| Document | Contents |
|---|---|
| `game_strategy.md` | Top-level architecture, stack rationale, development phases |
| `behavioral_model_design.md` | OCEAN system, needs hierarchy, modular synthesizer architecture |
| `lifecycle_heritability_design.md` | Lifecycle stages, trait inheritance, demographic model |
| `substrate_standard_human_design.md` | Biological substrate layer, Standard Human parameters, race/class design, UI design |
| `repo_architecture.md` | Repository layout, crate map, tooling, bootstrapping sequence |
| `session_summary.md` | End-of-session state, current blocker analysis, next session plan |
| `docs/adr/` | Architecture Decision Records — why decisions were made, not just what they are |

---

## Key Open Questions

These are tracked here because they have architectural implications and should
be decided deliberately rather than by default:

- **Simulation scale:** Individual named NPCs, anonymous population buckets,
  or a hybrid? This shapes the Rust data model at a fundamental level.
- **Player role:** Ship captain, faction leader, or detached economic actor?
  Shapes the entire UI and progression system.
- **Trait plasticity:** Should OCEAN scores drift under sustained conditions,
  or remain fixed within a generation? Fixed is simpler; drifting is richer.
- **Substrate mutability:** Can a species' biological substrate change over
  civilizational timescales? If so, at what rate and driven by what?
- **Player psychology inference:** Should the game observe the player's
  behavior over time and build a psychological model of them that NPCs respond
  to? Almost no games do this.
- **Subprocess vs embedded Python:** Keep PyO3 in-process for low call
  latency, or run Python as a subprocess for full isolation and hot reload?
  Both are architecturally sound; the current environment blocker may resolve
  this question in practice.
- **Win conditions:** Emergent sandbox or authored campaign? Shapes content
  investment entirely.

---

## Contributing

This is currently a solo exploratory project. The design is intentionally
kept in documents rather than comments so that architectural reasoning is
legible and revisitable. If you're reading this and the questions above
interest you, the `/docs` folder is the right place to start.

---

*Built with Rust, Python, and Godot. Inspired by behavioral economics,
population genetics, and the idea that the most interesting game content
is the kind that surprises its own designer.*