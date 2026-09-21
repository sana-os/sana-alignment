"""Protocol regressions replay observed output; these do not measure live model quality."""
import copy
import json
from pathlib import Path
import pytest
from test_alignment import call, Stub, intake, draft
from app.provider import ProviderError, generation_schema
from app.models import Draft

OBSERVED = json.loads((Path(__file__).parent / 'fixtures/observed-plan-divergence.json').read_text())

def replay():
    human = OBSERVED['observations'][0]['quote']
    # Exact AI clauses are reconstructed as a minimal supplied proposal for protocol replay.
    # This is NOT the complete original plan or a live model replay.
    ai = '\n'.join(e['quote'] for e in OBSERVED['observations'] if e['source'] == 'ai_interpretation')
    view = copy.deepcopy(OBSERVED['view'])
    view.pop('unknowns'); view.pop('questions')
    # Project the old response onto the new draft contract to isolate its citation failure.
    view['understanding'] = {'evidence': []}
    facts = copy.deepcopy(OBSERVED['fact'])
    for p in facts + view['premises']: p['execution_effect'] = None
    care = copy.deepcopy(OBSERVED['care'])
    for p in care: p.pop('execution_effect')
    return dict(input_message=human,ai_interpretation=ai), dict(kind='mapped',fact=facts,view=view,care=care)

def test_observed_missing_ai_citation_is_rejected():
    req, output = replay()
    with pytest.raises(ProviderError, match='provider_incomplete_comparison_evidence') as exc:
        call(req, Stub(intake(), output))
    assert exc.value.issue == dict(path='view.premise_gaps.0.evidence',rule='comparison_requires_human_and_supplied_ai_evidence')

@pytest.mark.parametrize('missing', ['input_message','ai_interpretation'])
def test_comparison_needs_both_source_roles(missing):
    req = dict(input_message='Show fictional records.',ai_interpretation='Show 20 fictional records.')
    gap = dict(kind='missing_premise',human_premise=None,ai_premise=req['ai_interpretation'],
        difference='The AI selected an unconfirmed count.',blocks_execution=False,
        evidence=[dict(source=k,quote=v) for k,v in req.items() if k != missing])
    with pytest.raises(ProviderError,match='provider_incomplete_comparison_evidence'):
        call(req,Stub(intake(),draft(unknowns=[],premise_gaps=[gap])))

def test_cited_material_ai_choice_can_remain_nonblocking():
    req = dict(input_message='Show fictional records.',ai_interpretation='Show 20 fictional records.')
    gap = dict(kind='missing_premise',human_premise=None,ai_premise=req['ai_interpretation'],
        difference='The AI selected an unconfirmed count.',blocks_execution=False,
        evidence=[dict(source=k,quote=v) for k,v in req.items()])
    r=call(req,Stub(intake(),draft(unknowns=[],premise_gaps=[gap])))
    assert r.status=='mapped_with_divergence'
    assert r.view.premise_gaps[0].human_premise is None
    assert r.meta.execution_authorized is False

def test_context_human_evidence_allowed_but_assistant_context_is_not_human():
    for speaker in ['human','ai']:
        req=dict(input_message='Compare the plan.',ai_interpretation='Show 20 records.',
            context=[dict(speaker=speaker,text='Show fictional records.')])
        gap=dict(human_premise='Show fictional records.',ai_premise='Show 20 records.',
            difference='The count was added.',blocks_execution=False,
            evidence=[dict(source='context.0',quote='Show fictional records.'),dict(source='ai_interpretation',quote='Show 20 records.')])
        stub=Stub(intake(),draft(unknowns=[],premise_gaps=[gap]))
        if speaker=='human': assert call(req,stub).status=='mapped_with_divergence'
        else:
            with pytest.raises(ProviderError,match='provider_incomplete_comparison_evidence'): call(req,stub)

def test_model_schema_requires_both_reference_roles():
    payload=dict(ai_interpretation='AI',context=[],_evidence_index={
        'q0':dict(source='input_message',quote='Human'), 'q1':dict(source='ai_interpretation',quote='AI')})
    evidence=generation_schema(Draft,payload)['$defs']['Gap']['properties']['evidence']
    enums=[x['contains']['properties']['ref']['enum'] for x in evidence['allOf']]
    assert enums==[['q0'],['q1']]
