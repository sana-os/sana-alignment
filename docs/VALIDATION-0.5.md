# 0.5.0 candidate validation

Local author run: `python -m pytest tests -q` with the configured uv test environment:
140 passed; two dependency deprecation warnings. This includes seven diagnostic tests
available in the author's workspace. An installation without those optional tests has 133 tests.

The new tests replay selected failure excerpts from request
9fe8f19d-a4a0-4ae6-80fc-ef957e04b8fa through the effect/overview contracts. They also exercise
the ASGI endpoint and mocked provider adapter, including exact effect reference resolution,
nullable values, source attribution, fallback, multilingual and long excerpts, and error paths.
The Dify parser tests cover both supported response versions and refusal to turn errors or
execution authorization into a normal result. Both distributed DSLs were parsed and their
graph endpoints and embedded parser code checked.

No live external model, Docker container, or Dify instance was available for this validation.
User model evaluation remains pending. No claim about overall semantic accuracy follows from
the automated results. See MIGRATION-0.5.md for the bounded guarantee and remaining risks.

## Operator-reported 0.5.0 follow-up

Request `9f793a32-7e57-4187-bd9c-9334cdc05c38`, using `examples/quality/offline.en.json`,
returned `mapped` with schema 0.5.0 after the operator confirmed application version 0.5.0.
Effects were null, the overview used exact attributed excerpts, and missing fields/count were
execution-scope unresolved items. No additional generation action appeared in that response.
However, Care added "The demo PC must operate without internet access." from the reported
connection state. That is an observed state-to-requirement error, not an accepted requirement.
Selected exact excerpts are in `tests/fixtures/observed-0.5.0-care.json`.
See [QUALITY-0.5.1.md](QUALITY-0.5.1.md) for the targeted follow-up and local validation.
