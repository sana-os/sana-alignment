"""Run one fresh inference and inspect evidence rejected by the installed engine.

Run from /app inside the existing container. This diagnostic prints failed quotes
and their source text; use the supplied synthetic examples when sharing output.
For the 0.5.10 verification package. Refuses inference on another app version.
Includes extraction labels and reference context so one run can locate role errors.
It does not alter app code, validation, prompts, settings, or provider responses.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))

import httpx
from pydantic import ValidationError
from app.engine import align, sources
from app.main import app
from app.models import AlignRequest
from app.provider import Provider, ProviderError, Settings


class RecordingProvider:
    def __init__(self, provider):
        self.provider = provider
        self.records = []
        self.active_stage = None
        self.validation_errors = []
        self.mapping = None
        self.scope_decisions = []

    async def generate(self, instruction, payload, schema):
        self.active_stage = schema.__name__
        if schema.__name__ == 'Draft':
            self.mapping = {
                'registry': payload.get('_evidence_index', {}),
                'functions': payload.get('_evidence_functions', {}),
                'care_refs': payload.get('_care_evidence_refs', []),
                'unknown_refs': payload.get('_unknown_evidence_refs', []),
                'non_fact_refs': payload.get('_non_fact_evidence_refs', []),
                'contexts': payload.get('_excerpt_context', {}),
            }
        def trace(frame, event, arg):
            if frame.f_code is not Provider.generate.__code__:
                return None
            if event == 'return' and self.active_stage == 'Draft':
                value = frame.f_locals.get('value')
                if isinstance(value, dict) and isinstance(value.get('view'), dict):
                    items = value['view'].get('unresolved', [])
                    if isinstance(items, list):
                        self.scope_decisions = [
                            {'path': f'view.unresolved.{i}', 'dependency': item.get('dependency')}
                            for i, item in enumerate(items) if isinstance(item, dict)]
                    gaps = value['view'].get('premise_gaps', [])
                    if isinstance(gaps, list):
                        self.scope_decisions.extend(
                            {'path': f'view.premise_gaps.{i}', 'dependency': item.get('dependency')}
                            for i, item in enumerate(gaps) if isinstance(item, dict))
            if event == 'exception' and len(self.validation_errors) < 16:
                _, error, _ = arg
                detail = {'stage': self.active_stage, 'exception': type(error).__name__}
                if isinstance(error, ValidationError):
                    detail['violations'] = [
                        {'path': '.'.join(map(str, item['loc'])), 'type': item['type'],
                         **{k:v for k,v in item.get('ctx', {}).items()
                            if k in ('max_length', 'min_length', 'actual_length') and type(v) is int}}
                        for item in error.errors(include_input=False, include_context=True, include_url=False)[:16]]
                elif isinstance(error, json.JSONDecodeError):
                    detail.update(line=error.lineno, column=error.colno, position=error.pos)
                elif not isinstance(error, (KeyError, IndexError, TypeError, ValueError)):
                    return trace
                self.validation_errors.append(detail)
            return trace
        previous_trace = sys.gettrace()
        sys.settrace(trace)
        try:
            value = await self.provider.generate(instruction, payload, schema)
        finally:
            sys.settrace(previous_trace)
        self.records.append((self.active_stage, value.model_dump()))
        return value


def evidence_mismatches(records, available):
    mismatches = []

    def inspect(node, stage, path=''):
        if isinstance(node, dict):
            for key, value in node.items():
                child = f'{path}.{key}' if path else key
                if key == 'evidence':
                    for i, item in enumerate(value):
                        source, quote = item['source'], item['quote']
                        reason = ('unknown_source' if source not in available else
                                  'blank_quote' if not quote.strip() else
                                  'quote_not_exact_substring' if quote not in available[source] else None)
                        if reason:
                            mismatches.append({'stage': stage, 'path': f'{child}.{i}',
                                'reason': reason, 'source': source, 'received_quote': quote,
                                'source_text': available.get(source)})
                else:
                    inspect(value, stage, child)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                inspect(value, stage, f'{path}.{i}')

    for stage, value in records:
        inspect(value, stage)
    return mismatches


def support_review(value, extraction):
    """Expose selected labels and exact anchors without judging their semantics."""
    rows = []
    for group, premises in (('fact', value.get('fact', [])),
                            ('view.premises', value.get('view', {}).get('premises', []))):
        for i, premise in enumerate(premises):
            anchors = []
            for evidence in premise.get('evidence', []):
                labels = sorted({e.get('function', 'unclear') for e in extraction
                    if e.get('source') == evidence.get('source') and e.get('quote') == evidence.get('quote')})
                anchors.append({**evidence, 'extraction_functions': labels})
            rows.append({'path': f'{group}.{i}', 'statement': premise.get('statement'),
                'source': premise.get('source'), 'status': premise.get('status'),
                'support_state': premise.get('support_state'), 'evidence': anchors})
    return rows


async def diagnose(request, provider, timeout):
    recorder = RecordingProvider(provider)
    report = {'diagnostic_version': 'provider-output-8', 'application_version': app.version,
              'run_type': 'new_inference', 'requested_language': request.language}
    if app.version != '0.5.10':
        report.update(run_type='not_started', outcome='configuration_error',
            error={'code': 'expected_application_0.5.10'})
        return report
    report['request_identity'] = {
        'ai_characters': len(request.ai_interpretation or ''),
        'input_message': request.input_message,
    }
    try:
        async with asyncio.timeout(timeout * 2 + 5):
            result = await align(request, recorder)
        report.update(outcome='success', result=result.model_dump())
    except ProviderError as error:
        report.update(outcome='provider_error', error={'code': error.code})
        if getattr(error, 'issue', None) is not None:
            report['error']['issue'] = error.issue
    except TimeoutError:
        report.update(outcome='provider_error', error={'code': 'alignment_timeout'})
    report['last_attempted_stage'] = recorder.active_stage
    report['completed_stages'] = [stage for stage, _ in recorder.records]
    mismatches = evidence_mismatches(recorder.records, sources(request))
    report['evidence_mismatch_count'] = len(mismatches)
    report['evidence_mismatches'] = mismatches[:16]
    report['provider_validation_errors'] = recorder.validation_errors
    report['extracted_clauses'] = next((v['evidence'] for stage, v in recorder.records
                                      if stage == 'Extraction'), None)
    report['scope_decisions'] = recorder.scope_decisions
    report['reference_review'] = []
    if recorder.mapping is not None:
        mapping = recorder.mapping
        report['reference_review'] = [
            {'ref': ref, **item, 'extraction_function': mapping['functions'].get(ref),
             'care_eligible': ref in mapping['care_refs'],
             'explicit_unknown': ref in mapping['unknown_refs'],
             'excluded_from_fact': ref in mapping['non_fact_refs'],
             'context': mapping['contexts'].get(ref)}
            for ref, item in mapping['registry'].items()]

    for stage, value in recorder.records:
        if stage != 'Draft':
            continue
        view = value.get('view', {})
        questions = []
        for i, item in enumerate(view.get('unresolved', [])):
            if item.get('question'):
                questions.append({'path': f'view.unresolved.{i}.question',
                                  'scope': item.get('scope'), 'text': item['question']})
        for group in ('premise_gaps', 'hypotheses'):
            for i, item in enumerate(view.get(group, [])):
                if item.get('verification_question'):
                    questions.append({'path': f'view.{group}.{i}.verification_question',
                                      'text': item['verification_question']})
        counted = {q['text'].strip() for q in questions if q.get('scope') != 'execution'}
        report['draft_review'] = {
            'care': value.get('care'),
            'unresolved': view.get('unresolved', []),
            'premise_gaps': view.get('premise_gaps', []),
            'hypotheses': view.get('hypotheses', []),
            'questions_with_paths': questions,
            'distinct_questions_counted_by_engine': len(counted),
        }
        report['support_review'] = support_review(value, report['extracted_clauses'] or [])
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request_file', type=Path)
    args = parser.parse_args()
    try:
        request = AlignRequest.model_validate_json(args.request_file.read_text(encoding='utf-8-sig'))
        settings = Settings.from_env()
    except (OSError, ValueError):
        print(json.dumps({'outcome': 'configuration_error', 'error': {'code': 'check_request_file_and_model_settings'}}))
        return 2
    async with httpx.AsyncClient(follow_redirects=False) as client:
        report = await diagnose(request, Provider(settings, client), settings.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['outcome'] == 'success' else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(asyncio.run(main()))
