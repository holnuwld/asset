from typing import Dict, List, Any

class DimensionsEngine:
    def __init__(self, accounts_map: Dict[str, Any]):
        self.accounts_map = accounts_map
        self.dims_config = {
            "risk": {
                "title": "Risk-On vs Risk-Off",
                "short": "Risk",
                "cats": [
                    {"key": "risk_on", "label": "Risk-On (Stocks/ETFs)", "target": 65.0, "hint": "Stocks & ETFs"},
                    {"key": "risk_off", "label": "Risk-Off (Deposits/Cash/Gold)", "target": 35.0, "hint": "Deposits, Gold & Cash"}
                ]
            },
            "currency": {
                "title": "Currency Allocation (KRW / USD / JPY)",
                "short": "Currency",
                "cats": [
                    {"key": "KRW", "label": "KRW", "target": 55.0, "hint": "KRW Assets"},
                    {"key": "USD", "label": "USD", "target": 38.0, "hint": "US Direct & Unhedged S&P500"},
                    {"key": "JPY", "label": "JPY", "target": 7.0, "hint": "Japan Stocks & JPY Cash"}
                ]
            },
            "country": {
                "title": "Stock Allocation by Country",
                "short": "Country",
                "note": "Stocks/ETFs only",
                "cats": [
                    {"key": "US", "label": "US Stocks", "target": 62.0, "hint": "US Direct + S&P500 ETFs"},
                    {"key": "KR", "label": "KR Stocks", "target": 30.0, "hint": "Samsung, SK Hynix, etc"},
                    {"key": "JP", "label": "JP Stocks", "target": 8.0, "hint": "Toyota, etc"}
                ]
            },
            "liquidity": {
                "title": "Fixed vs Liquid Assets",
                "short": "Liquidity",
                "cats": [
                    {"key": "fixed", "label": "Fixed (Deposits)", "target": 22.0, "hint": "Time Deposits"},
                    {"key": "liquid", "label": "Liquid (Stocks/Gold/Cash)", "target": 78.0, "hint": "Stocks, Gold, Cash"}
                ]
            },
            "account": {
                "title": "Account Allocation (9 Accounts)",
                "short": "Accounts",
                "cats": [
                    {"key": a["id"], "label": a["name"], "target": float(a["target_pct"]), "hint": a.get("account_type", "")}
                    for a in accounts_map.values()
                ]
            }
        }

    def calc_band(self, target: float, abs_tol: float = 5.0, rel_tol: float = 25.0) -> float:
        rel = (target * rel_tol / 100.0) if rel_tol > 0 else 999.0
        return max(0.5, min(abs_tol, rel))

    def evaluate_dimension(self, dim_key: str, holdings: Dict[str, Any], assets_map: Dict[str, Any],
                           eval_holding_krw_fn, ccy_mode: str = "real", abs_tol: float = 5.0, rel_tol: float = 25.0):
        cfg = self.dims_config.get(dim_key)
        if not cfg:
            return None

        buckets = {c["key"]: 0.0 for c in cfg["cats"]}
        total_eval = 0.0

        for key, h in holdings.items():
            qty = float(h["quantity"])
            if abs(qty) < 1e-9:
                continue

            ticker = h["ticker"]
            a = assets_map[ticker]
            val_krw = eval_holding_krw_fn(h, a)
            if val_krw <= 0:
                continue

            if dim_key == "account":
                acc_id = h["account_id"]
                buckets[acc_id] = buckets.get(acc_id, 0.0) + val_krw
                total_eval += val_krw
            elif dim_key == "currency":
                curr_target = a["exp_currency_real"] if ccy_mode == "real" else a["exp_currency_listing"]
                if curr_target in buckets:
                    buckets[curr_target] += val_krw
                    total_eval += val_krw
            elif dim_key == "risk":
                r_target = a["exp_risk"]
                if r_target in buckets:
                    buckets[r_target] += val_krw
                    total_eval += val_krw
            elif dim_key == "country":
                c_target = a.get("exp_country")
                if c_target and c_target in buckets:
                    buckets[c_target] += val_krw
                    total_eval += val_krw
            elif dim_key == "liquidity":
                l_target = a["exp_liquidity"]
                if l_target in buckets:
                    buckets[l_target] += val_krw
                    total_eval += val_krw

        rows = []
        for cat in cfg["cats"]:
            cur_val = buckets.get(cat["key"], 0.0)
            pct = (cur_val / total_eval * 100.0) if total_eval > 0 else 0.0
            tgt = cat["target"]
            diff = pct - tgt
            band = self.calc_band(tgt, abs_tol, rel_tol)
            is_out = abs(diff) >= band
            need_krw = ((tgt - pct) / 100.0 * total_eval) if total_eval > 0 else 0.0

            rows.append({
                "key": cat["key"],
                "label": cat["label"],
                "target": tgt,
                "cur_val": cur_val,
                "pct": pct,
                "diff": diff,
                "band": band,
                "is_out": is_out,
                "need_krw": need_krw,
                "hint": cat.get("hint", "")
            })

        return {
            "dim_key": dim_key,
            "title": cfg["title"],
            "short": cfg["short"],
            "note": cfg.get("note"),
            "total_eval": total_eval,
            "rows": rows
        }

    def evaluate_all_drifts(self, holdings: Dict[str, Any], assets_map: Dict[str, Any],
                            eval_holding_krw_fn, ccy_mode: str = "real", abs_tol: float = 5.0, rel_tol: float = 25.0):
        drifts = []
        for dim_key in ["risk", "currency", "country", "liquidity", "account"]:
            res = self.evaluate_dimension(dim_key, holdings, assets_map, eval_holding_krw_fn, ccy_mode, abs_tol, rel_tol)
            if res:
                for r in res["rows"]:
                    if r["is_out"]:
                        drifts.append({
                            "dim_key": dim_key,
                            "dim_short": res["short"],
                            "key": r["key"],
                            "label": r["label"],
                            "pct": r["pct"],
                            "target": r["target"],
                            "diff": r["diff"],
                            "band": r["band"],
                            "need_krw": r["need_krw"]
                        })
        drifts.sort(key=lambda x: -abs(x["diff"]))
        return drifts
