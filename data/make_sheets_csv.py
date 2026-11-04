import csv
import json
import os

data_dir = r"c:\cowork\asset\data"
json_path = os.path.join(data_dir, "assets_261103.json")

with open(json_path, "r", encoding="utf-8") as f:
    assets = json.load(f)

csv_out = os.path.join(data_dir, "금융자산_261103.csv")

headers = [
    "대분류", "금융기관", "계좌명", "계좌번호", "자산구분", "종목명", "티커",
    "거래통화", "보유수량", "매수단가(원통화)", "현재가(원통화)", "평가금액(원통화)", "평가손익(원통화)", "수익률(%)",
    "원화 매입금액", "원화 평가금액", "원화 평가손익", "세부태그"
]

rows = []
for a in assets:
    rows.append({
        "대분류": a["primary_category"],
        "금융기관": a["institution"],
        "계좌명": a["account_name"],
        "계좌번호": a["account_no"],
        "자산구분": a["asset_type"],
        "종목명": a["asset_name"],
        "티커": a["ticker"],
        "거래통화": a["currency"],
        "보유수량": a["quantity"],
        "매수단가(원통화)": a["avg_buy_price"],
        "현재가(원통화)": a["current_price_original"],
        "평가금액(원통화)": a["eval_amount_original"],
        "평가손익(원통화)": a["profit_loss_original"],
        "수익률(%)": a["profit_rate_pct"],
        "원화 매입금액": a["krw_buy_amount"],
        "원화 평가금액": a["krw_eval_amount"],
        "원화 평가손익": a["krw_profit_loss"],
        "세부태그": ", ".join(a["tags"])
    })

# 대분류 우선 정렬 (연금 -> 국내주식 -> 해외주식 -> 원자재 -> 현금성자산), 그 다음 평가금액 내림차순
category_order = {"연금": 1, "국내주식": 2, "해외주식": 3, "원자재": 4, "현금성자산": 5}
rows.sort(key=lambda x: (category_order.get(x["대분류"], 99), -x["원화 평가금액"]))

with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Generated {csv_out} with {len(rows)} rows.")
