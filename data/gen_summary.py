import json

with open('data/financial_assets_261103.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)

with open('data/summary.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total Rows: {len(rows)}\n\n")
    # Group by broker and account
    from collections import defaultdict
    by_acc = defaultdict(list)
    for r in rows:
        acc_key = f"{r['금융기관']} | {r['계좌명']} | {r['계좌번호']}"
        by_acc[acc_key].append(r)
    
    for acc_key, items in by_acc.items():
        eval_sum = sum(float(x.get('원화 평가금액') or 0) for x in items)
        invest_sum = sum(float(x.get('원화 매입금액') or 0) for x in items)
        out.write(f"=== {acc_key} ===\n")
        out.write(f"Total Eval: {eval_sum:,.0f} KRW, Invest: {invest_sum:,.0f} KRW, Count: {len(items)}\n")
        for it in items:
            out.write(f"  [{it['대분류']}] {it['종목명']} ({it['티커']}) - {it['보유수량']}주 | 매수가: {float(it['매수단가(원통화)']):,.2f} | 현재가: {float(it['현재가(원통화)']):,.2f} | 평가: {float(it['원화 평가금액']):,.0f}원 ({it['수익률(%)']}%)\n")
        out.write("\n")
