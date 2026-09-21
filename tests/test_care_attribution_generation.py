"""Source-aware generation constraints; no claim of live semantic accuracy."""
import copy
import json
from pathlib import Path

import pytest

from app.models import Draft
from app.provider import ProviderError, generation_schema
from test_alignment import Stub, call, care_premise, draft

TEXT = 'Confirm the format with the user.'


def scenario(speaker='ai'):
    req = {'input_message': TEXT, 'ai_interpretation': TEXT,
           'context': [{'speaker': speaker, 'text': TEXT}]}
    e = {'kind': 'substantive', 'frameworks': [], 'evidence': [
        {'source': s, 'quote': TEXT, 'function': 'request'}
        for s in ('input_message', 'ai_interpretation', 'context.0')]}
    return req, e


@pytest.mark.parametrize('speaker', ['human', 'ai', 'source'])
def test_identical_text_keeps_role_specific_generation_choices(speaker):
    req, e = scenario(speaker)
    stub = Stub(e, draft(unknowns=[]))
    call(req, stub)
    payload = stub.calls[1][1]
    refs = payload['_evidence_index']
    branches = generation_schema(Draft, payload)['$defs']['CareDraft']['oneOf']
    seen = set()
    for branch in branches:
        props = branch['properties']
        for ref in props['statement']['enum']:
            assert ref not in seen
            seen.add(ref)
            human = refs[ref]['source'] == 'input_message' or (refs[ref]['source'] == 'context.0' and speaker == 'human')
            expected = 'user_explicit' if human else 'provided_source'
            assert props['source']['const'] == expected
            assert payload['_care_reference_attribution'][ref] == {'source': expected, 'status': 'explicit'}
        for ref in props['evidence']['items']['properties']['ref']['enum']:
            human = refs[ref]['source'] == 'input_message' or (refs[ref]['source'] == 'context.0' and speaker == 'human')
            assert human == (props['source']['const'] == 'user_explicit')
    assert seen == set(payload['_care_evidence_refs'])


@pytest.mark.parametrize('origin', ['ai_interpretation', 'context.0'])
def test_runtime_still_rejects_ai_origin_user_explicit_without_repair(origin):
    req, e = scenario()
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=TEXT, evidence=[{'source': origin, 'quote': TEXT}])]
    with pytest.raises(ProviderError) as exc:
        call(req, Stub(e, d))
    assert exc.value.code == 'provider_invalid_attribution'
    assert exc.value.issue['rule'] == 'user_explicit_requires_human_evidence'


def test_attributed_ai_care_remains_available():
    req, e = scenario()
    d = draft(unknowns=[])
    d['care'] = [care_premise(statement=TEXT, source='provided_source',
                            evidence=[{'source': 'ai_interpretation', 'quote': TEXT}])]
    r = call(req, Stub(e, d))
    assert r.care[0].source == 'provided_source'
    assert r.care[0].evidence[0].source == 'ai_interpretation'
    assert not r.meta.execution_authorized


def test_stage3_record_preserves_known_semantic_defects_for_review():
    root = Path(__file__).parent / 'fixtures'
    r = json.loads((root / 'observed-0.5.3-stage03.json').read_text())
    assert r['request_id'] == '4a3f8524-e2b9-4d37-a9f1-1de7dca8b8a1'
    assert 'must be generated locally' in r['fact'][1]['statement']
    assert len(r['view']['premise_gaps']) == 3 and not r['view']['unresolved']
    # This is recorded failure material, not the desired classification.
    failure = json.loads((root / 'observed-0.5.3-stage04.json').read_text())
    assert failure['detail']['issue']['path'] == 'care.2.evidence.0.source'
