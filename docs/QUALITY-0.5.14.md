# 0.5.14 — processing allowances and correction evidence

The observed 0.5.13 stage-4 run recovered from one rejected mapping in 421.235
seconds and returned mapped. Its three capabilities were extracted as assumptions;
its three open implementation topics remained execution-scope unresolved items.
This is evidence for that run, not universal accuracy or a measured downstream gain.
The report is retained in tests/fixtures/observed-0.5.13-stage04-diagnostic.json.

0.5.14 keeps those classification prompts and validation rules. It adds named
processing allowances: low/medium/high permit 0/1/2 corrections after the initial
mapping. Extraction is called once. A successful validated mapping stops early.
The default stays medium; the inference budget remains 2 * LLM_TIMEOUT_SECONDS + 5.
A high run can therefore exhaust its budget before its last permitted attempt.

Ordinary API requests now leave a bounded local trace, including errors and
candidate classification/reference changes. Metadata is the default. Detail text
requires explicit opt-in. Logs carry no claim to capture hidden model reasoning.
A separate append-only correction record links the original and the proposed edit;
no edit is applied to a result automatically. See PROCESSING-MODES.md for the exact
configuration, retention and limitations.

The response JSON schema_version remains 0.5.0. A processing_mode request field and
response headers are additive. Existing Dify parsers remain usable. Server defaults
can be changed without reimporting Dify; per-request selection requires the field
in the Build request JSON. No new model, prompts or lower validation thresholds are
selected by low/high.

Verification: 373 controlled-provider regression tests pass, including all earlier
contract tests and mode/call limits, early success, terminal rejection, timeout,
concurrent isolation, metadata text exclusion, detail omission reporting, logging
failures, retention and correction preservation. Both existing dependency
deprecation warnings remain. Full live model, Windows PowerShell, Docker volume
and Dify execution of 0.5.14 is pending. These tests do not measure semantic accuracy.
The package is checked against the previously delivered 0.5.13 tree, including a
reverse apply check and byte-for-byte comparison after applying the patch.

The next operator check uses one normal HTTP request, initially low, with the same
stage-4 material and model configuration. The wrapper saves request, headers,
response, summary and the server trace. A low-mode 502 may be a correctly rejected
candidate without repair; inspect its trace instead of automatically rerunning.
Do not equate mapped, more calls, or a successful log write with semantic correctness.
After this check, verify the Dify HTTP path and broaden input coverage. Compare
with/without SANA on matched downstream tasks before claiming a measured benefit.
