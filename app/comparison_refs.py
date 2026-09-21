"""Render comparison positions from cited originals, preserving alternatives."""


def resolve_comparison(gap, registry, human_sources, path, unknown_refs=()):
    from .provider import ProviderError

    def reject(code, field, rule):
        raise ProviderError(code, issue={'path': f'{path}.{field}', 'rule': rule})

    if not isinstance(gap, dict):
        reject('provider_invalid_comparison_reference', 'human_premise', 'select_cited_position_reference_or_null')
    if 'difference' in gap:
        reject('provider_unexpected_difference', 'difference', 'difference_is_server_rendered_from_positions')
    result = dict(gap)
    parts = [f"[{gap.get('kind', 'interpretation_difference')}]"]
    for field, allowed in (('human_premise', human_sources), ('ai_premise', {'ai_interpretation'})):
        if field not in gap:
            reject('provider_invalid_comparison_reference', field, 'select_cited_position_reference_or_null')
        ref = gap[field]
        if ref is None:
            result[field] = None
            parts.append(f'[{field}]\nnull')
            continue
        if not isinstance(ref, str) or ref not in registry:
            reject('provider_invalid_comparison_reference', field, 'select_cited_position_reference_or_null')
        evidence = gap.get('evidence')
        if not isinstance(evidence, list) or {'ref': ref} not in evidence:
            reject('provider_uncited_comparison_reference', field, 'position_must_cite_same_reference')
        selected = registry[ref]
        if selected['source'] not in allowed:
            reject('provider_invalid_comparison_source', field, 'position_reference_must_match_speaker')
        result[field] = selected['quote']
        parts.append(f"[{field}: {selected['source']}]\n{selected['quote']}")
    # Both-null and evidence validation remain the engine's responsibility.
    # An open topic alone is not a compared position. Preserve genuine conflicts
    # and one-sided choices; do not infer a role from wording or relocate items.
    selected = [gap.get(field) for field in ('human_premise', 'ai_premise')
                if gap.get(field) is not None]
    if not selected:
        raise ProviderError('provider_empty_premise_gap', issue={
            'path': path, 'rule': 'gap_requires_stated_premise'})
    if gap.get('kind') != 'missing_premise' and 'dependency' in gap:
        reject('provider_invalid_gap_dependency', 'dependency',
               'dependency_is_only_for_missing_premise')
    if selected and all(ref in unknown_refs for ref in selected):
        reject('provider_invalid_gap_dependency', 'ai_premise',
               'open_topics_alone_are_not_comparison_positions')
    if gap.get('kind') == 'missing_premise':
        from .role_contract import resolve_unresolved
        resolved = resolve_unresolved({
            'dependency': gap.get('dependency'), 'evidence': gap.get('evidence')},
            registry, f'{path}.dependency')
        target = gap['dependency']['target_ref']
        if resolved['scope'] == 'execution':
            reject('provider_invalid_gap_dependency', 'dependency',
                   'execution_detail_belongs_in_unresolved')
        if target not in selected or target in unknown_refs:
            reject('provider_invalid_gap_dependency', 'dependency',
                   'missing_premise_requires_affected_comparison_position')
        result.pop('dependency', None)
    # Do not shorten long quotes or synthesize an absent human position.
    result['difference'] = '\n\n'.join(parts)
    return result
