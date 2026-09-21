"""Controlled reproduction of the missing field in the 0.5.14 low trace.

The full rejected candidate was not saved in metadata mode. These tests isolate
its reported violation; they do not claim to replay the original candidate.
"""
import pytest
from test_alignment import intake, draft
from test_modes_trace_0514 import api_run


@pytest.mark.parametrize('mode,status,calls', [('low',502,2),('medium',200,3)])
def test_missing_hypotheses_stops_low_and_is_reported_to_medium_repair(tmp_path,mode,status,calls):
    missing=draft(unknowns=[])
    del missing['view']['hypotheses']
    response,seen,trace=api_run(tmp_path,mode,[intake(),missing,draft(unknowns=[])])
    assert response.status_code==status and len(seen)==calls
    assert trace['model_calls'][1]['candidate_json'] is True
    first=trace['mapping_attempts'][0]
    assert first['error']['code']=='provider_invalid_output'
    assert first['error']['violations']==[{'code':'provider_invalid_output',
        'issue':{'path':'view.hypotheses','rule':'missing'}}]
    if mode=='low':
        assert first['retry_decision']=='limit_reached' and trace['retry_count']==0
        assert 'result' not in response.json()
    else:
        assert first['retry_decision']=='retry' and trace['retry_count']==1
        assert seen[2]['_mapping_feedback']['violations']==first['error']['violations']
        assert response.json()['view']['hypotheses']==[]
        assert response.json()['meta']['execution_authorized'] is False
