# Behavioral Model Design
## OCEAN Mapping · Needs Hierarchy · Modular Signal Architecture

---

## The Central Metaphor: The Personality Synthesizer

Before getting into specifics, it's worth establishing the organizing metaphor
because it isn't just poetic — it's a genuine architectural decision.

A modular synthesizer works like this:

- **Modules** each do one thing: generate a signal, shape a signal, gate a signal,
  combine signals, delay a signal
- **Patch cables** connect module outputs to module inputs in arbitrary topologies
- **CV (Control Voltage)** is the universal signal format — any output can modulate
  any input, because they all speak the same language
- **The patch** — the specific wiring diagram — is the instrument, not the modules
  themselves. Two synthesizers with identical modules but different patches produce
  completely different sounds.

This maps onto personality and behavior almost perfectly:

| Synth Concept | Behavioral Model Equivalent |
|---|---|
| Oscillator | Trait generator (continuous signal, e.g. Openness = 0.73) |
| Filter | Need shaper (sculpts raw drive into specific desire) |
| Envelope | Emotional state (shapes intensity over time, has attack/decay) |
| LFO | Mood (slow oscillation that modulates other signals) |
| VCA (amplifier) | Attention/salience gate (how much a signal reaches behavior) |
| Mixer | Priority resolver (combines competing need signals) |
| CV input | Any modulator input — trait modulating need, stress modulating trait, culture modulating everything |
| Patch cable | A defined relationship between two parameters |
| Patch | The complete wiring of a personality configuration |

The key insight: **everything speaks the same signal language** (normalized floats,
roughly 0.0–1.0 or -1.0–1.0 depending on the module). This is what makes it
"swap modules like a modular synth" — as long as the signal contract is honored,
any module can plug into any other.

---

## Layer 1: Trait Modules (The Oscillators)

OCEAN provides five continuous parameters. These are not behaviors — they are
raw generative signals that modulate everything downstream.

### The Five Traits and What They Actually Drive

---

**Openness** (0.0–1.0)
*The novelty signal*

High Openness = strong appetite for the unknown, the new, the frontier.
Low Openness = preference for established, familiar, proven.

| Domain | Low Openness | High Openness |
|---|---|---|
| Market behavior | Buys known brands, established routes | Early adopter, frontier goods, exotic imports |
| Exploration | Stays in charted space | Actively funds/pursues discovery |
| Technology | Late adopter, resists new tech | R&D investor, beta adopter |
| Risk profile | Avoids unpriced risk | Tolerates ambiguity premium |
| Information | Trusts established sources | Seeks novel signals, rumors |

Openness is the primary driver of **exploration demand** and **technology diffusion
curves**. A high-Openness population creates real markets for frontier goods
before supply chains exist to serve them.

---

**Conscientiousness** (0.0–1.0)
*The time-horizon signal*

High Conscientiousness = long planning horizon, deferred gratification, reliability.
Low Conscientiousness = short time horizon, impulsive, unreliable as a counterparty.

| Domain | Low Conscientiousness | High Conscientiousness |
|---|---|---|
| Market behavior | Spot market buyer, impulsive purchasing | Futures buyer, subscription contracts |
| Savings rate | Near-zero, fully consumed | High, maintains reserves |
| Infrastructure | Underinvests in maintenance | Over-invests, redundant systems |
| Contract reliability | Defaults under pressure | Honors contracts even at cost |
| Demand volatility | High variance, unpredictable | Low variance, smooth and forecastable |

Conscientiousness is the primary driver of **credit market behavior**, **supply
chain stability**, and **infrastructure investment rates**. A low-Conscientiousness
population has real purchasing power but is a terrible long-term trading partner.

---

**Extraversion** (0.0–1.0)
*The social density signal*

High Extraversion = draws energy from social contact, status-seeking, expressive.
Low Extraversion = self-sufficient, private, low social overhead.

| Domain | Low Extraversion | High Extraversion |
|---|---|---|
| Market behavior | Utility goods, private consumption | Status goods, visible consumption |
| Information network | Small trusted network, slow spread | Wide network, fast information spread |
| Political behavior | Disengaged, apolitical | Faction-joining, opinion leadership |
| Entertainment | Solo consumption (archives, libraries) | Events, communal experiences |
| Labor market | Specialist, deep individual work | Management, sales, coordination roles |

Extraversion is the primary driver of **status goods markets**, **information
propagation speed**, and **faction cohesion**. High-Extraversion populations are
volatile — they are susceptible to market manias, moral panics, and cascade effects.

---

**Agreeableness** (0.0–1.0)
*The cooperation signal*

High Agreeableness = trusting, cooperative, altruistic, conflict-averse.
Low Agreeableness = competitive, suspicious, self-interested, confrontational.

| Domain | Low Agreeableness | High Agreeableness |
|---|---|---|
| Trade behavior | Adversarial negotiation, zero-sum | Cooperative, positive-sum seeking |
| Mutual aid | Minimal, transactional | Strong commons, mutual insurance |
| Response to scarcity | Hoarding, price gouging | Rationing, sharing |
| Faction relations | Conflict-prone, territorial | Diplomatic, alliance-prone |
| Labor relations | Strikes, exploitation cycles | Negotiated agreements, stability |

Agreeableness is the primary driver of **trade friction**, **diplomatic outcomes**,
and **how populations respond to supply shocks**. A low-Agreeableness population
in scarcity conditions creates cascading market failures; a high-Agreeableness one
self-organizes rationing.

---

**Neuroticism** (0.0–1.0)
*The threat-sensitivity signal*

High Neuroticism = easily stressed, threat-focused, emotionally reactive.
Low Neuroticism = emotionally stable, stress-resistant, slow to alarm.

| Domain | Low Neuroticism | High Neuroticism |
|---|---|---|
| Risk aversion | Accepts volatility | Pays large premiums for certainty |
| Security spending | Minimal | Outsized, disproportionate to actual threat |
| Response to events | Slow to react, absorbs shocks | Fast, amplifies shocks into cascades |
| Demand stability | High during stress | Collapses or spikes non-linearly |
| Insurance markets | Thin, undersupplied | Deep, dominant economic sector |

Neuroticism is the **amplifier knob on the whole system**. High Neuroticism doesn't
change what people want — it makes them want it more urgently and more
irrationally. It is the primary driver of **market volatility**, **panic buying**,
and **security/defense spending beyond rational levels**.

---

## Layer 2: The Needs Hierarchy (The Filters)

Traits tell us *who someone is*. Needs tell us *what they want right now*. The
Needs layer sits between traits and market behavior.

We use a modified Maslow hierarchy — five tiers, but reframed for an interstellar
economic context. The key architectural point: **needs are not binary (met/unmet)**,
they are continuous satiation states with non-linear urgency curves.

```
URGENCY
  │
1 │     ██
  │    ████
  │   ██████
  │  █████████
  │ █████████████████___________
  └────────────────────────────── SATIATION
  0%                            100%
```

The urgency curve is steep when barely met, and approaches zero as satiation
approaches ~80%. Beyond ~80%, additional satiation actually reduces urgency
below baseline — the **surplus state** — which produces qualitatively different
demand (luxury, status, experiential rather than functional).

---

### Tier 1: Survival Needs
*Oxygen, food, water, thermal regulation, medical baseline*

These are the only needs with a **hard floor** — below a threshold they produce
not just high urgency but behavioral override (rationality degrades, social norms
break down, everything else in the hierarchy becomes temporarily invisible).

**OCEAN modulation:**
- Conscientiousness adjusts **reserve-building** behavior (how much surplus
  survival stock is maintained above current need)
- Neuroticism adjusts the **alarm threshold** — high-N populations begin showing
  survival anxiety at much higher satiation levels than objective need warrants
- Agreeableness determines whether scarcity produces **sharing or hoarding**

**Market signals generated:**
- Basic commodity demand (food, atmo, water, pharmaceuticals)
- Emergency price insensitivity when below satiation floor
- Stockpiling behavior from high-C + high-N combinations

---

### Tier 2: Security Needs
*Physical safety, stable governance, predictable supply chains, personal continuity*

Security needs are not just about physical threat — they encompass **predictability
of the future**. An unstable currency, an unreliable trade route, or a government
on the verge of collapse all trigger security need deficits.

**OCEAN modulation:**
- Neuroticism is the dominant modulator — high-N populations have permanently
  elevated security need urgency regardless of objective conditions
- Conscientiousness drives the **form** of security-seeking: high-C populations
  build reserves and systems; low-C populations seek protectors and dependencies
- Agreeableness shapes **collective vs individual** security strategies (mutual
  defense pacts vs personal armament)

**Market signals generated:**
- Defense and weapons demand
- Insurance and derivatives markets
- Political stability premium on trade routes
- Private security services
- Information markets (threat intelligence)

---

### Tier 3: Belonging Needs
*Community membership, cultural identity, faction affiliation, recognized relationships*

This tier is where **social structure** emerges from individual psychology at scale.
Belonging needs drive the formation of factions, guilds, religions, and cultural
identities — not as authored content, but as emergent solutions to a population-wide
need deficit.

**OCEAN modulation:**
- Extraversion is the primary modulator: high-E populations have steep belonging
  urgency and invest heavily in social goods; low-E populations have much lower
  baseline urgency here
- Agreeableness shapes **in-group vs out-group** behavior — low-A populations
  satisfy belonging needs through tribal identity and exclusion as much as inclusion
- Openness affects **tolerance of cultural diversity** within a belonging group

**Market signals generated:**
- Cultural goods (art, music, narrative media)
- Communal spaces and meeting infrastructure
- Faction insignia, uniforms, symbolic goods (status markers of membership)
- Communication infrastructure demand
- Pilgrimage/travel to culturally significant sites

---

### Tier 4: Esteem Needs
*Recognition, status, competence demonstration, reputation, legacy*

The tier where **luxury goods and status markets** live. Esteem needs only become
economically dominant once the lower three tiers are reasonably satisfied — which
means they are a lagging indicator of prosperity, and **their market size is one of
the best signals of a population's overall economic health**.

**OCEAN modulation:**
- Extraversion determines whether esteem is sought **publicly** (visible luxury,
  titles, trophies) or **privately** (personal mastery, private collection)
- Conscientiousness shapes whether esteem is sought through **achievement**
  (high-C) or **display** (low-C)
- Openness modulates what counts as prestigious — high-O populations confer
  esteem on novelty and exploration; low-O populations confer esteem on
  tradition and heritage

**Market signals generated:**
- Luxury goods of all categories
- Titles, certifications, ranking systems
- Patronage of arts and science
- Competitive markets (where winning matters beyond material stakes)
- Reputation services and record-keeping

---

### Tier 5: Transcendence Needs
*Meaning, legacy, ideological expression, the beyond-self*

The highest tier — and the one most capable of overriding all others, which is
what makes it dangerous and interesting. A population with strong transcendence
needs will accept material sacrifice (lower satisfaction of tiers 1-4) in pursuit
of ideological or existential goals.

This tier generates **zealotry, exploration imperatives, religious markets,
political idealism, and the willingness to colonize genuinely hostile environments
for non-economic reasons**.

**OCEAN modulation:**
- Openness is the primary driver: high-O populations generate strong transcendence
  need urgency naturally
- Neuroticism interacts dangerously here — high-N + high-Transcendence
  combinations produce ideological extremism (threat sensitivity channeled into
  an absolute worldview)
- Conscientiousness determines the **form**: long-horizon legacy-building (high-C)
  vs ecstatic present-tense expression (low-C)

**Market signals generated:**
- Exploration funding (intrinsic, not ROI-driven)
- Religious/ideological infrastructure
- Art at the highest investment levels
- Education and knowledge preservation
- Willingness to accept frontier conditions for ideological reasons

---

## Layer 3: The Modular Architecture (The Patch)

Here is where the synthesizer metaphor becomes the actual system design.

### Signal Flow Diagram

```
ENVIRONMENT ──────────────────────────────────────────────────┐
(prices, events, threat level, supply conditions)             │
                                                              ▼
TRAIT MODULES          MODULATION LAYER          NEEDS ENGINE
┌──────────┐          ┌──────────────────┐      ┌──────────────────┐
│ Openness ├──CV──────► Stress Amplifier │      │ Tier 1: Survival │
│   0.73   │          │ (Neuroticism×    │      │ satiation: 0.91  │
└──────────┘          │  threat_level)   ├─────►│ urgency: 0.12    │
┌──────────┐          └──────────────────┘      └────────┬─────────┘
│Conscient.│                                             │
│   0.61   ├──CV──────► Time Horizon     │      ┌────────▼─────────┐
└──────────┘          │ Filter           │      │ Tier 2: Security │
┌──────────┐          └──────────────────┘      │ satiation: 0.54  │
│Extravers.│                                    │ urgency: 0.71    │
│   0.44   ├──CV──────► Social Density   │      └────────┬─────────┘
└──────────┘          │ Amplifier        │               │
┌──────────┐          └──────────────────┘      ┌────────▼─────────┐
│Agreeable.│                                    │  Tier 3: Belong  │
│   0.58   ├──CV──────► Cooperation     │      │ satiation: 0.77  │
└──────────┘          │ Modifier        │      │ urgency: 0.31    │
┌──────────┐          └──────────────────┘      └────────┬─────────┘
│Neuroticm.│                                             │
│   0.82   ├──CV──────► (multiple       │      ┌────────▼─────────┐
└──────────┘          │  destinations)  │      │ Tier 4: Esteem   │
                      └─────────────────┘      │ satiation: 0.44  │
                                               │ urgency: 0.53    │
MOOD LAYER                                     └────────┬─────────┘
┌──────────────────┐                                    │
│ Emotional State  │  (LFO — slow oscillation)  ┌────────▼─────────┐
│ current: anxious ├───────────────────────────►│ Tier 5: Transcen │
│ decay: 0.03/tick │                            │ satiation: 0.29  │
└──────────────────┘                            │ urgency: 0.62    │
                                                └────────┬─────────┘
MEMORY MODULE                                            │
┌──────────────────┐                                     │
│ Past prices      ├────────────────────────────┐        │
│ Past events      │                            ▼        ▼
│ Trust ledger     │                     ┌──────────────────────┐
└──────────────────┘                     │   PRIORITY MIXER     │
                                         │ (resolves competing  │
SOCIAL MODULE                            │  urgencies into a    │
┌──────────────────┐                     │  ranked demand vector│
│ Peer signals     ├────────────────────►│ )                    │
│ Faction norms    │                     └──────────┬───────────┘
│ Trend data       │                                │
└──────────────────┘                                ▼
                                         ┌──────────────────────┐
                                         │   DECISION MODULE    │
                                         │ (maps demand vector  │
                                         │  to market actions)  │
                                         └──────────┬───────────┘
                                                    │
                                                    ▼
                                            MARKET SIGNALS
                                        (commodity demand, bids,
                                         faction actions, etc.)
```

---

### The Modules

Each module is a discrete unit with:
- **Inputs** (CV signals it accepts)
- **Outputs** (CV signals it produces)
- **Internal state** (persists between ticks)
- **Parameters** (the knobs — tunable constants)

This means every module can be hot-swapped, mocked for testing, or replaced
with a completely different implementation as long as it honors the signal contract.

---

**Trait Module**
- *What it does:* Holds the base OCEAN scores and outputs them as continuous signals
- *Inputs:* Optional CV modulation (culture, long-term experience can shift baseline traits slowly over time)
- *Outputs:* Five CV signals (O, C, E, A, N)
- *Parameters:* Base scores, plasticity rate (how fast traits drift under sustained pressure), floor/ceiling constraints
- *Swap opportunities:* Replace static traits with a dynamic trait model that drifts based on life events; or a trauma model that spikes Neuroticism on certain event types

---

**Needs Module (one per tier)**
- *What it does:* Maintains current satiation state, computes urgency from satiation using a configurable curve, outputs urgency signal
- *Inputs:* Satiation changes (from consumption), CV from trait modules (modulate urgency curve shape), environmental stress CV
- *Outputs:* Urgency signal (0.0–1.0), deficit signal (how far below comfortable satiation), surplus signal (how far above satiation threshold)
- *Parameters:* Satiation floor (survival override threshold), urgency curve shape (steepness, inflection point), trait modulation weights, decay rate (unsatisfied needs get more urgent over time)
- *Swap opportunities:* Replace Maslow-style hierarchy with a different need theory (ERG theory, Alderfer's model); add new need tiers for exotic civilizations; use empirically-fit curves from real economic data

---

**Stress Module**
- *What it does:* Aggregates environmental threat signals and amplifies Neuroticism's effect on all downstream modules
- *Inputs:* Threat level CV (from world state: war, scarcity, political instability), N trait signal
- *Outputs:* Amplified urgency multiplier (fed to all need modules), emotional state signal
- *Parameters:* Stress sensitivity, recovery rate, threshold for panic state (non-linear jump)
- *Swap opportunities:* Add post-traumatic stress model (stress leaves a residual baseline that decays slowly); swap for a pure rational-actor model (no stress amplification) for testing

---

**Memory Module**
- *What it does:* Maintains a rolling history of prices, events, and outcomes. Outputs expectation signals that modify current decision-making
- *Inputs:* Current prices, event notifications, outcome records
- *Outputs:* Price expectation CV, trust signals per counterparty, risk-adjusted value estimates
- *Parameters:* Memory window length, recency weighting (how much recent events dominate), forgetting rate
- *Swap opportunities:* Replace with a Bayesian belief-update model; add a "generational memory" model where collective trauma persists beyond individual memory windows; mock with a flat expectation model for baseline comparison

---

**Social Module**
- *What it does:* Injects peer effects, faction norms, and trend signals. Models the degree to which a population's behavior is shaped by what others around them are doing
- *Inputs:* Peer behavior aggregates, faction norm broadcasts, trend data, E trait CV (Extraversion modulates susceptibility)
- *Outputs:* Conformity pressure CV (modulates decision module), trend amplification signal, information spread rate
- *Parameters:* Baseline conformity pressure, Extraversion sensitivity weight, network density, echo chamber coefficient
- *Swap opportunities:* Add a propaganda module that injects synthetic social signals; replace with a network topology model (influencers, clusters, bridges); add a fashion cycle model for status goods

---

**Priority Mixer**
- *What it does:* Takes all need urgency signals and produces a ranked demand vector. This is where competing needs get resolved — the "what do I spend on first" decision
- *Inputs:* All five need urgency signals, available resource signal (purchasing power)
- *Outputs:* Ranked demand vector with budget allocation proportions
- *Parameters:* Tier hierarchy weight (lower tiers always outcompete higher tiers below their floor), diminishing returns curve across the vector, budget elasticity
- *Swap opportunities:* Replace with a lexicographic model (strict hierarchy, no tradeoffs); use a utility-maximization model; swap in a prospect theory model (losses weighted differently than gains)

---

**Decision Module**
- *What it does:* Converts the ranked demand vector into concrete market actions — bids, offers, investments, migration decisions, political acts
- *Inputs:* Demand vector, price signals from market, available options set, Memory module expectations
- *Outputs:* Market orders (buy/sell/invest), faction actions, migration pressure
- *Parameters:* Search cost tolerance, satisficing threshold (good-enough vs. optimal), risk tolerance (fed from Neuroticism), time discount rate (fed from Conscientiousness)
- *Swap opportunities:* This is the most powerful swap point. Replace the default bounded-rationality model with: a purely rational model for comparison; a habit-formation model; a dual-process model (fast/intuitive vs. slow/deliberate); or an ideologically-constrained model for zealot archetypes

---

### The Knob/Slider/Button Taxonomy

Every tunable parameter in the system falls into one of these categories:

**Structural knobs** (change what the model fundamentally is)
- Urgency curve shape per need tier
- Priority mixer hierarchy weights
- Which decision model the Decision Module uses
- Memory window length and forgetting curve

**Amplitude sliders** (change how loud a signal is)
- Trait modulation weights (how much Neuroticism amplifies stress)
- Social conformity pressure strength
- Stress response sensitivity
- Memory recency weighting

**Threshold buttons** (change when qualitative transitions happen)
- Survival override floor (below this, rationality breaks)
- Panic threshold in the Stress Module
- Luxury surplus threshold (above this, goods become status goods)
- Trust collapse threshold (below this, trade friction becomes prohibitive)

**Clock controls** (change timing and rates)
- Need urgency decay rate (how fast unmet needs become more urgent)
- Trait plasticity rate (how fast baseline traits drift)
- Stress recovery rate
- Memory forgetting rate

---

## Population vs Individual Representation

One design decision that shapes everything: are we modeling individuals or
distributions?

**Individual agent model:** Each NPC is a discrete entity with their own OCEAN
scores running their own full signal chain. Expensive, but produces rich emergent
social dynamics.

**Distribution model:** Each population unit (a city, a faction, a ship crew)
is represented as a *distribution* over trait space — a mean and variance for
each OCEAN dimension, plus correlation structure between dimensions. The signal
chain operates on the distribution's statistics, producing aggregate demand
vectors directly. Cheaper by orders of magnitude.

**The hybrid that probably makes sense here:** Distributions for the background
economy and named factions. Individual agent models only for player-facing
characters and faction leaders. The distribution model feeds aggregate market
signals; the individual agents create the storylines.

This means the system needs to support both:
- `AgentPersonality` — full signal chain for a single individual
- `PopulationPersonality` — statistical aggregate, mean/covariance over OCEAN,
  runs the same modules but on distribution math rather than point values

Both honor the same module interface. Both produce market signals in the same
format. The Priority Mixer and Decision Module don't care whether their inputs
came from a single agent or a population of ten thousand.

---

## The Archetype Emergence Pipeline

Archetypes are not authored. They emerge from clustering the distribution space.

1. Run the simulation with initial population distributions
2. Observe the demand vectors and behavioral patterns that emerge
3. Run k-means or HDBSCAN clustering on the (trait scores × need satiation × 
   behavioral output) space
4. Label the clusters: whatever falls out of the math becomes the game's faction 
   archetypes — Pioneers, Hoarders, Merchants, Zealots, etc.
5. Re-run periodically — archetypes should drift as the world changes

This is what makes it honest: the archetypes are *found*, not invented. If the
simulation produces something unexpected in cluster space, that's a signal the
psychology is doing something interesting.

---

## Open Design Questions

1. **Trait plasticity** — should OCEAN scores be fixed for a population, or drift
   under sustained conditions? (Sustained scarcity pushing Neuroticism up; 
   generations of peace pushing Agreeableness up.) This adds huge richness but
   makes the system much harder to reason about.

2. **Cross-population infection** — can behavioral traits spread? Does a high-E
   population's enthusiasm propagate to neighboring low-E populations via trade
   contact? This is essentially a cultural diffusion model on top of the personality model.

3. **Player psychology** — does the player have an OCEAN score? One interesting
   design: the player's observed behaviors over time cause the game to *infer*
   their psychological profile, and NPCs respond to the player as a psychological
   actor, not just a mechanical one.

4. **Discontinuities** — what happens at civilizational stress events? Famines,
   wars, first contact? Does the trait distribution *jump* discontinuously, or
   does it drift? The answer probably varies by tier of the Maslow hierarchy and
   by the severity of the event.

5. **The ideology module** — transcendence needs generate ideological demand, but
   ideologies also modulate all the other needs (a religion that suppresses esteem
   needs, or amplifies security needs). This creates a feedback loop between
   the top of the hierarchy and the bottom. Is that a sixth module, or a special
   case of the Social Module?

---

*This document defines the conceptual architecture. Implementation begins in `/models/`.*
