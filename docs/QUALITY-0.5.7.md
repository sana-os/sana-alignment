# 0.5.7: role consistency and explicit unresolved dependencies

## Observed baseline

The 0.5.6 stage-4 run, request `72e313f7-b020-498b-94a0-961bf7733144`,
completed Extraction and Draft with 22 extracted items, no evidence mismatches,
and no structural validation errors. Its three open topics were labelled unknown
and no longer appeared in Care. They still appeared as alignment-scope unresolved
items. The mixed state/local-generation requirement and the supplied plan's
capability assumptions were copied into Fact and View.

The complete uploaded report is preserved in
`tests/fixtures/observed-0.5.6-stage04-diagnostic.json`. Success of that inference
was not a semantic acceptance, not a demonstration of extraction above 32 items,
and not an exercise of comparison rendering (no premise gaps were returned).

## Changes

- Extraction can label an excerpt `mixed` or `assumption` instead of squeezing
  these into `state`. An explicitly posited plan condition belongs in View as a
  supplied assumption; its presence in text does not establish actual capability.
- The candidate generator offers original semicolon-separated clauses as well as
  the entire original line, within its existing 256-reference budget. It does
  not split code/inline code or translate text. Literal enclosing-line context
  accompanies smaller excerpts, so qualifications are available. The unchanged
  stage-4 request now has 51 candidates: the original 47 plus four clause excerpts.
  This count is not a target number of model selections.
- Fact evidence cannot contain a clause declared request, concern, proposal,
  unknown, mixed, assumption or unclear by extraction. Candidate restrictions are
  provided in the model-facing schema, and engine validation rejects violations
  as `provider_non_factual_evidence`. Matching is source-specific. A separate state
  excerpt can still support a factual claim. This checks declared role consistency,
  not whether the extraction label is semantically correct.
- The model-facing unresolved item selects a `dependency` instead of a bare
  `scope`: execution_detail, goal_meaning, constraint_scope, authority, referent,
  or comparison_assumption. Execution details use a null target; the other cases
  must identify and cite an original premise reference whose interpretation or
  comparison is unresolved. The adapter derives the public execution/alignment
  scope from that selected category. Invalid, uncited or legacy bare-scope output
  is rejected, not silently recategorized.
- Diagnostic v5 targets 0.5.7 and additionally records the generated dependency
  selections and the references excluded from Fact. This makes one live run enough
  to distinguish an extraction-role error from a scope-selection error. Prior
  versioned diagnostics remain unchanged.

No input is classified by words such as format/branding/must alone. Headings and
punctuation are context and excerpt boundaries, not automatic role decisions.
No goal, unknown or AI-origin Care is deleted to produce a mapped status. True
alignment unknowns remain possible and still affect status. Question count,
attribution, grounding, execution authority and other response bounds are retained.

## Compatibility and limits

App/image version is 0.5.7; public response schema remains 0.5.0. Public unresolved
items still contain `scope`, and the status strings are unchanged. This is an
internal model-generation protocol change. Existing Dify parsing does not require
reimport for this test. The model/provider settings have not changed.

The model still decides communicative function, dependency kind, target excerpt,
and materiality. A wrongly declared state can still pass role consistency; a
wrongly selected alignment category can still produce needs_clarification.
Conversely, a bad extraction label can cause a correct factual claim to be rejected.
Semicolon excerpts can lose qualifiers if selected without their enclosing context.
The instructions require preserving those qualifications; candidate generation is
not a semantic guarantee. These risks require review of live results.

The 0.5.7 adapter cannot reconstruct a dependency decision from an old bare scope
field; it rejects that output rather than guessing. Generation uses the existing
JSON-object mode and prompt schema, not guaranteed constrained decoding. Other
free-form statements still require semantic review.

## Local verification and next run

272 tests passed (two existing dependency deprecation warnings). The 24 new tests
cover the observed defects, English/Japanese clause candidates and parent context,
code and OR preservation, Fact role contradictions, preserved View assumptions,
source identity, all dependency kinds, invalid/uncited selections, and the complete
provider-to-diagnostic route. Generated JSON Schema was independently checked
against valid and invalid dependency combinations. These are controlled model
responses, not evidence of live classification accuracy.

Run the identical stage-4 input once after applying the 0.5.6-to-0.5.7 patch. Review
its extraction functions, reference exclusions, scope_decisions, Fact/Care and
unresolved fields. Do not require mapped regardless of content, and do not infer
that all earlier errors are resolved from one successful result. Stage 5 and Dify
remain subsequent checks. The Windows wrapper and the operator's live model
cannot be run here; their behavior is part of the next operator verification.
