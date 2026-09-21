# 0.5.12: one bounded mapping correction attempt

## Observed baseline

The operator's 0.5.11 stage-4 report used diagnostic provider-output-9 and the
unchanged 4250-character AI plan. It failed with provider_invalid_scope_dependency
at view.premise_gaps.0.dependency (dependency_requires_kind_and_target_ref).
All three reported gap dependencies were null in the diagnostic; v9 did not
distinguish an absent property from an explicit null. Extraction labelled the
environment clause mixed, the three capabilities assumption, and the three open
topics unknown. The rejected candidate nevertheless cited mixed q5 in Fact.
The report is retained verbatim in tests/fixtures/observed-0.5.11-stage04-diagnostic.json.

The user authorized bounded additional inference. This replaces the earlier
no-additional-call constraint; validation and source-attribution rules remain.

## Recovery contract

- SANA_MAPPING_RETRIES defaults to 1; only 0 and 1 are accepted. The HTTP endpoint
  and diagnostic v10 pass this policy into the engine. Direct Python callers of
  align retain the historical zero-retry default and can explicitly pass 1.
- Extraction runs once. A valid extraction, original request, source registry,
  speaker assignments and classification labels are reused without alteration.
  Mapping payloads are copied per attempt and state is local to the request.
- An explicit allowlist of output-contract errors permits one complete mapping
  regeneration. Feedback includes the error code/path/rule and up to 16 detected
  structural violations. Independent Fact exclusions and comparison/dependency
  checks can be reported together even when normal validation stops at the first
  error. These checks reuse the existing resolvers; they do not infer new labels.
- No target status is requested. The correction prompt preserves real conflicts,
  unresolved topics, alternatives and boundaries. A regenerated mapping passes
  the same provider checks, engine validation and final response construction.
  No rejected candidate is silently repaired, returned or merged into a result.
- Extraction failures, network/HTTP errors, rate limits, timeouts, refusals,
  incomplete responses and oversized provider responses do not trigger a retry.
  A second invalid mapping returns its error. There is no third mapping attempt.
- The total budget remains 2 * LLM_TIMEOUT_SECONDS + 5, including any retry.
  With the existing 300-second setting this is 605 seconds across at most three
  model calls. The deadline can cancel an unfinished correction; it is not a
  promise that all calls receive a full per-call allowance. The HTTP budget also
  includes the concurrency queue. Diagnostic execution has no HTTP queue/proxy.
- The public schema_version remains 0.5.0. Meta stages and error response shapes
  are unchanged. No new execution permission or external verification is granted.

## Diagnostic and verification

Diagnostic provider-output-10 targets application 0.5.12. mapping_attempts retains
each attempt's elapsed time, outcome, error, retry decision, dependency selections
and bounded candidate review (including gap positions and dependency_present).
retry_count, model_call_count, total elapsed time and retry_policy are explicit.
generated_stages describes parsed provider objects; completed_stages includes Draft
only if all engine validation passed. Candidate reviews remain validated=false.
Public result and support_review appear only for a successful final mapping.
No raw invalid Draft is sent back as a trusted instruction.

verify-stage4-0512.ps1 checks the application, diagnostic and input hashes and
requires the container's retry setting to be 1 before inference. Old scripts and
packages are unchanged. The request is still stage04.en.json, SHA256
feb95a60f6cf826f2a10576cd7d3f27dbe4ef101a3d67641a2e692f55d9f2b42.

337 controlled tests passed, including recovery from the observed combination of
missing dependencies and mixed Fact evidence, rejection on the second attempt,
engine-level rejection inside the retry boundary, disabled recovery, unchanged
extraction/payloads, non-retryable errors, malformed-JSON recovery over HTTP,
preservation of a real constraint conflict, cancellation, and concurrent request
isolation. The recorded extraction and selected violations inform the fixture;
the test does not claim to replay an unavailable complete raw rejected Draft.
Existing single-attempt contract tests explicitly disable retry. Two pre-existing
dependency deprecation warnings remain.

These are mocked-provider tests, not measured improvements in live-model accuracy
or latency. Windows PowerShell, Docker, Dify and the operator's model were not run
here. Runtime checks cannot catch every semantic omission or unsuitable judgment.
Review both attempts and final meaning, not just whether an error disappeared.

Run unchanged stage 4 once using the packaged wrapper and share 04.diagnostic.json,
including when the wrapper warns. Keep the model and timeout unchanged for this
comparison. Stage 5 and Dify testing follow review of that result. Dify's HTTP
retry remains off; its/proxy time limits need separate review before integration.
