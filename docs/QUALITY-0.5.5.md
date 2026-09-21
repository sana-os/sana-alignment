# 0.5.5 verification update: open topics and source-preserving comparisons

## Observed baseline

The operator's stage-4 diagnostic used application 0.5.4, provider-output-2 and
the unchanged 4,250-character AI plan. Request ID:
`90a3af58-e76d-4b9e-9b4c-10c3a1792073`.
It returned `needs_clarification` successfully with zero evidence mismatches,
zero provider validation errors and zero questions counted by the engine.
It did not reproduce the preceding `provider_excessive_questions` error.

The response and diagnostic are preserved without correcting their contents in
`tests/fixtures/observed-0.5.4-stage04-diagnostic.json`. Its semantic defects are
review material, not desired test expectations:

- Three open topics (format, count and branding) appeared in Care and in
  alignment-scope unresolved items.
- The library assumption included **already installed or can be bundled**, but
  its generated difference described only libraries already being present.
- Two assumptions were marked as blocking missing premises. This successful
  response does not establish that those judgments are appropriate or stable.

## Changes

1. Extraction has an `unknown` function for an explicitly unspecified variable
   or open topic. This differs from `unclear` (uncertain communicative function).
   Unknown-labelled clauses cannot supply Care anchors. A separately stated
   request to investigate an unknown can still be Care. This is not a keyword
   rule, and unknowns about authority or constraint scope remain possible
   alignment issues.
2. Both stages receive literal Markdown heading paths alongside evidence IDs.
   Quotes are unchanged. Repeated identical text retains all matching heading
   contexts. Headings inside fenced code are ignored. These headings are source
   data, never trusted instructions or automatic semantic labels.
3. In the standard provider wire protocol, gap positions are nullable cited
   reference IDs with source-role checks. `difference` is no longer generated
   by the model. The server renders the relation kind and both exact selected
   positions. This extends the extractive approach already used for understanding
   and intended effects to comparisons, preserving original alternatives and
   qualifications. Unknown/uncited/wrong-source IDs and an unexpected generated
   difference are rejected; they are not silently repaired.
4. The 0.5.5 diagnostic (`provider-output-3`) captures extraction functions and
   reference eligibility/context in the same inference as the Draft review. It
   refuses inference on another application version. The distributed stage-4
   runner verifies app version and file hashes and saves the complete report.

## Consumer-visible behavior

Application/image version is 0.5.5. Response schema remains 0.5.0. Existing Dify
parsing of that version and status strings remains compatible; no DSL import is
required for this verification. No Dify/model/network setting is changed here.

`human_premise` and `ai_premise` now contain selected original excerpts or null.
`difference` remains a string, but contains an extractive comparison, for example:

```text
[missing_premise]

[human_premise]
null

[ai_premise: ai_interpretation]
Use installed or bundled libraries.
```

The null side means no position was selected from the submitted human material;
it does not prove that no position exists elsewhere. The comparison kind and
blocking flag remain model assessments, not verified conclusions.

This intentionally trades a fluent free-form difference explanation for exact
positions and a typed relation. Source excerpts retain their original language.
The difference length limit increases from 6,000 to 14,000 characters to hold two
maximum-length positions with labels; original evidence is never truncated.
Consumers with their own 6,000-character output cap should account for this.

## Verified locally and still unverified

243 local workspace tests passed with two existing dependency deprecation warnings.
The 26 new tests cover the observed report identity, heading context, English and
Japanese unknown/request contrasts, rejection of unknown Care under controlled
labels, retained alignment uncertainty, complete alternative/condition quotations,
wrong-source and uncited comparisons, HTTP conflict routing, long excerpts and
diagnostic version/error reporting. The model-facing JSON Schemas were separately
validated with accepted and rejected comparison examples.

These tests exercise controlled model replies, not a live classifier. In particular,
the original v2 report did not record extraction labels; regression labels are
independently supplied expectations, not reconstructed internal model output.

The model still selects functions, excerpts, gap kind, unresolved scope and blocking
flags. It can select the wrong excerpt, omit a premise, or misclassify an open topic.
No forced `mapped` result, keyword-based scope rewrite, question truncation or
blanket deletion of AI-origin Care is introduced. A supplied AI policy can remain
Care with `provided_source` attribution. The prompt schema is guidance in JSON
object mode, not guaranteed constrained decoding. Free prose in other statement
fields still requires semantic review. Previous intermittent provider errors are
not declared resolved by this patch.

## Next operator check

Run the bundled stage-4 verification once against 0.5.5, keeping the model and
settings unchanged. Inspect the original human goal/prohibition, unknown labels,
Care attribution, unresolved scopes, comparison positions and any blocking claims.
Do not require `mapped` as a blanket acceptance criterion. A 200/success result
alone is not a semantic pass, and one run does not establish stability.

Use the saved report before requesting another inference. Stage 5 and Dify remain
subsequent checks after review of this run. The diagnostic directly invokes the
engine/provider in the running container; it does not test Dify transport or HTTP
middleware. Release readiness has not been established.

The PowerShell wrapper was inspected here but cannot be run in this Linux
workspace (PowerShell and the operator's Docker installation are unavailable).
Its Python diagnostic path is covered by controlled tests. Windows execution and
the live local model response are the next operator checks.
