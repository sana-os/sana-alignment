# Dify: Connection and comparison

Use this workflow to test connectivity or compare a supplied proposal with a human request.
Import `examples/dify/sana-alignment.en.yml` as **SANA Premise Alignment**.
There is no Dify LLM node; SANA uses its own model configuration.

[日本語の専用手順](DIFY-COMPARISON-ja.md)

1. Complete [Docker networking and API configuration](DIFY.md#1-connect-the-containers).
2. Follow [import and authentication instructions](DIFY.md#2-import-and-configure).
3. Enter `Hello`, leave the AI interpretation blank and select `en`. Expect `handshake`.
4. Replace the whole input with `Show customer information in next week's demo. Do not use real customer data.`
5. Enter `Connect to the production customer database in read-only mode and display a list.` as
   the AI interpretation. Expect `revision_required` with a constraint conflict.
6. Try entirely fictional data in both the request and proposal. Inspect the map and expect
   `mapped` when no material discrepancy remains.

Outputs are `status` and `result` (the complete JSON string). Branches return a result only;
they never authorize or execute a task. Blank AI interpretation requests SANA's own hypothesis
mode; it does not invoke a Dify planning model. See [the full guide](DIFY.md) for field limits,
troubleshooting, other statuses and the exact validation record.

For automatic proposal generation, use [Plan and Align](DIFY-PLAN-AND-ALIGN.md).

## Reuse a JSON test case without changing its text

Human request takes the decoded `input_message`; AI interpretation takes the decoded
`ai_interpretation`. Do not paste the complete JSON object or a quoted/escaped JSON
string into either field. The Build request node serializes the text once.

On Windows, load a known case and copy each property separately:

```powershell
$casePath = (Read-Host 'Full path to the request JSON').Trim('"')
$case = Get-Content -LiteralPath $casePath -Raw -Encoding UTF8 | ConvertFrom-Json
Set-Clipboard -Value $case.input_message
# Paste into Human request, then run the next line and paste into AI interpretation.
Set-Clipboard -Value $case.ai_interpretation
```

The distributed payload includes processing_mode=medium. Change it only inside the
Python payload object when selecting low/high; leave `request_body` as String and
stop on exceptions. Save final output and HTTP response headers. Confirm actual
mode/call count from the request-linked trace, since response schema 0.5.0 does not
include them. The final overview can omit goals: read Care and unresolved as well.
