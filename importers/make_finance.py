#!/usr/bin/env python3
"""Bake the currency converter + Thai gold ticker + crypto rows for the home page.

Everything is a build-time snapshot (like the news ticker) — fetched once here,
written to data/finance.json, and read by build.py with zero external
requests at page-load time. Refresh by re-running this before build.py;
morning_walk.sh runs it daily.

  python3 importers/make_finance.py

Sources, in order of preference:
- FX: Bank of Thailand reference rates (the official Thai figure — daily
  weighted-average interbank). The token lives in ~/.config/nanobotco/keys.json
  and never enters this repo. Falls back to Frankfurter (ECB, keyless) whenever
  the token or the gateway is unavailable, so a missing key degrades the
  source, never the widget.
- Gold: the Gold Traders Association's own public API (unchanged).
- Crypto: CoinGecko (demo key, same key store) — BTC, ETH, USDT in THB.
  Baked, never fetched from the reader's browser: a keyed commercial API is
  ours to call, not the reader's to be exposed to.

BOT unit trap, learned from the data: some currencies are quoted per 100 or
per 1,000 units — JPY arrives as "JAPAN : YEN (100 YEN)" with mid ~20.8.
The per-unit divisor is parsed out of the currency name, never assumed.
"""
import json
import re
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS_PATH = Path.home() / ".config" / "nanobotco" / "keys.json"
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; daily finance snapshot)"

FX_WANTED = ["USD", "EUR", "GBP", "CNY", "JPY"]
ECB_URL = "https://api.frankfurter.app/latest?from=THB&to=" + ",".join(FX_WANTED)
GOLD_URL = "https://www.goldtraders.or.th/api/GoldPrices/Latest?readjson=false"
COINS = [("bitcoin", "BTC", "บิตคอยน์"), ("ethereum", "ETH", "อีเธอเรียม"),
         ("tether", "USDT", "เทเธอร์")]


def load_keys():
    try:
        return json.loads(KEYS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def per_units(currency_name):
    """BOT quotes some currencies per 100 / per 1,000 — stated in the name."""
    m = re.search(r"\(([\d,]+)\s", currency_name or "")
    return int(m.group(1).replace(",", "")) if m else 1


def fx_from_bot(keys):
    bot = keys.get("bot_api") or {}
    tok, base = bot.get("token"), bot.get("base_fx")
    if not (tok and base):
        return None
    end = date.today()
    url = (f"{base}/DAILY_AVG_EXG_RATE/?start_period={end - timedelta(days=9)}"
           f"&end_period={end}&currency=")
    doc = fetch_json(url, headers={"Authorization": tok})
    latest = {}
    for row in doc["result"]["data"]["data_detail"]:
        cur = row.get("currency_id")
        if cur in FX_WANTED and (cur not in latest or row["period"] > latest[cur]["period"]):
            latest[cur] = row
    if len(latest) < len(FX_WANTED):
        return None
    rates, mid_thb = {}, {}
    day = max(r["period"] for r in latest.values())
    for cur, row in latest.items():
        units = per_units(row.get("currency_name_eng"))
        mid = float(row["mid_rate"])
        mid_thb[cur] = mid / units          # THB per 1 unit
        rates[cur] = units / mid            # units per 1 THB — the widget contract
    return {"date": day, "rates": rates, "mid_thb": mid_thb, "source": "bot"}


def fx_from_ecb():
    fx = fetch_json(ECB_URL)
    return {"date": fx["date"], "rates": fx["rates"], "source": "ecb"}


def crypto_from_coingecko(keys):
    cg = keys.get("coingecko_demo") or {}
    headers = {}
    if cg.get("key") or cg.get("token"):
        headers[cg.get("header", "x-cg-demo-api-key")] = cg.get("key") or cg.get("token")
    base = cg.get("base", "https://api.coingecko.com/api/v3")
    ids = ",".join(c[0] for c in COINS)
    doc = fetch_json(f"{base}/simple/price?ids={ids}&vs_currencies=thb"
                     f"&include_24hr_change=true", headers=headers)
    coins = []
    for cid, sym, th in COINS:
        row = doc.get(cid) or {}
        if "thb" not in row:
            continue
        coins.append({"id": cid, "sym": sym, "nameTh": th,
                      "thb": row["thb"],
                      "chg24": round(row.get("thb_24h_change") or 0.0, 2)})
    if not coins:
        return None
    from datetime import datetime
    return {"asOf": datetime.now().strftime("%Y-%m-%d %H:%M"), "coins": coins,
            "source": "coingecko"}


def main():
    keys = load_keys()
    out = {}
    try:
        out["fx"] = fx_from_bot(keys)
        if out["fx"]:
            print(f"fx: BOT {out['fx']['date']} — " +
                  ", ".join(f"{c} {v:.4f}" for c, v in out["fx"]["rates"].items()))
    except Exception as e:
        print(f"fx: BOT failed — {e}")
        out["fx"] = None
    if not out.get("fx"):
        try:
            out["fx"] = fx_from_ecb()
            print(f"fx: ECB fallback {out['fx']['date']} — {out['fx']['rates']}")
        except Exception as e:
            print(f"fx: FAILED entirely — {e}")
            out.pop("fx", None)
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
    try:
        crypto = crypto_from_coingecko(keys)
        if crypto:
            out["crypto"] = crypto
            print("crypto: " + ", ".join(f"{c['sym']} ฿{c['thb']:,.0f}" for c in crypto["coins"]))
    except Exception as e:
        print(f"crypto: FAILED — {e}")
    out["generated"] = date.today().isoformat()
    (ROOT / "data" / "finance.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote data/finance.json")


if __name__ == "__main__":
    main()
