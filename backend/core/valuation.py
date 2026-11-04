from typing import Dict, List, Any
from datetime import datetime

class ValuationEngine:
    def __init__(self, fx_dict: Dict[str, float]):
        self.fx = fx_dict

    def calc_accrued_interest(self, holding: Dict[str, Any], asset: Dict[str, Any], as_of_date: datetime) -> float:
        rate = asset.get("deposit_rate")
        start_str = asset.get("deposit_start")
        maturity_str = asset.get("deposit_maturity")
        if not (rate and start_str and maturity_str):
            return 0.0

        try:
            start = datetime.strptime(start_str, "%Y-%m-%d")
            maturity = datetime.strptime(maturity_str, "%Y-%m-%d")
            end_date = min(as_of_date, maturity)
            days = max(0, (end_date - start).days)
            return float(holding["quantity"]) * float(rate) * (days / 365.0)
        except Exception:
            return 0.0

    def eval_holding_krw(self, holding: Dict[str, Any], asset: Dict[str, Any], as_of_date: datetime) -> float:
        qty = float(holding["quantity"])
        fx_rate = self.fx.get(asset["currency"], 1.0)
        kind = asset["kind"]

        if kind == "DEPOSIT":
            return qty + self.calc_accrued_interest(holding, asset, as_of_date)
        elif kind == "CASH":
            return qty * fx_rate
        else:
            return qty * float(asset["price"]) * fx_rate

    def eval_portfolio(self, holdings: Dict[str, Any], assets_map: Dict[str, Any],
                       invested_principal: float, opening_principal: float,
                       processed_txs: List[Dict[str, Any]], as_of_date: datetime):
        total_eval_krw = 0.0
        total_cost_krw = 0.0
        price_pnl_krw = 0.0
        fx_pnl_krw = 0.0
        accrued_interest_krw = 0.0

        ticker_grouped = {}

        for key, h in holdings.items():
            qty = float(h["quantity"])
            if abs(qty) < 1e-9:
                continue

            ticker = h["ticker"]
            a = assets_map[ticker]
            curr_fx = self.fx.get(a["currency"], 1.0)
            val_krw = self.eval_holding_krw(h, a, as_of_date)
            cost_krw = qty * float(h["avg_price"]) * float(h["avg_fx"])

            total_eval_krw += val_krw
            total_cost_krw += cost_krw

            if a["kind"] == "DEPOSIT":
                accrued_interest_krw += (val_krw - cost_krw)
            elif a["kind"] == "CASH":
                if a["currency"] != "KRW":
                    fx_pnl_krw += qty * (curr_fx - float(h["avg_fx"]))
            else:
                if a["currency"] != "KRW":
                    price_pnl_krw += qty * (float(a["price"]) - float(h["avg_price"])) * float(h["avg_fx"])
                    fx_pnl_krw += qty * float(a["price"]) * (curr_fx - float(h["avg_fx"]))
                else:
                    price_pnl_krw += qty * (float(a["price"]) - float(h["avg_price"]))

            if ticker not in ticker_grouped:
                ticker_grouped[ticker] = {
                    "ticker": ticker,
                    "asset": a,
                    "rows": [],
                    "total_qty": 0.0,
                    "total_cost_krw": 0.0,
                    "total_val_krw": 0.0,
                    "total_cost_ccy": 0.0
                }
            tg = ticker_grouped[ticker]
            tg["rows"].append({
                "account_id": h["account_id"],
                "quantity": qty,
                "avg_price": float(h["avg_price"]),
                "avg_fx": float(h["avg_fx"]),
                "val_krw": val_krw
            })
            tg["total_qty"] += qty
            tg["total_val_krw"] += val_krw
            tg["total_cost_krw"] += cost_krw
            tg["total_cost_ccy"] += qty * float(h["avg_price"])

        ticker_list = []
        for tg in ticker_grouped.values():
            t_qty = tg["total_qty"]
            tg["avg_price"] = (tg["total_cost_ccy"] / t_qty) if t_qty > 0 else 0.0
            tg["avg_fx"] = (tg["total_cost_krw"] / tg["total_cost_ccy"]) if tg["total_cost_ccy"] > 0 else 1.0
            ticker_list.append(tg)

        ticker_list.sort(key=lambda x: (0 if x["asset"]["kind"] == "STOCK" else 1, -x["total_val_krw"]))

        start_of_year = datetime(as_of_date.year, 1, 1)
        total_days = max(1, (as_of_date - start_of_year).days)
        weighted_cf = 0.0

        for tx in processed_txs:
            if tx.get("status") == "ACTIVE" and tx.get("type") == "DEPOSIT":
                try:
                    tx_time = datetime.strptime(tx["time"][:10], "%Y-%m-%d")
                    passed_days = (as_of_date - tx_time).days
                    weight = max(0.05, min(1.0, passed_days / total_days))
                    weighted_cf += float(tx["qty"]) * float(tx.get("fx", 1.0)) * weight
                except Exception:
                    weighted_cf += float(tx["qty"]) * 0.5

        avg_invested_capital = opening_principal + weighted_cf
        total_gain_krw = total_eval_krw - invested_principal
        simple_roi_pct = (total_gain_krw / invested_principal * 100.0) if invested_principal > 0 else 0.0
        mwrr_pct = (total_gain_krw / avg_invested_capital * 100.0) if avg_invested_capital > 0 else 0.0

        return {
            "total_eval_krw": total_eval_krw,
            "total_cost_krw": total_cost_krw,
            "invested_principal": invested_principal,
            "total_gain_krw": total_gain_krw,
            "simple_roi_pct": simple_roi_pct,
            "mwrr_pct": mwrr_pct,
            "price_pnl_krw": price_pnl_krw,
            "fx_pnl_krw": fx_pnl_krw,
            "accrued_interest_krw": accrued_interest_krw,
            "ticker_list": ticker_list
        }
