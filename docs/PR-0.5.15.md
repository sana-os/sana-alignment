# Prepare SANA 0.5.15 prototype distribution and preserve development evidence

The runtime has accumulated bounded repair, attribution and scope checks, but the
distribution files and validation history need to reflect the operator's actual
experience. Earlier successful statuses also exposed semantic errors, so keeping
only passing examples would conceal useful development evidence.

This change prepares application 0.5.15 with response schema 0.5.0 for review. The
runtime supports low/medium/high processing allowances, the same validators in all
modes, bounded normal-endpoint traces and concrete mapping-repair feedback. The
publication preparation leaves that backend unchanged, explicitly sets medium in
both Dify exports, and adds dedicated English/Japanese usage instructions.

The evidence archive preserves 30 supplied JSON/text attachment references as 29
distinct original-byte files, with SHA256 provenance. It also preserves earlier
conversation observations as labelled summaries, existing regression fixtures and
version-specific engineering notes. Failed attempts, diagnostic-version differences,
input mistakes and timing discrepancies remain documented.

Validation includes the controlled test suite and offline checks of both embedded
workflow parsers/builders, variable references, status routes and recorded responses.
See docs/RELEASE-CHECKS-0.5.15.json for the final local result. Operator evidence
includes one medium HTTP recovery after one correction and successful fixed-plan
and generated-plan Dify outputs. The latter do not establish actual retry counts
or latency, and none of these cases establishes a general accuracy rate.

Remaining issues include classification variability, incomplete per-premise
citation coverage, selective overview content, scope expansion and long inference
times. See docs/KNOWN-LIMITATIONS.md. No returned status authorizes execution.
The existing application-code license selection remains an owner decision; source
terms in knowledge/LICENSE.md are unchanged. This PR does not publish a service.
