# Migration to 0.5.0: bounded effects and source excerpts

Application/image and response schema are 0.5.0; profile is workflow-premise-map-v0.5.
This is a response-contract change. Request format and status meanings remain unchanged.

Follow-up: application 0.5.1 keeps schema 0.5.0 and additionally bounds Care statements to
extracted concern quotations. See [QUALITY-0.5.1.md](QUALITY-0.5.1.md) for its source-language
behavior, staged evidence contract and remaining classification limits.

## Public output

| Field | 0.4 behavior | 0.5 behavior |
| --- | --- | --- |
| Fact/View execution_effect | Required generated string | String or null, default null; a string is an exact quote from that premise's evidence |
| view.understanding | Generated prose summary | Source-labelled original excerpts, or a localized short reply |
| view.understanding_evidence | Absent | Exact source/quote pairs used for the excerpt overview; [] for short replies |
| meta.understanding_mode | Absent | source_excerpts or short_reply |
| Care execution_effect | Server-supplied null | Unchanged |

An effect quotation reports what was stated; it is not a verified effect or an action performed.
The mapping model selects an evidence ID or null; the server requires that ID to be cited on
the same premise before resolving the exact quote. No generated effect text is silently erased.
Invalid references or uncited references fail with HTTP 502 and an error code.

The internal understanding draft only selects up to three quotations. The server deduplicates
exact pairs, supplements missing input_message/ai_interpretation sources with their full text,
and renders [source] followed by the quote. The public overview is a string up to 32000 characters;
clients should support multiline text and consult understanding_evidence for structured use.
No source text is truncated. This is an extractive overview, not a generated interpretation.
For greetings and uninterpretable input, localized short replies remain available. Unknowns
remain unknown: an echo is not substituted for the short statement of uncertainty.

Interpretation remains in view.premises, premise_gaps, hypotheses when applicable, and unresolved.
Selected excerpts may omit nuance; the full input and submitted AI proposal remain in observations
and/or the overview fallback. Do not treat excerpt selection as semantic verification.
Effect quotes and overview excerpts preserve source language even for a different requested
response language. Other generated prose continues to use the requested language.

## Dify apps already imported

Before testing the new backend, replace the Python code in **Parse response** with
[parse_alignment_response.py](../examples/dify/parse_alignment_response.py).
Keep inputs body/status_code and outputs alignment_status/alignment_json unchanged.
The parser accepts 0.4.0 and 0.5.0 for a staged migration or backend rollback, and rejects
unexpected versions, status values, HTTP failures or execution authorization.
It checks the integration envelope, not every nested semantic claim or the entire OpenAPI schema.
No reimport, model change, URL change, timeout change or greeting classifier is required.
The distributed YAMLs include the new parser, but existing imported apps do not update automatically.

## Regression and verification record

Observed response 9fe8f19d-a4a0-4ae6-80fc-ef957e04b8fa (0.4.4) is represented by selected exact
excerpts in tests/fixtures/observed-0.4.4-excerpts.json, including "generated locally" and
"records should be generated". It is a failure fixture, not an expected model answer.
Contract tests exercise nullable/omitted effects, rejection of unsupported effects and free-form
summaries, exact cross-language quotations, uncited IDs, deduplication, fallback coverage,
long excerpts, unknown replies, and the HTTP provider path. Explicit generation in original
material must survive; words such as generate are not globally banned.

Run `python -m pytest -q`. These tests use mocked providers and demonstrate contract behavior,
not live model accuracy. Local Docker and operator model validation for 0.5.0 remain pending.
Start with examples/quality/offline.en.json on the same model, then offline.ja.json and
observed-plan.en.json with the fixed original proposal. Inspect all generated statements and
differences, not only status or the now-extractive understanding.

## Remaining limitations

Factual role classification, materiality, statement paraphrases, gaps and unknowns remain
model-dependent. Exact quotations prevent new wording only in effect and overview fields.
They do not prove entailment, relevance, completeness or truth. A provider error must not be
converted to mapped or unknown. Known errors are surfaced without retries or silent corrections.
The earlier communication failure is outside this change. No live quality improvement is claimed
until reviewed model responses establish it.
