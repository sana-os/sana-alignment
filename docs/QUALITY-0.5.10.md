# 0.5.10: modality and support-state guidance

## Observed baseline

The 0.5.9 operator report cfb62ce9-3971-4fbe-b9dd-ea85d60958e0 completed
Extraction and Draft and returned mapped. The three implementation unknowns
remained execution-scoped. No spurious referent gap was emitted. The scripting OR
manual-editing assumption remained in View, but execution_assumption was not used;
that new category was therefore not demonstrated by the live run.

The whole offline/local-generation sentence and its obligation child were labelled
state. They did not enter Fact in this run. All ten View premises were labelled
unsupported, including attributed reports with exact quotes. Uniformity alone does
not prove error, but the output did not distinguish reporting a source premise
from assessing whether that premise is true. The complete report is retained in
tests/fixtures/observed-0.5.9-stage04-diagnostic.json.

## Changes

This update improves instructions and diagnostic visibility. It does not introduce
a semantic classifier, an extra inference, a retry, or a new rejection rule.

- Extraction instructions contrast reported state, obligation, and epistemic
  inference in English and Japanese. A mixed parent remains mixed even if its
  children are separately selected. A source heading is not an authoritative label.
  The word must by itself does not establish an obligation.
- Fact/View support_state now has schema documentation and explicit generation
  guidance. provided refers to a basis for the statement at its stated scope in
  submitted material; unsupported indicates an assertion beyond that basis;
  disputed requires a submitted contest; unknown leaves support undetermined;
  not_applicable is for a goal/value/requirement represented as such.
- A faithful report that a plan assumes a capability can be provided without
  establishing the capability. AI origin and externally_verified=false do not
  themselves imply unsupported. The statement must make its assessed scope clear.
  Care retains its existing mandatory not_applicable rule.
- Diagnostic provider-output-8 for app 0.5.10 adds support_review: Fact/View
  statements, source/status/support labels, original evidence and matching
  extraction functions. This is an inspection record, not a semantic verdict.

## Validation and limits

307 controlled tests passed. Added tests preserve the observed regression,
exercise English/Japanese mixed-role output through the HTTP provider adapter,
and verify that diagnostics retain all support labels without silently coercing
them. These tests supply model responses; they are not live accuracy measurements.

Public schema_version remains 0.5.0. OpenAPI descriptions and application version
are updated. Quotes, source identity, Care rules and existing gap/dependency guards
remain in place. No external checking of the plan's technical claims is added.

The model may still confuse state and obligation or choose an inappropriate
support label. Exact quote matching cannot prove implication or truth. The server
does not require artificial diversity among support labels or force mapped status.
Windows, Docker, Dify and the operator's model were not executed locally.

Run the unchanged stage-4 request once with verify-stage4-0510.ps1, retaining model
settings. Inspect the parent and child modality labels, human Care, Fact exclusion,
execution unknowns, alternative-preserving assumptions and support_review before
stage 5. Do not consider mapped alone a pass.
