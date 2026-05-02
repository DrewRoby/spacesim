//! Headless simulation runner — development and testing tool.
//!
//! Usage:
//!   cargo run -p spacesim-cli -- --ticks 100
//!   cargo run -p spacesim-cli -- --ticks 10 --species data/species/standard_human.toml
//!   make run-headless TICKS=1000

use anyhow::{Context, Result};
use pyo3::prelude::*;
use spacesim_core::Simulation;
use spacesim_types::propensities::Propensities;
use std::collections::HashMap;
use std::path::PathBuf;

// ── CLI args ──────────────────────────────────────────────────────────────────

struct Args {
    ticks:       u64,
    species_path: Option<PathBuf>,
}

fn parse_args() -> Args {
    let args: Vec<String> = std::env::args().collect();
    let mut ticks        = 10u64;
    let mut species_path = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--ticks" => {
                i += 1;
                if let Some(v) = args.get(i) {
                    ticks = v.parse().unwrap_or(10);
                }
            }
            "--species" => {
                i += 1;
                if let Some(v) = args.get(i) {
                    species_path = Some(PathBuf::from(v));
                }
            }
            _ => {}
        }
        i += 1;
    }
    Args { ticks, species_path }
}

// ── Python bridge ─────────────────────────────────────────────────────────────

/// Call spacesim_models.api.compute_propensities_from_toml() and return
/// the result as a typed Propensities struct.
fn fetch_propensities(toml_path: &str) -> Result<Propensities> {
    Python::with_gil(|py| {
        let api = py
            .import_bound("spacesim_models.api")
            .context("Could not import spacesim_models.api.\n\
                      Make sure the Python package is installed:\n\
                      \x20 pip install -e models/")?;

        let raw = api
            .call_method1("compute_propensities_from_toml", (toml_path,))
            .with_context(|| format!(
                "compute_propensities_from_toml() failed for path: {toml_path}"
            ))?;

        let map: HashMap<String, f64> = raw
            .extract()
            .context("Could not extract propensity dict from Python return value")?;

        Propensities::from_map(&map)
            .map_err(|e| anyhow::anyhow!("Propensities::from_map failed: {e}"))
    })
}

// ── Display ───────────────────────────────────────────────────────────────────

const BAR_WIDTH: usize = 36;

// ANSI codes — keep them inline so this file stays self-contained
const RESET:   &str = "\x1b[0m";
const BOLD:    &str = "\x1b[1m";
const DIM:     &str = "\x1b[2m";
const GREEN:   &str = "\x1b[32m";
const YELLOW:  &str = "\x1b[33m";
const RED:     &str = "\x1b[31m";
const MAGENTA: &str = "\x1b[35m";
const CYAN:    &str = "\x1b[36m";
const WHITE:   &str = "\x1b[37m";

fn propensity_color(name: &str) -> &'static str {
    match name {
        "cooperative_radius" | "innovation_rate_baseline"  => GREEN,
        "tribalism_ceiling"  | "volatility_under_stress"   => RED,
        "short_termism"      | "stratification_tendency"
        | "political_instability_cycle"                    => YELLOW,
        "ideological_susceptibility" | "loss_aversion_premium" => MAGENTA,
        "generational_memory_depth"                        => CYAN,
        _                                                  => WHITE,
    }
}

fn render_bar(name: &str, value: f32) -> String {
    let filled = (value * BAR_WIDTH as f32).round() as usize;
    let empty  = BAR_WIDTH.saturating_sub(filled);
    let color  = propensity_color(name);
    let bar    = format!(
        "{color}{}{DIM}{}{RESET}",
        "█".repeat(filled),
        "░".repeat(empty),
    );
    format!("  {name:<28} {bar} {BOLD}{value:.3}{RESET}")
}

fn print_propensities(species_name: &str, props: &Propensities) {
    println!("\n{BOLD}{WHITE}{}{RESET}", "─".repeat(70));
    println!("  {BOLD}{species_name}{RESET}");
    println!("{BOLD}{WHITE}{}{RESET}", "─".repeat(70));
    for (name, value) in props.entries() {
        println!("{}", render_bar(name, value));
    }
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() -> Result<()> {
    // Structured logging — RUST_LOG=debug for verbose output
    tracing_subscriber::fmt()
        .with_env_filter(
            std::env::var("RUST_LOG")
                .unwrap_or_else(|_| "spacesim=info".to_string()),
        )
        .init();

    let args = parse_args();

    println!("\n{BOLD}{WHITE}{line}", line = "═".repeat(70));
    println!("  SPACESIM — Headless Runner");
    println!("{line}{RESET}", line = "═".repeat(70));

    // ── Propensity computation (Python model) ─────────────────────────────────
    if let Some(ref species_path) = args.species_path {
        let path_str = species_path
            .canonicalize()
            .unwrap_or_else(|_| species_path.clone())
            .to_string_lossy()
            .into_owned();

        tracing::info!(path = %path_str, "Loading species substrate");
        println!("\n  {DIM}Species: {path_str}{RESET}");

        match fetch_propensities(&path_str) {
            Ok(props) => {
                // Extract species name from filename for display
                let species_name = species_path
                    .file_stem()
                    .map(|s| s.to_string_lossy().replace('_', " "))
                    .unwrap_or_else(|| "Unknown Species".into());

                print_propensities(&species_name, &props);
                tracing::info!("Propensities computed successfully");
            }
            Err(e) => {
                eprintln!("\n  {RED}✗ Propensity computation failed:{RESET}");
                eprintln!("    {e:#}");
                eprintln!("\n  {DIM}Hint: ensure the Python package is installed:{RESET}");
                eprintln!("    {DIM}pip install -e models/{RESET}\n");
                std::process::exit(1);
            }
        }
    } else {
        // No species file given — try the default location
        let default = PathBuf::from("data/species/standard_human.toml");
        if default.exists() {
            println!("\n  {DIM}No --species given. Trying default: {}{RESET}", default.display());
            let path_str = default
                .canonicalize()
                .unwrap_or(default)
                .to_string_lossy()
                .into_owned();
            match fetch_propensities(&path_str) {
                Ok(props) => print_propensities("Standard Human", &props),
                Err(e)    => {
                    eprintln!("\n  {YELLOW}Propensity computation skipped: {e:#}{RESET}");
                    eprintln!("  {DIM}Pass --species <path> or install the Python package.{RESET}");
                }
            }
        } else {
            println!("\n  {DIM}No --species given and no default found. Skipping propensities.");
            println!("  Usage: cargo run -p spacesim-cli -- --species data/species/standard_human.toml{RESET}");
        }
    }

    // ── Simulation tick loop ──────────────────────────────────────────────────
    println!("\n{BOLD}{WHITE}{}{RESET}", "─".repeat(70));
    println!("  {BOLD}Simulation{RESET}  ({} ticks)", args.ticks);
    println!("{BOLD}{WHITE}{}{RESET}", "─".repeat(70));

    tracing::info!(ticks = args.ticks, "Starting headless simulation run");
    let mut sim = Simulation::new()?;

    for _ in 0..args.ticks {
        sim.tick()?;
    }

    tracing::info!(tick_count = sim.tick_count, "Run complete");
    println!("\n  {GREEN}✓{RESET} {BOLD}{} ticks completed.{RESET}", sim.tick_count);
    println!("{BOLD}{WHITE}{}{RESET}\n", "═".repeat(70));

    Ok(())
}
