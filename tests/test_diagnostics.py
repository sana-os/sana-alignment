import asyncio
import pytest
from app.models import AlignRequest
from scripts.diagnose_alignment import diagnose, evidence_mismatches


@pytest.mark.parametrize('source,quote,reason', [
    ('input_message', '実在のデータは使えません。', 'quote_not_exact_substring'),
    ('input_message', 'Do not use real data.', 'quote_not_exact_substring'),
    ('input_message', ' ', 'blank_quote'),
    ('context.0', '実データ', 'unknown_source'),
])
def test_diagnostic_preserves_exact_failed_quote(source, quote, reason):
    text = '実在のデータは使えません！'
    node = {'view': {'premises': [{'evidence': [{'source': source, 'quote': quote}]}]}}
    issues = evidence_mismatches([('Draft', node)], {'input_message': text})
    assert issues == [{'stage': 'Draft', 'path': 'view.premises.0.evidence.0',
        'reason': reason, 'source': source, 'received_quote': quote,
        'source_text': text if source == 'input_message' else None}]


def test_exact_partial_quote_is_valid():
    assert evidence_mismatches([('Extraction', {'evidence': [
        {'source':'input_message', 'quote':'データは使えません'}]})],
        {'input_message':'実在のデータは使えません！'}) == []


def test_diagnostic_captures_rejected_intake_without_running_mapping():
    class FakeProvider:
        async def generate(self, instruction, payload, schema):
            assert schema.__name__ == 'Extraction'
            return schema.model_validate({'kind':'substantive','frameworks':[],
                'evidence':[{'source':'input_message','quote':'Do not use real data.'}]})
    report = asyncio.run(diagnose(AlignRequest(input_message='実データ不可'), FakeProvider(), 1))
    assert report['outcome'] == 'provider_error'
    assert report['error']['code'] == 'provider_ungrounded_evidence'
    assert report['completed_stages'] == ['Extraction']
    assert report['evidence_mismatches'][0]['received_quote'] == 'Do not use real data.'


def test_diagnostic_keeps_successful_result():
    class NeverCalled:
        async def generate(self, *args):
            raise AssertionError('Greeting must not call provider')
    report = asyncio.run(diagnose(AlignRequest(input_message='hello'), NeverCalled(), 1))
    assert report['outcome'] == 'success'
    assert report['result']['status'] == 'handshake'
    assert report['evidence_mismatches'] == []
    assert report['completed_stages'] == []
