"""Evidence/function contract tests with controlled model outputs, not a live classifier score."""
import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest

from app.main import create_app
from app.models import Draft, Extraction
from app.provider import Provider, ProviderError, generation_schema, resolve_references
from test_alignment import SETTINGS, Stub, call, care_premise, draft, intake, model_json, premise

ROOT = Path(__file__).resolve().parents[1]
OBSERVED = json.loads((ROOT/'tests/fixtures/observed-0.5.0-care.json').read_text())
REQUEST = json.loads((ROOT/OBSERVED['request_fixture']).read_text())
STATE = OBSERVED['fact']['statement']


def observed_replay():
    # The original internal extraction was not supplied. These function labels are
    # independently specified expectations; the Care texts below are exact observed excerpts.
    extracted = intake()
    extracted['evidence'] = [dict(source='input_message',quote=STATE,function='state')]
    extracted['evidence'] += [dict(source='input_message',quote=p['statement'],function='concern')
                              for p in OBSERVED['care'][:2]]
    d = draft(unknowns=[])
    d['fact'] = [copy.deepcopy(OBSERVED['fact'])]
    d['care'] = [{k:v for k,v in p.items() if k != 'execution_effect'} for p in OBSERVED['care']]
    return extracted, d


def test_observed_state_to_requirement_is_not_published_as_care():
    e, d = observed_replay()
    with pytest.raises(ProviderError, match='provider_unanchored_care_statement') as exc:
        call(REQUEST, Stub(e, d))
    assert exc.value.issue['path'] == 'care.2.statement'
    assert STATE not in str(exc.value.issue)


@pytest.mark.parametrize('source,status', [('user_explicit','explicit'),('user_implied','inferred'),('agent_inference','inferred')])
def test_copying_a_state_or_relabelling_it_inferred_cannot_bypass_care(source,status):
    e, d = observed_replay()
    d['care'][-1].update(statement=STATE,source=source,status=status)
    with pytest.raises(ProviderError, match='provider_unanchored_care_statement'):
        call(REQUEST, Stub(e,d))


def test_actual_goals_remain_and_state_remains_in_fact():
    e, d = observed_replay()
    d['care'].pop()
    stub = Stub(e,d)
    r = call(REQUEST,stub)
    assert r.status == 'mapped' and r.fact[0].statement == STATE
    assert [p.statement for p in r.care] == [p['statement'] for p in OBSERVED['care'][:2]]
    assert r.meta.execution_authorized is False
    assert len(stub.calls) == 2
    payload = stub.calls[1][1]
    quotes = [payload['_evidence_index'][ref]['quote'] for ref in payload['_care_evidence_refs']]
    assert STATE not in quotes and len(quotes) == 2
    assert all(set(e) == {'source','quote'} for e in payload['_evidence_index'].values())


@pytest.mark.parametrize('text', [
    'Do not connect the demo PC to the internet.',
    'デモ用PCをインターネットに接続しないでください。',
    'The demo PC must remain disconnected from the internet.',
    'I prefer offline operation.',
    'Real customer data cannot be used in the demo.',
    '実在の顧客データは使えません。',
    'After the demo, internet access is allowed.',
    'No conectes el PC de demostración a Internet.',
])
def test_explicit_boundary_preference_or_permission_keeps_exact_scope(text):
    e = intake(concerns=[text])
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=text,evidence=[dict(source='input_message',quote=text)])]
    r = call(dict(input_message=text,language='en'),Stub(e,d))
    assert r.care[0].statement == text  # Japanese/Spanish quotes are not translated.
    assert r.care[0].execution_effect is None


@pytest.mark.parametrize('function', ['state','proposal','other','unclear',None])
def test_non_concern_and_omitted_function_do_not_supply_care_anchors(function):
    e = intake(); item = dict(source='input_message',quote=STATE)
    if function is not None: item['function'] = function
    e['evidence'] = [item]
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=STATE,evidence=[dict(source='input_message',quote=STATE)])]
    with pytest.raises(ProviderError,match='provider_unanchored_care_statement'):
        call(dict(input_message=STATE),Stub(e,d))


def test_conflicting_extraction_labels_remain_ineligible_regardless_of_order():
    for labels in [('state','concern'),('concern','state')]:
        e = intake(); e['evidence'] = [dict(source='input_message',quote=STATE,function=f) for f in labels]
        d = draft(unknowns=[])
        d['care'] = [care_premise(statement=STATE,evidence=[dict(source='input_message',quote=STATE)])]
        with pytest.raises(ProviderError,match='provider_unanchored_care_statement'):
            call(dict(input_message=STATE),Stub(e,d))


def test_human_context_boundary_survives_without_becoming_current_state():
    text = 'Do not connect the PC during the demo.'
    req = dict(input_message=STATE,context=[dict(speaker='human',text=text)])
    e = intake(); e['evidence'] = [dict(source='context.0',quote=text,function='concern'),
        dict(source='input_message',quote=STATE,function='state')]
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=text,evidence=[dict(source='context.0',quote=text)])]
    r = call(req,Stub(e,d))
    assert r.care[0].evidence[0].source == 'context.0'


def test_an_ai_concern_cannot_become_the_humans_explicit_boundary():
    text = 'Do not connect the PC.'
    e = intake(); e['evidence'] = [dict(source='ai_interpretation',quote=text,function='concern')]
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=text,evidence=[dict(source='ai_interpretation',quote=text)])]
    with pytest.raises(ProviderError,match='provider_invalid_attribution'):
        call(dict(input_message=STATE,ai_interpretation=text),Stub(e,d))


def test_same_text_in_another_source_is_not_the_same_anchor():
    text = 'Do not connect the PC.'
    req = dict(input_message=text,ai_interpretation=text)
    e = intake(concerns=[text]); d = draft(unknowns=[])
    d['care'] = [care_premise(statement=text,source='provided_source',evidence=[dict(source='ai_interpretation',quote=text)])]
    with pytest.raises(ProviderError,match='provider_unanchored_care_statement'):
        call(req,Stub(e,d))


def test_reference_must_be_concern_and_cited_on_same_care_item():
    registry = {'q0':dict(source='input_message',quote=STATE),
                'q1':dict(source='input_message',quote='Do not connect it.')}
    for statement,refs,code in [('q0',['q0'],'provider_invalid_care_reference'),
                              ('q1',['q0'],'provider_uncited_care_statement'),
                              ('must operate offline',['q1'],'provider_invalid_care_reference')]:
        with pytest.raises(ProviderError,match=code):
            resolve_references({'care':[dict(statement=statement,evidence=[{'ref':r} for r in refs])]},registry,['q1'])


@pytest.mark.parametrize('variant', ['good','bad_prose','state_ref','uncited_ref'])
def test_real_http_adapter_accepts_explicit_concerns_and_rejects_boundary_bypass(variant):
    e, d = observed_replay(); d['care'].pop()
    replies = [e,d]
    def respond(request):
        body = json.loads(request.content)
        payload = json.loads(body['messages'][1]['content'])
        value = json.loads(model_json(request,replies.pop(0)))
        if '_evidence_index' in payload:
            registry = payload['_evidence_index']
            state_ref = next(ref for ref,item in registry.items() if item['quote'] == STATE)
            if variant == 'bad_prose': value['care'][0]['statement'] = OBSERVED['care'][2]['statement']
            if variant == 'state_ref': value['care'][0]['statement'] = state_ref
            if variant == 'uncited_ref': value['care'][0]['evidence'] = [{'ref':state_ref}]
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app = create_app(SETTINGS,Provider(SETTINGS,client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as api:
                    res = await api.post('/v1/align',json=REQUEST)
                    if variant == 'good':
                        assert res.status_code == 200
                        assert res.json()['status'] == 'mapped'
                        assert len(res.json()['care']) == 2
                    else:
                        assert res.status_code == 502 and 'result' not in res.json()
                        assert STATE not in res.text
    asyncio.run(run())


def test_uncertainty_can_be_preserved_without_inventing_care():
    text = 'Offline?'
    e = intake(); e['evidence'] = [dict(source='input_message',quote=text,function='unclear')]
    d = draft(unknowns=['It is unclear whether this reports a state or requests offline operation.'])
    r = call(dict(input_message=text),Stub(e,d))
    assert r.status == 'needs_clarification' and r.care is None


def test_prompt_schema_only_offers_concern_references_as_care_statements():
    extraction_schema = generation_schema(Extraction,{})
    assert 'function' in extraction_schema['$defs']['ExtractedEvidence']['required']
    registry = {'q0':dict(source='input_message',quote=STATE),
                'q1':dict(source='input_message',quote='Do not connect it.')}
    payload = dict(_evidence_index=registry,_care_evidence_refs=['q1'])
    schema = generation_schema(Draft,payload)
    assert schema['$defs']['CareDraft']['properties']['statement']['enum'] == ['q1']
    payload['_care_evidence_refs'] = []
    schema = generation_schema(Draft,payload)
    assert schema['properties']['care']['anyOf'] == [{'type':'null'},{'type':'array','maxItems':0}]
