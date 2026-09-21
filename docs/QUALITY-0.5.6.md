# 0.5.6: align extraction capacity with the source-reference budget

The operator's 0.5.5 stage-4 run failed in Extraction, before any stage completed.
The diagnostic identified a Pydantic `too_long` violation at `evidence`.
Extraction still had a 32-item limit, while the existing reference generator can
offer up to 256 candidates. The unchanged stage-4 input produces 47 candidates
(4 human-origin, 43 supplied-AI-origin) in the local implementation.

The old report does not record the rejected list length or duplicate references.
We can establish that it exceeded 32, not that it contained exactly 47 or that
all entries were valid. Zero evidence mismatches in that report is not successful
grounding validation: no validated extraction was available to inspect. This run
does not evaluate the 0.5.5 mapping/classification changes.

## Correction

- Extraction and candidate generation share `MAX_EXTRACTION_REFERENCES = 256`.
  All candidate IDs can now fit in an extraction. This is an upper bound, not a
  target; instructions still request relevant clauses and no repeated IDs.
- Excessive model lists are rejected before source-quote expansion, with
  `provider_excessive_extraction` and `max_items` / `actual_items` in the issue.
  Nothing is silently truncated, deduplicated or merged. Existing exact-reference,
  function, source, grounding and mapping checks remain.
- Other bounds (Care, Fact, View, gaps, unknowns, request size and provider response
  bytes) remain unchanged. The public response schema stays 0.5.0.
- Diagnostic v4 targets app 0.5.6 and records numeric Pydantic length limits and
  actual lengths when supplied by Pydantic. It does not print rejected raw values
  or arbitrary error context. Previous diagnostic files remain unchanged.

## Verification

248 local tests passed (two existing dependency deprecation warnings). Five new
tests cover the shared 256-item boundary, 257-item rejection before expansion,
all 47 original stage-4 candidates arriving at mapping without truncation, and
diagnostic count reporting. Model responses are controlled in these tests.
The observed operator report is retained in
`tests/fixtures/observed-0.5.5-stage04-error.json` without inventing its lost clauses.

This fixes a capacity mismatch, not demonstrated live semantic accuracy. The model
may still omit or duplicate clauses, misclassify functions, exceed bounds or choose
the wrong comparison scope. A larger extraction may increase mapping input and
latency. We do not claim that all long plans now pass or that previous intermittent
errors are resolved. No retry, question suppression or forced mapped status is added.

Next: run the identical stage-4 request once with app 0.5.6 and diagnostic v4,
then review the saved report. Stage 5 and Dify remain pending. Windows execution
of the new wrapper and real-model behavior cannot be exercised in this workspace;
the Python diagnostic and application paths were tested with controlled responses.
