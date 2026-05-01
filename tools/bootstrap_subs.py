#!/usr/bin/env python3
"""
bootstrap_stubs.py — Generate all missing stub files for the spacesim repo.

Run from the repo root:
    python tools/bootstrap_stubs.py

This is safe to re-run: it will never overwrite a file that already has content
beyond a minimal stub. It only writes files that are missing or empty.
"""

import sys
import os
from pathlib import Path

# ── Palette ───────────────────────────────────────────────────────────────────

RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"; CYAN = "\033[36m"

def written(p):  print(f"  {GREEN}+{RESET}  {p}")
def skipped(p):  print(f"  {CYAN}·{RESET}  {DIM}skipped (already has content): {p}{RESET}")
def heading(s):  print(f"\n{BOLD}{s}{RESET}")

# ── Safe writer ───────────────────────────────────────────────────────────────

STUB_MARKERS = ["# stub", "// stub", "stub", "todo", "placeholder"]

def write_if_empty(path: Path, content: str):
    """Write content only if the file doesn't exist or is effectively empty/stub."""
    if path.exists():
        existing = path.read_text().strip().lower()
        # Consider it non-stub if it has meaningful content (>5 lines or no stub marker)
        lines = [l for l in existing.splitlines() if l.strip()]
        has_stub_marker = any(m in existing for m in STUB_MARKERS)
        if len(lines) > 5 and not has_stub_marker:
            skipped(path)
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    written(path)

# ── File definitions ──────────────────────────────────────────────────────────

def files(root: Path) -> dict[Path, str]:
    """Return a dict of {path: content} for all files that should be generated."""

    return {

        # ── Root Cargo.toml (workspace manifest) ──────────────────────────────
        root / "Cargo.toml": """\
[workspace]
members = [
    "sim/types",
    "sim/core",
    "sim/ipc",
    "sim/bindings",
    "sim/cli",
]
resolver = "2"

# Dependency versions pinned here once; member crates reference with { workspace = true }
[workspace.dependencies]
serde       = { version = "1",    features = ["derive"] }
serde_json  = "1"
tokio       = { version = "1",    features = ["full"] }
rayon       = "1"
petgraph    = "0.6"
rand        = "0.8"
pyo3        = { version = "0.21", features = ["auto-initialize"] }
rmp-serde   = "1"
anyhow      = "1"
tracing     = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
""",

        # ── sim/types ─────────────────────────────────────────────────────────
        root / "sim/types/Cargo.toml": """\
[package]
name    = "spacesim-types"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { workspace = true }
""",

        root / "sim/types/src/lib.rs": """\
//! Shared type definitions for the spacesim workspace.
//!
//! This crate has zero logic and zero heavy dependencies.
//! Every other crate imports from here; nothing here imports from other sim crates.

pub mod signals;
pub mod population;
pub mod market;
""",

        root / "sim/types/src/signals.rs": """\
//! CV signal types — the "patch cable" format that all behavioral modules speak.
//!
//! All signals are normalized f32 values. Trait signals: [0.0, 1.0].
//! Signed signals (e.g. emotional valence): [-1.0, 1.0].

use serde::{Deserialize, Serialize};

/// A single normalized control-voltage signal.
pub type Cv = f32;

/// The five OCEAN trait signals output by a TraitModule.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct OceanSignals {
    pub openness:          Cv,
    pub conscientiousness: Cv,
    pub extraversion:      Cv,
    pub agreeableness:     Cv,
    pub neuroticism:       Cv,
}

/// Urgency signals output by the NeedsEngine — one per Maslow tier.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct NeedUrgencies {
    pub survival:      Cv,
    pub security:      Cv,
    pub belonging:     Cv,
    pub esteem:        Cv,
    pub transcendence: Cv,
}

/// The demand vector produced by the Priority Mixer and consumed by the market.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DemandVector {
    /// Commodity id → normalized demand pressure [0.0, 1.0]
    pub commodities: std::collections::HashMap<String, Cv>,
}
""",

        root / "sim/types/src/population.rs": """\
//! Population and agent state types.

use serde::{Deserialize, Serialize};
use crate::signals::{OceanSignals, NeedUrgencies};

/// Snapshot of a single named agent's psychological state.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentState {
    pub id:           u64,
    pub name:         Option<String>,
    pub traits:       OceanSignals,
    pub need_urgencies: NeedUrgencies,
    pub stress_level: f32,
}

/// Statistical summary of a population's trait distribution.
/// Used for background populations — cheaper than per-agent state.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PopulationDistribution {
    /// Node id (star system / station / planet) this population inhabits
    pub node_id:  u64,
    pub size:     u64,
    /// Mean OCEAN scores across the population
    pub trait_means: OceanSignals,
    /// Standard deviations per trait
    pub trait_stdevs: OceanSignals,
    pub need_urgencies: NeedUrgencies,
    pub stress_level: f32,
}
""",

        root / "sim/types/src/market.rs": """\
//! Market signal and commodity types.

use serde::{Deserialize, Serialize};

/// A single commodity's market state at a given tick.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommodityMarket {
    pub id:            String,
    pub name:          String,
    pub price:         f32,
    pub supply:        f32,
    pub demand:        f32,
    /// Rolling price history — ring buffer, newest last
    pub price_history: Vec<f32>,
}

/// All market state for a single node, sent to Godot each tick.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketSnapshot {
    pub node_id:     u64,
    pub tick:        u64,
    pub commodities: Vec<CommodityMarket>,
}
""",

        # ── sim/core ──────────────────────────────────────────────────────────
        root / "sim/core/Cargo.toml": """\
[package]
name    = "spacesim-core"
version = "0.1.0"
edition = "2021"

[dependencies]
spacesim-types = { path = "../types" }
serde          = { workspace = true }
rayon          = { workspace = true }
petgraph       = { workspace = true }
rand           = { workspace = true }
anyhow         = { workspace = true }
tracing        = { workspace = true }
""",

        root / "sim/core/src/lib.rs": """\
//! spacesim-core — the simulation engine.
//!
//! Owns world state, the tick loop, market clearing, and agent decisions.
//! Does not own the IPC server (sim/ipc) or Python bindings (sim/bindings).

pub mod tick;
pub mod world;
pub mod market;
pub mod agents;
pub mod events;

use anyhow::Result;

/// Top-level simulation state. Create one, call tick() in a loop.
pub struct Simulation {
    pub tick_count: u64,
    // TODO: world graph, population map, market state, event queue
}

impl Simulation {
    pub fn new() -> Result<Self> {
        tracing::info!("Initializing simulation");
        Ok(Self { tick_count: 0 })
    }

    /// Advance the simulation by one tick.
    pub fn tick(&mut self) -> Result<()> {
        self.tick_count += 1;
        tracing::debug!(tick = self.tick_count, "tick");
        // TODO: update world, clear markets, process events
        Ok(())
    }
}
""",

        root / "sim/core/src/tick.rs": """\
//! Tick engine — fixed timestep loop and parallel batch scheduling.
//! stub
""",

        root / "sim/core/src/world.rs": """\
//! World state — star system graph, populations, resources.
//! stub
""",

        root / "sim/core/src/market.rs": """\
//! Market clearing — price discovery, demand/supply matching.
//! stub
""",

        root / "sim/core/src/agents.rs": """\
//! Agent decision engine — faction goal stacks and action selection.
//! stub
""",

        root / "sim/core/src/events.rs": """\
//! Discrete event queue — generation, queuing, and consumption.
//! stub
""",

        # ── sim/ipc ───────────────────────────────────────────────────────────
        root / "sim/ipc/Cargo.toml": """\
[package]
name    = "spacesim-ipc"
version = "0.1.0"
edition = "2021"

[dependencies]
spacesim-types = { path = "../types" }
serde          = { workspace = true }
serde_json     = { workspace = true }
tokio          = { workspace = true }
rmp-serde      = { workspace = true }
anyhow         = { workspace = true }
tracing        = { workspace = true }
""",

        root / "sim/ipc/src/lib.rs": """\
//! spacesim-ipc — local IPC server bridging the Rust sim and Godot frontend.
//!
//! Godot connects as a TCP client. The server receives PlayerAction messages
//! and broadcasts WorldSnapshot + MarketUpdate + EventFired messages each tick.

pub mod server;
pub mod protocol;
pub mod handlers;

pub use server::IpcServer;
""",

        root / "sim/ipc/src/protocol.rs": """\
//! IPC message type definitions.
//!
//! These are the canonical message types that cross the Rust ↔ Godot boundary.
//! Both sides must agree on this format. Change carefully.

use serde::{Deserialize, Serialize};
use spacesim_types::market::MarketSnapshot;
use spacesim_types::population::PopulationDistribution;

// ── Outbound (Sim → Godot) ────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum SimMessage {
    WorldSnapshot(WorldSnapshot),
    MarketUpdate(MarketSnapshot),
    EventFired(GameEvent),
    Pong,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldSnapshot {
    pub tick:        u64,
    pub populations: Vec<PopulationDistribution>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameEvent {
    pub id:          String,
    pub description: String,
    pub node_id:     Option<u64>,
}

// ── Inbound (Godot → Sim) ─────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ClientMessage {
    Ping,
    TradeOrder(TradeOrder),
    // More player actions added here as game develops
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeOrder {
    pub commodity_id: String,
    pub quantity:     f32,
    pub node_id:      u64,
}
""",

        root / "sim/ipc/src/server.rs": """\
//! TCP IPC server — listens for Godot connections, dispatches messages.
//! stub
pub struct IpcServer;
impl IpcServer {
    pub async fn run(&self) -> anyhow::Result<()> {
        tracing::info!("IPC server stub — not yet implemented");
        Ok(())
    }
}
""",

        root / "sim/ipc/src/handlers.rs": """\
//! Per-message-type handler functions.
//! stub
""",

        # ── sim/bindings ──────────────────────────────────────────────────────
        root / "sim/bindings/Cargo.toml": """\
[package]
name    = "spacesim-bindings"
version = "0.1.0"
edition = "2021"

# PyO3 requires this to build a Python extension module
[lib]
crate-type = ["cdylib"]

[dependencies]
spacesim-types = { path = "../types" }
pyo3           = { workspace = true }
anyhow         = { workspace = true }
tracing        = { workspace = true }
serde_json     = { workspace = true }
""",

        root / "sim/bindings/src/lib.rs": """\
//! spacesim-bindings — PyO3 bridge into the Python behavioral model layer.
//!
//! This crate calls into spacesim_models.api (Python) and translates the
//! results into Rust types from spacesim-types.
//!
//! The Python interpreter must be initialized before any of these functions
//! are called. In the sim binary this happens at startup.

pub mod model_bridge;

use pyo3::prelude::*;

/// Initialize the Python interpreter and import spacesim_models.
/// Call once at sim startup before any bridge functions.
pub fn init_python() -> PyResult<()> {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        py.import_bound("spacesim_models")?;
        tracing::info!("Python behavioral model layer initialized");
        Ok(())
    })
}
""",

        root / "sim/bindings/src/model_bridge.rs": """\
//! Calls into spacesim_models.api and marshals results to Rust types.
//! stub — functions to be implemented as Python api.py is filled in.

use pyo3::prelude::*;
use anyhow::Result;
use spacesim_types::signals::DemandVector;
use spacesim_types::population::PopulationDistribution;

/// Call spacesim_models.api.get_market_signals() with a population snapshot.
/// Returns a DemandVector for the market clearing engine.
pub fn get_market_signals(_population: &PopulationDistribution) -> Result<DemandVector> {
    // stub
    Ok(DemandVector { commodities: Default::default() })
}
""",

        # ── sim/cli ───────────────────────────────────────────────────────────
        root / "sim/cli/Cargo.toml": """\
[package]
name    = "spacesim-cli"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "spacesim-cli"
path = "src/main.rs"

[dependencies]
spacesim-core  = { path = "../core" }
spacesim-types = { path = "../types" }
anyhow         = { workspace = true }
tracing        = { workspace = true }
tracing-subscriber = { workspace = true }
""",

        root / "sim/cli/src/main.rs": """\
//! Headless simulation runner — development and testing tool.
//!
//! Usage:
//!   cargo run -p spacesim-cli -- --ticks 100
//!   make run-headless TICKS=1000

use anyhow::Result;
use spacesim_core::Simulation;

fn main() -> Result<()> {
    // Initialize structured logging
    tracing_subscriber::fmt()
        .with_env_filter(
            std::env::var("RUST_LOG")
                .unwrap_or_else(|_| "spacesim=debug".to_string())
        )
        .init();

    // Parse --ticks argument (default 10)
    let ticks: u64 = std::env::args()
        .skip_while(|a| a != "--ticks")
        .nth(1)
        .and_then(|v| v.parse().ok())
        .unwrap_or(10);

    tracing::info!(ticks, "Starting headless simulation run");

    let mut sim = Simulation::new()?;

    for _ in 0..ticks {
        sim.tick()?;
    }

    tracing::info!(
        tick_count = sim.tick_count,
        "Simulation run complete"
    );

    Ok(())
}
""",

        # ── models/spacesim_models/signals.py ─────────────────────────────────
        root / "models/spacesim_models/signals.py": """\
\"\"\"
CV signal types — the Python mirror of sim/types/src/signals.rs.

All signals are normalized floats. Trait signals: [0.0, 1.0].
Signed signals (e.g. emotional valence): [-1.0, 1.0].

These dataclasses are the currency that all behavioral modules exchange.
Any module output can feed any module input as long as it speaks this language.
\"\"\"

from dataclasses import dataclass, field
from typing import NewType

# A single normalized control-voltage signal
Cv = NewType("Cv", float)


@dataclass
class OceanSignals:
    \"\"\"The five OCEAN trait signals output by a TraitModule.\"\"\"
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
    \"\"\"Urgency signals from the NeedsEngine — one per Maslow tier.\"\"\"
    survival:      Cv = Cv(0.0)
    security:      Cv = Cv(0.0)
    belonging:     Cv = Cv(0.0)
    esteem:        Cv = Cv(0.0)
    transcendence: Cv = Cv(0.0)


@dataclass
class DemandVector:
    \"\"\"
    Market demand signal produced by the Priority Mixer.
    Maps commodity id → normalized demand pressure [0.0, 1.0].
    \"\"\"
    commodities: dict[str, Cv] = field(default_factory=dict)
""",

        # ── models/spacesim_models/api.py ─────────────────────────────────────
        # Only write this if it exists but is empty/stub — don't clobber real content
        root / "models/spacesim_models/api.py": """\
\"\"\"
spacesim_models.api — the only surface area visible to Rust via PyO3.

Keep this file small and stable. All complexity lives in the submodules.
Add functions here only when a new Rust call-site genuinely needs one.
\"\"\"

from .signals import DemandVector, OceanSignals, NeedUrgencies


def get_market_signals(population_state: dict) -> dict:
    \"\"\"
    Given a population state snapshot from Rust, return a demand vector.

    Args:
        population_state: dict matching PopulationDistribution schema

    Returns:
        dict matching DemandVector schema — {commodity_id: pressure}
    \"\"\"
    # stub — returns zero demand for all commodities
    return DemandVector().commodities


def run_demographic_tick(population_state: dict, world_conditions: dict) -> dict:
    \"\"\"
    Advance the demographic model one tick.

    Args:
        population_state:  current PopulationDistribution snapshot
        world_conditions:  environmental signals (scarcity, conflict, etc.)

    Returns:
        Updated population_state dict
    \"\"\"
    # stub — returns population unchanged
    return population_state


def compute_propensities(substrate_params: dict) -> dict:
    \"\"\"
    Given a species substrate parameter dict, compute second-order propensities.

    Args:
        substrate_params: matches standard_human.toml schema

    Returns:
        dict of propensity_name → float [0.0, 1.0]
    \"\"\"
    # stub — returns neutral propensities
    return {
        "short_termism":            0.5,
        "tribalism_ceiling":        0.5,
        "volatility_under_stress":  0.5,
        "stratification_tendency":  0.5,
        "ideological_susceptibility": 0.5,
        "cooperative_radius":       0.5,
        "generational_memory_depth": 0.5,
        "innovation_rate_baseline": 0.5,
        "political_instability_cycle": 0.5,
        "loss_aversion_premium":    0.5,
    }


def initialize_population(substrate_params: dict, size: int) -> dict:
    \"\"\"
    Create a new population from a substrate preset.

    Args:
        substrate_params: matches standard_human.toml schema
        size:             target population count

    Returns:
        PopulationDistribution dict ready for Rust consumption
    \"\"\"
    # stub — returns a neutral population at the given size
    neutral_traits = OceanSignals().as_dict()
    return {
        "node_id":        0,
        "size":           size,
        "trait_means":    neutral_traits,
        "trait_stdevs":   {k: 0.1 for k in neutral_traits},
        "need_urgencies": {
            "survival": 0.2, "security": 0.3, "belonging": 0.3,
            "esteem": 0.4, "transcendence": 0.5,
        },
        "stress_level": 0.1,
    }
""",

    }


# ── Main ──────────────────────────────────────────────────────────────────────

def find_root() -> Path:
    candidate = Path.cwd()
    while True:
        if (candidate / "sim").exists() and (candidate / "models").exists():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            return Path.cwd()
        candidate = parent


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else find_root()
    print(f"\n\033[1mSpacesim Stub Generator\033[0m")
    print(f"  {DIM}Root: {root}{RESET}")

    targets = files(root)

    sections = [
        ("Root workspace",    lambda p: p.parent == root),
        ("sim/types",         lambda p: "sim/types" in str(p)),
        ("sim/core",          lambda p: "sim/core" in str(p)),
        ("sim/ipc",           lambda p: "sim/ipc" in str(p)),
        ("sim/bindings",      lambda p: "sim/bindings" in str(p)),
        ("sim/cli",           lambda p: "sim/cli" in str(p)),
        ("models/",           lambda p: "spacesim_models" in str(p)),
    ]

    for label, predicate in sections:
        matching = [(p, c) for p, c in targets.items() if predicate(p)]
        if not matching:
            continue
        print(f"\n\033[1m{label}\033[0m")
        for path, content in matching:
            write_if_empty(path, content)

    print(f"\n\033[1mDone.\033[0m")
    print(f"  {DIM}Now run: python tools/validate_repo.py{RESET}")
    print(f"  {DIM}Then:    cargo build{RESET}")
    print(f"  {DIM}Then:    make run-headless TICKS=10{RESET}\n")

    print(f"  \033[33m{BOLD}Note:{RESET} {DIM}game/project.godot must be created by Godot itself.")
    print(f"  Open Godot 4, choose 'New Project', set the project path to")
    print(f"  your game/ directory, and select the .NET (C#) renderer.{RESET}\n")


if __name__ == "__main__":
    main()