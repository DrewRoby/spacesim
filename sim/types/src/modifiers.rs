//! Economic behavior modifiers derived from species propensities.
//!
//! These translate the civilizational fingerprint (propensities) into
//! concrete adjustments on market clearing mechanics.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Market behavior modifiers for a species.
///
/// Each field adjusts one dimension of market mechanics. All values are
/// derived from propensities via linear mappings; the ranges are calibrated
/// so that mid-range propensities (0.5) produce neutral modifier values.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BehaviorModifiers {
    /// Multiplier on demand signal [1.0, 1.5].
    /// Fearful populations (high loss_aversion_premium) demand more than their
    /// satiation alone would suggest — hoarding impulse amplifies apparent need.
    pub demand_amplifier: f64,

    /// Fraction of base supply withheld from the open market [0.0, 0.4].
    /// Stratified societies see elite supply capture reducing market availability.
    pub supply_hoarding: f64,

    /// Multiplier on price_elasticity [0.5, 2.0].
    /// Volatile societies (high volatility_under_stress) over-react to imbalances,
    /// producing larger price swings per unit of demand-supply gap.
    pub price_sensitivity: f64,

    /// Price discount applied in slack markets (demand < 1.0) [0.0, 0.3].
    /// Cooperative societies use mutual aid to dampen price drops, providing
    /// a floor that prevents destabilizing deflation spirals.
    pub cooperation_discount: f64,

    /// Speculative premium added when demand is high [0.0, 0.15].
    /// Short-termism drives speculative buying above clearing price,
    /// inflating bubbles during scarcity events.
    pub speculation_premium: f64,
}

impl BehaviorModifiers {
    /// Derive modifiers from the propensity dict returned by Python's api.py.
    pub fn from_propensity_map(props: &HashMap<String, f64>) -> Self {
        let get = |key: &str| props.get(key).copied().unwrap_or(0.5);
        BehaviorModifiers {
            demand_amplifier:     1.0  + 0.5  * get("loss_aversion_premium"),
            supply_hoarding:      0.4  *        get("stratification_tendency"),
            price_sensitivity:    0.5  + 1.5  * get("volatility_under_stress"),
            cooperation_discount: 0.3  *        get("cooperative_radius"),
            speculation_premium:  0.15 *        get("short_termism"),
        }
    }

    /// Neutral modifiers — midpoint values, used when no species is loaded.
    pub fn neutral() -> Self {
        BehaviorModifiers {
            demand_amplifier:     1.25,
            supply_hoarding:      0.20,
            price_sensitivity:    1.25,
            cooperation_discount: 0.15,
            speculation_premium:  0.075,
        }
    }
}
