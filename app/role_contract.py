"""Structural checks for declared roles, not a semantic classifier."""

ALIGNMENT_DEPENDENCIES = ('goal_meaning', 'constraint_scope', 'authority',
                          'referent', 'comparison_assumption')
# These dependencies concern the meaning/scope of an affected proposition.
# An open topic alone is not that proposition. Authority and referent retain
# their distinct unknown-target cases (e.g. an unidentified approver/person).
POSITION_DEPENDENCIES = ('goal_meaning', 'constraint_scope', 'comparison_assumption')
DEPENDENCIES = ('execution_detail', 'execution_assumption') + ALIGNMENT_DEPENDENCIES
NON_FACT_FUNCTIONS = {'request', 'concern', 'proposal', 'unknown', 'mixed', 'assumption', 'unclear'}


def fact_exclusions(registry, functions):
    excluded = [registry[ref] for ref, function in functions.items()
                if function in NON_FACT_FUNCTIONS and ref in registry]
    return [ref for ref, item in registry.items() if any(
        bad['source'] == item['source'] and bad['quote'] in item['quote']
        for bad in excluded)]


def resolve_unresolved(item, registry, path, unknown_refs=()):
    from .provider import ProviderError
    def reject(rule):
        raise ProviderError('provider_invalid_scope_dependency', issue={'path': path, 'rule': rule})
    if not isinstance(item, dict) or 'scope' in item:
        reject('select_dependency_instead_of_generated_scope')
    dependency = item.get('dependency')
    if not isinstance(dependency, dict) or not {'kind', 'target_ref'} <= set(dependency):
        reject('dependency_requires_kind_and_target_ref')
    kind, ref = dependency['kind'], dependency['target_ref']
    if kind not in DEPENDENCIES:
        reject('unknown_dependency_kind')
    allowed = {'kind', 'target_ref', 'referent_span'} if kind == 'referent' else {'kind', 'target_ref'}
    if set(dependency) != allowed:
        reject('referent_requires_span_and_other_kinds_exclude_it')
    if kind == 'execution_detail':
        if ref is not None:
            reject('execution_detail_has_no_alignment_target')
        scope = 'execution'
    else:
        if not isinstance(ref, str) or ref not in registry:
            reject('alignment_dependency_requires_source_target')
        if not isinstance(item.get('evidence'), list) or {'ref': ref} not in item['evidence']:
            reject('alignment_target_must_be_cited')
        if kind in POSITION_DEPENDENCIES and ref in unknown_refs:
            reject('alignment_requires_affected_premise_not_open_topic')
        if kind == 'referent':
            span = dependency['referent_span']
            if (not isinstance(span, str) or not span.strip() or len(span) > 160
                    or span not in registry[ref]['quote']):
                reject('referent_span_requires_exact_target_substring')
        scope = 'execution' if kind == 'execution_assumption' else 'alignment'
    return {**{k:v for k,v in item.items() if k != 'dependency'}, 'scope': scope}
