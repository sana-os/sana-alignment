"""Full provider/engine recovery tests; controlled outputs, no live-model claim."""
import asyncio
import copy
import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from app.engine import align
from app.main import create_app
from app.models import AlignRequest, Draft
from app.provider import Provider, ProviderError, Settings
from scripts.diagnose_provider_output_v13 import diagnose
from test_alignment import SETTINGS, Stub, draft, intake, model_json, premise

FIXTURES = Path(__file__).parent / 'fixtures'
OBSERVED = json.loads((FIXTURES/'observed-0.5.11-stage04-diagnostic.json').read_text())
REQUEST = AlignRequest.model_validate_json((FIXTURES/'stage04.en.json').read_text())
SETTINGS_RETRY = replace(SETTINGS, mapping_retries=1)


def stage4_candidate(request, mixed=False, missing_dependency=False):
    """Reproduce observed violations, not an unavailable complete raw Draft."""
    payload = json.loads(json.loads(request.content)['messages'][1]['content'])
    registry = payload['_evidence_index']
    out = draft(unknowns=[], premises=[premise(statement=registry[r]['quote'],
        source='provided_source', evidence=[registry[r]]) for r in ('q7','q8','q9')],
        unresolved=[{'statement':registry[r]['quote'], 'scope':'execution',
            'evidence':[registry[r]], 'question':None} for r in ('q10','q11','q12')])
    out['fact'] = [premise(statement=registry['q2']['quote'], evidence=[registry['q2']])]
    if mixed:
        out['fact'].append(premise(statement=registry['q5']['quote'],
            source='provided_source', evidence=[registry['q5']]))
    out['care'] = [{k:v for k,v in premise(statement=registry[r]['quote'],
        support_state='not_applicable', evidence=[registry[r]]).items() if k != 'execution_effect'}
        for r in ('q3','q4')]
    value = json.loads(model_json(request,out))
    if missing_dependency:
        value['view']['premise_gaps'] = [{'kind':'missing_premise','blocks_execution':False,
            'human_premise':'q3','ai_premise':r, 'verification_question':None,
            'evidence':[{'ref':'q3'},{'ref':r}]} for r in ('q7','q8','q9')]
    return value


def stage4_transport(mapping_replies):
    seen = []
    def respond(request):
        body = json.loads(request.content)
        payload = json.loads(body['messages'][1]['content'])
        seen.append((body['messages'][0]['content'], payload))
        if '_extraction_index' in payload:
            content = model_json(request, {'kind':'substantive','frameworks':[],
                                          'evidence':OBSERVED['extracted_clauses']})
        else:
            reply = mapping_replies.pop(0)
            if isinstance(reply, httpx.Response):
                return reply
            content = json.dumps(reply(request))
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':content}}]})
    return httpx.MockTransport(respond), seen


def test_observed_failures_are_reported_together_and_repaired_once():
    transport, seen = stage4_transport([
        lambda r:stage4_candidate(r, mixed=True, missing_dependency=True), stage4_candidate])
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await diagnose(REQUEST,Provider(SETTINGS_RETRY,client),1)
    report = asyncio.run(run())
    assert report['outcome']=='success' and report['retry_count']==1
    assert report['model_call_count']==3
    assert [a['outcome'] for a in report['mapping_attempts']]==['provider_error','success']
    assert report['mapping_attempts'][0]['candidate_review']['source_counts']['fact']==2
    assert report['mapping_attempts'][1]['candidate_review']['source_counts']['fact']==1
    assert report['mapping_attempts'][0]['error']['code']=='provider_invalid_scope_dependency'
    issues=report['mapping_attempts'][0]['error']['violations']
    assert len(issues)==4
    assert {i['code'] for i in issues}=={'provider_invalid_scope_dependency','provider_non_factual_evidence'}
    first, second = seen[1][1], copy.deepcopy(seen[2][1])
    assert second.pop('_mapping_feedback')['violations']==issues
    assert second==first  # source, registry, extraction, attribution all unchanged
    assert 'MAPPING CORRECTION ATTEMPT' in seen[2][0]
    result=report['result']
    assert len(result['fact'])==1 and len(result['care'])==2
    assert [u['scope'] for u in result['view']['unresolved']]==['execution']*3
    assert result['meta']['execution_authorized'] is False
    assert all('elapsed_seconds' in a for a in report['mapping_attempts'])


def test_engine_validation_is_inside_retry_and_second_failure_never_returns_result():
    transport,seen=stage4_transport([lambda r:stage4_candidate(r,mixed=True)]*2)
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await diagnose(REQUEST,Provider(SETTINGS_RETRY,client),1)
    report=asyncio.run(run())
    assert report['error']['code']=='provider_non_factual_evidence'
    assert report['completed_stages']==['Extraction']
    assert len(seen)==3 and 'result' not in report and 'support_review' not in report
    assert report['mapping_attempts'][1]['retry_decision']=='limit_reached'
    assert all(a['error']['code']=='provider_non_factual_evidence' for a in report['mapping_attempts'])


def test_retry_can_be_disabled_without_extra_call():
    transport,seen=stage4_transport([lambda r:stage4_candidate(r,missing_dependency=True)])
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await diagnose(REQUEST,Provider(SETTINGS,client),1)
    report=asyncio.run(run())
    assert report['retry_count']==0 and len(seen)==2
    assert report['outcome']=='provider_error'


@pytest.mark.parametrize('code,status', [
    ('provider_timeout',504),('provider_rate_limited',503),('provider_unavailable',503),
    ('provider_http_error',502),('provider_incomplete_or_refused',502),
    ('provider_response_too_large',502)])
def test_non_output_failures_never_retry(code,status):
    class Fails(Stub):
        async def generate(self,instruction,payload,schema):
            if schema is Draft:
                self.calls.append((instruction,payload))
                raise ProviderError(code,status)
            return await super().generate(instruction,payload,schema)
    p=Fails(intake());attempts=[]
    with pytest.raises(ProviderError,match=code):
        asyncio.run(align(AlignRequest(input_message='Check the plan.'),p,
                          mapping_retries=1,mapping_attempts=attempts))
    assert len(p.calls)==2 and attempts[0]['retry_decision']=='not_repairable'


def test_extraction_failure_is_not_retried():
    class Fails:
        calls=0
        async def generate(self,*args):
            self.calls+=1
            raise ProviderError('provider_invalid_output')
    p=Fails();attempts=[]
    with pytest.raises(ProviderError):
        asyncio.run(align(AlignRequest(input_message='Check.'),p,
                          mapping_retries=1,mapping_attempts=attempts))
    assert p.calls==1 and not attempts


def test_http_retry_preserves_real_constraint_conflict():
    req=AlignRequest(input_message='Do not use real data.',ai_interpretation='Use the production database.')
    d=draft(unknowns=[],premise_gaps=[{
        'kind':'constraint_conflict','blocks_execution':True,
        'human_premise':req.input_message,'ai_premise':req.ai_interpretation,
        'difference':'unused','verification_question':None,
        'evidence':[{'source':'input_message','quote':req.input_message},
                    {'source':'ai_interpretation','quote':req.ai_interpretation}]}])
    replies=[intake(),None,d];calls=[]
    def respond(request):
        calls.append(request)
        value=replies.pop(0)
        content='{invalid' if value is None else model_json(request,value)
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':content}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app=create_app(SETTINGS_RETRY,Provider(SETTINGS_RETRY,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    result=await api.post('/v1/align',json=req.model_dump())
        assert result.status_code==200
        assert result.json()['status']=='revision_required'
        assert result.json()['meta']['execution_authorized'] is False
    asyncio.run(run());assert len(calls)==3


def test_total_budget_cancels_retry_and_records_both_attempts(monkeypatch):
    # Scale only the diagnostic clock budget for the test; exercise actual cancellation.
    from scripts import diagnose_provider_output_v13 as diagnostic
    original_timeout=asyncio.timeout
    monkeypatch.setattr(diagnostic.asyncio,'timeout',lambda seconds: original_timeout(0.03))
    class Slow(Stub):
        settings=SETTINGS_RETRY
        mapping_calls=0
        async def generate(self,instruction,payload,schema):
            if schema is Draft:
                self.mapping_calls+=1
                if self.mapping_calls==1:
                    raise ProviderError('provider_invalid_output')
                await asyncio.Event().wait()
            return await super().generate(instruction,payload,schema)
    p=Slow(intake())
    report=asyncio.run(diagnose(AlignRequest(input_message='Check the plan.'),p,1))
    assert report['error']['code']=='alignment_timeout' and 'result' not in report
    assert report['mapping_attempts'][1]['outcome']=='cancelled'
    assert report['mapping_attempts'][0]['error']['code']=='provider_invalid_output'
    assert p.mapping_calls==2


@pytest.mark.parametrize('raw,valid', [('0',True),('1',True),('2',False),('-1',False),('true',False)])
def test_retry_setting_is_bounded(monkeypatch,raw,valid):
    monkeypatch.setenv('LLM_MODEL','test');monkeypatch.setenv('SANA_MAPPING_RETRIES',raw)
    if valid:
        assert Settings.from_env().mapping_retries==int(raw)
    else:
        with pytest.raises(ValueError,match='SANA_MAPPING_RETRIES'):
            Settings.from_env()


def test_success_and_handshake_do_not_add_calls():
    p=Stub(intake(),draft(unknowns=[]));attempts=[]
    asyncio.run(align(AlignRequest(input_message='Check.'),p,mapping_retries=1,mapping_attempts=attempts))
    assert len(p.calls)==2 and len(attempts)==1
    p=Stub()
    result=asyncio.run(align(AlignRequest(input_message='Hello'),p,mapping_retries=1))
    assert result.status=='handshake' and not p.calls


def test_concurrent_requests_do_not_share_feedback_or_attempts():
    class PerRequest:
        seen=[]
        async def generate(self,instruction,payload,schema):
            await asyncio.sleep(0)
            if schema is not Draft:
                return schema.model_validate(intake())
            self.seen.append((payload['input_message'],copy.deepcopy(payload.get('_mapping_feedback'))))
            if payload['input_message']=='Fails first' and '_mapping_feedback' not in payload:
                raise ProviderError('provider_invalid_output')
            return schema.model_validate(draft(unknowns=[]))
    p=PerRequest();a=[];b=[]
    async def run():
        await asyncio.gather(
            align(AlignRequest(input_message='Fails first'),p,mapping_retries=1,mapping_attempts=a),
            align(AlignRequest(input_message='Succeeds first'),p,mapping_retries=1,mapping_attempts=b))
    asyncio.run(run())
    assert len(a)==2 and len(b)==1
    assert all(feedback is None for text,feedback in p.seen if text=='Succeeds first')
