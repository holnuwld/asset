import json
from datetime import datetime
from backend.db.database import get_db

def seed_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM accounts")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    accounts = [
        ("SAM_GEN", "삼성증권", "삼성증권 (종합/주식보상S)", "일반위탁", '["KR_STOCK","KR_ETF","CASH"]', 35.0, "KRW"),
        ("NAMU_GEN", "나무증권", "나무증권 (평생우대 CMA)", "CMA/위탁", '["KR_STOCK","KR_ETF","CASH"]', 25.0, "KRW"),
        ("KIW_OVS", "키움증권", "키움증권 (해외직투/외화RP)", "해외직투", '["US_STOCK","US_ETF","JP_STOCK","JP_ETF","RP","CASH"]', 12.0, "USD"),
        ("NAMU_GOLD", "나무증권", "나무증권 (KRX금현물)", "금현물", '["KRX_GOLD","CASH"]', 7.0, "KRW"),
        ("KB_PEN", "KB증권", "KB증권 (신연금저축)", "연금저축", '["KR_ETF","CASH"]', 6.0, "KRW"),
        ("KIW_ISA", "키움증권", "키움증권 (중개형ISA)", "ISA", '["KR_STOCK","KR_ETF","RP","CASH"]', 5.0, "KRW"),
        ("MG_DEP", "새마을금고", "새마을금고 (정기예탁금)", "정기예금", '["DEPOSIT"]', 3.0, "KRW"),
        ("SAM_IRP", "삼성증권", "삼성증권 (퇴직연금 IRP)", "IRP", '["KR_ETF","CASH"]', 3.0, "KRW"),
        ("TOSS_FX", "토스뱅크", "토스뱅크 (외화통장 엔화)", "외화예금", '["CASH"]', 4.0, "JPY")
    ]
    cur.executemany("""
    INSERT INTO accounts (id, broker, name, account_type, allowed_markets, target_pct, base_currency)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, accounts)

    assets_data = [
        ("CASH-KRW", "원화 예수금", 'CASH', 'KRW', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("CASH-USD", "달러 외화예수금", 'CASH', 'USD', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'USD', 'USD', None, 'liquid', None, None, None),
        ("CASH-JPY", "엔화 외화예수금", 'CASH', 'JPY', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'JPY', 'JPY', None, 'liquid', None, None, None),
        ("000270", "기아", 'KR_STOCK', 'KRW', 'STOCK', 96700.0, 81221.4, 111205.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("000660", "SK하이닉스", 'KR_STOCK', 'KRW', 'STOCK', 1414000.0, 1308857.0, 1626100.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("005380", "현대차", 'KR_STOCK', 'KRW', 'STOCK', 279000.0, 232300.0, 320850.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("005930", "삼성전자", 'KR_STOCK', 'KRW', 'STOCK', 222000.0, 70231.9, 255300.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("006400", "삼성SDI", 'KR_STOCK', 'KRW', 'STOCK', 497500.0, 288875.1, 572125.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("030190", "NICE평가정보", 'KR_STOCK', 'KRW', 'STOCK', 17320.0, 15229.0, 19918.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("035420", "NAVER", 'KR_STOCK', 'KRW', 'STOCK', 171200.0, 213719.7, 196880.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("051600", "한전KPS", 'KR_STOCK', 'KRW', 'STOCK', 41900.0, 56769.0, 48185.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("078600", "대주전자재료", 'KR_STOCK', 'KRW', 'STOCK', 83100.0, 99517.0, 95565.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("091160", "KODEX 미국반도체", 'KR_ETF', 'KRW', 'STOCK', 46307.3, 12325.0, 53253.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("131970", "두산테스나", 'KR_STOCK', 'KRW', 'STOCK', 82900.0, 34017.0, 95335.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("138910", "TIGER 구리실물", 'KR_ETF', 'KRW', 'STOCK', 15378.8, 15594.0, 17686.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("192650", "드림텍", 'KR_STOCK', 'KRW', 'STOCK', 6330.0, 9741.0, 7279.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("195870", "해성디에스", 'KR_STOCK', 'KRW', 'STOCK', 44150.0, 50486.1, 50772.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("207940", "삼성바이오로직스", 'KR_STOCK', 'KRW', 'STOCK', 1435000.0, 912111.0, 1650250.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("243840", "신흥에스이씨", 'KR_STOCK', 'KRW', 'STOCK', 5710.0, 10167.0, 6566.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("245340", "TIGER 미국다우존스30", 'KR_ETF', 'KRW', 'STOCK', 33740.0, 16800.0, 38801.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("269540", "PLUS 미국S&P500(H)", 'KR_ETF', 'KRW', 'STOCK', 29410.0, 13780.0, 33822.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("278530", "KODEX 200TR", 'KR_ETF', 'KRW', 'STOCK', 32430.0, 8249.0, 37294.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("282A.T", "GLOBAL X JAPAN SEMICONDUCTOR (282A)", 'JP_ETF', 'JPY', 'STOCK', 2083.0, 1750.0, 2395.0, 'risk_on', 'JPY', 'JPY', "JP", 'liquid', None, None, None),
        ("329180", "HD현대중공업", 'KR_STOCK', 'KRW', 'STOCK', 289000.0, 491628.4, 332350.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("329750", "TIGER 미국달러단기채권액티브", 'KR_ETF', 'KRW', 'STOCK', 12733.9, 13054.0, 14644.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("371460", "TIGER 차이나전기차SOLACTIVE", 'KR_ETF', 'KRW', 'STOCK', 8523.9, 10251.0, 9802.0, 'risk_on', 'CNY', 'KRW', "CN", 'liquid', None, None, None),
        ("379780", "RISE 미국S&P500", 'KR_ETF', 'KRW', 'STOCK', 20677.09, 17696.36, 23779.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("379800", "KODEX 미국나스닥100TR", 'KR_ETF', 'KRW', 'STOCK', 21855.88, 19200.0, 25134.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("381170", "TIGER 미국테크TOP10 INDXX", 'KR_ETF', 'KRW', 'STOCK', 28378.1, 12636.0, 32635.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("396500", "TIGER 반도체TOP10", 'KR_ETF', 'KRW', 'STOCK', 29802.7, 24332.0, 34273.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("449170", "TIGER KOFR금리액티브(합성)", 'KR_ETF', 'KRW', 'STOCK', 112325.0, 109407.0, 129174.0, 'risk_off', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("453850", "ACE 미국30년국채액티브(H)", 'KR_ETF', 'KRW', 'STOCK', 7616.14, 8736.13, 8759.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("457490", "KODEX 머니마켓액티브", 'KR_ETF', 'KRW', 'STOCK', 106030.0, 103738.0, 121934.0, 'risk_off', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("457490_US", "KODEX 미국머니마켓액티브", 'KR_ETF', 'KRW', 'STOCK', 13330.0, 13869.99, 15329.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("475400", "씨메스로보틱스", 'KR_STOCK', 'KRW', 'STOCK', 13390.0, 34403.2, 15398.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("487410", "KODEX 반도체레버리지", 'KR_ETF', 'KRW', 'STOCK', 46355.0, 144383.0, 53308.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("487430", "KODEX AI전력핵심설비", 'KR_ETF', 'KRW', 'STOCK', 25075.0, 40349.0, 28836.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("487440", "KODEX 미국AI전력핵심인프라", 'KR_ETF', 'KRW', 'STOCK', 15698.3, 16068.0, 18053.0, 'risk_on', 'USD', 'KRW', "US", 'liquid', None, None, None),
        ("6954.T", "FANUC (화낙, 6954)", 'JP_STOCK', 'JPY', 'STOCK', 5648.0, 6184.0, 6495.0, 'risk_on', 'JPY', 'JPY', "JP", 'liquid', None, None, None),
        ("7003.T", "MITSUI E&S HOLDINGS (미쓰이E&S홀딩스, 7003)", 'JP_STOCK', 'JPY', 'STOCK', 3506.0, 5796.67, 4032.0, 'risk_on', 'JPY', 'JPY', "JP", 'liquid', None, None, None),
        ("8001.T", "ITOCHU CORP (이토추상사, 8001)", 'JP_STOCK', 'JPY', 'STOCK', 2271.0, 1889.4, 2612.0, 'risk_on', 'JPY', 'JPY', "JP", 'liquid', None, None, None),
        ("BOXX", "Alpha Architect 1-3 Month Box ETF (BOXX)", 'US_ETF', 'USD', 'STOCK', 118.85, 117.12, 136.68, 'risk_off', 'USD', 'USD', "US", 'liquid', None, None, None),
        ("CASH-JPY-KIWOVS", "키움증권 JPY 외화예수금", 'CASH', 'JPY', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'JPY', 'JPY', None, 'liquid', None, None, None),
        ("CASH-JPY-TOSS", "토스 외화통장 엔화(JPY)", 'CASH', 'JPY', 'CASH', 1.0, 1.052099176, 1.0, 'risk_off', 'JPY', 'JPY', None, 'liquid', None, None, None),
        ("CASH-KRW-KB", "KB증권 연금예수금", 'CASH', 'KRW', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("CASH-KRW-KIWOVS", "키움증권 원화예수금", 'CASH', 'KRW', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("CASH-KRW-NAMUGOLD", "나무 금현물 예수금", 'CASH', 'KRW', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("CASH-KRW-SAMGEN", "삼성증권 일반예수금", 'CASH', 'KRW', 'CASH', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("CASH-KRW-SAMIRP", "현금성자산(삼성증권)", 'CASH', 'KRW', 'RP', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("CASH-USD-KIWOVS", "키움증권 USD 외화예수금", 'CASH', 'USD', 'CASH', 1.0, 1.0, 1.15, 'risk_off', 'USD', 'USD', None, 'liquid', None, None, None),
        ("DEP-MG-2027", "삼성전자 새마을금고 정기예탁금", 'DEPOSIT', 'KRW', 'DEPOSIT', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'fixed', 0.038, "2025-11-03", "2027-11-03"),
        ("GOLD-KRX", "금 99.99_1kg", 'KRX_GOLD', 'KRW', 'STOCK', 168970.0, 115869.0, 194315.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("HANWHA_VISION", "한화비전", 'KR_STOCK', 'KRW', 'STOCK', 48450.0, 54898.0, 55717.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("KORU", "Direxion Daily MSCI South Korea Bull 3X Shares (KORU)", 'US_ETF', 'USD', 'STOCK', 11.1315, 28.108, 12.8, 'risk_on', 'USD', 'USD', "KR", 'liquid', None, None, None),
        ("RAM", "Roundhill T-Rex 2X Long DRAM and Memory Device ETF (RAM)", 'US_ETF', 'USD', 'STOCK', 8.0999, 20.5694, 9.31, 'risk_on', 'USD', 'USD', "US", 'liquid', None, None, None),
        ("RP-KRW-ISA-7D", "일반RP(7일, 2.65%)", 'CASH', 'KRW', 'RP', 1.0, 1.0, 1.0, 'risk_off', 'KRW', 'KRW', None, 'liquid', None, None, None),
        ("RP-USD-7D-1", "USD 일반RP(7일, 3.50%) #1", 'CASH', 'USD', 'RP', 1.0, 1.0, 1.15, 'risk_off', 'USD', 'USD', None, 'liquid', None, None, None),
        ("RP-USD-7D-2", "USD 일반RP(7일, 3.50%) #2", 'CASH', 'USD', 'RP', 1.0, 1.0, 1.15, 'risk_off', 'USD', 'USD', None, 'liquid', None, None, None),
        ("RP-USD-ONDEMAND", "USD 일반RP(수시, 3.35%)", 'CASH', 'USD', 'RP', 1.0, 1.0, 1.15, 'risk_off', 'USD', 'USD', None, 'liquid', None, None, None),
        ("SAMSUNG_EPIS_HOLDINGS", "삼성에피스홀딩스", 'KR_STOCK', 'KRW', 'STOCK', 310500.0, 912111.0, 357075.0, 'risk_on', 'KRW', 'KRW', "KR", 'liquid', None, None, None),
        ("SMR", "NuScale Power Corp (SMR)", 'US_STOCK', 'USD', 'STOCK', 5.41, 14.8, 6.22, 'risk_on', 'USD', 'USD', "US", 'liquid', None, None, None),
        ("TSLA", "Tesla Inc (TSLA)", 'US_STOCK', 'USD', 'STOCK', 405.175, 390.005, 465.95, 'risk_on', 'USD', 'USD', "US", 'liquid', None, None, None),
        ("UEC", "Uranium Energy Corp (UEC)", 'US_STOCK', 'USD', 'STOCK', 7.66, 12.22, 8.81, 'risk_on', 'USD', 'USD', "US", 'liquid', None, None, None),
    ]
    cur.executemany("""
    INSERT INTO assets (ticker, name, market, currency, kind, price, prev_price, high_52w, exp_risk, exp_currency_real, exp_currency_listing, exp_country, exp_liquidity, deposit_rate, deposit_start, deposit_maturity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, assets_data)

    opening_data = [
        ('KB_PEN', '396500', 748.0, 24332.0, 1.0),
        ('KB_PEN', '091160', 242.0, 12325.0, 1.0),
        ('KB_PEN', '487440', 562.0, 16068.0, 1.0),
        ('SAM_IRP', '396500', 268.0, 27060.52, 1.0),
        ('KB_PEN', '381170', 274.0, 12636.0, 1.0),
        ('KB_PEN', '329750', 463.0, 13054.0, 1.0),
        ('SAM_IRP', '457490_US', 379.0, 13869.99, 1.0),
        ('KB_PEN', '138910', 280.0, 15594.0, 1.0),
        ('KB_PEN', 'CASH-KRW-KB', 4031065.0, 1.0, 1.0),
        ('SAM_IRP', '379800', 170.0, 19200.0, 1.0),
        ('SAM_IRP', '379780', 110.0, 17696.36, 1.0),
        ('SAM_IRP', '453850', 295.0, 8736.13, 1.0),
        ('KB_PEN', '371460', 214.0, 10251.0, 1.0),
        ('SAM_IRP', '245340', 40.0, 16800.0, 1.0),
        ('SAM_IRP', '269540', 45.0, 13780.0, 1.0),
        ('SAM_IRP', 'CASH-KRW-SAMIRP', 192900.0, 1.0, 1.0),
        ('SAM_GEN', '005930', 1300.0, 70231.9, 1.0),
        ('NAMU_GEN', '457490', 900.0, 103738.0, 1.0),
        ('NAMU_GEN', '449170', 509.0, 109407.0, 1.0),
        ('KIW_ISA', '457490_US', 3674.0, 13950.0, 1.0),
        ('NAMU_GEN', '000660', 28.0, 1308857.0, 1.0),
        ('SAM_GEN', '005380', 123.0, 232300.0, 1.0),
        ('SAM_GEN', '006400', 44.0, 288875.1, 1.0),
        ('NAMU_GEN', '078600', 252.0, 99517.0, 1.0),
        ('NAMU_GEN', '487430', 750.0, 40349.0, 1.0),
        ('NAMU_GEN', '278530', 519.0, 8249.0, 1.0),
        ('SAM_GEN', '457490_US', 1137.0, 13871.1, 1.0),
        ('SAM_GEN', '035420', 55.0, 213719.7, 1.0),
        ('SAM_GEN', '195870', 209.0, 50486.1, 1.0),
        ('SAM_GEN', '000270', 88.0, 81221.4, 1.0),
        ('NAMU_GEN', '051600', 178.0, 56769.0, 1.0),
        ('NAMU_GEN', '207940', 5.0, 912111.0, 1.0),
        ('NAMU_GEN', '192650', 829.0, 9741.0, 1.0),
        ('NAMU_GEN', '030190', 228.0, 15229.0, 1.0),
        ('SAM_GEN', '329180', 12.0, 491628.4, 1.0),
        ('NAMU_GEN', '487410', 56.0, 144383.0, 1.0),
        ('SAM_GEN', 'CASH-KRW-SAMGEN', 2555616.0, 1.0, 1.0),
        ('NAMU_GEN', '243840', 400.0, 10167.0, 1.0),
        ('NAMU_GEN', 'SAMSUNG_EPIS_HOLDINGS', 3.0, 912111.0, 1.0),
        ('SAM_GEN', '475400', 12.0, 34403.2, 1.0),
        ('SAM_GEN', '131970', 1.0, 34017.0, 1.0),
        ('SAM_GEN', 'HANWHA_VISION', 1.0, 54898.0, 1.0),
        ('KIW_OVS', 'BOXX', 200.0, 117.12, 1341.0),
        ('KIW_OVS', 'TSLA', 30.0, 390.005, 1341.0),
        ('KIW_OVS', '8001.T', 500.0, 1889.4, 8.4819),
        ('KIW_OVS', '7003.T', 300.0, 5796.67, 8.4819),
        ('KIW_OVS', '6954.T', 100.0, 6184.0, 8.4819),
        ('KIW_OVS', 'KORU', 300.0, 28.108, 1341.0),
        ('KIW_OVS', 'RAM', 309.0, 20.5694, 1341.0),
        ('KIW_OVS', '282A.T', 150.0, 1750.0, 8.4819),
        ('KIW_OVS', 'SMR', 165.0, 14.8, 1341.0),
        ('NAMU_GOLD', 'GOLD-KRX', 470.0, 115869.0, 1.0),
        ('KIW_OVS', 'UEC', 275.0, 12.22, 1341.0),
        ('NAMU_GOLD', 'CASH-KRW-NAMUGOLD', 3692.0, 1.0, 1.0),
        ('MG_DEP', 'DEP-MG-2027', 30000000.0, 1.0, 1.0),
        ('TOSS_FX', 'CASH-JPY-TOSS', 2539397.0, 1.052099176, 8.482),
        ('KIW_OVS', 'RP-USD-7D-1', 11581.0, 1.0, 1341.0),
        ('KIW_OVS', 'RP-USD-7D-2', 5600.0, 1.0, 1341.0),
        ('KIW_OVS', 'RP-USD-ONDEMAND', 4400.0, 1.0, 1341.0),
        ('KIW_ISA', 'RP-KRW-ISA-7D', 2580000.0, 1.0, 1.0),
        ('KIW_OVS', 'CASH-JPY-KIWOVS', 50633.0, 1.0, 8.4819),
        ('KIW_OVS', 'CASH-KRW-KIWOVS', 1482.0, 1.0, 1.0),
        ('KIW_OVS', 'CASH-USD-KIWOVS', 0.23, 1.0, 1339.13),
    ]
    cur.executemany("""
    INSERT INTO opening_balances (account_id, ticker, quantity, avg_price, avg_fx)
    VALUES (?, ?, ?, ?, ?)
    """, opening_data)

    # Initial transactions
    tx_data = [
        ("TX-1001", 1001, "2026-10-15 10:15", "TELEGRAM", "SAM_GEN", "BUY", "005930", 50, 220000.0, 0, 1.0, "ACTIVE", "[삼성증권] 매수체결 삼성전자 50주 단가 220,000원", "국내주식 체결"),
        ("TX-1002", 1002, "2026-10-22 14:20", "TELEGRAM", "KIW_OVS", "SELL", "TSLA", 5, 410.0, 0, 1341.0, "ACTIVE", "[키움증권] 해외주식 매도 TSLA 5주 체결가 $410.00", "해외주식 체결"),
        ("TX-1003", 1003, "2026-10-28 11:00", "TELEGRAM", "NAMU_GOLD", "BUY", "GOLD-KRX", 10, 169000.0, 0, 1.0, "ACTIVE", "[나무증권] 매수체결 금현물 10g 단가 169,000원", "국내/금현물 체결"),
        ("TX-1004", 1004, "2026-11-01 09:30", "TELEGRAM(명령)", "SAM_GEN", "DEPOSIT", "CASH-KRW-SAMGEN", 10000000.0, 1.0, 0, 1.0, "ACTIVE", "/입금 삼성종합 10000000", "외부 원금 추가납입")
    ]
    cur.executemany("""
    INSERT INTO transactions (id, seq, time, source, acc, type, ticker, qty, price, fee, fx, status, raw, parser)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tx_data)

    conn.commit()
    conn.close()
    print("Database seeded successfully with 2026-11-03 portfolio data.")

if __name__ == "__main__":
    from backend.db.database import init_db
    import os
    if os.path.exists("data/asset.db"):
        os.remove("data/asset.db")
    init_db()
    seed_db()
