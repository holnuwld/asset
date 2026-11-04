import json

with open('data/assets_master.json', 'r', encoding='utf-8') as f:
    assets = json.load(f)

with open('data/opening_master.json', 'r', encoding='utf-8') as f:
    opening = json.load(f)

seed_py = '''import json
from datetime import datetime
from backend.db.database import get_db

def seed_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM accounts")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    accounts = [
        ("SAM_GEN", "삼성증권", "삼성증권 (종합/주식보상S)", "일반위탁", '["KR_STOCK","KR_ETF","CASH"]', 35.0, "KRW"),
        ("NAMU_GEN", "나무증권", "나무증권 (평생우대 CMA)", "CMA/위탁", '["KR_STOCK","KR_ETF","CASH"]', 25.0, "KRW"),
        ("KIW_OVS", "키움증권", "키움증권 (해외직투/외화RP)", "해외직투", '["US_STOCK","US_ETF","JP_STOCK","JP_ETF","RP","CASH"]', 12.0, "USD"),
        ("NAMU_GOLD", "나무증권", "나무증권 (KRX금현물)", "금현물", '["KRX_GOLD","CASH"]', 7.0, "KRW"),
        ("KB_PEN", "KB증권", "KB증권 (신연금저축)", "연금저축", '["KR_ETF","CASH"]', 6.0, "KRW"),
        ("KIW_ISA", "키움증권", "키움증권 (중개형ISA)", "ISA", '["KR_STOCK","KR_ETF","RP","CASH"]', 5.0, "KRW"),
        ("MG_DEP", "새마을금고", "새마을금고 (정기예탁금)", "정기예금", '["DEPOSIT"]', 3.0, "KRW"),
        ("SAM_IRP", "삼성증권", "삼성증권 (퇴직연금 IRP)", "IRP", '["KR_ETF","CASH"]', 3.0, "KRW"),
        ("TOSS_FX", "토스뱅크", "토스뱅크 (외화통장 엔화)", "외화예금", '["CASH"]', 4.0, "JPY")
    ]
    cur.executemany("""
    INSERT INTO accounts (id, broker, name, account_type, allowed_markets, target_pct, base_currency)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, accounts)

    assets_data = [
'''

for k, v in sorted(assets.items()):
    dep_rate = 0.038 if v['kind'] == 'DEPOSIT' else None
    dep_start = "2025-11-03" if v['kind'] == 'DEPOSIT' else None
    dep_mat = "2027-11-03" if v['kind'] == 'DEPOSIT' else None
    seed_py += f"        ({json.dumps(k, ensure_ascii=False)}, {json.dumps(v['name'], ensure_ascii=False)}, '{v['market']}', '{v['currency']}', '{v['kind']}', {v['price']}, {v['prev']}, {v['high52']}, '{v['exp']['risk']}', '{v['exp']['currency']['real']}', '{v['exp']['currency']['listing']}', {json.dumps(v['exp']['country']) if v['exp']['country'] else 'None'}, '{v['exp']['liquidity']}', {dep_rate if dep_rate is not None else 'None'}, {json.dumps(dep_start) if dep_start else 'None'}, {json.dumps(dep_mat) if dep_mat else 'None'}),\n"

seed_py += '''    ]
    cur.executemany("""
    INSERT INTO assets (ticker, name, market, currency, kind, price, prev_price, high_52w, exp_risk, exp_currency_real, exp_currency_listing, exp_country, exp_liquidity, deposit_rate, deposit_start, deposit_maturity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, assets_data)

    opening_data = [
'''

for op in opening:
    fx_val = op.get('fx', 1.0)
    seed_py += f"        ('{op['acc']}', '{op['t']}', {op['qty']}, {op['avg']}, {fx_val}),\n"

seed_py += '''    ]
    cur.executemany("""
    INSERT INTO opening_balances (account_id, ticker, quantity, avg_price, avg_fx)
    VALUES (?, ?, ?, ?, ?)
    """, opening_data)

    # Initial transactions
    tx_data = [
        ("TX-1001", 1001, "2026-10-15 10:15", "TELEGRAM", "SAM_GEN", "BUY", "005930", 50, 220000.0, 0, 1.0, "ACTIVE", "[삼성증권] 매수체결 삼성전자 50주 단가 220,000원", "국내주식 체결"),
        ("TX-1002", 1002, "2026-10-22 14:20", "TELEGRAM", "KIW_OVS", "SELL", "TSLA", 5, 410.0, 0, 1341.0, "ACTIVE", "[키움증권] 해외주식 매도 TSLA 5주 체결가 $410.00", "해외주식 체결"),
        ("TX-1003", 1003, "2026-10-28 11:00", "TELEGRAM", "NAMU_GOLD", "BUY", "GOLD-KRX", 10, 169000.0, 0, 1.0, "ACTIVE", "[나무증권] 매수체결 금현물 10g 단가 169,000원", "국내/금현물 체결"),
        ("TX-1004", 1004, "2026-11-01 09:30", "TELEGRAM(명령)", "SAM_GEN", "DEPOSIT", "CASH-KRW-SAMGEN", 10000000.0, 1.0, 0, 1.0, "ACTIVE", "/입금 삼성종합 10000000", "외부 원금 추가납입")
    ]
    cur.executemany("""
    INSERT INTO transactions (id, seq, time, source, acc, type, ticker, qty, price, fee, fx, status, raw, parser)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tx_data)

    conn.commit()
    conn.close()
    print("Database seeded successfully with 2026-11-03 portfolio data.")

if __name__ == "__main__":
    from backend.db.database import init_db
    import os
    if os.path.exists("data/asset.db"):
        os.remove("data/asset.db")
    init_db()
    seed_db()
'''

with open('backend/db/seed.py', 'w', encoding='utf-8') as f:
    f.write(seed_py)

print("Updated backend/db/seed.py successfully.")
