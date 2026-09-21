"""Observed failure material and controlled protocol tests, not live accuracy tests."""
import asyncio
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from app.extraction_refs import extraction_index, excerpt_context
from app.main import create_app
from app.models import Draft
from app.provider import Provider, ProviderError, generation_schema, resolve_references
from test_alignment import SETTINGS, Stub, call, care_premise, draft, model_json

ROOT = Path(__file__).resolve().parents[1]
REPORT = json.loads((ROOT / 'tests/fixtures/observed-0.5.4-stage04-diagnostic.json').read_text())
REQUEST_BYTES = (ROOT / 'tests/fixtures/stage04.en.json').read_bytes()
REQUEST = json.loads(REQUEST_BYTES)
UNKNOWN_QUOTES = [item['evidence'][0]['quote'] for item in REPORT['result']['view']['unresolved']]
LIBRARIES = REPORT['result']['view']['premise_gaps'][1]['evidence'][1]['quote']


def test_observed_record_is_same_stage4_success_not_excessive_question_reproduction():
    assert hashlib.sha256(REQUEST_BYTES).hexdigest() == 'feb95a60f6cf826f2a10576cd7d3f27dbe4ef101a3d67641a2e692f55d9f2b42'
    assert REPORT['diagnostic_version'] == 'provider-output-2'
    assert REPORT['result']['request_id'] == '90a3af58-e76d-4b9e-9b4c-10c3a1792073'
    assert REPORT['request_identity']['ai_characters'] == len(REQUEST['ai_interpretation']) == 4250
    assert REPORT['outcome'] == 'success'
    assert REPORT['draft_review']['distinct_questions_counted_by_engine'] == 0
    assert len(REPORT['result']['care']) == 6
    assert all(x['scope'] == 'alignment' for x in REPORT['result']['view']['unresolved'])
    # Preserve defects as observations, not desired expectations.
    assert 'or can be bundled' in LIBRARIES
    assert 'bundled' not in REPORT['result']['view']['premise_gaps'][1]['difference']


def test_unknown_fragments_receive_literal_heading_context_without_quote_rewriting():
    refs = extraction_index(REQUEST)
    contexts = excerpt_context(REQUEST, refs)
    for quote in UNKNOWN_QUOTES:
        ref = next(r for r, e in refs.items() if e['quote'] == quote)
        assert contexts[ref] == {'heading_paths': [['### 3. Unknowns']]}
        assert refs[ref] == {'source': 'ai_interpretation', 'quote': quote}


def test_repeated_text_keeps_distinct_contexts_and_fenced_headings_are_not_real():
    text = '# Unknowns\nSame topic.\n# Requirements\n```md\n# Unknowns\n```\nSame topic.'
    payload = {'input_message': text}
    refs = {'q1': {'source': 'input_message', 'quote': 'Same topic.'},
            'q2': {'source': 'input_message', 'quote': text}}
    context = excerpt_context(payload, refs)
    assert context == {'q1': {'heading_paths': [['# Unknowns'], ['# Requirements']]}}


@pytest.mark.parametrize('language,text,instruction', [
    ('en', 'The format is unspecified.', 'Confirm the format.'),
    ('ja', '形式は未指定です。', '形式を確認してください。'),
])
def test_unknown_is_not_care_but_a_separate_request_about_it_is(language, text, instruction):
    req = {'input_message': text + '\n' + instruction, 'language': language}
    extraction = {'kind': 'substantive', 'frameworks': [], 'evidence': [
        {'source': 'input_message', 'quote': text, 'function': 'unknown'},
        {'source': 'input_message', 'quote': instruction, 'function': 'request'}]}
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=instruction, evidence=[{'source': 'input_message', 'quote': instruction}])]
    d['view']['unresolved'] = [{'statement': text, 'scope': 'execution',
        'evidence': [{'source': 'input_message', 'quote': text}], 'question': None}]
    stub = Stub(extraction, d)
    result = call(req, stub)
    assert result.status == 'mapped' and result.view.questions == []
    payload = stub.calls[1][1]
    assert set(payload['_unknown_evidence_refs']).isdisjoint(payload['_care_evidence_refs'])
    d['care'].append(care_premise(statement=text, evidence=[{'source': 'input_message', 'quote': text}]))
    with pytest.raises(ProviderError, match='provider_unanchored_care_statement'):
        call(req, Stub(extraction, d))


def test_observed_unknown_care_is_rejected_when_extracted_as_unknown():
    # Original extraction labels were not recorded in v2; labels here are controlled
    # expectations. This does NOT establish that a live model selects them.
    extraction = {'kind': 'substantive', 'frameworks': [], 'evidence': [
        {'source': 'ai_interpretation', 'quote': q, 'function': 'unknown'} for q in UNKNOWN_QUOTES]}
    for item in REPORT['draft_review']['care'][3:]:
        d = draft(unknowns=[])
        d['care'] = [item]
        with pytest.raises(ProviderError, match='provider_unanchored_care_statement'):
            call(REQUEST, Stub(extraction, d))


@pytest.mark.parametrize('scope,expected', [('execution', 'mapped'), ('alignment', 'needs_clarification')])
def test_unknown_label_does_not_force_implementation_scope_or_mapped(scope, expected):
    text = 'Whether the partner team counts as external is unclear.'
    req = {'input_message': text}
    extraction = {'kind': 'substantive', 'frameworks': [], 'evidence': [
        {'source': 'input_message', 'quote': text, 'function': 'unknown'}]}
    d = draft(unknowns=[], unresolved=[{'statement': text, 'scope': scope,
        'evidence': [{'source': 'input_message', 'quote': text}], 'question': None}])
    assert call(req, Stub(extraction, d)).status == expected


def positions(human='Do not use real data.', ai=LIBRARIES):
    registry = {'q0': {'source': 'input_message', 'quote': human},
                'q1': {'source': 'ai_interpretation', 'quote': ai}}
    gap = {'kind': 'missing_premise', 'blocks_execution': False,
           'dependency': {'kind': 'comparison_assumption', 'target_ref': 'q1'},
           'human_premise': None, 'ai_premise': 'q1',
           'evidence': [{'ref': 'q0'}, {'ref': 'q1'}], 'verification_question': None}
    return registry, gap


@pytest.mark.parametrize('quote', [LIBRARIES,
    'Use scripts or edit a file manually, unless neither is available.',
    '導入済み、または同梱可能なライブラリを使う。ただし外部への接続はしない。'])
def test_original_options_negation_and_qualifications_survive_comparison(quote):
    registry, gap = positions(ai=quote)
    result = resolve_references({'premise_gaps': [gap]}, registry)['premise_gaps'][0]
    assert result['ai_premise'] == quote
    assert result['difference'] == f'[missing_premise]\n\n[human_premise]\nnull\n\n[ai_premise: ai_interpretation]\n{quote}'
    assert result['human_premise'] is None
    assert not result['blocks_execution']


@pytest.mark.parametrize('mutation,code', [
    ({'difference': 'AI assumes required libraries are already present.'}, 'provider_unexpected_difference'),
    ({'ai_premise': 'already present'}, 'provider_invalid_comparison_reference'),
    ({'ai_premise': 'q0'}, 'provider_invalid_comparison_source'),
    ({'human_premise': 'q1'}, 'provider_invalid_comparison_source'),
    ({'evidence': [{'ref': 'q0'}]}, 'provider_uncited_comparison_reference'),
])
def test_bad_comparisons_are_rejected_not_repaired(mutation, code):
    registry, gap = positions()
    with pytest.raises(ProviderError, match=code):
        resolve_references({'premise_gaps': [{**gap, **mutation}]}, registry)


def test_identical_context_text_cannot_swap_position_speakers():
    registry, gap = positions(human='Same.', ai='Same.')
    registry['q2'] = {'source': 'context.0', 'quote': 'Same.'}
    gap.update(human_premise='q2', evidence=[{'ref': 'q2'}, {'ref': 'q1'}])
    assert resolve_references({'premise_gaps': [gap]}, registry,
        human_sources={'input_message', 'context.0'})['premise_gaps'][0]['human_premise'] == 'Same.'
    with pytest.raises(ProviderError, match='provider_invalid_comparison_source'):
        resolve_references({'premise_gaps': [gap]}, registry)


def test_maximum_length_positions_are_not_truncated():
    registry, gap = positions('人' * 6000, 'A' * 6000)
    gap['human_premise'] = 'q0'
    result = resolve_references({'premise_gaps': [gap]}, registry)['premise_gaps'][0]
    d = draft(unknowns=[], premise_gaps=[result])
    validated = Draft.model_validate(d)
    assert len(validated.view.premise_gaps[0].difference) > 12000
    assert result['difference'].endswith('A' * 6000)


def test_generation_schema_requests_cited_positions_without_free_difference():
    registry, _ = positions()
    schema = generation_schema(Draft, {'_evidence_index': registry,
        'input_message': 'Human.', 'ai_interpretation': 'AI.'})
    gap = schema['$defs']['Gap']
    assert 'difference' not in gap['properties'] and 'difference' not in gap['required']
    assert gap['properties']['human_premise']['anyOf'][1]['enum'] == ['q0']
    assert gap['properties']['ai_premise']['anyOf'][1]['enum'] == ['q1']


@pytest.mark.parametrize('bad_prose', [False, True])
def test_http_comparison_preserves_conflict_and_rejects_generated_difference(bad_prose):
    req = {'input_message': 'Do not use real data.', 'ai_interpretation': 'Read the production database.'}
    extraction = {'kind': 'substantive', 'frameworks': [], 'evidence': [
        {'source': 'input_message', 'quote': req['input_message'], 'function': 'concern'},
        {'source': 'ai_interpretation', 'quote': req['ai_interpretation'], 'function': 'proposal'}]}
    gap = {'kind': 'constraint_conflict', 'blocks_execution': True,
        'human_premise': req['input_message'], 'ai_premise': req['ai_interpretation'],
        'difference': 'This fixture text is not sent to the provider.',
        'evidence': [{'source': key, 'quote': value} for key, value in req.items()],
        'verification_question': None}
    replies = [extraction, draft(unknowns=[], premise_gaps=[gap])]
    def respond(request):
        wire = json.loads(model_json(request, replies.pop(0)))
        if bad_prose and 'view' in wire:
            wire['view']['premise_gaps'][0]['difference'] = 'A newly invented explanation.'
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(wire)}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            app = create_app(SETTINGS, Provider(SETTINGS, client))
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as api:
                    response = await api.post('/v1/align', json=req)
        assert not replies
        if bad_prose:
            assert response.status_code == 502
            assert response.json()['detail']['code'] == 'provider_unexpected_difference'
        else:
            assert response.status_code == 200
            result = response.json()
            assert result['status'] == 'revision_required' and result['meta']['execution_authorized'] is False
            assert result['view']['premise_gaps'][0]['human_premise'] == req['input_message']
            assert result['view']['premise_gaps'][0]['ai_premise'] == req['ai_interpretation']
            assert all(value in result['view']['premise_gaps'][0]['difference'] for value in req.values())
    asyncio.run(run())
