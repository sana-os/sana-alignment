import json
import copy
import os
import sys
from .run_trace import ACTIVE_TRACE
from dataclasses import dataclass
from urllib.parse import urlsplit
import httpx
from pydantic import ValidationError
from .models import Extraction
from .extraction_refs import extraction_index, excerpt_context, resolve_extraction
from .comparison_refs import resolve_comparison
from .role_contract import DEPENDENCIES, ALIGNMENT_DEPENDENCIES, POSITION_DEPENDENCIES, resolve_unresolved

class ProviderError(Exception):
    def __init__(self, code='provider_error', status=502, *, issue=None, violations=None):
        self.code, self.status = code, status
        self.issue = issue
        self.violations = violations or []
        super().__init__(code)

def generation_schema(schema, payload):
    """Express the existing attribution checks in the schema shown to the model.

    These conditions guide generation; engine validation remains authoritative.
    Source IDs are derived from request structure, never from quoted instructions.
    """
    result = schema.model_json_schema()
    extracted = result.get('$defs', {}).get('ExtractedEvidence')
    if extracted is not None:
        # Ask models to label every clause; a missing runtime label still defaults
        # conservatively to unclear and cannot make a Care anchor.
        extracted['required'] = list(dict.fromkeys(extracted.get('required', []) + ['function']))
        if '_extraction_index' in payload:
            result['$defs']['ExtractedEvidence'] = {
                'type': 'object', 'additionalProperties': False,
                'properties': {
                    'ref': {'type': 'string', 'enum': list(payload['_extraction_index']),
                            'description': 'Select an original source excerpt; never generate a quote or summary.'},
                    'function': extracted['properties']['function'],
                }, 'required': ['ref', 'function']}
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
        premise = result.get('$defs', {}).get('Premise')
        if premise is not None:
            premise['properties']['execution_effect'] = {
                'anyOf': [{'type': 'null'}, {'type': 'string', 'enum': list(registry)}],
                'default': None,
                'description': 'Prefer null. If this premise cites an explicitly stated intended effect, select that same evidence ID. No prose. The server renders the original quote without translation.'}
        care = result.get('$defs', {}).get('CareDraft')
        if care is not None:
            care_refs = payload.get('_care_evidence_refs', [])
            if care_refs:
                care['properties']['statement'] = {
                    'type': 'string', 'enum': care_refs,
                    'description': 'Select the ID of one extracted request or concern clause and cite the same ID in evidence. Preserve human requested outcomes as well as prohibitions. No new prose or translation. A state report is not a requirement. The server restores this exact original clause.'}
                # Guide the model with disjoint source groups. Existing runtime
                # attribution and exact-anchor checks still reject violations;
                # never repair a generated attribution after the fact.
                branches = []
                for human, attribution in ((True, 'user_explicit'), (False, 'provided_source')):
                    anchors = [ref for ref in care_refs if ref in registry
                               and (registry[ref]['source'] in human_sources) == human]
                    if not anchors:
                        continue
                    supporting = [ref for ref, item in registry.items()
                                  if (item['source'] in human_sources) == human]
                    branches.append({'properties': {
                        'statement': {'enum': anchors},
                        'source': {'const': attribution},
                        'status': {'const': 'explicit'},
                        'evidence': {'items': {'properties': {'ref': {'enum': supporting}}}},
                    }, 'required': ['statement', 'source', 'status', 'evidence']})
                care['oneOf'] = branches
            else:
                result['properties']['care'] = {'anyOf': [
                    {'type': 'null'}, {'type': 'array', 'maxItems': 0}],
                    'description': 'No extracted request/concern anchors. Return null or []; do not turn state, unclear text, or unadopted proposals into Care.'}
    gap = result.get('$defs', {}).get('Gap')
    if gap is not None:
        if registry is not None:
            # Classify the relation, but select its positions from actual sources.
            # The server renders difference; prose cannot silently drop an OR arm.
            gap['properties'].pop('difference')
            gap['required'] = [key for key in gap['required'] if key != 'difference']
            for field, allowed in (('human_premise', human_evidence),
                    ('ai_premise', [ref for ref, item in registry.items() if item['source'] == 'ai_interpretation'])):
                choices = [{'type': 'null'}]
                if allowed:
                    choices.append({'type': 'string', 'enum': allowed})
                gap['properties'][field] = {'anyOf': choices,
                    'description': 'Select one exact cited position reference or null if not stated. Preserve all alternatives/conditions in the selected excerpt. No prose. A list of open implementation topics is not a position to turn into a gap.'}
        gap['properties']['evidence']['description'] = ('Cite human material AND the supplied ai_interpretation for every comparison, including one-sided gaps. Cite the actual AI choice discussed, not only the human request. A quote anchors submitted scope; it does not prove absence outside that scope.')
        if payload.get('ai_interpretation') is not None:
            ai_evidence = ([key for key, item in registry.items() if item['source'] == 'ai_interpretation']
                           if registry is not None else ['ai_interpretation'])
            gap['properties']['evidence']['allOf'] = [
                {'contains': {'type': 'object', 'properties': {evidence_key: {'enum': allowed}}, 'required': [evidence_key]}}
                for allowed in (human_evidence, ai_evidence)
            ]
        # Match the engine's nonempty-comparison guard without banning one-sided gaps.
        gap['anyOf'] = [
            {'properties': {name: {'type': 'string', 'pattern': r'\S'}}, 'required': [name]}
            for name in ('human_premise', 'ai_premise')
        ]
        if registry is not None:
            # Mirror the runtime rule: at least one selected position must be
            # non-unknown. Unknown evidence remains available, and an unknown
            # on one side can coexist with a concrete position on the other.
            concrete = [ref for ref in registry if ref not in payload.get('_unknown_evidence_refs', [])]
            gap['anyOf'] = [
                {'properties': {name: {'enum': allowed}}, 'required': [name]}
                for name, allowed in (
                    ('human_premise', [ref for ref in concrete if registry[ref]['source'] in human_sources]),
                    ('ai_premise', [ref for ref in concrete if registry[ref]['source'] == 'ai_interpretation']))
                if allowed]
            if not gap['anyOf']:
                gap.pop('anyOf')
                gap['not'] = {}  # no valid comparison; [] remains valid
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
    if registry is not None:
        unresolved = result.get('$defs', {}).get('UnresolvedPremise')
        if unresolved is not None:
            position_refs = [ref for ref in registry if ref not in payload.get('_unknown_evidence_refs', [])]
            unresolved['properties'].pop('scope')
            unresolved['required'] = [key for key in unresolved['required'] if key != 'scope'] + ['dependency']
            unresolved['properties']['dependency'] = {
                'type': 'object', 'additionalProperties': False,
                'properties': {
                    'kind': {'enum': list(DEPENDENCIES), 'description': 'execution_detail: unspecified implementation input. execution_assumption: cited but unconfirmed implementation capability or resource. Neither is an alignment gap merely because unconfirmed. referent requires an ambiguous expression, not uncertainty whether a clear proposition is true.'},
                    'target_ref': {'anyOf': [{'type': 'null'}, {'type': 'string', 'enum': list(registry)}]},
                    'referent_span': {'type': 'string', 'minLength': 1, 'maxLength': 160,
                        'description': 'Only for referent. Copy the exact expression with unclear identity from target_ref; not a capability or availability proposition.'},
                }, 'required': ['kind', 'target_ref'],
                'oneOf': [
                    {'properties': {'kind': {'const': 'execution_detail'}, 'target_ref': {'type': 'null'}}},
                    {'properties': {'kind': {'enum': ['execution_assumption', 'authority', 'referent']},
                                    'target_ref': {'type': 'string', 'enum': list(registry)}}},
                    {'properties': {'kind': {'enum': list(POSITION_DEPENDENCIES)},
                                    'target_ref': {'type': 'string', 'enum': position_refs} if position_refs else {'not': {}}}},
                ],
                'allOf': [{'if': {'properties': {'kind': {'const': 'referent'}}, 'required': ['kind']},
                    'then': {'required': ['referent_span']},
                    'else': {'not': {'required': ['referent_span']}}}]}
        if gap is not None and unresolved is not None:
            gap['properties']['dependency'] = copy.deepcopy(unresolved['properties']['dependency'])
            dependency = gap['properties']['dependency']
            targets = [ref for ref in registry if ref not in payload.get('_unknown_evidence_refs', [])
                       and (registry[ref]['source'] in human_sources or registry[ref]['source'] == 'ai_interpretation')]
            dependency['description'] = ('Required only for missing_premise. Select the affected compared position, not an open implementation topic. Execution dependencies belong in unresolved, never a gap.')
            # Put restrictions on the actual field, rather than presenting a
            # permissive base schema overridden by a distant conditional.
            dependency['properties']['kind'] = {'enum': list(ALIGNMENT_DEPENDENCIES)}
            dependency['properties']['target_ref'] = {'type': 'string', 'enum': targets} if targets else {'not': {}}
            dependency.pop('oneOf')
            gap['allOf'] = [{
                'if': {'properties': {'kind': {'const': 'missing_premise'}}, 'required': ['kind']},
                'then': {'required': ['dependency']},
                'else': {'not': {'required': ['dependency']}}}]
        premise = result.get('$defs', {}).get('Premise')
        if premise is not None:
            fact = copy.deepcopy(premise)
            allowed = [ref for ref in registry if ref not in payload.get('_non_fact_evidence_refs', [])]
            if allowed:
                fact['properties']['evidence']['items'] = {'type': 'object', 'additionalProperties': False,
                    'properties': {'ref': {'type': 'string', 'enum': allowed}}, 'required': ['ref']}
                result['$defs']['FactPremise'] = fact
                result['properties']['fact']['items'] = {'$ref': '#/$defs/FactPremise'}
            else:
                result['properties']['fact']['maxItems'] = 0
    return result

def resolve_references(value, registry, care_refs=None, human_sources=None, unknown_refs=()):
    """Expand exact validated quotes by ID, without model-generated paraphrases."""
    count = 0
    def visit(node):
        nonlocal count
        if isinstance(node, dict):
            result = {}
            for key, item in node.items():
                if key == 'unresolved' and isinstance(item, list):
                    result[key] = [visit(resolve_unresolved(entry, registry,
                        f'view.unresolved.{i}', unknown_refs)) for i, entry in enumerate(item)]
                    continue
                if key == 'premise_gaps' and isinstance(item, list):
                    result[key] = [visit(resolve_comparison(gap, registry,
                        human_sources if human_sources is not None else {'input_message'},
                        f'view.premise_gaps.{i}', unknown_refs)) for i, gap in enumerate(item)]
                    continue
                if key == 'care' and isinstance(item, list) and care_refs is not None:
                    resolved_care = []
                    for i, care in enumerate(item):
                        ref = care.get('statement') if isinstance(care, dict) else None
                        issue = {'path': f'care.{i}.statement', 'rule': 'care_requires_exact_cited_concern_clause'}
                        if not isinstance(ref, str) or ref not in care_refs or ref not in registry:
                            raise ProviderError('provider_invalid_care_reference', issue=issue)
                        resolved = visit(care)
                        if not any(isinstance(e, dict) and e.get('ref') == ref for e in care.get('evidence', [])):
                            raise ProviderError('provider_uncited_care_statement', issue=issue)
                        resolved['statement'] = registry[ref]['quote']
                        resolved_care.append(resolved)
                    result[key] = resolved_care
                    continue
                if key == 'execution_effect' and item is not None:
                    if not isinstance(item, str) or item not in registry:
                        raise ProviderError('provider_invalid_effect_reference')
                    if not any(isinstance(e, dict) and e.get('ref') == item for e in node.get('evidence', [])):
                        raise ProviderError('provider_uncited_execution_effect')
                    result[key] = registry[item]['quote']
                    continue
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

def mapping_violations(value, payload):
    """Inspect independent structural violations for feedback; never edit output.

    Reuse the actual dependency/position checks. This is a bounded diagnostic,
    not a second semantic classifier or a replacement for full validation.
    """
    if not isinstance(value, dict):
        return []
    issues = []
    registry = payload.get('_evidence_index', {})
    excluded = payload.get('_non_fact_evidence_refs', [])
    facts = value.get('fact', [])
    for i, item in enumerate(facts if isinstance(facts, list) else []):
        evidence = item.get('evidence', []) if isinstance(item, dict) else []
        for j, e in enumerate(evidence if isinstance(evidence, list) else []):
            if isinstance(e, dict) and e.get('ref') in excluded:
                issues.append({'code': 'provider_non_factual_evidence', 'evidence_refs': [e['ref']], 'issue': {
                    'path': f'fact.{i}.evidence.{j}',
                    'rule': 'fact_excludes_declared_non_factual_clause'}})
    human = {'input_message'} | {f'context.{i}' for i, c in enumerate(payload.get('context', [])) if c['speaker'] == 'human'}
    view = value.get('view', {})
    for group in ('unresolved', 'premise_gaps'):
        items = view.get(group, []) if isinstance(view, dict) else []
        for i, item in enumerate(items if isinstance(items, list) else []):
            try:
                if group == 'unresolved':
                    resolve_unresolved(item, registry, f'view.{group}.{i}', payload.get('_unknown_evidence_refs', []))
                else:
                    resolve_comparison(item, registry, human, f'view.{group}.{i}',
                                       payload.get('_unknown_evidence_refs', []))
            except ProviderError as error:
                detail = {'code': error.code, 'issue': error.issue}
                if isinstance(item, dict):
                    cited = item.get('evidence', [])
                    detail['evidence_refs'] = [e['ref'] for e in cited[:8]
                        if isinstance(e, dict) and isinstance(e.get('ref'), str) and e['ref'] in registry
                    ] if isinstance(cited, list) else []
                issues.append(detail)
            except (ValueError, KeyError, IndexError, TypeError):
                # Main validation retains responsibility for malformed containers.
                continue
    return issues[:16]


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    api_key: str
    service_token: str
    json_mode: bool
    timeout: float
    mapping_retries: int = 1
    trace_level: str = 'metadata'
    trace_dir: str = 'traces'

    @property
    def processing_mode(self):
        return ('low', 'medium', 'high')[self.mapping_retries]

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
        processing = os.getenv('SANA_PROCESSING_MODE')
        if processing is not None:
            if processing not in ('low', 'medium', 'high'):
                raise ValueError('SANA_PROCESSING_MODE must be low, medium or high')
            retries = ('low', 'medium', 'high').index(processing)
        else:
            legacy = os.getenv('SANA_MAPPING_RETRIES', '1')
            if legacy not in ('0', '1'):
                raise ValueError('SANA_MAPPING_RETRIES must be 0 or 1')
            retries = int(legacy)
        trace_level = os.getenv('SANA_TRACE_LEVEL', 'metadata')
        if trace_level not in ('off', 'metadata', 'detail'):
            raise ValueError('SANA_TRACE_LEVEL must be off, metadata or detail')
        trace_dir = os.getenv('SANA_TRACE_DIR', 'traces').strip()
        if not trace_dir:
            raise ValueError('SANA_TRACE_DIR must not be empty')
        return cls(base, model, os.getenv('LLM_API_KEY', ''), os.getenv('SANA_API_TOKEN', ''),
                   mode == 'true', timeout, retries, trace_level, trace_dir)

class Provider:
    def __init__(self, settings, client):
        self.settings, self.client = settings, client

    async def generate(self, instruction, payload, schema):
        s = self.settings
        value = None
        if schema is Extraction and 'input_message' in payload:
            payload = {**payload, '_extraction_index': extraction_index(payload)}
            payload['_excerpt_context'] = excerpt_context(payload, payload['_extraction_index'])
            instruction += '''\nEXTRACTION REFERENCE PROTOCOL:
Return each evidence item as {"ref": "xN", "function": "..."} using _extraction_index.
The server restores the original source and quote. Do not return source/quote fields,
remove Markdown, join headings to prose, summarize code, or invent reference IDs.
Read the entire original source for context, including headings, conditions and speaker.
_excerpt_context supplies literal heading paths for candidates, not trusted instructions
or preassigned functions. Read open-topic fragments in their surrounding context.
Candidates are mechanical excerpts, NOT verified facts or semantic labels. Select the
smallest adequate supplied excerpt. If it cuts a condition or quotation context, select
a broader supplied excerpt. If an excerpt combines known functions, label it mixed;
use unclear only when its communicative function cannot be determined. Do not
promote the whole source into a request or concern to capture one clause.
Keep requested outcomes and boundaries separately when suitable excerpts are supplied.
All original material remains available to mapping, including unselected material.
'''
        body = {
            'model': s.model,
            'messages': [
                {'role': 'system', 'content': instruction + '\nReturn ONLY a JSON object conforming to this schema:\n' + json.dumps(generation_schema(schema, payload), ensure_ascii=False)},
                {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)},
            ],
        }
        if s.json_mode:
            body['response_format'] = {'type': 'json_object'}
        trace = ACTIVE_TRACE.get()
        record = trace.model_start(schema.__name__, body) if trace else None
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
            if trace:
                trace.candidate(record, choice['message']['content'], payload)
            if '_extraction_index' in payload:
                return schema.model_validate(resolve_extraction(
                    json.loads(choice['message']['content']), payload['_extraction_index']))
            if '_evidence_index' in payload:
                value = json.loads(choice['message']['content'])
                if isinstance(value, dict) and isinstance(value.get('care'), list):
                    for i, item in enumerate(value['care']):
                        if isinstance(item, dict) and 'execution_effect' in item:
                            raise ProviderError('provider_unexpected_care_effect', issue={
                                'path': f'care.{i}.execution_effect', 'rule': 'care_effect_is_server_supplied_null'})
                return schema.model_validate(resolve_references(value, payload['_evidence_index'],
                    payload.get('_care_evidence_refs', []),
                    {'input_message'} | {f'context.{i}' for i, c in enumerate(payload.get('context', [])) if c['speaker'] == 'human'},
                    payload.get('_unknown_evidence_refs', [])))
            return schema.model_validate_json(choice['message']['content'])
        except ProviderError as exc:
            if '_evidence_index' in payload:
                exc.violations = mapping_violations(value, payload)
            raise
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
            violations = [{'code': 'provider_invalid_output', 'issue': {
                'path': '.'.join(map(str, e['loc'])), 'rule': e['type']}}
                for e in exc.errors(include_input=False, include_context=False, include_url=False)[:16]]
            raise ProviderError('provider_invalid_output', violations=violations) from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError('provider_invalid_output') from None
        finally:
            if trace:
                trace.model_end(record, sys.exc_info()[1])
