import json
from collections import defaultdict

with open('data/financial_assets_261103.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)

accounts = defaultdict(lambda: {'count': 0, 'eval_krw': 0, 'invest_krw': 0, 'items': []})
categories = defaultdict(float)
total_eval = 0
total_invest = 0

for r in rows:
    acc_key = f"{r['금융기관']}_{r['계좌명']}"
    eval_krw = float(r.get('원화 평가금액') or 0)
    invest_krw = float(r.get('원화 매입금액') or 0)
    total_eval += eval_krw
    total_invest += invest_krw
    accounts[acc_key]['count'] += 1
    accounts[acc_key]['eval_krw'] += eval_krw
    accounts[acc_key]['invest_krw'] += invest_krw
    accounts[acc_key]['broker'] = r['금융기관']
    accounts[acc_key]['name'] = r['계좌명']
    accounts[acc_key]['num'] = r['계좌번호']
    accounts[acc_key]['items'].append(r)
    categories[r.get('대분류', '기타')] += eval_krw

print(f"Total Eval KRW: {total_eval:,.0f}")
print(f"Total Invest KRW: {total_invest:,.0f}")
print(f"Profit KRW: {total_eval - total_invest:,.0f} ({(total_eval/total_invest - 1)*100:.2f}%)")
print("\nAccounts summary:")
for k, v in accounts.items():
    print(f"- {k} ({v['num']}): {v['count']} items, Eval: {v['eval_krw']:,.0f} KRW ({(v['eval_krw']/total_eval)*100:.1f}%)")

print("\nCategories summary:")
for k, v in categories.items():
    print(f"- {k}: {v:,.0f} KRW ({(v/total_eval)*100:.1f}%)")
