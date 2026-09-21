# Validation record — historical checkpoints

For current 0.5.15 publication evidence, including retained failures, see the
[development evidence archive](validation/README.md) and [release notes](RELEASE-0.5.15.md).
The checkpoint-specific statements below retain their historical scope; a pending
case here may have a later observation in that archive.

## English Dify import and operator runs

The operator imported `examples/dify/sana-alignment.en.yml` as a new app and supplied these results:

| Request ID | Submitted case | Observed result |
| --- | --- | --- |
| `fa2fc5d5-0741-49ba-a432-41fc1b3d9a7b` | `Hello`, English | `handshake`, acknowledgment `Hello.`, Care null, no model stages |
| `038e395b-203f-4481-8ad6-68803cb3152f` | Offline demo PC / fictional customer data, with a retained `Hello` prefix and trailing newline | `mapped`, extraction and mapping completed, English prose, reported PC state in Fact, stated goal and real-data boundary in Care |

The second run's submitted text was exactly:

```json
"HelloThe demo PC is not connected to the internet. Display entirely fictional customer information in the demo. Do not use real customer data.\n"
```

The AI proposal matched the distributed example. The received text and the evidence retained
`HelloThe...`; the response was not short-circuited as a greeting. Hypotheses, gaps, unresolved items
and questions were empty. The Fact execution_effect stayed within the stated lack of internet
connectivity, rather than claiming inability to access every external service. No execution
authority was granted. This is one observed result, not proof that prior scope or role errors
cannot recur. It is recorded as a variation, not silently normalized into a clean-example pass.

The imported English workflow now has operator-reported live evidence for import, greeting and
substantive processing. Its exact clean English example and conflict branch have not yet been
reported after this import. The earlier Japanese original did exercise the conflict branch.
No model/prompt/DSL logic change was made in response to these successful runs.

## Operator 0.4.2 results and English Dify example

The operator confirmed image startup and OpenAPI application version 0.4.2. The Japanese demo
comparison returned revision_required through Dify, retained the known conflict and empty hypotheses,
and introduced no replacement plan. It still placed a requirement in Fact as well as Care.
In a subsequent offline-PC / fictional-data case, the output returned mapped and separated the
reported PC state from the goal and boundary. Its Fact execution_effect overgeneralized lack of
internet access into inability to reach external services. That is a remaining scope-quality issue.
Neither run proves that earlier classification variability is resolved. HTTP node elapsed times
were about 123 and 113 seconds respectively; these are not isolated model-compute measurements.

The supplied `SANA Connection Test.yml` is the basis for `examples/dify/sana-alignment.en.yml`.
The original file's SHA-256 is `0b533c895967b8d9ecca160e49b57ad8f8518be6cb6429348de60e39822c2761`.
The derivative preserves all eight node IDs, seven edges, code-node Python, variable selectors,
branch conditions and terminal output fields. English labels, an API-origin environment variable,
API-matched input limits, and HTTPS certificate verification are the distribution changes.

Local checks passed for five serialization cases (including quotes, newlines, Unicode and maximum
individual input lengths), four rejected human inputs, all seven status routes, and ten invalid
HTTP/JSON/schema/status responses. Every variable reference resolves in the derived graph; the
network override retains the tested alias and does not change port bindings. These are controlled
local checks, not execution by Dify or a real model. Subsequent live operator evidence is recorded
above. Backend application code and version remain 0.4.2.

## Version 0.4.2 comparison-mode hypothesis boundary

- Application tests: **99 passed** (`python -m pytest tests/test_alignment.py -q`), with the same two existing dependency deprecation warnings.
- A controlled HTTP-provider replay of the hypothesis from operator request `3bab0894-9779-496e-a94f-cad9a9bd7aed` now returns `provider_unexpected_comparison_hypothesis`, even alongside a valid known conflict. The offending item is not silently removed to create a successful response.
- The model receives a request-specific hypotheses limit of zero for supplied-AI comparisons. The limit does not leak into omitted/null-AI requests. Blocking and nonblocking hypotheses both violate comparison mode; no keyword matching is used.
- Existing no-AI interpretation, genuine local uncertainty alongside a known conflict, one-sided gap, explicit alternative, evidence and attribution cases remain covered.
- Application/image 0.4.2; public response schema_version 0.4.0 and profile v0.4 remain unchanged.
- Real Uvicorn startup, deterministic English/Japanese greeting responses and bundled/live OpenAPI equality passed with an unavailable provider address; no model was called.
- At authoring time, real-model inference, Windows/Docker, Dify execution and GitHub CI had not been run for this update. Subsequent operator results are recorded above. Structural tests do not establish model adherence or semantic quality in other fields.

Operator-reported 0.4.1 evidence: Docker startup, Japanese demo/English transfer conflicts, fictional
records mapping and uninterpretable-input handling succeeded in the supplied runs. Dify networking,
dynamic request serialization, response parsing and revision/mapped/other branch routing also worked.
The later Japanese form run still prescribed synthetic or anonymized replacement data in a blocking
View hypothesis. This is a semantic regression despite correct routing and status. Prior successful
runs do not establish reliability or a language-specific difference. The next live check is that same
Dify request with 0.4.2, inspecting the whole output as well as the expected empty hypotheses list;
the subsequent results are recorded above.

## Version 0.4.1 comparison guard and attribution guidance

- Application tests: **95 passed** (`python -m pytest tests/test_alignment.py -q`), with the same two existing dependency deprecation warnings.
- The exact both-null missing-premise fragment from the operator's Japanese 0.4.0 run is replayed through a controlled HTTP provider. It now returns a content-free `provider_empty_premise_gap` error rather than a successful map with that fabricated gap.
- Null/whitespace-only comparisons are rejected. One-sided missing-premise comparisons remain valid. Existing explicit-replacement, partial-unknown, evidence and attribution tests remain in place.
- This verifies structural rejection, not that the model will stop generating the bad fragment. The new attribution and scope guidance still needs live-model evaluation. Cross-source semantic contamination is not deterministically detected.
- Application/image 0.4.1; response schema_version remains 0.4.0 with the same fields.

Operator-reported 0.4.0 evidence: Docker startup and handshake succeeded. The English transfer and
demo runs each returned the expected conflict, retained Care, and did not add replacement methods
or unnecessary questions. The Japanese demo identified the conflict but imported the AI's list
screen into a human goal's execution_effect and added a missing_premise about synthetic/anonymized
replacement data. Both gap positions were null. That is not semantic acceptance of the Japanese
case. These single runs do not establish a language-specific accuracy difference or reliability.

## Version 0.4.0 staged extraction and scoped uncertainty

- Application tests: **88 passed** (`python -m pytest tests/test_alignment.py -q`), with the same two existing dependency deprecation warnings.
- Controlled-provider cases verify that an uncertain extraction hint cannot discard an AI comparison or extracted boundary; known Care survives local uncertainty.
- A mocked end-to-end HTTP case verifies the mapping schema's evidence-ID protocol, human-source attribution enums, exact quote restoration and the transfer-conflict result. Unknown or malformed reference IDs are rejected.
- Execution-only unknowns do not cause questions or clarification status. A question attached to that scope is rejected rather than silently removed. A separate alignment unknown survives alongside a known conflict.
- Local greeting and unknown responses use the same public unresolved-item representation. English remains the default; evidence retains original text.
- Real Uvicorn startup, English/Japanese deterministic greeting requests and bundled/live OpenAPI equality: passed, with no model called.
- Real-model extraction coverage, scope judgment, meaning, multilingual quality and latency remain unverified for 0.4.0. Docker, Dify and GitHub CI for this update were not run here.

The operator's 0.3.0 transfer test returned `context_insufficient`, generic questions and null Care
despite an explicit external-transfer boundary and a supplied upload proposal. The pipeline could
short-circuit at its intake kind. Version 0.4 changes that gate and the model tasks; controlled tests
verify the new behavior under supplied responses, not that the operator's model will classify
every case correctly. The first live regression should be `examples/transfer.en.json`.

The two stages still use at most two model calls, with no repair/retry call. No measured improvement
in accuracy, token use, or speed is claimed. Core wording and runtime knowledge hash are unchanged.

## Version 0.3.0 Care generation boundary

- Application tests: **73 passed** (`python -m pytest tests/test_alignment.py -q`), with the same two existing dependency deprecation warnings.
- Controlled-provider tests verify that the model-facing Care schema omits execution_effect and forbids extras; both text and null emitted there are rejected. Valid Care is preserved and serialized with server-supplied null.
- An explicitly supplied replacement choice remains in Care.statement; it is not removed by this change.
- Real Uvicorn startup, English/Japanese deterministic greetings, and bundled/live OpenAPI equality: passed. No model was called for this check.
- The operator subsequently reported Docker startup, handshake and English/Japanese demo results with `revision_required` and null Care effects. The English result still introduced synthetic/anonymized alternatives in View and asked about the replacement source. The later transfer result discarded the known boundary (see 0.4 above). These observations are partial regression evidence, not full semantic acceptance.

Later 0.2.2 operator results: one Japanese diagnostic run met the demo-case expectations with zero
quote mismatches. The earlier Japanese quote failure was not reproduced or explained. English
repeatedly inserted synthetic/anonymized data into Care.execution_effect as an unstated replacement.
This prompted removal of that generation task. The new null is not evidence that all other model
text is grounded, and does not grant downstream execution authority.

## Version 0.2.2 attribution and semantic-guidance update

- Automated tests: **69 passed**, with the same two dependency deprecation warnings.
- Controlled-provider HTTP tests exercise each attribution failure branch, including AI context incorrectly cited as human, and verify content-free field-path/rule diagnostics.
- Provider-request tests verify that human source IDs and source/status conditions reach the model and do not leak from one request to another.
- Application/image version 0.2.2; response schema_version remains 0.2.0.
- Live model and Docker evaluation of this version remain pending.

Operator-reported 0.2.1 results: the English example returned provider_invalid_attribution; the
specific offending field/value cannot be reconstructed from that error alone. The Japanese example
returned revision_required with Japanese prose and a correctly marked known conflict. It still
classified goals/boundaries as Fact, asked implementation questions, and invented a legal/privacy
rationale in execution_effect. This is partial progress, not semantic acceptance or Dify readiness.

## Version 0.2.1 Care schema hotfix

- Automated tests: **64 passed**; two pre-existing dependency deprecation warnings.
- Dedicated CarePremise schema permits only `support_state=not_applicable` and is used for both the model draft and API response.
- Controlled HTTP-provider regression verifies the schema actually sent to the model, accepts valid Care, and rejects each of the four other support states without rewriting output.
- Fact/View premises retain their existing support-state choices. Error code `provider_invalid_care_support` is retained.
- Application/image version is 0.2.1; response `schema_version` remains 0.2.0 because the existing Care requirement is unchanged.
- Actual model adherence still requires operator testing. JSON mode alone does not enforce this schema at decoding time.

The operator reported successful Docker startup and English handshake for 0.2.0, followed by
`provider_invalid_care_support` for both English and Japanese substantive examples. These errors
locate a Care support-state violation but do not reveal which value the model produced. Inspection
found that the shared premise schema permitted values subsequently rejected for Care. This hotfix
removes that schema/validator inconsistency; it does not claim live-model success yet.

## Version 0.2.0, authoring environment

- Python 3.12 virtual environment; pinned dependencies in requirements.txt and requirements-dev.lock.
- `python -m pytest tests -q`: **60 passed**.
- Real Uvicorn process: health check, UTF-8 greeting requests with English default and Japanese override: **passed**. The smoke test used an unavailable provider address to ensure these routes needed no model.
- Live `/openapi.json` matches the bundled schema and reports version 0.2.0.
- Original document wording: CRLF-to-LF canonical hash checks pass for knowledge and all five reference papers.
- Runtime `knowledge_sha256` remains `f2b5ba63b58ab92597019e8a59a391bc15b363b1e0c14a32372ee5af4f01990b`, matching the prior operator-reported run. Core wording and effective runtime knowledge have not changed.
- Controlled-provider tests cover language routing and short-reply fallback, request validation, framework selection, nullable questions, conflict status derivation, question limits, evidence/attribution checks, errors, and HTTP integration.
- Two dependency deprecation warnings remain in Starlette's test-client integration (HTTPX migration and AnyIO alias); neither caused a failure. Runtime provider uses HTTPX 0.28.1.

Generated greeting examples come from the local deterministic branch. Controlled provider fixtures
are not real model responses. Language instructions and structural guards do not prove correct
language use, interpretation, or classification by the live model.

Not executed for 0.2 in the authoring environment:

- Docker build/run: Docker executable unavailable.
- Real LLM inference: the operator's LAN server is not available here.
- Dify integration or validation of its request/proxy networking.
- Updated GitHub Actions run or container registry publication.
- Load testing, adversarial model evaluation, native-speaker review, or production hardening.

## Historical baseline: version 0.1.0

- Authoring tests: 36 passed, plus Uvicorn startup/health/handshake.
- The operator subsequently reported a successful Docker build/start and health response.
- The operator also reported real inference through llama.cpp with gpt-oss-120b-MXFP4.
- That response identified a premise conflict but mixed output languages, reopened an explicit
  real-data prohibition, conflated synthetic and anonymized data, invented reasons, and over-asked
  implementation details. Successful transport was not sufficient semantic acceptance.

Those findings motivated the 0.2 changes. They are not evidence that the revised behavior has
already passed live-model evaluation. Follow ACCEPTANCE.md before connecting execution paths.
