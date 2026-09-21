"""Observed two-attempt failure shapes; raw candidates were not retained.

Reconstruct source references from the known input and verify hashes. Construct
controlled candidates to exercise recorded violations, not verbatim model replays.
"""
import asyncio
import copy
import json
from pathlib import Path
from dataclasses import replace
import httpx
import pytest
from app.main import create_app
from app.models import AlignRequest
from app.extraction_refs import extraction_index
from app.provider import Provider, ProviderError, resolve_references
from app.repair_feedback import repair_contract
from app.run_trace import digest
from test_alignment import SETTINGS, model_json, premise, draft

FIX=Path(__file__).parent/'fixtures'
OBSERVED=json.loads((FIX/'observed-0.5.14-stage04-medium-trace.json').read_text())
REQUEST=AlignRequest.model_validate_json((FIX/'stage04.en.json').read_text()).model_copy(update={'processing_mode':'medium'})
INDEX=extraction_index(REQUEST.model_dump(exclude={'processing_mode'}))
EXTRACTION={'kind':'substantive','frameworks':[], 'evidence':[
    {**INDEX[e['ref']], 'function':e['function']} for e in OBSERVED['model_calls'][0]['extraction_labels']]}


def candidate(request,variant):
    payload=json.loads(json.loads(request.content)['messages'][1]['content'])
    registry=payload['_evidence_index']
    for ref,entry in registry.items():
        assert digest(entry['quote'])==OBSERVED['model_calls'][1]['reference_labels'][ref]['quote_sha256']
    fact_refs=['q2','q5']+(['q6'] if variant=='initial' else [])
    d=draft(unknowns=[],premises=[premise(statement=registry[ref]['quote'],source='provided_source',
            support_state='provided',evidence=[registry[ref]]) for ref in ('q8','q9')])
    d['fact']=[premise(statement=registry[ref]['quote'],source='user_explicit' if ref=='q2' else 'provided_source',
                     support_state='provided',evidence=[registry[ref]]) for ref in fact_refs]
    d['care']=[{k:v for k,v in premise(statement=registry[ref]['quote'],
        source='user_explicit' if ref in ('q3','q4') else 'provided_source',
        evidence=[registry[ref]]).items() if k!='execution_effect'} for ref in ('q3','q4','q6','q7','q10')]
    value=json.loads(model_json(request,d))
    if variant=='initial':
        value['view']['premise_gaps']=[{'kind':'interpretation_difference','blocks_execution':False,
            'human_premise':'q3' if ref in ('q8','q9','q10') else None,
            'ai_premise':ref,'verification_question':None,
            'evidence':[{'ref':'q3'},{'ref':ref}]} for ref in ('q8','q9','q10','q12','q13','q14')]
    else:
        value['view']['unresolved']=[{'statement':registry[ref]['quote'],
            'evidence':[{'ref':ref}],'question':None,
            'dependency':({'kind':'execution_detail','target_ref':None} if variant=='valid'
                else {'kind':kind,'target_ref':ref})}
            for ref,kind in [('q12','constraint_scope'),('q13','goal_meaning'),('q14','constraint_scope')]]
    return value


def run_sequence(tmp_path,variants):
    seen=[]
    def respond(request):
        body=json.loads(request.content);payload=json.loads(body['messages'][1]['content']);seen.append(payload)
        content=(model_json(request,EXTRACTION) if '_extraction_index' in payload
                 else json.dumps(candidate(request,variants.pop(0))))
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':content}}]})
    settings=replace(SETTINGS,mapping_retries=1,trace_level='metadata',trace_dir=str(tmp_path))
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app=create_app(settings,Provider(settings,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    return await api.post('/v1/align',json=REQUEST.model_dump())
    response=asyncio.run(run())
    trace=json.loads(next(tmp_path.glob('trace-*.json')).read_text())
    return response,trace,seen


def test_observed_second_failure_is_still_rejected_at_medium_limit(tmp_path):
    response,trace,seen=run_sequence(tmp_path,['initial','bad_scope'])
    assert response.status_code==502 and len(seen)==3
    attempts=trace['mapping_attempts']
    assert attempts[0]['error']['code']=='provider_invalid_gap_dependency'
    assert len(attempts[0]['error']['violations'])==4
    assert attempts[1]['error']['code']=='provider_invalid_scope_dependency'
    assert len(attempts[1]['error']['violations'])==3
    assert attempts[1]['retry_decision']=='limit_reached' and trace['retry_count']==1
    assert 'result' not in trace
    assert trace['limits']['model_calls']==3


def test_correction_sees_specific_refs_and_explicit_forms_without_source_mutation(tmp_path):
    response,trace,seen=run_sequence(tmp_path,['initial','valid'])
    assert response.status_code==200 and len(seen)==3
    before,after=seen[1],copy.deepcopy(seen[2]);feedback=after.pop('_mapping_feedback')
    assert before==after
    contract=feedback['repair_contract']
    assert contract==trace['mapping_attempts'][0]['error']['repair_contract']
    refs={r['ref']:r for r in contract['references_in_violations']}
    assert refs['q6']['extraction_function']=='concern' and not refs['q6']['fact_reference_allowed']
    for ref in ('q12','q13','q14'):
        assert refs[ref]['extraction_function']=='unknown'
        assert not refs[ref]['position_dependency_target_allowed']
    form=contract['unresolved_forms']['implementation_detail']['fixed_fields']
    assert form=={'dependency':{'kind':'execution_detail','target_ref':None},'question':None}
    assert contract['required_comparison_fields']=={'view.hypotheses':[]}
    value=response.json()
    assert len(value['care'])==5 # human + explicitly source-labelled AI concerns preserved
    assert value['care'][0]['source']=='user_explicit' and value['care'][2]['source']=='provided_source'
    assert len(value['view']['unresolved'])==3 and {u['scope'] for u in value['view']['unresolved']}=={'execution'}
    assert value['meta']['execution_authorized'] is False
    assert REQUEST.input_message not in json.dumps(trace) and 'secret-key' not in json.dumps(trace)


def contract_payload():
    return {'input_message':'Do not disclose confidential material.',
        '_evidence_index':{'q0':{'source':'input_message','quote':'Do not disclose confidential material.'},
                           'q1':{'source':'ai_interpretation','quote':'The relevant fields are unspecified.'}},
        '_evidence_functions':{'q0':'concern','q1':'unknown'},
        '_unknown_evidence_refs':['q1'],'_non_fact_evidence_refs':['q0','q1']}


@pytest.mark.parametrize('kind', ['goal_meaning','constraint_scope','comparison_assumption','authority','referent','execution_assumption'])
def test_advertised_dependency_forms_keep_actual_alignment_and_execution_cases(kind):
    payload=contract_payload();error=ProviderError('provider_invalid_scope_dependency',
        violations=[{'evidence_refs':['q1']}])
    contract=repair_contract(error,payload)
    forms=contract['unresolved_forms']
    group=('affected_position' if kind in ('goal_meaning','constraint_scope','comparison_assumption')
           else 'implementation_assumption' if kind=='execution_assumption' else 'identity_or_authority')
    target='q0' if group=='affected_position' else 'q1'
    assert target in forms[group]['target_ref_options']
    dep={'kind':kind,'target_ref':target}
    if kind=='referent':dep['referent_span']='fields'
    item={'statement':'A topic to resolve.','question':None,'evidence':[{'ref':target}], 'dependency':dep}
    out=resolve_references({'unresolved':[item]},payload['_evidence_index'],unknown_refs=['q1'])
    assert out['unresolved'][0]['scope']==('execution' if kind=='execution_assumption' else 'alignment')
    assert 'q1' not in forms['affected_position']['target_ref_options']
    # This tests protocol compatibility only, not the semantic suitability of the sample wording.


def test_required_empty_hypotheses_is_specific_to_comparison():
    error=ProviderError('provider_invalid_output')
    p=contract_payload();assert 'required_comparison_fields' not in repair_contract(error,p)
    p['ai_interpretation']='An interpretation.'
    assert repair_contract(error,p)['required_comparison_fields']=={'view.hypotheses':[]}


def test_fake_reference_cannot_become_feedback_context_or_leak_text():
    p=contract_payload();before=copy.deepcopy(p)
    e=ProviderError('provider_invalid_output',violations=[{'evidence_refs':['q1','SECRET_VALUE','q1']}])
    contract=repair_contract(e,p)
    assert [r['ref'] for r in contract['references_in_violations']]==['q1']
    assert 'SECRET_VALUE' not in json.dumps(contract)
    assert p==before
