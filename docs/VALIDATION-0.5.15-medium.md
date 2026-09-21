# Operator observation: 0.5.15, stage 4, medium

The normal HTTP request returned **200 / mapped** after one mapping correction.
This run demonstrates recovery from the observed scope-dependency violation within
the configured medium limits. It does not establish a success rate or complete
semantic accuracy of the map or the submitted plan.

Request ID: `381b25ff-59e8-4263-b217-1cdcab98b812`.
The operator supplied the summary, full response and metadata trace. Repository
fixtures use the prefix `observed-0.5.15-stage04-medium-`; the `files.json` manifest
records uploaded-file and normalized-fixture hashes. Uploaded originals were not
modified. No live inference was performed during this review.

## Identity and bounded recovery

- Application: 0.5.15; response schema: 0.5.0; mode: medium, selected in the request.
- Known stage-4 source file: 4,250 AI characters;
  SHA256 `feb95a60f6cf826f2a10576cd7d3f27dbe4ef101a3d67641a2e692f55d9f2b42`.
- Request IDs agree across all three uploaded files. The known material plus
  `processing_mode=medium` reproduces both canonical request and material hashes
  recorded by the server. The wrapper's sent-file byte hash is operator-reported;
  the actual sent request file was not attached for independent byte comparison.
- All 39 reference quote hashes match reconstructed source excerpts in both
  mapping calls. Reference IDs are local to this run.

| Processing step | Recorded outcome | Seconds |
| --- | --- | ---: |
| Extraction model call | Parsed | 61.972 |
| First mapping attempt | Rejected: `provider_invalid_scope_dependency` | 195.243 |
| Second mapping attempt | Accepted | 199.721 |
| Server total | Three model calls, one correction | 456.940 |
| Client wrapper total | HTTP 200, curl exit 0 | 452.997 |

The model-call and mapping-attempt timings measure different spans. Server and
client totals differ by 3.943 seconds; the cause has not been established. Both
reported totals remain below the configured 605-second inference deadline. Trace
saving/copying succeeded. No high-mode run is needed to demonstrate this recovery.

The first mapping assigned the open format/count/branding topics to alignment
dependencies targeting those same unknown references. The trace records the new
`mapping-repair-contract-1`, including their labels and the execution-detail form.
After correction:

| Topic / reference | First dependency | Accepted dependency |
| --- | --- | --- |
| Format / q10 | `constraint_scope`, target q10 | `execution_detail`, null target |
| Record count / q11 | `goal_meaning`, target q11 | `execution_detail`, null target |
| Possible branding constraints / q12 | `constraint_scope`, target q12 | `execution_detail`, null target |

All three topics retain their source citations in the public `view.unresolved`,
with execution scope and null questions. They were not deleted to obtain `mapped`.
The previous 0.5.14 medium run ended at the same validation rule. The initial
extraction and candidates differ between these runs, so this is a successful
observed recovery, not a controlled estimate of the feedback change's causal effect.

## Preserved content

- Fact contains only the human-reported lack of internet connectivity.
- Care preserves both the display goal and the prohibition on real customer data,
  citing `input_message` with `user_explicit` attribution.
- The three supplied implementation assumptions remain labelled `Assumption:` in
  View, with `provided_source` attribution; they are not externally verified facts.
- The AI's "all data must be generated locally" requirement remains in View. Its
  separate AI-attributed Care entry was removed during correction; the requirement
  was neither erased from the map nor promoted to a human instruction. Whether
  such an added requirement is consequential still requires contextual review.
- Hypotheses, premise gaps and questions are empty; execution authorization remains
  false. An empty gap list reports this model's assessment, not a correctness proof.

The public response validates against the local response model. All 61 quote
occurrences are exact substrings of their attributed source. This checks source
matching, not whether each generated statement is fully supported by its own quote.

## Remaining statement-to-citation coverage issue

Manual inspection found examples where a statement combines material from several
parts of the plan but cites only one part:

| Response path | Statement includes | Its attached evidence covers |
| --- | --- | --- |
| `view.premises.5` | A list of customer fields, including IDs, names, contact details and creation date | Only "Identify the fields the demo needs, e.g.:" |
| `view.premises.6` | Names, domains, addresses and phone numbers | Only the names bullet |
| `view.premises.10` | Place a file or replace a hard-coded list | Only the file-placement bullet |

The additional details appear elsewhere in the supplied plan. These examples are
incomplete per-item citations, not proof that those details were invented absent
from all submitted material. Whole-plan quotations in the overview do not repair
the evidence attached to an individual premise. Corrective review should add the
relevant exact excerpts or narrow/split the statement. No correction was silently
applied to the saved response, and no validator was relaxed during this review.

The overview also contains the full AI plan as a source fallback. This is visible
source material, not independent verification of the code or its claims. The
observed response is retained both as successful scope-recovery material and as
a counterexample for later citation-coverage evaluation.

## Dify compatibility check and next live check

The actual `Parse response` code embedded in both distributed workflows was run
locally against this saved response. Both returned `mapped` and preserved the full
decoded JSON, including Care, unresolved items and execution_authorized=false.
This required no model call. It verifies those parser exports, not the deployed
Dify app, HTTP/proxy path, routing or workflow timeout.

The next live integration check can use the comparison workflow with the unchanged
stage-4 input and supplied proposal, explicitly adding `processing_mode: "medium"`
to its Build request payload. Keep HTTP automatic retries off. The export's HTTP
read timeout is 600 seconds; any proxy/workflow limits also apply. This successful
direct run took about 7.5 minutes and is not a latency guarantee. The server's
605-second maximum budget is longer than the export's 600-second read timeout.
Review the configured boundary before relying on this workflow for distribution.

Retain HTTP status/body/headers, request ID and trace on that single run. A new
inference can produce a different valid classification or fail; compare the actual
returned content. After the fixed-proposal integration check, the Plan and Align
workflow can assess independently generated proposals. Its planning model adds
both variable content and elapsed time, so its status must be evaluated against
the proposal actually generated.
