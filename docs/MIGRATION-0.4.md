# Migrating 0.3.0 to 0.4.0

The request format, endpoint and environment variables are unchanged. Rebuild the image after
applying the update. This version changes the response schema and the model-facing protocol.

## Client changes

| Field | 0.4 behavior |
| --- | --- |
| `schema_version` | `0.4.0` |
| `meta.profile` | `workflow-premise-map-v0.4` |
| `meta.stages_completed` | New array: `[]`, `["extraction"]`, or `["extraction", "mapping"]` |
| `view.unresolved` | New array of `{statement, scope, evidence, question}`; scope is `alignment` or `execution` |
| `view.unknowns` | Derived statements from alignment-scope unresolved items only |
| `view.questions` | Derived alignment questions only; at most one distinct question |
| `care[].execution_effect` | Still null, supplied by the server |
| Public evidence | Still `{source, quote}`; exact source text, including original language |

Clients that validate schemas strictly must adopt the bundled `docs/openapi.json`. Existing fields
remain, but `mapped` does not assert that every later execution input is available. Inspect
`view.unresolved` for those details. Known conflicts retain `revision_required` even when a separate
alignment unknown remains. `meta.execution_authorized` is still always false.

## Model and error behavior

The first call extracts explicit source clauses. The second classifies/computes the premise map,
using the original request as well as those clauses. The mapping call selects evidence IDs; the
server resolves them to the existing public quotation format. No client sends these internal IDs.
Pure deterministic greetings still need no model. Other short routes can finish after extraction.

An extraction hint cannot discard a supplied AI interpretation, context, or extracted statement.
Missing document contents do not by themselves prevent comparing an explicit transfer boundary
with an upload proposal. They can remain execution-scope unknowns without a question.

New provider errors:

- `provider_invalid_evidence_reference`: mapping returned an unknown ID or malformed reference.
- `provider_execution_question`: an execution-only unresolved item contained a question.

Existing schema, attribution and exact quotation errors remain. The extraction stage can still
return `provider_ungrounded_evidence`. No invalid provider response is rewritten into a successful
map or semantic unknown; no automatic retry is added. Schema descriptions guide the model but
do not enforce semantic correctness or constrained decoding.

## Retest

Run `examples/transfer.en.json` first, then the English and Japanese demo cases, one at a time.
For transfer, expect the explicit boundary in Care and a known conflict, without requesting the
missing document or an alternative service. Execution-only unknowns may be recorded with a null
question. Inspect all fields for invented permissions or reasons.

Continue with `docs/ACCEPTANCE.md` after those regressions pass. Automated controlled-provider
tests cover protocol behavior; this version still needs live evaluation on the operator's model.
