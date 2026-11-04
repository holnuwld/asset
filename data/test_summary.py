import sys
sys.path.append('.')
from fastapi.testclient import TestClient
from backend.main import app

c = TestClient(app)
r = c.get('/api/summary')
print('Status:', r.status_code)
d = r.json()
print(f"Total eval: {d['total_eval_krw']:,.0f} KRW")
print(f"Invested:   {d['invested_principal']:,.0f} KRW")
print(f"MWRR:       {d['mwrr_pct']:.2f}%")
print(f"Holdings:   {d['holdings_count']}")
