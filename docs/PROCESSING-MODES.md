# Processing modes and correction records

Status: implemented in application 0.5.14; response schema remains 0.5.0.
Controlled-provider tests pass. Normal-HTTP low/medium failures and a subsequent
0.5.15 medium recovery are recorded in the [evidence archive](validation/README.md).
Both Dify paths have reported successful outputs; their actual mode/call counts
were not included in those final outputs. No live high-mode result is claimed.

## Purpose

SANA supplies a source-attributed premise map to a downstream process. The release
goal is bounded useful assistance with inspectable errors, not a claim of perfect
classification across every input. Known error tendencies should be documented
with the model, configuration and observed cases that support them. Users need to
be able to inspect and correct an interpretation after the run.

More inference is a processing allowance, not a guarantee of greater accuracy.
A second map can correct one error while introducing another. An improvement over
running without SANA must be measured with matched inputs and downstream models;
the stage-4 diagnostic runs alone do not establish that improvement.

## Initial modes

Canonical configuration values: low, medium, high. The default is medium, retaining
the current allowance. Each substantive run performs extraction once, then mapping.

| Mode | Initial mapping | Maximum mapping corrections | Maximum model calls | Purpose |
| --- | --- | --- | --- | --- |
| low | 1 | 0 | 2 | Fast premise map with a record of detected limitations |
| medium | 1 | 1 | 3 | Current bounded correction behavior |
| high | 1 | 2 | 4 | One further opportunity to correct a validation-rejected map |

A successful validated map ends the run. High does not always spend four calls and
does not yet mean an independent semantic review or model ensemble. Greetings and
extraction-only short routes keep their existing smaller call counts. Log actual
calls separately from the configured maximum.

All modes share source-attribution, exact-quote, schema and dependency validation.
Low is not permission to present invalid output as a valid map. A rejected candidate
leaves metadata; its text is available only with detail tracing enabled; the normal API result stays an
error when no attempt passes. Semantic uncertainty in a structurally valid map can
remain visible in the map and its limitations. Execution is never authorized by SANA.

The implementation retains the existing total deadline by default:
2 * LLM_TIMEOUT_SECONDS + 5, including all attempts (605 seconds with the current
300-second setting). Raising an attempt allowance does not automatically raise
that deadline. Report effective mode, call limit and deadline together. Deadline
exhaustion stops the run; it does not trigger another request or a silent fallback.
Timeouts, refusal, rate limits and transport failures retain their no-retry behavior.

## Trace contract

Use request_id to connect the API result/error with an application-level trace.
This works in the ordinary API endpoint, including Dify HTTP requests. Historical direct-engine diagnostics are separate and do not write endpoint traces.
The trace format is alignment-trace-1. See configuration and retention below.

Default operational records contain:

- Request/trace ID, UTC timestamp, application and public schema versions.
- Effective mode, configured retry/deadline limits, actual stage and attempt counts.
- Provider model identifier and non-secret generation settings, where available;
  prompt, knowledge and input hashes. Mark unavailable model/runtime details as
  unknown rather than inferring them.
- Per-attempt duration, validation outcome, error code/path/rule and retry decision.
- Reference IDs and classification/routing changes that explain why the selected
  result differs from an earlier candidate; distinguish a changed judgment from
  a verified correction.
- Final status or terminal error, timeout information and execution_authorized=false.

Keep credentials and authorization headers out of logs. Full input text, exact
excerpts and candidate/final payloads belong in an explicitly enabled local detail
trace, with size/retention limits. Default metadata traces can identify a run but
cannot reproduce its content without the corresponding saved input. Hashes are
identifiers, not a promise of anonymization. Do not export logs automatically.

If a detail trace is truncated or cannot be written, record that fact. A missing
trace must not be reported as saved. Store observable outputs, cited evidence and
concise decision summaries, not a claim to record hidden model reasoning.

## Known limitations and corrections

Maintain a versioned list of observed failure patterns. Each entry should identify
the model/configuration coverage, affected field, consequence, evidence/run IDs,
current guard or mitigation and remaining uncertainty. Do not turn a small sample
into an error-rate claim or a universal trait of every supported model.

Initial evidence from this development sequence:

| Pattern | Observed evidence | Current handling / limitation |
| --- | --- | --- |
| A mixed state/requirement enters Fact | 0.5.12 stage 4, first attempt | Rejected; one correction removed it. Extraction labels can still be wrong. |
| Implementation unknowns become alignment issues | 0.5.12 final map; 0.5.13 first attempt | Explicit affected-premise checks and correction. Irrelevant non-unknown targets may still pass structural checks. |
| Posited capability is labelled state | 0.5.12 extraction | Guidance revised; 0.5.13 labelled the three clauses assumption. This is one observation, not a reliability estimate. |
| Correction changes previously suitable routing | 0.5.12 first vs second attempt | Retain both attempts; validate every attempt equally and review the final meaning. |
| A supplied claim is mistaken for verified reality | General contract risk, not an error-rate claim | Preserve attribution and externally_verified=false; provided is support at the stated scope, not external verification. |

A later correction is a separate operator-supplied record linked to the original request,
field/item and source reference. Record the proposed correction, concise basis,
who or what proposed it, and whether a person accepted it. Preserve the original
trace. A proposed correction must not overwrite the original or acquire human
authority automatically. These records can become regression cases; logging alone
does not train the model or establish that a correction is true.

## Release evidence

Separate application contract failures, semantic quality findings and transport
failures in reporting. Publish known limits alongside the chosen default mode.
Modes and logs do not replace regression coverage for attribution, preserved
boundaries, real conflicts, uncertainty, call/deadline limits and diagnostic integrity.

Before asserting downstream benefit, compare the same tasks with/without SANA,
holding downstream model/settings constant. Record material boundary violations,
missed goals, unnecessary clarification, useful corrections and elapsed time.
Keep observed results distinct from untested acceptance criteria.

The observed 0.5.13 stage-4 run used request
561124f4-28d4-459f-bde0-a28c65c9fc90, diagnostic provider-output-11 and matching
verification hashes. It took 421.235 seconds with one retry, returned mapped,
kept the three open topics in execution scope and the three capabilities labelled
assumption, retained human goal/boundary in Care, and granted no execution authority.
The exact report is tests/fixtures/observed-0.5.13-stage04-diagnostic.json.
This supports moving from an endless single-case tuning loop toward bounded modes,
traceability and broader evaluation; it does not certify the entire plan or all cases.


## Configuration and saved records

Request field `processing_mode` accepts `low`, `medium`, `high`, or null/omission.
It overrides the server default for this request and is not sent to the model.
Server default: `SANA_PROCESSING_MODE=medium`. When that variable is absent,
legacy `SANA_MAPPING_RETRIES=0|1` still selects low/medium; when present, the named
mode wins. The legacy numeric variable does not accept 2; use high for two repairs.
This is a per-request allowance, not a server quota or an independent semantic review.

`SANA_TRACE_LEVEL=metadata` is the default; `detail` enables original inputs,
model-visible messages, candidate content, source references and final results.
`off` disables writes. Detail records do not include API keys, authorization headers,
or a provider's separate reasoning channel. Saved text may itself contain sensitive
information supplied by the caller/model: review it before sharing.
`SANA_TRACE_DIR` defaults to `traces` (relative to the application working directory).
The supplied Compose file mounts the persistent named volume `alignment_traces`
at `/app/traces`; it survives container replacement. `docker compose down -v`
deletes named volumes. Retention is not a backup.

Records are saved as `trace-<request_id>.json`. Both successful results and terminal
processing errors have `X-SANA-Request-ID`, `X-SANA-Processing-Mode` and
`X-SANA-Trace-Status` response headers. The successful JSON request_id is the same.
Trace status is `saved`, `saved_with_omissions`, `failed`, or `off`. The JSON response
contract is unchanged. A failed write leaves the alignment result intact and emits
an operational error with its ID. Invalid request bodies and failed authentication
are rejected before model processing and do not produce these alignment traces.
A process crash or forced container termination can prevent a completed record;
this is a completed-run log, not a durable per-token journal.

Retention at write time is seven days, at most 1,000 trace/correction files and
64,000,000 bytes in this store. Oldest records are removed to keep those limits.
Records are never overwritten under an existing ID. Details are capped at
1,000,000 bytes per run: omitted detail fields are named in `detail_omissions`.
A whole record exceeding 2,000,000 bytes is rejected and reported as a failed write.
Retention runs on writes; an idle server does not run scheduled cleanup.
The supplied single-worker process serializes store writes. Multi-worker/shared
network-folder operation has not been verified.

`model_calls[].outcome=parsed` means the provider output parsed; the engine can still
reject that candidate. `mapping_attempts` gives the final validation outcome for each
attempt. `decision_changes` compares allowlisted labels and reference IDs by item
path between candidates. Reordering can appear as a change: these are observed
changes, not verified corrections or semantic equivalence judgments. Freeform
statements/quotes are available only in detail mode. Unrecognized rejected field
names are masked in metadata validation paths.

The inference deadline includes queue time and all model calls. Saving the trace
happens after inference; no extra model attempt is started while saving.
Temperature/seed are recorded as provider defaults unknown; this application does
not silently change them. Request hashes use sorted UTF-8 JSON serialization, not
the original file bytes. `material_sha256` excludes processing_mode, allowing the
same submitted material across modes to be identified.

## API and Dify use

Set a server default in `.env` and recreate the container, or add a field in the
JSON body produced by Dify's Build request node:

```json
{"input_message":"Hello","language":"en","processing_mode":"low"}
```

For a plan comparison, retain the existing input_message and ai_interpretation and
add processing_mode to that same object. Parse response and status branches can
remain unchanged for schema 0.5.0. Dify's HTTP response headers hold the request ID
on errors as well as success. Read/connect/proxy limits remain separate from SANA's
budget: a high allowance does not prevent a Dify timeout. Start direct API checking
with the packaged verification script, then check Dify's path once.

## Correction record

An operator can submit UTF-8 JSON via stdin to `python -m app.corrections` in the
container. Example structure (replace the ID with an existing trace):

```json
{
  "request_id": "561124f4-28d4-459f-bde0-a28c65c9fc90",
  "field_path": "view.unresolved",
  "proposed_change": "Retain the specified implementation unknown.",
  "basis": "Cite the original plan clause and explain the discrepancy.",
  "proposer": "human",
  "review_status": "proposed",
  "evidence_refs": []
}
```

The module requires the original trace, checks supplied reference IDs, and saves
`correction-<id>.json` with the original file hash and timestamp. It does not verify
the meaning of the proposed edit, overwrite an original, update an API result,
train a model or authorize execution. Review status is the submitter's report;
accepted is not an authentication or approval grant. No corrections are generated
automatically. Correction text is saved because the operator explicitly submits
it; store retention also applies to these records.


## 0.5.15 correction-feedback addition

A failed mapping now records `error.repair_contract`, version
`mapping-repair-contract-1`. It groups reference IDs involved in collected
violations, extraction labels and the existing valid dependency forms. This is
server-built feedback, not a corrected result. It is sent to the model only when
`retry_decision` is `retry`. Low and exhausted attempts may have this record but
start no additional call. No freeform source/candidate text is included in it.

The observed 0.5.14 low and medium failures are documented separately in
VALIDATION-0.5.14-low.md and VALIDATION-0.5.14-medium.md. They validate bounded
attempts and the normal endpoint trace path, not successful mapping or an accuracy
ranking across modes. Interpretation and correction quality remain model-dependent.
