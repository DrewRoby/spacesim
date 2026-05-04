//! spacesim-core — the simulation engine.
//!
//! Owns world state, the market clearing tick, and need satiation state.
//! Pure Rust — no Python calls here; the CLI drives PyO3 and passes
//! results into apply_tick().

pub mod tick;
pub mod world;
pub mod market;
pub mod agents;
pub mod events;

use anyhow::Result;
use std::collections::HashMap;
use spacesim_types::{
    config::SimConfig,
    modifiers::BehaviorModifiers,
    market::{CommodityMarket, MarketSnapshot},
};

// ── World state ───────────────────────────────────────────────────────────────

/// All mutable simulation state at a single point in time.
///
/// The CLI loads config and species data, calls Python once per tick via PyO3
/// to decay/satisfy needs and compute demand, then calls apply_tick() here
/// to update prices and advance the clock.
pub struct WorldState {
    pub tick:        u64,
    /// Need satiation distributions: {need_id: (mean, variance)}
    pub satiation:   HashMap<String, (f64, f64)>,
    /// Live market state keyed by commodity id
    pub market:      HashMap<String, CommodityMarket>,
    /// Static per-day supply from TOML, before hoarding modifier
    pub base_supply: HashMap<String, f64>,
    pub config:      SimConfig,
    pub modifiers:   BehaviorModifiers,
}

impl WorldState {
    pub fn new(
        need_ids:    &[String],
        commodities: &[String],
        base_supply: HashMap<String, f64>,
        config:      SimConfig,
        modifiers:   BehaviorModifiers,
    ) -> Result<Self> {
        let satiation = need_ids.iter()
            .map(|id| (
                id.clone(),
                (config.starting_satiation_mean, config.starting_satiation_variance),
            ))
            .collect();

        let market = commodities.iter()
            .map(|id| (id.clone(), CommodityMarket {
                id:            id.clone(),
                name:          id.replace('_', " "),
                price:         1.0,
                supply:        base_supply.get(id).copied().unwrap_or(0.0) as f32,
                demand:        0.5,
                price_history: vec![1.0],
            }))
            .collect();

        tracing::info!(
            needs = need_ids.len(),
            commodities = commodities.len(),
            tick_days = config.tick_days,
            "WorldState initialized"
        );

        Ok(WorldState { tick: 0, satiation, market, base_supply, config, modifiers })
    }

    /// Effective supply per commodity per day, after hoarding is applied.
    pub fn effective_supply(&self) -> HashMap<String, f64> {
        let avail = 1.0 - self.modifiers.supply_hoarding;
        self.base_supply.iter()
            .map(|(id, &s)| (id.clone(), s * avail))
            .collect()
    }

    /// Apply one tick: update prices from Python-computed demand and satiation,
    /// then advance the tick counter.
    ///
    /// Called by the CLI after every PyO3 run_market_tick() call.
    ///
    /// new_satiation : {need_id: (mean, variance)} returned by Python
    /// demand        : {commodity_id: demand [0,1]} returned by Python
    pub fn apply_tick(
        &mut self,
        new_satiation: HashMap<String, (f64, f64)>,
        demand:        HashMap<String, f64>,
    ) -> MarketSnapshot {
        self.satiation = new_satiation;

        let eff_avail  = 1.0 - self.modifiers.supply_hoarding;
        let alpha      = self.config.price_elasticity * self.modifiers.price_sensitivity;
        let speculation = self.modifiers.speculation_premium;
        let coop       = self.modifiers.cooperation_discount;

        for (id, market) in &mut self.market {
            let d_raw   = demand.get(id).copied().unwrap_or(0.0);
            let d       = (d_raw * self.modifiers.demand_amplifier).min(1.0);
            let s       = self.base_supply.get(id).copied().unwrap_or(0.0) * eff_avail;

            let imbalance = d - s;
            let mut price = market.price as f64;

            // Core price discovery
            price *= 1.0 + alpha * imbalance;

            // Speculative premium: inflates price when demand is high
            price *= 1.0 + speculation * d;

            // Cooperation discount: dampens price drop when demand is low
            price *= 1.0 - coop * (1.0 - d).max(0.0);

            price = price.clamp(0.05, 20.0);

            market.price  = price as f32;
            market.demand = d as f32;
            market.supply = s as f32;
            market.price_history.push(price as f32);
            // Keep at most two years of weekly history
            if market.price_history.len() > 104 {
                market.price_history.remove(0);
            }
        }

        self.tick += 1;

        MarketSnapshot {
            node_id:     0,
            tick:        self.tick,
            commodities: self.market.values().cloned().collect(),
        }
    }

    /// Mean satiation across all needs — a single health signal for display.
    pub fn mean_satiation(&self) -> f64 {
        if self.satiation.is_empty() { return 0.0; }
        self.satiation.values().map(|(m, _)| m).sum::<f64>() / self.satiation.len() as f64
    }
}
