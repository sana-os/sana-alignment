# Migrating from 0.1.0 to 0.2.0

This prototype changes the response contract. The endpoint remains `/v1/align`, but
`schema_version` is now `0.2.0` and `meta.profile` is `workflow-premise-map-v0.2`.
Update consumers before using 0.2 in an existing workflow.

| Area | 0.1 | 0.2 |
| --- | --- | --- |
| Omitted `language` | Japanese | English |
| Language values | `ja` / `en` | Common language/script/region tags; UTF-8 |
| Omitted `frameworks` | Automatic selection | No additional detailed lens |
| Automatic selection | Omission or null; up to three | `"auto"` or explicit null; at most one |
| Explicit lenses | Up to three | Unchanged |
| Known constraint conflict | Usually `needs_clarification` | `revision_required` when classified as a blocking `constraint_conflict` |
| Gap type | Unspecified | `kind`: conflict, interpretation difference, or missing premise |
| Per-entry question | Required text | Nullable; null required for known conflicts |
| Questions | Multiple fields could contain different questions | At most one distinct focused question across all fields |
| Language metadata | Absent | Requested tag, actual short-reply language, short-reply fallback flag |

For callers that relied on the old defaults, explicitly send `language: "ja"` and
`frameworks: "auto"`. Core principles remain loaded in all modes.

Generated prose follows the requested language; evidence and observations stay verbatim.
The server does not detect or certify a substantive model response's language.
Clients must accept null questions. Handle unknown future statuses explicitly rather than treating
all HTTP 200 responses as a successful execution gate.

The prompt now distinguishes goals/boundaries in Care from factual claims and avoids inventing
reasons for explicit constraints. These semantic behaviors need model-level review.
Code checks only structure, quotation provenance, limited attribution rules, and status derivation.

## Updating a checkout

Keep your existing `.env`. After applying the changes or pulling the updated branch:

```powershell
docker compose up --build -d
docker compose ps
curl.exe --max-time 10 http://localhost:8000/healthz
curl.exe --max-time 620 http://localhost:8000/v1/align -H "Content-Type: application/json" --data-binary "@examples/align.en.json"
curl.exe --max-time 620 http://localhost:8000/v1/align -H "Content-Type: application/json" --data-binary "@examples/align.json"
```

Run the two inference requests sequentially, particularly with a model server configured for one slot.
Add an Authorization header if you enabled `SANA_API_TOKEN`.
Review them with [ACCEPTANCE.md](ACCEPTANCE.md). Model timeouts/output errors are diagnostic results;
record their error code instead of interpreting them as a successful premise map.
