from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from backend.db.database import get_db, init_db
from backend.db.seed import seed_db
from backend.core.ledger import LedgerEngine
from backend.core.valuation import ValuationEngine
from backend.core.dimensions import DimensionsEngine
from backend.core.backfill import BackfillEngine
from backend.market.fetcher import MarketFetcher

app = FastAPI(title="AssetFlow API", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# App State / Engines
FX_CURRENT = {"KRW": 1.0, "USD": 1385.0, "JPY": 9.215}
ledger_engine = LedgerEngine(FX_CURRENT)
val_engine = ValuationEngine(FX_CURRENT)
fetcher = MarketFetcher()

def load_db_state():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts")
    accounts = [dict(r) for r in cur.fetchall()]
    accounts_map = {a["id"]: a for a in accounts}

    cur.execute("SELECT * FROM assets")
    assets = [dict(r) for r in cur.fetchall()]
    assets_map = {a["ticker"]: a for a in assets}

    cur.execute("SELECT * FROM opening_balances")
    opening = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM transactions ORDER BY time, seq")
    transactions = [dict(r) for r in cur.fetchall()]

    conn.close()
    return accounts_map, assets_map, opening, transactions

@app.on_event("startup")
def startup_event():
    init_db()
    seed_db()
    accounts_map, assets_map, opening, transactions = load_db_state()
    backfill = BackfillEngine(ledger_engine, val_engine)
    backfill.run_catchup_sync(datetime.now())

# ==========================================
#  API Endpoints
# ==========================================

@app.get("/api/summary")
def get_summary(ccy_mode: str = "real", abs_tol: float = 5.0, rel_tol: float = 25.0):
    accounts_map, assets_map, opening, transactions = load_db_state()
    dims_engine = DimensionsEngine(accounts_map)
    now = datetime.now()

    replay_res = ledger_engine.rebuild(opening, transactions, assets_map)
    val_res = val_engine.eval_portfolio(
        replay_res["holdings"], assets_map,
        replay_res["invested_principal"], replay_res["opening_principal"],
        replay_res["processed_txs"], now
    )

    drifts = dims_engine.evaluate_all_drifts(
        replay_res["holdings"], assets_map,
        lambda h, a: val_engine.eval_holding_krw(h, a, now),
        ccy_mode=ccy_mode, abs_tol=abs_tol, rel_tol=rel_tol
    )

    this_month_str = now.strftime("%Y-%m")
    this_year_str = now.strftime("%Y-")

    month_realized = 0.0
    year_realized = 0.0
    overseas_stock_realized = 1150000.0

    for tx in replay_res["processed_txs"]:
        if tx.get("realized_pnl") is not None:
            t_time = tx["time"]
            r_val = float(tx["realized_pnl"])
            if t_time.startswith(this_month_str):
                month_realized += r_val
            if t_time.startswith(this_year_str):
                year_realized += r_val
                a = assets_map.get(tx["ticker"])
                if a and a["market"] in ("US_STOCK", "US_ETF", "JP_STOCK", "JP_ETF"):
                    overseas_stock_realized += r_val

    return {
        "as_of": now.strftime("%Y-%m-%d %H:%M"),
        "total_eval_krw": val_res["total_eval_krw"],
        "invested_principal": val_res["invested_principal"],
        "external_net_cashflow": replay_res["external_cashflow"],
        "total_gain_krw": val_res["total_gain_krw"],
        "simple_roi_pct": val_res["simple_roi_pct"],
        "mwrr_pct": val_res["mwrr_pct"],
        "price_pnl_krw": val_res["price_pnl_krw"],
        "fx_pnl_krw": val_res["fx_pnl_krw"],
        "accrued_interest_krw": val_res["accrued_interest_krw"],
        "drifts_count": len(drifts),
        "top_drift": drifts[0] if drifts else None,
        "this_month_realized": month_realized,
        "this_year_realized": year_realized,
        "overseas_stock_realized": overseas_stock_realized,
        "overseas_tax_remain": max(0.0, 2500000.0 - overseas_stock_realized),
        "holdings_count": len([h for h in replay_res["holdings"].values() if abs(h["quantity"]) > 1e-9]),
        "ticker_list": val_res["ticker_list"],
        "accounts": list(accounts_map.values())
    }

@app.get("/api/dimension/{dim_key}")
def get_dimension(dim_key: str, ccy_mode: str = "real", abs_tol: float = 5.0, rel_tol: float = 25.0):
    accounts_map, assets_map, opening, transactions = load_db_state()
    dims_engine = DimensionsEngine(accounts_map)
    now = datetime.now()

    replay_res = ledger_engine.rebuild(opening, transactions, assets_map)
    res = dims_engine.evaluate_dimension(
        dim_key, replay_res["holdings"], assets_map,
        lambda h, a: val_engine.eval_holding_krw(h, a, now),
        ccy_mode=ccy_mode, abs_tol=abs_tol, rel_tol=rel_tol
    )
    if not res:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return res

@app.get("/api/macro")
def get_macro():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM market_quotes ORDER BY category, symbol")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    if not rows:
        rows = fetcher.update_db_quotes()
    return rows

@app.post("/api/macro/refresh")
def refresh_macro():
    return fetcher.update_db_quotes()

class ExternalDepositReq(BaseModel):
    account_id: str
    amount: float
    note: Optional[str] = "External Deposit"

@app.post("/api/cashflow/deposit")
def add_external_deposit(req: ExternalDepositReq):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT MAX(seq) FROM transactions")
    max_seq = (cur.fetchone()[0] or 1000) + 1
    tx_id = f"TX-{max_seq}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    with conn:
        cur.execute("""
        INSERT INTO transactions (id, seq, time, source, acc, type, ticker, qty, price, fee, fx, status, raw, parser)
        VALUES (?, ?, ?, 'WEB', ?, 'DEPOSIT', 'CASH-KRW', ?, 1.0, 0, 1.0, 'ACTIVE', ?, 'Web Deposit')
        """, (tx_id, max_seq, now_str, req.account_id, req.amount, f"/deposit {req.account_id} {int(req.amount)}"))
    conn.close()

    accounts_map, assets_map, opening, transactions = load_db_state()
    BackfillEngine(ledger_engine, val_engine).run_catchup_sync(datetime.now())

    return {"status": "success", "tx_id": tx_id, "amount": req.amount}

class OpeningBalanceItem(BaseModel):
    account_id: str
    ticker: str
    quantity: float
    avg_price: float
    avg_fx: Optional[float] = 1.0

class OpeningImportRequest(BaseModel):
    items: List[OpeningBalanceItem]
    mode: str = "upsert"  # "upsert" or "replace_all"

@app.post("/api/opening/import")
def import_opening_balances(req: OpeningImportRequest):
    conn = get_db()
    cur = conn.cursor()

    imported = 0
    with conn:
        if req.mode == "replace_all":
            cur.execute("DELETE FROM opening_balances")

        for it in req.items:
            cur.execute("SELECT id FROM accounts WHERE id = ?", (it.account_id,))
            if not cur.fetchone():
                continue

            cur.execute("SELECT ticker FROM assets WHERE ticker = ?", (it.ticker,))
            if not cur.fetchone():
                ccy = "USD" if any(c.isalpha() for c in it.ticker) and not it.ticker.endswith(".T") else ("JPY" if it.ticker.endswith(".T") else "KRW")
                market = "US_STOCK" if ccy == "USD" else ("JP_STOCK" if ccy == "JPY" else "KR_STOCK")
                country = "US" if ccy == "USD" else ("JP" if ccy == "JPY" else "KR")
                cur.execute("""
                INSERT OR IGNORE INTO assets (ticker, name, market, currency, kind, price, prev_price, high_52w, exp_risk, exp_currency_real, exp_currency_listing, exp_country, exp_liquidity)
                VALUES (?, ?, ?, ?, 'STOCK', ?, ?, ?, 'risk_on', ?, ?, ?, 'liquid')
                """, (it.ticker, it.ticker, market, ccy, it.avg_price, it.avg_price, it.avg_price, ccy, ccy, country))

            cur.execute("""
            INSERT INTO opening_balances (account_id, ticker, quantity, avg_price, avg_fx)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(account_id, ticker) DO UPDATE SET
                quantity = excluded.quantity,
                avg_price = excluded.avg_price,
                avg_fx = excluded.avg_fx
            """, (it.account_id, it.ticker, it.quantity, it.avg_price, it.avg_fx or 1.0))
            imported += 1

    conn.close()

    accounts_map, assets_map, opening, transactions = load_db_state()
    BackfillEngine(ledger_engine, val_engine).run_catchup_sync(datetime.now())

    return {"status": "success", "count": imported}

@app.get("/api/transactions")
def get_transactions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions ORDER BY time DESC, seq DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.post("/api/transactions/{tx_id}/cancel")
def cancel_transaction(tx_id: str):
    conn = get_db()
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    with conn:
        cur.execute("UPDATE transactions SET status='CANCELED', canceled_at=? WHERE id=?", (now_str, tx_id))
    conn.close()

    accounts_map, assets_map, opening, transactions = load_db_state()
    replay_res = ledger_engine.rebuild(opening, transactions, assets_map)
    if replay_res["errors"]:
        conn = get_db()
        with conn:
            conn.execute("UPDATE transactions SET status='ACTIVE', canceled_at=NULL WHERE id=?", (tx_id,))
        conn.close()
        raise HTTPException(status_code=409, detail=f"Cancel failed due to dependency ({replay_res['errors']})")

    return {"status": "success", "canceled_id": tx_id}

@app.post("/api/backfill/sync")
def trigger_backfill():
    accounts_map, assets_map, opening, transactions = load_db_state()
    backfill = BackfillEngine(ledger_engine, val_engine)
    res = backfill.run_catchup_sync(datetime.now())
    return res

@app.get("/api/snapshots")
def get_snapshots(days: int = 180):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT snapshot_date, eval_krw, invested_krw FROM daily_snapshots
    WHERE scope_type='TOTAL'
    ORDER BY snapshot_date ASC
    LIMIT ?
    """, (days,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    sample_file = Path(__file__).resolve().parent.parent / "sample_dashboard_v2.html"
    return FileResponse(sample_file)
