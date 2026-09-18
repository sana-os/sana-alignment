import json
import os
from dataclasses import dataclass
from urllib.parse import urlsplit
import httpx
from pydantic import ValidationError

class ProviderError(Exception):
    def __init__(self, code='provider_error', status=502, *, issue=None):
        self.code, self.status = code, status
        self.issue = issue
        super().__init__(code)

def generation_schema(schema, payload):
    """Express the existing attribution checks in the schema shown to the model.

    These conditions guide generation; engine validation remains authoritative.
    Source IDs are derived from request structure, never from quoted instructions.
    """
    result = schema.model_json_schema()
    registry = payload.get('_evidence_index')
    human_sources = ['input_message'] + [f'context.{i}' for i, c in enumerate(payload.get('context', [])) if c['speaker'] == 'human']
    evidence_key = 'source'
    human_evidence = human_sources
    if registry is not None:
        result['$defs']['Evidence'] = {'type': 'object', 'additionalProperties': False,
            'properties': {'ref': {'type': 'string', 'enum': list(registry),
                'description': 'Select a supplied evidence ID. Do not rewrite or translate the quote.'}},
            'required': ['ref']}
        evidence_key = 'ref'
        human_evidence = [key for key, item in registry.items() if item['source'] in human_sources]
    gap = result.get('$defs', {}).get('Gap')
    if gap is not None:
        # Match the engine's nonempty-comparison guard without banning one-sided gaps.
        gap['anyOf'] = [
            {'properties': {name: {'type': 'string', 'pattern': r'\S'}}, 'required': [name]}
            for name in ('human_premise', 'ai_premise')
        ]
    mapping_view = result.get('$defs', {}).get('MappingView')
    if mapping_view is not None and payload.get('ai_interpretation') is not None:
        mapping_view['properties']['hypotheses'].update({
            'maxItems': 0,
            'description': 'Empty in supplied-AI comparison mode. Compare submitted positions in premise_gaps; keep genuine interpretation limits in unresolved. Do not generate a third proposed plan.',
        })
    for name in ('Premise', 'CareDraft'):
        definition = result.get('$defs', {}).get(name)
        if definition is None:
            continue
        definition['allOf'] = [
            {'if': {'properties': {'source': {'const': 'user_explicit'}}, 'required': ['source']},
             'then': {'properties': {
                 'status': {'const': 'explicit'},
                 'evidence': {'items': {'properties': {evidence_key: {'enum': human_evidence}}}},
             }}},
            {'if': {'properties': {'source': {'enum': ['user_implied', 'agent_inference']}}, 'required': ['source']},
             'then': {'properties': {'status': {'enum': ['inferred', 'unclear']}}}},
        ]
    return result

def resolve_references(value, registry):
    """Expand exact validated quotes by ID, without model-generated paraphrases."""
    count = 0
    def visit(node):
        nonlocal count
        if isinstance(node, dict):
            result = {}
            for key, item in node.items():
                if key != 'evidence':
                    result[key] = visit(item)
                    continue
                if not isinstance(item, list):
                    raise ProviderError('provider_invalid_evidence_reference')
                resolved = []
                for entry in item:
                    count += 1
                    if (count > 640 or not isinstance(entry, dict) or set(entry) != {'ref'}
                            or not isinstance(entry['ref'], str) or entry['ref'] not in registry):
                        raise ProviderError('provider_invalid_evidence_reference')
                    resolved.append(dict(registry[entry['ref']]))
                result[key] = resolved
            return result
        if isinstance(node, list):
            return [visit(item) for item in node]
        return node
    return visit(value)

@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    api_key: str
    service_token: str
    json_mode: bool
    timeout: float

    @classmethod
    def from_env(cls):
        base = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
        u = urlsplit(base)
        if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('LLM_BASE_URL must be an http(s) base URL without credentials/query/fragment')
        model = os.getenv('LLM_MODEL', '').strip()
        if not model:
            raise ValueError('Set LLM_MODEL to your provider model ID')
        mode = os.getenv('LLM_JSON_MODE', 'true').lower()
        if mode not in ('true', 'false'):
            raise ValueError('LLM_JSON_MODE must be true or false')
        timeout = float(os.getenv('LLM_TIMEOUT_SECONDS', '90'))
        if not 1 <= timeout <= 300:
            raise ValueError('LLM_TIMEOUT_SECONDS must be 1..300')
        return cls(base, model, os.getenv('LLM_API_KEY', ''), os.getenv('SANA_API_TOKEN', ''), mode == 'true', timeout)

class Provider:
    def __init__(self, settings, client):
        self.settings, self.client = settings, client

    async def generate(self, instruction, payload, schema):
        s = self.settings
        body = {
            'model': s.model,
            'messages': [
                {'role': 'system', 'content': instruction + '\nReturn ONLY a JSON object conforming to this schema:\n' + json.dumps(generation_schema(schema, payload), ensure_ascii=False)},
                {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)},
            ],
        }
        if s.json_mode:
            body['response_format'] = {'type': 'json_object'}
        headers = {'Authorization': 'Bearer ' + s.api_key} if s.api_key else {}
        try:
            async with self.client.stream('POST', s.base_url + '/chat/completions', json=body, headers=headers, timeout=s.timeout) as response:
                if response.status_code == 429:
                    raise ProviderError('provider_rate_limited', 503)
                if response.status_code >= 400:
                    raise ProviderError('provider_http_error')
                chunks = bytearray()
                async for chunk in response.aiter_bytes():
                    chunks.extend(chunk)
                    if len(chunks) > 1_000_000:
                        raise ProviderError('provider_response_too_large')
            raw = json.loads(chunks)
            choice = raw['choices'][0]
            if choice.get('finish_reason') != 'stop' or choice['message'].get('refusal'):
                raise ProviderError('provider_incomplete_or_refused')
            if '_evidence_index' in payload:
                value = json.loads(choice['message']['content'])
                return schema.model_validate(resolve_references(value, payload['_evidence_index']))
            return schema.model_validate_json(choice['message']['content'])
        except httpx.TimeoutException:
            raise ProviderError('provider_timeout', 504) from None
        except httpx.RequestError:
            raise ProviderError('provider_unavailable', 503) from None
        except ValidationError as exc:
            for error in exc.errors():
                loc = error['loc']
                if len(loc) == 3 and loc[0] == 'care' and loc[2] == 'execution_effect':
                    raise ProviderError('provider_unexpected_care_effect', issue={
                        'path': f'care.{loc[1]}.execution_effect',
                        'rule': 'care_effect_is_server_supplied_null',
                    }) from None
            if any(len(e['loc']) == 3 and e['loc'][0] == 'care' and e['loc'][2] == 'support_state' for e in exc.errors()):
                raise ProviderError('provider_invalid_care_support') from None
            raise ProviderError('provider_invalid_output') from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError('provider_invalid_output') from None
