# 0.5.11: align generation guidance with comparison validation

## Observed baseline

The 0.5.10 provider-output-8 stage-4 run completed Extraction, then failed during
Draft resolution with provider_invalid_gap_dependency, path
view.premise_gaps.0.ai_premise, rule open_topics_alone_are_not_comparison_positions.
The generated dependencies pointed at q10/q11/q12, the format/count/branding
unknowns, with kind constraint_scope. No validated Draft or support_review existed.
The exact operator report is retained in
tests/fixtures/observed-0.5.10-stage04-diagnostic.json.

## Conflicts found and changes

- The main extractor instructions said to label known mixed functions mixed, but
  Provider.generate appended a later instruction saying unclear. The appended
  instruction now agrees: mixed for known combined functions, unclear for an
  indeterminate function. This does not decide semantic labels from punctuation.
- Older mapping prose still prescribed scope=execution or scope=alignment, while
  the current wire protocol requires dependency. Those instructions now refer to
  dependencies; a repeated routing paragraph was removed. A blanket instruction
  to empty unresolved items when no material issue existed was narrowed to gaps,
  so relevant execution unknowns remain retainable.
- Assumptions headings are described as evidence of the author's framing, not
  proof of truth and not context to ignore. Declarative capability wording alone
  does not establish that a posited condition is an observed state.
- The generated Gap schema now mirrors the runtime requirement that at least one
  selected comparison position is not an extracted unknown. An unknown on one
  side is still permitted with a concrete position on the other. Evidence remains
  available; no text is deleted. If no concrete positions exist, gap items are
  disallowed while an empty gap list remains valid.
- Missing-premise dependency kinds and targets are restricted directly on the
  dependency property. It no longer advertises execution kinds and unknown
  targets in a permissive base schema overridden by a distant conditional.
  Existing runtime checks, including speaker identity and cited-target checks,
  remain unchanged.
- Diagnostic provider-output-9 targets 0.5.11 and adds rejected_draft_review on a
  failed draft: bounded support labels and reference IDs, explicitly marked
  validated=false. This is not a successful result or evidence of correct meaning.
  It includes original item counts and its diagnostic limits; validated output
  and model responses are never truncated or repaired by this feature.

## Validation and remaining limits

318 controlled tests passed. Added cases compare generated choice sets with the
runtime guard for unknown-only, one-sided and concrete comparisons; retain the
observed rejected targets; exercise the real provider/diagnostic adapter with a
mock model; and verify bounded rejected-label reporting. The complete prompt sent
to the mock model is checked for the mixed/unclear and scope/dependency conflicts.
These are not live-model accuracy results or a full JSON Schema conformance audit.

The provider uses JSON-object mode and supplies the schema as prompt text. It does
not enforce constrained decoding. A model can ignore the schema, misclassify a
clause, omit information or select a semantically inappropriate concrete target.
Quote matching still cannot prove logical support or truth. No retry, third model
stage, automatic relabelling, or relaxation of runtime validation was introduced.

Public schema_version remains 0.5.0. Run the unchanged 4250-character stage-4 input
once with verify-stage4-0511.ps1, retaining model settings. Review extraction roles,
execution unknowns, assumptions, Fact/Care provenance and support labels before
stage 5 or Dify. Windows, Docker and the operator's model were not run here.
