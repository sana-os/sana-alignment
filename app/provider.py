import json
import os
from dataclasses import dataclass
from urllib.parse import urlsplit
import httpx
from pydantic import ValidationError

class ProviderError(Exception):
    def __init__(self, code='provider_error', status=502):
        self.code, self.status = code, status
        super().__init__(code)

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
                {'role': 'system', 'content': instruction + '\nReturn ONLY a JSON object conforming to this schema:\n' + json.dumps(schema.model_json_schema(), ensure_ascii=False)},
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
            return schema.model_validate_json(choice['message']['content'])
        except httpx.TimeoutException:
            raise ProviderError('provider_timeout', 504) from None
        except httpx.RequestError:
            raise ProviderError('provider_unavailable', 503) from None
        except (ValueError, KeyError, IndexError, TypeError, ValidationError):
            raise ProviderError('provider_invalid_output') from None
