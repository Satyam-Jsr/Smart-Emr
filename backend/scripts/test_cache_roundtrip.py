"""Test cache roundtrip:
1) Run init_db() to create any missing tables
2) POST to /patients/1/summarize
3) Print response and check summary_cache table for entries
"""
import sys
import os
# Ensure backend package directory is on sys.path so `import app` works when run from this script
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.database import init_db, SessionLocal
from app.models import SummaryCache
import requests
import json
import os

# ensure DB tables
init_db()
print('init_db done')

# call summarize endpoint
url = os.environ.get('SUMMARIZE_URL', 'http://localhost:8000/patients/1/summarize')
print('POST', url)
resp = requests.post(url, json={})
print('status', resp.status_code)
try:
    payload = resp.json()
    print('response JSON:\n', json.dumps(payload, indent=2))
except Exception as e:
    print('failed to parse json response', e)

# inspect DB
s = SessionLocal()
rows = s.query(SummaryCache).filter(SummaryCache.patient_id == 1).order_by(SummaryCache.updated_at.desc()).all()
print('found cached rows:', len(rows))
for r in rows:
    print('id=', r.id, 'patient_id=', r.patient_id, 'source=', r.source, 'updated_at=', r.updated_at)
    try:
        parsed = json.loads(r.summary_json)
        print('cached one_line:', parsed.get('one_line'))
    except Exception as e:
        print('cached parse failed', e)
s.close()
