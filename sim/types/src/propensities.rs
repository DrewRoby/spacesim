/// Second-order propensities computed from a species substrate.
///
/// These are the readable civilizational fingerprint of a species —
/// derived outputs, not inputs. The Python model computes them;
/// Rust stores and displays them.
///
/// All values are in [0.0, 1.0]. Higher = more of that tendency.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Propensities {
    /// How strongly the species discounts future rewards vs present ones.
    pub short_termism: f32,

    /// The natural ceiling on tribal group size before institutional trust required.
    pub tribalism_ceiling: f32,

    /// How much behaviour degrades under sustained stress.
    pub volatility_under_stress: f32,

    /// Speed and persistence with which informal status hierarchies form.
    pub stratification_tendency: f32,

    /// How readily coherent worldviews and ideologies are adopted and spread.
    pub ideological_susceptibility: f32,

    /// Natural radius of trust and cooperation without institutional scaffolding.
    pub cooperative_radius: f32,

    /// How many generations a civilizational trauma echoes before fading.
    pub generational_memory_depth: f32,

    /// Background rate at which novel behaviours and technologies spread.
    pub innovation_rate_baseline: f32,

    /// Natural frequency of faction formation and political realignment.
    pub political_instability_cycle: f32,

    /// Size of insurance, security, and certainty-premium markets.
    pub loss_aversion_premium: f32,
}

impl Propensities {
    /// Build from the flat HashMap returned by Python's api.py.
    pub fn from_map(map: &HashMap<String, f64>) -> Result<Self, String> {
        let get = |key: &str| -> Result<f32, String> {
            map.get(key)
                .copied()
                .map(|v| v as f32)
                .ok_or_else(|| format!("missing propensity key: '{key}'"))
        };

        Ok(Self {
            short_termism:               get("short_termism")?,
            tribalism_ceiling:           get("tribalism_ceiling")?,
            volatility_under_stress:     get("volatility_under_stress")?,
            stratification_tendency:     get("stratification_tendency")?,
            ideological_susceptibility:  get("ideological_susceptibility")?,
            cooperative_radius:          get("cooperative_radius")?,
            generational_memory_depth:   get("generational_memory_depth")?,
            innovation_rate_baseline:    get("innovation_rate_baseline")?,
            political_instability_cycle: get("political_instability_cycle")?,
            loss_aversion_premium:       get("loss_aversion_premium")?,
        })
    }

    /// Ordered list of (name, value) pairs — useful for display.
    pub fn entries(&self) -> [(&'static str, f32); 10] {
        [
            ("short_termism",               self.short_termism),
            ("tribalism_ceiling",           self.tribalism_ceiling),
            ("volatility_under_stress",     self.volatility_under_stress),
            ("stratification_tendency",     self.stratification_tendency),
            ("ideological_susceptibility",  self.ideological_susceptibility),
            ("cooperative_radius",          self.cooperative_radius),
            ("generational_memory_depth",   self.generational_memory_depth),
            ("innovation_rate_baseline",    self.innovation_rate_baseline),
            ("political_instability_cycle", self.political_instability_cycle),
            ("loss_aversion_premium",       self.loss_aversion_premium),
        ]
    }
}
