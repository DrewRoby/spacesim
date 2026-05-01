# Repository & Workspace Architecture
## Structure, Conventions & Tooling Decisions

> *This document commits the project to its physical layout.*
> *Changing it later is painful. Read before implementing.*

---

## Guiding Principles

1. **Each layer is independently runnable.** The Python model layer runs and
   tests without Rust. The Rust sim runs headless without Godot. Godot can
   display mock data without a live sim. No layer should require another to
   be healthy in order to develop or test.

2. **Data is nobody's code.** All game configuration (faction definitions,
   commodity tables, event templates, substrate presets) lives in `/data` as
   flat TOML files. No layer owns it. All layers read it. Modders touch it
   without touching code.

3. **The IPC contract is the spine.** The message format between Rust and
   Godot is the most load-bearing interface in the system. It lives in its
   own crate and its own document, and nothing on either side of it should
   be able to change it silently.

4. **Docs live with the code.** The design documents produced so far belong
   in `/docs` under version control, not in a separate wiki that drifts out
   of sync.

5. **Tooling is explicit.** Every non-obvious command needed to build, run,
   or test any part of the project is captured in a `Makefile` at the repo
   root. Nobody should have to remember incantations.

---

## Top-Level Repository Layout

```
spacesim/
│
├── Cargo.toml                  # Workspace root — lists all Rust crates
├── Makefile                    # Top-level build/run/test commands
├── .env.example                # Environment variable template
├── .gitignore
├── README.md
│
├── sim/                        # Rust workspace (all crates)
├── models/                     # Python behavioral model package
├── game/                       # Godot 4 project
├── data/                       # Shared game data (TOML)
├── tools/                      # Asset pipeline, Blender scripts, utilities
└── docs/                       # All design documents
```

---

## `/sim` — The Rust Workspace

The Rust side is a **Cargo workspace** — a single `Cargo.toml` at the repo
root (not inside `/sim`) that declares multiple member crates. Each crate has
a single clear responsibility.

### Crate Map

```
sim/
├── core/                       # The simulation engine
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── tick.rs             # Tick engine, main loop
│       ├── world/
│       │   ├── mod.rs
│       │   ├── galaxy.rs       # Star system graph (petgraph)
│       │   ├── population.rs   # Population state per node
│       │   └── resources.rs    # Resource inventories
│       ├── market/
│       │   ├── mod.rs
│       │   ├── clearing.rs     # Price clearing algorithm
│       │   ├── commodities.rs  # Commodity definitions
│       │   └── history.rs      # Price history ring buffers
│       ├── agents/
│       │   ├── mod.rs
│       │   ├── faction.rs      # Faction agent logic
│       │   └── goals.rs        # Goal stack implementation
│       └── events/
│           ├── mod.rs
│           └── queue.rs        # Discrete event queue
│
├── ipc/                        # IPC server (Godot ↔ Rust bridge)
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── server.rs           # TCP/Unix socket server (tokio)
│       ├── protocol.rs         # Message type definitions (serde)
│       └── handlers.rs         # Per-message-type handlers
│
├── bindings/                   # PyO3 Python bindings
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       └── model_bridge.rs     # Calls into Python behavioral model
│
├── cli/                        # Headless test runner / dev tool
│   ├── Cargo.toml
│   └── src/
│       └── main.rs             # Run N ticks headless, dump state
│
└── types/                      # Shared type definitions (no logic)
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        ├── signals.rs          # CV signal types (the "patch cable" format)
        ├── population.rs       # PopulationState, AgentState structs
        └── market.rs           # MarketSignal, DemandVector types
```

### Why `types/` Is Its Own Crate

Every other crate depends on `types/`. It has zero dependencies of its own.
This prevents circular dependencies and means the shared type definitions —
especially the CV signal format and the IPC message types — can be imported
by `core`, `ipc`, and `bindings` without any of them knowing about each other.
It also compiles essentially instantly, so it never becomes a build bottleneck.

### Root `Cargo.toml` (Workspace)

```toml
[workspace]
members = [
    "sim/core",
    "sim/ipc",
    "sim/bindings",
    "sim/cli",
    "sim/types",
]
resolver = "2"

[workspace.dependencies]
# Pinned here, referenced in member crates as { workspace = true }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
rayon = "1"
petgraph = "0.6"
rand = "0.8"
pyo3 = { version = "0.21", features = ["auto-initialize"] }
rmp-serde = "1"          # MessagePack serialization
anyhow = "1"
tracing = "0.1"
tracing-subscriber = "0.3"
```

Pinning all dependency versions at the workspace level means every crate
uses identical versions. No version drift between crates, no duplicate
compilations of the same dependency at different versions.

---

## `/models` — The Python Package

A proper installable Python package, not a pile of scripts. This matters
because `bindings/` calls into it via PyO3, and PyO3 needs a real importable
module to call.

```
models/
├── pyproject.toml              # PEP 517 build config (replaces setup.py)
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Dev/test dependencies
│
└── spacesim_models/            # The actual package (importable as this name)
    ├── __init__.py
    │
    ├── substrate/              # Species biological substrate
    │   ├── __init__.py
    │   ├── constants.py        # Standard Human preset values
    │   ├── species.py          # SpeciesSubstrate dataclass
    │   └── presets.py          # Named preset registry
    │
    ├── personality/            # OCEAN trait system
    │   ├── __init__.py
    │   ├── traits.py           # TraitModule, AgentPersonality
    │   ├── population.py       # PopulationPersonality (distribution math)
    │   └── heritability.py     # Heritability engine, covariance matrix
    │
    ├── lifecycle/              # Lifecycle and demographic model
    │   ├── __init__.py
    │   ├── stages.py           # LifecycleStage enum, stage transitions
    │   ├── demographic.py      # DemographicModule (births/deaths)
    │   └── inheritance.py      # Mate selection, trait inheritance
    │
    ├── needs/                  # Needs hierarchy (Maslow-derived)
    │   ├── __init__.py
    │   ├── tiers.py            # NeedTier enum, satiation curves
    │   ├── engine.py           # NeedsEngine module
    │   └── urgency.py          # Urgency curve math
    │
    ├── behavior/               # Decision and action modules
    │   ├── __init__.py
    │   ├── stress.py           # StressModule
    │   ├── memory.py           # MemoryModule
    │   ├── social.py           # SocialModule
    │   ├── mixer.py            # PriorityMixer
    │   └── decision.py         # DecisionModule → market signals
    │
    ├── archetypes/             # Emergent clustering
    │   ├── __init__.py
    │   ├── clustering.py       # HDBSCAN over trait × need space
    │   └── registry.py         # Named archetype registry (runtime output)
    │
    ├── signals.py              # CV signal types (mirrors sim/types)
    └── api.py                  # The clean interface PyO3 calls into
```

### `api.py` — The PyO3 Contract

This file is the *only* entry point from Rust into Python. It exports a small,
stable set of functions that `bindings/model_bridge.rs` calls. Nothing else
in the Python package is visible to Rust directly.

```python
# spacesim_models/api.py
# This is the surface area of the Python layer as seen from Rust.
# Keep it small. Keep it stable. All complexity lives behind it.

def get_market_signals(population_state: dict) -> dict:
    """Given a population state snapshot, return a demand vector."""
    ...

def run_demographic_tick(population_state: dict, world_conditions: dict) -> dict:
    """Advance the demographic model one tick. Return updated population state."""
    ...

def compute_propensities(substrate_params: dict) -> dict:
    """Given substrate parameters, return computed second-order propensities."""
    ...

def initialize_population(substrate_params: dict, size: int) -> dict:
    """Create a new population from a substrate preset."""
    ...
```

Four functions. That is the entire Rust-visible API surface of the Python layer.

### `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "spacesim-models"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "scipy>=1.12",
    "pymc>=5.0",
    "factor-analyzer>=0.5",
    "scikit-learn>=1.4",
    "networkx>=3.2",
    "hdbscan>=0.8",
    "pydantic>=2.0",    # Strict dataclasses for all state objects
    "tomllib",          # Reading /data TOML configs (stdlib in 3.11+)
]
```

---

## `/game` — The Godot 4 Project

Godot project lives here as a peer to Rust and Python, not nested inside
either. The Godot project root is `/game` and contains a standard Godot
project structure.

```
game/
├── project.godot               # Godot project config
├── export_presets.cfg          # Build targets
│
├── scenes/
│   ├── main/
│   │   └── Main.tscn           # Root scene, IPC connection lifecycle
│   ├── galaxy_map/
│   │   ├── GalaxyMap.tscn
│   │   └── SystemNode.tscn
│   ├── system_view/
│   │   └── SystemView.tscn
│   ├── market/
│   │   ├── MarketUI.tscn
│   │   └── PriceChart.tscn
│   ├── population_dashboard/
│   │   ├── PopulationDashboard.tscn
│   │   └── PropensityRadar.tscn
│   └── designer/
│       ├── DesignerMode.tscn
│       └── SubstratePanel.tscn
│
├── scripts/                    # GDScript and C# source
│   ├── autoloads/
│   │   ├── SimConnection.cs    # IPC client — singleton, connects on start
│   │   ├── GameState.cs        # Local cache of last received world snapshot
│   │   └── EventBus.gd         # Signal bus for UI ↔ logic decoupling
│   ├── ui/
│   │   ├── PropensityRadar.cs  # Radar chart renderer
│   │   ├── PriceChart.cs       # Price history chart
│   │   └── DemographicPyramid.cs
│   └── designer/
│       └── SubstrateSlider.gd  # Per-parameter slider widget
│
├── assets/
│   ├── ships/                  # GLTF ship models
│   ├── stations/               # GLTF station models
│   ├── environments/
│   │   └── skyboxes/           # HDRI space backgrounds
│   ├── ui/
│   │   └── fonts/
│   └── audio/
│
└── addons/                     # Godot plugins (if any)
```

### Why C# for Autoloads and UI, GDScript for Scene Logic

`SimConnection.cs` needs to handle async TCP reads without blocking the
render thread — C#'s async/await is much cleaner for this than GDScript.
The data-binding heavy UI components (charts, radar) also benefit from C#'s
type safety when parsing MessagePack payloads.

GDScript remains appropriate for scene-level logic: input handling, animation
triggers, simple state machines. The rule: if it touches the network or
parses structured data, use C#. If it moves a node around, use GDScript.

---

## `/data` — Shared Game Configuration

Owned by nobody. Read by everyone. All files are TOML.

```
data/
├── species/
│   ├── standard_human.toml     # The Standard Human substrate preset
│   └── _template.toml          # Documented template for custom species
│
├── factions/
│   ├── _template.toml
│   └── terran_consortium.toml  # First faction definition
│
├── commodities/
│   └── commodities.toml        # Full commodity table with base properties
│
├── market/
│   └── market_config.toml      # Clearing algorithm parameters
│
├── events/
│   └── event_templates.toml    # Probabilistic event definitions
│
├── world/
│   └── galaxy_seed.toml        # Starting galaxy configuration
│
└── designer/
    └── propensity_weights.toml # Weights for propensity computation
                                # (how much each substrate param contributes
                                #  to each propensity)
```

### `standard_human.toml` (Initial Structure)

```toml
[meta]
name = "Standard Human"
version = "0.1.0"
description = "Baseline homo sapiens substrate parameters."

[cognitive]
temporal_discounting_rate = 0.72    # 0=linear/patient, 1=extreme hyperbolic
cognitive_load_ceiling = 0.28       # 0=high capacity, 1=low capacity (heuristic-dominant)
apophenia_coefficient = 0.76        # 0=literal, 1=pattern-saturated
loss_aversion_coefficient = 2.3     # Symmetric=1.0; Standard Human ~2.3
dunbar_number = 150                 # Hard social tracking limit

[social]
ingroup_detection_sensitivity = 0.68   # 0=cosmopolitan, 1=hair-trigger tribal
reciprocal_altruism_radius = 0.45      # 0=kin-only, 1=diffuse altruism
dominance_hierarchy_sensitivity = 0.71 # 0=rank-blind, 1=rank-saturated
coalition_formation_instinct = 0.74    # 0=transactional, 1=identity-fused

[stress]
fight_weight = 0.38
flight_weight = 0.42
freeze_weight = 0.20
stress_recovery_rate = 0.18         # 0=instant recovery, 1=permanent accumulation
trauma_consolidation_threshold = 0.55  # 0=resilient, 1=easily marked

[development]
lifespan_years = 80
stage_proportions = { development = 0.15, youth = 0.15, adult = 0.40, elder = 0.20, terminal = 0.10 }
critical_period_sensitivity = 0.72  # 0=even plasticity, 1=early years are destiny
intergenerational_trauma_coefficient = 0.15

[heritability]
openness = 0.57
conscientiousness = 0.49
extraversion = 0.54
agreeableness = 0.42
neuroticism = 0.48

[heritability.covariance]
# Upper triangle only; matrix is symmetric
oc = -0.10
oe =  0.05
oa =  0.10
on = -0.05
ce =  0.05
ca =  0.10
cn = -0.15
ea =  0.20
en = -0.10
an = -0.30
```

---

## `/tools` — Asset Pipeline & Utilities

```
tools/
├── blender/
│   ├── README.md               # How to run these scripts
│   ├── batch_export.py         # Export all assets to GLTF
│   ├── cleanup_mesh.py         # Remove dupes, fix normals, decimate
│   └── lod_generator.py        # Generate LOD variants
│
├── asset_pipeline/
│   ├── validate_assets.py      # Check all referenced assets exist
│   └── thumbnail_gen.py        # Generate thumbnails for designer UI
│
└── sim_inspector/
    ├── README.md
    └── inspector.py            # Connect to headless sim, query state,
                                # dump CSVs — dev/debug tool
```

---

## `/docs` — Design Documentation

```
docs/
├── index.md                    # Document map and reading order
├── game_strategy.md            # ← already written
├── behavioral_model_design.md  # ← already written
├── lifecycle_heritability_design.md  # ← already written
├── substrate_standard_human_design.md  # ← already written
├── repo_architecture.md        # ← this document
│
├── ipc_protocol.md             # IPC message format spec (to be written)
├── data_schema.md              # TOML schema documentation (to be written)
└── adr/                        # Architecture Decision Records
    └── 0001-polyglot-stack.md  # Why Rust + Python + Godot
```

### Architecture Decision Records (ADRs)

An ADR is a short document that records *why* a significant decision was made,
not just what it was. The format is: Context → Decision → Consequences.
They're invaluable six months later when you've forgotten why something is
the way it is. Every non-obvious architectural decision gets one.

---

## The `Makefile`

Every meaningful operation is a named make target. No memorizing commands.

```makefile
.PHONY: help build test run-headless run-game install-python clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk \
	'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Rust
build-sim: ## Build all Rust crates (debug)
	cargo build

build-sim-release: ## Build all Rust crates (release/optimized)
	cargo build --release

test-sim: ## Run all Rust tests
	cargo test

run-headless: ## Run sim headless for N ticks (usage: make run-headless TICKS=1000)
	cargo run -p cli -- --ticks $(TICKS)

# Python
install-python: ## Install Python package in development mode
	pip install -e models/[dev]

test-python: ## Run Python model tests
	pytest models/

# Combined
run-game: ## Build sim + launch Godot (requires Godot in PATH)
	cargo build && godot --path game/

# Maintenance
clean: ## Remove build artifacts
	cargo clean
	find models -name "*.pyc" -delete
	find models -name "__pycache__" -delete
```

---

## `.gitignore`

```gitignore
# Rust
/target/
Cargo.lock          # Excluded for libraries; include if this becomes a binary dist

# Python
__pycache__/
*.pyc
*.pyo
.venv/
models/*.egg-info/
dist/
.pytest_cache/
.mypy_cache/

# Godot
game/.godot/
game/export/
*.import            # Do NOT ignore — these should be committed

# Environment
.env
*.env.local

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/settings.json
.idea/
*.swp
```

Note: `*.import` files from Godot are intentionally *not* ignored. They are
generated by Godot's import system and should be committed so the project
opens correctly for any contributor without requiring a full re-import.

---

## Dependency & Tooling Versions (Pinned)

Pinning ensures reproducible builds. Update deliberately, not accidentally.

| Tool | Version | Notes |
|---|---|---|
| Rust | 1.77+ | Specify in `rust-toolchain.toml` |
| Python | 3.11+ | `tomllib` is stdlib from 3.11 |
| Godot | 4.2+ | .NET build required for C# |
| uv | latest | Fast Python package manager, replaces pip for dev |

### `rust-toolchain.toml`

```toml
[toolchain]
channel = "stable"
components = ["rustfmt", "clippy"]
```

---

## Bootstrapping Sequence

The exact order of operations to go from zero to a running (headless) sim:

```bash
# 1. Clone and enter
git clone <repo> spacesim && cd spacesim

# 2. Install Python package
pip install uv
uv pip install -e models/

# 3. Verify Python models run independently
pytest models/
python -c "from spacesim_models.api import compute_propensities; print('OK')"

# 4. Build Rust workspace
cargo build

# 5. Run headless sim (should tick without crashing)
make run-headless TICKS=10

# 6. Open Godot project (manual)
# File → Open → select game/project.godot
```

Steps 1–5 should be achievable without Godot installed. The game layer is
the last thing that needs to be healthy, not the first.

---

## What This Architecture Forecloses

In the interest of honesty about tradeoffs, committing to this layout makes
the following harder:

- **Moving to a monolith later** — the three-layer separation is baked in.
  If the IPC overhead ever becomes a real problem, the fix is optimizing the
  protocol, not collapsing the layers.
- **Switching game engines** — the IPC protocol is engine-agnostic, but the
  Godot scene structure and C# autoloads aren't. Switching to Unity would mean
  rewriting `/game` but not touching `/sim` or `/models`.
- **Pure Python sim** — the Python layer is modeling, not simulation. If you
  ever want to prototype the full sim in Python for speed of iteration, you'd
  do that in a separate experimental branch, not in this structure.

These are acceptable tradeoffs for the architecture we've chosen.

---

*Implement this structure before writing any simulation logic.*
*The scaffolding is the foundation; build it once and build it right.*
