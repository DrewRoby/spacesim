//! Simulation configuration loaded from data/sim_config.toml.

use serde::{Deserialize, Serialize};

/// Global parameters controlling the simulation tick loop and market mechanics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimConfig {
    /// Days each simulation tick represents (7 = weekly ticks).
    pub tick_days: u32,

    /// Base price adjustment per unit demand-supply imbalance.
    /// price_next = price × (1 + price_elasticity × price_sensitivity × (demand − supply))
    pub price_elasticity: f64,

    /// Initial mean satiation for all biological needs [0.0, 1.0].
    pub starting_satiation_mean: f64,

    /// Initial satiation variance across the population [0.0, 0.25].
    pub starting_satiation_variance: f64,
}

impl Default for SimConfig {
    fn default() -> Self {
        SimConfig {
            tick_days:                   7,
            price_elasticity:            0.15,
            starting_satiation_mean:     0.5,
            starting_satiation_variance: 0.10,
        }
    }
}
