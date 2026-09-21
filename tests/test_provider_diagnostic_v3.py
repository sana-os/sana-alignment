"""One-run diagnostic coverage; controlled providers only."""
import asyncio
import json
import sys

import httpx
import pytest

from app.models import AlignRequest
from app.provider import Provider
from scripts import diagnose_provider_output_v3 as diagnostic
from test_alignment import SETTINGS, Stub, draft, intake, model_json


@pytest.fixture(autouse=True)
def diagnostic_target_version(monkeypatch):
    # v3 remains an immutable 0.5.5 diagnostic, independently of the current app.
    monkeypatch.setattr(diagnostic.app, 'version', '0.5.5')


def test_diagnostic_checks_version_before_inference(monkeypatch):
    monkeypatch.setattr(diagnostic.app, 'version', '0.5.4')
    stub = Stub()
    report = asyncio.run(diagnostic.diagnose(AlignRequest(input_message='Check.'), stub, 1))
    assert report['run_type'] == 'not_started' and not stub.calls
    assert report['error']['code'] == 'expected_application_0.5.5'


def test_diagnostic_collects_unknown_label_context_and_empty_question_count_in_one_run():
    req = AlignRequest(input_message='Show the draft.',
        ai_interpretation='### Unknowns\n- File format.')
    extraction = intake()
    extraction['evidence'] = [{'source': 'ai_interpretation', 'quote': '- File format.', 'function': 'unknown'}]
    d = draft(unknowns=[], unresolved=[{'statement': 'File format.', 'scope': 'execution', 'question': None}])
    stub = Stub(extraction, d)
    report = asyncio.run(diagnostic.diagnose(req, stub, 1))
    assert report['diagnostic_version'] == 'provider-output-3'
    assert report['outcome'] == 'success' and len(stub.calls) == 2
    row = next(r for r in report['reference_review'] if r['quote'] == '- File format.')
    assert row['extraction_function'] == 'unknown' and row['explicit_unknown']
    assert not row['care_eligible']
    assert row['context'] == {'heading_paths': [['### Unknowns']]}
    assert report['extracted_clauses'] == extraction['evidence']
    assert report['draft_review']['distinct_questions_counted_by_engine'] == 0


def test_diagnostic_preserves_excessive_questions_rejection_and_locations():
    req = AlignRequest(input_message='Unclear recipients and transfer boundary.')
    d = draft(unknowns=[], unresolved=[
        {'statement': 'Recipient.', 'scope': 'alignment', 'question': 'Who is the recipient?'},
        {'statement': 'Boundary.', 'scope': 'alignment', 'question': 'What counts as external?'}])
    report = asyncio.run(diagnostic.diagnose(req, Stub(intake(), d), 1))
    assert report['error']['code'] == 'provider_excessive_questions'
    assert report['draft_review']['distinct_questions_counted_by_engine'] == 2
    assert [q['path'] for q in report['draft_review']['questions_with_paths']] == [
        'view.unresolved.0.question', 'view.unresolved.1.question']


@pytest.mark.parametrize('reply', ['{invalid json', '{"kind":"invalid", "frameworks":[], "evidence":[]}'])
def test_diagnostic_restores_trace_and_retains_parse_or_validation_failure(reply):
    def respond(request):
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': reply}}]})
    async def run():
        before = sys.gettrace()
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            report = await diagnostic.diagnose(AlignRequest(input_message='Check the plan.'), Provider(SETTINGS, client), 1)
        assert sys.gettrace() is before
        assert report['error']['code'] == 'provider_invalid_output'
        assert report['completed_stages'] == []
        assert report['extracted_clauses'] is None
        assert report['provider_validation_errors']
    asyncio.run(run())
