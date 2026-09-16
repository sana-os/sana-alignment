# Design — workflow-premise-map-v0.1

## Goal and boundaries

This derivative implements a stateless premise-mapping API between input and execution.
It preserves the SANA Constitution and follows the task-role distinctions from LLM Ambiguity Lab v2.
The external contract is a new workflow profile, not Core Specification v1.0 compliance.

Flow:

1. Validate request size, field names, and API token when configured.
2. Exact standalone greetings → deterministic handshake response (zero LLM calls).
3. Intake LLM → handshake / unclear / context_insufficient / substantive; select optional lenses.
4. Only substantive inputs → mapping LLM with selected full framework references.
5. Validate JSON, evidence substrings, attribution constraints and Care support-state.
6. Derive status in code and return Fact/View/Care, observations, provenance, and metadata.
7. Caller preserves differences and decides what happens next outside this service.

A greeting followed by a task is not short-circuited. Context or an AI interpretation disables the local greeting shortcut.
Meaningless/uninterpretable input is not classified by ASCII, script, or keyword heuristics.
Non-whitelisted greetings and unknown input require an available LLM; outages are HTTP errors, never semantic judgments.
The intake kind and materiality remain model judgments. The code cannot prove their semantic correctness.

## Loading and source control

System reference order is Core_Principle → Integrated_Knowledge → Communication_Layer.
The workflow adapter follows these references. The selected lenses follow the adapter.
Core_Specification is developer reference, not part of the LLM prompt.
No original Principle text is rewritten. Framework original bytes are retained.
The two Communication Layer attachments were byte-identical.
Core README and Framework README receive distinct filenames to avoid collision.

The adapter makes uncertain causal explanations hypotheses and preserves provenance. It does not
convert the frameworks' general causal claims or unresolved citation markers into independently verified facts.
The final prompt's schema controls serialization, not the user's values.

## Differences from Core Specification v1.0

| Original concept | This implementation | Reason |
| --- | --- | --- |
| AUTH → PREMISE → ANALYSIS_GATE → RESPONSE | Stateless intake and mapping | Workflow insertion is the requested first target |
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
Intake identifies gross missing task context; more detailed operational resolution can be upstream.

Fact is a factual *claim*, not verified truth. Observations record exact received text separately.
Care maps protected interests/values and does not require factual proof.
Different interpretations can remain. `mapped_with_divergence` is not consensus.
Minor assumptions may be disclosed without asking the user to confirm everything.
Only a material blocking hypothesis/gap or unresolved question causes `needs_clarification`.
A model can still miss an ambiguity; mapping does not confer authorization.

## Evidence and trust

Source IDs are `input_message`, `ai_interpretation`, and `context.N`.
Evidence must be a nonblank exact substring of that source, not a generated paraphrase.
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
combined JSON max 24,000 characters; response body cap 1 MB; at most 4 active alignment requests per worker.
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
External model inference is pending operator-supplied configuration. No API secrets were requested in chat.
Tests must be supplemented with representative user tasks before declaring a release candidate.

## References

- https://github.com/sana-os/sana-os — source architecture and attribution
- https://sana-os.org/llm-ambiguity-lab/ — premise roles, provenance, divergence
- https://deshimarusakaguchi.com/llm-ambiguity-lab/ — operational ambiguity and missing references
- https://fastapi.tiangolo.com/deployment/docker/ — container deployment
- https://www.python-httpx.org/async/ — asynchronous provider requests
- https://www.python-httpx.org/advanced/timeouts/ — provider timeout behavior


## Additional papers and continuing context

Four supplied papers are retained unchanged in references/, separately from runtime knowledge.
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

Source: https://preferencecompass.info/en/#q=1 and the four supplied papers in references/.


Cognitive Compression and Infrahumanization, Section 6, further motivates distinguishing a
compressed proxy from the full case without requiring all compression to be reversed.
Unknown discarded information must remain unknown. This service can expose possible missing
premises and declared summary loss; it cannot measure a human's actual cognitive compression
or recover facts never supplied. The presence of a short instruction is not proof of cognitive failure.
Reintroduction of context is selective and task-dependent; the goal is not maximum questioning.
