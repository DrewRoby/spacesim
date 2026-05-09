//! Headless simulation runner — development and testing tool.
//!
//! Usage:
//!   cargo run -p spacesim-cli -- --ticks 52
//!   cargo run -p spacesim-cli -- --ticks 52 --species data/species/standard_human.toml
//!   cargo run -p spacesim-cli -- --ticks 52 --config data/sim_config.toml \
//!                                            --species data/species/standard_human.toml
//!   cargo run -p spacesim-cli -- --ticks 0 --ipc    # run forever, stream to Godot

use anyhow::{Context, Result};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use spacesim_core::WorldState;
use spacesim_ipc::{IpcServer, protocol::SimMessage};
use spacesim_types::{
    config::SimConfig,
    modifiers::BehaviorModifiers,
    propensities::Propensities,
};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;

// ── CLI args ──────────────────────────────────────────────────────────────────

struct Args {
    ticks:            u64,   // 0 = run forever (IPC mode)
    ipc:              bool,  // launch the TCP server for Godot
    species_path:     Option<PathBuf>,
    config_path:      PathBuf,
    needs_toml:       PathBuf,
    commodities_dir:  PathBuf,
}

fn parse_args() -> Args {
    let args: Vec<String> = std::env::args().collect();
    let mut ticks           = 10u64;
    let mut ipc             = false;
    let mut species_path    = None;
    let mut config_path     = PathBuf::from("data/sim_config.toml");
    let mut needs_toml      = PathBuf::from("data/needs/biological_needs.toml");
    let mut commodities_dir = PathBuf::from("data/commodities/");
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--ticks"       => { i += 1; if let Some(v) = args.get(i) { ticks = v.parse().unwrap_or(10); } }
            "--ipc"         => { ipc = true; }
            "--species"     => { i += 1; if let Some(v) = args.get(i) { species_path = Some(PathBuf::from(v)); } }
            "--config"      => { i += 1; if let Some(v) = args.get(i) { config_path = PathBuf::from(v); } }
            "--needs"       => { i += 1; if let Some(v) = args.get(i) { needs_toml = PathBuf::from(v); } }
            "--commodities" => { i += 1; if let Some(v) = args.get(i) { commodities_dir = PathBuf::from(v); } }
            _ => {}
        }
        i += 1;
    }
    // --ipc implies run forever unless a finite tick count was explicitly given
    if ipc && ticks == 10 { ticks = 0; }
    Args { ticks, ipc, species_path, config_path, needs_toml, commodities_dir }
}

// ── ANSI colors ───────────────────────────────────────────────────────────────

const RESET:   &str = "\x1b[0m";
const BOLD:    &str = "\x1b[1m";
const DIM:     &str = "\x1b[2m";
const GREEN:   &str = "\x1b[32m";
const YELLOW:  &str = "\x1b[33m";
const RED:     &str = "\x1b[31m";
const MAGENTA: &str = "\x1b[35m";
const CYAN:    &str = "\x1b[36m";
const WHITE:   &str = "\x1b[37m";

// ── Python bridge ─────────────────────────────────────────────────────────────

fn import_api<'py>(py: Python<'py>) -> Result<Bound<'py, PyModule>> {
    py.import_bound("spacesim_models.api")
        .context("Could not import spacesim_models.api.\n\
                  Make sure the Python package is installed:\n\
                  \x20 pip install -e models/")
}

fn fetch_propensities(toml_path: &str) -> Result<Propensities> {
    Python::with_gil(|py| {
        let api = import_api(py)?;
        let raw = api
            .call_method1("compute_propensities_from_toml", (toml_path,))
            .with_context(|| format!("compute_propensities_from_toml() failed for: {toml_path}"))?;
        let map: HashMap<String, f64> = raw.extract()
            .context("Could not extract propensity dict")?;
        Propensities::from_map(&map)
            .map_err(|e| anyhow::anyhow!("Propensities::from_map failed: {e}"))
    })
}

fn fetch_modifiers(toml_path: &str) -> Result<BehaviorModifiers> {
    Python::with_gil(|py| {
        let api = import_api(py)?;
        let raw = api
            .call_method1("get_behavior_modifiers_from_toml", (toml_path,))
            .context("get_behavior_modifiers_from_toml() failed")?;
        let map: HashMap<String, f64> = raw.extract()
            .context("Could not extract modifiers dict")?;
        Ok(BehaviorModifiers::from_propensity_map(&map))
    })
}

fn fetch_base_supplies(commodities_dir: &str) -> Result<HashMap<String, f64>> {
    Python::with_gil(|py| {
        let api = import_api(py)?;
        let raw = api
            .call_method1("load_base_supplies", (commodities_dir,))
            .context("load_base_supplies() failed")?;
        raw.extract().context("Could not extract base_supplies dict")
    })
}

/// Calls Python run_market_tick — the hot path, invoked every tick.
fn run_market_tick_py(
    needs_toml:       &str,
    commodities_dir:  &str,
    satiation:        &HashMap<String, (f64, f64)>,
    effective_supply: &HashMap<String, f64>,
    tick_days:        u32,
) -> Result<(HashMap<String, (f64, f64)>, HashMap<String, f64>)> {
    Python::with_gil(|py| {
        let api = import_api(py)?;

        // Build Python dicts from Rust HashMaps
        let sat_dict = PyDict::new_bound(py);
        for (k, (m, v)) in satiation {
            sat_dict.set_item(k, (*m, *v))?;
        }
        let supply_dict = PyDict::new_bound(py);
        for (k, v) in effective_supply {
            supply_dict.set_item(k, *v)?;
        }

        let result = api.call_method1(
            "run_market_tick",
            (needs_toml, commodities_dir, sat_dict, supply_dict, tick_days as i64),
        ).context("run_market_tick() failed")?;

        let (new_sat, demand): (HashMap<String, (f64, f64)>, HashMap<String, f64>) =
            result.extract().context("Could not extract run_market_tick result")?;

        Ok((new_sat, demand))
    })
}

// ── Display helpers ───────────────────────────────────────────────────────────

const BAR_WIDTH: usize = 36;

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

fn price_color(price: f32) -> &'static str {
    if price > 1.5 { RED }
    else if price > 1.1 { YELLOW }
    else if price < 0.7 { CYAN }
    else { GREEN }
}

fn print_tick_header(tick: u64, tick_days: u32, mean_satiation: f64) {
    let week = tick;
    let day  = (tick - 1) * tick_days as u64 + 1;
    let sat_color = if mean_satiation > 0.7 { GREEN }
                    else if mean_satiation > 0.4 { YELLOW }
                    else { RED };
    println!(
        "\n  {BOLD}Week {week:>3}{RESET}  {DIM}(day {day}){RESET}  \
         population satiation {sat_color}{BOLD}{:.2}{RESET}",
        mean_satiation,
    );
}

fn print_market_row(id: &str, price: f32, demand: f32, supply: f32, prev_price: f32) {
    let arrow = if price > prev_price * 1.01 { "▲" }
                else if price < prev_price * 0.99 { "▼" }
                else { "─" };
    let col = price_color(price);
    println!(
        "  {id:<16} {col}{BOLD}{price:>6.3}{RESET} {col}{arrow}{RESET}  \
         demand {demand:.2}  supply {supply:.3}",
    );
}

fn print_modifiers(mods: &BehaviorModifiers) {
    println!("\n{BOLD}{WHITE}{}{RESET}", "─".repeat(70));
    println!("  {BOLD}Behavior Modifiers{RESET}");
    println!("{BOLD}{WHITE}{}{RESET}", "─".repeat(70));
    println!("  {DIM}demand_amplifier     {RESET}{BOLD}{:.3}{RESET}   \
              {DIM}supply_hoarding      {RESET}{BOLD}{:.3}{RESET}",
        mods.demand_amplifier, mods.supply_hoarding);
    println!("  {DIM}price_sensitivity    {RESET}{BOLD}{:.3}{RESET}   \
              {DIM}cooperation_discount {RESET}{BOLD}{:.3}{RESET}",
        mods.price_sensitivity, mods.cooperation_discount);
    println!("  {DIM}speculation_premium  {RESET}{BOLD}{:.3}{RESET}",
        mods.speculation_premium);
}

// ── Main ──────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "spacesim=info".to_string()),
        )
        .init();

    let args = parse_args();

    println!("\n{BOLD}{WHITE}{line}", line = "═".repeat(70));
    println!("  SPACESIM — Headless Runner");
    println!("{line}{RESET}", line = "═".repeat(70));

    // ── Load sim config ───────────────────────────────────────────────────────
    let config: SimConfig = if args.config_path.exists() {
        let content = std::fs::read_to_string(&args.config_path)
            .with_context(|| format!("Could not read {}", args.config_path.display()))?;
        toml::from_str(&content)
            .with_context(|| format!("Could not parse {}", args.config_path.display()))?
    } else {
        println!("  {DIM}No sim_config.toml found — using defaults.{RESET}");
        SimConfig::default()
    };

    println!(
        "\n  {DIM}Config: {} days/tick  α={:.3}{RESET}",
        config.tick_days, config.price_elasticity,
    );

    // ── Canonicalize data paths ───────────────────────────────────────────────
    let needs_toml = args.needs_toml
        .canonicalize()
        .unwrap_or_else(|_| args.needs_toml.clone())
        .to_string_lossy()
        .into_owned();

    let commodities_dir = args.commodities_dir
        .canonicalize()
        .unwrap_or_else(|_| args.commodities_dir.clone())
        .to_string_lossy()
        .into_owned();

    // ── Load species propensities + modifiers ─────────────────────────────────
    let species_path = args.species_path.as_ref().or_else(|| {
        let default = PathBuf::from("data/species/standard_human.toml");
        if default.exists() { Some(Box::leak(Box::new(default)) as &PathBuf) } else { None }
    });

    let (species_name, propensities, modifiers) = if let Some(path) = species_path {
        let path_str = path.canonicalize()
            .unwrap_or_else(|_| path.clone())
            .to_string_lossy()
            .into_owned();

        println!("\n  {DIM}Species: {path_str}{RESET}");

        match (fetch_propensities(&path_str), fetch_modifiers(&path_str)) {
            (Ok(props), Ok(mods)) => {
                let name = path.file_stem()
                    .map(|s| s.to_string_lossy().replace('_', " "))
                    .unwrap_or_else(|| "Unknown Species".into());
                tracing::info!("Propensities computed successfully");
                (name, Some(props), mods)
            }
            (Err(e), _) | (_, Err(e)) => {
                eprintln!("\n  {RED}✗ Species computation failed:{RESET}\n    {e:#}");
                eprintln!("  {DIM}Hint: pip install -e models/{RESET}");
                std::process::exit(1);
            }
        }
    } else {
        println!("\n  {DIM}No --species given. Using neutral behavior modifiers.{RESET}");
        ("(neutral)".to_owned(), None, BehaviorModifiers::neutral())
    };

    if let Some(ref props) = propensities {
        print_propensities(&species_name, props);
    }
    print_modifiers(&modifiers);

    // ── Load base supplies from Python ────────────────────────────────────────
    let base_supply = fetch_base_supplies(&commodities_dir)
        .context("Could not load commodity base supplies")?;

    let commodity_ids: Vec<String> = {
        let mut ids: Vec<String> = base_supply.keys().cloned().collect();
        ids.sort();
        ids
    };

    // We need need_ids; derive them from a Python call to get the initial satiation keys
    // by running one tick with a default state to discover them — or just hard-code the
    // standard biological needs.  We call run_market_tick once with empty satiation
    // (Python will default to 0.5) to bootstrap the need_id list.
    let need_ids: Vec<String> = {
        let init_satiation: HashMap<String, (f64, f64)> = HashMap::new();
        let eff_supply: HashMap<String, f64> = base_supply.iter()
            .map(|(k, &v)| (k.clone(), v * (1.0 - modifiers.supply_hoarding)))
            .collect();
        let (initial_sat, _) = run_market_tick_py(
            &needs_toml, &commodities_dir,
            &init_satiation, &eff_supply,
            config.tick_days,
        ).context("Could not bootstrap need ids from run_market_tick")?;
        let mut ids: Vec<String> = initial_sat.keys().cloned().collect();
        ids.sort();
        ids
    };

    // ── Build world state ─────────────────────────────────────────────────────
    let mut world = WorldState::new(
        &need_ids,
        &commodity_ids,
        base_supply,
        config.clone(),
        modifiers.clone(),
    )?;

    // ── IPC server (optional) ─────────────────────────────────────────────────
    let ipc: Option<Arc<IpcServer>> = if args.ipc {
        let server = Arc::new(IpcServer::new());
        let srv    = Arc::clone(&server);
        tokio::spawn(async move { srv.run().await.expect("IPC server error") });
        println!("  {CYAN}IPC server started — waiting for Godot on port 7777{RESET}");
        // Brief pause so the listener is ready before the first tick
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        Some(server)
    } else {
        None
    };

    // ── Tick loop ─────────────────────────────────────────────────────────────
    let run_forever = args.ticks == 0;
    println!("\n{BOLD}{WHITE}{}{RESET}", "─".repeat(70));
    if run_forever {
        println!("  {BOLD}Simulation{RESET}  (running until Ctrl-C × {} days/tick)", config.tick_days);
    } else {
        println!("  {BOLD}Simulation{RESET}  ({} ticks × {} days)", args.ticks, config.tick_days);
    }
    println!("{BOLD}{WHITE}{}{RESET}", "─".repeat(70));

    // Track previous prices for movement arrows
    let mut prev_prices: HashMap<String, f32> = world.market.iter()
        .map(|(id, m)| (id.clone(), m.price))
        .collect();

    tracing::info!(ticks = args.ticks, ipc = args.ipc, "Starting simulation run");

    let mut tick_num = 0u64;
    loop {
        if !run_forever && tick_num >= args.ticks { break; }

        let eff_supply = world.effective_supply();

        let (new_satiation, demand) = run_market_tick_py(
            &needs_toml,
            &commodities_dir,
            &world.satiation,
            &eff_supply,
            world.config.tick_days,
        ).context("run_market_tick failed")?;

        let snapshot = world.apply_tick(new_satiation, demand);
        let mean_sat = world.mean_satiation();

        // Broadcast to Godot if IPC is active
        if let Some(ref server) = ipc {
            server.broadcast(&SimMessage::MarketUpdate(snapshot.clone()));
        }

        print_tick_header(snapshot.tick, world.config.tick_days, mean_sat);

        // Sort commodities by demand descending for readability
        let mut sorted = snapshot.commodities.clone();
        sorted.sort_by(|a, b| b.demand.partial_cmp(&a.demand).unwrap_or(std::cmp::Ordering::Equal));

        for c in &sorted {
            let prev = prev_prices.get(&c.id).copied().unwrap_or(1.0);
            print_market_row(&c.id, c.price, c.demand, c.supply, prev);
            prev_prices.insert(c.id.clone(), c.price);
        }

        tick_num += 1;

        // In IPC mode, pace the sim at roughly 1 tick/second so Godot can follow
        if run_forever {
            tokio::time::sleep(std::time::Duration::from_millis(1000)).await;
        }
    }

    tracing::info!(tick_count = world.tick, "Run complete");
    println!("\n  {GREEN}✓{RESET} {BOLD}{} ticks completed.{RESET}", world.tick);
    println!("  {DIM}Final mean satiation: {:.3}{RESET}", world.mean_satiation());
    println!("{BOLD}{WHITE}{}{RESET}\n", "═".repeat(70));

    Ok(())
}
