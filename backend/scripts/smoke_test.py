import json, time, threading, urllib.request, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT/'.venv'/'Scripts'/'python.exe'
PORT = 8010
BASE = f'http://127.0.0.1:{PORT}'

# Start server in a background process
proc = subprocess.Popen([str(VENV_PY), '-m', 'uvicorn', 'backend.main:app', '--port', str(PORT)], cwd=ROOT)
print('Started server PID', proc.pid)
# Wait for it to boot
for i in range(30):
    try:
        with urllib.request.urlopen(BASE + '/api/v1/health', timeout=0.5) as r:
            if r.status == 200:
                print('Health OK')
                break
    except Exception:
        time.sleep(0.3)
else:
    print('Server failed to start')
    proc.terminate(); sys.exit(1)

# Test reviews endpoint
payload_reviews = json.dumps({
    'reviews': [
        'Great battery life and bright screen',
        'Terrible camera, slow performance'
    ],
    'aspect_method': 'keywords'
}).encode()
req = urllib.request.Request(BASE + '/api/v1/analyze/reviews', data=payload_reviews, headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as resp:
    data_reviews = json.loads(resp.read().decode())
print('Reviews analysis:', json.dumps(data_reviews, indent=2))

# Test text endpoint
payload_text = json.dumps({
    'text': 'Battery is fantastic. Camera is awful. Design feels solid and nice.',
    'splitter': 'sentence',
    'aspect_method': 'keywords'
}).encode()
req2 = urllib.request.Request(BASE + '/api/v1/analyze/text', data=payload_text, headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req2) as resp:
    data_text = json.loads(resp.read().decode())
print('Text analysis:', json.dumps(data_text, indent=2))

proc.terminate()
proc.wait(timeout=5)
print('Server terminated.')
