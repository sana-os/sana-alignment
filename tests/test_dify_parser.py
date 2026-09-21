import json
from pathlib import Path
import runpy
import pytest

main = runpy.run_path(str(Path(__file__).resolve().parent.parent / 'examples/dify/parse_alignment_response.py'))['main']

def response(version):
    return dict(schema_version=version,status='mapped',meta=dict(execution_authorized=False,
        understanding_mode='source_excerpts'),view=dict(understanding='[input_message]\n表示',understanding_evidence=[]))

@pytest.mark.parametrize('version',['0.4.0','0.5.0'])
def test_parser_preserves_data_across_migration(version):
    value=response(version)
    out=main(json.dumps(value,ensure_ascii=False),200)
    assert out['alignment_status']=='mapped'
    assert json.loads(out['alignment_json'])==value

@pytest.mark.parametrize('fault',['http','json','version','status','authority','overview'])
def test_parser_cannot_turn_errors_into_success(fault):
    v=response('0.5.0')
    if fault=='version': v['schema_version']='9.0.0'
    if fault=='status': v['status']='approved'
    if fault=='authority': v['meta']['execution_authorized']=True
    if fault=='overview': v['view']['understanding_evidence']=None
    with pytest.raises(ValueError):
        main('not json' if fault=='json' else json.dumps(v),502 if fault=='http' else 200)
