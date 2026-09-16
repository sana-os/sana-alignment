# 📄 CPM 1.1 – SANA Edition

```markdown
---
title: "CPM 1.1 – SANA Edition"
framework: "Cognitive Processing Model"
version: "1.1"
status: "draft"
layer: "Framework Layer"
related_frameworks:
  - GMM
  - RBM
  - RSM
  - History Analysis
metadata_spec: "CPM Metadata Spec – SANA Edition"
---

# CPM 1.1 – SANA Edition

## 1. Overview

CPM (Cognitive Processing Model) describes how humans process uncertainty and how narratives emerge from cognitive pressure.

The model focuses on how humans handle **unknown variables (X)** and how cognition transitions between exploration and narrative substitution.

CPM functions as the **cognitive detection layer** within SANA OS.

```

unknown X
↓
trigger
↓
cognitive processing
↓
architect state
↓
decision / narrative / simulation

```

---

# 2. Core Principle

Human cognition cannot indefinitely tolerate unknown variables.

Therefore cognition tends to move toward:

1. **Narrative substitution**
2. **Exploratory simulation**

Architects are individuals capable of **preserving unknown variable X without immediate substitution.**

---

# 3. Unknown Variable

```

X = unknown / incomplete / ambiguous information

```

Examples:

- emerging technology
- unknown social groups
- geopolitical instability
- institutional contradiction
- future risk scenarios

---

# 4. Cognitive Triggers

CPM defines three primary triggers.

---

## 4.1 Curiosity Trigger

Occurs when survival pressure is low.

```

stable environment
↓
curiosity
↓
exploration

```

Characteristics:

- high uncertainty tolerance
- variable preservation
- exploratory cognition

---

## 4.2 Survival Anxiety Trigger

Occurs when perceived threat increases.

```

perceived threat
↓
survival anxiety
↓
cognitive compression

```

Characteristics:

- threat classification
- rapid narrative substitution
- group alignment

---

## 4.3 Success Trigger

Occurs when long-term success stabilizes the dominant narrative.

```

long-term success
↓
narrative validation
↓
question suppression

```

This produces the **Success Paradox**:

```

success
↓
narrative sanctification
↓
correction loop failure

```

Historically this pattern appears before major civilizational crises.

---

# 5. Cognitive Processing Modes

---

## 5.1 Survival Compression Mode

```

unknown X
↓
threat classification
↓
rapid narrative substitution

```

Goal:

```

reduce uncertainty quickly

```

Typical outcomes:

- labeling
- enemy construction
- identity reinforcement

---

## 5.2 Narrative Stabilization Mode

```

unknown X
↓
integration into existing narrative

```

Goal:

```

maintain social stability

```

Typical outcomes:

- ideological reinforcement
- institutional defense
- tradition preservation

---

## 5.3 Exploratory Simulation Mode

```

unknown X
↓
variable preservation
↓
future simulation

```

Goal:

```

structural understanding

```

Typical outcomes:

- scenario modeling
- systemic prediction
- structural analysis

---

# 6. Architect State

Architects are individuals capable of sustaining **Exploratory Simulation Mode** under uncertainty.

Architect is defined as a **cognitive state**, not a personality type.

---

## Architect States

```

dormant
active
camouflaged
fragmented
assimilating
collapsed

```

---

### Dormant

Architect capability exists but is inactive due to environmental stability.

---

### Active

Exploratory simulation is actively performed.

Conditions supporting this state include:

- psychological safety
- tolerance for uncertainty
- low punishment for dissent

---

### Camouflaged

Architect hides exploratory cognition within dominant narratives.

```

exploration
+
narrative camouflage

```

Purpose:

```

survival within narrative-dominant systems

```

---

### Fragmented

Multiple architects produce competing interpretations of X.

```

multiple models
↓
interpretation conflict

```

Fragmentation may lead to internal conflict among reformers.

---

### Assimilating

Architect gradually adopts the dominant narrative.

Triggers include:

- prolonged social pressure
- belonging pressure
- survival pressure

---

### Collapsed

Narrative substitution becomes locked.

```

temporary narrative
↓
identity fusion
↓
belief lock

```

Exploratory cognition stops.

---

# 7. Architect State Transitions

Architect states change due to **environmental pressure**.

```

environment pressure
↓
state transition

```

Key pressures include:

- survival pressure
- social conformity pressure
- belonging pressure
- institutional repression

Example transitions:

```

active
↓ (social pressure)
camouflaged

```
```

camouflaged
↓ (long-term narrative exposure)
assimilating

```
```

assimilating
↓ (belief lock)
collapsed

```
```

active
↓ (multiple competing models)
fragmented

```

---

# 8. Narrative Translation

Architect survival historically depends on **translation ability**.

```

structural discovery
↓
narrative translation
↓
social acceptance

```

Successful architects often convert structural insight into culturally acceptable narratives.

This mechanism allows structural change to be absorbed by society.

---

# 9. Cognitive Risks

---

## Narrative Lock

```

temporary narrative
↓
identity fusion
↓
irreversible belief

```

---

## Hostility Escalation

```

uncertainty
↓
threat perception
↓
enemy construction

```

---

# 10. Output

CPM produces cognitive state signals used by other frameworks.

Output categories include:

- trigger type
- processing mode
- architect state
- narrative attachment
- survival pressure
- simulation activation

Detailed fields are defined in:

```

CPM Metadata Spec – SANA Edition

```

---

# 11. Framework Integration

CPM provides cognitive signals to other frameworks.

```

CPM → GMM
cognitive pressure → layer instability

CPM → RBM
perceived shortage → survival anxiety

CPM → RSM
architect state → role dynamics

CPM → History Analysis
narrative formation → historical record

```

---

# 12. Role in SANA OS

Within SANA OS, CPM functions as the **cognitive detection layer**.

```

human cognition
↓
CPM detection
↓
framework integration
↓
SANA OS interpretation

```

CPM does not determine truth.

Its role is to identify **how cognition processes uncertainty**, allowing SANA OS to stabilize dialogue conditions.

---

# 13. Design Philosophy

CPM analyzes **how beliefs emerge**, not whether they are correct.

This enables SANA OS to maintain **psychological safety** while examining conflicting narratives.

---


---

# 📄 CPM Metadata Spec – SANA Edition.md

```markdown
---
title: "CPM Metadata Spec – SANA Edition"
framework: "Cognitive Processing Model"
version: "1.0"
status: "draft"
layer: "Metadata Layer"
related_frameworks:
  - CPM
  - GMM
  - RBM
  - RSM
  - History Analysis
purpose: "Define canonical metadata fields produced by CPM"
---

# CPM Metadata Spec – SANA Edition

## 1. Overview

This document defines the **canonical metadata schema produced by CPM (Cognitive Processing Model).**

The metadata enables interoperability between SANA OS frameworks.

```

human cognition
↓
CPM detection
↓
CPM metadata output
↓
framework integration

````

Frameworks consuming CPM metadata include:

- GMM (Civilizational structure analysis)
- RBM (Resource bottleneck model)
- RSM (Role system model)
- History Analysis (Narrative transmission)

CPM metadata acts as the **cognitive signal layer** within SANA OS.

---

# 2. Metadata Philosophy

CPM metadata describes **how cognition processes uncertainty**, not whether beliefs are correct.

The schema is designed to:

- detect cognitive pressure
- identify narrative formation
- detect architect activity
- allow cross-framework interpretation

This enables SANA OS to stabilize dialogue conditions while maintaining analytical neutrality.

---

# 3. Core Output Schema

CPM produces a structured output object.

Example structure:

```yaml
CPM_Output:

  trigger_type: survival_anxiety

  processing_mode: exploratory_simulation

  architect_state: camouflaged

  narrative_attachment: 0.5

  simulation_activation: true

  environment_pressure:
    survival_pressure: 0.8
    conformity_pressure: 0.7
    belonging_pressure: 0.6
````

---

# 4. Field Definitions

## 4.1 trigger_type

Defines what initiated cognitive processing.

```yaml
trigger_type:
  type: enum
  values:
    - curiosity
    - survival_anxiety
    - success
```

### Description

* **curiosity**
  Exploration triggered by stable conditions.

* **survival_anxiety**
  Cognitive compression triggered by perceived threat.

* **success**
  Stabilization triggered by prolonged success and narrative validation.

---

# 4.2 processing_mode

Defines how cognition currently processes unknown variable X.

```yaml
processing_mode:
  type: enum
  values:
    - survival_compression
    - narrative_stabilization
    - exploratory_simulation
```

### Description

**survival_compression**

```
unknown X
↓
threat classification
↓
rapid narrative substitution
```

**narrative_stabilization**

```
unknown X
↓
integration into dominant narrative
```

**exploratory_simulation**

```
unknown X
↓
variable preservation
↓
future modeling
```

---

# 4.3 architect_state

Represents the current cognitive state of an Architect.

```yaml
architect_state:
  type: enum
  values:
    - dormant
    - active
    - camouflaged
    - fragmented
    - assimilating
    - collapsed
```

### Description

**dormant**

Architect capability exists but is inactive.

**active**

Exploratory simulation is actively performed.

**camouflaged**

Architect hides exploratory cognition within dominant narrative structures.

**fragmented**

Multiple architects generate competing interpretations.

**assimilating**

Architect gradually adopts dominant narrative.

**collapsed**

Narrative substitution becomes locked and exploratory cognition stops.

---

# 4.4 narrative_attachment

Represents the strength of attachment to the dominant narrative.

```yaml
narrative_attachment:
  type: float
  range: 0.0 – 1.0
```

Meaning:

```
0.0 = no narrative attachment
1.0 = complete identity fusion with narrative
```

High values increase risk of **Narrative Lock**.

---

# 4.5 simulation_activation

Indicates whether exploratory simulation is currently active.

```yaml
simulation_activation:
  type: boolean
```

True indicates:

```
future modeling
scenario exploration
structural analysis
```

---

# 4.6 environment_pressure

Represents environmental pressures influencing cognitive state transitions.

```yaml
environment_pressure:

  survival_pressure:
    type: float
    range: 0.0 – 1.0

  conformity_pressure:
    type: float
    range: 0.0 – 1.0

  belonging_pressure:
    type: float
    range: 0.0 – 1.0
```

---

### survival_pressure

Represents perceived threat to survival.

Sources include:

* war
* economic collapse
* instability
* existential risk

---

### conformity_pressure

Represents pressure to conform to dominant narratives.

Sources include:

* ideological enforcement
* institutional control
* social punishment

---

### belonging_pressure

Represents psychological pressure to remain within the group.

Sources include:

* fear of exclusion
* identity dependency
* social attachment

---

# 5. Derived Indicators (Optional)

Frameworks may derive additional signals.

Examples:

```yaml
derived_signals:

  narrative_lock_risk
  architect_visibility
  correction_loop_status
```

---

# 6. Cross-Framework Integration

CPM metadata is used by other frameworks as follows.

---

## CPM → GMM

Maps cognitive pressure to civilizational layers.

```
survival_pressure → Layer A instability

narrative_attachment → Layer B rigidity

conformity_pressure → Layer C enforcement
```

---

## CPM → RBM

Maps cognitive signals to resource stress.

```
survival_anxiety trigger → resource scarcity

survival_pressure → RBM bottleneck detection
```

---

## CPM → RSM

Maps architect state to role dynamics.

```
architect_state → Architect role activity

fragmented → role conflict

collapsed → architect deficit
```

---

## CPM → History Analysis

Maps narrative formation to historical record.

```
narrative_stabilization → ideology formation

exploratory_simulation → reform narratives

success trigger → narrative sanctification
```

---

# 7. Design Constraints

CPM metadata must satisfy the following conditions:

1. **Framework neutrality**

The metadata must not encode ideological judgments.

2. **Cross-framework compatibility**

All fields must be interpretable by GMM, RBM, RSM, and History Analysis.

3. **Extensibility**

Future SANA OS layers (including Time Layer) may extend this schema.

---

# 8. Role in SANA OS

CPM Metadata forms the **cognitive signal interface** of SANA OS.

```
human cognition
↓
CPM detection
↓
metadata signals
↓
multi-framework analysis
↓
SANA OS interpretation
```

This allows SANA OS to maintain **psychological safety and structured dialogue** even under conflicting narratives.

---
