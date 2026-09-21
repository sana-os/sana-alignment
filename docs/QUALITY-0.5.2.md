# 0.5.2: explicit requests versus tentative proposals

Application/image: **0.5.2**. Public response schema and profile remain **0.5.0** and
`workflow-premise-map-v0.5`. Dify configuration, provider settings and the two-stage pipeline
remain unchanged. No inference, retry, permission step or silent response repair is added.

## Diagnostic evidence

The operator's fresh 0.5.1 diagnostic, request `3f8ae8e6-88e0-46ed-a7b5-6c8d54d51b1f`,
reproduced the missing Japanese display goal. Its extraction labelled
`完全に架空の顧客情報を表示してください。` as `proposal`. The corresponding `q3` reference
had `care_eligible=false` and `selected_as_care=false`. The prohibition was classified
`concern` and retained. `eligible_but_not_selected` was empty.

This identifies an extraction misclassification and consequent candidate exclusion **in that
diagnostic run**, not a mapping-stage selection omission. The earlier request
`e7374678-5335-4858-bbe8-553ab4e09369` had the same visible omission but no internal trace;
its internal cause cannot be independently reconstructed from this later inference.
Exact selected diagnostic excerpts are stored in `tests/fixtures/observed-0.5.1-ja-care-trace.json`.

## Change

Extraction now has an explicit `request` function for an instruction asking for an action or
outcome, including a method that the speaker has explicitly adopted. `proposal` is clarified
as a tentative option or supplied AI plan, not an adopted human instruction. Care anchors
accept `request` and `concern`; states, unadopted proposals and unclear clauses remain excluded.
The same quote labelled both request and concern remains eligible; either label combined with
state, proposal or unclear remains unclear. The source/quote identity is unchanged.

Prompt and schema descriptions give contrasts between Japanese and English imperatives,
polite requests, adopted methods, tentative options and supplied AI plans. Imperative wording
inside an AI proposal does not make it the human's instruction. Quoted, withdrawn or hypothetical
instructions are not automatically endorsed requests. The mapper is instructed to preserve
requested outcomes alongside prohibitions rather than retaining only the protective boundary.

This is a model-facing taxonomy and guidance change plus support for its new internal enum.
It is not a suffix/keyword detector. The server does **not** reclassify every proposal as a
request, automatically fill missing goals, or treat all candidate concerns as current agreement.
Care remains an exact cited source quote, with its original language and no execution authority.

## Validation and remaining limits

Author workspace: **194 tests passed**, with two existing dependency deprecation warnings.
180 are application/contract tests; 14 are optional diagnostic tests in the author workspace.
The patch adds 18 request-function cases and includes no new runtime dependency.
Tests preserve the observed misclassification as-is and separately exercise a controlled
expected request label, positive request examples, negative option/state examples, attribution,
compatible and conflicting duplicate labels, schema eligibility and exact quote preservation.

These tests establish protocol behavior conditional on model labels. They do not prove the
model will assign the corrected label in a live inference. If it still chooses proposal or
omits the clause, Care can still miss the goal; if it mislabels a state as request/concern,
the original state can still appear in Care. A mapping omission of an eligible candidate is
also still possible. No overall recall, precision or reliability rate is claimed.

Docker, Dify and the operator's local model are unavailable for author execution. The prior
0.5.1 live English and Japanese boundary results do not establish 0.5.2 accuracy.

## Targeted operator check

Re-run the existing Care diagnostic against `examples/quality/offline.ja.json` after rebuilding.
The existing standalone `diagnose_care.py` works unchanged; it reads the installed engine.
The target clause should have function request (or concern), care_eligible=true and
selected_as_care=true. Care should contain both the display goal and real-data prohibition;
the reported connection state belongs in Fact. `mapped` alone is not sufficient.
The response schema is still 0.5.0 and execution_authorized remains false.

If the PowerShell session was restarted, re-create the diagnostic payload/runner using the
previous diagnostic instructions, or run the fixed API request first. No Dify reimport is needed.
