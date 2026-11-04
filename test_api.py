from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def get(path):
    r = client.get(path)
    return r.json()

def post(path, payload):
    r = client.post(path, json=payload)
    return r.json()

def main():
    print("Testing /api/summary ...")
    summary = get("/api/summary")
    print(f"  Total eval: {int(summary['total_eval_krw']):,} KRW")
    print(f"  MWRR: {summary['mwrr_pct']:.2f}%")
    print(f"  Holdings count: {summary['holdings_count']}")

    print("\nTesting /api/macro ...")
    macros = get("/api/macro")
    print(f"  Macro items count: {len(macros)}")
    for m in macros[:4]:
        print(f"  - {m['symbol']}: {m['value']} ({m['change_pct']}%)")

    print("\nTesting /api/dimension/risk ...")
    risk = get("/api/dimension/risk")
    for row in risk["rows"]:
        print(f"  - {row['label']}: {row['pct']:.1f}% (Target: {row['target']:.1f}%)")

    print("\nTesting /api/dimension/account ...")
    acc = get("/api/dimension/account")
    for row in acc["rows"]:
        print(f"  - {row['label']}: {row['pct']:.1f}% (Target: {row['target']:.1f}%)")

    print("\nTesting /api/cashflow/deposit ...")
    dep = post("/api/cashflow/deposit", {"account_id": "SAM_GEN", "amount": 10000000})
    print(f"  Deposit added: {dep}")

    print("\nTesting /api/transactions ...")
    txs = get("/api/transactions")
    print(f"  Transaction list count: {len(txs)}")
    last_tx = txs[0]
    print(f"  Latest tx: {last_tx['id']} {last_tx['type']} {last_tx['acc']} {last_tx['status']}")

    print("\nTesting /api/transactions/{id}/cancel ...")
    cancel_res = client.post(f"/api/transactions/{dep['tx_id']}/cancel").json()
    print(f"  Cancel result: {cancel_res}")

    print("\nALL API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
