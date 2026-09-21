"""Contract tests, not claims about the model's classification accuracy."""
import asyncio
import copy
import json
from pathlib import Path
import httpx
import pytest
from test_alignment import SETTINGS, Stub, call, draft, intake, premise, model_json
from app.engine import overview_evidence
from app.main import create_app
from app.models import AlignRequest, Draft, Evidence
from app.provider import Provider, ProviderError, generation_schema, resolve_references

ROOT = Path(__file__).resolve().parent.parent
OBSERVED = json.loads((ROOT/'tests/fixtures/observed-0.4.4-excerpts.json').read_text())
REQUEST = json.loads((ROOT/OBSERVED['request_fixture']).read_text())

def mapped_draft(effect='omitted'):
    d = draft(unknowns=[])
    p = premise(statement=REQUEST['ai_interpretation'],source='provided_source',
        support_state='provided',evidence=[dict(source='ai_interpretation',quote=REQUEST['ai_interpretation'])])
    p.pop('execution_effect')
    if effect != 'omitted': p['execution_effect'] = effect
    d['view']['premises'] = [p]
    return d

@pytest.mark.parametrize('effect', ['omitted',None])
def test_effect_defaults_to_null_and_summary_cannot_add_generate(effect):
    result=call(REQUEST,Stub(intake(),mapped_draft(effect)))
    assert result.schema_version=='0.5.0' and result.status=='mapped'
    assert result.view.premises[0].execution_effect is None
    assert result.meta.understanding_mode=='source_excerpts'
    assert result.view.understanding == '\n\n'.join(f'[{k}]\n{REQUEST[k]}' for k in ('input_message','ai_interpretation'))
    assert 'generated' not in result.view.understanding
    assert 'create' not in result.view.understanding
    assert result.meta.execution_authorized is False

@pytest.mark.parametrize('effect', OBSERVED['execution_effects'])
def test_observed_effect_expansion_rejected_by_engine(effect):
    with pytest.raises(ProviderError,match='provider_uncited_execution_effect'):
        call(REQUEST,Stub(intake(),mapped_draft(effect)))

@pytest.mark.parametrize('effect', OBSERVED['execution_effects']+['q999',42,{'ref':'q1'}])
def test_effect_reference_cannot_be_prose_or_unresolved(effect):
    with pytest.raises(ProviderError,match='provider_invalid_effect_reference'):
        resolve_references({'execution_effect':effect,'evidence':[{'ref':'q1'}]},
            {'q1':dict(source='ai_interpretation',quote=REQUEST['ai_interpretation'])})

def test_effect_must_use_reference_cited_on_same_premise_even_if_text_matches():
    registry={'q0':dict(source='input_message',quote='Display records.'),
              'q1':dict(source='ai_interpretation',quote='Display records.')}
    with pytest.raises(ProviderError,match='provider_uncited_execution_effect'):
        resolve_references({'execution_effect':'q0','evidence':[{'ref':'q1'}]},registry)

def test_explicit_generation_quote_is_preserved_without_translation():
    text='架空の顧客データを生成して表示する。'
    req=dict(input_message='架空データを見せて。',ai_interpretation=text,language='en')
    d=draft(unknowns=[])
    d['view']['premises']=[premise(source='provided_source',statement='Generate fictional data.',
        execution_effect=text,evidence=[dict(source='ai_interpretation',quote=text)])]
    result=call(req,Stub(intake(),d))
    assert result.view.premises[0].execution_effect==text
    assert text in result.view.understanding
    assert result.view.understanding_evidence[-1].source=='ai_interpretation'

def test_summary_selection_is_exact_deduplicated_and_missing_side_supplemented():
    e=Evidence(source='input_message',quote='The demo PC is not connected to the internet.')
    d=mapped_draft(); d['view']['understanding']={'evidence':[e.model_dump(),e.model_dump()]}
    result=call(REQUEST,Stub(intake(),d))
    assert result.view.understanding_evidence==[e,Evidence(source='ai_interpretation',quote=REQUEST['ai_interpretation'])]
    assert result.view.understanding==f'[input_message]\n{e.quote}\n\n[ai_interpretation]\n{REQUEST["ai_interpretation"]}'

def test_summary_cannot_quote_unsupplied_generated_actions():
    d=mapped_draft(); d['view']['understanding']={'evidence':[dict(source='ai_interpretation',quote='Generate records locally.')]}
    with pytest.raises(ProviderError,match='provider_ungrounded_evidence'):
        call(REQUEST,Stub(intake(),d))

def test_long_overview_keeps_all_selected_and_supplemented_sources():
    req=dict(input_message='A'*6000,ai_interpretation='B'*6000,
        context=[dict(speaker='human',text='C'*5900)])
    selected=[Evidence(source='context.0',quote='C'*n) for n in (5898,5899,5900)]
    d=draft(unknowns=[]); d['view']['understanding']={'evidence':[e.model_dump() for e in selected]}
    r=call(req,Stub(intake(),d))
    assert len(r.view.understanding_evidence)==5
    assert len(r.view.understanding)>29000
    assert r.view.understanding.endswith('B'*6000)

def test_unknown_still_says_unknown_instead_of_echoing_as_understanding():
    d=draft(unknowns=[]); d['kind']='unclear'
    r=call(dict(input_message='ぽらぬげざもきゅ',language='ja'),Stub(intake(),d))
    assert r.status=='unknown' and 'わかりません' in r.view.understanding
    assert r.view.understanding_evidence==[] and r.meta.understanding_mode=='short_reply'

@pytest.mark.parametrize('variant', ['good','quoted_effect','old_summary','bad_effect'])
def test_real_provider_path_and_http_response_contract(variant):
    d=mapped_draft(None)
    if variant=='quoted_effect': d['view']['premises'][0]['execution_effect']=REQUEST['ai_interpretation']
    if variant=='old_summary': d['view']['understanding']=OBSERVED['understanding']
    if variant=='bad_effect': d['view']['premises'][0]['execution_effect']=OBSERVED['execution_effects'][0]
    replies=[intake(),d]
    def respond(request):
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':model_json(request,replies.pop(0))}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app=create_app(SETTINGS,Provider(SETTINGS,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    res=await api.post('/v1/align',json=REQUEST)
                    if variant in ('good','quoted_effect'):
                        assert res.status_code==200
                        v=res.json(); assert v['schema_version']=='0.5.0'
                        expected = None if variant=='good' else REQUEST['ai_interpretation']
                        assert v['view']['premises'][0]['execution_effect'] == expected
                        assert v['meta']['understanding_mode']=='source_excerpts'
                    else:
                        assert res.status_code==502 and 'result' not in res.json()
    asyncio.run(run())

def test_model_schema_offers_nullable_reference_effect_and_evidence_only_summary():
    payload=dict(input_message='Display.',_evidence_index={'q0':dict(source='input_message',quote='Display.')})
    schema=generation_schema(Draft,payload)
    assert schema['$defs']['Premise']['properties']['execution_effect']['default'] is None
    assert schema['$defs']['Premise']['properties']['execution_effect']['anyOf'][1]['enum']==['q0']
    assert set(schema['$defs']['SummaryDraft']['properties'])=={'evidence'}
