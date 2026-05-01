# Species Substrate, Standard Human & Designer Architecture
## Summary Document

> *Extends: lifecycle_heritability_design.md*
> *Covers: biological substrate layer, Standard Human parameter set, second-order*
> *propensities, race/class design philosophy, dashboard & designer UI sketch*

---

## The Key Distinction This Document Establishes

The previous documents defined OCEAN as the personality layer — individual
variation *within* a species. This document defines the layer beneath that:
the **biological substrate**, which is the species-level hardware that OCEAN
runs on.

The substrate doesn't vary between individuals of the same species. It *does*
vary between races. This distinction is the architectural foundation of the
entire race design system:

- **Substrate parameters** → what kind of creature this is
- **OCEAN distributions** → what kind of *people* this population contains
- **Second-order propensities** → what the above predicts about civilizational behavior

"Standard Human" is a named preset in substrate space. Alien races are other
points in that same space. Class differences are OCEAN distribution differences
sitting on top of a fixed substrate.

---

## Layer 0: The Biological Substrate

These parameters are species-level constants. Every individual of a given
species shares them. They are the knobs exposed in Designer Mode.

---

### 1. Cognitive Architecture Constants

**Temporal Discounting Rate**
How steeply future rewards are devalued relative to present ones. Humans
discount hyperbolically and steeply — a reward now is worth dramatically more
than the same reward next year, and the curve is non-linear. Even high-C
individuals discount the future; Conscientiousness only modulates *how steeply*
relative to this baseline. Produces characteristic civilizational short-termism.

*Standard Human: High steep hyperbolic discounting*
*Designer range: Linear (patient) → Extreme hyperbolic (impulsive)*

---

**Cognitive Load Ceiling / Heuristic Threshold**
How much simultaneous complexity an agent can hold in deliberate reasoning
before defaulting to intuitive heuristics. Humans hit this ceiling quickly —
we operate on heuristics most of the time. The ceiling is a species constant;
the tendency to push against it varies by Conscientiousness and Openness.
Determines how rational market behavior is at the individual level under load.

*Standard Human: Low ceiling, heavy heuristic reliance*
*Designer range: Very low (pure intuition) → Very high (near-rational)*

---

**Apophenia Coefficient / Pattern Recognition Bias**
The degree to which the mind detects patterns that aren't there. Humans are
extreme false-positive machines — evolutionarily, missing a real pattern cost
more than hallucinating a false one. Drives superstition, agency detection
(seeing intentionality in random events), and conspiracy formation. Modulated
by Openness and Neuroticism but the baseline is universal.

*Standard Human: Very high*
*Designer range: Low (literal, pattern-skeptical) → Extreme (sees meaning everywhere)*

---

**Loss Aversion Coefficient**
From prospect theory: the asymmetry between how much losses hurt versus how
much equivalent gains feel good. Standard Human value is ~2.2–2.5x — losses
hurt more than twice as much as equivalent gains feel good. Species-universal
in humans. Drives insurance markets, status quo bias, holding losing positions,
and the outsized political salience of loss over gain.

*Standard Human: ~2.3*
*Designer range: 1.0 (symmetric, rational) → 4.0+ (extreme loss aversion)*

---

**Dunbar Number / Social Tracking Limit**
The cognitive limit on meaningful tracked relationships, with nested tiers.
For humans: ~5 intimate, ~15 close, ~50 meaningful, ~150 known. Beyond ~150,
social cognition degrades and tribal heuristics take over. Not a preference —
a processing constraint. Determines the maximum radius of natural (non-
institutional) trust and the point at which formal hierarchy becomes necessary.

*Standard Human: ~150 (with nested tiers at 5 / 15 / 50)*
*Designer range: ~20 (near-solitary) → 500+ (highly social, large natural groups)*

---

### 2. Social Instinct Parameters

**In-Group / Out-Group Detection Sensitivity**
How readily the mind classifies others as "us" vs "them," and how sharply
behavior differs across that boundary. Humans are moderately-high — triggered
by surprisingly superficial signals (color, accent, arbitrary assignment).
Separate from Agreeableness, which modulates how *hostile* you are to the
out-group once detected. Low sensitivity = no natural tribalism; very high
sensitivity = kin-only trust radius.

*Standard Human: Moderately high, triggered by weak signals*
*Designer range: Minimal (cosmopolitan by default) → Extreme (hair-trigger tribalism)*

---

**Reciprocal Altruism Radius**
The effective range of "I'll help you now because you might help me later"
reasoning, and its decay rate with social distance. The biological substrate
of trade networks, legal systems, and reputation markets. Humans extend this
to non-kin across a moderate radius; it decays with distance. Conscientiousness
and Agreeableness modulate how far institutional trust can extend the radius
beyond its biological floor.

*Standard Human: Moderate radius, moderate decay*
*Designer range: Kin-only → Diffuse (altruistic toward strangers by default)*

---

**Dominance Hierarchy Sensitivity**
How attuned the mind is to status differentials, and how automatically behavior
adjusts to perceived rank. Humans are quite high — we detect status differences
rapidly and involuntarily. Generates natural stratification even in flat
organizations. Extraversion modulates how much you *compete* for rank; this
parameter controls how much rank shapes behavior at all.

*Standard Human: High automatic sensitivity*
*Designer range: Flat (rank-blind) → Extreme (every interaction rank-calibrated)*

---

**Coalition Formation Instinct**
The drive to form alliances, track who is allied with whom, and invest
cognitive resources in alliance maintenance. Humans are obsessively political
— we compute alliance structures even in contexts where it doesn't matter.
The substrate of all faction behavior. Extraversion amplifies it; Agreeableness
shapes its character; but the instinct itself is universal in humans.

*Standard Human: High — persistent background political computation*
*Designer range: Low (purely transactional, no faction loyalty) → Extreme (identity-fused with faction)*

---

### 3. Stress Response Profile

**Threat Response Distribution (Fight / Flight / Freeze)**
The default weighting across the three acute threat responses. Species-level
baseline; modulated by Neuroticism and life history at the individual level.
Some species might lack one response entirely. Humans are roughly balanced
with cultural variation.

*Standard Human: Roughly balanced, culturally modulated*
*Designer range: Per-response sliders summing to 1.0*

---

**Stress Response Duration / Recovery Rate**
How long the physiological stress response persists after threat resolution.
Humans have a slow decay relative to most animals — this is what makes
sustained anxiety possible and what makes populations vulnerable to chronic
civilizational stress. An alien with fast decay has intense acute responses
that resolve cleanly, producing very different behavior under prolonged threat.

*Standard Human: Slow — chronic stress is possible and common*
*Designer range: Very fast (acute only, no chronic) → Very slow (stress accumulates freely)*

---

**Trauma Consolidation Threshold**
Event intensity above which experiences are permanently consolidated into
behavioral modification rather than processed and resolved. Below this: bad
experiences fade. Above it: they reshape the trait baseline. Species-level;
Neuroticism modulates how close an agent operates to the threshold at baseline.

*Standard Human: Moderate threshold — significant events leave marks*
*Designer range: High threshold (resilient, trauma-resistant) → Low threshold (easily marked)*

---

### 4. Developmental Parameters

**Lifespan**
Total lifespan and stage proportion distribution. Standard Human: ~80 years,
with stages at approximately 15% Development / 15% Youth / 40% Adult / 20%
Elder plus rising mortality through Elder stage.

*Standard Human: ~80 years*
*Designer range: 20 years (fast-cycling, rapid generational turnover) → 500+ years*

---

**Critical Period Sensitivity**
How much early developmental windows outweigh later ones in trait-shaping.
Humans have pronounced critical periods — early conditions leave deep marks.
High sensitivity means the shared environment component during Development
stage dominates lifetime trait formation. Low sensitivity means environment
matters more evenly across all stages.

*Standard Human: High — early conditions disproportionately formative*
*Designer range: Low (even plasticity across lifespan) → Extreme (first years are destiny)*

---

**Intergenerational Trauma Transmission Coefficient**
The epigenetic and behavioral channel by which parental trauma reaches
offspring beyond what standard heritability and shared environment already
capture. In humans: real and measurable (children of famine/war survivors
show trait differences not fully explained by other channels). A thin but
nonzero channel.

*Standard Human: Low-to-moderate (~0.1–0.2 of parental trauma signal)*
*Designer range: 0.0 (no transmission) → 0.5 (strong intergenerational echo)*

---

### 5. Heritability Matrix

The species-level heritability coefficients for each OCEAN dimension and the
genetic covariance matrix (trait correlations). This defines the *rules of
the game* that trait distributions play by. Changing this is what makes a
race "more cooperative by nature" or "constitutionally more anxious."

**Standard Human heritability vector:**
```
O: 0.57    C: 0.49    E: 0.54    A: 0.42    N: 0.48
```

**Standard Human genetic covariance matrix:**
```
        O      C      E      A      N
O  [ 1.00, -0.10,  0.05,  0.10, -0.05]
C  [-0.10,  1.00,  0.05,  0.10, -0.15]
E  [ 0.05,  0.05,  1.00,  0.20, -0.10]
A  [ 0.10,  0.10,  0.20,  1.00, -0.30]
N  [-0.05, -0.15, -0.10, -0.30,  1.00]
```

The most important structural feature of this matrix: the strong N-A
inverse correlation (-0.30). High Neuroticism genetically co-varies with
lower Agreeableness. This means anxious populations tend toward hostility —
not as a cultural choice but as a biological tendency. Alien races might
have a very different (or absent) N-A relationship.

---

## Second-Order Propensities

Propensities are **computed outputs, not inputs**. They are predictions that
fall out of the substrate parameters and are displayed to the player as
legible behavioral tendencies. The designer sets substrate; the UI computes
and displays propensities in real time as sliders move.

| Propensity | Primary Drivers | Civilizational Prediction |
|---|---|---|
| **Short-termism** | Temporal discounting rate | Infrastructure underinvestment; difficulty sustaining multi-decade projects |
| **Tribalism ceiling** | Dunbar number + in-group sensitivity | Maximum natural polity size; trade network radius before institutional trust required |
| **Volatility under stress** | Stress duration + N heritability | Market behavior degradation during crises; recovery timeline |
| **Stratification tendency** | Dominance hierarchy sensitivity | Inequality persistence; speed of informal hierarchy formation |
| **Ideological susceptibility** | Apophenia coefficient + pattern bias | Frequency of millenarian movements; coherent worldview adoption rate |
| **Cooperative radius** | Reciprocal altruism radius + A heritability | Effective trade network range; institutional trust requirements |
| **Generational memory depth** | Trauma transmission + stress decay | How many generations a civilizational trauma echoes |
| **Innovation rate baseline** | O heritability + critical period sensitivity | Background rate of novel behavior emergence and technology diffusion |
| **Political instability cycle** | Coalition instinct + dominance sensitivity | Natural frequency of faction formation and collapse |
| **Loss aversion premium** | Loss aversion coefficient | Size of insurance/security markets; status quo bias in political economy |

Propensities are displayed as a **radar/spider chart** — a visual fingerprint
of the species. The Standard Human radar is the reference shape shown faintly
behind any custom species' radar, so the player can always see deviation from
the human baseline at a glance.

---

## Race and Class: How They Relate

### Race = Substrate

A race is a named preset in substrate parameter space. Races differ from
each other in their cognitive architecture, social instincts, stress profiles,
developmental parameters, and heritability matrices. All of these are set in
Designer Mode.

"Standard Human" is one point in this space. An alien race is another point.
The Second-Order Propensities are the readable summary of what that point
*means* in civilizational terms.

### Class = OCEAN Distribution

A class is a characteristic OCEAN distribution profile (mean and variance
per trait) that exists *within* a given race's substrate constraints. A
"Merchant class" is a sub-population whose trait distribution has drifted —
through assortative mating, economic sorting, and cultural selection — toward
a specific region of trait space: high C, moderate E, low N.

Classes run on their race's substrate. The same Merchant class OCEAN profile
produces systematically different economic behavior in two different races
because:
- The loss aversion coefficient changes the risk calculus
- The temporal discounting rate changes the time horizon of deals
- The stress response duration changes behavior under supply shocks
- The heritability matrix determines how stable the class profile is across generations

**This is the emergent cross-race class playstyle differentiation** — it
doesn't need to be authored. It falls out of the math.

### Class Emergence and Mobility

Classes are not authored in the game — they emerge from the lifecycle model
as OCEAN distributions cluster over time through assortative mating and
economic sorting. The tightness of the heritability matrix determines how
fast and stable these clusters become.

Class mobility is a direct function of:
- How high the heritability coefficients are (higher = lower mobility)
- How strong the assortative mating pressure is (stronger = more self-reinforcing classes)
- How volatile the environment is (high volatility disrupts clustering)

A race with low heritability and high environmental volatility will have
fluid, poorly-defined classes. A race with high heritability and stable
environments will develop rigid, stable castes over generations — not because
the game was told to make castes, but because the math produced them.

---

## UI Architecture

### Two Modes

**Gameplay Dashboard** — live population readout during play
- Demographic pyramid (age structure at a glance)
- Five OCEAN distribution curves, current vs. historical baseline
- Need tier satiation bars (population average across all five tiers)
- Archetype breakdown (emergent clusters displayed as a donut chart)
- Second-order propensity radar chart (the most legible single population view)
- Stress level and aggregate emotional state
- Trend arrows on all readings — is this population drifting toward or away from each propensity

**Designer Mode** — substrate-up species creation and modding

*Implementation order: substrate-up, because the player is the designer.*

Layout:
- Full substrate parameter panel, organized into the five groups above
- Each parameter is a labeled slider with:
  - Hard bounds (biologically plausible range)
  - "Standard Human" marker as a visual reference point
  - Tooltip explaining what the parameter does and what extreme values predict
- Second-order propensity radar updates live as sliders move — the computed
  fingerprint of the species reacts in real time
- Heritability matrix displayed as a color-coded correlation grid
  (not raw numbers — warm/cool color mapping for positive/negative correlation,
  with value on hover)
- Named presets panel: "Standard Human" as default reference; player-saved
  custom species; future built-in alien race presets
- Simulation preview: run 50 simulated generations with current settings,
  display the resulting trait distribution and propensity radar — "what does
  this species look like after history has worked on them?"

### Substrate-Up vs. Propensity-Down

The initial implementation is **substrate-up** — the player sets raw
parameters and reads the computed propensities as feedback. This is the
right starting point because:

1. It gives full control with no information loss
2. The propensity display teaches the player what each parameter *means*
   over time, building intuition
3. It's architecturally simpler — propensities are one-way computed outputs

A **propensity-down** mode (set target propensities, solver finds substrate
parameters) is a valuable future addition but requires an inverse solver and
introduces degeneracy (many substrate combinations produce similar propensities).
Flag for Phase 2 of Designer Mode.

---

## Open Questions

1. **Substrate mutability** — can a species' substrate parameters change over
   very long timescales through civilizational selective pressure? A species
   that has been spacefaring for ten thousand years might have a genuinely
   different Dunbar number than its planetary ancestors. Is this in scope,
   and if so, at what timescale does substrate drift happen versus trait
   distribution drift?

2. **Multi-species populations** — when two races co-inhabit a station or
   planet, how do their substrate differences interact? A mixed-race market
   where one species has 2.3x loss aversion and another has 1.1x will produce
   systematic arbitrage opportunities. Is this modeled, and how is the UI
   legible when reading a mixed population?

3. **Substrate discovery** — does the player know the substrate parameters of
   alien races they encounter, or is it a thing to be discovered through
   observation and interaction? This is a significant game design question —
   full transparency makes the game a spreadsheet; full opacity makes the
   behavioral model invisible. A middle path: propensities are observable
   through interaction; substrate parameters require research or espionage
   to fully unlock.

4. **Minimum viable substrate** — for the first playable build, which substrate
   parameters are load-bearing enough to implement first, and which can be
   held at Standard Human defaults while other systems are built? Candidates
   for early implementation: loss aversion coefficient, Dunbar number, stress
   recovery rate. Candidates to stub out initially: apophenia, critical period
   sensitivity, intergenerational trauma transmission.

---

*This document captures design decisions from the post-lifecycle conversation.*
*Implementation begins with the Designer Mode UI scaffolding and the Standard*
*Human parameter preset, then extends to full OCEAN distribution tooling.*
