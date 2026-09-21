# SANA Premise Alignment API — 0.5.15 prototype

0.5.15 makes correction feedback concrete with the affected reference IDs and
existing dependency forms. Validation, modes and deadlines are unchanged. One
normal-HTTP medium run recovered after one correction, and both Dify workflows
have operator-reported successful runs. See [release notes](docs/RELEASE-0.5.15.md),
[known limitations](docs/KNOWN-LIMITATIONS.md), and the
[development evidence archive](docs/validation/README.md), including failed runs.


0.5.14 adds low/medium/high processing allowances and bounded local traces for normal
API and Dify requests. All modes use the same validation. A passing result ends early;
more calls do not guarantee greater semantic accuracy. See [modes, traces and corrections](docs/PROCESSING-MODES.md)
and [the update and verification record](docs/QUALITY-0.5.14.md).


0.5.2 distinguishes explicit action requests from tentative proposals during extraction.
Both requests and stated concerns can anchor Care. See [the request classification update](docs/QUALITY-0.5.2.md).

Upgrading from 0.5.0? See [the Care boundary update](docs/QUALITY-0.5.1.md).
Care now selects original concern clauses; a reported state cannot become a newly worded
requirement in that field. Response schema remains 0.5.0; the 0.5 Dify parser is unchanged.

Upgrading from 0.4.x? Read [the 0.5 migration guide](docs/MIGRATION-0.5.md).
Effects may now be null; the overview uses attributed source excerpts. Existing Dify apps
need the updated Parse response code before using schema 0.5.0.

**Powered by [SANA OS](https://sana-os.org/)**

Surface the premises behind human input and an AI's proposed interpretation before execution.
The API returns **Fact / View / Care**, quoted evidence, uncertainties, and differences.
It carries no conversation state between inference requests; bounded local operational traces are retained by default. The caller retains responsibility for execution and its rules.

English is the default for documentation and generated responses. Inputs and outputs use UTF-8;
set `language` to request another response language. Evidence stays in its original language.

## Quick start

Requires Git and Docker with Linux containers (Docker Desktop on Windows/macOS or Docker Engine).

```bash
git clone https://github.com/sana-os/sana-alignment.git
cd sana-alignment
cp .env.example .env
```

In Windows PowerShell, replace the last command with:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally: set `LLM_BASE_URL`, `LLM_MODEL`, and, if your provider requires it, `LLM_API_KEY`.
The base URL ends in `/v1`; the service appends `/chat/completions`.
Use the exact model identifier returned by your provider. Keep credentials out of Git.
For a local server without authentication, set `LLM_API_KEY=` to an empty value.

```bash
docker compose up --build -d
```

Or build and run directly:

```bash
docker build -t sana-alignment:0.5.15 .
docker run --rm --name sana-alignment --env-file .env -p 127.0.0.1:8000:8000 sana-alignment:0.5.15
```

Open [interactive API documentation](http://localhost:8000/docs).
`GET /healthz` checks the process only; `provider_connectivity: not_checked` is intentional.
This repository builds the image locally; it does not assume a published container image exists.

## First request

```bash
curl --max-time 620 http://localhost:8000/v1/align -H "Content-Type: application/json" --data-binary @examples/align.en.json
```

PowerShell: use `curl.exe` and quote the file argument: `--data-binary "@examples/align.en.json"`.
If `SANA_API_TOKEN` is set, add `-H "Authorization: Bearer YOUR_SANA_TOKEN"`.
This token authenticates this API; it is separate from the model provider's API key.

```json
{
  "input_message": "Show customer information in next week's demo. Do not use real customer data.",
  "ai_interpretation": "Connect to the production customer database in read-only mode and display a list.",
  "language": "en"
}
```

Expected *semantic behavior*: identify the conflict with the explicit data boundary,
return `revision_required`, and avoid asking permission to disregard that boundary.
Do not assume anonymized real records satisfy it. This is an acceptance criterion,
not a claim that every model has passed it.

`ai_interpretation` is an explicitly supplied interpretation or proposal, not hidden chain-of-thought.
When supplied, the engine compares the submitted positions through `premise_gaps` and leaves
`view.hypotheses` empty. Genuine interpretation limits remain visible in `view.unresolved`.
When absent, the engine can report its own tentative interpretation hypotheses and leaves
`premise_gaps` empty. Neither mode authorizes inventing a replacement plan.
The service never performs the submitted task.

## Two-stage processing

1. **Extract** exact clauses with a provisional communicative function: state, request, concern,
   proposal, other, or unclear. This is narrower than full Fact/View/Care mapping.
   A quotation records what was said, not that it is true.
2. **Map** their roles and compare premises using the original request and extracted quotations.
   This stage selects evidence IDs; the server restores the exact source and quote in the response.

The extraction stage's `kind` is a hint, not a gate that can discard a supplied AI comparison,
context, or extracted statements. Whole-source references remain available to the mapping stage
so an extraction omission does not remove the original evidence. Care statements, however,
must select a clause explicitly labelled request or concern during extraction, with matching evidence.
Whole-source availability alone cannot supply a Care anchor. A missed or mislabelled concern
can therefore be omitted; extraction recall and classification require live evaluation.
The public API still returns
`source` and `quote`; the internal IDs are not a new client requirement.

Unknowns have a scope. Missing document contents can matter for executing a summary, while an
explicit external-transfer prohibition and a proposed upload already suffice for comparison.
That case should return `revision_required`, preserving the boundary in Care. It need not ask
for the document or a replacement method. See [the transfer example](examples/transfer.en.json).

Schema descriptions explain role boundaries; they are generation guidance, not enforced semantic
rules. Server validation checks structure, references, attribution and question constraints.
Scope and meaning still require evaluation with the chosen model.

## Languages and character encoding

| Setting or field | Contract |
| --- | --- |
| `language` omitted | Generate English prose (`en`), regardless of input language |
| `language: "ja"` | Generate Japanese prose |
| Other tags, e.g. `en-GB`, `pt-BR`, `zh-Hant`, `ar` | Request that language; substantive analysis depends on the model |
| JSON field names, status values, identifiers | Stable English machine-readable identifiers |
| `evidence[].quote`, `observations[].quote`, `care[].statement` | Exact source text, never translated |
| Character encoding | UTF-8 throughout; no additional character-set packs required |

The tag validator accepts common language/script/region forms and normalizes their casing.
It does not implement the full BCP 47 registry or extension syntax. Tags are not automatically
inferred from input. A tag can be syntactically accepted without being supported by the model.

Fixed short replies support English, Japanese, Spanish, French, German, Portuguese,
Simplified/Traditional Chinese, and Arabic. Other short-reply languages fall back to English.
`meta.requested_language`, `meta.short_reply_language`, and `meta.language_fallback` report this.
For substantive model output, `short_reply_language` is null; `language_fallback=false`
is **not** certification of the model's language compliance. That behavior needs live evaluation.
Regional variants use the primary-language template. Chinese script takes precedence over region.
Translations have not undergone independent native-speaker review.

## Fact / View / Care

| Field | Meaning |
| --- | --- |
| `observations` | Received text and exact supporting quotations with source IDs |
| `fact` | Factual claims in the task, not independently verified truths |
| `view.premises` | Interpretations, evaluations, and framings in submitted material |
| `view.understanding` | Source-labelled original excerpts, or a localized short reply; see `meta.understanding_mode` |
| `view.hypotheses` | Engine interpretation hypotheses when no AI proposal was supplied; empty in comparison mode |
| `view.premise_gaps` | Differences between human input and the supplied AI interpretation |
| `view.unresolved` | Local unknowns, each with `alignment` or `execution` scope and an optional question |
| `view.unknowns`, `view.questions` | Derived from alignment-scope unresolved items; at most one distinct focused question |
| `care` | Stated interests, priorities, boundaries, and desired outcomes; null if unknown |
| `acknowledgment` | Short social response, separate from Care |

A request or prohibition belongs in Care; the fact that it was uttered is recorded in observations.
Fact may be empty. Do not infer a privacy, legal, emotional, or other motive simply from a boundary.
These are model instructions; schema validation cannot prove semantic classification is correct.

Premises carry `source`, `status`, `support_state`, `materiality`, and `evidence`.
Care reports `execution_effect: null` (not assessed); the model does not generate this field
for Care. Its `statement` is an exact extracted concern clause in its original language.
The mapping stage cannot paraphrase it into a new obligation or add a motive. This checks
provenance and wording, not whether the extractor's function label is semantically correct.
Effects on proposed execution and conflicts
belong in View. Fact/View premise effects default to null; non-null values are exact evidence
quotes in their source language. They are not new predictions. A negative constraint does not authorize
a replacement method. Explicitly requested alternatives remain preserved as stated requirements.
`externally_verified` is always false. Care uses `support_state: "not_applicable"` because a value
is not a factual claim requiring proof. Source IDs are `input_message`, `ai_interpretation`, and
`context.N`. Exact quote matching checks provenance, not logical support or truth.

For Fact/View, `support_state` assesses the statement at its stated scope within
submitted material. `provided` means that material supplies a basis; `unsupported`
means the assertion exceeds that basis; `disputed` requires an explicit contest in
the material; `unknown` leaves support undetermined; `not_applicable` represents a
goal/value/requirement rather than a factual assessment. A supported report that a
plan assumes a capability does not establish the capability itself. AI origin or
`externally_verified: false` alone does not imply `unsupported`. These are model
judgments, not semantic guarantees enforced by exact quote matching.

## Status and downstream workflows

| Status | Meaning |
| --- | --- |
| `handshake` | Pure greeting or acknowledgment, without analysis |
| `unknown` | Meaning cannot be interpreted from supplied material; Care is null |
| `context_insufficient` | No useful task premise or referent can be identified; not merely a missing execution input |
| `revision_required` | A supplied AI interpretation is classified as conflicting with an explicit constraint |
| `needs_clarification` | A material alignment premise remains unresolved; known parts are preserved |
| `mapped` | This output identifies no material unresolved alignment issue; later execution inputs may still be missing |
| `mapped_with_divergence` | Differences remain visible but are classified as nonblocking |

`premise_gaps[].kind` distinguishes `constraint_conflict`, `interpretation_difference`, and
`missing_premise`. Known conflicts require `blocks_execution=true` and `verification_question=null`.
Other gaps and hypotheses can also have a null question. No question is needed just to populate a field.
A genuinely unclear constraint scope can still require clarification.
Every gap needs a stated premise on at least one side. An unspecified implementation method on
both sides is not a comparison. A genuine one-sided gap remains valid; if neither side supplies a
needed alignment variable, record it in `view.unresolved` instead. Do not invent a counterpart.

`view.unresolved[].scope` separates information needed to interpret or compare premises (`alignment`)
from later implementation inputs (`execution`). Execution-only items require `question: null` and
do not cause `needs_clarification`. Known conflicts take status precedence, while any separate genuine
alignment unknown remains visible. A local uncertainty must not erase known goals or constraints.

`blocks_execution` is an advisory premise signal, not an enforced veto.
`meta.execution_authorized` is always false: this service never grants execution authority.
It does not mandate human approval for every task either. The Executor follows its own rules.
Preserve the original request alongside these annotations; never treat HTTP 200 alone as clearance.

Import [the English Dify workflow](examples/dify/sana-alignment.en.yml) and follow the
[Dify setup guide](docs/DIFY.md) for a runnable integration example based on the operator's export.
The operator confirmed import, greeting and an English substantive run in the tested installation;
see the validation record for the exact input variation and remaining quality limits.

For Dify, use an HTTP Request node and branch on the JSON `status`. Known conflicts can be routed
back to a plan-revision step; unresolved premises can be handled according to workflow rules.
First verify the API's behavior independently. Container networking must then be configured so
Dify's request/proxy path can reach it: `localhost` inside Dify is not this service, and the default
Compose binding exposes port 8000 only on the host's loopback interface.

## Context and optional framework lenses

`context` is an optional oldest-to-newest list:

```json
{
  "speaker": "human",
  "text": "I do not know the deadline yet.",
  "representation": "verbatim",
  "response_status": "unknown",
  "omitted_information": null
}
```

`speaker`: `human|ai|source`. `representation`: `verbatim|summary|unknown`.
`response_status`: `answered|unknown|context_dependent|not_applicable|declined`, or null.
These metadata are caller declarations, not authenticity guarantees. Previous AI hypotheses do not
become human agreement. Summaries must not be treated as full primary evidence.
There is no stored session; resubmit relevant context and scoped corrections when continuing.

`frameworks` omitted or `[]` loads no additional detailed lens. The SANA Core is always present,
including Integrated Knowledge. Use `"auto"` to request conservative selection of at most one lens;
legacy explicit `null` also selects this mode. An explicit list can contain up to three lenses:
`RBM`, `GMM`, `CPM`, `RSM`, `Legitimacy_Layer`, `History_Analysis`, `Value_Formation`.
Lenses organize provisional interpretations; they are not calibrated numeric diagnostic tools.

## Provider compatibility and errors

The provider must implement `/chat/completions`, `messages`, and `choices[0].message.content`.
Set `LLM_JSON_MODE=false` if it does not support `response_format: {"type":"json_object"}`;
response schema validation still applies. Extraction followed by mapping normally uses two LLM calls.
Deterministic standalone greetings use none; an extraction-only short route uses one.
`meta.stages_completed` reports `[]`, `["extraction"]`, or `["extraction", "mapping"]` on success.
Since 0.5.12, `SANA_MAPPING_RETRIES=1` (default) allows one additional mapping call
after an output-contract failure. Accepted extraction and original sources are reused;
the complete regenerated mapping must pass the same validation. No target status is
requested. Set `SANA_MAPPING_RETRIES=0` to disable it. Extraction failures, transport
errors, rate limits, refusals, incomplete responses and timeouts are not retried.
Staging or regeneration does not itself guarantee lower latency or better accuracy.
The model must accommodate the Core, selected lenses, request, and output schema.

For a model server on another computer, use that computer's reachable address in `LLM_BASE_URL`.
For a server on the Docker Desktop host, `host.docker.internal` is the host name provided by Docker.
A container's `localhost` refers to the container itself.
`LLM_TIMEOUT_SECONDS` accepts 1–300 per model call; the total request budget is twice that plus five seconds.
This total budget is unchanged by retries: at most three model calls share it. A retry
may be cancelled when that budget expires. API response schema_version remains 0.5.0;
per-attempt errors, durations and candidate reviews are available in diagnostic v11,
not added to the public response. See [0.5.12 verification notes](docs/QUALITY-0.5.12.md).
In 0.5.13, goal-meaning, constraint-scope and comparison-assumption dependencies
must target an affected premise, not an extracted open topic alone. Genuine
authority and referent unknowns remain possible alignment issues. See
[0.5.13 routing checks and limits](docs/QUALITY-0.5.13.md).

| HTTP code | Meaning |
| --- | --- |
| 401 | This API's token is missing or invalid |
| 413 / 422 | Request size or schema is invalid |
| 502 | Invalid provider output, evidence/attribution contract failure, or upstream HTTP error |
| 503 | Provider unreachable or rate limited |
| 504 | Provider or total alignment timeout |

Errors return a `detail.code`. Attribution failures also include `detail.issue.path` and
`detail.issue.rule`, identifying the failing output field and rule without returning submitted text. Multiple distinct questions, excessive automatic lenses, or an
inconsistent constraint-conflict record are rejected, not silently rewritten into a successful map.
A model-generated Care execution_effect, including null, returns `provider_unexpected_care_effect`.
The server supplies the public null field only after validating a draft that omits it.
Unknown or malformed mapping evidence IDs return `provider_invalid_evidence_reference`;
a question attached to an execution-only unresolved item returns `provider_execution_question`.
Extraction quotes still undergo exact substring validation and can return `provider_ungrounded_evidence`.
`provider_empty_premise_gap` rejects gaps where both positions are null or blank, with a content-free
field path/rule. It does not establish whether nonempty positions or their difference are meaningful.
`provider_unexpected_comparison_hypothesis` rejects a nonempty `view.hypotheses` when an AI proposal
was supplied. The model-visible schema also sets `maxItems: 0` for that request. Comparison
uncertainties belong in gaps or unresolved items, not a third proposed plan. This structural check
does not detect arbitrary invented content in other fields; all prose still needs live evaluation.
Version 0.5.0 uses response `schema_version: "0.5.0"` and the v0.5 profile; see [migration details](docs/MIGRATION-0.5.md) for nullable quoted effects and extractive overviews.
A connection failure never becomes a semantic `unknown` response.

## Development and release status

Python 3.12:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.lock
python -m pytest -q
```

See [validation](docs/VALIDATION.md), [live acceptance cases](docs/ACCEPTANCE.md),
[design](docs/DESIGN.md), and [migration from 0.3.0](docs/MIGRATION-0.4.md).
Tests with mocked providers verify contracts, not the chosen model's understanding.
The GitHub Actions workflow includes a Docker smoke test; a configured workflow is not evidence
that current GitHub CI has passed. Version 0.5.15 remains a prototype with bounded
live evidence; see the release notes for the precise verification scope.

There is no external fact lookup, RAG, downstream execution, persistent learning, or calibrated Δv.
Metadata tracing is enabled by default; opt-in detail tracing can retain submitted
content and generated candidates locally. API keys are excluded from these traces.
Your provider receives submitted content. See the processing-mode guide for retention.
The bundled configuration is for local use. Public service operation needs its own authentication,
TLS, quotas, and deployment controls.

## Sources and attribution

- [SANA OS source](https://github.com/sana-os/sana-os)
- [LLM Ambiguity Lab v2](https://sana-os.org/llm-ambiguity-lab/)
- [LLM Ambiguity Lab v1](https://deshimarusakaguchi.com/llm-ambiguity-lab/)
- [Preference Compass](https://preferencecompass.info/en/#q=1)

`knowledge/` retains the supplied source wording, including Core Principle. Git can normalize
CRLF line endings to LF; manifests retain original-byte SHA-256 values and separate `lf_sha256`
values for cross-platform content checks. No substantive source text was rewritten.
Five supplied papers are included in `references/` as design background, not as runtime prompts
or proven guarantees. Preference Compass informs handling of uncertainty and continuing context;
no questionnaire or personality scoring is included.

This is a derivative workflow profile, not full Core Specification compliance.
Original source terms are in [SANA OS License v1.0](knowledge/LICENSE.md).
A license for the newly written application code still needs the owner's selection;
this repository does not implicitly grant an MIT or other license for it.
