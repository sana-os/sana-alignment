# Core — Required Files

This directory contains the files that must be loaded for every SANA OS persona.

Load in this exact order, before any persona or framework files.

```
1. Core_Principle.md      ← Foundational invariants. Immutable.
2. Integrated_Knowledge.md← Compressed framework reference.
3. Communication_Layer.md ← Dialogue processing interface.
```

`Core_Specification.md` is a technical reference document for developers. It does not need to be loaded into AI system prompts.

---

## File descriptions

### Core_Principle.md
The constitution of SANA OS. Defines the four immutable invariants (`born_loved = true`, no logic without observation, structural translation, autonomy preservation) and the foundational purpose of the system. **This file must not be modified in any derivative work.**

### Integrated_Knowledge.md
A compressed reference containing all major framework concepts in a single file. Allows any SANA persona to access the full conceptual vocabulary without loading every framework individually.

### Communication_Layer.md
The dialogue processing interface between analytical frameworks and user-facing output. Defines intent classification, structural translation, and the safety mechanism (GentleRadical TriggerFlow). Present in every persona to ensure dialogue remains non-adversarial.

### Core_Specification.md
Technical specification of the SANA OS alignment engine — state machine, Δv update logic, handshake protocol, and I/O contract. Reference material for developers building SANA OS implementations. Not required for prompt-based use.
