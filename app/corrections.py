"""Append an operator-supplied correction record; never apply or authorize a task.

Usage: python -m app.corrections --trace-dir /app/traces < correction.json
Review status is the submitter's statement, not authenticated human approval.
"""
import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .run_trace import TraceStore


class Correction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: uuid.UUID
    field_path: str = Field(pattern=r'^(fact|care|view)(\.[A-Za-z_0-9]+)*$', max_length=160)
    proposed_change: str = Field(min_length=1, max_length=6000)
    basis: str = Field(min_length=1, max_length=6000)
    proposer: Literal['human', 'model', 'other']
    review_status: Literal['proposed', 'accepted', 'rejected'] = 'proposed'
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)


def append_correction(store, value):
    correction = Correction.model_validate(value)
    original = store.folder / f'trace-{correction.request_id}.json'
    # Link the saved original exactly; do not create an apparently grounded orphan.
    raw = original.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError('original_trace_too_large')
    trace = json.loads(raw)
    if trace['request_id'] != str(correction.request_id):
        raise ValueError('original_trace_id_mismatch')
    references = {ref for call in trace.get('model_calls', [])
                  for ref in call.get('reference_labels', {})}
    if any(ref not in references for ref in correction.evidence_refs):
        raise ValueError('unknown_evidence_reference')
    record = {'correction_version': 'alignment-correction-1',
              'correction_id': str(uuid.uuid4()),
              'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              **correction.model_dump(mode='json'),
              'original_trace_sha256': hashlib.sha256(raw).hexdigest(),
              'review_status_is_submitter_reported': True,
              'applied_to_original': False, 'execution_authorized': False}
    return store.write(record, correction=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace-dir', default='/app/traces')
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(32769)
        if len(raw) > 32768:
            raise ValueError('correction_too_large')
        path = append_correction(TraceStore(args.trace_dir), json.loads(raw.decode('utf-8-sig')))
    except (OSError, ValueError, KeyError):
        print(json.dumps({'outcome': 'error', 'code': 'correction_not_saved'}))
        return 2
    print(json.dumps({'outcome': 'saved', 'file': path.name, 'applied': False}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
