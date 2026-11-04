import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "asset.db"

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            broker TEXT NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            allowed_markets TEXT NOT NULL, -- JSON list
            target_pct REAL NOT NULL DEFAULT 0,
            base_currency TEXT NOT NULL DEFAULT 'KRW'
        );

        CREATE TABLE IF NOT EXISTS assets (
            ticker TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            market TEXT NOT NULL, -- KR_STOCK, KR_ETF, US_STOCK, US_ETF, JP_STOCK, KRX_GOLD, DEPOSIT, CASH
            currency TEXT NOT NULL, -- KRW, USD, JPY
            kind TEXT NOT NULL, -- STOCK, DEPOSIT, CASH
            price REAL NOT NULL,
            prev_price REAL NOT NULL,
            high_52w REAL NOT NULL,
            exp_risk TEXT NOT NULL,
            exp_currency_real TEXT NOT NULL,
            exp_currency_listing TEXT NOT NULL,
            exp_country TEXT,
            exp_liquidity TEXT NOT NULL,
            deposit_rate REAL,
            deposit_start TEXT,
            deposit_maturity TEXT
        );

        CREATE TABLE IF NOT EXISTS opening_balances (
            account_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            avg_fx REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (account_id, ticker),
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (ticker) REFERENCES assets(ticker)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            seq INTEGER NOT NULL,
            time TEXT NOT NULL,
            source TEXT NOT NULL,
            acc TEXT NOT NULL,
            type TEXT NOT NULL, -- BUY, SELL, MATURITY, DEPOSIT, WITHDRAW
            ticker TEXT NOT NULL,
            qty REAL NOT NULL,
            price REAL NOT NULL,
            fee REAL NOT NULL DEFAULT 0,
            fx REAL NOT NULL DEFAULT 1.0,
            to_acc TEXT,
            to_ticker TEXT,
            interest REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, CANCELED
            raw TEXT,
            parser TEXT,
            hash TEXT,
            canceled_at TEXT,
            FOREIGN KEY (acc) REFERENCES accounts(id)
        );

        CREATE TABLE IF NOT EXISTS daily_snapshots (
            snapshot_date TEXT NOT NULL,
            scope_type TEXT NOT NULL, -- TOTAL, DIMENSION
            dimension_key TEXT,
            category_key TEXT,
            eval_krw REAL NOT NULL,
            invested_krw REAL NOT NULL,
            weight_pct REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (snapshot_date, scope_type, dimension_key, category_key)
        );

        CREATE TABLE IF NOT EXISTS market_quotes (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL, -- FX, BOND, INDEX, CRYPTO, GOLD
            value REAL NOT NULL,
            prev_value REAL,
            change_pct REAL,
            change_bp REAL,
            note TEXT,
            updated_at TEXT NOT NULL
        );
        """)
    conn.close()
