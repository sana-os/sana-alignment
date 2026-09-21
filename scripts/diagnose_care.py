"""Read-only Care coverage diagnostic for application 0.5.1.

Runs one NEW inference (the normal two stages) with the installed engine/settings.
Does not change prompts, validation, model output, configuration, or application files.
Reports submitted quotes and Care selections; use synthetic fixtures when sharing.
No private reasoning, system prompts, credentials, or model configuration are printed.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))

import httpx
from app.engine import align
from app.main import app
from app.models import AlignRequest
from app.provider import Provider, ProviderError, Settings


class CareRecorder:
    def __init__(self, provider):
        self.provider = provider
        self.extraction = None
        self.mapping = None
        self.draft = None
        self.active_stage = None

    async def generate(self, instruction, payload, schema):
        self.active_stage = schema.__name__
        if self.active_stage == 'Draft':
            # These server-created fields record the actual candidate gate used in this run.
            self.mapping = {
                'registry': payload.get('_evidence_index', {}),
                'functions': payload.get('_evidence_functions', {}),
                'care_refs': payload.get('_care_evidence_refs', []),
            }
        value = await self.provider.generate(instruction, payload, schema)
        if self.active_stage == 'Extraction':
            self.extraction = value.model_dump()
        elif self.active_stage == 'Draft':
            self.draft = value.model_dump()
        return value


def coverage_trace(recorder):
    """Describe observations without inferring what the extractor should have labelled."""
    if recorder.mapping is None:
        return {'mapping_started': False, 'draft_received': False, 'references': []}
    mapping = recorder.mapping
    refs = []
    for ref, evidence in mapping['registry'].items():
        selected = None
        if recorder.draft is not None:
            selected = any(p['statement'] == evidence['quote'] and evidence in p['evidence']
                           for p in recorder.draft.get('care') or [])
        function = mapping['functions'].get(ref)
        refs.append({
            'ref': ref, **evidence,
            # None means no extraction label exists for this whole-source registry entry.
            # 'unclear' means the engine has an unclear/omitted/conflicting extraction label.
            'extraction_function': function,
            'care_eligible': ref in mapping['care_refs'],
            'selected_as_care': selected,
        })
    return {'mapping_started': True, 'draft_received': recorder.draft is not None,
            'references': refs,
            'eligible_but_not_selected': [item['ref'] for item in refs
                if item['care_eligible'] and item['selected_as_care'] is False]}


async def diagnose(request, provider, timeout):
    recorder = CareRecorder(provider)
    report = {'diagnostic_version': 'care-coverage-1', 'application_version': app.version,
              'run_type': 'new_inference', 'requested_language': request.language}
    try:
        async with asyncio.timeout(timeout * 2 + 5):
            result = await align(request, recorder)
        report.update(outcome='success', result=result.model_dump())
    except ProviderError as error:
        report.update(outcome='provider_error', error={'code': error.code})
        if error.issue is not None:
            report['error']['issue'] = error.issue
    except TimeoutError:
        report.update(outcome='provider_error', error={'code': 'alignment_timeout'})
    report['last_attempted_stage'] = recorder.active_stage
    report['extracted_clauses'] = recorder.extraction['evidence'] if recorder.extraction is not None else None
    report['care_trace'] = coverage_trace(recorder)
    return report


async def main(request_json):
    try:
        request = AlignRequest.model_validate_json(request_json)
        settings = Settings.from_env()
    except ValueError:
        print(json.dumps({'outcome': 'configuration_error',
                         'error': {'code': 'check_request_file_and_model_settings'}}))
        return 2
    async with httpx.AsyncClient(follow_redirects=False) as client:
        report = await diagnose(request, Provider(settings, client), settings.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['outcome'] == 'success' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request_file', type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        text = args.request_file.read_text(encoding='utf-8-sig')
    except OSError:
        print(json.dumps({'outcome': 'configuration_error', 'error': {'code': 'request_file_unavailable'}}))
        raise SystemExit(2)
    raise SystemExit(asyncio.run(main(text)))
