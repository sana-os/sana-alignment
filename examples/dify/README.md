# Dify workflows

| Workflow | Purpose | Setup |
| --- | --- | --- |
| [Connection and comparison](sana-alignment.en.yml) | Compare manually supplied text; no Dify model required | [Dedicated guide](../../docs/DIFY-COMPARISON.md) |
| [Plan and Align](sana-plan-and-align.en.yml) | Generate a plan using a selectable Dify model, then compare it with the original request | [Dedicated guide](../../docs/DIFY-PLAN-AND-ALIGN.md) |

Both return a premise map, not execution authorization. English is the default response language.
Both have successful operator-reported runs in the 0.5.15 test context; see the
[evidence archive](../../docs/validation/README.md). The distributed Build request
code explicitly sends processing_mode=medium. To choose low or high, edit that
value in the Python payload, not the exception-default output. Plan and Align
requires model selection after import. New artifact import across Dify versions
and general model accuracy are not established by those recorded runs.
Existing apps: [replace Parse response code](parse_alignment_response.py) using
[the migration guide](../../docs/MIGRATION-0.5.md); preserve your existing model settings.
