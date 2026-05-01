# Space Exploration & Economic Sim — Master Strategy Document

> **Stack Summary:** Rust (simulation core) · Python (behavioral models) · Godot 4 (game frontend) · Meshy + Blender (asset pipeline)

---

## 1. Vision & Design Philosophy

A space exploration and economic simulation where **human psychology drives everything downstream**. Rather than scripting economic behaviors directly, we model populations as distributions of psychological traits. Markets, factions, political structures, and exploration incentives all emerge from the aggregate wants, fears, and values of simulated populations — not from hand-authored rules.

The player operates in this world as an actor with real leverage, but not omnipotent control. Moving a market means moving the *people* behind it.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     GODOT 4 (Frontend)                   │
│   Rendering · UI · Input · Audio · Scene Management      │
└────────────────────┬────────────────────────────────────┘
                     │  IPC (Unix socket / shared memory)
                     │  JSON or MessagePack protocol
┌────────────────────▼────────────────────────────────────┐
│                  RUST (Simulation Core)                   │
│   Tick Engine · Agent State · Market Clearing · World     │
└────────────────────┬────────────────────────────────────┘
                     │  PyO3 FFI bindings
┌────────────────────▼────────────────────────────────────┐
│              PYTHON (Behavioral Model Layer)              │
│   Personality Distributions · Needs Engine · Archetypes  │
└─────────────────────────────────────────────────────────┘
```

Each layer has a clear ownership boundary. Godot never touches simulation state directly. Python never runs on the hot path. Rust owns the clock.

---

## 3. Principal Components

### 3.1 Behavioral Model Layer (Python)

The intellectual core of the project. Defines *who* the simulated population is and *what they want*.

**Personality Trait System**
- Based on the **OCEAN / Big Five** model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Populations represented as **trait distributions** (means + variance per faction/culture/region), not individual discrete agents
- Libraries: `factor_analyzer`, `PyMC`, `scipy.stats`

**Needs & Desires Engine**
- Hierarchy loosely inspired by Maslow but flattened and parameterized: survival needs, security needs, belonging needs, status needs, transcendence needs
- Each need tier has a **satiation curve** — partially met needs create market signals; fully met needs generate surplus demand for luxury/status goods
- Trait scores modulate the shape and urgency of these curves (high Neuroticism → steeper anxiety curve around security needs)

**Behavioral Archetypes**
- Cluster analysis on trait distributions produces named archetypes: Pioneers, Hoarders, Diplomats, Zealots, Merchants, etc.
- Archetypes are shorthand for the sim — they summarize a distribution bucket into a decision-making profile
- Archetypes are **emergent**, not authored — they arise from the underlying distribution math

**Output Interface**
- Python exposes a clean API to Rust via PyO3: `get_market_signals(population_state)` → demand vectors
- Model parameters are hot-reloadable TOML/JSON configs — you should be able to tune personality distributions without recompiling anything

---

### 3.2 Simulation Core (Rust)

The engine that runs the world forward in time. Owns state, owns the clock, owns all mutable data.

**Tick Engine**
- Fixed timestep simulation loop (configurable: 1 sim-day per tick, or faster for time-skip)
- Parallel agent-batch processing via `rayon` — population groups updated concurrently with no shared mutable state within a tick
- Deterministic given a seed — important for save/load and debugging

**World State**
- Star systems, planets, stations, and routes represented as a graph (`petgraph`)
- Each node carries: resource inventories, population records, infrastructure level, faction control
- State is serialized to disk via `serde` + `bincode` for save files

**Market Clearing Engine**
- Receives demand vectors from the Python behavioral layer each tick
- Runs a simple but extensible price-clearing algorithm: supply/demand ratio sets price, price feeds back into next tick's demand (elasticity)
- Supports: commodity markets, labor markets, information markets (rumors, intelligence)
- Price history stored as ring buffers — feeds into player-facing charts and NPC decision-making

**Agent Decision Engine**
- NPC factions and corporations are first-class agents with their own goal stacks
- Goal stacks are driven by archetype profiles — a Merchant faction prioritizes route efficiency; a Zealot faction prioritizes ideological spread over profit
- Decision trees are authored in data (TOML), not code — easy to tune without recompiling

**Event System**
- Discrete events (discovery, war declaration, economic crash) are generated probabilistically based on world state thresholds
- Events are queued and consumed by both the Godot frontend (for display) and the sim itself (for state changes)
- Rust crates: `serde`, `rayon`, `petgraph`, `rand`, `tokio` (for the IPC server)

---

### 3.3 IPC Layer (Rust ↔ Godot)

The bridge between simulation truth and what the player sees.

**Protocol**
- Rust runs a lightweight **local TCP or Unix domain socket server**
- Godot connects as a client, sends commands (player actions), receives state snapshots and event streams
- Serialization: **MessagePack** (faster than JSON, still human-debuggable with tooling)

**Message Types**
- `WorldSnapshot` — full or delta state for the current system view
- `MarketUpdate` — price and demand changes this tick
- `EventFired` — discrete event for the UI to handle (news ticker, popup, etc.)
- `PlayerAction` — trade order, route assignment, diplomatic overture, etc.

**Tick Synchronization**
- Godot renders at display framerate; sim runs at its own cadence
- Godot interpolates visual state between received snapshots — the sim does not care about framerate

---

### 3.4 Game Frontend (Godot 4)

Godot owns everything the player sees and touches. It is deliberately kept dumb — it renders state, it does not compute it.

**Key Scenes**
- **Galaxy Map** — node graph of star systems, trade routes, faction territories
- **System View** — orbital mechanics display, planet/station detail panels
- **Market UI** — price charts (driven by Rust ring buffer data), order entry, inventory
- **Faction Intel** — personality/archetype readouts for known factions (lore-flavored presentation of the underlying OCEAN data)
- **News & Events Feed** — surfaces discrete events from the Rust event queue

**GDScript vs C#**
- Use **C#** for anything performance-adjacent (IPC handling, data parsing, UI data binding)
- Use **GDScript** for scene logic, input handling, and anything that benefits from fast iteration

**Rendering Approach**
- Godot 4's Vulkan renderer is capable of high-quality space visuals with relatively little custom shader work
- Space backgrounds: pre-rendered skyboxes generated by tooling (see Asset Pipeline)
- Ships and stations: imported GLTF from the asset pipeline

---

## 4. Data Architecture

```
/data
  /galaxy
    systems.toml          # Star system definitions
    routes.toml           # Initial trade route graph
  /factions
    faction_*.toml        # Per-faction personality distributions + starting state
  /archetypes
    archetypes.toml       # Named archetype definitions (output of Python clustering)
  /markets
    commodities.toml      # Goods, base prices, production/consumption profiles
  /events
    event_templates.toml  # Probabilistic event definitions
  /models
    ocean_weights.json    # Tuned OCEAN → behavior mappings
```

All game configuration lives in flat files. The Rust sim reads these at startup. Modding is a first-class citizen from day one.

---

## 5. Development Phases

### Phase 0 — Foundation (Current)
- [ ] Define repo structure (Cargo workspace + Python package + Godot project)
- [ ] Stub IPC protocol and get Godot talking to a Rust process
- [ ] Implement basic OCEAN → needs mapping in Python
- [ ] Define commodity list and initial faction roster

### Phase 1 — Sim Core
- [ ] Working tick engine with market clearing
- [ ] PyO3 bridge: Rust calls Python behavioral model each tick
- [ ] Basic save/load
- [ ] Headless test harness — run 1000 ticks, inspect market history, no Godot required

### Phase 2 — Visible World
- [ ] Galaxy map in Godot pulling live data from Rust
- [ ] Market UI with price history charts
- [ ] Player can execute trades and see market respond

### Phase 3 — Personality Made Visible
- [ ] Faction intel screen showing archetype readouts
- [ ] Events surface in UI, driven by simulation thresholds
- [ ] NPC factions pursue goals visibly (expansion, trade, conflict)

### Phase 4 — Content & Polish
- [ ] Custom 3D assets integrated (see Asset Pipeline)
- [ ] Procedural star system generation
- [ ] Full player progression loop

---

## 6. 3D Asset Pipeline

### Recommended Toolchain: Meshy → Blender → Godot

This is designed for a solo developer who wants quality assets without becoming a 3D artist, with AI handling the heavy lifting.

---

### 6.1 Meshy (Primary Generation Tool)

**Meshy** (`meshy.ai`) is the current best-in-class AI 3D generation tool for this use case.

- **Text-to-3D and Image-to-3D** — describe a ship or station in words, get a mesh back in minutes
- Outputs **GLTF/OBJ/FBX** — all importable directly into Blender and Godot
- Generates **UV maps and basic textures automatically** — significant time savings
- Has a Blender plugin for in-editor generation

**Workflow for a ship asset:**
1. Write a text prompt in Meshy: *"Hard-edged utilitarian cargo hauler, asymmetric, exposed fuel tanks, weathered metal, sci-fi"*
2. Generate 4 variants, pick the best
3. Export GLTF → import to Blender for cleanup
4. Export from Blender → import to Godot

**Other tools worth knowing:**
- **CSM (Common Sense Machines)** — better for image-to-3D when you have reference art
- **Luma Genie** — strong for organic shapes (alien fauna, terrain features)
- **Krea AI** — for generating reference images to feed into Meshy

---

### 6.2 Blender (Cleanup & Control)

Blender is unavoidable for quality results, but the scope of what you need to learn is much narrower than full modeling from scratch.

**You only need to learn:**
- Basic navigation and selection (one session)
- Mesh cleanup: removing duplicate vertices, fixing normals, decimating poly count
- Material/shader basics: plugging Meshy's textures into Blender's PBR material nodes
- GLTF export settings for Godot compatibility

**I will write all non-trivial Blender Python scripts.** Blender has a full Python API (`bpy`) — repetitive tasks (batch export, LOD generation, texture baking) can be fully automated. You describe what you want done to a set of assets, I write the script.

**Recommended Blender add-ons:**
- **BlenderKit** — library of free materials and some base meshes
- **Node Wrangler** — makes the shader node editor much less painful
- **Meshy Blender Plugin** — generate directly inside Blender

---

### 6.3 Godot Import Pipeline

- All assets enter Godot as **GLTF 2.0** — the native format, no conversion step
- Set up a `/assets/ships/`, `/assets/stations/`, `/assets/environments/` folder structure in the Godot project
- Godot's import system auto-generates `.import` files — commit these to version control
- For space backgrounds: **HDRI skyboxes** from `polyhaven.com` (free, CC0) are high quality and require no generation

---

## 7. Repository Structure (Proposed)

```
/spacesim
  /sim/                   # Rust Cargo workspace
    /core/                # Main sim crate (tick engine, markets, world state)
    /ipc/                 # IPC server crate
    /bindings/            # PyO3 Python bindings crate
  /models/                # Python behavioral model package
    /personality/         # OCEAN trait system
    /needs/               # Needs/desires engine
    /archetypes/          # Clustering and archetype generation
  /game/                  # Godot 4 project
    /scenes/
    /scripts/
    /assets/
  /data/                  # Shared game data (TOML configs)
  /tools/                 # Blender scripts, asset pipeline utilities
  README.md
  this_document.md
```

---

## 8. Key Open Questions

These are decisions that don't need to be made now but should be tracked:

1. **Scale of simulation** — are we modeling individual named NPCs, anonymous population buckets, or a hybrid? This affects memory architecture significantly.
2. **Player role** — ship captain, faction leader, or detached "god mode" economic actor? Shapes the UI entirely.
3. **Win conditions / progression** — emergent sandbox or authored campaign structure?
4. **Procedural generation depth** — how much of the galaxy is authored vs. generated at runtime?
5. **Multiplayer** — almost certainly out of scope, but the IPC architecture should not foreclose it.

---

*Document status: Living draft. Update as architectural decisions are finalized.*
