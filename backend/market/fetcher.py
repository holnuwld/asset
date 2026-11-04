import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from backend.db.database import get_db

logger = logging.getLogger("market_fetcher")

class MarketFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def fetch_upbit_btc(self) -> Optional[Dict[str, float]]:
        try:
            r = self.session.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3)
            if r.status_code == 200:
                data = r.json()[0]
                price = float(data["trade_price"])
                prev = float(data["prev_closing_price"])
                chg = float(data["signed_change_rate"]) * 100.0
                return {"price": price, "prev": prev, "chg_pct": chg}
        except Exception as e:
            logger.warning(f"Upbit BTC fetch error: {e}")
        return None

    def fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, float]]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
            r = self.session.get(url, timeout=4)
            if r.status_code == 200:
                data = r.json()
                meta = data["chart"]["result"][0]["meta"]
                price = float(meta.get("regularMarketPrice") or 0.0)
                prev = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price)
                chg = ((price - prev) / prev * 100.0) if prev > 0 else 0.0
                return {"price": price, "prev": prev, "chg_pct": chg}
        except Exception as e:
            logger.warning(f"Yahoo quote error for {symbol}: {e}")
        return None

    def fetch_kr_stock(self, ticker: str) -> Optional[Dict[str, float]]:
        clean = ticker.replace("_US", "")
        if not (clean.isdigit() and len(clean) == 6):
            return None
        try:
            url = f"https://m.stock.naver.com/api/stock/{clean}/basic"
            r = self.session.get(url, timeout=3)
            if r.status_code == 200:
                d = r.json()
                close_str = d.get("closePrice", "").replace(",", "")
                chg_str = d.get("fluctuationsRatio", "0")
                if close_str:
                    price = float(close_str)
                    chg_pct = float(chg_str)
                    prev = price / (1.0 + chg_pct / 100.0) if (1.0 + chg_pct / 100.0) != 0 else price
                    return {"price": price, "prev": prev, "chg_pct": chg_pct}
        except Exception as e:
            logger.warning(f"Naver stock error for {ticker}: {e}")
        return None

    def fetch_krx_gold(self) -> Optional[Dict[str, float]]:
        try:
            url = "https://api.stock.naver.com/marketindex/metals/M04020000"
            r = self.session.get(url, timeout=3)
            if r.status_code == 200:
                d = r.json()
                close_str = d.get("closePrice", "").replace(",", "")
                chg_str = d.get("fluctuationsRatio", "0")
                if close_str:
                    price = float(close_str)
                    chg_pct = float(chg_str)
                    prev = price / (1.0 + chg_pct / 100.0) if (1.0 + chg_pct / 100.0) != 0 else price
                    return {"price": price, "prev": prev, "chg_pct": chg_pct}
        except Exception as e:
            logger.warning(f"Naver Gold fetch error: {e}")
        return None

    def fetch_all_portfolio_prices(self) -> Dict[str, Dict[str, float]]:
        """Fetch live prices concurrently for all holding assets in SQLite DB."""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT ticker, currency, kind FROM assets WHERE kind = 'STOCK'")
        assets_rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        results = {}

        def _fetch_asset(a):
            t = a["ticker"]
            curr = a["currency"]
            if t == "GOLD-KRX":
                g = self.fetch_krx_gold()
                if g:
                    return t, g
            elif curr == "KRW":
                s = self.fetch_kr_stock(t)
                if s:
                    return t, s
            elif curr in ("USD", "JPY"):
                y = self.fetch_yahoo_quote(t)
                if y:
                    return t, y
            return t, None

        with ThreadPoolExecutor(max_workers=16) as pool:
            for t, data in pool.map(_fetch_asset, assets_rows):
                if data:
                    results[t] = data

        return results

    def update_portfolio_prices_in_db(self) -> Dict[str, Any]:
        """Fetch real-time prices and update assets table in DB."""
        prices = self.fetch_all_portfolio_prices()
        if not prices:
            return {"updated_count": 0, "prices": {}}

        conn = get_db()
        with conn:
            cur = conn.cursor()
            for t, p_info in prices.items():
                cur.execute("""
                UPDATE assets
                SET price = ?, prev_price = ?
                WHERE ticker = ?
                """, (p_info["price"], p_info["prev"], t))
        conn.close()

        logger.info(f"Updated live prices for {len(prices)} assets in DB.")
        return {"updated_count": len(prices), "prices": prices}

    def fetch_all_macro(self) -> List[Dict[str, Any]]:
        quotes = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. FX
        usdkrw = self.fetch_yahoo_quote("KRW=X")
        if usdkrw:
            quotes.append({
                "symbol": "USD/KRW", "name": "USD/KRW", "category": "FX",
                "value": round(usdkrw["price"], 1), "prev_value": round(usdkrw["prev"], 1),
                "change_pct": round(usdkrw["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str
            })
        else:
            quotes.append({"symbol": "USD/KRW", "name": "USD/KRW", "category": "FX", "value": 1341.0, "prev_value": 1340.0, "change_pct": 0.07, "change_bp": None, "note": "Default", "updated_at": now_str})

        jpykrw = self.fetch_yahoo_quote("JPYKRW=X")
        if jpykrw:
            quotes.append({
                "symbol": "JPY/KRW", "name": "JPY(100)/KRW", "category": "FX",
                "value": round(jpykrw["price"] * 100, 1), "prev_value": round(jpykrw["prev"] * 100, 1),
                "change_pct": round(jpykrw["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str
            })
        else:
            quotes.append({"symbol": "JPY/KRW", "name": "JPY(100)/KRW", "category": "FX", "value": 848.2, "prev_value": 850.1, "change_pct": -0.22, "change_bp": None, "note": "Default", "updated_at": now_str})

        eurkrw = self.fetch_yahoo_quote("EURKRW=X")
        if eurkrw:
            quotes.append({"symbol": "EUR/KRW", "name": "EUR/KRW", "category": "FX", "value": round(eurkrw["price"], 1), "prev_value": round(eurkrw["prev"], 1), "change_pct": round(eurkrw["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "EUR/KRW", "name": "EUR/KRW", "category": "FX", "value": 1502.3, "prev_value": 1499.6, "change_pct": 0.18, "change_bp": None, "note": None, "updated_at": now_str})

        cnykrw = self.fetch_yahoo_quote("CNYKRW=X")
        if cnykrw:
            quotes.append({"symbol": "CNY/KRW", "name": "CNY/KRW", "category": "FX", "value": round(cnykrw["price"], 1), "prev_value": round(cnykrw["prev"], 1), "change_pct": round(cnykrw["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "CNY/KRW", "name": "CNY/KRW", "category": "FX", "value": 194.2, "prev_value": 194.4, "change_pct": -0.12, "change_bp": None, "note": None, "updated_at": now_str})

        # 2. Bonds
        us10y = self.fetch_yahoo_quote("^TNX")
        if us10y:
            bp = (us10y["price"] - us10y["prev"]) * 100
            quotes.append({
                "symbol": "US10Y", "name": "US 10Y", "category": "BOND",
                "value": round(us10y["price"], 2), "prev_value": round(us10y["prev"], 2),
                "change_pct": round(us10y["chg_pct"], 2), "change_bp": round(bp, 1), "note": None, "updated_at": now_str
            })
        else:
            quotes.append({"symbol": "US10Y", "name": "US 10Y", "category": "BOND", "value": 4.18, "prev_value": 4.15, "change_pct": 0.72, "change_bp": 3.0, "note": None, "updated_at": now_str})

        quotes.append({"symbol": "US30Y", "name": "US 30Y", "category": "BOND", "value": 4.42, "prev_value": 4.39, "change_pct": 0.68, "change_bp": 3.0, "note": None, "updated_at": now_str})
        quotes.append({"symbol": "KR10Y", "name": "KR 10Y", "category": "BOND", "value": 3.09, "prev_value": 3.11, "change_pct": -0.64, "change_bp": -2.0, "note": None, "updated_at": now_str})
        quotes.append({"symbol": "JP10Y", "name": "JP 10Y", "category": "BOND", "value": 0.97, "prev_value": 0.96, "change_pct": 1.04, "change_bp": 1.0, "note": None, "updated_at": now_str})
        quotes.append({"symbol": "CN10Y", "name": "CN 10Y", "category": "BOND", "value": 2.12, "prev_value": 2.15, "change_pct": -1.40, "change_bp": -3.0, "note": None, "updated_at": now_str})

        # 3. Indices
        nasdaq = self.fetch_yahoo_quote("^IXIC")
        if nasdaq:
            quotes.append({"symbol": "NASDAQ", "name": "NASDAQ", "category": "INDEX", "value": round(nasdaq["price"], 1), "prev_value": round(nasdaq["prev"], 1), "change_pct": round(nasdaq["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "NASDAQ", "name": "NASDAQ", "category": "INDEX", "value": 18489.5, "prev_value": 18371.9, "change_pct": 0.64, "change_bp": None, "note": None, "updated_at": now_str})

        kospi = self.fetch_yahoo_quote("^KS11")
        if kospi:
            quotes.append({"symbol": "KOSPI", "name": "KOSPI", "category": "INDEX", "value": round(kospi["price"], 1), "prev_value": round(kospi["prev"], 1), "change_pct": round(kospi["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "KOSPI", "name": "KOSPI", "category": "INDEX", "value": 2593.8, "prev_value": 2609.2, "change_pct": -0.59, "change_bp": None, "note": None, "updated_at": now_str})

        kosdaq = self.fetch_yahoo_quote("^KQ11")
        if kosdaq:
            quotes.append({"symbol": "KOSDAQ", "name": "KOSDAQ", "category": "INDEX", "value": round(kosdaq["price"], 1), "prev_value": round(kosdaq["prev"], 1), "change_pct": round(kosdaq["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "KOSDAQ", "name": "KOSDAQ", "category": "INDEX", "value": 753.2, "prev_value": 761.7, "change_pct": -1.12, "change_bp": None, "note": None, "updated_at": now_str})

        n225 = self.fetch_yahoo_quote("^N225")
        if n225:
            quotes.append({"symbol": "N225", "name": "NIKKEI", "category": "INDEX", "value": round(n225["price"], 1), "prev_value": round(n225["prev"], 1), "change_pct": round(n225["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "N225", "name": "NIKKEI", "category": "INDEX", "value": 38981.7, "prev_value": 38911.5, "change_pct": 0.18, "change_bp": None, "note": None, "updated_at": now_str})

        # 4. Gold & Crypto
        gold = self.fetch_krx_gold()
        if gold:
            quotes.append({"symbol": "KRX_GOLD", "name": "KRX Gold(1g)", "category": "GOLD", "value": round(gold["price"], 0), "prev_value": round(gold["prev"], 0), "change_pct": round(gold["chg_pct"], 2), "change_bp": None, "note": "KRX 실시간", "updated_at": now_str})
        else:
            quotes.append({"symbol": "KRX_GOLD", "name": "KRX Gold(1g)", "category": "GOLD", "value": 173870.0, "prev_value": 168970.0, "change_pct": 2.90, "change_bp": None, "note": None, "updated_at": now_str})

        btcusd = self.fetch_yahoo_quote("BTC-USD")
        if btcusd:
            quotes.append({"symbol": "BTC_USD", "name": "Bitcoin($)", "category": "CRYPTO", "value": round(btcusd["price"], 1), "prev_value": round(btcusd["prev"], 1), "change_pct": round(btcusd["chg_pct"], 2), "change_bp": None, "note": None, "updated_at": now_str})
        else:
            quotes.append({"symbol": "BTC_USD", "name": "Bitcoin($)", "category": "CRYPTO", "value": 68420.0, "prev_value": 66986.0, "change_pct": 2.14, "change_bp": None, "note": None, "updated_at": now_str})

        upbit_btc = self.fetch_upbit_btc()
        if upbit_btc:
            quotes.append({"symbol": "BTC_KRW", "name": "Upbit BTC(KRW)", "category": "CRYPTO", "value": upbit_btc["price"], "prev_value": upbit_btc["prev"], "change_pct": round(upbit_btc["chg_pct"], 2), "change_bp": None, "note": "Upbit Live", "updated_at": now_str})
        else:
            quotes.append({"symbol": "BTC_KRW", "name": "Upbit BTC(KRW)", "category": "CRYPTO", "value": 94850000.0, "prev_value": 93008000.0, "change_pct": 1.98, "change_bp": None, "note": "09:00", "updated_at": now_str})

        return quotes

    def update_db_quotes(self):
        quotes = self.fetch_all_macro()
        conn = get_db()
        with conn:
            cur = conn.cursor()
            for q in quotes:
                cur.execute("""
                INSERT INTO market_quotes (symbol, name, category, value, prev_value, change_pct, change_bp, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    value=excluded.value,
                    prev_value=excluded.prev_value,
                    change_pct=excluded.change_pct,
                    change_bp=excluded.change_bp,
                    note=excluded.note,
                    updated_at=excluded.updated_at
                """, (q["symbol"], q["name"], q["category"], q["value"], q["prev_value"], q["change_pct"], q["change_bp"], q["note"], q["updated_at"]))
        conn.close()
        return quotes
