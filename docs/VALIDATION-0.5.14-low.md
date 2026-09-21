# Operator observation: 0.5.14, stage 4, low mode

Request: f5e3f217-81cb-433a-8b04-d8a740061d6f.
Evidence: the operator's pasted wrapper summary and uploaded trace.json, copied
without changes to tests/fixtures/observed-0.5.14-stage04-low-trace.json.
The application was 0.5.14 and the trace format alignment-trace-1, metadata level.
No new model inference was run during this analysis.

## Identity and outcome

The known stage-4 source file SHA256 is
feb95a60f6cf826f2a10576cd7d3f27dbe4ef101a3d67641a2e692f55d9f2b42.
Loading that request under the installed request model and adding processing_mode
low reproduces both trace request_sha256 and material_sha256. Reconstructing the
reference registry from the known input and recorded extraction IDs matches all
39 reference quote hashes. This reconstruction supplies the known source text;
it does not recover unsaved model-generated statements.

The submitted request file's byte hash in the wrapper summary and the canonical
parsed-request hash in the trace use different serializations. Their difference
is expected; they must not be compared as byte-identical files.

- HTTP 502, provider_invalid_output; curl exit 0 means curl received the response.
- Extraction produced parseable output in 71.161 seconds.
- Mapping produced parseable JSON in 183.220 seconds, but Draft validation rejected
  a missing required view.hypotheses field. The attempt lasted 183.225 seconds.
- Actual model calls: 2. Mapping attempts: 1. Retries: 0.
- Retry decision: limit_reached, matching low's configured zero corrections.
- Trace status: saved; the wrapper reported successful copying to trace.json.
- Execution authorization: false. No validated final map exists for this run.

This verifies the observed low call bound, error propagation and ordinary endpoint
trace/save/copy path. It does not establish usable alignment output, semantic
correctness, successful correction, log retention after container replacement,
high mode, or the Dify route.

## Why the field matters

With a supplied AI interpretation, the current model contract requires
view.hypotheses: [] rather than an invented third plan. In 0.5.14 the field must
still be present. Its omission is a schema failure even when the surrounding JSON
is parseable. No silent empty-list insertion or application update was performed
as part of reviewing this run. The rest of the candidate has not passed every
engine check, because Draft validation failed before final mapping validation.

The isolated regression in test_observed_missing_hypotheses_0514.py covers two
controlled cases: low reports the missing-field error and stops; medium conveys
the same path/rule in correction feedback and accepts a supplied valid second
response. Both tests passed. They reproduce the reported failure condition, not
the complete unsaved model candidate, and do not demonstrate live recovery.

## Candidate quality observations

These refer to the rejected candidate, not a final accepted map:

- Human request and prohibition are represented by two Care selections, q3/q4,
  attributed to user_explicit. Fact selects q2, the human connectivity state.
- Format, record count and possible branding constraints are all selected as
  execution_detail unresolved topics (q10/q11/q12).
- q5 includes both lack of connectivity and the plan's requirement that all data
  be generated locally. It is labelled state during extraction even though it
  combines roles. The candidate places q5 in View, not Fact. This remains evidence
  of a role-classification error without evidence of Fact contamination here.
- q7 is the plan's assumption that the demo interface can receive file data or
  hard-coded structures. It is labelled assumption, but a missing_premise gap
  targets it with comparison_assumption and blocks_execution=true. This merits
  semantic review for overclassification of an implementation capability as an
  alignment issue. Metadata does not contain the full generated statement or all
  selected comparison positions, so it does not settle that interpretation.

## Timing caveat

The server trace elapsed_seconds is 254.397; its stage times sum to approximately
that total. The operator's Windows wrapper reports 247.994. Both carry the same
request ID, but differ by 6.403 seconds, with server time exceeding client time.
The cause is not established. Do not describe this as ordinary network overhead or
combine these measurements into one latency figure. Keep the two clock measurements
separate during later comparisons; this does not explain the explicit schema error.

## Next bounded check

Keep application 0.5.14, input and model settings; invoke the same wrapper once
with -Mode medium. This is a new inference, not a continuation of the saved low
candidate. An allowed correction is used only if that new mapping fails with a
repairable validation error. No manual success-until-repeated loop is proposed.
Review summary.json, trace.json and response.json before the Dify route. In
particular, compare actual calls, correction reasons and resulting classifications
without attributing all differences between independent samples to mode alone.
