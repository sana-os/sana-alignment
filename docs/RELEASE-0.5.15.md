# SANA Premise Alignment 0.5.15 — prototype release notes

Application 0.5.15, response schema 0.5.0, workflow profile v0.5.
This publication preparation retains the tested backend without a new application
version. It adds distribution settings, dedicated instructions and preserved
development evidence. It does not claim production readiness or perfect semantics.

## What is included

- Source-attributed Fact / View / Care, exact source quotations, extractive overview,
  premise differences and locally retained uncertainty before execution.
- low/medium/high allowances: extraction once, then initial mapping with at most
  zero/one/two corrections. Same validators and configured total deadline in every
  mode. Success returns early; no mode grants execution authority.
- Normal-endpoint traces and separate correction records. New 0.5.15 repair
  feedback gives the relevant reference labels and existing dependency forms.
- Two English Dify exports: manually supplied comparison and model-selected
  Plan and Align. Both explicitly send medium; the planning provider is chosen
  after import. Graph connections and output names retain their tested structure.
- Separate English and Japanese setup guides explaining the different input roles,
  JSON handling, mode placement, result reading and timeout boundaries.
- [Development evidence archive](validation/README.md): raw test attachments,
  earlier conversation observations, fixtures, failures and successful recoveries.

## Evidence and validation

The normal endpoint has an observed 0.5.15 medium recovery after one mapping retry:
request `381b25ff-59e8-4263-b217-1cdcab98b812`, HTTP 200 mapped, three model calls,
456.940 server seconds / 452.997 wrapper seconds. This is one case, not a success rate.

The operator also supplied completed Dify comparison and planning-workflow outputs:
`87642555-a65d-4618-b509-9e9dd874286a` and
`60757f14-a927-4b2c-8c44-11309d83d60c`. Their final maps do not include actual mode,
attempt counts or timing; those metrics remain unverified for those runs.

Offline publication checks execute the actual embedded Build request and Parse
response code, preserve Unicode/quotes/newlines and mode, check variable references
and all seven status routes, reject representative malformed responses, and replay
the three observed 0.5.15 response fixtures without losing their JSON content.
These checks do not emulate a Dify deployment. The 30 raw attachment references
resolve to 29 byte-preserved files with verified hashes.

The publication test report is [RELEASE-CHECKS-0.5.15.json](RELEASE-CHECKS-0.5.15.json).
GitHub CI and live import of the final packaged exports remain separate checks.
Existing working apps with the same payload edit need not be repeatedly rerun to
claim a better success rate.

## Known limits

Read [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md) before interpreting mapped as a
quality verdict. Per-item citation coverage, assumptions losing their framing,
selective overview coverage, scope expansion and model variability remain visible.
The service does not externally verify facts, execute plans or certify sample code.

The Dify exports retain a 600-second HTTP read timeout. SANA's standard budget with
LLM_TIMEOUT_SECONDS=300 is 605 seconds; proxies and the full workflow impose other
limits, and the planning model adds time. Align deployment budgets before relying
on the integration. No timeout or retry budget was silently increased for release.

## Upgrade and publication

- From the delivered 0.5.15 update, apply the separate publication patch after
  checking it. Backend files and requirements.txt are unchanged; no rebuild is
  needed solely for this documentation/workflow update.
- Existing Dify apps can retain their selected model and network/authentication
  settings. Set processing_mode inside Build request's payload if not already set.
- New installations use the dedicated workflow guide. Record the actual Dify and
  provider versions when evaluating a new environment.
- Do not commit local .env, compose.override.yaml or the live traces directory.
  The curated archive is deliberately included, with provenance and scope limits.
- Before declaring an open-source code license, the owner must resolve the existing
  README note that the application-code license is unselected. This preparation
  does not choose or change that license. knowledge/LICENSE.md retains its original
  source terms; these must not be silently treated as a newly selected code license.

Suggested release title: **SANA Premise Alignment 0.5.15 — bounded retries and Dify workflows**.
Suggested tag after review/merge: `v0.5.15`. Preparing these files does not create
a tag, GitHub release, or public API service.
