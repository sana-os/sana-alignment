# Earlier operator observations preserved from the working conversation

These are curated summaries of supplied console output, JSON and screenshots.
They are not reconstructed raw provider outputs. Missing dates, app versions,
request IDs or metrics remain unknown. Similar inputs and repeated uploads are
not counted as independent benchmark trials. Files that survived as attachments
are additionally preserved in [the raw archive](archive/manifest.json).

## Early integration and classification

| Context / request ID | Observed result | Development relevance |
| --- | --- | --- |
| Initial Japanese conflict, `006f76b1-5f3e-4247-b4f6-d56bd8e6d8f5` | HTTP 200, revision_required; posted body truncated | Do not treat the truncated body as complete validation evidence |
| Japanese conflict, `06b38d4a-a224-44ec-8652-21332d0466cc` | revision_required, conflict blocks execution, Dify revision branch | Production read-only access conflicts with the real-data prohibition |
| English fictional data, `2e921297-0468-4964-b9ca-2a5027b0570e` | mapped, empty gaps | Compatible proposal; not execution authorization |
| Greeting, `5446568d-0edb-4a51-96c8-870dda1bb61f` | handshake, no extraction/mapping; Dify Other branch | Model-free greeting path |
| Japanese conflict, `3bab0894-9779-496e-a94f-cad9a9bd7aed` | revision_required plus an unwanted synthetic/anonymized replacement hypothesis | Supplied-AI comparison must not generate replacement hypotheses |
| App 0.4.2, `6538be56-af14-4b8f-a46b-00c57883a46e` | revision_required; no replacement hypothesis; a request also appears in Fact | Classification remained imperfect despite successful routing |
| Japanese offline task, `ba12a1a7-42f5-4c18-9a97-5d5f4b76a738` | mapped | Fact effect broadened no internet into inability to access external services |
| Imported English workflow, `fa2fc5d5-0741-49ba-a432-41fc1b3d9a7b` | handshake | Import/greeting completed |
| English import, `038e395b-203f-4481-8ad6-68803cb3152f` | mapped with `HelloThe...` prefix and trailing newline | Input variation was retained, not a clean-input replay |
| Greeting, `68a9ab1f-9f1f-4359-805f-ce82dd1bdd75` | handshake | Subsequent successful greeting |
| Plan workflow greeting, `e5d319b9-7773-4fb6-9ed0-f6746b69e281` | mapped; AI supplied `Hello! How can I assist you today?` | Supplied AI text invokes comparison; not the no-AI handshake route |
| App 0.4.3, `bcffd0b5-d09c-4dae-90c7-8283c051b7ca` | mapped_with_divergence | Compatible local implementation treated as a difference; display expanded into generation |
| App 0.4.4, `9fe8f19d-a4a0-4ae6-80fc-ef957e04b8fa` | mapped | AI unspecified fields/count entered Fact; effects added local generation; unresolved lacked evidence |
| App 0.5.0, `9f793a32-7e57-4187-bd9c-9334cdc05c38` | mapped, extractive overview and null effects | Human state still became an added no-internet requirement in Care |
| App 0.5.1 English offline, `e4e838ee-87aa-4457-b0f9-8befa9c344be` | mapped | State in Fact, goal/prohibition in Care, cited execution unknown |
| App 0.5.1 English prohibition, `bfdf2fd5-e580-4411-a823-c829948bcf96` | mapped, Fact empty | Explicit no-connection instruction belongs in Care |
| App 0.5.1 Japanese offline, `e7374678-5335-4858-bbe8-553ab4e09369` | mapped | Display goal omitted from Care; unresolved evidence empty |
| App 0.5.1 Japanese prohibition, `f634a32e-53c2-4052-816e-4c192eb30ea4` | mapped | Three instructions in Care; unresolved evidence still empty |
| App 0.5.1 diagnostic, `3f8ae8e6-88e0-46ed-a7b5-6c8d54d51b1f` | mapped | Display request extracted as proposal, ineligible for Care; omission originated before mapping selection |
| App 0.5.2 diagnostic, `752af765-4e16-4525-9c38-632dd444ed62` | mapped | Display clause extracted as request and selected for Care; unspecified items retained with evidence |
| English conflict, `43154c5d-57ec-450a-b9c8-7dc25c41de19` | revision_required | Known conflict remained detectable after quality changes |
| Dify old parser | Unexpected SANA response schema | Parser version guard needed migration to response schema 0.5.0 |
| Dify after parser replacement, `aecba7f7-b5be-4862-b0bb-68660adc849e` | revision_required | Conflict output passed Dify parser and routing |

## Long-plan diagnostics and bounded retries

| Context | Observed result | Scope of evidence |
| --- | --- | --- |
| Initial long planning workflow | HTTP node reported maximum retries (0), approximately 83 seconds | Cause not established; retry count text is not the root cause |
| Later generated long plan | Same HTTP-node error after approximately 100 seconds | Dify failure distinct from later direct-API diagnosis |
| App 0.5.2 direct long plan | HTTP 502 provider_ungrounded_evidence; 58.923590 seconds | Repeated pasted identical console output is one reported measurement, not proof of independent repeated runs |
| App 0.5.3 diagnostic | provider_invalid_attribution at care.2.evidence.0.source; user_explicit_requires_human_evidence | The failed third item's full content was not supplied |
| AI-only confirmation request, `b732b1fc-20d6-43a2-8414-3ff6b20b9fcc` | mapped; human Care only goal/prohibition | AI request stayed attributed to AI; two execution unknowns lacked evidence |
| Human-adopted confirmation request, `768a2c95-e500-442f-be7a-5478cef4f6f5` | mapped; confirmation instruction also in human Care | Same wording can change role with human adoption |
| App 0.5.3 ladder stage 1, `bc16816f-aa5d-46e2-9ebb-2474591f039d` | HTTP 200 mapped, 366 AI characters, 119.375 seconds | Raw 01.response.json is archived |
| App 0.5.3 ladder stage 2 | HTTP 502 provider_invalid_output, 1,063 AI characters, 193.882 seconds | Stage runner stopped; response and subsequent fresh diagnostics are separate records |
| App 0.5.3 ladder stage 3, `4a3f8524-e2b9-4d37-a9f1-1de7dca8b8a1` | HTTP 200 mapped_with_divergence, 1,974 AI characters, 221.831 seconds | Format/count/branding unknowns became missing-premise gaps |
| App 0.5.3 ladder stage 4 | HTTP 502 provider_invalid_attribution, 4,250 AI characters, 191.931 seconds | care.2.evidence.0.source attribution violation |
| App 0.5.4 older diagnostic | provider_excessive_questions; Extraction and Draft completed | No quote mismatches; empty Pydantic errors did not imply semantic validity |
| App 0.5.4 newer diagnostic, `90a3af58-e76d-4b9e-9b4c-10c3a1792073` | needs_clarification | Separate inference; not contradictory evidence about the older failed run |
| App 0.5.5 stage 4 | provider_invalid_output, Extraction evidence too_long; wrapper 109.554 seconds | No completed stages; no mapping recovery had occurred |
| App 0.5.6, `72e313f7-b020-498b-94a0-961bf7733144` | needs_clarification | Full diagnostic retained; HTTP/diagnostic success alone was insufficient |
| App 0.5.7, `f948475d-33ad-4fe8-9c21-f096d5e77cef` | mapped_with_divergence | Full diagnostic and version-specific quality review retained |
| App 0.5.8, `02942cf0-6d97-4758-ae0b-25b4a90a6a55` | mapped_with_divergence | Full diagnostic retained |
| App 0.5.9, `cfb62ce9-3971-4fbe-b9dd-ea85d60958e0` | mapped | Full diagnostic retained; not a general quality guarantee |
| App 0.5.10 | provider_invalid_gap_dependency; wrapper 290.288 seconds | Open topics alone are not comparison positions |
| App 0.5.11 | provider_invalid_scope_dependency; wrapper 280.528 seconds | Dependency requires kind and target_ref |
| App 0.5.12, `76064e91-d4a5-46b0-b9ec-93c3c7f59b19` | needs_clarification after one correction; 409.431 seconds | Mixed Fact fixed but execution unknowns regressed into alignment scope |
| App 0.5.13, `561124f4-28d4-459f-bde0-a28c65c9fc90` | mapped after one correction; 421.235 seconds | Successful diagnostic recovery; not yet a normal endpoint mode test |
| App 0.5.14 low, `f5e3f217-81cb-433a-8b04-d8a740061d6f` | HTTP 502 provider_invalid_output, no retry | Missing hypotheses field; client 247.994 seconds; saved trace |
| App 0.5.14 medium, `36e70a85-dbe5-4af1-af01-fb3d0b4e7173` | HTTP 502 provider_invalid_scope_dependency after one retry | Client 497.821 seconds; server 508.889; unresolved timing difference retained |
| App 0.5.15 medium, `381b25ff-59e8-4263-b217-1cdcab98b812` | HTTP 200 mapped after one retry | Client 452.997 seconds; server 456.940; targeted scope repair succeeded |
| App 0.5.15-context Dify comparison, `87642555-a65d-4618-b509-9e9dd874286a` | mapped final output | Actual mode, retries and timing not included in supplied final output |
| Planning workflow input mix-up | timed out, 636.271 seconds | Human request contained the old long proposal; causal relationship to timeout not established |
| App 0.5.15-context Plan and Align, `60757f14-a927-4b2c-8c44-11309d83d60c` | mapped, correct short human input and a new generated plan | Five execution unknowns retained; runtime mode/retries/timing unreported |

## Setup and workflow observations

- OpenAPI application versions and healthy containers were checked by the operator
  during upgrades. A successful healthz response explicitly did not check provider
  connectivity. App 0.5.x continuing to return schema 0.5.0 is intentional.
- An attempted patch used a request JSON path and failed with No valid patches.
  Another documentation patch was already present. Neither failure is an inference
  result. Preserve patch/version/hash checks in installation instructions.
- PowerShell RemoteSigned blocked a downloaded wrapper. The operator checked its
  expected SHA256 and unblocked that file; the global execution policy was not
  changed. Diagnostic v1/v2 and later wrappers have distinct version/hash guards.
- The first attempted Dify mode entry was placed in an exception default output.
  The corrected location is the Python payload object. Exception handling should
  stop on failure rather than substitute a partial request body.
- JSON string syntax was initially pasted into a text field. ConvertFrom-Json and
  copying the decoded property preserve actual text; JSON escaping is then applied
  exactly once by Build request. In Plan and Align, copy input_message, not the old
  ai_interpretation. The planning node supplies the latter automatically.
- PR #1 was reported merged after two checks passed; the screenshot identified
  merge commit 78c6c5e and source commit 4cee8b0. That is historical repository
  evidence, not proof that subsequent local 0.5.x patches have been pushed.

Records omitted from the conversation cannot be recovered by assigning likely
statuses. Keep future original request/response/trace files alongside this ledger.
