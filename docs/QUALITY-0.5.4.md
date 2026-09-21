# 0.5.4: source-aware Care generation

The stage-4 operator run on 0.5.3 failed at care.2.evidence.0.source with
user_explicit_requires_human_evidence. The rejected Care text was not captured;
we do not reconstruct it. The stage-3 response is also retained as observed
failure material: a mixed state/requirement was placed in Fact, and ordinary
execution unknowns were placed in premise_gaps.

## Changes

- Mapping includes a server-built Care reference attribution table based on the
  actual source and context speaker, not imperative wording or duplicate text.
- The model-facing Care schema has disjoint human/nonhuman branches. Human anchors
  use user_explicit; AI/source anchors use provided_source. Each branch limits
  its supporting evidence to that source group. Exact clause quotation remains
  required. This does not establish that every selected clause is a genuine concern.
- Existing runtime attribution and grounding checks remain. No generated source
  label is silently rewritten, and AI-origin Care is not blanket-deleted.
- Instructions distinguish mixed state/requirement sentences from factual claims,
  preserve alternatives and modal qualifications in explanations, and separate
  implementation unknowns from comparison uncertainties. No keyword-based
  reassignment of facts, gaps, unknowns or final status is introduced.

The model is asked for JSON using the existing json_object mode. The schema is
guidance in its prompt, not guaranteed constrained decoding. A model can still
violate it; existing validation will reject applicable violations. Semantic
classification, omissions and paraphrase errors remain possible. Prompt changes
are not proof of improved live accuracy.

## Validation and next live run

217 local workspace tests passed with two existing dependency deprecation warnings.
Seven new tests cover source groups including context speakers, identical human/AI
text, rejection of human attribution for AI evidence, preservation of source-labelled
AI Care, and the recorded stage-3/4 failure material. Optional diagnostic tests in
the workspace can make its count differ from a distributed checkout.

The generated JSON Schema was separately checked for validity and tested against
valid human/AI Care entries and crossed attributions. These are controlled tests,
not live model runs. Public response schema remains 0.5.0; app/image is 0.5.4.

First replay the identical 4,250-character stage-4 request. Inspect Care provenance,
Fact vs mixed requirements, execution unknowns, and explanations retaining original
alternatives. Do not require mapped as the success criterion. Compare the recorded
0.5.3 and new runs as fresh stochastic inferences, not a deterministic replay.
The unexplained earlier provider_invalid_output remains unresolved.
