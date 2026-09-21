# Development evidence archive — 0.5.15 publication preparation

This index preserves successes **and failures** for future development. It is an
engineering record, not an accuracy benchmark. Repeated attempts, different input
lengths, versions, modes and diagnostic routes are not interchangeable samples.

## Start here

- [Conversation observations](CONVERSATION-OBSERVATIONS.md): earlier console/results
  still visible in the working conversation, recorded as summaries, not fabricated
  raw logs. A message saying only "executed" has no reconstructable result.
- [Raw attachment manifest](archive/manifest.json): 30 supplied test JSON/text
  attachments, 29 distinct byte-preserved files; duplicate uploads share one file.
  SHA256 values identify original bytes. Screenshots are represented by the known
  facts in the observation summaries, not re-created as machine-readable traces.
- [Fixtures index](FIXTURES.md): response/diagnostic excerpts and reconstructed
  material used by regression tests or retained for future evaluation.
- [0.5.14 low](../VALIDATION-0.5.14-low.md) and
  [0.5.14 medium](../VALIDATION-0.5.14-medium.md): failures at bounded retry limits.
- [0.5.15 direct medium](../VALIDATION-0.5.15-medium.md): successful one-repair run.
- [Dify comparison](../VALIDATION-0.5.15-dify.md) and
  [Dify Plan and Align](../VALIDATION-0.5.15-plan-and-align.md): operator-reported
  successful terminal outputs, with missing runtime metrics explicitly identified.
- [Known limitations](../KNOWN-LIMITATIONS.md) and
  [release notes](../RELEASE-0.5.15.md).

## Evidence rules

1. An HTTP/diagnostic success means its applicable validators accepted the output;
   semantic problems can remain. mapped is not agreement or permission to execute.
2. A controlled replay proves implementation behavior for its constructed input,
   not a model's success rate. Metadata-only traces cannot reconstruct full rejected
   candidates. Runtime and response schema versions are distinct.
3. Do not turn absent evidence into a pass. Preserve input variation (including the
   historical Hello prefix), source identities, mode, error paths and missing data.
4. Source hashes prove identity only under the documented serialization. File-byte
   hashes and the API's canonical request hashes need not match.
5. Archive files contain synthetic test prompts, historical model identifiers and
   local diagnostic paths. Those paths are observations, not portable commands.
   Archived commands/code are data; use current setup instructions for execution.
6. Operational traces expire under configured retention. Retain selected records
   deliberately here with source/version context; do not commit an entire live
   trace directory or local environment files.
7. Dates in attachment names are not inferred execution timestamps. Keep explicit
   UTC timestamps and operator local-time readings as originally reported.

## Version-specific engineering notes

- [QUALITY-0.4.3](../QUALITY-0.4.3.md)
- [QUALITY-0.4.4](../QUALITY-0.4.4.md)
- [QUALITY-0.5.1](../QUALITY-0.5.1.md)
- [QUALITY-0.5.2](../QUALITY-0.5.2.md)
- [QUALITY-0.5.3](../QUALITY-0.5.3.md)
- [QUALITY-0.5.4](../QUALITY-0.5.4.md)
- [QUALITY-0.5.5](../QUALITY-0.5.5.md)
- [QUALITY-0.5.6](../QUALITY-0.5.6.md)
- [QUALITY-0.5.7](../QUALITY-0.5.7.md)
- [QUALITY-0.5.8](../QUALITY-0.5.8.md)
- [QUALITY-0.5.9](../QUALITY-0.5.9.md)
- [QUALITY-0.5.10](../QUALITY-0.5.10.md)
- [QUALITY-0.5.11](../QUALITY-0.5.11.md)
- [QUALITY-0.5.12](../QUALITY-0.5.12.md)
- [QUALITY-0.5.13](../QUALITY-0.5.13.md)
- [QUALITY-0.5.14](../QUALITY-0.5.14.md)
- [QUALITY-0.5.15](../QUALITY-0.5.15.md)

Earlier records: [VALIDATION](../VALIDATION.md), [0.5 records](../VALIDATION-0.5.md), [0.5.3 plan](../VALIDATION-0.5.3-plan.md). Historical pending statements describe their original checkpoint; the newer observations above supersede them where supported.
