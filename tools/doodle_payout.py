#!/usr/bin/env python3
"""Pay what doodle voters are owed, in sats, over Lightning, through a local phoenixd.

Nan, 2026-10-05: "use lightning." The ledger is tools/doodle_score.py's; this turns each payee's owed
dollars into whole sats at the current price (mempool.space /api/v1/prices), pays the ones owed at
least MIN_SATS through phoenixd's POST /paylnaddress, and appends what was paid to
cache/doodle_votes/paid.jsonl, which the ledger reads back. The part of a sat left over stays owed.

Only a Lightning address (name@domain) is paid; anything else stays owed and is listed. A run stops
at RUN_CAP_USD unless --cap says otherwise, and stops when the wallet balance would not cover it.

phoenixd: https://phoenix.acinq.co/server — runs on this Mac, port 9740, basic auth with the
http-password from ~/.phoenix/phoenix.conf. Fund it before the first run.

    python3 tools/doodle_payout.py                 what would be paid, nothing sent
    python3 tools/doodle_payout.py --send          pay it
    python3 tools/doodle_payout.py --send --cap 20 pay at most $20 this run
"""
import base64
import datetime as dt
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import doodle_score  # noqa: E402

PHOENIXD = "http://127.0.0.1:9740"
CONF = Path.home() / ".phoenix" / "phoenix.conf"
PRICE_URL = "https://mempool.space/api/v1/prices"
MIN_SATS = 100
RUN_CAP_USD = 10.0
LN_ADDRESS = re.compile(r"^[a-z0-9._+-]+@[a-z0-9-]+(\.[a-z0-9-]+)+$", re.I)
MESSAGE = "Mot Dang doodle notes and picks · motdang.net/doodles"


def usd_per_btc():
    req = urllib.request.Request(PRICE_URL, headers={"User-Agent": "MotDangPayout/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return float(json.loads(r.read())["USD"])


def phoenixd(path, form=None):
    m = re.search(r"^http-password=(.+)$", CONF.read_text(), re.M) if CONF.exists() else None
    if not m:
        raise SystemExit("no http-password in %s: is phoenixd installed and run once?" % CONF)
    auth = base64.b64encode((":" + m.group(1).strip()).encode()).decode()
    data = urllib.parse.urlencode(form).encode() if form is not None else None
    req = urllib.request.Request(PHOENIXD + path, data=data, headers={"Authorization": "Basic " + auth})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def plan(price):
    """[(payee, sats, usd)] that can be paid now, and [(payee, owed_usd, why)] that cannot."""
    W, _, events, V, N, F, K = doodle_score.weighted()
    L = doodle_score.ledger(V, N, F, K)
    pay, wait = [], []
    for p, P in sorted(L.items(), key=lambda x: -x[1]["owed"]):
        if P["owed"] <= 0:
            continue
        sats = math.floor(P["owed"] / price * 1e8)
        if not LN_ADDRESS.match(p):
            wait.append((p, P["owed"], "not a Lightning address"))
        elif sats < MIN_SATS:
            wait.append((p, P["owed"], "%d sats owed, paid from %d" % (sats, MIN_SATS)))
        else:
            pay.append((p, sats, sats / 1e8 * price))
    return pay, wait


def main(a):
    send = "--send" in a
    cap = float(a[a.index("--cap") + 1]) if "--cap" in a else RUN_CAP_USD
    price = usd_per_btc()
    pay, wait = plan(price)
    print("BTC $%.0f · %d payee(s) to pay, $%.4f · %d waiting" % (price, len(pay), sum(u for _, _, u in pay), len(wait)))
    for p, s, u in pay:
        print("  pay   %-40s %7d sats  $%.4f" % (p[:40], s, u))
    for p, u, why in wait:
        print("  wait  %-40s $%.4f  %s" % (p[:40], u, why))
    if not send:
        print("dry run: nothing sent (--send pays)")
        return
    bal = phoenixd("/getbalance")
    have = int(bal.get("balanceSat", 0))
    print("wallet: %d sats" % have)
    out = doodle_score.PAID
    out.parent.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    for p, s, u in pay:
        if spent + u > cap:
            print("  stop: the run cap of $%.2f" % cap)
            break
        if s > have:
            print("  stop: the wallet holds %d sats, %s is owed %d" % (have, p, s))
            break
        try:
            r = phoenixd("/paylnaddress", {"amountSat": s, "address": p, "message": MESSAGE})
        except (urllib.error.URLError, json.JSONDecodeError) as err:
            print("  fail  %s: %s" % (p, err))
            continue
        if "paymentPreimage" not in r:
            print("  fail  %s: %s" % (p, r.get("reason", r)))
            continue
        fee = int(r.get("routingFeeSat", 0))
        have -= s + fee
        spent += u
        with open(out, "a") as fh:
            fh.write(json.dumps({"payee": p, "usd": round(u, 6), "sats": s, "fee_sats": fee, "btc_usd": price,
                                 "at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                                 "ref": r.get("paymentId", "")}) + "\n")
        print("  paid  %-40s %7d sats (+%d fee)" % (p[:40], s, fee))
    print("paid $%.4f this run" % spent)


if __name__ == "__main__":
    main(sys.argv[1:])
