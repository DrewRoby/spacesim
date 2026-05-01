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
