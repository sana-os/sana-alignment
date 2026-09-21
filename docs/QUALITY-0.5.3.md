# 0.5.3: source references during extraction

An operator's fresh 0.5.2 diagnostic on the long offline-demo plan failed with
`provider_ungrounded_evidence` after Extraction returned. Fourteen proposed quotes
were not exact substrings of `ai_interpretation`. They included removed Markdown,
joined headings and prose, compressed lists, and a prose summary of code. Mapping
had not started. This identifies the fresh diagnostic failure, not the exact cause
of the earlier Dify HTTP-node failure.

The fixture `tests/fixtures/observed-0.5.2-extraction-mismatches.json` preserves the
diagnostic fields and all fourteen mismatches, storing their identical source text
once. It does not contain the successful extraction clauses or an inferred full
model response.

## Change

The HTTP provider now supplies a server-built extraction reference index. The model
returns `{ref, function}`; the adapter restores source/quote before existing engine
validation. Free-text quotes, unknown IDs, and extra fields are rejected with
`provider_invalid_extraction_reference`. Exact-substring validation is retained.
There is no fuzzy matching, Markdown normalization, automatic quote repair, retry,
extra model call, or execution of submitted code.

Candidates contain the complete sources and mechanical line/sentence excerpts.
Fenced code remains whole. Original markup, internal whitespace and Unicode are
preserved. At most 256 candidates are provided; excessive candidates are grouped
into contiguous larger excerpts rather than dropping the remaining source. All
original sources remain available in both stages. Reference IDs preserve source
identity even when two speakers submit the same words.

These boundaries are not semantic parsing. Inline code and marked-up lines are
kept whole; sentence splitting can be imperfect. The model must read surrounding
context and choose a broader reference when needed. Mixed functions should remain
unclear rather than becoming a whole-paragraph Care anchor. Candidate selection,
classification, omission, and comparison errors remain possible. This change does
not validate claims inside the generated plan or guarantee any particular status.

Application/image version: 0.5.3. Public schema: 0.5.0. Existing Dify parsers that
accept 0.5.0 remain compatible. Extraction's private model-facing format changes;
the adapter continues returning the same internal Extraction model to the engine
and diagnostic recorder.

## Validation

205 local tests passed, including eleven new cases covering all fourteen rejected
quotes, exact Markdown/code restoration, Japanese and English candidate separation,
source identity, bounded indexes, invalid references, and the HTTP provider adapter.
Existing end-to-end mocked provider and engine tests also pass. Two dependency
deprecation warnings remain. Tests use recorded inputs and mocked responses, not
live model generation. A live rerun of the observed plan is still required.
