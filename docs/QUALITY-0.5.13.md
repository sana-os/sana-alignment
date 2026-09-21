# 0.5.13: require an affected premise for scope interpretation

## Observed 0.5.12 run

The operator ran stage 4 with provider-output-10 on 0.5.12. Both verification
hashes matched. Request 76064e91-d4a5-46b0-b9ec-93c3c7f59b19 completed in 409.431
seconds, within the 605-second budget, with three model calls and one retry.
The first mapping failed provider_non_factual_evidence because Fact cited mixed
q5. The correction removed it from Fact and the final response passed validation.
This demonstrates one observed recovery, not a measured success rate.

The final status was needs_clarification. The first attempt's format, count and
branding items had execution_detail dependencies. The second instead selected
constraint_scope with targets q10/q11/q12, all extracted unknowns. Those were not
stated boundaries whose meaning was unclear. The 0.5.12 unresolved resolver only
required a valid cited ID and allowed this semantic regression through. The run
also labelled three posited capabilities in the Assumptions section state instead
of assumption. They were not included in the final Fact list, but the extraction
labels remained problematic. The original report is retained unchanged at
tests/fixtures/observed-0.5.12-stage04-diagnostic.json.

## Changes

- goal_meaning, constraint_scope and comparison_assumption in unresolved now
  require a target not labelled unknown by extraction. They describe the meaning
  or scope of an affected goal, boundary or compared premise; an open topic alone
  is not that affected premise. Invalid selections raise
  provider_invalid_scope_dependency with rule
  alignment_requires_affected_premise_not_open_topic.
- An unknown can still be quoted in evidence alongside the separate affected
  premise. The runtime rule and the generated schema's dependency branches agree.
  The rule is applied to the first mapping and correction equally, and the error
  is eligible for the existing single retry. No status is forced and no item is
  automatically moved, relabelled or deleted.
- authority and referent retain unknown targets: an unknown approver or an
  unidentified expression can itself be an alignment issue. Exact referent-span
  checks remain. Execution dependencies are also unchanged. The distinction is
  by declared dependency and extraction labels, not words such as format/count.
- Correction guidance explicitly preserves valid execution routing while fixing
  other fields. It forbids changing a kind or target merely to evade validation.
  This is generation guidance, not a claim that a model cannot change judgments.
- The state definition now distinguishes a condition reported as actually
  holding from a prerequisite posited for a plan, without requiring external
  verification. English/Japanese contrasts show an assumption, a reported test,
  and a mixed report. Mapping guidance no longer tells the model to disregard
  heading context; headings are relevant framing but not a label or proof of truth.
  No heading-matching classifier or automatic extraction repair was introduced.
- Diagnostic provider-output-11 targets 0.5.13. Each attempt's scope_decisions now
  includes evidence IDs, the target's extraction function, and whether that target
  was labelled unknown. Existing attempt timing, outcome and error records remain.

## Verification and limitations

352 controlled tests passed. New cases reject the three observed unknown targets
under each of the three affected dependency kinds, preserve a genuinely unclear
human boundary with its supporting unknown, retain authority and referent unknowns,
and check generated choices. Full provider/engine tests reconstruct relevant
mapping fields from the observed response, exercise one repair without losing
Care or open topics, and reject the observed Fact-error-then-scope-regression
sequence at the retry limit. The original raw Draft was not available, so the
reconstruction is not claimed as an exact replay. Two existing dependency
deprecation warnings remain.

An output accepted by 0.5.12 can now be rejected by 0.5.13, including after the
single correction. The limit stays one mapping retry; no further call is made to
obtain a desired status. The total budget remains 2 * LLM_TIMEOUT_SECONDS + 5
(605 seconds at the existing 300-second setting), shared by up to three calls.
Public schema_version stays 0.5.0 and execution_authorized stays false.

The added guard is structural, not a proof of relevance or logical support. A
model can select an unrelated non-unknown target, choose the wrong dependency,
or misclassify extraction. In particular, changing assumption instructions does
not establish improved live-model accuracy, and the correction reuses extraction.
There is no semantic agreement/consistency guarantee between two generated maps.
Review the final content and both attempts. Windows PowerShell, Docker, Dify and
the operator's model were not run here.

Use verify-stage4-0513.ps1 once with the same input, model and timeout. The wrapper
checks application, diagnostic and input hashes and requires retries=1. Share the
saved 04.diagnostic.json whether successful or rejected. Review routing, Fact/Care,
attribution, assumptions and timing before stage 5 or Dify. Dify re-import is not
needed for this unchanged response schema; its transport limits remain a separate
integration check.
