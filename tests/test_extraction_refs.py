import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.engine import validate_evidence
from app.extraction_refs import extraction_index, resolve_extraction
from app.models import Extraction
from app.provider import Provider, ProviderError, Settings, generation_schema

OBSERVED = json.loads((Path(__file__).parent / 'fixtures/observed-0.5.2-extraction-mismatches.json').read_text())
PAYLOAD = {'input_message': 'Display fictional data. Do not use real data.',
           'ai_interpretation': OBSERVED['source_text']}


def test_observed_fourteen_rewrites_still_fail_exact_grounding():
    assert OBSERVED['evidence_mismatch_count'] == 14
    for item in OBSERVED['evidence_mismatches']:
        with pytest.raises(ProviderError, match='provider_ungrounded_evidence'):
            from app.models import Evidence
            validate_evidence([Evidence(source=item['source'], quote=item['received_quote'])],
                              {'ai_interpretation': OBSERVED['source_text']})


def test_candidates_preserve_markdown_code_unicode_and_all_sources():
    refs = extraction_index(PAYLOAD)
    assert all(item['quote'] in PAYLOAD[item['source']] for item in refs.values())
    assert any('**Environment:**' in item['quote'] and '\n' not in item['quote'] for item in refs.values())
    code = next(item['quote'] for item in refs.values() if item['quote'].startswith('```python'))
    assert 'random.randint(1000,9999)' in code and code.endswith('```')
    assert all(m['received_quote'] not in [item['quote'] for item in refs.values()]
               for m in OBSERVED['evidence_mismatches'])


@pytest.mark.parametrize('text,expected', [
    ('PCは接続されていません。架空の情報を表示してください。実在データは使わないでください。', 3),
    ('The PC is offline. Display fictional data. Do not use real data.', 3),
])
def test_state_goal_boundary_remain_separately_selectable(text, expected):
    refs = extraction_index({'input_message': text})
    parts = [item['quote'] for item in refs.values() if item['quote'] != text]
    assert len(parts) == expected
    assert all(part in text for part in parts)


def test_context_duplicate_words_keep_source_identity_and_budget():
    payload = {'input_message': 'Same.', 'ai_interpretation': 'Same.',
               'context': [{'text': 'Line.\n' * 300, 'speaker': 'human'} for _ in range(12)]}
    refs = extraction_index(payload)
    assert len(refs) <= 256
    assert {i['source'] for i in refs.values()} == {'input_message', 'ai_interpretation', *[f'context.{i}' for i in range(12)]}
    assert sum(i['quote'] == 'Same.' for i in refs.values()) == 2
    assert any(i['quote'] == payload['context'][0]['text'] for i in refs.values())


@pytest.mark.parametrize('entry', [
    {'ref': 'missing', 'function': 'proposal'},
    {'ref': 0, 'function': 'proposal'},
    {'ref': 'x0', 'function': 'proposal', 'quote': 'rewritten'},
    {'source': 'input_message', 'quote': 'rewritten', 'function': 'proposal'},
    {'ref': 'x0'},
])
def test_invalid_extraction_reference_is_not_repaired(entry):
    with pytest.raises(ProviderError, match='provider_invalid_extraction_reference'):
        resolve_extraction({'kind': 'substantive', 'frameworks': [], 'evidence': [entry]}, extraction_index(PAYLOAD))


def test_provider_restores_original_quotes_before_engine_validation():
    def respond(request):
        body = json.loads(request.content)
        payload = json.loads(body['messages'][1]['content'])
        refs = payload['_extraction_index']
        ref = next(r for r, item in refs.items() if item['quote'].startswith('- **Environment:**'))
        schema = generation_schema(Extraction, payload)
        assert set(schema['$defs']['ExtractedEvidence']['properties']) == {'ref', 'function'}
        value = {'kind': 'substantive', 'frameworks': [], 'evidence': [{'ref': ref, 'function': 'proposal'}]}
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(value)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            value = await Provider(Settings('https://test/v1', 'test', '', '', True, 1), client).generate('', PAYLOAD, Extraction)
        validate_evidence(value.evidence, PAYLOAD)
        assert value.evidence[0].source == 'ai_interpretation'
        assert '**Environment:**' in value.evidence[0].quote
    asyncio.run(run())
