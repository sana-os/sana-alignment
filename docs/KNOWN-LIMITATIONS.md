# Known limitations in 0.5.15

SANA maps supplied premises; understanding is not agreement or execution authority.
Use the [evidence archive](validation/README.md) to see both successful and failed
cases. These observations are not a representative accuracy benchmark.

| Tendency | Observed examples | Implication for downstream use |
| --- | --- | --- |
| State/request/assumption confusion | Earlier Japanese request omitted from Care; assumed capabilities labelled state | Inspect source framing and human Care; classification is not perfect |
| Scope expansion | No internet interpreted as no external services/APIs; display expanded into generation | Compare exact human boundaries with AI additions; do not infer broad bans |
| Missing implementation details treated as alignment blockers | Format/count/branding became gaps or alignment unresolved items | Dependency checks and repair help, but can still exhaust a mode's allowance |
| Per-item citation coverage | A long field-list statement citing only a heading | Exact quote existence does not prove that the full statement follows from it |
| Selective overview and assumption framing | Overview omitted goals; Assumptions heading lost in View | Read original material, Care, premises and unresolved together |
| Variable outputs on repeated runs | Corrected Fact followed by incorrect scope; success followed by later errors | More attempts do not ensure monotonic improvement |
| Long local-model latency | Direct medium success around 7.5 minutes; other attempts failed/timed out | Budget across planner, SANA, HTTP node, proxy and whole workflow |
| Model and deployment dependence | One operator installation; provider defaults for seed/temperature unknown | Switching models is supported configuration, not equivalent measured quality |

All modes use the same validators. low/medium/high allow zero/one/two mapping
corrections, respectively, within the same configured total budget. high is not an
independent reviewer. No failed candidate is automatically relabelled into success.
On a terminal error, inspect its trace rather than treating it as mapped or unknown.

`provided_source` + `provided` says a claim or proposal was supplied with support
at its reported scope. It does not independently establish the proposal's factual
truth, implementation capability or safety. externally_verified stays false.
The service does not execute or externally validate generated scripts or example data.

Metadata traces retain selected labels, reference hashes and errors, not full
rejected prose. Detail tracing is opt-in and bounded. Logs can expire; retain
relevant request/response/trace files for later review. Correction records are
separate annotations, not edits to original evidence or an automatic training loop.

The distributed Plan and Align workflow sends the human request to the selected
planner before alignment. It does not separately classify greetings, and the map
cannot undo that earlier transmission. Both workflows end with results, not task
execution. Read [processing modes](PROCESSING-MODES.md) and the dedicated Dify guide.
