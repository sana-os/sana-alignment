# SANA OS – Core Specification v1.0

### Structural Alignment Engine

---

# 0. Introduction

## 0.1 Purpose

SANA Core is a structural alignment engine.

It ensures:

* Premise alignment precedes analysis
* Stability precedes optimization
* Exposure is controlled
* Dialogue remains non-adversarial

Core does not optimize persuasion.
Core does not enforce ideology.
Core does not act as analytical authority.

---

## 0.2 Non-Goals

Core does not:

* Diagnose personality
* Persist identity profiles
* Enforce value hierarchy
* Perform unsolicited structured analysis
* Replace user autonomy

---

## 0.3 Core Design Invariants

1. **Alignment First**
   Premise alignment precedes analysis.

2. **Stability Over Optimization**
   Lower Δv before increasing analytical depth.

3. **Invocation Is Allowed. Result-Dumping Is Not.**

4. **Exposure Is Gated.**

5. **Δv Is the Primary Engine Variable.**

---

# 1. Architecture Overview

## 1.1 Structural Separation

SANA OS is composed of:

* Core (Alignment Engine)
* Framework Layer (Optional structural lenses)
* Persona Layer (Expression modulation)
* LLM Provider (Language realization)

Core governs structure.
Frameworks provide models.
Persona shapes tone.
LLM generates language.

---

## 1.2 High-Level Flow

```text
Client Input
    ↓
Core Intake
    ↓
State Update
    ↓
Exposure Decision
    ↓
Prompt Construction
    ↓
LLM Provider
    ↓
Client Output
```

Core controls structure, not wording.

---

# 2. Core State Machine

## 2.1 State Definitions

```text
STATE_AUTHENTICATION
STATE_PREMISE_ALIGNMENT
STATE_ANALYSIS_GATE
STATE_RESPONSE_CONSTRUCTION
```

State progression is sequential but reversible.

---

## 2.2 State Diagram

```text
AUTH → PREMISE → ANALYSIS_GATE → RESPONSE
 ↑                                   ↓
 └──────────── Reversion ────────────┘
```

Stability overrides progression.

---

## 2.3 State Descriptions

### STATE_AUTHENTICATION

* Establish non-hostile baseline
* Initiate handshake
* Reduce Δv

Maximum Exposure: 0

---

### STATE_PREMISE_ALIGNMENT

* Clarify assumptions
* Map constraints
* Reduce structural ambiguity

Maximum Exposure: 1

---

### STATE_ANALYSIS_GATE

* Determine exposure eligibility
* Evaluate user intent
* Invoke frameworks internally (if needed)

Maximum Exposure: 2 (conditional)

---

### STATE_RESPONSE_CONSTRUCTION

* Enforce exposure format
* Apply persona modulation
* Deliver output

---

## 2.4 Transition Conditions

Authentication Trigger:

```
delta_v > 0.75 → STATE_AUTHENTICATION
```

Premise Progression:

```
baseline_stable == true
AND delta_v ≤ 0.65
```

Analysis Eligibility:

```
premises_confirmed == true
AND delta_v ≤ 0.55
```

Reversion:

```
Δv spike OR volatility == HIGH
```

---

# 3. Δv (Delta-v) Update Logic

## 3.1 Definition

```
delta_v ∈ [0.0, 1.0]
```

Δv represents structural misalignment.

It measures:

* Premise friction
* Escalation risk
* Handshake instability

Δv is the only scalar that gates exposure.

---

## 3.2 Initial Value

```
delta_v = 0.20
```

---

## 3.3 Update Formula

```
delta_v_new = clamp(
    delta_v_old * 0.85 + signal * 0.15
)
```

Signal represents structural friction estimation.

---

## 3.4 Threshold Behavior

```
delta_v > 0.75  → Stabilization Required
0.55–0.75       → Clarification Only
0.45–0.55       → Exposure Level 1
≤ 0.45          → Exposure Level 2 (intent-gated)
```

---

# 4. Handshake Protocol (SYN / ACK)

## 4.1 Purpose

Handshake establishes structural non-hostility.

It is authentication, not empathy simulation.

---

## 4.2 Model

```
SYN → ACK → STABLE
```

---

## 4.3 SYN Detection

Cooperative signals increase:

```
handshake += 0.3 (cap 1.0)
```

---

## 4.4 ACK Behavior (Δv Dependent)

| Δv Range  | ACK Behavior              |
| --------- | ------------------------- |
| ≤ 0.50    | Normal ACK                |
| 0.50–0.75 | Short ACK + Stabilization |
| > 0.75    | Stabilization before ACK  |

---

## 4.5 Baseline Stabilization

```
handshake ≥ 0.6
AND delta_v ≤ 0.65
```

→ baseline_stable = true

---

# 5. Layer A/B/C Supplementary Tags

## 5.1 Purpose

Layer tags are framing modifiers, not decision engines.

Primary engine: Δv
Supplementary tags: A/B/C

---

## 5.2 Definitions

Layer A – Survival / Stability
Layer B – Meaning / Narrative
Layer C – Institutional / Logical Structure

---

## 5.3 Representation

```
layer_estimate = { A: float, B: float, C: float }
bottleneck ∈ {A, B, C, UNKNOWN}
```

Layer tags influence framing only.

They do not override Δv.

---

# 6. Exposure Control & Timing Policy

## 6.1 Exposure Levels

```
exposure_level ∈ {0, 1, 2}
```

| Level | Visibility | Purpose           |
| ----- | ---------- | ----------------- |
| 0     | Hidden     | Stabilization     |
| 1     | Soft Hint  | Premise alignment |
| 2     | Explicit   | Structured output |

---

## 6.2 Exposure Level 1 Rule

Mandatory format:

```
[Hypothesis] + [Verification Question]
```

No verdicts.
No definitive labeling.
Must preserve autonomy.

---

## 6.3 Exposure Level 2 Eligibility

Allowed only when:

```
premises_confirmed == true
AND delta_v ≤ 0.45
AND intent == analysis_request (or consent)
```

---

## 6.4 Dialogue vs Workflow

Dialogue Mode:

* Exposure 1 dominant
* Persona modulation active

Workflow Mode:

* Exposure 2 default
* Minimal persona modulation

---

## 6.5 Prohibition Clause

Dialogue Mode must not:

* Dump structured diagnosis
* Lead with framework authority
* Deliver verdict-style declarations
* Attribute identity

---

# 7. Core State Management

## 7.1 Session Scope

All state is session-scoped.
No cross-session persistence.

---

## 7.2 State Variables

```
phase
delta_v
volatility
handshake
baseline_stable
premises_confirmed
intent
constraints
assumptions
open_questions
exposure_level
layer_estimate
bottleneck
```

---

## 7.3 Update Order (Invariant)

1. Estimate signal → update Δv
2. Update volatility
3. Detect SYN → update handshake
4. Update layer tags
5. Evaluate state transition
6. Determine exposure level
7. Construct response

---

# 8. Core I/O Contract

## 8.1 Input Schema

```json
{
  "input_message": "string",
  "conversation_context": [],
  "mode": "dialogue | workflow",
  "persona": "string | null",
  "session_id": "string"
}
```

---

## 8.2 Output Schema (Primary)

```json
{
  "llm_prompt": "string",
  "exposure_level": 0 | 1 | 2,
  "state": "STATE_*",
  "delta_v": 0.0,
  "volatility": "LOW | HIGH"
}
```

---

## 8.3 Responsibility Boundary

Core:

* Controls structure
* Controls exposure
* Controls Δv gating
* Controls handshake gating

Core does NOT:

* Determine ideological correctness
* Persist psychological profile
* Replace user autonomy
* Operate as analytical authority

---

# 9. Stability Principle

When uncertain:

> Reduce exposure.
> Lower Δv.
> Reconfirm premises.

Stability precedes optimization.
Premise alignment precedes analysis.

---
