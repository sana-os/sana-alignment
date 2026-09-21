"""Offline release checks; no model, Docker, Dify or network calls."""
import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'handshake', 'unknown', 'context_insufficient', 'revision_required',
            'needs_clarification', 'mapped', 'mapped_with_divergence'}


def check_workflow(filename):
    path = ROOT / 'examples/dify' / filename
    workflow = yaml.safe_load(path.read_text(encoding='utf-8'))
    graph = workflow['workflow']['graph']
    nodes = {n['id']: n['data'] for n in graph['nodes']}
    assert len(nodes) == len(graph['nodes'])
    assert workflow['dependencies'] == []
    types = {n['type'] for n in nodes.values()}
    planning = 'llm' in types
    assert types <= {'start', 'end', 'code', 'http-request', 'if-else', 'llm'}
    for edge in graph['edges']:
        assert edge['source'] in nodes and edge['target'] in nodes
    by_title = {n['title']: n for n in nodes.values()}
    functions = {}
    for title in ('Build request', 'Parse response'):
        node = by_title[title]
        assert node.get('error_strategy') in (None, 'none')
        assert not node.get('retry_config', {}).get('retry_enabled', False)
        namespace = {}
        exec(compile(node['code'], str(path) + ':' + title, 'exec'), namespace)
        functions[title] = namespace['main']
    build, parse = functions['Build request'], functions['Parse response']
    human = '表示 "quoted"\nKeep the input. \\path 😀'
    proposal = 'Draft: "fictional"\nsecond line'
    payload = json.loads(build(human, proposal, 'ja')['request_body'])
    assert payload == {'input_message': human, 'ai_interpretation': proposal,
                       'language': 'ja', 'processing_mode': 'medium'}
    assert json.loads(build(human, proposal, '')['request_body'])['language'] == 'en'
    try:
        build('   ', proposal, 'en')
    except ValueError:
        pass
    else:
        raise AssertionError('Empty human input accepted')
    if planning:
        model = next(n['model'] for n in nodes.values() if n['type'] == 'llm')
        assert model['provider'] == model['name'] == ''
        for message, plan in [(human, ''), ('x' * 6001, proposal), (human, 'x' * 6001)]:
            try:
                build(message, plan, 'en')
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid planning input accepted')
    else:
        assert 'ai_interpretation' not in json.loads(build('Hello', '', 'en')['request_body'])
    outputs = {}
    for node_id, node in nodes.items():
        if node['type'] == 'start':
            outputs[node_id] = {v['variable'] for v in node['variables']}
        elif node['type'] == 'code':
            outputs[node_id] = set(node['outputs'])
        elif node['type'] == 'http-request':
            outputs[node_id] = {'body', 'status_code', 'headers', 'files'}
            assert node['method'] == 'post' and node['body']['type'] == 'raw-text'
            assert not node['retry_config']['retry_enabled']
            assert node['ssl_verify'] is True
            assert node['timeout']['read'] == 600
            assert node['authorization']['type'] == 'no-auth'
        elif node['type'] == 'llm':
            outputs[node_id] = {'text'}
    env = {e['name'] for e in workflow['workflow']['environment_variables']}

    def selector(value):
        assert len(value) == 2
        owner, variable = value
        assert variable in (env if owner == 'env' else outputs[owner]), value

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('value_selector', 'variable_selector'):
                    if not (key == 'variable_selector' and item == [] and value.get('enabled') is False):
                        selector(item)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            for match in re.findall(r'\{\{#([^#]+)#\}\}', value):
                selector(match.split('.'))
    walk(workflow)
    for status in STATUSES:
        result = {'schema_version': '0.5.0', 'status': status,
                  'meta': {'execution_authorized': False, 'understanding_mode': 'source_excerpts'},
                  'view': {'understanding': 'Quoted source', 'understanding_evidence': []}}
        parsed = parse(json.dumps(result), 200)
        assert parsed['alignment_status'] == status
        assert json.loads(parsed['alignment_json']) == result
        branch_id = next(k for k, n in nodes.items() if n['type'] == 'if-else')
        branch = nodes[branch_id]
        matches = [c['case_id'] for c in branch['cases']
                   if all(cond['comparison_operator'] == 'is' and cond['value'] == status
                          for cond in c['conditions'])]
        handle = matches[0] if matches else 'false'
        edge = next(e for e in graph['edges'] if e['source'] == branch_id and e['sourceHandle'] == handle)
        end = nodes[edge['target']]
        assert end['type'] == 'end'
        expected = 'Revision required' if status == 'revision_required' else 'Premise map ready' if status == 'mapped' else 'Other alignment result'
        assert end['title'] == expected
    for body, status_code in [('{}', 502), ('not-json', 200), ('[]', 200),
                              ('{"schema_version":"invalid"}', 200)]:
        try:
            parse(body, status_code)
        except ValueError:
            pass
        else:
            raise AssertionError('Malformed response accepted')
    preserved = 0
    for fixture in sorted((ROOT / 'tests/fixtures').glob('observed-0.5.15-*-response.json')):
        result = json.loads(fixture.read_text(encoding='utf-8'))
        assert json.loads(parse(json.dumps(result), 200)['alignment_json']) == result
        preserved += 1
    assert preserved == 3
    return {'workflow': filename, 'status_routes': len(STATUSES), 'observed_responses_preserved': preserved}


def check_archive():
    base = ROOT / 'docs/validation/archive'
    records = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))['records']
    for item in records:
        raw = (base / item['archive_file']).read_bytes()
        assert len(raw) == item['bytes']
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
    assert len(records) == 30
    return {'attachments': len(records), 'distinct_files': len({r['archive_file'] for r in records})}


if __name__ == '__main__':
    print(json.dumps({'scope': 'offline checks; not a live Dify or model run',
        'workflows': [check_workflow(n) for n in ('sana-alignment.en.yml', 'sana-plan-and-align.en.yml')],
        'archive': check_archive()}, indent=2))
