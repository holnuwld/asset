import json

with open('data/assets_master.json', 'r', encoding='utf-8') as f:
    assets = json.load(f)

with open('data/opening_master.json', 'r', encoding='utf-8') as f:
    opening = json.load(f)

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Build ACCOUNTS js
accounts_js = """  const ACCOUNTS = [
    { id: 'SAM_GEN',   name: '삼성증권 (종합/주식보상S)', type: '일반위탁', allow: ['KR_STOCK','KR_ETF','CASH'], target: 35 },
    { id: 'NAMU_GEN',  name: '나무증권 (평생우대 CMA)',  type: 'CMA/위탁', allow: ['KR_STOCK','KR_ETF','CASH'], target: 25 },
    { id: 'KIW_OVS',   name: '키움증권 (해외직투/외화RP)',type: '해외직투', allow: ['US_STOCK','US_ETF','JP_STOCK','JP_ETF','RP','CASH'], target: 12 },
    { id: 'NAMU_GOLD', name: '나무증권 (KRX금현물)',     type: '금현물',   allow: ['KRX_GOLD','CASH'], target: 7 },
    { id: 'KB_PEN',    name: 'KB증권 (신연금저축)',      type: '연금저축', allow: ['KR_ETF','CASH'], target: 6 },
    { id: 'KIW_ISA',   name: '키움증권 (중개형ISA)',     type: 'ISA',      allow: ['KR_STOCK','KR_ETF','RP','CASH'], target: 5 },
    { id: 'MG_DEP',    name: '새마을금고 (정기예탁금)',   type: '정기예금', allow: ['DEPOSIT'], target: 3 },
    { id: 'SAM_IRP',   name: '삼성증권 (퇴직연금 IRP)',   type: 'IRP',      allow: ['KR_ETF','CASH'], target: 3 },
    { id: 'TOSS_FX',   name: '토스뱅크 (외화통장 엔화)', type: '외화예금', allow: ['CASH'], target: 4 }
  ];"""

# Build ASSETS js
assets_lines = ["  const ASSETS = {"]
for k, v in sorted(assets.items()):
    c_str = json.dumps(v['currency'], ensure_ascii=False)
    exp_str = json.dumps(v['exp'], ensure_ascii=False)
    dep_str = ""
    if v['kind'] == 'DEPOSIT':
        dep_str = ", deposit: { rate: 0.038, start: new Date(2025, 10, 3), maturity: new Date(2027, 10, 3) }"
    assets_lines.append(f"    '{k}': {{ name: {json.dumps(v['name'], ensure_ascii=False)}, market: '{v['market']}', ccy: {c_str}, kind: '{v['kind']}', price: {v['price']}, prev: {v['prev']}, high52: {v['high52']}{dep_str}, exp: {exp_str} }},")
assets_lines.append("  };")
assets_js = "\n".join(assets_lines)

# Build OPENING js
opening_lines = ["  const OPENING = ["]
for op in opening:
    fx_part = f", fx: {op['fx']}" if 'fx' in op else ""
    opening_lines.append(f"    {{ acc: '{op['acc']}', t: '{op['t']}', qty: {op['qty']}, avg: {op['avg']}{fx_part} }},")
opening_lines.append("  ];")
opening_js = "\n".join(opening_lines)

# Build TICKER_ALIAS js
aliases = {
    '삼성전자': '005930', '삼전': '005930', '005930': '005930',
    'SK하이닉스': '000660', '하이닉스': '000660', '000660': '000660',
    '현대차': '005380', '005380': '005380',
    '삼성SDI': '006400', '006400': '006400',
    'NAVER': '035420', '네이버': '035420', '035420': '035420',
    '기아': '000270', '000270': '000270',
    '해성디에스': '195870', '195870': '195870',
    '대주전자재료': '078600', '078600': '078600',
    '삼성바이오로직스': '207940', '삼바': '207940', '207940': '207940',
    '드림텍': '192650', '192650': '192650',
    'NICE평가정보': '030190', '030190': '030190',
    '금현물': 'GOLD-KRX', 'KRX금': 'GOLD-KRX', 'KRX금현물': 'GOLD-KRX', 'GOLD-KRX': 'GOLD-KRX', '금 99.99_1kg': 'GOLD-KRX',
    'TSLA': 'TSLA', '테슬라': 'TSLA',
    'BOXX': 'BOXX',
    'UEC': 'UEC', '우라늄에너지': 'UEC',
    'SMR': 'SMR', '뉴스케일파워': 'SMR',
    'KORU': 'KORU',
    'RAM': 'RAM',
    '이토추상사': '8001.T', '이토추': '8001.T', '8001.T': '8001.T', 'ITOCHU': '8001.T',
    '미쓰이E&S': '7003.T', '7003.T': '7003.T',
    '화낙': '6954.T', 'FANUC': '6954.T', '6954.T': '6954.T',
    '일본반도체': '282A.T', '282A.T': '282A.T',
    'TIGER반도체TOP10': '396500', '396500': '396500',
    'KODEX미국반도체': '091160', '091160': '091160', '91160': '091160',
    'KODEX미국AI전력핵심인프라': '487440', '487440': '487440',
    'TIGER미국테크TOP10INDXX': '381170', '381170': '381170',
    'TIGER미국달러단기채권액티브': '329750', '329750': '329750',
    'TIGER구리실물': '138910', '138910': '138910',
    'TIGER차이나전기차SOLACTIVE': '371460', '371460': '371460',
    'KODEX미국머니마켓액티브': '457490_US', '457490_US': '457490_US',
    'KODEX머니마켓액티브': '457490', '457490': '457490',
    'TIGERKOFR금리액티브': '449170', '449170': '449170',
    'KODEXAI전력핵심설비': '487430', '487430': '487430',
    'KODEX200TR': '278530', '278530': '278530',
    'KODEX미국나스닥100TR': '379800', '379800': '379800',
    'RISE미국S&P500': '379780', '379780': '379780',
    'ACE미국30년국채액티브(H)': '453850', '453850': '453850',
    'TIGER미국다우존스30': '245340', '245340': '245340',
    'PLUS미국S&P500(H)': '269540', '269540': '269540',
    '새마을금고정기예탁금': 'DEP-MG-2027', '새마을예금': 'DEP-MG-2027', 'DEP-MG-2027': 'DEP-MG-2027'
}
alias_lines = ["  const TICKER_ALIAS = {"]
for k, v in aliases.items():
    alias_lines.append(f"    {json.dumps(k, ensure_ascii=False)}: '{v}',")
alias_lines.append("  };")
alias_js = "\n".join(alias_lines)

# Build ACC_ALIAS js
acc_alias_js = """  const ACC_ALIAS = [
    [/삼성.*IRP|IRP/i, 'SAM_IRP'],
    [/삼성.*주식|삼성.*종합|삼성/i, 'SAM_GEN'],
    [/키움.*ISA|ISA/i, 'KIW_ISA'],
    [/키움.*외화RP|외화RP/i, 'KIW_OVS'],
    [/키움|해외직투|영웅문/i, 'KIW_OVS'],
    [/나무.*금|금현물|KRX금/i, 'NAMU_GOLD'],
    [/나무|NH|CMA/i, 'NAMU_GEN'],
    [/KB|신연금|연금저축/i, 'KB_PEN'],
    [/새마을|MG/i, 'MG_DEP'],
    [/토스|외화통장/i, 'TOSS_FX']
  ];"""

print("Generated code snippets successfully.")
with open('data/generated_js.py', 'w', encoding='utf-8') as f:
    f.write(f"# Generated JS fragments\nACCOUNTS_JS = '''{accounts_js}'''\nASSETS_JS = '''{assets_js}'''\nOPENING_JS = '''{opening_js}'''\nTICKER_ALIAS_JS = '''{alias_js}'''\nACC_ALIAS_JS = '''{acc_alias_js}'''\n")
