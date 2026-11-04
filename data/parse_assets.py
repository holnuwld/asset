import json

with open('data/financial_assets_261103.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)

print(f"Total rows: {len(rows)}")

# Check distinct assets
assets_dict = {}
for r in rows:
    ticker = str(r['티커']).strip()
    # Normalize ticker: if KR stock/ETF is numeric and length < 6, pad with 0s
    if ticker.isdigit() and len(ticker) < 6:
        ticker = ticker.zfill(6)
    
    name = r['종목명'].strip()
    ccy = r['거래통화'].strip()
    price = float(r['현재가(원통화)'])
    category = r['대분류'].strip()
    sub_cat = r['자산구분'].strip()
    tags = r['세부태그'].strip()
    
    if ticker not in assets_dict:
        assets_dict[ticker] = {
            'ticker': ticker,
            'name': name,
            'ccy': ccy,
            'price': price,
            'category': category,
            'sub_cat': sub_cat,
            'tags': tags,
            'holdings': []
        }
    assets_dict[ticker]['holdings'].append(r)

print(f"Unique assets count: {len(assets_dict)}")
for k, v in sorted(assets_dict.items()):
    total_val = sum(float(x.get('원화 평가금액') or 0) for x in v['holdings'])
    print(f"{k:20s} | {v['name']:30s} | {v['ccy']:4s} | 현재가: {v['price']:12.2f} | 평가합: {total_val:12,.0f} | 건수: {len(v['holdings'])}")
