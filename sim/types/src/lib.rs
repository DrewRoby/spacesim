//! Shared type definitions for the spacesim workspace.
//!
//! This crate has zero logic and zero heavy dependencies.
//! Every other crate imports from here; nothing here imports from other sim crates.

pub mod signals;
pub mod population;
pub mod market;
pub mod propensities;
