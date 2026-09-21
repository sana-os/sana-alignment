"""Extraction capacity/diagnostic regressions; no claim of live model accuracy."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.engine import align
from app.extraction_refs import extraction_index, resolve_extraction
from app.models import AlignRequest, Extraction, MAX_EXTRACTION_REFERENCES
from app.provider import Provider, ProviderError, generation_schema
from scripts.diagnose_provider_output_v4 import diagnose
from test_alignment import SETTINGS, draft, model_json


def test_budget_is_shared_between_candidates_schema_and_model():
    payload = {'input_message': '\n'.join(f'Clause {i}.' for i in range(255))}
    refs = extraction_index(payload)
    assert len(refs) == MAX_EXTRACTION_REFERENCES == 256
    schema = generation_schema(Extraction, {**payload, '_extraction_index': refs})
    assert schema['properties']['evidence']['maxItems'] == len(refs)
    wire = {'kind': 'substantive', 'frameworks': [],
            'evidence': [{'ref': r, 'function': 'unclear'} for r in refs]}
    result = Extraction.model_validate(resolve_extraction(wire, refs))
    assert len(result.evidence) == 256
    assert [(e.source, e.quote) for e in result.evidence] == [(e['source'], e['quote']) for e in refs.values()]


def test_excess_rejected_before_quote_expansion_with_actual_count():
    value = {'kind': 'substantive', 'frameworks': [],
             'evidence': [{'ref': 'x0', 'function': 'unclear'}] * 257}
    with pytest.raises(ProviderError, match='provider_excessive_extraction') as exc:
        resolve_extraction(value, {'x0': {'source': 'input_message', 'quote': 'A' * 6000}})
    assert exc.value.issue == {'path': 'evidence', 'rule': 'extraction_reference_budget',
                              'max_items': 256, 'actual_items': 257}
    with pytest.raises(ValidationError) as exc:
        Extraction.model_validate({**value, 'evidence': [
            {'source': 'input_message', 'quote': 'A', 'function': 'unclear'}] * 257})
    assert exc.value.errors()[0]['type'] == 'too_long'


def test_stage4_all_candidates_reach_mapping_without_truncation():
    req = AlignRequest.model_validate_json((Path(__file__).parent / 'fixtures/stage04.en.json').read_text())
    original_refs = extraction_index(req.model_dump())
    assert len(original_refs) == 51  # 47 originals plus four clause candidates in 0.5.7.
    calls = []
    def respond(request):
        payload = json.loads(json.loads(request.content)['messages'][1]['content'])
        calls.append(payload)
        if '_extraction_index' in payload:
            content = json.dumps({'kind': 'substantive', 'frameworks': [],
                'evidence': [{'ref': ref, 'function': 'unclear'} for ref in payload['_extraction_index']]})
        else:
            refs = payload['_evidence_index']
            selected = [refs[r] for r in payload['extracted_statements']]
            assert selected == list(original_refs.values())
            content = model_json(request, draft(unknowns=[]))
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await align(req, Provider(SETTINGS, client))
        assert result.meta.stages_completed == ['extraction', 'mapping']
        assert not result.meta.execution_authorized
    asyncio.run(run())
    assert len(calls) == 2


@pytest.mark.parametrize('case', ['over_budget', 'framework_limit'])
def test_new_diagnostic_records_counts_without_reconstructing_rejected_clauses(case, monkeypatch):
    from scripts.diagnose_provider_output_v4 import app
    monkeypatch.setattr(app, 'version', '0.5.6')  # v4 is the immutable 0.5.6 diagnostic.
    def respond(request):
        payload = json.loads(json.loads(request.content)['messages'][1]['content'])
        ref = next(iter(payload['_extraction_index']))
        value = {'kind': 'substantive', 'frameworks': [],
            'evidence': [{'ref': ref, 'function': 'unclear'}] * (257 if case == 'over_budget' else 1)}
        if case == 'framework_limit':
            value['frameworks'] = ['RBM', 'GMM', 'CPM', 'RSM']
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(value)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            report = await diagnose(AlignRequest(input_message='Check the plan.'), Provider(SETTINGS, client), 1)
        assert report['diagnostic_version'] == 'provider-output-4'
        assert report['completed_stages'] == [] and report['extracted_clauses'] is None
        if case == 'over_budget':
            assert report['error']['issue']['actual_items'] == 257
            assert report['error']['issue']['max_items'] == 256
        else:
            violation = report['provider_validation_errors'][0]['violations'][0]
            assert violation == {'path': 'frameworks', 'type': 'too_long', 'max_length': 3, 'actual_length': 4}
    asyncio.run(run())
