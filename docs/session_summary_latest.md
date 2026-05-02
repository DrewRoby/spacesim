# Session Summary & Forward Plan
## Progress, Current Blocker, and Next Steps

> *Written at end of Session 1. Read this at the start of Session 2.*

---

## What We Built

This session was unusually productive for a first session. In roughly
chronological order:

**Design documents produced (all in `/docs`):**
- `game_strategy.md` — top-level architecture, stack choices, development phases
- `behavioral_model_design.md` — OCEAN trait system, needs hierarchy, modular
  synthesizer architecture
- `lifecycle_heritability_design.md` — lifecycle stages, trait heritability engine,
  mate selection, demographic module
- `substrate_standard_human_design.md` — biological substrate layer, Standard Human
  parameter set, second-order propensities, race/class design philosophy, UI sketch
- `repo_architecture.md` — full repository layout, crate map, file destinations,
  bootstrapping sequence, tooling decisions

**Working code:**
- Complete Rust workspace scaffold (5 crates: types, core, ipc, bindings, cli)
- `cargo build` completing cleanly with only an expected unused-import warning
- Headless sim runner ticking correctly (`cargo run -p spacesim-cli -- --ticks 10`)
- Python package structure (`spacesim_models`) with all submodule directories
- `SpeciesSubstrate` dataclass with full validation and TOML loading
- `compute_propensities()` — ten propensity functions with real weighted math
- `tools/run_propensities.py` producing correct, readable, colored output against
  Standard Human and three comparison variants
- `tools/validate_repo.py` — repo structure checker
- `tools/bootstrap_stubs.py` — stub file generator

**The model produced its first real output** — propensity values that are
internally consistent and pass intuition checks against human behavioral
economics (high tribalism, high ideological susceptibility, moderate cooperative
radius, etc.). Cross-variant comparisons (anxious species, cooperative species,
extreme loss aversion) produced directionally correct diffs.

**The Python→Rust bridge was designed but not yet running** — PyO3 bindings in
`sim/cli/src/main.rs` call `spacesim_models.api.compute_propensities_from_toml()`,
but `cargo build` did not complete cleanly before the session ended due to the
environment issue described below.

---

## The Blocker: What We Know

The symptom is: `cargo build` fails while trying to satisfy PyO3's Python
dependency, and the Python package dependencies (`pymc`, `scipy`, etc.) are
producing version conflicts that cycle with each other depending on which Python
version is active.

The user cycled from Python 3.14 down to 3.9 trying to find a stable
combination, without reaching one.

---

## Possible Misdiagnoses — Read Before Assuming

Before diving into solutions, it's worth stepping back to ask whether the
problem is actually what it appears to be. There are several plausible
misdiagnoses:

### Misdiagnosis 1: "This is a PyO3 problem"

PyO3 0.21 supports Python 3.8 through 3.13. The Python *version* is almost
certainly not the PyO3 constraint — PyO3 is quite permissive. The error is
more likely one of:
- PyO3 can't *find* the Python interpreter (environment isolation issue)
- PyO3 found the wrong interpreter (multiple Pythons on PATH)
- The Python packages are conflicting with *each other*, not with PyO3

**What to check:** Does `cargo build` fail with a PyO3 linker/compile error,
or does `pip install -e models/` fail? These are different problems with
different solutions.

### Misdiagnosis 2: "I need to change the Python version"

Cycling Python versions is rarely the right fix for package conflicts. The
right fix is almost always environment isolation. If you're installing into
the system Python, you're fighting every other Python package on the machine
for compatible versions.

**What to check:** Has the Python package ever been installed into a clean
virtual environment (`python -m venv .venv && source .venv/bin/activate &&
pip install -e models/`)? If not, that's the first real thing to try.

### Misdiagnosis 3: "I need all the ML packages now"

`pymc`, `scipy`, `factor_analyzer`, `hdbscan`, `scikit-learn` — these are
heavy scientific packages with complex dependency graphs and native extensions.
But we don't actually *use* any of them yet. `compute_propensities()` as
currently written uses only Python stdlib (`math`, `dataclasses`, `tomllib`).

**The real question:** Does `pip install -e models/` need to install all of
`requirements.txt` right now, or can we trim `pyproject.toml` to just the
packages we actually use today (which is: nothing beyond stdlib) and add the
heavy packages incrementally as we need them?

### Misdiagnosis 4: "The architecture needs to change (C, separate processes)"

This is the most tempting misdiagnosis because it feels like a principled
response to a technical problem. But changing to C, or separating the Python
into a subprocess, would be a significant architectural decision made in
response to what is almost certainly an environment configuration problem —
not a fundamental incompatibility.

The subprocess architecture *is* worth considering on its own merits (see
below), but it should not be chosen as a workaround for a pip conflict.

---

## The Real Options (Architectural, Not Just Environmental)

With clear heads, there are three viable architectures for the Python↔Rust
bridge. All three are sound. The choice is about tradeoffs, not about which
one "works."

### Option A: PyO3 Embedded (Current Design)

Rust embeds a Python interpreter via PyO3 and calls Python functions directly
in-process.

**Pros:**
- Zero IPC overhead — function call latency
- Shared memory — no serialization for large state
- Clean error propagation (Python exceptions become Rust errors)
- Already designed and partially implemented

**Cons:**
- Python interpreter is linked at compile time — version pinning is real
- Virtual environment management becomes part of the Rust build process
- The heavy ML packages (pymc etc.) are loaded into the sim process

**When it breaks:** Exactly the scenario we're in — environment conflicts
during the compile/link phase.

**Fix effort:** Likely just a virtual environment + trimmed requirements.
Probably 20 minutes with fresh eyes.

### Option B: Python as a Subprocess / Local Service

The Rust sim spawns Python as a child process and communicates over stdin/stdout
or a local socket. The Python layer is a long-running service that responds to
requests.

**Pros:**
- Complete isolation — no linking, no version pinning in cargo build
- Python crashes don't take down the sim
- Python can be restarted independently (hot reload of models)
- Already have IPC infrastructure from the Godot bridge

**Cons:**
- Serialization overhead on every call (msgpack or JSON)
- More moving parts to manage at startup
- Latency per call (fine for per-tick model calls, would matter for inner loops)

**When it's right:** If the model layer becomes a long-running service with
its own lifecycle (which it probably should, eventually). Also right if we
want to be able to hot-reload model parameters without restarting the sim.

**Verdict:** This is the more *correct* long-term architecture even independent
of the current blocker. The current blocker might actually be pushing us in the
right direction.

### Option C: Compile Python to Native (Cython / mypyc)

Compile the Python behavioral model to a native extension module, link that
into Rust.

**Pros:**
- Performance of compiled code
- No runtime interpreter dependency

**Cons:**
- Massive increase in build complexity
- Loses the "iterate on the model without recompiling" benefit
- The whole point of Python here is fast iteration — compiling defeats that
- Not worth it at this stage

**Verdict:** Ruled out. The iteration speed benefit of Python is worth more
than the performance gain at this stage.

---

## Recommended Next Session Plan

### Step 1: Diagnose Before Fixing (15 minutes)

Answer these questions before touching anything:

```bash
# Which Python is active right now?
which python3
python3 --version

# Does PyO3's build fail, or does pip fail first?
# Try installing ONLY the packages we actually use right now:
pip install tomllib   # (actually stdlib in 3.11+, so this might be a no-op)

# Try the absolute minimum install:
pip install -e models/ --no-deps
python3 -c "from spacesim_models.substrate import SpeciesSubstrate; print('OK')"

# If that works, the model layer runs. Does cargo build work then?
cargo build
```

If `pip install -e models/ --no-deps` + `cargo build` succeeds, the problem
is entirely in the heavy ML dependencies — none of which we need yet.

### Step 2: Trim `pyproject.toml` Dependencies

Remove everything from `[project] dependencies` that we don't use yet:

```toml
# KEEP (used now):
# nothing — compute_propensities uses only stdlib

# ADD BACK as we actually use them:
# numpy          ← when we do matrix math in heritability engine
# scipy          ← when we need statistical distributions
# pymc           ← when we do Bayesian population modeling
# scikit-learn   ← when we run archetype clustering
# hdbscan        ← when we run archetype clustering
```

The whole `pyproject.toml` dependencies list becomes empty for now. This is
correct — we add dependencies when we need them, not speculatively.

### Step 3: Decide on Subprocess vs Embedded

With a working minimal build, make the architecture decision cleanly:

**Keep PyO3 embedded if:** The minimal build works and feels stable. The
performance benefit of in-process calls is worth managing the environment.

**Switch to subprocess if:** Even the minimal build has friction, OR if the
hot-reload benefit (change Python model without restarting Rust sim) seems
valuable for the design iteration workflow we'll be doing.

The subprocess architecture maps well onto what we already have: the IPC
server in `sim/ipc` already handles async message passing. We'd add a
`ModelService` alongside it that speaks to Python instead of Godot.

### Step 4: Get the Pipeline Green

Whichever architecture, the goal for next session is the same end state:
`cargo run -p spacesim-cli -- --species data/species/standard_human.toml`
prints propensity bars. When that works, the full pipeline — TOML → Python
math → Rust display — is real and everything else builds on it.

### Step 5: First Commodity (if time)

Once the pipeline is green, add a single commodity to world state — food/oxygen
is the natural choice since it maps to Tier 1 survival needs. The goal is to
see it appear in tick logs and to have the Standard Human's survival need
urgency influence its demand signal, however crudely.

That's the moment the behavioral model starts shaping the economy.

---

## State of the Repo at Session End

```
✓ Cargo workspace builds (without PyO3 CLI changes)
✓ Headless sim runs 10 ticks cleanly
✓ Python model produces correct propensity output via run_propensities.py
✗ cargo build with PyO3 CLI does not complete
✗ Rust→Python pipeline not yet running end-to-end
~ cli/src/main.rs, cli/Cargo.toml written but not buildable yet
~ sim/types/src/propensities.rs written but not integrated
```

**Safe fallback:** The last clean `cargo build` state is the pre-PyO3 CLI.
If needed, revert `sim/cli/Cargo.toml` and `sim/cli/src/main.rs` to the
stub versions to restore a clean build while the environment is sorted.

---

*Pick up here next session. Diagnose first, fix second, build third.*
