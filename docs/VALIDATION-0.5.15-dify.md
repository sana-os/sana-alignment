# Operator observation: fixed-proposal Dify run

Request `87642555-a65d-4618-b509-9e9dd874286a` returned a final `mapped` label and
response JSON with matching status. This was supplied after the operator was
instructed to place processing_mode=medium inside Build request's payload and to
paste the decoded stage-4 proposal. The response schema is 0.5.0. Application
0.5.15 is the surrounding operator context, not a field verified by this response.

The parsed response and provenance hashes are retained in
`tests/fixtures/observed-0.5.15-stage04-dify-{response,files}.json`. The original
uploaded text remains unchanged. No additional inference was run for this review.

## Confirmed from the supplied output

- The reported Dify test produced the terminal status and full JSON, providing
  evidence of a successful comparison-workflow run for this installation.
- The response validates against the local response model. All 57 quote
  occurrences match their attributed sources in the known stage-4 fixture.
- The full human input matches that fixture. Matching source excerpts do not prove
  byte-for-byte equality of the entire submitted AI proposal; the sent request
  was not included.
- Fact contains only the human-reported lack of internet connectivity.
- Care retains the human display goal and real-data prohibition. The extra data
  policy entry is explicitly attributed to the supplied AI, not to the human.
- Format, record count and possible branding constraints remain cited execution
  uncertainties with null questions. They also occur as unknown-support View
  entries; that duplication is visible, not a conversion into resolved facts.
- No premise gaps or hypotheses are reported. Execution authorization remains false.

## Limits and variation

This response has no processing-mode or attempt-count fields. No HTTP headers,
server trace or elapsed time were supplied. Therefore this record does not verify
that medium was selected, that a repair occurred, or how long the run took. Those
details must be established from the corresponding trace, not inferred from mapped.

Unlike the earlier direct-HTTP response, this sample attaches specific field and
element quotations to the corresponding View entries, so it does not reproduce
the earlier broad-list/single-heading example. That difference is one new sample,
not evidence that citation coverage has been fixed generally.

The UI/scripting/library assumptions remain in View with provided_source attribution
and externally_verified=false, but their statements no longer explicitly say
Assumption. Their original heading context matters. A reader should not treat
provided support for a reported proposal as established implementation capability.
The View is selective: some fields and later implementation steps occur only in
observations, and the code block is not reproduced there. This response does not
certify complete plan coverage, code correctness or external claims in the plan.

## Next integration step

The fixed-proposal workflow has produced a successful operator-reported result.
The next distinct check is the Plan and Align workflow: keep the same human request,
select the configured planning model, explicitly include processing_mode=medium in
Build request, and run once. Retain the generated proposal, serialized HTTP request,
HTTP response headers/status, final response and corresponding SANA trace. Assess
the actual new proposal; do not require mapped regardless of its content. The
planning call and SANA's internal repair calls have different roles and budgets.

This observation is integration evidence for the supplied installation, not a
general success-rate measurement or authorization to publish or execute a plan.
