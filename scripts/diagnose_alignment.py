"""Run one fresh inference and inspect evidence rejected by the installed engine.

Run from /app inside the existing container. This diagnostic prints failed quotes
and their source text; use the supplied synthetic examples when sharing output.
It does not alter app code, validation, prompts, settings, or provider responses.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))

import httpx
from app.engine import align, sources
from app.main import app
from app.models import AlignRequest
from app.provider import Provider, ProviderError, Settings


class RecordingProvider:
    def __init__(self, provider):
        self.provider = provider
        self.records = []
        self.active_stage = None

    async def generate(self, instruction, payload, schema):
        self.active_stage = schema.__name__
        value = await self.provider.generate(instruction, payload, schema)
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


async def diagnose(request, provider, timeout):
    recorder = RecordingProvider(provider)
    report = {'diagnostic_version': '1', 'application_version': app.version,
              'run_type': 'new_inference', 'requested_language': request.language}
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
