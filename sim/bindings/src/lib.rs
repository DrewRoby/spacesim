//! spacesim-bindings — PyO3 bridge into the Python behavioral model layer.
//!
//! This crate calls into spacesim_models.api (Python) and translates the
//! results into Rust types from spacesim-types.
//!
//! The Python interpreter must be initialized before any of these functions
//! are called. In the sim binary this happens at startup.

pub mod model_bridge;

use pyo3::prelude::*;

/// Initialize the Python interpreter and import spacesim_models.
/// Call once at sim startup before any bridge functions.
pub fn init_python() -> PyResult<()> {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        py.import_bound("spacesim_models")?;
        tracing::info!("Python behavioral model layer initialized");
        Ok(())
    })
}
