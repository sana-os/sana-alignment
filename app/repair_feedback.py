"""Concrete reference constraints for an allowed mapping correction.

These are the existing structural rules, not new semantic classifications. No
candidate field is changed, no unknown is discarded, and no status is prescribed.
"""
from .role_contract import POSITION_DEPENDENCIES

FUNCTIONS = {'state', 'request', 'concern', 'proposal', 'unknown', 'mixed',
             'assumption', 'other', 'unclear'}


def repair_contract(error, payload):
    registry = payload.get('_evidence_index', {})
    unknowns = set(payload.get('_unknown_evidence_refs', []))
    excluded = set(payload.get('_non_fact_evidence_refs', []))
    functions = payload.get('_evidence_functions', {})
    relevant = []
    for issue in error.violations[:16]:
        for ref in issue.get('evidence_refs', [])[:8]:
            if isinstance(ref, str) and ref in registry and ref not in relevant:
                relevant.append(ref)
    contract = {
        'version': 'mapping-repair-contract-1',
        'references_in_violations': [{
            'ref': ref, 'source': registry[ref]['source'],
            'extraction_function': functions.get(ref) if functions.get(ref) in FUNCTIONS else None,
            'fact_reference_allowed': ref not in excluded,
            'position_dependency_target_allowed': ref not in unknowns,
        } for ref in relevant],
        'open_topic_refs': [ref for ref in registry if ref in unknowns],
        'fact_reference_options': [ref for ref in registry if ref not in excluded],
        'unresolved_forms': {
            'implementation_detail': {
                'use_when': 'The unresolved item concerns an implementation input, without ambiguity about an affected goal, constraint, authority, referent or compared premise.',
                'fixed_fields': {'dependency': {'kind': 'execution_detail', 'target_ref': None},
                                 'question': None},
                'evidence': 'Retain the supplied reference(s) for that open topic. Do not invent an answer.',
            },
            'implementation_assumption': {
                'kind': 'execution_assumption',
                'target_ref_options': list(registry),
                'question': None,
                'use_when': 'An unconfirmed implementation capability/resource is being assessed. Cite that actual assumption, not a newly invented capability.',
            },
            'affected_position': {
                'kinds': list(POSITION_DEPENDENCIES),
                'target_ref_options': [ref for ref in registry if ref not in unknowns],
                'use_when': 'A separately cited goal/constraint/compared premise has unclear meaning or scope. Merely choosing a different ID to pass validation is not a correction.',
            },
            'identity_or_authority': {
                'kinds': ['referent', 'authority'],
                'target_ref_options': list(registry),
                'use_when': 'A real identity or authority uncertainty remains, including an unknown approver. An implementation topic does not become an identity or authority issue by renaming it.',
                'referent_span': 'For referent only, copy the exact ambiguous expression from target_ref.',
            },
        },
        'preservation': 'Preserve human goals/boundaries, real conflicts and meaningful unknowns. Reassess affected items from the sources; these forms do not predetermine semantic scope. Return a complete new candidate for the same validation.',
    }
    if payload.get('ai_interpretation') is not None:
        contract['required_comparison_fields'] = {'view.hypotheses': []}
    return contract
