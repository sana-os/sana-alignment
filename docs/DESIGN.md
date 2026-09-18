# Design — workflow-premise-map-v0.4

## Goal and boundaries

This derivative implements a stateless premise-mapping API between input and execution.
It preserves the SANA Constitution and follows the task-role distinctions from LLM Ambiguity Lab v2.
The external contract is a new workflow profile, not Core Specification v1.0 compliance.

Flow:

1. Validate request size, field names, and API token when configured.
2. Exact standalone greetings → deterministic handshake response (zero LLM calls).
3. Extraction LLM → exact clauses and a tentative kind; select optional lenses. No Fact/View/Care classification here.
4. Validate those source quotations. If any clause, context, or AI proposal is available, continue to mapping regardless of the kind hint. A substantive hint also continues. Otherwise use a short response.
5. Mapping LLM → classify/compare using original text plus extracted clauses; cite registered evidence IDs and give unknowns an alignment/execution scope.
6. Resolve evidence IDs to exact quotations; validate structure, attribution, Care support-state, question scope/count and conflict-record consistency.
7. Derive status in code and return Fact/View/Care, observations, local unknowns, provenance, and completed stages.
8. Caller preserves differences and decides what happens next outside this service.

A greeting followed by a task is not short-circuited. Context or an AI interpretation disables the local greeting shortcut.
Meaningless/uninterpretable input is not classified by ASCII, script, or keyword heuristics.
Non-whitelisted greetings and unknown input require an available LLM; outages are HTTP errors, never semantic judgments.
Kind hints, extracted coverage, materiality and unknown scope remain model judgments. The code cannot prove their semantic correctness.

## Loading and source control

System reference order is Core_Principle → Integrated_Knowledge → Communication_Layer.
Selected lenses follow the Core. The workflow adapter and output-language contract follow all references, so the task-specific output rules remain explicit.
Core_Specification is developer reference, not part of the LLM prompt.
No original Principle or framework wording is rewritten. Git normalized some CRLF line endings to LF during the initial Windows upload. Manifests retain original-byte `sha256` and separate CRLF-to-LF `lf_sha256` values; tests check the latter so line endings do not masquerade as substantive edits. `.gitattributes` makes LF the checkout convention.
The two Communication Layer attachments were byte-identical.
Core README and Framework README receive distinct filenames to avoid collision.

The adapter makes uncertain causal explanations hypotheses and preserves provenance. It does not
convert the frameworks' general causal claims or unresolved citation markers into independently verified facts.
The final prompt includes a schema as generation guidance. The server checks structure after generation;
JSON-object mode does not itself impose schema-constrained decoding. Descriptions annotate the roles,
not executable semantic rules or a definition of the user's values.

## Differences from Core Specification v1.0

| Original concept | This implementation | Reason |
| --- | --- | --- |
| AUTH → PREMISE → ANALYSIS_GATE → RESPONSE | Stateless extraction and mapping | Workflow insertion is the requested first target |
| Session Δv, EWMA update, thresholds | `delta_v=null` | No calibrated observation-to-signal estimator was supplied |
| Handshake accumulator >=0.6 | ACK for pure greetings | No artificial repeated greetings required by a stateless API |
| Exposure 0/1/2 | Fixed machine-readable schema; tentative content | Serialization visibility is separated from diagnostic depth |
| Premises confirmed before deep analysis | No deep/definitive diagnosis | Lenses help formulate questions and provisional premise maps |
| RBM invoked after alignment | Provisional lens use only, before confirmation | Deliberate profile difference; no RBM quantitative diagnosis is claimed |
| Technical output includes `llm_prompt` | Fact/View/Care JSON | Intended for downstream workflow consumers |
| Intent: honest/misunderstanding/malice | handshake/unclear/context_insufficient/substantive | Do not classify hidden hostile motives from wording |
| GentleRadical TriggerFlow | Reference instructions in prompt; no stateful OneShot engine | Full dialogue safety state machine is outside this version |
| Learning feedback | Caller resubmits context | No cross-session profiling, training or persistent memory |
| Framework numeric variables | Not calculated | Required observations/units not defined for general text |

Original sections also contain competing exposure threshold descriptions (analysis eligibility ≤0.55,
explicit exposure ≤0.45, workflow default exposure 2). No silent resolution is claimed.
Time Layer is referenced in the materials but its standalone definition was not supplied.
It is therefore not an independently selectable framework. CPM metadata is present within CPM.md.

## v1 and v2 relationship

The two public Labs are educational simulators. This API uses their concepts, not their
preset results or heuristic confidence scores. It is not a reimplementation of the complete DCRL loop.
Extraction preserves explicit information; mapping separates premise interpretation from readiness to execute.

Fact is a factual *claim*, not verified truth. Observations record exact received text separately.
Care maps protected interests/values and does not require factual proof.
Different interpretations can remain. `mapped_with_divergence` is not consensus.
Minor assumptions may be disclosed without asking the user to confirm everything.
Alignment-scope unknowns, blocking hypotheses/gaps, or broad interpretation limits cause `needs_clarification` when some premises remain mapped. With no known portions, broad limits can instead yield `unknown` or `context_insufficient`. A known blocking `constraint_conflict` takes precedence and yields `revision_required`; separate unresolved items remain in the response. Execution-only unknowns do not block alignment. Nonblocking per-entry questions may remain optional. A request or prohibition is placed in Care; observations record the fact that it was said.
A model can still miss an ambiguity; mapping does not confer authorization.

## Evidence and trust

Source IDs are `input_message`, `ai_interpretation`, and `context.N`.
Extraction evidence must be a nonblank exact substring of that source, not a generated paraphrase.
The server registers whole-source text and validated extracted clauses with request-local IDs.
Mapping selects these IDs rather than rewriting quotations. A whole-source entry provides an anchor
when extraction missed a clause; the original request remains present. Unknown IDs, extra reference
properties, or direct quotations in the mapping protocol are rejected. Public evidence still has
the same `source`/`quote` shape after deterministic resolution; no fuzzy quote repair occurs.
This verifies quotation provenance, NOT logical entailment or external truth.
`user_explicit` cannot cite AI/source messages, and inferred premises cannot be marked explicit.
Other attribution and materiality judgments still require evaluation with the chosen model.

Input/context is serialized as a user data object. System instructions forbid treating it as control.
There is no tool dispatcher, code executor, URL fetcher, or command execution based on input.
These measures reduce control confusion; semantic prompt-injection resistance is not proven by schema tests.
Provider refusal, invalid JSON, truncated output, ungrounded evidence and request errors return non-2xx responses.
No fallback fabricates a successful premise map. No automatic retry consumes additional tokens silently.

## Operations

POST /v1/align, GET /healthz, GET /docs, GET /openapi.json.
Request body cap 128 KiB; text fields max 6,000 characters; max 12 context entries;
combined JSON max 24,000 characters; each upstream response body capped at 1 MB; at most 4 active alignment requests per worker.
A total request timeout includes semaphore wait; provider has network timeouts.
Provider URL and credentials are configured by the operator, not supplied per request.
Redirect following is disabled; API key is excluded from model messages.
Model is selected via environment. Settings require Python 3.12 and a configured model ID.
No DB, chat storage, request content logging or external retrieval. Uvicorn access log is disabled.

Authentication is optional for localhost development; the bundled compose file binds host localhost.
The service is a prototype, not a hardened public multi-tenant service.
A public deployment needs its own ingress/TLS, authentication, quotas, and operational review.
The provider receives submitted input/context and its retention rules apply.

## Acceptance status

Automated mocked-provider tests verify contracts and controls, not LLM understanding.
Docker is specified but could not be executed in the authoring environment (no Docker executable).
The operator demonstrated Docker startup and real llama.cpp inference for 0.1. That run exposed semantic issues motivating 0.2; it does not validate the revised version. See VALIDATION.md for version-specific evidence. No API secrets were requested in chat.
Tests must be supplemented with representative user tasks before declaring a release candidate.

## References

- https://github.com/sana-os/sana-os — source architecture and attribution
- https://sana-os.org/llm-ambiguity-lab/ — premise roles, provenance, divergence
- https://deshimarusakaguchi.com/llm-ambiguity-lab/ — operational ambiguity and missing references
- https://fastapi.tiangolo.com/deployment/docker/ — container deployment
- https://www.python-httpx.org/async/ — asynchronous provider requests
- https://www.python-httpx.org/advanced/timeouts/ — provider timeout behavior


## Additional papers and continuing context

Five supplied papers are retained in references/, separately from runtime knowledge; wording is unchanged and original/canonical hashes are recorded.
Their claims are design arguments, not experimentally established guarantees for this software.

| Reference | Requirement applied | Limit |
| --- | --- | --- |
| Triangle of Intelligence, 6.2–6.3 | Observe evidence/limits; critique the engine's own assumptions; calculate a usable structural account | Observation is submitted-text only; semantic critique is model-dependent |
| Instability of Justice, 6.1–6.3 | Surface premises as a process goal; do not optimize for consensus, comfort or compliance with a preferred view | No claim of value-free neutrality or elimination of factual errors |
| Separating Interpreter from Executor, 4.2–4.4 | This API is Interpreter; callers own rules, authorization and execution | A separated component can still be ineffective; rule quality is a separate responsibility |

Fact/View/Care are output categories. Observation/critique/calculation are processing functions.
They are not one-to-one: critique can apply to each output category.
The current mapping prompt and validators implement part of these requirements; they do not
prove philosophical competence or immunity to the described failure modes.

The Interpreter returns an annotated case, not a binding decision. The `blocks_execution` name
means a premise is judged material enough to require clarification; it is an advisory signal,
not an enforced veto or grant of permission. The caller determines how its own rules use it.
`execution_authorized=false` means this service never grants execution authority.
This also does not imply a human approval dialog is mandatory for every downstream task.
A separately specified Executor can operate automatically under its own rules.
Model-provider constraints remain applicable; this separation does not bypass them.

The original request must remain available alongside annotations. Do not replace it silently
with a rewritten prompt. Monitor case-level interpretation failures and evaluate them periodically;
a JSON-returning service that does not materially observe the input can become the paper's
Phantom Observer. No performance/robustness guarantee is claimed by merely separating processes.

Preference Compass was reviewed via its public HTML. Its unknown/context-dependent/not-applicable/
declined answers and separation of hypotheses from confirmed agreements inform optional context
metadata and continuing-context instructions. No questionnaire, trait scoring, relationship storage
or complete Relationship Portability Sheet importer was added.

Context entries are oldest to newest. Callers may label representation (verbatim/summary/unknown),
response_status and omitted_information. These are declarations, not authenticity guarantees.
Old AI interpretations are not human agreement. Explicit scoped corrections should update the
interpretation; unresolved differences remain visible. Unknown/declined answers should not cause
recursive persuasion. Live-model tests must verify these prompt-level behaviors.
The deterministic unknown branch remains a generic clarification response, not a full dialogue manager.

Source: https://preferencecompass.info/en/#q=1 and the supplied papers in references/.


Cognitive Compression and Infrahumanization, Section 6, further motivates distinguishing a
compressed proxy from the full case without requiring all compression to be reversed.
Unknown discarded information must remain unknown. This service can expose possible missing
premises and declared summary loss; it cannot measure a human's actual cognitive compression
or recover facts never supplied. The presence of a short instruction is not proof of cognitive failure.
Reintroduction of context is selective and task-dependent; the goal is not maximum questioning.


## English default and multilingual output

All API identifiers remain English; UTF-8 handles text in any script without character-set packs.
`language` defaults to `en` and accepts a documented subset of language-tag syntax.
The requested language is present in both stage payloads. Extraction returns source quotations
without translation. The mapping stage receives the generated-prose language rule, while evidence
is selected by ID and restored verbatim. This is not a language detector or proof of compliance.

Short routes use `app/i18n.py` templates and report their actual template language and fallback.
Unsupported short-reply languages fall back to English. Substantive output relies on the model;
its metadata does not certify language compliance. No automatic translation rewrites evidence.

Detailed lenses are off by default, while the Core (including Integrated Knowledge) remains loaded.
Automatic selection is opt-in (`auto` or legacy explicit null), limited to one justified lens.
A deadline alone does not establish resource overload, nor does a rule establish a legitimacy crisis.
Explicit callers may select up to three lenses. Excess automatic selection is a provider error.

## Explicit constraints and question scope

A known conflict with a clear human boundary calls for revising the supplied AI interpretation,
not for asking the human to restate or waive that boundary. Known conflicts have
`kind=constraint_conflict`, `blocks_execution=true`, and `verification_question=null`.
The code rejects inconsistent combinations; it cannot prove that the model chose the correct kind.
Genuinely ambiguous scope belongs to `missing_premise` and can warrant a focused question.

At most one distinct question is allowed across View and per-entry fields. Identical strings may
be repeated as references. The server rejects excess questions rather than silently dropping them.
It does not infer semantic equivalence between differently worded questions. All these contracts
are in the model's instructions; the per-entry schema also allows null to avoid forced questions.
No automatic repair call or fallback changes an invalid output into a successful result.

## The Shadow of the Future

The added paper's conditional argument motivates examining an operative time horizon and the
loss of future options when those premises materially affect the submitted task. The prompt asks
for such differences only where supported, without assuming future preferences cannot change.
It adds no reward function, self-preservation objective, cooperation optimizer, or new mandatory lens.

The paper does not establish that the configured model has a stable long horizon, or provide an
external verification procedure for that property. This adapter therefore claims only a limited
design implication, not a proof of cooperation, rational agency, alignment, or safety.


## 0.2.1 Care schema correction

Care has a dedicated schema with required `support_state: const not_applicable`, shared by
model drafts and API responses. Explicit source attribution is still represented by `source`,
`status`, and `evidence`; it does not turn a preference or boundary into a factual proof claim.
Fact/View retain the broader support-state enum. Invalid Care still returns the existing error
code rather than being rewritten. JSON-object mode does not impose schema-constrained decoding,
so model adherence remains subject to live evaluation. The response schema version stays 0.2.0.


## 0.2.2 Attribution diagnostics and semantic regression

The model-visible schema now includes conditional rules matching the engine's existing attribution
checks: `user_explicit` requires explicit status and human evidence; `user_implied` and
`agent_inference` cannot have explicit status. Human evidence source IDs are derived per request
from input_message and context entries declared human. This is not a verification of identity.
These conditions supplement the prompt; JSON-object mode does not enforce conditional decoding.

The engine retains its checks. Attribution errors return a static rule identifier and field path
under `detail.issue`, without returning the generated text, input, credentials, or full prompt.
Other errors retain their existing shape. No automatic rewriting or repair call is introduced.

Role-specific field descriptions and an illustrative workshop example distinguish factual claims
from goals/boundaries, task effects from invented justifications, and premise questions from later
implementation detail. These are model guidance, not semantic guarantees. In particular, no code
keyword filter can establish whether a real request does or does not provide a legal rationale.


## 0.3.0 Care generation boundary (supersedes the 0.2 Care shape)

The model-facing CareDraft includes the concern, attribution, materiality, and evidence, with
support_state fixed to not_applicable. It has no execution_effect property and forbids extras.
The API-facing CarePremise adds execution_effect=null to explicitly report that no separate
Care effect was assessed. A draft containing that field is rejected, even if its value is null;
unsupported content is never silently removed from a generated answer to pass validation.

This reduces a redundant generation task that repeatedly introduced implementation suggestions.
It does not prove semantic grounding: invented permission can still appear in another text field,
and all fields need live review. A stated alternative stays in Care.statement when supported by
human input. Material differences in the proposed execution stay in View. Core text is unchanged.
The response schema and profile advance to 0.3 because consumers must accept null Care effects.

## 0.4.0 Extraction and scoped uncertainty

The former intake classifier is now an extraction stage. It preserves explicit clauses before
Fact/View/Care classification, reducing the number of different judgments requested in one call.
The call count remains at most two; neither lower latency nor improved model accuracy is assumed.
The mapping stage receives both original material and extracted statements. A tentative
context_insufficient label cannot suppress a supplied AI comparison or extracted constraint.

The internal Draft has a required kind and `view.unresolved`. Each unresolved item has a statement,
scope, optional evidence, and nullable question. Absent information cannot itself be quoted.
An execution-scope question is a provider error, not text silently removed to pass validation.
At most one distinct question is allowed across alignment items, gaps and hypotheses. Outer
whitespace is ignored for counting/deduplicating questions; the unresolved items remain intact.
The public `view.unknowns` and `view.questions` are derived from alignment-scope items. Short
responses use the same representation. Gaps/hypotheses retain their own nullable question fields.

For the transfer regression, a missing document body is an execution input. The external-transfer
prohibition can already be compared with a supplied upload proposal. Expected output preserves
the Care boundary and reports a conflict without asking for the body or a new delivery method.
A separate genuinely ambiguous boundary scope can still coexist with that known conflict.
Scope selection is a model judgment; these controls do not guarantee it is always correct.

Completion means the relevant premise differences have been surfaced. It does not mean all
implementation requirements have been collected, the parties agree, or execution is authorized.
All generated fields need review for invented replacements or rationales, including unresolved
statements and questions. A negative constraint does not supply its own positive alternative.

The response schema and application are 0.4.0; the profile is workflow-premise-map-v0.4.
`meta.stages_completed` distinguishes local handshake, extraction-only and extraction-plus-mapping.
See MIGRATION-0.4.md for client changes and ACCEPTANCE.md for live-model checks.

## 0.4.1 Attribution guidance and empty-comparison guard

The operator's English transfer and demo responses met the targeted checks in single runs. A
Japanese demo response found the real conflict but also attached an AI-only list-screen choice
to a human goal, and added an execution requirement as a missing-premise gap with both sides null.

The prompt now distinguishes material alignment issues from later implementation inputs in the
blocking rule itself. It applies this distinction across gaps, hypotheses and unresolved items.
Plain goals stay in Care; an AI implementation must not be attached to them through View effects.
Human evaluations can still be View, and explicitly requested implementations remain valid Care.
These role and meaning requirements are model guidance, not deterministic semantic checks.

The model-visible gap schema requires at least one nonblank stated position via anyOf. The engine
enforces the same condition with provider_empty_premise_gap, including a static field path/rule.
Both-null gaps are rejected, not silently deleted or rewritten into successful responses. Real
one-sided comparisons remain valid; alignment variables absent from both sides use unresolved.
This guard cannot prove that a nonempty position is supported. It does not detect arbitrary
invented alternatives or cross-source meaning contamination; live review is still required.

The application/image is 0.4.1. Public response fields, schema_version 0.4.0 and profile v0.4 remain
unchanged. No retry, keyword filter, extra model call, or source-document change is introduced.

## 0.4.2 Supplied comparison and engine hypotheses

The operator's later 0.4.1 Dify form run correctly identified the demo's production-data conflict,
but also prescribed synthetic or anonymized replacement data in a blocking engine hypothesis.
Its source quotation was exact. Quote provenance alone does not establish that the prescription
follows from the request; a correct status did not make the whole result acceptable.

The mapping contract now separates two modes. With a supplied ai_interpretation, compare the two
submitted positions in premise_gaps and keep genuine interpretation limits in unresolved. In this
mode view.hypotheses must be empty. Without a supplied AI proposal, engine interpretation hypotheses
remain available; they are tentative readings of the request, not instructions to adopt new plans.
One-sided gaps, nonblocking differences, and a local unknown alongside a known conflict remain valid.

The request-specific model-visible MappingView schema sets hypotheses.maxItems to zero only for
comparison mode. The engine rejects a violation with provider_unexpected_comparison_hypothesis and
a content-free path/rule diagnostic. It does not silently remove the item or retry generation.
JSON-object mode is not schema-constrained decoding, so the runtime rejection remains necessary.

This prevents a third plan being emitted in the comparison-mode hypothesis field; it cannot prove
that gaps, unresolved items, understanding or other prose are semantically supported. Moving the
same invented alternative to another field is still a failure. No keyword filter is used.
Application/image 0.4.2 retains public response schema_version 0.4.0 and profile v0.4. Existing Dify
response parsing remains compatible. Core wording and the number of model calls are unchanged.
