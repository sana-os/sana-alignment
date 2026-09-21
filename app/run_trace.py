"""Bounded, local records of observable outputs; never model hidden reasoning.

Metadata uses allowlisted labels/IDs and hashes. Detail is an explicit operator opt-in.
The ContextVar is request-local, including across concurrent inference awaits.
"""
import contextvars
import copy
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import threading
import time
import uuid
from datetime import datetime, timezone

ACTIVE_TRACE = contextvars.ContextVar('sana_run_trace', default=None)
MODES = {'low': 0, 'medium': 1, 'high': 2}
TRACE_VERSION = 'alignment-trace-1'
MAX_DETAIL_BYTES = 1_000_000
MAX_RECORD_BYTES = 2_000_000
MAX_STORE_BYTES = 64_000_000
MAX_FILES = 1000
RETENTION_SECONDS = 7 * 24 * 3600
_LOCK = threading.Lock()
_LOG = logging.getLogger(__name__)
FUNCTIONS = {'state', 'request', 'concern', 'proposal', 'unknown', 'mixed', 'assumption', 'other', 'unclear'}
LABELS = {
    'source': {'user_explicit', 'user_implied', 'provided_source', 'agent_inference'},
    'status': {'explicit', 'inferred', 'unclear'},
    'support_state': {'provided', 'unsupported', 'unknown', 'disputed', 'not_applicable'},
    'kind': {'missing_premise', 'constraint_conflict', 'interpretation_difference',
             'execution_detail', 'execution_assumption', 'authority', 'referent',
             'goal_meaning', 'constraint_scope', 'comparison_assumption'},
    'scope': {'execution', 'alignment'},
}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


PATH_FIELDS = set("fact care view premises unresolved premise_gaps hypotheses understanding understanding_evidence evidence quote ref source statement status support_state materiality execution_effect human_premise ai_premise difference dependency target_ref referent_span kind blocks_execution verification_question question scope extraction frameworks function response".split())


def safe_error(value):
    if not isinstance(value, dict):
        return {'code': 'internal_error'}
    output = {'code': value.get('code', 'internal_error')}
    issue = value.get('issue')
    if isinstance(issue, dict):
        path = str(issue.get('path', ''))
        output['issue'] = {'path': '.'.join(p if p in PATH_FIELDS or p.isdecimal()
            else '<field>' for p in path.split('.')), 'rule': issue.get('rule')}
    if isinstance(value.get('violations'), list):
        output['violations'] = [safe_error(v) for v in value['violations'][:16]]
    # Constructed by repair_feedback from server reference IDs/labels and fixed
    # protocol text only. It contains no submitted or generated freeform text.
    if isinstance(value.get('repair_contract'), dict):
        output['repair_contract'] = copy.deepcopy(value['repair_contract'])
    return output


def decisions(value, registry):
    """Only supplied reference IDs and finite labels, never generated prose."""
    if not isinstance(value, dict):
        return []
    view = value.get('view') if isinstance(value.get('view'), dict) else {}
    result = []
    for group, items in [('fact', value.get('fact')), ('care', value.get('care')),
                         *[(f'view.{k}', view.get(k)) for k in ('premises', 'unresolved', 'premise_gaps')]]:
        if not isinstance(items, list):
            continue
        for i, item in enumerate(items[:32]):
            if not isinstance(item, dict):
                continue
            entry = {'path': f'{group}.{i}', 'evidence_refs': []}
            evidence = item.get('evidence')
            for e in evidence[:32] if isinstance(evidence, list) else []:
                ref = e.get('ref') if isinstance(e, dict) else None
                if isinstance(ref, str) and ref in registry:
                    entry['evidence_refs'].append(ref)
            for key, allowed in LABELS.items():
                if key in item:
                    val = item[key]
                    entry[key] = val if isinstance(val, str) and val in allowed else 'invalid'
            dependency = item.get('dependency')
            if isinstance(dependency, dict):
                kind, target = dependency.get('kind'), dependency.get('target_ref')
                entry['dependency'] = {
                    'kind': kind if isinstance(kind, str) and kind in LABELS['kind'] else 'invalid',
                    'target_ref': target if isinstance(target, str) and target in registry else None,
                }
            if type(item.get('blocks_execution')) is bool:
                entry['blocks_execution'] = item['blocks_execution']
            result.append(entry)
    return result


class RunTrace:
    def __init__(self, request, settings, application_version, knowledge_hash):
        self.started = time.monotonic()
        self.level = settings.trace_level
        self.detail_bytes = 0
        self.attempts = []
        self.mode = request.processing_mode or settings.processing_mode
        self.retries = MODES[self.mode]
        self.request_id = str(uuid.uuid4())
        self.data = {
            'trace_version': TRACE_VERSION, 'request_id': self.request_id,
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'application_version': application_version, 'schema_version': '0.5.0',
            'processing_mode': self.mode,
            'mode_source': 'request' if request.processing_mode else 'server',
            'limits': {'mapping_retries': self.retries, 'model_calls': 2 + self.retries,
                       'total_seconds': settings.timeout * 2 + 5},
            'model': settings.model, 'generation_settings': {'json_mode': settings.json_mode,
                'temperature': 'provider_default_unknown', 'seed': 'provider_default_unknown'},
            'knowledge_sha256': knowledge_hash,
            'request_sha256': digest(request.model_dump()),
            'material_sha256': digest(request.model_dump(exclude={'processing_mode'})),
            'trace_level': self.level, 'model_calls': [],
            'mapping_attempts': self.attempts, 'details': {}, 'detail_omissions': [],
            'execution_authorized': False,
        }
        self.detail('request', request.model_dump())

    def detail(self, name, value):
        if self.level != 'detail':
            return
        content = encoded(value)
        if self.detail_bytes + len(content) > MAX_DETAIL_BYTES:
            self.data['detail_omissions'].append(name)
        else:
            self.data['details'][name] = copy.deepcopy(value)
            self.detail_bytes += len(content)

    def model_start(self, stage, body):
        record = {'call': len(self.data['model_calls']) + 1, 'stage': stage,
                  'prompt_sha256': digest(body['messages']), 'outcome': 'started',
                  '_started': time.monotonic()}
        self.data['model_calls'].append(record)
        self.detail(f'call_{record["call"]}_messages', body['messages'])
        return record

    def candidate(self, record, content, payload):
        record['content_sha256'] = digest(content)
        self.detail(f'call_{record["call"]}_candidate', content)
        try:
            value = json.loads(content)
        except (ValueError, TypeError):
            record['candidate_json'] = False
            return
        record['candidate_json'] = True
        registry = payload.get('_evidence_index', {})
        if registry:
            record['reference_labels'] = {
                ref: {'source': item['source'], 'quote_sha256': digest(item['quote']),
                      'function': payload.get('_evidence_functions', {}).get(ref)}
                for ref, item in registry.items()}
            record['decisions'] = decisions(value, registry)
            self.detail(f'call_{record["call"]}_references', registry)
            previous = next((r for r in reversed(self.data['model_calls'][:-1])
                             if r['stage'] == 'Draft' and 'decisions' in r), None)
            if previous:
                before = {r['path']: r for r in previous['decisions']}
                after = {r['path']: r for r in record['decisions']}
                record['decision_changes'] = [{'path': path, 'before': before.get(path),
                    'after': after.get(path)} for path in sorted(before.keys() | after.keys())
                    if before.get(path) != after.get(path)]
        elif isinstance(value, dict) and isinstance(value.get('evidence'), list):
            index = payload.get('_extraction_index', {})
            record['extraction_labels'] = [{'ref': e['ref'],
                'function': e.get('function') if isinstance(e.get('function'), str) and e.get('function') in FUNCTIONS else 'invalid'}
                for e in value['evidence'][:256] if isinstance(e, dict)
                and isinstance(e.get('ref'), str) and e['ref'] in index]
            self.detail(f'call_{record["call"]}_references', index)

    def model_end(self, record, error):
        record['elapsed_seconds'] = round(time.monotonic() - record.pop('_started'), 3)
        # Parsing is not final engine validation; mapping_attempts records that outcome.
        record['outcome'] = 'parsed' if error is None else 'error'
        if error is not None:
            record['error_code'] = getattr(error, 'code', 'cancelled_or_internal_error')

    def finish(self, result=None, error=None):
        self.data.update(elapsed_seconds=round(time.monotonic() - self.started, 3),
                         model_call_count=len(self.data['model_calls']),
                         retry_count=max(0, len(self.attempts) - 1))
        for attempt in self.attempts:
            if 'error' in attempt:
                attempt['error'] = safe_error(attempt['error'])
        if result is not None:
            self.data.update(outcome='success', status=result.status,
                             completed_stages=result.meta.stages_completed)
            self.detail('result', result.model_dump())
        else:
            self.data.update(outcome='error', error=safe_error(error or {'code': 'internal_error'}))
        if self.level != 'detail':
            self.data.pop('details')
        return self.data


class TraceStore:
    """One-process bounded local store. Retention also applies to correction records."""
    def __init__(self, folder):
        self.folder = Path(folder)

    def write(self, record, *, correction=False):
        record_id = record['correction_id' if correction else 'request_id']
        if str(uuid.UUID(record_id)) != record_id:
            raise ValueError('invalid_record_id')
        name = ('correction-' if correction else 'trace-') + record_id + '.json'
        blob = encoded(record) + b'\n'
        if len(blob) > MAX_RECORD_BYTES:
            raise ValueError('trace_record_too_large')
        with _LOCK:
            self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            target = self.folder / name
            if target.exists() or target.is_symlink():
                raise FileExistsError(name)
            now = time.time()
            files = []
            for p in self.folder.iterdir():
                if not re.fullmatch(r'(trace|correction)-[0-9a-f-]{36}\.json', p.name) or p.is_symlink():
                    continue
                s = p.stat()
                if now - s.st_mtime > RETENTION_SECONDS:
                    p.unlink()
                else:
                    files.append((s.st_mtime, p, s.st_size))
            size = sum(s for _, _, s in files)
            for _, p, s in sorted(files):
                if len(files) < MAX_FILES and size + len(blob) <= MAX_STORE_BYTES:
                    break
                p.unlink()
                size -= s
                files = [x for x in files if x[1] != p]
            target = self.folder / name
            # Exclusive creation preserves previously stored records.
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(blob)
                    stream.flush()
            except BaseException:
                target.unlink(missing_ok=True)
                raise
        return target


def save_trace(store, trace, record):
    if trace.level == 'off':
        return 'off'
    try:
        store.write(record)
        return 'saved_with_omissions' if record['detail_omissions'] else 'saved'
    except (OSError, ValueError):
        # No input, secrets, exception paths or candidate text in the operational log.
        _LOG.error('SANA trace_write_failed request_id=%s', trace.request_id)
        return 'failed'
