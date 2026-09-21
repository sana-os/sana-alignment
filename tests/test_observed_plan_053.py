"""Recorded evidence and controlled routing checks, not live model accuracy."""
import copy
import json
from pathlib import Path

import pytest

from app.provider import ProviderError
from test_alignment import Stub, call

ROOT = Path(__file__).resolve().parents[1]
RECORD = json.loads((ROOT / 'tests/fixtures/observed-0.5.3-plan-diagnostic.json').read_text())
REQUEST = json.loads((ROOT / 'examples/quality/observed-plan-052.en.json').read_text())


def replay():
    result = RECORD['result']
    view = {k: copy.deepcopy(result['view'][k])
            for k in ('premises', 'hypotheses', 'premise_gaps', 'unresolved')}
    view['understanding'] = {'evidence': copy.deepcopy(result['view']['understanding_evidence'])}
    # The diagnostic did not record draft.kind. 'mapped' is a controlled input;
    # the scope labels alone are sufficient to reproduce the reported status.
    draft = {'kind': 'mapped', 'fact': copy.deepcopy(result['fact']),
             'view': view, 'care': copy.deepcopy(RECORD['draft_care'])}
    extraction = {'kind': 'substantive', 'frameworks': [],
                  'evidence': copy.deepcopy(RECORD['extracted_clauses'])}
    return extraction, draft


def test_recorded_quotes_are_grounded_in_exact_replayed_request():
    assert RECORD['result']['request_id'] == '3cc1ea62-0d7b-4c4d-ad35-15fc04883cda'
    for item in RECORD['extracted_clauses']:
        assert item['quote'] in REQUEST[item['source']]


def test_recorded_alignment_scopes_are_sufficient_to_trigger_clarification():
    r = call(REQUEST, Stub(*replay()))
    assert r.status == 'needs_clarification'
    assert len(r.care) == 2 and len(r.view.unknowns) == 3
    assert not r.meta.execution_authorized


def test_controlled_execution_scopes_do_not_interrupt_mapping():
    e, d = replay()
    for u in d['view']['unresolved']:
        u['scope'] = 'execution'
    r = call(REQUEST, Stub(e, d))
    assert r.status == 'mapped'
    assert len(r.view.unresolved) == 3
    assert not r.view.unknowns and not r.view.questions
    # This tests routing only; it does not assert that the real long plan is aligned.
    assert not r.meta.execution_authorized


def test_characterize_ai_request_still_exposed_as_care_candidate():
    e, d = replay()
    stub = Stub(e, d)
    call(REQUEST, stub)
    payload = stub.calls[1][1]
    ai_request = next(item for item in e['evidence']
                      if item['source'] == 'ai_interpretation' and item['function'] == 'request')
    refs = payload['_evidence_index']
    selected = next(ref for ref, item in refs.items()
                    if item == {k: ai_request[k] for k in ('source', 'quote')})
    # Characterization of a remaining candidate-generation weakness, not desired behavior.
    assert selected in payload['_care_evidence_refs']


def test_simulated_ai_request_cannot_be_published_as_user_explicit_care():
    e, d = replay()
    ai_request = next(item for item in e['evidence']
                      if item['source'] == 'ai_interpretation' and item['function'] == 'request')
    added = copy.deepcopy(d['care'][0])
    added['statement'] = ai_request['quote']
    added['evidence'] = [{k: ai_request[k] for k in ('source', 'quote')}]
    d['care'].append(added)
    with pytest.raises(ProviderError) as exc:
        call(REQUEST, Stub(e, d))
    assert exc.value.code == 'provider_invalid_attribution'
    assert exc.value.issue == {'path': 'care.2.evidence.0.source',
                              'rule': 'user_explicit_requires_human_evidence'}
    # This constructed case is not a reconstruction of the earlier failed inference.
