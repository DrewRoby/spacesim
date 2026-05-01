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
