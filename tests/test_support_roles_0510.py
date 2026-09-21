"""Replay and controlled pipeline checks; these do not measure live classification."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest
from app.models import AlignRequest
from app.provider import Provider
from scripts.diagnose_provider_output_v13 import diagnose, support_review
from test_alignment import SETTINGS, draft, model_json, premise

OBSERVED = json.loads((Path(__file__).parent/'fixtures/observed-0.5.9-stage04-diagnostic.json').read_text())

def test_observed_diagnostic_exposes_regression_without_relabelling():
    r = OBSERVED['result']
    assert r['request_id'] == 'cfb62ce9-3971-4fbe-b9dd-ea85d60958e0'
    rows = support_review(r, OBSERVED['extracted_clauses'])
    view = [p for p in rows if p['path'].startswith('view.')]
    assert len(view) == 10 and {p['support_state'] for p in view} == {'unsupported'}
    assert view[0]['evidence'][0]['extraction_functions'] == ['state']
    assert any(e['function']=='state' and e['quote']=='all data must be generated locally.'
               for e in OBSERVED['extracted_clauses'])

@pytest.mark.parametrize('state,rule', [
    ('The PC is offline;', 'all data must be generated locally.'),
    ('PCは未接続です；', 'データはローカルで生成しなければならない。'),
])
def test_corrected_mixed_labels_keep_rule_out_of_fact_and_source_in_care(state,rule):
    full = state + ' ' + rule
    req = AlignRequest(input_message='Review the plan.', ai_interpretation=full)
    evidence = lambda q: {'source':'ai_interpretation','quote':q}
    extraction = {'kind':'substantive','frameworks':[], 'evidence':[
        {**evidence(full),'function':'mixed'}, {**evidence(state),'function':'state'},
        {**evidence(rule),'function':'concern'}]}
    d = draft(unknowns=[])
    d['fact'] = [premise(statement=state,source='provided_source',evidence=[evidence(state)])]
    c = premise(statement=rule,source='provided_source',support_state='not_applicable',evidence=[evidence(rule)])
    c.pop('execution_effect',None)
    d['care'] = [c]
    replies = [extraction,d]
    def respond(request):
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':model_json(request,replies.pop(0))}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            p = await diagnose(req,Provider(SETTINGS,client),1)
        assert p['outcome'] == 'success'
        assert p['result']['fact'][0]['statement'] == state
        assert p['result']['care'][0]['statement'] == rule
        assert p['result']['care'][0]['source'] == 'provided_source'
        assert p['support_review'][0]['evidence'][0]['extraction_functions'] == ['state']
    asyncio.run(run())

@pytest.mark.parametrize('label', ['provided','unsupported','disputed','unknown','not_applicable'])
def test_support_diagnostic_retains_model_judgment_without_coercion(label):
    # Same sentence under each label deliberately tests transport, not whether
    # all labels would be semantically appropriate for this sentence.
    text = 'The plan assumes scripts or manual editing are available.'
    req = AlignRequest(input_message='Review the plan.', ai_interpretation=text)
    e = {'source':'ai_interpretation','quote':text}
    extraction = {'kind':'substantive','frameworks':[], 'evidence':[{**e,'function':'assumption'}]}
    d = draft(unknowns=[],premises=[premise(statement=text,source='provided_source',
        support_state=label,evidence=[e])])
    replies = [extraction,d]
    def respond(request):
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':model_json(request,replies.pop(0))}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            p = await diagnose(req,Provider(SETTINGS,client),1)
        assert p['outcome'] == 'success'
        assert p['support_review'][0]['support_state'] == label
        assert p['support_review'][0]['evidence'][0]['extraction_functions'] == ['assumption']
        assert p['result']['view']['premises'][0]['externally_verified'] is False
        assert not p['result']['meta']['execution_authorized']
    asyncio.run(run())
