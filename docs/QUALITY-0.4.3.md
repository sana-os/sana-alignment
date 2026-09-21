# Quality update 0.4.3

Response schema remains 0.4.0. No networking, retry policy, planning prompt or greeting routing
changes are included. Application and image version become 0.4.3.

## Evidence and observed failures

Operator response `55204382-1814-4eec-91ce-4d78e53da747` is preserved in
`tests/fixtures/observed-plan-divergence.json` as an observed failure, not a gold answer.
It placed directives in Fact, expanded no internet into no network connectivity, attributed
a derived operating requirement as explicit Care, and described AI choices without AI quotations.
The original input begins with `HelloThe`; that prefix is deliberately preserved.

## Changes and limits

The mapping instructions now audit clause roles regardless of the AI plan's headings,
preserve modality and network scope across all generated fields, distinguish implied Care
from explicit Care, and distinguish execution unknowns from material unconfirmed choices.
Gap descriptions require a real supplied position, not a claim about missing information.
Model-visible schema reinforces Care attribution and comparison evidence.

The server rejects each supplied-AI gap that lacks either human-source evidence or evidence
from `ai_interpretation`, with `provider_incomplete_comparison_evidence` (HTTP 502).
Human context is accepted; assistant context cannot stand in for the human. One-sided gaps
remain valid: quote both submitted scopes and leave the missing position null.
No quotes are silently inserted, no map is silently corrected, and no automatic retries are added.

This structural guard proves source coverage, not semantic entailment. Both quotes could still
be irrelevant or misinterpreted. Classification and meaning preservation remain model-dependent;
prompt improvements require live evaluation. Local stub tests must not be presented as proof
of improved LLM accuracy. A provider validation error is not `unknown` or an aligned result.

## Live regression review

Use the comparison workflow to hold the proposal fixed. Do not regenerate a different plan
between baseline and candidate runs. Keep the same model and parameters and record request IDs.
`examples/quality/observed-plan.en.json` reconstructs the request from the operator's submitted
original input and full displayed plan; it retains the HelloThe prefix. It is not a captured
HTTP payload, and display-time formatting may differ from the original transmitted text.
Use `examples/quality/offline.en.json` and `offline.ja.json`, then `network-scope.en.json`.

For each response inspect:

1. Fact contains the reported connection state, not display requests or prohibitions.
2. Care preserves the fictional-display goal and real-data boundary. Derived goals are not explicit.
3. No internet does not become a ban on LAN or every network, in any generated field.
4. Material AI-only choices are attributed to the AI, with relevant AI quotations in gaps.
5. Mere missing implementation details do not force divergence, a question or blocked alignment.
6. No new plan, motives or execution authority are invented.

There is no fixed expected status for every network-scope interpretation: inspect whether
broader isolation is identified as an AI proposal rather than a user requirement. For the
fully matching local-fictional-data examples, expect mapped without artificial differences.
Repeat in both languages and preserve failures. This release's live model evaluation is pending.
