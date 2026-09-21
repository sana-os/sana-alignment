"""Request/option contract contrasts; controlled labels do not measure model accuracy."""
import copy
import json
from pathlib import Path

import pytest

from app.models import Draft, Extraction
from app.provider import ProviderError, generation_schema
from test_alignment import Stub, call, care_premise, draft, intake

ROOT = Path(__file__).resolve().parents[1]
TRACE = json.loads((ROOT/'tests/fixtures/observed-0.5.1-ja-care-trace.json').read_text())
REQUEST = json.loads((ROOT/TRACE['request_fixture']).read_text())
GOAL = TRACE['extracted_clauses'][1]['quote']
BOUNDARY = TRACE['care_statements'][0]


def care(text, source='input_message'):
    return care_premise(statement=text,evidence=[dict(source=source,quote=text)])


def test_exact_observed_extraction_is_preserved_not_silently_relabelled():
    e = intake(); e['evidence'] = copy.deepcopy(TRACE['extracted_clauses'])
    d = draft(unknowns=[]); d['care'] = [care(BOUNDARY)]
    stub = Stub(e,d)
    r = call(REQUEST,stub)
    assert [c.statement for c in r.care] == TRACE['care_statements']
    payload = stub.calls[1][1]
    goal_ref = next(ref for ref,entry in payload['_evidence_index'].items() if entry['quote'] == GOAL)
    assert payload['_evidence_functions'][goal_ref] == 'proposal'
    assert goal_ref not in payload['_care_evidence_refs']


def test_expected_request_label_can_preserve_goal_alongside_boundary():
    # Only this controlled expectation changes the observed label; the fixture stays exact.
    e = intake(); e['evidence'] = copy.deepcopy(TRACE['extracted_clauses'])
    e['evidence'][1]['function'] = 'request'
    d = draft(unknowns=[]); d['care'] = [care(GOAL),care(BOUNDARY)]
    stub = Stub(e,d); r = call(REQUEST,stub)
    assert r.status == 'mapped' and [c.statement for c in r.care] == [GOAL,BOUNDARY]
    payload = stub.calls[1][1]
    schema = generation_schema(Draft,payload)
    allowed = schema['$defs']['CareDraft']['properties']['statement']['enum']
    assert {payload['_evidence_index'][ref]['quote'] for ref in allowed} == {GOAL,BOUNDARY}
    assert not r.meta.execution_authorized


@pytest.mark.parametrize('text', [
    '完全に架空の顧客情報を表示してください。',
    'ローカルファイルを使って表示してください。',
    '架空の一覧を表示してもらえますか。',
    'Display entirely fictional customer information.',
    'Could you display fictional records, please?',
    'Use the local CSV file for the display.',
])
def test_explicit_action_and_adopted_method_are_eligible_with_request_label(text):
    e = intake(); e['evidence'] = [dict(source='input_message',quote=text,function='request')]
    d = draft(unknowns=[]); d['care'] = [care(text)]
    r = call(dict(input_message=text,language='en'),Stub(e,d))
    assert r.care[0].statement == text and r.care[0].status == 'explicit'


@pytest.mark.parametrize('text,function', [
    ('架空の顧客情報を表示する案を検討しています。','proposal'),
    ('One option would be to display fictional records.','proposal'),
    ('「架空の情報を表示してください」という依頼は取り下げます。','other'),
    ('The demo PC is not connected to the internet.','state'),
])
def test_options_withdrawn_requests_and_states_are_not_blanket_promoted(text,function):
    e = intake(); e['evidence'] = [dict(source='input_message',quote=text,function=function)]
    d = draft(unknowns=[]); d['care'] = [care(text)]
    with pytest.raises(ProviderError,match='provider_unanchored_care_statement'):
        call(dict(input_message=text),Stub(e,d))


def test_request_and_concern_labels_for_same_quote_are_compatible_for_care():
    for labels in [('request','concern'),('concern','request')]:
        e = intake(); e['evidence'] = [dict(source='input_message',quote=GOAL,function=f) for f in labels]
        d = draft(unknowns=[]); d['care'] = [care(GOAL)]
        assert call(dict(input_message=GOAL),Stub(e,d)).care[0].statement == GOAL


@pytest.mark.parametrize('other_function', ['state','proposal','unclear'])
def test_request_with_incompatible_label_does_not_bypass_uncertainty(other_function):
    e = intake(); e['evidence'] = [dict(source='input_message',quote=GOAL,function=f)
                                  for f in ('request',other_function)]
    d = draft(unknowns=[]); d['care'] = [care(GOAL)]
    with pytest.raises(ProviderError,match='provider_unanchored_care_statement'):
        call(dict(input_message=GOAL),Stub(e,d))


def test_context_request_remains_attributed_and_ai_request_is_not_human_agreement():
    e = intake(); e['evidence'] = [dict(source='context.0',quote=GOAL,function='request')]
    d = draft(unknowns=[]); d['care'] = [care(GOAL,'context.0')]
    req = dict(input_message='比較してください。',context=[dict(speaker='human',text=GOAL)])
    assert call(req,Stub(e,d)).care[0].evidence[0].source == 'context.0'
    req['context'][0]['speaker'] = 'ai'
    with pytest.raises(ProviderError,match='provider_invalid_attribution'):
        call(req,Stub(e,d))


def test_extractor_schema_exposes_request_and_retains_unclear_fallback():
    schema = generation_schema(Extraction,{})
    function = schema['$defs']['ExtractedEvidence']['properties']['function']
    assert 'request' in function['enum'] and 'proposal' in function['enum']
    assert function['default'] == 'unclear'
