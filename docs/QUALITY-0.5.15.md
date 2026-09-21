# 0.5.15 — make correction feedback concrete

The observed 0.5.14 medium run used its one permitted correction but still failed:
open implementation topics moved from premise_gaps to unresolved while retaining
invalid alignment dependencies on those same open topics. An AI requirement was
removed from Fact during that correction. Source-level attribution and two human
Care anchors remained in the recorded candidates; no final map was validated.
See VALIDATION-0.5.14-medium.md for evidence and limitations.

0.5.15 adds mapping-repair-contract-1 to the feedback available after a rejected
mapping. It includes the reference IDs involved in collected violations, their
extraction labels, Fact eligibility and the allowed affected-position target set.
It shows the execution_detail/null-target/null-question form explicitly and
preserves distinct forms for implementation assumptions, affected premises, and
identity/authority uncertainty. Supplied-AI comparisons also explicitly require
view.hypotheses: []. The server does not fill that field automatically.

These constraints restate the existing validators. They are not a semantic
classifier and do not force every unknown into execution scope. Full new candidates
still face the same validators. Real conflicts and meaningful uncertainty must be
preserved. The inference model, extraction stage, first mapping guidance, all mode
limits and total deadline remain unchanged. No target status is specified.

The same contract is recorded at mapping_attempts[].error.repair_contract in the
ordinary metadata trace. It contains server-built reference labels/IDs and fixed
protocol text, with no user/candidate prose. Its presence after a failed attempt
means it was prepared; it is sent only if a correction is actually allowed.
For low or a terminal medium failure there is no additional model call. The trace
format remains alignment-trace-1 with this additive error field. Public response
schema stays 0.5.0. Dify parsers and mode selection remain compatible.

Validation: 385 controlled-provider tests pass. Added coverage reconstructs the
recorded initial Fact/gap violations and second-attempt unresolved violations,
checks that medium still rejects the latter at its limit, checks exact repair
feedback delivery/logging without changing source inputs, and checks a valid
controlled correction retaining human and AI attribution and three execution
unknowns. Actual scope/authority/referent validator compatibility remains covered.
The two existing dependency deprecation warnings remain.

Subsequent operator evidence records one successful medium HTTP run on 0.5.15:
request 381b25ff-59e8-4263-b217-1cdcab98b812 returned 200 / mapped after one correction.
The three open implementation topics retained their citations and were corrected
to execution scope. See [the observation review](VALIDATION-0.5.15-medium.md) for
identity checks, timings, local Dify parser replay and remaining per-premise
statement-to-citation coverage issues. This is one successful recovery, not an
accuracy guarantee or a measured success rate. No new inference or timeout
allowance was added. The delivered package was checked against the previously
delivered 0.5.14 tree and verified after patch application; its original files
remain unchanged. The observation review and fixtures were added afterward.
