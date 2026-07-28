#!/usr/bin/env python3
"""Bake the currency converter + Thai gold ticker for the home page.

Both are build-time snapshots (like the news ticker) — fetched once here,
written to data/finance.json, and read by build.py with zero external
requests at page-load time. Refresh by re-running this before build.py.

  python3 importers/make_finance.py

Sources: Frankfurter (ECB rates, free/keyless) for currency; the Gold
Traders Association's own public API for Thai gold.
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; daily finance snapshot)"

FX_URL = "https://api.frankfurter.app/latest?from=THB&to=USD,EUR,GBP,CNY,JPY"
GOLD_URL = "https://www.goldtraders.or.th/api/GoldPrices/Latest?readjson=false"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main():
    out = {}
    try:
        fx = fetch_json(FX_URL)
        out["fx"] = {"date": fx["date"], "rates": fx["rates"]}
        print(f"fx: {fx['date']} — {fx['rates']}")
    except Exception as e:
        print(f"fx: FAILED — {e}")
    try:
        g = fetch_json(GOLD_URL)
        out["gold"] = {
            "asOf": g["asTime"],
            "barBuy": g["bL_BuyPrice"], "barSell": g["bL_SellPrice"],
            "ornamentBuy": g["oM965_BuyPrice"], "ornamentSell": g["oM965_SellPrice"],
            "changeFromPrevDay": g["priceChangeFromPrevDayLast"],
        }
        print(f"gold: {g['asTime']} — bar {g['bL_BuyPrice']}/{g['bL_SellPrice']}")
    except Exception as e:
        print(f"gold: FAILED — {e}")
    (ROOT / "data" / "finance.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote data/finance.json")


if __name__ == "__main__":
    main()
