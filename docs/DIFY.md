# Dify workflow example

Import [sana-alignment.en.yml](../examples/dify/sana-alignment.en.yml) to call SANA from a Dify
Workflow. This example returns a premise map and routes its status. It does not execute the task.
No Dify LLM node or model-provider plugin is required: the SANA API uses its own configured provider.

## Basis and compatibility

This is an English derivative of the operator's working `SANA Connection Test.yml` export.
The export's eight node IDs, seven edges, variable selectors, Python code, output names and three
terminal branches are preserved. Input labels, descriptions, limits and the API URL setting are
adapted for distribution. HTTPS certificate verification is enabled; the default local HTTP URL
is unaffected. Retries remain disabled.

| Version | Meaning |
| --- | --- |
| SANA application 0.4.2 | Backend used in the operator's latest tests |
| SANA response schema 0.4.0 | Required by the response parser; intentionally unchanged |
| DSL `version: 0.5.0` | Preserved from the supplied export; not a SANA or Dify application version |
| Dify 1.10.1-fix.1 | Image tag reported by the operator; broader version compatibility is unverified |

The original workflow has operator-reported successful greeting, conflict and mapped runs.
The operator subsequently imported this English derivative and reported a successful greeting and
an English substantive run. The latter input retained an accidental `Hello` prefix (`HelloThe...`)
and a trailing newline; its task was mapped with separate Fact and Care and no extra hypotheses.
This is evidence for that actual input, not an exact replay of the clean example below.
Local checks also cover references, serialization, parsing and routing. These observations do not
certify other Dify versions or general model quality. The SANA application code is unchanged.

## 1. Connect the containers

If Dify already reaches `http://sana-alignment:8000/healthz`, retain that working network configuration
and skip this section. The example assumes self-hosted Dify and SANA on the same Docker host.
Dify Cloud cannot resolve a private Docker network alias.

Inspect the existing networks:

```powershell
docker ps --format "table {{.Names}}\t{{.Networks}}"
```

Choose an existing network reachable by Dify's actual HTTP request path, including its SSRF proxy
when configured. The operator's tested network was `docker_default`. Set
`DIFY_DOCKER_NETWORK=your_existing_network_name` in the SANA repository's local `.env` if yours differs.
This is separate from any Dify `.env` file. Start the Dify stack first so that network exists.

From the SANA repository root, only if no local override already exists:

```powershell
if (Test-Path .\compose.override.yaml) {
    throw 'Keep your existing override and merge the network configuration if needed.'
}
Copy-Item .\compose.dify.example.yaml .\compose.override.yaml
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Check the Compose configuration before continuing.' }
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw 'Check the Docker startup logs.' }
```

On Linux/macOS, copy the same example only when `compose.override.yaml` is absent, then run the
same Compose commands. The override attaches SANA to its own network and the selected existing
network under the alias `sana-alignment`. It leaves the host port bound to `127.0.0.1:8000`.
The local override is ignored by Git; the configurable example is the distributed file.

The alias must be unique on that network. Docker service discovery uses container ports, so Dify
calls port 8000 on the alias. Its own `localhost` is not the SANA container. External networks and
aliases survive container recreation when declared in Compose.
See [Docker networking](https://docs.docker.com/compose/how-tos/networking/) and
[Compose overrides](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/).

## 2. Import and configure

1. In Dify Studio, choose **Import DSL File** and select `examples/dify/sana-alignment.en.yml`.
   Import as a new app so the tested original remains available.
2. Open the new **SANA Premise Alignment** app. Its environment variable `SANA_BASE_URL` defaults to
   `http://sana-alignment:8000`. For another deployment, enter the reachable origin without a trailing
   slash or `/v1/align`. The **Align premises** HTTP node appends `/v1/align`.
3. Leave **No Auth** when the SANA API has no token configured. If `SANA_API_TOKEN` is configured on
   SANA, create a Secret environment variable in Dify for that token and select it in the HTTP node's
   Bearer authentication setting. This is the SANA API token, not the LLM provider key.

The distributed DSL contains no token, private LAN address or model file path. Secret values belong
in the importing installation and should be excluded from later shared exports. See
[Dify import/export](https://docs.dify.ai/en/cloud/use-dify/workspace/app-management#app-export-and-import)
and [HTTP node configuration](https://docs.dify.ai/en/cloud/use-dify/nodes/http-request).

The HTTP request is POST with `Content-Type: application/json`. The body is **Raw Text** containing
only the **Build request → request_body** variable. That code uses `json.dumps`, so quotes, newlines
and Unicode in user inputs are serialized as JSON without interpolation into a hand-written template.
Do not surround this variable with another pair of quotes.

## 3. Inputs and defaults

| Input | Required | Limit | Behavior |
| --- | --- | --- | --- |
| `input_message` / Human request | Yes | 6,000 characters | Preserved as submitted; whitespace-only input is rejected |
| `ai_interpretation` / AI interpretation | No | 6,000 characters | Blank or whitespace-only means omitted; otherwise preserve the proposal |
| `language` / Response language | No | 35 characters | Defaults to `en`, including when left blank; use `ja`, `es`, `ar`, etc. |

These limits match individual API fields. The API also validates language-tag syntax and total
request size. A tag is a request to the model, not a guarantee of translation quality. Evidence
quotes remain in their original language. The sample exposes no conversation history or framework
selector; the API supports those separately.

## 4. Run two import checks

First submit `Hello` as Human request, with the AI interpretation blank and language `en`.
Expect `handshake`, a short English acknowledgment, and **Other alignment result**. This checks
the imported URL/variables/HTTP/parser path without calling the model.

Then replace the full contents of each form field using these values (each JSON key corresponds
to one form field). Clear the earlier `Hello` instead of appending the next request to it:

```json
{
  "input_message": "The demo PC is not connected to the internet. Display entirely fictional customer information in the demo. Do not use real customer data.",
  "ai_interpretation": "On that PC, display entirely fictional customer information without connecting to external services or using any real customer data.",
  "language": "en"
}
```

Expected semantic treatment: the reported PC state belongs in Fact; the display goal and real-data
boundary belong in Care; the supplied proposal belongs in View. Expect `mapped`, empty hypotheses
and no material premise gap, ending at **Premise map ready**. This is an acceptance criterion.
The operator's observed English success used the `HelloThe...` variation described above;
the exact clean-input case has not been reported for this imported derivative.

For a conflict check, use [align.en.json](../examples/align.en.json): expect `revision_required`
and **Revision required**, without an invented replacement method or a question reopening the ban.

## 5. Outputs and routing

All three terminal nodes return the same output fields:

- `status`: the SANA status string.
- `result`: the full SANA response serialized as a JSON string, preserving Fact / View / Care,
  evidence, unknowns, request ID and metadata. A later code node can use `json.loads(result)`.

| SANA status | Terminal node |
| --- | --- |
| `revision_required` | Revision required |
| `mapped` | Premise map ready |
| `handshake`, `unknown`, `context_insufficient`, `needs_clarification`, `mapped_with_divergence` | Other alignment result |
| HTTP failure, malformed JSON, incompatible schema or unrecognized status | Error; no normal terminal result |

The response parser checks the HTTP status, schema version and allowed status values. It is not a
second full SANA schema validator or a semantic checker. A provider error must not be converted
into `mapped` or a semantic `unknown`. Keep error behavior and retries as configured when first testing.

`mapped` means this response identifies no material unresolved alignment issue. It does not mean
agreement, complete execution requirements, externally verified facts or execution permission.
`meta.execution_authorized` remains false. When extending the workflow, pass the original input
alongside the map and let the downstream Executor apply its own rules. This sample ends with results
so no submitted task is executed while checking the integration.

## Timeouts and troubleshooting

The supplied export's timeouts are retained: connect 10 seconds, read 600 seconds, write 10 seconds;
automatic retry is off. Dify and its proxy can impose additional limits. With SANA's per-call
`LLM_TIMEOUT_SECONDS=300`, its total two-call budget can reach 605 seconds, longer than this read
timeout. If that boundary matters, use a lower provider budget such as 280 seconds (565 seconds
total) or coordinate all HTTP/proxy/workflow limits. The successful operator runs took roughly two
minutes; that is not a latency guarantee or a measurement of model compute alone.

- Name-resolution/connectivity errors: check the URL variable and the networks of SANA and Dify's
  request/proxy path. Keep the SSRF proxy policy enabled; inspect its logs for actual rejections.
- HTTP 405: the align endpoint requires POST. Health uses GET.
- HTTP 401: configure the SANA API token in Dify's HTTP node if enabled on SANA.
- HTTP 422: check field lengths, language tag and that the Raw Text body contains serialized JSON.
- HTTP 502: inspect the HTTP node response for SANA's `detail.code`; this can be a detected model
  contract violation, not a network failure. **Parse response** intentionally stops on non-200.
- Schema error: application 0.4.2 still returns response schema 0.4.0. The DSL's own 0.5.0 version
  is unrelated. If a later backend changes the response contract, review the parser deliberately.

## Quality limits still under evaluation

The operator's 0.4.2 conflict run preserved the known conflict and empty hypotheses, but placed a
request in Fact as well as Care. A later offline-PC case separated Fact and Care correctly, while
its execution_effect generalized lack of internet access into inability to access external services.
These observations remain semantic quality issues; the integration example does not fix them.
See [the validation record](VALIDATION.md) and [live acceptance cases](ACCEPTANCE.md).
