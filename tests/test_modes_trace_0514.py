import asyncio
import json
import os
from dataclasses import replace
from pathlib import Path
import uuid
import httpx
import pytest
from app.main import create_app
from app.models import AlignRequest
from app.provider import Provider, Settings
from app.run_trace import ACTIVE_TRACE, TraceStore
from app.corrections import append_correction
from test_alignment import SETTINGS, intake, draft, model_json
from test_mapping_retry_0512 import stage4_transport, stage4_candidate, REQUEST


def api_run(tmp_path, mode, replies, *, trace_level='metadata'):
    settings = replace(SETTINGS, mapping_retries=1, trace_level=trace_level, trace_dir=str(tmp_path))
    calls=[]
    def respond(request):
        body=json.loads(request.content);payload=json.loads(body['messages'][1]['content'])
        calls.append(payload)
        assert 'processing_mode' not in payload
        value=replies.pop(0)
        content=value if isinstance(value,str) else model_json(request,value)
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':content}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app=create_app(settings,Provider(settings,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    response=await api.post('/v1/align',json={'input_message':'PRIVATE input marker',
                        'processing_mode':mode})
        return response
    response=asyncio.run(run())
    records=list(tmp_path.glob('trace-*.json'))
    return response,calls,json.loads(records[0].read_text()) if records else None


@pytest.mark.parametrize('mode,errors,want_status,calls',[
    ('low',1,502,2),('medium',1,200,3),('medium',2,502,3),
    ('high',2,200,4),('high',3,502,4),('high',0,200,2)])
def test_modes_bound_calls_and_trace_all_results(tmp_path,mode,errors,want_status,calls):
    response,seen,trace=api_run(tmp_path,mode,[intake()]+['{invalid']*errors+[draft(unknowns=[])])
    assert response.status_code==want_status and len(seen)==calls
    assert trace['model_call_count']==calls
    assert trace['processing_mode']==mode and trace['limits']['total_seconds']==7
    assert trace['request_id']==response.headers['X-SANA-Request-ID']
    assert response.headers['X-SANA-Trace-Status']=='saved'
    assert trace['retry_count']==calls-2
    assert trace['execution_authorized'] is False
    serialized=json.dumps(trace)
    assert all(marker not in serialized for marker in ('PRIVATE input marker','secret-key','{invalid','Bearer'))
    assert trace['model_calls'][-1]['prompt_sha256']
    if want_status==200:
        assert response.json()['request_id']==trace['request_id']
        assert trace['mapping_attempts'][-1]['outcome']=='success'
    else:
        assert trace['mapping_attempts'][-1]['retry_decision']=='limit_reached'
        assert 'result' not in trace


def test_detail_records_original_and_rejected_candidate(tmp_path):
    response,seen,trace=api_run(tmp_path,'medium',[intake(),'{invalid',draft(unknowns=[])],trace_level='detail')
    assert trace['details']['request']['input_message']=='PRIVATE input marker'
    assert trace['details']['call_2_candidate']=='{invalid'
    assert trace['details']['result']['request_id']==trace['request_id']
    assert 'secret-key' not in json.dumps(trace)


def test_detail_budget_is_visible(tmp_path,monkeypatch):
    import app.run_trace as module
    monkeypatch.setattr(module,'MAX_DETAIL_BYTES',1)
    response,_,trace=api_run(tmp_path,'low',[intake(),draft(unknowns=[])],trace_level='detail')
    assert response.status_code==200 and response.headers['X-SANA-Trace-Status']=='saved_with_omissions'
    assert trace['details']=={} and 'request' in trace['detail_omissions']


def test_off_has_no_file(tmp_path):
    response,_,trace=api_run(tmp_path,'low',[intake(),draft(unknowns=[])],trace_level='off')
    assert response.headers['X-SANA-Trace-Status']=='off' and trace is None


def test_write_failure_is_visible_without_discarding_result(tmp_path,monkeypatch):
    def fails(*args,**kwargs):raise OSError('PRIVATE failure')
    monkeypatch.setattr(TraceStore,'write',fails)
    response,_,trace=api_run(tmp_path,'low',[intake(),draft(unknowns=[])])
    assert response.status_code==200 and response.headers['X-SANA-Trace-Status']=='failed'
    assert trace is None


@pytest.mark.parametrize('mode,count',[('low',0),('medium',1),('high',2)])
def test_env_mode_overrides_legacy_and_request_omission_uses_server(monkeypatch,tmp_path,mode,count):
    monkeypatch.setenv('LLM_MODEL','test');monkeypatch.setenv('SANA_PROCESSING_MODE',mode)
    monkeypatch.setenv('SANA_MAPPING_RETRIES','1')
    settings=Settings.from_env()
    assert settings.mapping_retries==count and settings.processing_mode==mode
    app=create_app(replace(settings,trace_dir=str(tmp_path)))
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        response=client.post('/v1/align',json={'input_message':'Hello'})
    trace=json.loads(next(tmp_path.glob('trace-*.json')).read_text())
    assert response.headers['X-SANA-Processing-Mode']==mode
    assert trace['model_call_count']==0 and trace['mapping_attempts']==[]


def test_invalid_mode_is_rejected_without_inference(tmp_path):
    response,seen,trace=api_run(tmp_path,'hige',[])
    assert response.status_code==422 and not seen and trace is None


def test_real_provider_trace_keeps_rejected_decisions_and_changed_refs(tmp_path):
    settings=replace(SETTINGS,mapping_retries=1,trace_level='metadata',trace_dir=str(tmp_path))
    transport,seen=stage4_transport([lambda r:stage4_candidate(r,mixed=True),stage4_candidate])
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            app=create_app(settings,Provider(settings,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    return await api.post('/v1/align',json=REQUEST.model_dump())
    result=asyncio.run(run()); assert result.status_code==200
    trace=json.loads(next(tmp_path.glob('trace-*.json')).read_text())
    first,second=trace['model_calls'][1:]
    assert first['outcome']=='parsed' # engine rejection is recorded separately
    assert trace['mapping_attempts'][0]['error']['code']=='provider_non_factual_evidence'
    assert first['reference_labels']['q5']['function']=='mixed'
    assert any(c['path']=='fact.1' for c in second['decision_changes'])
    assert REQUEST.input_message not in json.dumps(trace)


def test_metadata_masks_unrecognized_validation_paths(tmp_path):
    invalid=draft(unknowns=[]);invalid['PRIVATE_EXTRA_KEY']='othersecret'
    _,_,trace=api_run(tmp_path,'low',[intake(),invalid])
    assert 'PRIVATE_EXTRA_KEY' not in json.dumps(trace)
    assert '<field>' in json.dumps(trace)


def test_malformed_function_cannot_break_trace_hook(tmp_path):
    _,_,trace=api_run(tmp_path,'low',[{'kind':'substantive','frameworks':[],
        'evidence':[{'source':'input_message','quote':'PRIVATE input marker','function':[]}]}])
    assert trace['outcome']=='error' and trace['model_call_count']==1
    assert trace['error']['code']=='provider_invalid_output'


def test_concurrent_traces_keep_own_ids_and_calls(tmp_path):
    settings=replace(SETTINGS,trace_level='detail',trace_dir=str(tmp_path))
    async def respond(request):
        await asyncio.sleep(0)
        payload=json.loads(json.loads(request.content)['messages'][1]['content'])
        value=intake() if '_extraction_index' in payload else draft(unknowns=[])
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':model_json(request,value)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app=create_app(settings,Provider(settings,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    return await asyncio.gather(*[api.post('/v1/align',json={'input_message':s}) for s in ('Alpha task','Beta task')])
    results=asyncio.run(run());assert all(r.status_code==200 for r in results)
    traces=[json.loads(p.read_text()) for p in tmp_path.glob('trace-*.json')]
    assert len(traces)==2
    for t in traces:
        assert t['model_call_count']==2
        text=t['details']['request']['input_message']
        other='Beta task' if text=='Alpha task' else 'Alpha task'
        assert other not in json.dumps(t)
    assert ACTIVE_TRACE.get() is None


def test_total_deadline_cancels_inflight_call_and_is_saved(tmp_path,monkeypatch):
    import app.main as main
    original_timeout=asyncio.timeout
    monkeypatch.setattr(main.asyncio,'timeout',lambda _: original_timeout(0.02))
    settings=replace(SETTINGS,trace_level='metadata',trace_dir=str(tmp_path))
    async def respond(request):await asyncio.Event().wait()
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app=create_app(settings,Provider(settings,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    return await api.post('/v1/align',json={'input_message':'Check this task','processing_mode':'high'})
    response=asyncio.run(run())
    assert response.status_code==504
    trace=json.loads(next(tmp_path.glob('trace-*.json')).read_text())
    assert trace['error']['code']=='alignment_timeout' and trace['model_call_count']==1
    assert trace['model_calls'][0]['outcome']=='error'


def test_store_retention_and_corrections_preserve_original(tmp_path,monkeypatch):
    import app.run_trace as module
    store=TraceStore(tmp_path)
    expired=store.write({'request_id':str(uuid.uuid4())});os.utime(expired,(1,1))
    response,_,trace=api_run(tmp_path,'low',[intake(),draft(unknowns=[])])
    assert not expired.exists()
    original=tmp_path/f'trace-{trace["request_id"]}.json';before=original.read_bytes()
    record={'request_id':trace['request_id'],'field_path':'view.unresolved','proposed_change':'Retain a missing topic.',
        'basis':'The original plan lists this topic.','proposer':'human'}
    correction=append_correction(store,record)
    saved=json.loads(correction.read_text())
    assert saved['review_status']=='proposed' and saved['applied_to_original'] is False
    assert saved['execution_authorized'] is False and original.read_bytes()==before
    with pytest.raises(FileExistsError):store.write(trace)
    monkeypatch.setattr(module,'MAX_FILES',2)
    store.write({'request_id':str(uuid.uuid4())})
    assert len(list(tmp_path.glob('*.json')))==2


def test_correction_missing_original_or_reference_cannot_be_saved(tmp_path):
    record={'request_id':str(uuid.uuid4()),'field_path':'care.0','proposed_change':'Goal','basis':'Quote','proposer':'model'}
    store=TraceStore(tmp_path)
    with pytest.raises(FileNotFoundError):append_correction(store,record)
    store.write({'request_id':record['request_id']})
    with pytest.raises(ValueError,match='unknown_evidence_reference'):
        append_correction(store,{**record,'evidence_refs':['q999']})
