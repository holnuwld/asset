import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.db.database import get_db

logger = logging.getLogger("backfill")

class BackfillEngine:
    def __init__(self, ledger_engine, valuation_engine):
        self.ledger_engine = ledger_engine
        self.val_engine = valuation_engine

    def run_catchup_sync(self, as_of_date: datetime):
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT MAX(snapshot_date) FROM daily_snapshots WHERE scope_type='TOTAL'")
        row = cur.fetchone()
        last_date_str = row[0] if row and row[0] else None

        if not last_date_str:
            start_date = as_of_date - timedelta(days=180)
        else:
            try:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                start_date = last_date + timedelta(days=1)
            except Exception:
                start_date = as_of_date - timedelta(days=7)

        if start_date > as_of_date:
            conn.close()
            return {"synced_days": 0, "message": "Already up to date"}

        cur.execute("SELECT * FROM accounts")
        accounts = [dict(r) for r in cur.fetchall()]
        accounts_map = {a["id"]: a for a in accounts}

        cur.execute("SELECT * FROM assets")
        assets = [dict(r) for r in cur.fetchall()]
        assets_map = {a["ticker"]: a for a in assets}

        cur.execute("SELECT * FROM opening_balances")
        opening_rows = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM transactions ORDER BY time, seq")
        tx_rows = [dict(r) for r in cur.fetchall()]

        curr = start_date
        synced_count = 0

        with conn:
            while curr <= as_of_date:
                curr_str = curr.strftime("%Y-%m-%d")
                txs_up_to_day = [t for t in tx_rows if t["time"][:10] <= curr_str]

                replay_res = self.ledger_engine.rebuild(opening_rows, txs_up_to_day, assets_map)
                val_res = self.val_engine.eval_portfolio(
                    replay_res["holdings"], assets_map,
                    replay_res["invested_principal"], replay_res["opening_principal"],
                    replay_res["processed_txs"], curr
                )

                cur.execute("""
                INSERT INTO daily_snapshots (snapshot_date, scope_type, dimension_key, category_key, eval_krw, invested_krw, weight_pct)
                VALUES (?, 'TOTAL', 'TOTAL', 'TOTAL', ?, ?, 100.0)
                ON CONFLICT(snapshot_date, scope_type, dimension_key, category_key) DO UPDATE SET
                    eval_krw=excluded.eval_krw,
                    invested_krw=excluded.invested_krw
                """, (curr_str, val_res["total_eval_krw"], val_res["invested_principal"]))

                synced_count += 1
                curr += timedelta(days=1)

        conn.close()
        return {"synced_days": synced_count, "from": start_date.strftime("%Y-%m-%d"), "to": as_of_date.strftime("%Y-%m-%d")}
