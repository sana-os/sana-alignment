"""Check real HTTP startup and deterministic handshake; no LLM credentials used."""
import http.client
import json
import time

for attempt in range(30):
    try:
        c = http.client.HTTPConnection('127.0.0.1',8000,timeout=2)
        c.request('GET','/healthz')
        r = c.getresponse()
        assert r.status == 200
        r.read(); c.close()
        break
    except (OSError, AssertionError):
        if attempt == 29: raise
        time.sleep(1)
for request, language, acknowledgment in [
    ({'input_message':'こんにちは'}, 'en', 'Hello.'),
    ({'input_message':'こんにちは', 'language':'ja'}, 'ja', 'こんにちは。'),
]:
    c = http.client.HTTPConnection('127.0.0.1',8000,timeout=2)
    c.request('POST','/v1/align',body=json.dumps(request,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'})
    r = c.getresponse(); data = json.loads(r.read()); c.close()
    assert r.status == 200, data
    assert data['schema_version'] == '0.5.0'
    assert data['status']=='handshake' and data['care'] is None
    assert data['meta']['execution_authorized'] is False
    assert data['meta']['requested_language'] == language
    assert data['acknowledgment'] == acknowledgment
    assert data['observations'][0]['quote'] == request['input_message']
print('HTTP smoke passed (no external model called)')
