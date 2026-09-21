"""Observed retry routing regression; controlled provider outputs only."""
import asyncio
import copy
import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from app.models import AlignRequest, Draft
from app.provider import Provider, ProviderError, generation_schema, resolve_references
from app.role_contract import POSITION_DEPENDENCIES
from scripts.diagnose_provider_output_v13 import diagnose
from test_alignment import SETTINGS, model_json

ROOT=Path(__file__).parent/'fixtures'
OBSERVED=json.loads((ROOT/'observed-0.5.12-stage04-diagnostic.json').read_text())
REQUEST=AlignRequest.model_validate_json((ROOT/'stage04.en.json').read_text())
REGISTRY={r['ref']:{'source':r['source'],'quote':r['quote']} for r in OBSERVED['reference_review']}
UNKNOWNS=[r['ref'] for r in OBSERVED['reference_review'] if r['explicit_unknown']]


def wire_item(kind='constraint_scope',target='q10'):
    return {'statement':REGISTRY['q10']['quote'],'question':None,
            'evidence':[{'ref':target}], 'dependency':{'kind':kind,'target_ref':target}}


@pytest.mark.parametrize('kind',POSITION_DEPENDENCIES)
@pytest.mark.parametrize('target',UNKNOWNS)
def test_open_topic_is_not_an_affected_position(kind,target):
    item=wire_item(kind,target);before=copy.deepcopy(item)
    with pytest.raises(ProviderError) as error:
        resolve_references({'unresolved':[item]},REGISTRY,unknown_refs=UNKNOWNS)
    assert error.value.code=='provider_invalid_scope_dependency'
    assert error.value.issue['rule']=='alignment_requires_affected_premise_not_open_topic'
    assert item==before  # do not relocate, relabel or discard a rejected item


def test_unknown_is_preserved_with_genuine_constraint_scope_target():
    registry={'h':{'source':'input_message','quote':'Do not disclose confidential information.'},
              'u':{'source':'ai_interpretation','quote':'Which information is confidential is unspecified.'}}
    item={'statement':registry['u']['quote'],'question':None,
          'evidence':[{'ref':'h'},{'ref':'u'}],
          'dependency':{'kind':'constraint_scope','target_ref':'h'}}
    out=resolve_references({'unresolved':[item]},registry,unknown_refs=['u'])['unresolved'][0]
    assert out['scope']=='alignment'
    assert out['evidence']==list(registry.values())


@pytest.mark.parametrize('kind,text,span',[
    ('referent','Who is meant by "them"?','them'),
    ('authority','Who can authorize disclosure of this file is unknown.',None)])
def test_identity_and_authority_unknowns_are_not_forced_to_execution(kind,text,span):
    registry={'u':{'source':'input_message','quote':text}}
    dependency={'kind':kind,'target_ref':'u'}
    if span is not None:
        dependency['referent_span']=span
    item={'statement':text,'question':None,'evidence':[{'ref':'u'}],'dependency':dependency}
    out=resolve_references({'unresolved':[item]},registry,unknown_refs=['u'])['unresolved'][0]
    assert out['scope']=='alignment' and out['evidence']==[registry['u']]


def test_schema_offers_affected_positions_and_keeps_unknowns_as_evidence():
    payload={'input_message':REQUEST.input_message,'ai_interpretation':REQUEST.ai_interpretation,
             '_evidence_index':REGISTRY,'_unknown_evidence_refs':UNKNOWNS}
    schema=generation_schema(Draft,payload)
    dep=schema['$defs']['UnresolvedPremise']['properties']['dependency']
    position_branch=next(b for b in dep['oneOf'] if 'constraint_scope' in b['properties']['kind'].get('enum',[]))
    assert set(position_branch['properties']['target_ref']['enum']).isdisjoint(UNKNOWNS)
    assert set(UNKNOWNS)<=set(schema['$defs']['Evidence']['properties']['ref']['enum'])
    other=next(b for b in dep['oneOf'] if 'authority' in b['properties']['kind'].get('enum',[]))
    assert set(UNKNOWNS)<=set(other['properties']['target_ref']['enum'])


def observed_mapping(request,routing='observed',mixed_fact=False):
    # Reconstruct the relevant mapping fields from the public result. The original
    # raw Draft was not retained; do not present this as an exact model replay.
    result=OBSERVED['result'];view=result['view']
    d={'kind':'mapped','fact':copy.deepcopy(result['fact']),
       'care':[{k:v for k,v in p.items() if k!='execution_effect'} for p in result['care']],
       'view':{k:copy.deepcopy(view[k]) for k in ('premises','hypotheses','premise_gaps','unresolved')}}
    d['view']['understanding']={'evidence':view['understanding_evidence'][:3]}
    if mixed_fact:
        d['fact'].append({**result['fact'][0],'statement':REGISTRY['q5']['quote'],
                          'source':'provided_source','evidence':[REGISTRY['q5']]})
    value=json.loads(model_json(request,d))
    for i,item in enumerate(value['view']['unresolved']):
        item['dependency']=(copy.deepcopy(OBSERVED['scope_decisions'][i]['dependency'])
            if routing=='observed' else {'kind':'execution_detail','target_ref':None})
    return value


def run_sequence(replies):
    calls=[]
    def respond(request):
        body=json.loads(request.content);payload=json.loads(body['messages'][1]['content'])
        calls.append((body['messages'][0]['content'],payload))
        if '_extraction_index' in payload:
            content=model_json(request,{'kind':'substantive','frameworks':[],
                                       'evidence':OBSERVED['extracted_clauses']})
        else:
            assert payload['_evidence_index']==REGISTRY
            content=json.dumps(replies.pop(0)(request))
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':content}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            return await diagnose(REQUEST,Provider(replace(SETTINGS,mapping_retries=1),client),1)
    return asyncio.run(run()),calls


def test_observed_scope_error_is_repaired_without_removing_open_topics():
    report,calls=run_sequence([observed_mapping,lambda r:observed_mapping(r,'execution')])
    assert report['outcome']=='success' and report['retry_count']==1
    assert report['mapping_attempts'][0]['error']['issue']['rule']=='alignment_requires_affected_premise_not_open_topic'
    assert len(report['mapping_attempts'][0]['error']['violations'])==3
    assert report['mapping_attempts'][0]['scope_decisions'][0]['target_is_explicit_unknown'] is True
    assert report['mapping_attempts'][1]['scope_decisions'][0]['target_is_explicit_unknown'] is False
    result=report['result']
    assert [u['scope'] for u in result['view']['unresolved']]==['execution']*3
    assert [u['evidence'] for u in result['view']['unresolved']]==[u['evidence'] for u in OBSERVED['result']['view']['unresolved']]
    assert result['fact']==OBSERVED['result']['fact']
    assert result['care']==OBSERVED['result']['care']
    assert not result['meta']['execution_authorized']
    assert len(calls)==3
    assert calls[1][1]=={k:v for k,v in calls[2][1].items() if k!='_mapping_feedback'}
    # Exercise actual transmitted context/guidance, not a label-changing heuristic.
    assert 'reported as actually holding' in calls[0][0]
    assert 'Assumptions' in calls[0][0] and 'Operator / Test result:' in calls[0][0]
    assert any('### 2. Assumptions' in path for c in calls[0][1]['_excerpt_context'].values() for path in c['heading_paths'])


def test_initial_fact_error_then_scope_regression_is_rejected_at_retry_limit():
    report,calls=run_sequence([lambda r:observed_mapping(r,'execution',mixed_fact=True),observed_mapping])
    assert report['mapping_attempts'][0]['error']['code']=='provider_non_factual_evidence'
    assert report['error']['code']=='provider_invalid_scope_dependency'
    assert report['mapping_attempts'][1]['retry_decision']=='limit_reached'
    assert report['outcome']=='provider_error' and 'result' not in report
    assert report['retry_count']==1 and len(calls)==3
