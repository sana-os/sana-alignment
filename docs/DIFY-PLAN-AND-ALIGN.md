# Dify: Plan and Align

Import `examples/dify/sana-plan-and-align.en.yml` as a new Workflow app.
[日本語の専用手順](DIFY-PLAN-AND-ALIGN-ja.md)
This is a distribution candidate. The operator has now reported a successful planning-workflow
run in the 0.5.15 test context, returning schema 0.5.0 and mapped after correcting the human input.
See [the observed result and remaining limits](VALIDATION-0.5.15-plan-and-align.md).
This verifies the reported installation, not every model or Dify version. The prior timeout's
cause remains unconfirmed. See [migration instructions](MIGRATION-0.5.md) for parser migration;
retain the selected planning model when replacing Parse response code.

## 1. Connect SANA

Follow sections 1 and 2 of [the connection guide](DIFY.md) for Docker networking,
SANA_BASE_URL and optional Bearer authentication. Confirm the comparison workflow works first.
Keep its app available for controlled tests.

## 2. Select the planning model

Open **Draft plan — select model** and select a chat model configured in your Dify workspace.
The distributed provider and model fields are intentionally empty. There are no bundled provider
dependencies or credentials. Install/configure your chosen provider if needed, then select it.
If your Dify importer rejects an unconfigured model, do not publish the app; report the import
error so the template can be adapted to your version.

The Dify planning model and SANA's alignment model are independent. SANA's model is configured
in its own `.env`. Changing the Dify model does not change SANA's model. Both may use the same
local server; requests in this workflow are sequential. Model selection and supported parameters
are explained in the [Dify LLM documentation](https://docs.dify.ai/en/cloud/use-dify/nodes/llm).
Use a text response. If a reasoning model includes internal reasoning in its text output, configure
the provider to expose the final answer separately before using it as a proposal.

The original request is sent to the planning provider BEFORE alignment. Configure both providers
locally when the submitted material must stay local. SANA cannot undo an earlier transmission.

## 3. Run

Enter **Human request** and **Response language** (`en` by default). No manually supplied AI
interpretation is needed. The workflow generates a proposal, JSON-encodes the unchanged input
and proposal, calls SANA, validates the response and routes by status.

Paste only the human task into Human request. Do not paste an earlier generated
plan there. Build request's `input_message` comes from Input; `ai_interpretation`
comes from Draft plan's text output. The distributed payload explicitly includes
processing_mode=medium; low/high can be selected by changing that value in the
Python code. Do not use an exception default value to set a request field.

First task:

```text
The demo PC is not connected to the internet. Display entirely fictional customer information
in the demo. Do not use real customer data.
```

Inspect the actual proposal before assessing the status. A compliant proposal should normally
be mapped; a conflicting proposal should require revision. Unlike the comparison workflow,
the proposal varies with the model, so a fixed status alone is not an acceptance test.

## 4. Read the outputs

Every terminal branch returns `original_request`, `proposed_plan`, `status`, and `result`.
`result` is the full alignment JSON encoded as a string. `mapped` is not permission to execute.
`revision_required` returns the conflicting proposal for review. Other outcomes preserve their
original status, including uncertainty. No branch executes a task or automatically revises a plan.
HTTP/JSON errors stop the run instead of returning a successful map.

Read Care and unresolved alongside the overview and original plan: the extractive
overview is selective. Supplied AI assumptions remain claims of that source,
not verified user capabilities. See [known limitations](KNOWN-LIMITATIONS.md).

Blank model output stops the run. A request or proposal over 6000 characters also stops rather
than truncating possible constraints. Shorten explicitly or adjust the model output configuration.
A greeting still visits the planning model in this template; use the comparison app for a
model-free handshake check. No conversation memory, tools, RAG or file upload is enabled.

## 5. Validate before distribution

- Import into the target Dify version and select a model without editing graph connections.
- Run the fictional-data task; confirm the original request is byte-for-byte preserved in JSON.
- Check that the returned proposal equals the text supplied to SANA as `ai_interpretation`.
- Use the comparison app to test a deliberately conflicting plan and an unknown input.
- Check empty/oversized proposals and failed HTTP requests stop, with no successful terminal result.
- Record Dify/provider/model versions and request IDs. Do not export credentials.

Switching models preserves the wiring but does not establish equivalent alignment quality.

Keep the actual generated plan and serialized HTTP request with the result. Save
the response headers and request-linked server trace when mode/retry/timing evidence
is needed; those metrics are not in the final map. The HTTP read timeout in the
export is 600 seconds; SANA's default total inference budget is 605 seconds, and
the planner, proxies and workflow have additional limits. See the connection guide's
timeout section. Inspect a failed node before changing limits or repeating inference.
