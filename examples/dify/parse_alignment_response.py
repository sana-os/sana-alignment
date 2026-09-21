"""Paste into Dify's Parse response node; keep body/status_code inputs and outputs."""
import json


def main(body: str, status_code: int) -> dict:
    if status_code != 200:
        raise ValueError('SANA HTTP request failed')
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        raise ValueError('SANA response is not valid JSON') from None
    if not isinstance(data, dict) or data.get('schema_version') not in ('0.4.0', '0.5.0'):
        raise ValueError('Unexpected SANA response schema')
    allowed = {'handshake', 'unknown', 'context_insufficient', 'revision_required',
               'needs_clarification', 'mapped', 'mapped_with_divergence'}
    status = data.get('status')
    if not isinstance(status, str) or status not in allowed:
        raise ValueError('Unexpected SANA alignment status')
    meta = data.get('meta')
    if not isinstance(meta, dict) or meta.get('execution_authorized') is not False:
        raise ValueError('Unexpected SANA execution authority')
    if data['schema_version'] == '0.5.0':
        view = data.get('view')
        if (not isinstance(view, dict) or not isinstance(view.get('understanding'), str)
                or not isinstance(view.get('understanding_evidence'), list)
                or meta.get('understanding_mode') not in ('source_excerpts', 'short_reply')):
            raise ValueError('Unexpected SANA overview contract')
    return {'alignment_status': status, 'alignment_json': json.dumps(data, ensure_ascii=False)}
