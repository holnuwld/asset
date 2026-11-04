import json

with open('data/financial_assets_261103.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)

# Account mapping
def get_acc_id(r):
    broker = r['금융기관'].strip()
    name = r['계좌명'].strip()
    if 'KB' in broker or '신연금' in name:
        return 'KB_PEN'
    if '삼성' in broker:
        if 'IRP' in name or '퇴직연금' in name:
            return 'SAM_IRP'
        return 'SAM_GEN'
    if '나무' in broker:
        if '금현물' in name:
            return 'NAMU_GOLD'
        return 'NAMU_GEN'
    if '키움' in broker:
        if 'ISA' in name:
            return 'KIW_ISA'
        return 'KIW_OVS'
    if '새마을' in broker:
        return 'MG_DEP'
    if '토스' in broker:
        return 'TOSS_FX'
    return 'UNKNOWN'

# Market / asset type determination
def get_asset_info(r):
    t = str(r['티커']).strip()
    if t == '457490' and '미국' in r['종목명']:
        t = '457490_US'
    if t.isdigit() and len(t) < 6:
        t = t.zfill(6)
    name = r['종목명'].strip()
    ccy = r['거래통화'].strip()
    price = float(r['현재가(원통화)'])
    prev_price = float(r['매수단가(원통화)'])
    category = r['대분류'].strip()
    sub_cat = r['자산구분'].strip()
    tags = r['세부태그'].strip()
    
    # Kind & Market
    kind = 'STOCK'
    market = 'KR_STOCK'
    risk = 'risk_on'
    country = 'KR'
    liquidity = 'liquid'
    real_ccy = ccy
    list_ccy = ccy
    
    if '예수금' in name or '현금성' in name or t.startswith('CASH-') or t.startswith('RP-'):
        kind = 'CASH'
        market = 'CASH'
        risk = 'risk_off'
        country = None
        if 'RP' in t:
            kind = 'RP'
        if ccy == 'USD':
            real_ccy = 'USD'
            list_ccy = 'USD'
        elif ccy == 'JPY':
            real_ccy = 'JPY'
            list_ccy = 'JPY'
        else:
            real_ccy = 'KRW'
            list_ccy = 'KRW'
    elif '예탁금' in name or '예금' in name or t.startswith('DEP-'):
        kind = 'DEPOSIT'
        market = 'DEPOSIT'
        risk = 'risk_off'
        country = None
        liquidity = 'fixed'
    elif '금 99' in name or 'GOLD-KRX' in t:
        kind = 'STOCK'
        market = 'KRX_GOLD'
        risk = 'risk_off'
        country = None
    elif sub_cat == '국내ETF':
        market = 'KR_ETF'
        if '미국' in name or '다우' in name or 'S&P' in name or '나스닥' in name or '테크' in name or 'AI' in name:
            country = 'US'
            real_ccy = 'USD'
            list_ccy = 'KRW'
        elif '차이나' in name:
            country = 'CN'
            real_ccy = 'CNY'
            list_ccy = 'KRW'
        elif '채권' in name or '국채' in name or '머니마켓' in name or 'KOFR' in name or '금리' in name:
            risk = 'risk_off'
            country = 'KR'
            if '미국' in name:
                country = 'US'
                real_ccy = 'USD'
        elif '구리' in name:
            risk = 'risk_off'
            country = None
    elif sub_cat == '해외주식' or ccy in ('USD', 'JPY'):
        if ccy == 'USD':
            market = 'US_ETF' if ('ETF' in name or 'Shares' in name) else 'US_STOCK'
            country = 'US'
            real_ccy = 'USD'
            list_ccy = 'USD'
            if 'KORU' in t:
                country = 'KR'
            elif 'BOXX' in t:
                risk = 'risk_off'
            elif 'UEC' in t:
                country = 'US'
        elif ccy == 'JPY':
            market = 'JP_ETF' if ('ETF' in name or 'GLOBAL X' in name) else 'JP_STOCK'
            country = 'JP'
            real_ccy = 'JPY'
            list_ccy = 'JPY'
    else: # 국내주식
        market = 'KR_STOCK'
        country = 'KR'
        real_ccy = 'KRW'
        list_ccy = 'KRW'

    return {
        'ticker': t,
        'name': name,
        'market': market,
        'currency': ccy,
        'kind': kind,
        'price': price,
        'prev': prev_price,
        'high52': round(price * 1.15, 2 if ccy == 'USD' else 0),
        'exp': {
            'risk': risk,
            'currency': {'real': real_ccy, 'listing': list_ccy},
            'country': country,
            'liquidity': liquidity
        }
    }

assets = {}
opening = []

for r in rows:
    acc_id = get_acc_id(r)
    a_info = get_asset_info(r)
    t = a_info['ticker']
    if t not in assets:
        assets[t] = a_info
    
    qty = float(r['보유수량'])
    avg = float(r['매수단가(원통화)'])
    
    # Calculate effective fx from file
    eval_krw = float(r.get('원화 평가금액') or 0)
    invest_krw = float(r.get('원화 매입금액') or 0)
    ccy = r['거래통화'].strip()
    
    fx = 1.0
    if ccy == 'USD':
        fx = round(invest_krw / (qty * avg), 2) if (qty * avg) > 0 else 1341.0
    elif ccy == 'JPY':
        # JPY per 1 yen
        fx = round(invest_krw / (qty * avg), 4) if (qty * avg) > 0 else 8.482
    
    item = {'acc': acc_id, 't': t, 'qty': qty, 'avg': avg}
    if ccy in ('USD', 'JPY'):
        item['fx'] = fx
    opening.append(item)

print(f"Generated {len(assets)} assets and {len(opening)} opening items.")

# Verify evaluation sum with FX = {KRW: 1, USD: 1341.0, JPY: 8.482}
FX = {'KRW': 1.0, 'USD': 1341.0, 'JPY': 8.482}
calc_eval = 0
calc_invest = 0
for op in opening:
    a = assets[op['t']]
    fx_rate = FX[a['currency']]
    cur_val = op['qty'] * a['price'] * fx_rate
    inv_val = op['qty'] * op['avg'] * op.get('fx', fx_rate)
    calc_eval += cur_val
    calc_invest += inv_val

print(f"Calculated Eval KRW:   {calc_eval:15,.0f}")
file_eval = sum(float(r['원화 평가금액']) for r in rows)
file_invest = sum(float(r['원화 매입금액']) for r in rows)
print(f"Original File Eval:    {file_eval:15,.0f}")
print(f"Diff:                  {calc_eval - file_eval:15,.0f}")
print(f"Calculated Invest KRW: {calc_invest:15,.0f}")
print(f"Original File Invest:  {file_invest:15,.0f}")
print(f"Diff:                  {calc_invest - file_invest:15,.0f}")

print("\nDifferences > 1000:")
for i, (op, r) in enumerate(zip(opening, rows)):
    a = assets[op['t']]
    fx_rate = FX[a['currency']]
    cur_val = op['qty'] * a['price'] * fx_rate
    file_val = float(r['원화 평가금액'])
    diff = cur_val - file_val
    if abs(diff) > 1000:
        print(f"Diff row {i}: {op['t']} ({a['name']}): calc {cur_val:,.0f} vs file {file_val:,.0f} (diff: {diff:,.0f})")
