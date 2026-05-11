//! Static commodity definitions — what a commodity satisfies, not its market state.
//!
//! CommodityProfile is loaded from data/commodities/*.toml at startup and is
//! immutable during a run. The runtime market state lives in CommodityMarket
//! (market.rs). These are separate so the data layer stays independent of
//! the simulation state.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Static definition of one commodity — its nutrient satisfaction profile.
///
/// `satisfies` maps need_id → satisfaction per unit [0.0, 1.0].
/// Absent keys mean the commodity provides nothing for that need.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommodityProfile {
    pub id:          String,
    pub name:        String,
    pub description: String,
    pub satisfies:   HashMap<String, f32>,
}

/// The full set of commodity profiles loaded from a data directory.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CommodityCatalog {
    pub profiles: Vec<CommodityProfile>,
}

impl CommodityCatalog {
    pub fn get(&self, id: &str) -> Option<&CommodityProfile> {
        self.profiles.iter().find(|p| p.id == id)
    }

    pub fn ids(&self) -> impl Iterator<Item = &str> {
        self.profiles.iter().map(|p| p.id.as_str())
    }
}
