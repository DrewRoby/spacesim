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
