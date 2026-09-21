"""Role consistency and dependency contracts; controlled outputs, not accuracy scores."""
import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest

from app.extraction_refs import extraction_index, excerpt_context
from app.models import AlignRequest, Draft
from app.provider import Provider, ProviderError, generation_schema, resolve_references
from app.role_contract import DEPENDENCIES, fact_exclusions
from scripts.diagnose_provider_output_v13 import diagnose
from test_alignment import SETTINGS, Stub, call, draft, premise, model_json

ROOT = Path(__file__).parent
OBSERVED = json.loads((ROOT/'fixtures/observed-0.5.6-stage04-diagnostic.json').read_text())
FULL = '- **Environment:** The demo PC has no internet connectivity; all data must be generated locally.'
STATE = '- **Environment:** The demo PC has no internet connectivity;'
RULE = 'all data must be generated locally.'


def test_observed_success_retains_semantic_defects_as_regression_material():
    assert OBSERVED['result']['request_id'] == '72e313f7-b020-498b-94a0-961bf7733144'
    assert len(OBSERVED['extracted_clauses']) == 22
    assert OBSERVED['outcome'] == 'success'
    assert all(x['scope'] == 'alignment' for x in OBSERVED['result']['view']['unresolved'])
    assert any(e['quote'] == FULL and e['function'] == 'state' for e in OBSERVED['extracted_clauses'])
    assert any('all data must be generated locally' in p['statement'] for p in OBSERVED['result']['fact'])


@pytest.mark.parametrize('text,clauses', [(FULL, (STATE, RULE)),
    ('PCは未接続；ローカルで生成してください。', ('PCは未接続；', 'ローカルで生成してください。'))])
def test_clause_candidates_keep_parent_context_and_original_qualifiers(text, clauses):
    payload = {'input_message': text}
    refs = extraction_index(payload)
    context = excerpt_context(payload, refs)
    assert any(v['quote'] == text for v in refs.values())
    for quote in clauses:
        ref = next(r for r, e in refs.items() if e['quote'] == quote)
        assert context[ref]['enclosing_lines'] == [text]
        assert quote in text


def test_code_and_alternatives_are_not_broken_at_semicolons():
    text = '```python\nx = 1; y = 2\n```\nUse `a;b` or `c;d`.\nUse installed or bundled libraries.'
    refs = extraction_index({'input_message': text})
    quotes = [e['quote'] for e in refs.values()]
    assert 'x = 1;' not in quotes and 'y = 2' not in quotes
    assert 'Use `a;b` or `c;d`.' in quotes
    assert 'Use installed or bundled libraries.' in quotes


def scenario():
    req = {'input_message': 'Show fictional records.', 'ai_interpretation': FULL}
    extraction = {'kind':'substantive','frameworks':[], 'evidence': [
        {'source':'ai_interpretation','quote':FULL,'function':'mixed'},
        {'source':'ai_interpretation','quote':STATE,'function':'state'},
        {'source':'ai_interpretation','quote':RULE,'function':'concern'}]}
    return req, extraction


@pytest.mark.parametrize('quote,accepted', [(STATE,True),(FULL,False),(RULE,False)])
def test_fact_accepts_state_part_but_not_declared_mixed_or_directive(quote, accepted):
    req, extraction = scenario()
    d = draft(unknowns=[])
    d['fact'] = [premise(statement=quote,source='provided_source',evidence=[{'source':'ai_interpretation','quote':quote}])]
    stub = Stub(extraction,d)
    if accepted:
        assert call(req,stub).fact[0].statement == STATE
    else:
        with pytest.raises(ProviderError, match='provider_non_factual_evidence'):
            call(req,stub)
    payload = stub.calls[1][1]
    forbidden = {payload['_evidence_index'][r]['quote'] for r in payload['_non_fact_evidence_refs']}
    assert FULL in forbidden and RULE in forbidden and STATE not in forbidden


def test_declared_plan_assumption_can_remain_in_view_but_not_fact():
    text = 'The user can run scripts or edit manually.'
    req = {'input_message':'Show a demo.', 'ai_interpretation':text}
    e = {'kind':'substantive','frameworks':[], 'evidence':[{'source':'ai_interpretation','quote':text,'function':'assumption'}]}
    p = premise(statement=text,source='provided_source',evidence=[{'source':'ai_interpretation','quote':text}])
    d=draft(unknowns=[],premises=[p])
    assert call(req,Stub(e,d)).view.premises[0].statement == text
    d['fact']=[p]
    with pytest.raises(ProviderError,match='provider_non_factual_evidence'):
        call(req,Stub(e,d))


def test_role_exclusion_does_not_cross_source_identity():
    refs={'q0':{'source':'input_message','quote':'Same.'},'q1':{'source':'ai_interpretation','quote':'Same.'}}
    assert fact_exclusions(refs, {'q0':'state','q1':'assumption'}) == ['q1']


def test_fact_schema_excludes_known_non_fact_references_without_restricting_view():
    req,e=scenario()
    stub=Stub(e,draft(unknowns=[]));call(req,stub)
    payload=stub.calls[1][1];schema=generation_schema(Draft,payload)
    allowed=schema['$defs']['FactPremise']['properties']['evidence']['items']['properties']['ref']['enum']
    assert set(allowed).isdisjoint(payload['_non_fact_evidence_refs'])
    assert schema['$defs']['MappingView']['properties']['premises']['items']['$ref']=='#/$defs/Premise'


REGISTRY={'q0':{'source':'input_message','quote':'Send the file to them.'},
          'q1':{'source':'ai_interpretation','quote':'The format is unspecified.'}}


@pytest.mark.parametrize('kind', DEPENDENCIES)
def test_dependency_controls_scope_without_forcing_all_unknowns_to_execution(kind):
    target=None if kind=='execution_detail' else 'q0'
    item={'statement':'An open topic.', 'dependency':{'kind':kind,'target_ref':target},
          'evidence':[{'ref':'q0'}], 'question':None}
    if kind == 'referent':
        item['dependency']['referent_span'] = 'them'
    out=resolve_references({'unresolved':[item]},REGISTRY)['unresolved'][0]
    assert out['scope']==('execution' if kind in ('execution_detail','execution_assumption') else 'alignment')
    assert 'dependency' not in out


@pytest.mark.parametrize('edit', [
    {'scope':'alignment'},
    {'dependency':{'kind':'alignment','target_ref':'q0'}},
    {'dependency':{'kind':'execution_detail','target_ref':'q0'}},
    {'dependency':{'kind':'referent','target_ref':None}},
    {'dependency':{'kind':'referent','target_ref':'q999'}},
    {'evidence':[]},
])
def test_invalid_or_uncited_dependency_is_not_silently_repaired(edit):
    item={'statement':'Who is them?', 'dependency':{'kind':'referent','target_ref':'q0','referent_span':'them'},
          'evidence':[{'ref':'q0'}], 'question':None}
    with pytest.raises(ProviderError,match='provider_invalid_scope_dependency'):
        resolve_references({'unresolved':[{**item,**edit}]},REGISTRY)


@pytest.mark.parametrize('scope,kind,expected', [('execution','execution_detail','mapped'),('alignment','referent','needs_clarification')])
def test_full_provider_diagnostic_records_scope_decision_and_preserves_routing(scope,kind,expected):
    req=AlignRequest(input_message='Send the file to them.',ai_interpretation='Send the file. Its format is unspecified.')
    e={'kind':'substantive','frameworks':[], 'evidence':[{'source':'input_message','quote':req.input_message,'function':'request'}]}
    d=draft(unknowns=[],unresolved=[{'statement':'An open topic.','scope':scope,'question':None}])
    replies=[e,d]
    def respond(request):
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':model_json(request,replies.pop(0))}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            report=await diagnose(req,Provider(SETTINGS,client),1)
        assert report['outcome']=='success'
        assert report['result']['status']==expected
        assert report['scope_decisions'][0]['dependency']['kind']==kind
        assert report['result']['view']['unresolved'][0]['scope']==scope
        assert not report['result']['meta']['execution_authorized']
        assert len(report['reference_review'])>0
    asyncio.run(run())
