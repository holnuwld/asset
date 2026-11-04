from typing import Dict, List, Any, Optional

class LedgerEngine:
    def __init__(self, fx_dict: Optional[Dict[str, float]] = None):
        self.fx = fx_dict or {"KRW": 1.0, "USD": 1385.0, "JPY": 9.215}

    def get_cash_ticker(self, currency: str) -> str:
        if currency == "USD":
            return "CASH-USD"
        if currency == "JPY":
            return "CASH-JPY"
        return "CASH-KRW"

    def rebuild(self, opening_rows: List[Dict[str, Any]], tx_rows: List[Dict[str, Any]], assets_map: Dict[str, Any]):
        holdings = {}
        opening_principal = 0.0
        external_cashflow = 0.0

        def get_holding(acc_id: str, ticker: str):
            key = f"{acc_id}|{ticker}"
            if key not in holdings:
                a = assets_map.get(ticker)
                curr = a["currency"] if a else "KRW"
                holdings[key] = {
                    "account_id": acc_id,
                    "ticker": ticker,
                    "quantity": 0.0,
                    "avg_price": 1.0 if (a and a["kind"] in ("CASH", "DEPOSIT")) else 0.0,
                    "avg_fx": self.fx.get(curr, 1.0)
                }
            return holdings[key]

        # 1. Opening Balances
        for o in opening_rows:
            h = get_holding(o["account_id"], o["ticker"])
            h["quantity"] = float(o["quantity"])
            h["avg_price"] = float(o["avg_price"])
            h["avg_fx"] = float(o.get("avg_fx") or 1.0)
            opening_principal += h["quantity"] * h["avg_price"] * h["avg_fx"]

        # 2. Sort and replay active transactions
        active_txs = [t for t in tx_rows if t.get("status") == "ACTIVE"]
        active_txs.sort(key=lambda x: (x["time"], x["seq"]))

        processed_txs = []
        errors = []

        for tx in active_txs:
            tx_copy = dict(tx)
            res = self.apply_tx(tx_copy, get_holding, assets_map)
            if res.get("error"):
                errors.append({"tx_id": tx["id"], "error": res["error"]})
                continue
            
            tx_copy["realized_pnl"] = res.get("realized_pnl")
            tx_copy["realized_price"] = res.get("realized_price")
            tx_copy["realized_fx"] = res.get("realized_fx")
            tx_copy["warn"] = res.get("warn")

            if tx["type"] == "DEPOSIT":
                external_cashflow += float(tx["qty"]) * float(tx.get("fx", 1.0))
            elif tx["type"] == "WITHDRAW":
                external_cashflow -= float(tx["qty"]) * float(tx.get("fx", 1.0))

            processed_txs.append(tx_copy)

        return {
            "holdings": holdings,
            "opening_principal": opening_principal,
            "external_cashflow": external_cashflow,
            "invested_principal": opening_principal + external_cashflow,
            "processed_txs": processed_txs,
            "errors": errors
        }

    def apply_tx(self, tx: Dict[str, Any], get_holding_fn, assets_map: Dict[str, Any]):
        a = assets_map.get(tx["ticker"])
        if not a:
            return {"error": f"Asset not found: {tx['ticker']}"}

        tx_type = tx["type"]
        is_fx = a["currency"] != "KRW"
        h = get_holding_fn(tx["acc"], tx["ticker"])
        cash_h = get_holding_fn(tx["acc"], self.get_cash_ticker(a["currency"]))

        qty = float(tx["qty"])
        price = float(tx["price"])
        fee = float(tx.get("fee", 0.0))
        tx_fx = float(tx.get("fx", self.fx.get(a["currency"], 1.0)))
        gross = qty * price

        if tx_type == "BUY":
            cost_ccy = gross + fee
            if is_fx:
                from_cash = max(0.0, min(cash_h["quantity"], cost_ccy))
                from_spot = cost_ccy - from_cash
                cost_krw = from_cash * cash_h["avg_fx"] + from_spot * tx_fx
            else:
                cost_krw = cost_ccy

            old_ccy = h["quantity"] * h["avg_price"]
            old_krw = old_ccy * h["avg_fx"]
            new_ccy = old_ccy + cost_ccy
            new_krw = old_krw + cost_krw

            h["quantity"] += qty
            h["avg_price"] = new_ccy / h["quantity"] if h["quantity"] > 0 else 0.0
            h["avg_fx"] = (new_krw / new_ccy) if is_fx and new_ccy > 0 else 1.0
            cash_h["quantity"] -= cost_ccy

            warn = "Cash shortfall warning" if cash_h["quantity"] < -0.005 else None
            return {"warn": warn}

        elif tx_type == "SELL":
            if h["quantity"] + 1e-9 < qty:
                return {"error": f"Insufficient quantity: holding {h['quantity']} < sell {qty}"}

            proceeds = gross - fee
            price_pnl = (price - h["avg_price"]) * qty * h["avg_fx"] - fee * h["avg_fx"]
            fx_pnl = proceeds * (tx_fx - h["avg_fx"]) if is_fx else 0.0
            total_realized = price_pnl + fx_pnl

            h["quantity"] -= qty
            if h["quantity"] < 1e-9:
                h["quantity"] = 0.0

            if is_fx:
                base = max(cash_h["quantity"], 0.0)
                cash_h["avg_fx"] = (base * cash_h["avg_fx"] + proceeds * tx_fx) / (base + proceeds) if (base + proceeds) > 0 else tx_fx

            cash_h["quantity"] += proceeds
            return {
                "realized_pnl": total_realized,
                "realized_price": price_pnl,
                "realized_fx": fx_pnl
            }

        elif tx_type == "MATURITY":
            if h["quantity"] + 1e-6 < qty:
                return {"error": "Insufficient deposit balance"}
            h["quantity"] -= qty
            dest_acc = tx.get("to_acc") or tx["acc"]
            dest_h = get_holding_fn(dest_acc, "CASH-KRW")
            interest = float(tx.get("interest", 0.0))
            dest_h["quantity"] += qty + interest
            return {
                "realized_pnl": interest,
                "realized_price": interest,
                "realized_fx": 0.0
            }

        elif tx_type == "DEPOSIT":
            h["quantity"] += qty
            return {}

        elif tx_type == "WITHDRAW":
            if h["quantity"] < qty:
                return {"error": "Insufficient balance for withdrawal"}
            h["quantity"] -= qty
            return {}

        return {"error": f"Unknown tx type: {tx_type}"}
