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
