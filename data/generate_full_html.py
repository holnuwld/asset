import re
import json

with open('data/generated_js.py', 'r', encoding='utf-8') as f:
    js_code = f.read()

# Load js fragments
local_env = {}
exec(js_code, {}, local_env)
ACCOUNTS_JS = local_env['ACCOUNTS_JS']
ASSETS_JS = local_env['ASSETS_JS']
OPENING_JS = local_env['OPENING_JS']
TICKER_ALIAS_JS = local_env['TICKER_ALIAS_JS']
ACC_ALIAS_JS = local_env['ACC_ALIAS_JS']

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Header text
html = re.sub(
    r'<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-500 border border-emerald-500/30">.*?</span>',
    '<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-500 border border-emerald-500/30">● 실사용 9개 계좌 맞춤 (2026.11.03 기준)</span>',
    html, count=1
)
html = re.sub(
    r'<h1 class="text-lg md:text-xl font-bold tracking-tight">AssetFlow 포트폴리오 매니저 <span class="text-sky-400">.*?</span></h1>',
    '<h1 class="text-lg md:text-xl font-bold tracking-tight">AssetFlow 포트폴리오 매니저 <span class="text-sky-400">v2.2</span></h1>',
    html, count=1
)
html = re.sub(
    r'<p class="text-xs text-\[var\(--muted-foreground\)\] mt-0.5">삼성\(일반·IRP\).*?</p>',
    '<p class="text-xs text-[var(--muted-foreground)] mt-0.5">삼성(종합·IRP) · 나무(CMA·KRX금) · 키움(해외·ISA) · KB(연금) · 새마을금고 · 토스(엔화) | 총 평가 10억 6,000만원 | 월간·연간 실현손익 · 기간별 매매조회 · MWRR 평잔수익률</p>',
    html, count=1
)

# 2. Update TODAY, FX, S
today_fx_block = """  const TODAY = new Date(2026, 10, 3, 15, 30);      // 2026-11-03 (화)
  const DAY = 864e5;
  // JPY는 100엔당 원화 환율(848.2원 -> 1엔당 8.482원)
  const FX = { KRW: 1, USD: 1341.0, JPY: 8.482 };"""

html = re.sub(
    r'const TODAY = new Date\(2026, 9, 21, 15, 58\);.*?const FX = \{ KRW: 1, USD: \d+\.?\d*, JPY: \d+\.?\d* \};',
    today_fx_block,
    html, flags=re.DOTALL
)

# 3. Replace ACCOUNTS
accounts_pattern = r'const ACCOUNTS = \[.*?\];\s*const ACC = Object\.fromEntries\(ACCOUNTS\.map\(a => \[a\.id, a\]\)\);'
new_acc_block = f"{ACCOUNTS_JS}\n  const ACC = Object.fromEntries(ACCOUNTS.map(a => [a.id, a]));"
html = re.sub(accounts_pattern, new_acc_block, html, flags=re.DOTALL)

# 4. Update MARKET_LABEL
market_label_old = r'const MARKET_LABEL = \{.*?\};'
market_label_new = """const MARKET_LABEL = {
    KR_STOCK: '국내주식', KR_ETF: '국내상장 ETF', US_STOCK: '미국주식', US_ETF: '미국 ETF',
    JP_STOCK: '일본주식', JP_ETF: '일본 ETF', KRX_GOLD: 'KRX금현물(1g)', DEPOSIT: '정기예탁금',
    RP: '환매조건부채권(RP)', CASH: '예수금'
  };"""
html = re.sub(market_label_old, market_label_new, html, flags=re.DOTALL)

# 5. Replace ASSETS
assets_pattern = r'const ASSETS = \{.*?\n  \};\s*const TICKER_ALIAS = \{'
html = re.sub(assets_pattern, f"{ASSETS_JS}\n\n  const TICKER_ALIAS = {{", html, flags=re.DOTALL)

# 6. Replace TICKER_ALIAS
alias_pattern = r'const TICKER_ALIAS = \{.*?\n  \};\s*const ACC_ALIAS = \['
html = re.sub(alias_pattern, f"{TICKER_ALIAS_JS}\n\n  const ACC_ALIAS = [", html, flags=re.DOTALL)

# 7. Replace ACC_ALIAS
acc_alias_pattern = r'const ACC_ALIAS = \[.*?\];'
html = re.sub(acc_alias_pattern, ACC_ALIAS_JS, html, flags=re.DOTALL)

# 8. Replace OPENING
opening_pattern = r'const OPENING = \[.*?\];\s*// 2026년 1월~8월 확정 월별 실현손익 이력'
new_opening_block = f"{OPENING_JS}\n\n  // 2026년 1월~10월 확정 월별 실현손익 이력"
html = re.sub(opening_pattern, new_opening_block, html, flags=re.DOTALL)

# 9. Update HISTORICAL_MONTHLY_REALIZED
hist_pnl = """  const HISTORICAL_MONTHLY_REALIZED = {
    '2026-01': 1420000,
    '2026-02': 2680000,
    '2026-03': -1190000,
    '2026-04': 3950000,
    '2026-05': 2510000,
    '2026-06': 5120000,
    '2026-07': 1340000,
    '2026-08': 3790000,
    '2026-09': 4850000,
    '2026-10': 3240000
  };"""
html = re.sub(r'const HISTORICAL_MONTHLY_REALIZED = \{.*?\};', hist_pnl, html, flags=re.DOTALL)

# 10. Update DIMS targets
new_dims = """  const DIMS = {
    risk:      { title: '위험자산 vs 안전자산', short: '위험/안전', cats: [
                 { key: 'risk_on',  label: '위험자산 (주식·ETF)', target: 65, hint: '국내/해외 주식·주식형 ETF' },
                 { key: 'risk_off', label: '안전자산 (예금·현금·KRX금·채권)', target: 35, hint: '새마을 예탁금·KRX금·예수금·MMF·단기채·외화RP' } ] },
    currency:  { title: '통화별 자산 비중 (KRW / USD / JPY)', short: '통화', cats: [
                 { key: 'KRW', label: '원화 (KRW)', target: 72, hint: '국내주식·예금·금현물·원화예수금·원화MMF' },
                 { key: 'USD', label: '달러 (USD)', target: 23, hint: '키움 미국주식·외화RP·미국ETF·USD MMF' },
                 { key: 'JPY', label: '엔화 (JPY)', target: 5,  hint: '토스 외화통장 엔화·키움 일본주식' } ] },
    country:   { title: '주식 내 국가별 비중 (한국 / 미국 / 일본)', short: '국가', note: '주식·ETF 자산만 집계', cats: [
                 { key: 'KR', label: '한국주식', target: 75, hint: '삼성전자·현대차·하이닉스 등 국내주식' },
                 { key: 'US', label: '미국주식', target: 21, hint: 'TSLA·BOXX + 연금/IRP/ISA 미국ETF' },
                 { key: 'JP', label: '일본주식', target: 4,  hint: '이토추상사·미쓰이E&S·화낙 등 일본주식' } ] },
    liquidity: { title: '만기고정 vs 유동자산', short: '만기/유동', cats: [
                 { key: 'fixed',  label: '만기고정 (새마을 정기예탁금)', target: 3, hint: '새마을금고 정기예탁금 (3,000만원)' },
                 { key: 'liquid', label: '유동자산 (주식·금·RP·예수금)', target: 97, hint: '상장주식·ETF·KRX금·외화RP·예수금' } ] },
    account:   { title: '실사용 9개 계좌별 자산 비중', short: '계좌(9개)', cats: ACCOUNTS.map(a => ({
                 key: a.id, label: a.name, target: a.target, hint: '허용: ' + a.allow.map(m => MARKET_LABEL[m] || m).join('·') })) }
  };"""
html = re.sub(r'const DIMS = \{.*?\n  \};', new_dims, html, flags=re.DOTALL)

# 11. Update PRESETS
new_presets = """  const PRESETS = [
    ['📩 삼성증권 매수 삼성전자 50주', '[Web발신] [삼성증권] 매수체결 삼성전자 50주 단가 220,000원'],
    ['📩 키움 해외 매도 TSLA 5주(실현손익)', '[키움증권] 해외주식 매도 TSLA 5주 체결가 $410.00'],
    ['📩 키움 일본 이토추 100주 매수(¥)', '[키움증권] 해외주식 매수 8001.T 100주 체결가 ¥2,280'],
    ['📩 나무 KRX금현물 10g 매수', '[나무증권] 매수체결 금현물 10g 단가 169,000원'],
    ['💵 /입금 삼성종합 1,000만원 (원금추가)', '/입금 삼성종합 10000000'],
    ['📩 새마을금고 예탁금 만기 → 삼성증권', '[새마을금고] 정기예탁금 만기해지 원금 30,000,000원 이자 1,140,000원 → 삼성종합 입금'],
    ['⛔ /매수 KB개인연금 삼성전자 (제약거부)', '/매수 KB개인연금 삼성전자 10 222000'],
    ['↩️ /취소 (직전 거래 취소)', '/취소']
  ];"""
html = re.sub(r'const PRESETS = \[.*?\];', new_presets, html, flags=re.DOTALL)

# Write to frontend/index.html, index.html, and sample_dashboard_v2.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('sample_dashboard_v2.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated HTML to frontend/index.html, index.html, and sample_dashboard_v2.html!")
