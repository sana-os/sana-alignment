# Frameworks — Reference Guide

This directory contains the analytical frameworks of SANA OS.

Frameworks are **optional analytical lenses** — they are not continuously active. Each is invoked when the relevant structural pattern is detected in the conversation.

Load only the frameworks required for your persona. See `/personas/README.md` for the recommended loading order per persona.

---

## Framework index

| File | Full name | Primary use |
|---|---|---|
| `GMM.md` | Governance Maturity Model | Structural state diagnosis across layers A/B/C |
| `RBM.md` | Resource Balance Model | Demand/supply overload detection |
| `CPM.md` | Cognitive Processing Model | Cognitive compression and narrative formation |
| `RSM.md` | Role System Model | Role failure within organisations and states |
| `Legitimacy_Layer.md` | Legitimacy Layer | Narrative Core vs. Institution Core alignment |
| `History_Analysis.md` | History Analysis Framework | Source Trifurcation, non-competitive framing |
| `Value_Formation.md` | Personal Value Formation | Proximity Rule, priority filtering |

---

## Framework descriptions

### GMM — Governance Maturity Model
Diagnoses structural stability across Layers A (survival), B (narrative), and C (institution). Evaluates layer gaps, structural stress, and absorption capacity. The stability condition `V ≤ k × A_eff` governs whether a system can absorb change without collapse.

**Used by:** Persona_History

---

### RBM — Resource Balance Model
Identifies where demand exceeds supply for critical functions. `Gap_j = Demand_j − Supply_j`. Does not assign blame — detects structural overload. Produces bottleneck identification for any system.

**Used by:** Persona_Coaching, Persona_History, Persona_Reasoning

---

### CPM — Cognitive Processing Model
Describes how humans handle unknown variables (X) under pressure. Three processing modes: survival compression, narrative stabilisation, exploratory simulation. Includes architect state tracking (dormant / active / camouflaged / collapsed). Integrates CPM Metadata Spec.

**Used by:** Persona_Coaching, Persona_History

---

### RSM — Role System Model
Analyses collective systems as networks of functional roles (Decider, Architect, Integrator, Executor, Observer, Auditor). Identifies role capture, architect isolation, and succession deficit as failure modes.

**Used by:** Persona_History, Persona_Reasoning

---

### Legitimacy_Layer — Legitimacy Layer
Analyses civilisational cohesion through the alignment of Narrative Core (who we are) and Institution Core (what structure is valid). Legitimacy gap = distance between these two cores. Tightly coupled with Time Layer dynamics.

**Used by:** Persona_History

---

### History_Analysis — History Analysis Framework
Defines the Source Trifurcation (Fact / Perception / Record), non-competitive framing, and the Thought Experiment Sandbox. Provides the expression policy for historical dialogue.

**Used by:** Persona_History

---

### Value_Formation — Personal Value Formation
Models how individual value hierarchies form through reward/punishment systems. Defines the Proximity Rule (`Priority = Impact / Distance`), trust dynamics, and priority filtering protocol. Foundation for coaching-level analysis.

**Used by:** Persona_Coaching

---

## Integration map

```
CPM ──→ GMM   (cognitive pressure → layer instability)
CPM ──→ RBM   (perceived shortage → survival anxiety)
CPM ──→ RSM   (architect state → role dynamics)
CPM ──→ History_Analysis  (narrative formation → historical record)
GMM ──→ Legitimacy_Layer  (layer gaps → cohesion diagnosis)
RBM ──→ RSM   (resource stress → role capacity)
Legitimacy_Layer ──→ History_Analysis  (institutional legitimacy → historical dynamics)
Value_Formation ──→ RBM   (personal survival pressure → resource demand)
```
