//! Calls into spacesim_models.api and marshals results to Rust types.
//! stub — functions to be implemented as Python api.py is filled in.

use pyo3::prelude::*;
use anyhow::Result;
use spacesim_types::signals::DemandVector;
use spacesim_types::population::PopulationDistribution;

/// Call spacesim_models.api.get_market_signals() with a population snapshot.
/// Returns a DemandVector for the market clearing engine.
pub fn get_market_signals(_population: &PopulationDistribution) -> Result<DemandVector> {
    // stub
    Ok(DemandVector { commodities: Default::default() })
}
