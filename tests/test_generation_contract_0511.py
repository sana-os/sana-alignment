"""Check the generated choice sets against the existing runtime guard."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest
from app.models import AlignRequest, Draft
from app.provider import Provider, ProviderError, generation_schema, resolve_references
from scripts.diagnose_provider_output_v13 import candidate_review, diagnose
from test_alignment import SETTINGS, draft, model_json, premise

REGISTRY = {'h': {'source':'input_message','quote':'Do not use real data.'},
            'u': {'source':'ai_interpretation','quote':'Record count is unknown.'},
            'a': {'source':'ai_interpretation','quote':'Use the production database.'}}

def schema(registry=REGISTRY, unknowns=('u',)):
    return generation_schema(Draft, {'input_message':'Do not use real data.',
        'ai_interpretation':'Use the production database.', '_evidence_index':registry,
        '_unknown_evidence_refs':list(unknowns)})['$defs']['Gap']

@pytest.mark.parametrize('human,ai,accepted', [(None,'u',False),('h','u',True),
    ('h','a',True),(None,'a',True),('h',None,True),(None,None,False)])
def test_schema_choice_sets_match_runtime_unknown_only_guard(human,ai,accepted):
    selected = {'human_premise':human,'ai_premise':ai}
    # Inspect this specific generated anyOf, not pretend to implement JSON Schema.
    allowed = any(selected[b['required'][0]] in b['properties'][b['required'][0]]['enum']
                  for b in schema()['anyOf'])
    assert allowed == accepted
    g = {**selected,'kind':'interpretation_difference','blocks_execution':False,
         'verification_question':None,'evidence':[{'ref':'h'},{'ref':ai or 'a'}]}
    if accepted:
        out = resolve_references({'premise_gaps':[g]},REGISTRY,unknown_refs=['u'])
        assert len(out['premise_gaps']) == 1
    else:
        with pytest.raises(ProviderError):
            resolve_references({'premise_gaps':[g]},REGISTRY,unknown_refs=['u'])

def test_no_concrete_positions_forbids_gap_items_but_keeps_empty_list():
    g = schema({'u':REGISTRY['u']})
    assert g['not'] == {} and 'anyOf' not in g
    assert g['properties']['dependency']['properties']['target_ref'] == {'not':{}}

def test_missing_dependency_choices_are_restricted_at_actual_property():
    dep = schema()['properties']['dependency']
    assert 'execution_detail' not in dep['properties']['kind']['enum']
    assert 'execution_assumption' not in dep['properties']['kind']['enum']
    assert 'u' not in dep['properties']['target_ref']['enum']
    assert 'oneOf' not in dep

def test_observed_unknown_targets_are_not_offered_as_missing_dependencies():
    p = json.loads((Path(__file__).parent/'fixtures/observed-0.5.10-stage04-diagnostic.json').read_text())
    refs = {r['ref']:{'source':r['source'],'quote':r['quote']} for r in p['reference_review']}
    unknowns = [r['ref'] for r in p['reference_review'] if r['explicit_unknown']]
    g = schema(refs,unknowns)
    for decision in p['scope_decisions']:
        assert decision['dependency']['target_ref'] not in g['properties']['dependency']['properties']['target_ref']['enum']

def test_rejected_diagnostic_keeps_candidate_labels_without_promoting_to_result():
    req = AlignRequest(input_message=REGISTRY['h']['quote'], ai_interpretation=REGISTRY['u']['quote'])
    extraction = {'kind':'substantive','frameworks':[], 'evidence':[{**REGISTRY['u'],'function':'unknown'}]}
    g = {'kind':'missing_premise','blocks_execution':False,'human_premise':None,
         'ai_premise':req.ai_interpretation,'difference':'unused',
         'evidence':[REGISTRY['h'],REGISTRY['u']],'verification_question':None}
    d = draft(unknowns=[],premise_gaps=[g],premises=[premise(statement=req.ai_interpretation,
        source='provided_source',support_state='unsupported',evidence=[REGISTRY['u']])])
    replies=[extraction,d];instructions=[]
    def respond(request):
        instructions.append(json.loads(request.content)['messages'][0]['content'])
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':model_json(request,replies.pop(0))}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            p = await diagnose(req,Provider(SETTINGS,client),1)
        assert p['outcome']=='provider_error' and 'result' not in p
        assert p['error']['code']=='provider_invalid_gap_dependency'
        assert p['rejected_draft_review']['validated'] is False
        assert p['rejected_draft_review']['support_labels'][0]['support_state']=='unsupported'
        assert len(replies)==0
    asyncio.run(run())
    assert 'mixes functions, label it unclear' not in instructions[0]
    assert 'known functions, label it mixed' in instructions[0]
    assert 'scope=execution' not in instructions[1]
    assert 'scope=alignment' not in instructions[1]

def test_candidate_review_bounds_and_types():
    review = candidate_review({'fact':[{'source':'x'*100,'evidence':[{'ref':'q'*100}]*20}]*20,'view':{}})
    assert review['source_counts']['fact']==20
    assert len(review['support_labels'])==16
    assert len(review['support_labels'][0]['evidence_refs'])==8
    assert len(review['support_labels'][0]['source'])==80
    assert candidate_review({'fact':[None],'view':{}})['support_labels']==[]
