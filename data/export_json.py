import json
import sys
sys.path.append('.')

with open('data/financial_assets_261103.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)

from data.build_master import assets, opening, get_acc_id, get_asset_info

# Export to json for clean inspection and embedding
with open('data/assets_master.json', 'w', encoding='utf-8') as f:
    json.dump(assets, f, ensure_ascii=False, indent=2)

with open('data/opening_master.json', 'w', encoding='utf-8') as f:
    json.dump(opening, f, ensure_ascii=False, indent=2)

print("Saved assets_master.json and opening_master.json")
