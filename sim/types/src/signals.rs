//! CV signal types — the "patch cable" format that all behavioral modules speak.
//!
//! All signals are normalized f32 values. Trait signals: [0.0, 1.0].
//! Signed signals (e.g. emotional valence): [-1.0, 1.0].

use serde::{Deserialize, Serialize};

/// A single normalized control-voltage signal.
pub type Cv = f32;

/// The five OCEAN trait signals output by a TraitModule.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct OceanSignals {
    pub openness:          Cv,
    pub conscientiousness: Cv,
    pub extraversion:      Cv,
    pub agreeableness:     Cv,
    pub neuroticism:       Cv,
}

/// Urgency signals output by the NeedsEngine — one per Maslow tier.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct NeedUrgencies {
    pub survival:      Cv,
    pub security:      Cv,
    pub belonging:     Cv,
    pub esteem:        Cv,
    pub transcendence: Cv,
}

/// The demand vector produced by the Priority Mixer and consumed by the market.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DemandVector {
    /// Commodity id → normalized demand pressure [0.0, 1.0]
    pub commodities: std::collections::HashMap<String, Cv>,
}
