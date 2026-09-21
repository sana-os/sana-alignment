# Operator publication check: 0.5.15

Source: operator-submitted console output in the publication-preparation conversation. This is a summary, not a byte-for-byte console archive.

- Windows PowerShell invoked a disposable container from `sana-alignment:0.5.15`.
- Repository mounted read-only at `/src`; separate virtual environment under `/tmp`.
- Dependencies installed from `requirements-dev.lock`.
- `python -m pytest tests -q -p no:cacheprovider`: **369 passed, 2 warnings in 5.21 seconds**.
- Warnings: Starlette TestClient/httpx deprecation and anyio BlockingPortal alias deprecation.
- `scripts/verify_release_0515.py` succeeded: two workflows, seven status routes and three preserved observed responses each; archive 30 references / 29 distinct files.
- No live inference or Dify import was performed by this check.

The preparation environment previously reported 388 passing tests. Three test modules in that environment contain exactly 19 tests (7 + 7 + 5): `test_diagnostics.py`, `test_care_diagnostics.py`, and `test_observed_plan_053.py`. Those modules were not listed among the operator's earlier changed/untracked files. Their absence is a candidate explanation; actual presence is checked by `git apply --check` before the supplement is applied. The supplementary patch adds those modules and their `scripts/diagnose_care.py` helper without changing application code. The operator's post-supplement test result is not yet known.
