# Quality candidate 0.4.4

Based on operator response bcffd0b5-d09c-4dae-90c7-8283c051b7ca from 0.4.3.
Response schema stays 0.4.0. No networking, retries, greeting routing or Dify DSL changes.

Observed improvements: factual connection state separated from Care; both comparison sources
quoted; no universal-network prohibition in Fact. Remaining failures: the supplied display
proposal became a generation action, and a compatible local implementation became a divergence.

Mapping instructions and model-facing field descriptions now distinguish action from possible
implementation prerequisites, human requirements from AI choices, and consequential differences
from compatible detail. Genuine nonblocking differences must remain visible. These are generation
guidance changes, not a deterministic semantic detector. No output is silently removed or reworded.

## Fixed-input regression evaluation

Use the existing request files with the same model and parameters. Save complete responses and
request IDs. Do not regenerate the plan for each version. Review all fields, not only status.

| Request | Acceptance criteria |
| --- | --- |
| examples/quality/offline.en.json | mapped; connection state in Fact; display goal and no-real-data boundary in Care; local approach attributed to AI; no invented generation action; no gap merely for local resources |
| examples/quality/offline.ja.json | Same role/action/scope criteria in Japanese |
| examples/quality/network-scope.en.json | LAN disconnection and assumed file permission remain visible as AI choices; not silently mapped away or attributed to human; no invented explicit prohibition |
| examples/align.en.json | revision_required; production-data proposal conflicts with no-real-data boundary; preserve both quotes |
| examples/quality/observed-plan.en.json | Generation is explicitly in this longer plan: preserve it rather than globally banning the word; separate compatible detail from consequential unconfirmed assumptions |

The first case is the fixed input that produced the observed 0.4.3 failure. Test success in stub
unit tests does not establish these semantic criteria. Live 0.4.4 evaluation remains pending.
Use a few repeated fixed-input runs to assess variability after the first reviewed run passes.

## Dify greeting routing (design only)

A classifier before the planner can distinguish pure social greetings from task-bearing or
uncertain inputs. Pure greeting: omit ai_interpretation and submit the unchanged input to SANA.
Task-bearing, mixed greeting/task or uncertain: preserve the original input and use the planner.
Never strip a Hello prefix from the submitted text. Let SANA produce its own response; do not
forge a handshake JSON from a classifier label. SANA may still use its extraction stage for
greetings outside its exact local greeting list. Context-bearing conversations need contextual
classification; a simple greeting label must not discard a pending task. Classification itself
uses a model and can be wrong. This routing is not implemented by this backend patch.
