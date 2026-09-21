"""Controlled routing checks, not a live-model accuracy claim."""
import copy
import json
from pathlib import Path

import pytest
from app.provider import ProviderError, resolve_references, generation_schema
from app.models import Draft

REGISTRY = {
    'h': {'source': 'input_message', 'quote': 'Display fictional records. Do not use real data.'},
    'u': {'source': 'ai_interpretation', 'quote': 'The record count is unspecified.'},
    'a': {'source': 'ai_interpretation', 'quote': 'Use the production database.'},
}

def gap(kind='missing_premise', target='u'):
    result = dict(kind=kind, blocks_execution=False, human_premise=None,
                  ai_premise=target, evidence=[{'ref':'h'}, {'ref':target}],
                  verification_question=None)
    if kind == 'missing_premise':
        result['dependency'] = {'kind':'comparison_assumption', 'target_ref':target}
    return result

@pytest.mark.parametrize('kind', ['missing_premise','interpretation_difference','constraint_conflict'])
def test_unknown_alone_cannot_be_relabelled_as_comparison(kind):
    with pytest.raises(ProviderError, match='provider_invalid_gap_dependency'):
        resolve_references({'premise_gaps':[gap(kind)]}, REGISTRY, unknown_refs=['u'])

def test_execution_unknown_is_retained_with_original_evidence():
    item = {'statement':'The record count is unspecified.', 'question':None,
            'evidence':[{'ref':'u'}], 'dependency':{'kind':'execution_detail','target_ref':None}}
    result = resolve_references({'unresolved':[item]}, REGISTRY)
    assert result['unresolved'][0]['scope'] == 'execution'
    assert result['unresolved'][0]['evidence'] == [REGISTRY['u']]

@pytest.mark.parametrize('edit', [
    {'dependency':{'kind':'execution_detail','target_ref':None}},
    {'dependency':{'kind':'comparison_assumption','target_ref':'h'}},
    {'dependency':None},
])
def test_bad_missing_dependency_is_rejected_without_rerouting(edit):
    item = {**gap(target='a'), **edit}
    original = copy.deepcopy(item)
    with pytest.raises(ProviderError):
        resolve_references({'premise_gaps':[item]}, REGISTRY)
    assert item == original

def test_consequential_one_sided_choice_and_real_conflict_survive():
    missing = gap(target='a')
    result = resolve_references({'premise_gaps':[missing]}, REGISTRY)['premise_gaps'][0]
    assert result['human_premise'] is None
    assert result['ai_premise'] == REGISTRY['a']['quote']
    assert 'dependency' not in result
    conflict = gap('constraint_conflict', 'a')
    conflict.update(human_premise='h', blocks_execution=True)
    result = resolve_references({'premise_gaps':[conflict]}, REGISTRY)['premise_gaps'][0]
    assert result['blocks_execution'] and result['kind'] == 'constraint_conflict'

def test_observed_routing_failure_remains_reproducible():
    p = json.loads((Path(__file__).parent/'fixtures/observed-0.5.7-stage04-diagnostic.json').read_text())
    assert p['result']['request_id'] == 'f948475d-33ad-4fe8-9c21-f096d5e77cef'
    assert not p['scope_decisions'] and not p['result']['view']['unresolved']
    refs = {x['ref']:{'source':x['source'],'quote':x['quote']} for x in p['reference_review']}
    unknowns = [x['ref'] for x in p['reference_review'] if x['explicit_unknown']]
    for old in p['result']['view']['premise_gaps']:
        target = next(r for r in unknowns if refs[r]['quote'] == old['ai_premise'])
        human = next(r for r,e in refs.items() if e['source']=='input_message')
        item = {**gap(target=target), 'evidence':[{'ref':human},{'ref':target}]}
        with pytest.raises(ProviderError, match='provider_invalid_gap_dependency'):
            resolve_references({'premise_gaps':[item]}, refs, unknown_refs=unknowns)

def test_schema_requires_missing_dependency_but_not_for_conflict():
    schema = generation_schema(Draft, {'_evidence_index':REGISTRY,
        '_unknown_evidence_refs':['u'], 'input_message':REGISTRY['h']['quote'],
        'ai_interpretation':REGISTRY['a']['quote']})
    condition = schema['$defs']['Gap']['allOf'][0]
    assert condition['then']['required'] == ['dependency']
    assert 'u' not in schema['$defs']['Gap']['properties']['dependency']['properties']['target_ref']['enum']

@pytest.mark.parametrize('as_gap', [False, True])
def test_real_provider_path_reports_routing_and_never_grants_authority(as_gap):
    import asyncio
    import httpx
    from app.models import AlignRequest
    from app.provider import Provider
    from scripts.diagnose_provider_output_v13 import diagnose
    from test_alignment import SETTINGS, draft, model_json
    req = AlignRequest(input_message=REGISTRY['h']['quote'], ai_interpretation=REGISTRY['u']['quote'])
    extraction = {'kind':'substantive','frameworks':[], 'evidence':[
        {**REGISTRY['u'], 'function':'unknown'}]}
    if as_gap:
        item = gap()
        item.pop('dependency')
        item.update(ai_premise=req.ai_interpretation, difference='Unused mock text.',
                    evidence=[REGISTRY['h'], REGISTRY['u']])
        d = draft(unknowns=[], premise_gaps=[item])
    else:
        d = draft(unknowns=[], unresolved=[{'statement':req.ai_interpretation,
            'scope':'execution','evidence':[REGISTRY['u']], 'question':None}])
    replies = [extraction,d]
    def respond(request):
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop',
            'message':{'content':model_json(request,replies.pop(0))}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            report = await diagnose(req,Provider(SETTINGS,client),1)
        assert report['diagnostic_version'] == 'provider-output-13'
        if as_gap:
            assert report['outcome'] == 'provider_error'
            assert report['error']['code'] == 'provider_invalid_gap_dependency'
            assert report['scope_decisions'][0]['path'] == 'view.premise_gaps.0'
        else:
            assert report['outcome'] == 'success'
            assert report['result']['view']['unresolved'][0]['scope'] == 'execution'
            assert report['result']['status'] == 'mapped'
            assert not report['result']['meta']['execution_authorized']
    asyncio.run(run())
