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
c = http.client.HTTPConnection('127.0.0.1',8000,timeout=2)
c.request('POST','/v1/align',body=json.dumps({'input_message':'こんにちは'}).encode(),headers={'Content-Type':'application/json'})
r = c.getresponse(); data = json.loads(r.read()); c.close()
assert r.status == 200, data
assert data['status']=='handshake' and data['care'] is None
assert data['meta']['execution_authorized'] is False
print('HTTP smoke passed (no external model called)')
