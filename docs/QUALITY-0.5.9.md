# 0.5.9: implementation capability versus ambiguous identity

## Observed baseline

The operator's 0.5.8 stage-4 run completed successfully. Format, record count and
branding topics were retained as execution-scoped unresolved items. Fact retained
only the human-reported offline state; human goals and boundaries were preserved.
The response still contained a one-sided missing_premise gap for the assumption
that the user can use a scripting environment OR manually edit a file. Its
dependency was referent, target q10, although the cited proposition concerns
capability rather than an unclear identity. The full report is retained in
tests/fixtures/observed-0.5.8-stage04-diagnostic.json.

## Changes

- Added the internal dependency category execution_assumption for a cited,
  unconfirmed implementation capability/resource. It maps to public execution
  scope, requires its own cited target and is not permitted as a missing-premise
  gap dependency. It does not establish the assumption as Fact or erase it.
- A referent dependency now requires referent_span: a nonblank exact substring
  (at most 160 characters) of the cited target quotation. Other dependency kinds
  cannot carry this field. Both unresolved and missing-premise routes share this
  check. The field is diagnostic/model-facing; public schema remains 0.5.0.
- Instructions distinguish whether a proposition is true from what an expression
  denotes. Tool availability alone is not identity ambiguity or permission to
  disclose data. Preserve OR alternatives, real authority questions, and actual
  conflicts instead of forcing a mapped outcome.
- Diagnostic provider-output-7 targets app 0.5.9. Its existing scope_decisions
  capture the added category and span as part of each dependency. Previous
  versioned diagnostic scripts remain unchanged.

## Evidence and limits

299 controlled tests passed, including the observed missing-span failure, exact
span checks, execution-assumption evidence and alternatives, genuine referent and
authority cases, rejected capability gaps, and mock HTTP/diagnostic paths.
These establish contract behavior, not live-model semantic accuracy.

The witness is necessary structural evidence, not proof of genuine ambiguity.
A model can still select an existing but semantically inappropriate span or a
different inappropriate dependency category, omit a premise, or overstate its
importance. No keyword-based semantic classifier, automatic rerouting, retry, or
silent deletion was added. Invalid generated output can still produce a provider
error. No external verification of the submitted plan's technical claims occurs.

The operator must verify the unchanged 4250-character stage-4 request once on
0.5.9 using verify-stage4-059.ps1. Inspect both unresolved and gaps, their diagnostic
dependencies, Fact/Care provenance, and preserved alternatives. Status alone is
not acceptance. Windows, Docker, Dify and the operator's live model were not run
in the development environment. Stage 5 and Dify follow review of this report.
