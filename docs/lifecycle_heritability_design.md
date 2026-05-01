# Lifecycle, Heritability & Trait Evolution
## An Extension to the Behavioral Model Design

> *Extends: behavioral_model_design.md*
> *Depends on: OCEAN trait system, Needs hierarchy, Module architecture*

---

## The Gap in the Current Model

The behavioral model as currently designed treats population trait distributions
as stable parameters — they can be tuned, and individuals can drift slowly under
sustained pressure (trait plasticity), but there is no mechanism by which a
population fundamentally *becomes different people* over time.

This is wrong in an important way. In the real world, trait distributions change
primarily not because individuals change, but because:

1. **New individuals are born** with trait profiles inherited from — but not
   identical to — their parents, shaped additionally by developmental environment
2. **Old individuals die**, removing their trait profiles from the distribution
3. **Differential reproduction** means some trait profiles produce more offspring
   than others, shifting the distribution even if every individual is static

This is population genetics applied to psychology. The trait distribution of a
civilization *evolves* over generations, and the mechanism is the lifecycle.

The current model needs a Lifecycle Layer sitting below the Trait Module,
driving the slow-timescale evolution of who the population fundamentally is.

---

## What Behavioral Genetics Actually Tells Us

Before designing the model, it's worth grounding this in the science. OCEAN trait
heritability is one of the better-studied areas of behavioral genetics. Twin
studies consistently produce these heritability estimates:

| Trait | Heritability | Notes |
|---|---|---|
| Openness | ~57% | Highest heritability of the five |
| Conscientiousness | ~49% | |
| Extraversion | ~54% | |
| Agreeableness | ~42% | Most environmentally plastic |
| Neuroticism | ~48% | |

What the remaining variance breaks down to:
- **Shared environment** (~10–15%): the family, community, and civilization context
  during development — the "same household" effect
- **Non-shared environment** (~25–35%): unique individual experiences, the
  specific luck of what happens to you personally
- **Developmental noise** (~5–10%): genuinely stochastic variation — quantum
  randomness of development, if you like

The key implication: **traits are substantially but not fully heritable**. A child
is not a deterministic blend of their parents. There is real variance around the
heritable component, and that variance is shaped by the developmental environment.
This is what makes evolution possible — pure heritability with no variance would
just lock traits in place forever.

---

## The Lifecycle Model

### Lifecycle Stages

Rather than continuous age, we use discrete stages. This is computationally
friendlier and maps better to game systems (you care about what stage an agent
is in, not their precise age). The actual time-durations are civilization
parameters — a species with a 200-year lifespan uses different numbers but the
same stage logic.

```
CONCEPTION ──► DEVELOPMENT ──► YOUTH ──► ADULT ──► ELDER ──► DEATH
                    │              │         │         │
                    │              │         │         │
              [Traits being   [Traits     [Traits   [Traits
               formed from     mostly      locked,   drifting
               heritable +     plastic,    stable    toward
               environment]    learning]   output]   settled
                                                      values]
```

**Development Stage** *(pre-social, trait formation)*
- Trait values are not yet set — they are being assembled from genetic inheritance
  plus environmental input
- The agent is not a market participant, not a faction member
- High sensitivity to environmental conditions: scarcity, violence, stability,
  cultural richness all leave permanent marks
- This is where intergenerational trauma enters: a Development Stage spent in
  crisis conditions produces an Adult with a permanently elevated Neuroticism floor
- Duration: ~15–20% of lifespan (configurable per civilization)

**Youth Stage** *(trait plasticity at maximum)*
- Trait values are set but highly plastic — sustained experiences still reshape them
- Beginning to participate in markets (labor, social goods), but not yet fully
- This is where education, propaganda, and cultural exposure have their strongest
  effect on trait values
- Mate selection begins (often poorly, biased toward proximate and available)
- Duration: ~15% of lifespan

**Adult Stage** *(primary economic participation, traits mostly stable)*
- Traits are largely locked in — significant events can still cause shifts, but
  the baseline is resistant
- Full market participation: labor, goods, political action, reproduction
- This stage generates the bulk of the economic signal the simulation cares about
- Mate selection is active and more sophisticated (resource assessment, value
  alignment, long-term signaling)
- Duration: ~40% of lifespan

**Elder Stage** *(reduced output, trait settling, wisdom effects)*
- Reduced labor market participation, reduced physical consumption needs
- Traits drift toward their "settled" values — Neuroticism often decreases,
  Agreeableness often increases, Openness polarizes (very high or very low)
- New effect: **Wisdom modifier** — accumulated Memory Module content creates
  an experience signal that improves decision quality for familiar domains
  (but may reduce flexibility for novel ones)
- Increased political weight per capita (more invested in status quo, more
  accumulated social capital)
- Duration: ~20% of lifespan, with rising mortality rate

**Death**
- The agent's trait profile is removed from the population distribution
- This is not a sad event in the model — it is the primary mechanism of
  population-level trait evolution
- Death rates are modulated by: stage (elder mortality >> adult mortality),
  environmental conditions (scarcity, disease, conflict), and trait profile
  (high-N agents have elevated stress-related mortality in sustained crisis)

---

## Trait Inheritance: The Heritability Engine

When two agents reproduce, the offspring's trait profile is computed from:

```
offspring_trait = heritable_component + environment_component + noise_component
```

### The Heritable Component

Not a simple average of the parents. The genetic model uses **quantitative
trait inheritance** — each OCEAN dimension is treated as a polygenic trait
influenced by many independent genetic loci.

In practice this means:

```
genetic_midpoint = (parent_A_trait + parent_B_trait) / 2
heritable_component = genetic_midpoint + regression_to_mean_term
```

The **regression to mean** term is important and often overlooked: offspring of
extreme parents tend to be less extreme than their parents. Two highly neurotic
parents will produce a neurotic child — but typically less neurotic than the
average of the parents, because extreme phenotypes require many genetic factors
to align, and that alignment is probabilistically disrupted in recombination.

The regression coefficient is roughly `(1 - heritability)` — so for a trait
with 50% heritability, offspring will regress ~50% of the distance from the
genetic midpoint back toward the population mean. This is what keeps trait
distributions from collapsing to extremes over generations.

### Trait Covariance: The Hidden Structure

OCEAN traits are not independent. There are stable genetic correlations between
them — pairs of traits that tend to co-vary because they share underlying genetic
architecture. The relevant ones for this model:

| Trait Pair | Correlation | Why It Matters |
|---|---|---|
| N ↑ and A ↓ | Negative (~-0.3) | High Neuroticism pulls Agreeableness down — the anxious tend toward hostility |
| O ↑ and C ↓ | Weak negative | Openness-seeking and rule-following are in mild tension |
| E ↑ and A ↑ | Positive (~+0.2) | Sociability and warmth co-vary |
| N ↑ and N offspring ↑ | Strong (~+0.5) | Neuroticism is the most parentally predictive trait |

This means inheritance is not five independent draws — it's drawing from a
**multivariate distribution with covariance structure**. In code this is a
multivariate normal draw with a covariance matrix derived from the parental
trait profiles. The covariance matrix is a civilization parameter that can
be tuned per species or culture.

### The Environmental Component

The **shared environment** effect: the developmental context the child grows
up in shifts the heritable baseline. This operates as an additive term sourced
from the current world state during the agent's Development Stage:

```
environment_component = Σ (condition_i × trait_sensitivity_i × duration_i)
```

Where conditions include:

| World Condition | Primary Trait Effect | Secondary |
|---|---|---|
| Sustained scarcity | Neuroticism +, Conscientiousness + | Openness - |
| Sustained abundance | Neuroticism -, Openness + | Conscientiousness - |
| Violence / conflict | Neuroticism +, Agreeableness - | — |
| Strong stable governance | Conscientiousness +, N - | — |
| Cultural richness | Openness + | Extraversion + |
| Isolation | Extraversion -, Openness - | — |
| High inequality | N +, Agreeableness - | Conscientiousness polarizes |

The **sensitivity** parameters determine how much each condition moves each trait,
and these are themselves modulated by the heritable component — high-N children
are *more* environmentally sensitive (this is the gene-environment interaction
effect). This creates a self-reinforcing dynamic: high-N populations raised in
bad conditions produce *more* environmentally-sensitive offspring, who are then
more damaged by the same conditions.

### The Noise Component

Genuinely stochastic. A draw from a zero-mean distribution with variance
proportional to `(1 - heritability)` for each trait. This represents the
non-shared environmental variance and developmental noise — the unpredictable
part of who you turn out to be.

The noise term is what prevents the population from collapsing to a fixed point
and enables the random variation that natural selection (or its civilizational
equivalent) acts on.

---

## Mate Selection

Even a crude mate selection model produces non-trivial dynamics because of
**assortative mating** — the empirical tendency of people to select partners
with similar trait profiles to their own.

### Why Assortative Mating Matters for the Simulation

Assortative mating on OCEAN traits causes trait distributions to become
**bimodal over generations**. If high-O individuals preferentially mate with
other high-O individuals, the O distribution in the population gradually splits
into two humps rather than remaining normally distributed. This is the
mathematical origin of naturally occurring psychological factions — they don't
need to be authored, they emerge from mate selection over generations.

This is a potentially very powerful emergent behavior: the simulation could
spontaneously generate culturally distinct sub-populations within a single
faction, purely from the math of mate selection.

### Mate Selection Model (Layered by Stage)

**Proximity filter (universal, lowest cost)**
You can only mate with someone you have social contact with. This is determined
by the Social Module's network density parameter. Isolated populations have
lower choice breadth, increasing assortative mating coefficients as a side
effect (you end up mating with people who are similar because your social
network is homogeneous).

**Trait similarity preference (primary selection criterion)**
Weighted similarity score across OCEAN dimensions. Not all traits are equally
weighted in mate selection — the empirical evidence suggests:
- Agreeableness and Extraversion are the strongest positively assorted traits
  (people strongly prefer similar levels)
- Openness is moderately positively assorted
- Conscientiousness is weakly assorted (some attraction to complementary levels)
- Neuroticism has a complicated pattern: moderate positive assortment at
  moderate levels, but very high-N individuals have *reduced* selectivity
  (anxiety drives acceptance of worse matches)

**Resource/status assessment (secondary criterion)**
Modulated heavily by the Esteem Need satiation state and by the specific
archetypes involved. Agents with high Esteem urgency weight potential partner
status more heavily. This creates a resource-trait tradeoff in the selection
function: a high-status but personality-mismatched partner can be preferred
over a low-status but well-matched one, depending on the agent's current need
state.

**Value alignment (tertiary, costly to assess)**
Agents with strong Transcendence needs assess ideological alignment before
committing. A Zealot archetype will not mate with someone from an incompatible
ideological cluster regardless of other factors. This is expensive to compute
but only matters for high-Transcendence populations.

### Reproduction Rate as a Trait Function

Different trait profiles have empirically different reproduction rates. For
the simulation, we model this as a base rate modulated by traits:

| Trait Profile | Effect on Reproduction Rate |
|---|---|
| High Conscientiousness | Reduced rate (more investment per child, more planning) |
| High Extraversion | Increased rate (more social contact, higher impulsivity) |
| High Neuroticism | Reduced rate (anxiety increases barriers, elevated stress reduces fertility) |
| High Openness | Slightly reduced rate (novelty-seeking delays commitment) |
| Low Agreeableness | Unpredictable — high conflict can increase or decrease rate |

The important emergent effect: **Conscientiousness is self-limiting**. High-C
populations produce fewer, better-resourced children. Low-C populations produce
more, worse-resourced children. Over many generations, this creates a stable
dynamic tension in any mixed population — not drift to an extreme, but a
maintained distribution.

This is the **r/K selection** dynamic from evolutionary ecology, arriving
naturally from the trait model without being authored.

---

## The Demographic Module

A new module in the synthesizer — sits outside the individual agent chain and
operates at the population level, tracking the age structure and driving births
and deaths.

```
┌─────────────────────────────────────────────────────┐
│                  DEMOGRAPHIC MODULE                  │
│                                                      │
│  Age Distribution                                    │
│  ┌────────────────────────────────────────────┐      │
│  │ Dev: 18%  │  Youth: 15%  │  Adult: 47%  │ Elder: 20% │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  Inputs:  world conditions, carrying capacity,       │
│           resource availability, conflict level      │
│  Outputs: birth events (→ Heritability Engine)       │
│           death events (→ removes from distribution) │
│           stage transition events                    │
│           dependency ratio signal (CV to market)     │
└─────────────────────────────────────────────────────┘
```

The **dependency ratio** output is an important market signal: a population
heavy in Development stage is a net consumption drain with low labor output —
it will show high Survival and Security need urgency relative to its productive
capacity. This creates real economic pressure that compounds with other
conditions.

### Demographic Transition

The model should capture the **demographic transition** — the well-documented
historical pattern where:

1. Pre-industrial: high birth rate, high death rate, stable population, young age structure
2. Early industrial: death rate falls (medicine, sanitation), birth rate stays high — population boom
3. Late industrial: birth rate falls (education, female autonomy, urbanization) — population stabilizes
4. Post-industrial: low birth rate, low death rate, aging population

This transition is not authored — it emerges from the interaction of:
- Increasing survival need satiation (death rate falls)
- Increasing Conscientiousness with prosperity (birth rate falls)
- Changing economic incentives for children (urbanization effect)

A civilization that achieves this transition will show a characteristic
demographic bulge moving through its age distribution over time — a simulation
of the baby boom, essentially. This has profound market implications (youth
bulge = high growth, explosive consumption; elder bulge = low growth,
healthcare dominance, conservative politics).

---

## Intergenerational Effects: The Long Memory

The most interesting emergent behavior of the lifecycle model is that
**population trauma and prosperity have multi-generational echoes** that the
individuals experiencing them have no direct memory of.

The mechanism:

1. Sustained scarcity during Development stage elevates adult Neuroticism baseline
2. High-N adults have more volatile market behavior, more security spending,
   reduced investment in Openness goods
3. High-N adults produce high-N offspring (heritability) in a high-N environment
   (shared environment effect) — double amplification
4. Even after the scarcity ends, the trait distribution stays elevated for
   1–3 generations before regression to mean brings it back
5. The economic behavior of the traumatized generation perpetuates the conditions
   that traumatized them (underinvestment in growth, hoarding, tribalism) —
   a third amplification path through the environment

This is a model of generational trauma with real predictive content. It also
works in the positive direction: sustained prosperity and stability produces
a cascade of low-N, high-O populations that generate the economic conditions
for further prosperity, until some external shock interrupts the cycle.

---

## Revised Module Architecture with Lifecycle

The synthesizer now has an additional pre-trait layer:

```
LIFECYCLE LAYER (slow timescale — generational)
┌─────────────────────────────────────────────────────┐
│  Demographic Module                                  │
│    ↓ births          ↓ deaths                        │
│  Heritability Engine                                 │
│    parental traits + environment + noise             │
│    → new agent trait profile                         │
│  Development Module                                  │
│    world conditions during development stage         │
│    → permanent environmental component to traits     │
└─────────────────┬───────────────────────────────────┘
                  │ feeds trait distributions into ↓
PERSONALITY LAYER (medium timescale — years)
┌─────────────────────────────────────────────────────┐
│  Trait Module → Modulation Layer → Needs Engine      │
│  (as previously designed)                           │
└─────────────────┬───────────────────────────────────┘
                  │ feeds urgency signals into ↓
BEHAVIOR LAYER (fast timescale — ticks)
┌─────────────────────────────────────────────────────┐
│  Priority Mixer → Decision Module → Market Signals   │
└─────────────────────────────────────────────────────┘
```

Three distinct timescales, each driving the layer below it:
- **Generational** (decades of sim time): lifecycle changes *who the population is*
- **Personal** (years of sim time): trait plasticity and mood change *how they behave*
- **Transactional** (days/ticks): need states and decisions change *what they buy*

The important architectural property: each layer's outputs are the slow-changing
parameters of the layer below. The Demographic Module doesn't need to run every
tick — it can run once per simulated year. The Trait Module runs more frequently
but not every tick. The Behavior Layer runs every tick because markets clear
every tick.

This tiered update rate is critical for performance at scale.

---

## New Open Questions

1. **Sexual vs asexual reproduction** — for alien civilizations, mate selection
   might work entirely differently. Is the Heritability Engine parameterized
   broadly enough to handle n-parent reproduction, clonal populations with
   occasional mutation events, or hive-mind consensus reproduction?

2. **Cultural inheritance** — memes propagate alongside genes. A child inherits
   not just trait tendencies from parents but also ideological frameworks, which
   modulate how those traits express. Is cultural inheritance modeled as a
   separate channel alongside genetic inheritance, or is it subsumed into the
   shared environment component?

3. **Epigenetics** — some environmental effects on gene expression are heritable
   without being genetic. The child of a famine survivor has a measurably different
   metabolic profile. Should we model a thin epigenetic layer that carries
   one-generation environmental echoes beyond what the shared environment component
   already captures?

4. **Adoption and migration** — an agent raised by parents with very different
   trait profiles from their genetic parents, or who migrates during Development
   stage, will show trait profiles that partially diverge from their heritable
   baseline. This is the "environment dominates in extreme cases" scenario.
   How is it handled?

5. **Accelerated timescale** — the player will not want to wait 30 real minutes
   for a simulated generation to pass. Generational timescale events need a
   time-compression mechanism where the sim can fast-forward through demographic
   processes and then surface the results. How do we make generational change
   *visible and legible* to the player without requiring them to watch in real time?

---

*This document extends behavioral_model_design.md. Implement the Demographic
Module and Heritability Engine after the base personality layer is stable.*
