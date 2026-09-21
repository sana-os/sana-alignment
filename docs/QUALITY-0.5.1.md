# 0.5.1: preserve the state / concern boundary

Application and local image: **0.5.1**. Public response schema: **0.5.0**.
Request fields, statuses, profile, two model stages and Dify parser are unchanged.
No third inference, retry or model replacement is added.

## Observed failure

Operator response `9f793a32-7e57-4187-bd9c-9334cdc05c38` reported this state in Fact:
"The demo PC is not connected to the internet."
It also invented this explicit Care requirement:
"The demo PC must operate without internet access."
The evidence quote existed, but it did not make that normative reformulation explicit.
The selected exact response excerpts are retained in `tests/fixtures/observed-0.5.0-care.json`;
the internal extraction output was not supplied and is not claimed to have been observed.

## Implementation

1. Extraction attaches a provisional `function` to each verbatim clause: `state`, `concern`,
   `proposal`, `other`, or `unclear`. Concern means an explicitly expressed goal, preference,
   priority, requirement or prohibition. Clauses retain their negation, conditions and scope.
2. The server constructs `_care_evidence_refs` from exact source/quote pairs labelled concern.
   Missing labels default to unclear. Conflicting labels for the same pair also become unclear.
   Whole-source entries remain available for comparison but are not automatically Care anchors.
3. The mapping model selects one permitted reference for each Care statement and cites that
   same reference in its evidence. The provider adapter resolves its original quote.
4. The engine independently requires the resulting statement to equal a cited concern clause.
   A state, a proposal, free-form obligation or an unrelated concern reference cannot pass that
   check. Changing the attribution to inferred does not bypass it.

Care statements now retain **source language**, including cross-language requests. They are
not translated or paraphrased. Explanations in View continue to use the requested language.
This intentionally narrows Care: a practical implication of a reported state is not rendered
as a new Care requirement. If relevant, View may expose it as a tentative implication.
The original clause and its source remain available in evidence and observations.

Reading a clause's function is still a model judgment, not a keyword rule. For example,
"The printer cannot connect" can report a capability, while "Real customer data cannot be
used in the demo" can express an exclusion. The words cannot, not, and must are not globally
banned. "I prefer offline operation" remains a concern without any prohibition keyword.

## Guarantees and limits

The bounded guarantee is that Care's wording must come from an eligible cited clause. A
mapping-stage paraphrase cannot add "must" to a source that only says "is not connected".
It does **not** guarantee that the extraction model classifies every clause correctly, chooses
complete clauses, recalls all concerns or understands every language. If it mislabels a state
as concern, that state can still appear verbatim in Care. If it misses a real concern, Care can
omit it. Original material remains available to comparison, but that does not guarantee recall.
Fact/View prose, comparison conclusions and source attribution still need semantic review.

Malformed or disallowed Care references fail with HTTP 502 and a machine-readable issue:
`provider_invalid_care_reference`, `provider_uncited_care_statement`, or
`provider_unanchored_care_statement`. Invalid output is not silently dropped or relabelled
mapped/unknown, and it does not grant execution authority. These errors indicate a provider
contract violation; genuinely ambiguous material can still be mapped to unresolved/clarification.

## Local validation

`python -m pytest tests -q`: **169 passed**, with two existing dependency deprecation warnings.
This includes seven optional diagnostic tests in the author workspace; without those tests,
the same distributed application suite contains 162 tests.

The 29 new cases cover observed failure replay, state copying, inferred-label bypass, explicit
prohibitions/preferences/permissions in multiple languages, context and AI attribution, mixed
extraction labels, missing labels, same text in different sources, incorrect references, the
mocked HTTP provider path, and preservation of unresolved classification uncertainty.
Expected extraction labels are controlled test fixtures, **not measured live classifier output**.
These tests demonstrate the protocol boundary; they do not establish a live accuracy rate.

Docker and the operator's llama.cpp/Dify environment were not available for local execution.
At package creation, 0.5.1 model evaluation was pending; operator results are recorded below.
No new dependency or Dify reimport is required.

## Operator contrast cases

| Request file | Expected distinction |
| --- | --- |
| `examples/quality/offline.en.json` | Reported connection state in Fact; display goal and real-data exclusion in Care; no newly invented offline obligation |
| `examples/quality/offline.ja.json` | Corresponding Japanese state/goal distinction |
| `examples/quality/no-internet.en.json` | Explicit no-internet instruction remains in Care, along with the other two concerns |
| `examples/quality/no-internet.ja.json` | Corresponding Japanese explicit prohibition remains in Care |

For these compatible proposals, `mapped` is the expected status; execution details alone should
not create a difference. Inspect content, not only status. All executions remain unauthorized.
Start with the English state case and the English prohibition case, retaining their full responses.

## Operator-reported follow-up: four runs

| Request ID | Case | Observed result |
| --- | --- | --- |
| `e4e838ee-87aa-4457-b0f9-8befa9c344be` | English reported state | mapped; one Fact state, two Care concerns; no invented offline obligation |
| `bfdf2fd5-e580-4411-a823-c829948bcf96` | English explicit prohibition | mapped; Fact empty, all three stated concerns in Care |
| `e7374678-5335-4858-bbe8-553ab4e09369` | Japanese reported state | mapped; state retained in Fact but the explicit display goal omitted from Care; only real-data exclusion retained |
| `f634a32e-53c2-4052-816e-4c192eb30ea4` | Japanese explicit prohibition | mapped; Fact empty, all three stated concerns in Care |

These are individual operator runs, not a measured reliability rate. The Japanese state case
does **not** satisfy the Care coverage criterion despite its mapped status. Its missing goal
is present in observations, but that is not a substitute for retaining the human concern in Care.
The final output does not expose the extraction function labels or the candidate list. It cannot
establish whether the goal was mislabelled during extraction or dropped during mapping.

`scripts/diagnose_care.py` runs one fresh inference without modifying the installed engine,
prompts, settings or results, and reports the actual function labels, eligibility and selected
Care references from that run. It cannot reconstruct the previously reported inference. If the
fresh run succeeds, that does not disprove the earlier omission or identify its cause.
Seven diagnostic tests distinguish controlled selection omissions, classification mismatches,
provider failure and a non-reproducing successful run; they do not simulate live model accuracy.
Selected response excerpts are retained in `tests/fixtures/observed-0.5.1-ja-care.json`.
