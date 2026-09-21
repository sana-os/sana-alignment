"""Capability vs identity contracts; controlled labels do not prove model accuracy."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest
from app.models import AlignRequest
from app.provider import Provider, ProviderError, resolve_references
from scripts.diagnose_provider_output_v13 import diagnose
from test_alignment import SETTINGS, draft, model_json

OBSERVED = json.loads((Path(__file__).parent/'fixtures/observed-0.5.8-stage04-diagnostic.json').read_text())
CAPABILITY = OBSERVED['result']['view']['premise_gaps'][0]['ai_premise']
REGISTRY = {'a':{'source':'ai_interpretation','quote':CAPABILITY},
            'h':{'source':'input_message','quote':'Send the file to them.'}}

def item(kind, target, span=None):
    dep = {'kind':kind,'target_ref':target}
    if span is not None:
        dep['referent_span'] = span
    return {'statement':REGISTRY[target]['quote'],'evidence':[{'ref':target}],
            'question':None,'dependency':dep}

def test_observed_referent_label_lacks_identity_witness():
    assert OBSERVED['application_version'] == '0.5.8'
    decision = OBSERVED['scope_decisions'][-1]['dependency']
    assert decision == {'kind':'referent','target_ref':'q10'}
    with pytest.raises(ProviderError, match='provider_invalid_scope_dependency'):
        resolve_references({'unresolved':[item('referent','a')]},REGISTRY)

def test_execution_assumption_preserves_both_alternatives_and_source():
    out = resolve_references({'unresolved':[item('execution_assumption','a')]},REGISTRY)['unresolved'][0]
    assert out['scope'] == 'execution'
    assert out['evidence'] == [REGISTRY['a']]
    assert ' or ' in out['statement']
    assert 'dependency' not in out

@pytest.mark.parametrize('kind,target,span', [('referent','h','them'),('authority','h',None)])
def test_genuine_alignment_dependencies_remain_available(kind,target,span):
    out = resolve_references({'unresolved':[item(kind,target,span)]},REGISTRY)['unresolved'][0]
    assert out['scope'] == 'alignment'

@pytest.mark.parametrize('span', ['', ' ', 'they', 'x'*161, 7])
def test_referent_requires_bounded_literal_span(span):
    with pytest.raises(ProviderError,match='provider_invalid_scope_dependency'):
        resolve_references({'unresolved':[item('referent','h',span)]},REGISTRY)

def test_other_categories_cannot_carry_identity_witness():
    with pytest.raises(ProviderError,match='provider_invalid_scope_dependency'):
        resolve_references({'unresolved':[item('authority','h','them')]},REGISTRY)

def test_execution_assumption_cannot_be_disguised_as_missing_gap():
    g = {'kind':'missing_premise','blocks_execution':False,
         'human_premise':None,'ai_premise':'a','evidence':[{'ref':'a'},{'ref':'h'}],
         'verification_question':None,'dependency':{'kind':'execution_assumption','target_ref':'a'}}
    with pytest.raises(ProviderError,match='provider_invalid_gap_dependency'):
        resolve_references({'premise_gaps':[g]},REGISTRY)

@pytest.mark.parametrize('kind,text,span,expected', [
    ('execution_assumption', CAPABILITY, None, 'mapped'),
    ('referent', 'Send the file to them.', 'them', 'needs_clarification'),
    ('authority', 'Approval to disclose this file has not been established.', None, 'needs_clarification'),
])
def test_provider_and_diagnostic_preserve_capability_identity_and_authority(kind,text,span,expected):
    req = AlignRequest(input_message='Review the supplied plan.', ai_interpretation=text)
    evidence = {'source':'ai_interpretation','quote':text}
    extraction = {'kind':'substantive','frameworks':[], 'evidence':[{**evidence,'function':'assumption'}]}
    d = draft(unknowns=[],unresolved=[{'statement':text,'scope':'execution',
        'evidence':[evidence],'question':None}])
    replies = [extraction,d]
    def respond(request):
        value = json.loads(model_json(request,replies.pop(0)))
        if 'view' in value:
            entry = value['view']['unresolved'][0]
            entry['dependency'] = {'kind':kind,'target_ref':entry['evidence'][0]['ref']}
            if span is not None:
                entry['dependency']['referent_span'] = span
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            report = await diagnose(req,Provider(SETTINGS,client),1)
        assert report['outcome'] == 'success'
        assert report['result']['status'] == expected
        assert report['scope_decisions'][0]['dependency']['kind'] == kind
        assert report['scope_decisions'][0]['dependency'].get('referent_span') == span
        assert not report['result']['meta']['execution_authorized']
    asyncio.run(run())
