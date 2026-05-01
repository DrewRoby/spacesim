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
