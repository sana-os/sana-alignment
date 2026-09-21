# Operator observation: 0.5.14, stage 4, medium

Request 36e70a85-dbe5-4af1-af01-fb3d0b4e7173, normal HTTP endpoint, medium.
The uploaded summary.json, response.json and trace(1).json agree on request identity
and terminal error. Fixtures under observed-0.5.14-stage04-medium-* normalize JSON
formatting; observed-0.5.14-stage04-medium-files.json records original/fixture hashes.
The uploaded files remain unchanged. No live inference was run during analysis.

Known stage-4 material and the requested medium mode reproduce the trace's parsed
request hash and material hash. All 36 reference quote hashes match reconstructed
source excerpts in both mapping attempts. References are local to a run: medium's
q12/q13/q14 are low's q10/q11/q12 by quote identity, not by reference ID.

The low and medium runs share material_sha256 and the initial extraction prompt
hash, but have different extracted clauses and candidates. This is a new inference,
not a resumed low candidate. Do not attribute every difference to mode or estimate
accuracy from these two samples.

## Results

| Stage | Observed result |
| --- | --- |
| Extraction | Parsed, 121.878 seconds |
| Mapping 1 | Rejected, 203.016 seconds per attempt record; repair requested |
| Mapping 2 | Rejected, 183.985 seconds per attempt record; limit reached |
| Calls/retries | Three calls, one correction, medium limits respected |
| Final | HTTP 502 provider_invalid_scope_dependency; no validated map |
| Trace | Saved and copied successfully; execution_authorized false |

The first mapping put q6 (the AI's local-generation requirement) in Fact and
made open format/count/branding topics into interpretation_difference gaps. The
primary error was provider_invalid_gap_dependency at view.premise_gaps.3.ai_premise;
the supplementary violations include the non-factual reference and all three gaps.

The second candidate removed q6 from Fact and removed the six recorded gaps. It
retained the two human Care anchors and three separately attributed AI concerns.
It moved the three open topics into unresolved but assigned:

| Topic / reference | Rejected dependency |
| --- | --- |
| Format / q12 | constraint_scope targeting q12 |
| Record count / q13 | goal_meaning targeting q13 |
| Possible branding constraints / q14 | constraint_scope targeting q14 |

Each target is the open topic itself. The existing rule requires an affected
premise for these alignment dependency kinds. Moving an item into unresolved alone
did not finish the correction. The first invalid unresolved dependency terminates
resolution; the diagnostic collector also records the other two.

For an actual implementation-detail uncertainty, the existing valid form is
execution_detail with target_ref null and question null, with the original topic
still cited in evidence. A real goal/constraint ambiguity requires an appropriately
cited affected premise. Authority and referent uncertainties retain their separate
valid unknown-target cases. None of these rules should be used to discard a real
constraint conflict or force every unknown into execution scope.

These are selected candidate labels, not a complete saved candidate. Metadata does
not recover generated statements or establish that all other fields passed. In
particular, a different primary error does not prove that the low run's previously
missing hypotheses field is present in this independently generated candidate.

## Additional limits

The extraction separates the mixed environment sentence into a state and a concern
in this sample. However, under Assumptions, the availability/bundling clause is
labelled state and the download-related clause concern. These classifications still
need semantic review in context; extraction guidance has not made every label right.

Server time is 508.889 seconds; wrapper time is 497.821 seconds (11.068 difference).
The discrepancy is retained, not explained as network overhead. Budget remaining
on the server clock was about 96 seconds. Another attempt of similar duration to
the observed correction would exceed the existing 605-second budget, so escalating
to high is not the immediate experiment.

## Targeted follow-up

0.5.15 adds a server-built repair_contract to correction feedback: relevant reference
IDs/labels, eligible affected-position targets, explicit execution-detail shape and
preservation of real alignment issues. It changes neither validation nor mode/call/
time limits and performs no automatic relabelling or field insertion. The tests
reconstruct the observed failure conditions using controlled candidates; full raw
candidate replay and live model recovery are not claimed. The next operator check
is one medium request on the updated version with the same material and model.
