# Publication fixture completion: 0.5.15

The operator's post-supplement run stopped during pytest collection:
`FileNotFoundError: /src/tests/fixtures/observed-0.5.3-plan-diagnostic.json`.
There was one collection error and two dependency deprecation warnings in 1.59 seconds.
No passing-test total or subsequent release-check result was produced by this run.
This does not supersede the earlier 369-passed result; it records a later packaging failure.

The preceding supplement added three test modules but omitted this required historical fixture.
The fixture-completion package supplies the existing reference fixture and its exact request file,
`examples/quality/observed-plan-052.en.json`. Missing files are added; matching existing text is
retained (LF/CRLF equivalence allowed for the two JSON files). Differing existing content causes
a preflight stop. No application code, validators or historical model results are changed.

## Source evidence

- [Original submitted console text](archive/console-20260921-075641.txt)
- Original upload name: `貼り付けられたテキスト（1 点）(20260921-075641).txt`
- SHA256: `530ff32224cc3ba670cd3d7303136dcd48f58f80a6477296189828d6b33876d7`
- Bytes: 19402
- Preserved byte-for-byte; existing `console-* -text` Git attributes apply.
- This is an additional publication-check attachment, outside the earlier manifest's fixed
  30 references / 29 files. The earlier manifest is unchanged.

Local verification of the restored dependencies is separate from the operator's next run,
whose result is not yet available. No live inference is needed for this packaging repair.

## Operator follow-up: fixture completion verified

After installing the missing diagnostic fixture and request JSON:
- Disposable Docker container: sana-alignment:0.5.15.
- Dependencies: requirements-dev.lock.
- pytest: 388 passed, 2 warnings in 4.57 seconds.
- Offline release checks: both workflows passed; seven status routes and
  three preserved observed responses each.
- Historical archive verified: 30 references / 29 distinct files.
- The earlier collection failure is resolved.
- No live model inference or new Dify import was performed.
- Source: operator-submitted console output; this is a summary.
