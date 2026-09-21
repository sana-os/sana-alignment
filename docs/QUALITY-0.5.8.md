# 0.5.8: open-topic routing across gaps and unresolved items

## Observed baseline

The operator's 0.5.7 stage-4 diagnostic, request
`f948475d-33ad-4fe8-9c21-f096d5e77cef`, completed both model stages with 31
extracted clauses and no reported evidence mismatch. Fact contained only the
human-reported offline state. The mixed environment clause and three assumptions
were correctly excluded from Fact. Human goals and constraints remained in Care.

However, the three unknown implementation topics (format, count, branding) were
placed in `missing_premise` gaps, with no unresolved items or scope decisions.
The result was `mapped_with_divergence`. This bypassed the 0.5.7 unresolved-only
dependency contract. The complete operator report is preserved in
`tests/fixtures/observed-0.5.7-stage04-diagnostic.json`.

## Changes

- Model instructions require choosing execution versus comparison relevance before
  selecting the output container. Open implementation topics must be retained in
  execution-scoped unresolved items, not renamed or discarded.
- Each generated `missing_premise` gap requires the same structured dependency
  category used for alignment unresolved items, and a cited target that is one of
  its actual comparison positions. Execution-detail dependencies are rejected.
- A comparison whose selected positions are all extracted unknowns is rejected
  under any gap kind. Evidence that merely cites the overall human request is not
  itself a selected comparison position.
- Other gap kinds retain the existing cited-position protocol. Genuine conflicts,
  consequential one-sided assumptions, source identity, alternatives and full
  quoted positions remain supported. Public schema_version remains 0.5.0.
- Diagnostic provider-output-6 targets app 0.5.8 and records dependency selections
  from both unresolved and gap containers, including failed provider outputs.
  Prior versioned diagnostics are unchanged.

## Limits

These are structural consistency checks and model instructions, not semantic
proof. A model can still misclassify an unknown, choose an irrelevant non-unknown
target, overstate materiality, or omit a topic. Compound source excerpts remain
possible. The server does not guess categories from keywords, silently reroute or
drop gaps, or force a mapped status. Invalid output returns a provider error and
may require further model-guidance work. No automatic retry was added.

## Validation and next step

284 controlled tests passed. Added cases reproduce the observed unknown-only gap,
reject relabelling it as another gap kind, preserve execution unknown evidence,
reject invalid dependencies without mutation, and preserve real conflicts and
one-sided choices. Mock HTTP provider tests exercise the diagnostic path for both
success and rejection. These are not live-model accuracy results.

The generated OpenAPI document was refreshed. Windows, Docker, Dify and the
operator's model were not available for execution here. Run the bundled stage-4
verification once on 0.5.8 with the same 4250-character request and unchanged model
settings; inspect the saved diagnostic before stage 5 or Dify. Do not use status
alone as the acceptance criterion.
