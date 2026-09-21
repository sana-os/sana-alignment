"""Controlled alternative causes; neither is claimed as the observed internal cause."""
import asyncio
import copy
import json
from pathlib import Path

import pytest

from app.models import AlignRequest
from app.provider import ProviderError
from scripts.diagnose_care import CareRecorder, diagnose
from test_alignment import Stub, care_premise, draft, intake

ROOT = Path(__file__).resolve().parents[1]
OBSERVED = json.loads((ROOT/'tests/fixtures/observed-0.5.1-ja-care.json').read_text())
REQUEST = AlignRequest.model_validate_json((ROOT/OBSERVED['request_fixture']).read_text())
GOAL = OBSERVED['omitted_goal_from_input']
BOUNDARY = OBSERVED['care_statements'][0]


def replies(function='concern', include_goal=False):
    e = intake(concerns=[BOUNDARY])
    e['evidence'].append(dict(source='input_message',quote=GOAL,function=function))
    d = draft(unknowns=[])
    concerns = [BOUNDARY, GOAL] if include_goal else [BOUNDARY]
    d['care'] = [care_premise(statement=text,evidence=[dict(source='input_message',quote=text)])
                 for text in concerns]
    return e,d


@pytest.mark.parametrize('function,eligible', [('concern',True),('proposal',False),('unclear',False)])
def test_diagnostic_distinguishes_selection_omission_from_extraction_label(function,eligible):
    e,d = replies(function)
    report = asyncio.run(diagnose(REQUEST,Stub(e,d),1))
    assert report['run_type'] == 'new_inference' and report['outcome'] == 'success'
    item = next(r for r in report['care_trace']['references'] if r['quote'] == GOAL)
    assert item['extraction_function'] == function
    assert item['care_eligible'] is eligible and item['selected_as_care'] is False
    assert (item['ref'] in report['care_trace']['eligible_but_not_selected']) is eligible
    assert [p['statement'] for p in report['result']['care']] == [BOUNDARY]


def test_successful_new_inference_does_not_claim_to_reproduce_prior_omission():
    e,d = replies(include_goal=True)
    report = asyncio.run(diagnose(REQUEST,Stub(e,d),1))
    assert report['care_trace']['eligible_but_not_selected'] == []
    assert report['result']['request_id'] != OBSERVED['request_id']


def test_mapping_provider_error_is_not_reported_as_candidate_omission():
    e,_ = replies()
    class Fails(Stub):
        async def generate(self,instruction,payload,schema):
            if schema.__name__ == 'Draft': raise ProviderError('provider_timeout',504)
            return await super().generate(instruction,payload,schema)
    report = asyncio.run(diagnose(REQUEST,Fails(e),1))
    assert report['outcome'] == 'provider_error'
    assert report['care_trace']['mapping_started']
    assert not report['care_trace']['draft_received']
    assert report['care_trace']['eligible_but_not_selected'] == []
    assert all(r['selected_as_care'] is None for r in report['care_trace']['references'])


def test_recorder_passes_instruction_payload_and_return_value_without_modification():
    from app.models import Extraction
    payload={'input_message': GOAL}
    value=Extraction.model_validate(intake(concerns=[GOAL]))
    original=copy.deepcopy(value.model_dump())
    class Provider:
        async def generate(self,instruction,received,schema):
            assert instruction == 'unchanged instruction' and received is payload
            assert schema is Extraction
            return value
    recorder=CareRecorder(Provider())
    result=asyncio.run(recorder.generate('unchanged instruction',payload,Extraction))
    assert result is value and result.model_dump() == original


def test_handshake_reports_no_model_trace():
    report=asyncio.run(diagnose(AlignRequest(input_message='Hello'),Stub(),1))
    assert report['result']['status'] == 'handshake'
    assert report['care_trace']['mapping_started'] is False
    assert report['extracted_clauses'] is None
