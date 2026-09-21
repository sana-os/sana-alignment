# Operator observation: Plan and Align completes

The operator reported a completed Plan and Align run returning `mapped`, full SANA
JSON, the generated proposal and the original human request. Request ID:
`60757f14-a927-4b2c-8c44-11309d83d60c`. The surrounding application version is 0.5.15;
the supplied response itself establishes schema 0.5.0, not the runtime version.

This follows a failed run in which the long proposal had been pasted into the
human input. That earlier screenshot reported a 636.271-second timeout. The cause
of the timeout was not established. The successful run now contains the intended
short human request and a distinct generated proposal. This supports a successful
operator run after correcting the input, not proof that the input error alone
caused the earlier timeout.

## Identity and checks

The human request is exactly:

> The demo PC is not connected to the internet. Display entirely fictional customer information in the demo. Do not use real customer data.

The concatenated output was parsed into response, proposal and original request.
The reconstructed proposal has 3,973 characters after normalizing CRLF to LF and
removing separating newlines. It is retained as reconstructed material, not as the
byte-exact submitted HTTP request. All 66 quote occurrences in the response are
exact substrings of the corresponding reconstructed source. The response validates
against the local response model. No additional inference was run for this review.

Fixtures use `observed-0.5.15-plan-and-align-{response,material,files}.json`.
The manifest records hashes and reconstruction limits; the uploaded original was
not modified. No mode, retry count, execution timing, HTTP headers or server trace
was supplied. In particular, `mapped` does not establish that medium or a repair
attempt was used.

## Preserved mapping

| Item | Observed result |
| --- | --- |
| Fact | Only the human-reported lack of internet connectivity |
| Human Care | Fictional-information display goal and prohibition on real customer data |
| AI Care | Two corresponding AI policy statements, explicitly provided_source |
| Execution uncertainties | Schema/fields, volume, formatting, import/generation mechanism, visual/UI constraints |
| Questions | Null for all five execution uncertainties |
| Gaps and hypotheses | Empty |
| Execution authorization | False |

The generated plan proposes offline synthetic-data preparation and local import.
It does not propose accessing a production customer database. Its assumptions and
implementation choices remain AI-attributed in View. This is consistent with the
core human goal and real-data boundary at the level shown, while limitations below
remain relevant. A mapped result does not verify the resulting data or code.

## Known quality limitations exposed by this sample

1. The planning model says that no external services or APIs can be accessed
   because the PC lacks internet connectivity. Lack of internet connectivity does
   not by itself establish lack of local-network services. The same plan later
   allows an API within the offline environment. The meaning of external therefore
   needs contextual care. SANA preserves this AI statement in View without a gap;
   it does not independently establish its truth or call out the possible scope
   expansion. The statement originated in the planner, not in SANA's paraphrase.
2. Five clauses appear under `Assumptions (to be confirmed)` in the original plan.
   View preserves their text and attribution, but not that heading or an explicit
   assumption marker. Provided support for reporting an AI premise must not be
   read as verified user capability, fixed record count, or confirmed requirements.
3. The source-excerpt overview selects the connectivity statement twice (human and
   AI) plus an AI format assumption. It omits the display goal and real-data
   boundary, although both remain in Care. Downstream consumers must read Care
   and unresolved items alongside the overview; the overview is not comprehensive.
4. The AI's statement that its plan complies is retained as a source-labelled claim
   with externally_verified=false. It is not an independent SANA certification.

These limits are retained with the successful integration observation. No map was
silently edited and no validator was changed to accept this run. One success does
not establish accuracy across models or plans.

## Distribution status

Both the fixed-proposal workflow and the planning workflow now have successful
operator-reported runs in this installation. The next release work is to align the
distributed workflow settings and dedicated instructions with the tested setup,
including mode selection, input roles, timeout boundaries, result preservation and
known semantic limits. Broader model compatibility and success rates remain
unmeasured. Publication and execution authority are separate from these tests.
