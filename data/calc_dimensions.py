import json

with open('data/assets_master.json', 'r', encoding='utf-8') as f:
    assets = json.load(f)

with open('data/opening_master.json', 'r', encoding='utf-8') as f:
    opening = json.load(f)

FX = {'KRW': 1.0, 'USD': 1341.0, 'JPY': 8.482}

# Compute dimensions
total_eval = 0
risk_buckets = {'risk_on': 0, 'risk_off': 0}
ccy_real_buckets = {'KRW': 0, 'USD': 0, 'JPY': 0, 'CNY': 0}
country_buckets = {'KR': 0, 'US': 0, 'JP': 0, 'CN': 0, 'OTHER': 0}
liq_buckets = {'liquid': 0, 'fixed': 0}
acc_buckets = {}

for op in opening:
    a = assets[op['t']]
    val = op['qty'] * a['price'] * FX[a['currency']]
    total_eval += val
    
    # Risk
    risk_buckets[a['exp']['risk']] += val
    
    # Currency (real)
    real_c = a['exp']['currency']['real']
    ccy_real_buckets[real_c] = ccy_real_buckets.get(real_c, 0) + val
    
    # Country (stock only)
    c = a['exp']['country']
    if c:
        country_buckets[c] = country_buckets.get(c, 0) + val
    
    # Liquidity
    liq_buckets[a['exp']['liquidity']] += val
    
    # Account
    acc_buckets[op['acc']] = acc_buckets.get(op['acc'], 0) + val

print(f"Total Eval: {total_eval:,.0f} KRW\n")

print("1. Risk-On vs Risk-Off:")
for k, v in risk_buckets.items():
    print(f"  {k:10s}: {v:12,.0f} KRW ({v/total_eval*100:.1f}%)")

print("\n2. Currency (Real exposure):")
for k, v in ccy_real_buckets.items():
    print(f"  {k:10s}: {v:12,.0f} KRW ({v/total_eval*100:.1f}%)")

print("\n3. Country (Stock/ETF equity):")
country_total = sum(country_buckets.values())
for k, v in country_buckets.items():
    print(f"  {k:10s}: {v:12,.0f} KRW ({v/country_total*100:.1f}% of equity)")

print("\n4. Liquidity:")
for k, v in liq_buckets.items():
    print(f"  {k:10s}: {v:12,.0f} KRW ({v/total_eval*100:.1f}%)")

print("\n5. Accounts:")
for k, v in sorted(acc_buckets.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k:10s}: {v:12,.0f} KRW ({v/total_eval*100:.1f}%)")
