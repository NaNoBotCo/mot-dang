#!/usr/bin/env python3
"""probe_line_oa.py — resolve a LINE handle to its public Official Account page.

    python3 importers/probe_line_oa.py --seed-disk            ids already in the catalogue
    python3 importers/probe_line_oa.py --seed-disk --limit 40 a short polite run
    python3 importers/probe_line_oa.py --ids @gyk4392g,lin.ee/IMU3iSK
    python3 importers/probe_line_oa.py --report               rebuild the JSON from cache, no network
    python3 importers/probe_line_oa.py --self-test            no network

WHY. A Chiang Mai shop with no website often has a LINE Official Account, and
that account has a public web page. Measured 2026-09-21 on @gyk4392g: the page
carries the name, the basic and vanity ids, the certified badge, the friend
count, a phone, a description, an hours field, a street address WITH A LAT/LNG,
and the account's own website field — which is null, which is the finding.

WHAT A HANDLE RESOLVES TO. Three outcomes, all recorded:
  page        page.line.me renders a profile — the full payload above.
  add-friend  page.line.me 307s to line.me/R/ti/p/@<id>; the account is live
              and the basic id is recovered from the redirect, and that is all
              there is. A verified id is still a lead.
  dead        line.me/R/ti/p/@<id> answers 404. The account is gone.

WHAT IT WILL NOT DO.
  · It does not enumerate. Every id probed here was observed somewhere first.
  · isNoIndex is the account asking not to be listed. Honoured, and the skip is
    written down rather than dropped, so a later pass cannot mistake it for a
    gap.
  · ti/p/~<name> and ti/p/<token> are personal handles, not Official Accounts.
    Recorded as kind "personal" and never hydrated.
  · It writes no records. data/curated/line_discovery.json is leads; a record
    needs a person to promote it.

WHAT "NO OTHER FOOTPRINT" MEANS HERE. Only that the OA's own website field is
empty and the catalogue row carrying this handle has no website, on the date in
the row. It is not a claim that none exists.

Politeness: one request at a time, --pause seconds (default 1.5) plus jitter, a
UA that names us, and it stops — saving progress — on a 429 or a 403.
"""
import argparse
import datetime as dt
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
CURATED = ROOT / "data" / "curated"
CACHE = ROOT / "cache" / "line_oa"
SEARCH_SEEDS = ROOT / "cache" / "line_oa_seeds.json"
OUT = CURATED / "line_discovery.json"

UA = "MotDangBot/1.0 (+https://motdang.net/about.html; directory discovery; 530kings@proton.me)"
TODAY = dt.date.today().isoformat()

# An auto-assigned Official Account basic id: @ + 8 of [a-z0-9]. A vanity id is
# @ + 4..20 of [a-z0-9._-]. A personal handle rides ti/p/~name or ti/p/<token>.
BASIC_RE = re.compile(r"^[a-z0-9]{8}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{3,19}$")

URL_RE = re.compile(
    r"https?://(?:"
    r"lin\.ee/(?P<short>[A-Za-z0-9]+)"
    r"|page\.line\.me/(?:%40|@)?(?P<page>[A-Za-z0-9._-]+)"
    r"|line\.me/(?:R/)?ti/p/(?P<tip>[@~]?[A-Za-z0-9._-]+)"
    r")"
)


def classify(handle):
    """('oa', '@id') · ('personal', '~name') · ('short', code) · (None, None)"""
    h = (handle or "").strip()
    if h.startswith("~"):
        return "personal", h
    h = h.lstrip("@")
    if not h:
        return None, None
    # An OA id is lower case. A ti/p/<token> for a person carries capitals.
    if h == h.lower() and ID_RE.match(h):
        return "oa", "@" + h
    return "personal", h


def handles_in(text):
    """Every LINE handle in a blob of text, as (kind, value)."""
    out = []
    for m in URL_RE.finditer(text or ""):
        if m.group("short"):
            out.append(("short", m.group("short")))
        elif m.group("page"):
            out.append(classify(m.group("page")))
        else:
            out.append(classify(m.group("tip")))
    return [(k, v) for k, v in out if k]


# ---- seeds ------------------------------------------------------------------

def seed_from_disk():
    """Handles the catalogue already carries, with the row that carried them."""
    seeds = {}
    for prov in ("cm", "cr"):
        path = CANON / f"{prov}.json"
        if not path.exists():
            continue
        for rec in json.loads(path.read_text(encoding="utf-8")):
            blob = json.dumps(rec, ensure_ascii=False)
            if "lin.ee" not in blob and "line.me" not in blob:
                continue
            for kind, val in handles_in(blob):
                seeds.setdefault((kind, val), []).append({
                    "id": rec.get("id"), "name": rec.get("name"),
                    "province": prov, "hasWebsite": bool(rec.get("website")),
                })
    for path in sorted(CURATED.glob("*.json")):
        try:
            blob = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "lin.ee" not in blob and "line.me" not in blob:
            continue
        for kind, val in handles_in(blob):
            seeds.setdefault((kind, val), []).append({"id": None, "name": None,
                                                      "province": None,
                                                      "hasWebsite": None,
                                                      "from": path.name})
    return seeds


def seed_from_search():
    """Handles discover_line.py found on the open web."""
    seeds = {}
    if not SEARCH_SEEDS.exists():
        return seeds
    doc = json.loads(SEARCH_SEEDS.read_text(encoding="utf-8"))
    for h in doc.get("handles") or []:
        seeds.setdefault((h["kind"], h["handle"]), []).append({
            "id": None, "name": h.get("name_hint"), "province": h.get("prov"),
            "hasWebsite": None, "from": h.get("found_on"),
        })
    return seeds


# ---- the fetch --------------------------------------------------------------

def _get(url, follow=True):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "th,en;q=0.8",
    })
    opener = urllib.request.build_opener()
    if not follow:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        opener = urllib.request.build_opener(NoRedirect)
    with opener.open(req, timeout=25) as r:
        return r.getcode(), r.geturl(), r.read().decode("utf-8", "replace")


def parse_profile(html):
    """The __NEXT_DATA__ payload of a page.line.me profile, flattened."""
    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    outer = json.loads(m.group(1))
    inner = json.loads(outer["props"]["pageProps"]["initialDataString"])
    acc = inner.get("account") or {}
    info = acc.get("accountInfo") or {}
    prof = acc.get("profile") or {}
    di = prof.get("displayInformation") or {}
    na = di.get("newAddress") or {}
    tel = next((b.get("tel") for b in prof.get("btnList") or [] if b.get("tel")), None)
    basic = (prof.get("info") or {}).get("basicInfo") or {}
    return {
        "basicId": info.get("basicSearchId"),
        "vanityId": info.get("premiumSearchId"),
        "name": prof.get("name"),
        "badge": prof.get("badgeType"),
        "friends": info.get("friendCount"),
        "country": info.get("countryCode"),
        "province": na.get("provinceName"),
        "city": na.get("cityName"),
        "address": na.get("baseAddress"),
        "postal": na.get("postalCode"),
        "lat": na.get("lat"),
        "lng": na.get("lng"),
        "tel": tel or di.get("tel"),
        "website": di.get("website"),
        "hours": di.get("workingTime"),
        "desc": basic.get("description"),
        "statusMsg": (prof.get("info") or {}).get("statusMsg"),
        "noIndex": bool(acc.get("isNoIndex")),
    }


def probe(kind, val):
    """One handle to one row. Raises Stop on a rate limit."""
    row = {"kind": kind, "handle": val, "fetched": TODAY}
    if kind == "personal":
        row["outcome"] = "personal"
        return row
    start = f"https://lin.ee/{val}" if kind == "short" else f"https://page.line.me/{val.lstrip('@')}"
    try:
        code, final, html = _get(start)
    except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            raise Stop(f"{e.code} on {start}")
        row["outcome"] = "dead" if e.code == 404 else f"http-{e.code}"
        return row
    except Exception as e:                                   # noqa: BLE001
        row["outcome"] = f"err-{type(e).__name__}"
        return row
    row["final"] = final
    prof = parse_profile(html)
    if prof:
        row["outcome"] = "page"
        row.update(prof)
        return row
    # lin.ee 302s to the add-friend page with the @ percent-encoded (%40), and
    # a regex that only knows "@" reads 33 live accounts as unresolved.
    plain = urllib.parse.unquote(final)
    m = re.search(r"ti/p/@?([A-Za-z0-9._-]+)", plain) or re.search(r"page\.line\.me/@?([A-Za-z0-9._-]+)", plain)
    if m:
        k, v = classify(m.group(1))
        row["outcome"] = "add-friend" if k == "oa" else "personal"
        row["basicId"] = v if k == "oa" else None
        row["handle_resolved"] = v
    elif "wongnai.com/delivery/businesses/" in plain:
        # A lin.ee link that is a LINE MAN storefront rather than an account.
        # LINE MAN and Wongnai are one company, so the merchant id is a real
        # identity for the shop — kept, and named for what it is.
        row["outcome"] = "lineman"
        row["linemanId"] = re.search(r"businesses/([A-Za-z0-9]+)", plain).group(1)
    else:
        row["outcome"] = "unresolved"
    return row


class Stop(Exception):
    pass


# ---- the pass ---------------------------------------------------------------

def key_of(kind, val):
    return f"{kind}_{val.lstrip('@~')}".lower()


def run(seeds, limit=None, pause=1.5, fresh_days=30):
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = []
    for kind, val in seeds:
        path = CACHE / f"{key_of(kind, val)}.json"
        if path.exists():
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
                age = (dt.date.today() - dt.date.fromisoformat(old["fetched"])).days
                if age <= fresh_days:
                    continue
            except Exception:                                # noqa: BLE001
                pass
        todo.append((kind, val))
    if limit:
        todo = todo[:limit]
    done = 0
    for kind, val in todo:
        try:
            row = probe(kind, val)
        except Stop as e:
            print(f"stopped: {e} — {done} done, progress saved", file=sys.stderr)
            break
        (CACHE / f"{key_of(kind, val)}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=1), encoding="utf-8")
        done += 1
        if done % 25 == 0:
            print(f"  {done}/{len(todo)}", file=sys.stderr, flush=True)
        if row["outcome"] != "personal":
            time.sleep(pause + random.random())
    return done


def repair():
    """Re-read every cached row's final URL with today's parser. No network.

    The redirect parser has been wrong twice — once on a percent-encoded @,
    once on a lin.ee that lands on a LINE MAN storefront — and both times the
    answer was already sitting in the cache under outcome "unresolved". A
    parser fix should not cost a second pass over LINE.
    """
    fixed = 0
    for path in CACHE.glob("*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            continue
        if row.get("outcome") != "unresolved" or not row.get("final"):
            continue
        plain = urllib.parse.unquote(row["final"])
        m = re.search(r"ti/p/@?([A-Za-z0-9._-]+)", plain) or \
            re.search(r"page\.line\.me/@?([A-Za-z0-9._-]+)", plain)
        if m:
            kind, val = classify(m.group(1))
            row["outcome"] = "add-friend" if kind == "oa" else "personal"
            row["basicId"] = val if kind == "oa" else None
            row["handle_resolved"] = val
        elif "wongnai.com/delivery/businesses/" in plain:
            row["outcome"] = "lineman"
            row["linemanId"] = re.search(r"businesses/([A-Za-z0-9]+)", plain).group(1)
        else:
            continue
        path.write_text(json.dumps(row, ensure_ascii=False, indent=1), encoding="utf-8")
        fixed += 1
    return fixed


def report(seeds):
    rows, counts = [], {}
    for path in sorted(CACHE.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            continue
        seen_on = seeds.get((row.get("kind"), row.get("handle")), [])
        row["seenOn"] = seen_on
        counts[row.get("outcome", "?")] = counts.get(row.get("outcome", "?"), 0) + 1
        rows.append(row)

    def inprov(r):
        p = (r.get("province") or "").lower()
        return "chiang mai" in p or "chiang rai" in p

    pages = [r for r in rows if r.get("outcome") == "page"]
    listed = [r for r in pages if not r.get("noIndex")]
    doc = {
        "_comment": "LINE Official Accounts resolved from handles the catalogue "
                    "already carried. LEADS, not records: a record needs a person "
                    "to promote it. 'website': null is the OA's own field, on the "
                    "date in 'fetched' — not a claim that no other footprint exists.",
        "generated": TODAY,
        "source": {"type": "platform", "ref": "https://page.line.me/",
                   "via": "probe_line_oa.py", "credit": "LINE Corporation",
                   "note": "public Official Account profile pages"},
        "counts": {
            "handles": len(rows),
            "outcomes": counts,
            "withProfilePage": len(pages),
            "noIndexHonoured": sum(1 for r in pages if r.get("noIndex")),
            "inProvince": sum(1 for r in listed if inprov(r)),
            "pinned": sum(1 for r in listed if r.get("lat")),
            "oaWebsiteEmpty": sum(1 for r in listed if not r.get("website")),
        },
        "accounts": sorted(listed, key=lambda r: (r.get("province") or "zz", r.get("name") or "")),
        "leadsOnly": [{"kind": r["kind"], "handle": r["handle"],
                       "basicId": r.get("basicId"), "linemanId": r.get("linemanId"),
                       "outcome": r["outcome"],
                       "seenOn": r["seenOn"]}
                      for r in rows if r.get("outcome") in ("add-friend", "personal", "dead", "lineman", "unresolved")],
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def self_test():
    assert classify("@gyk4392g") == ("oa", "@gyk4392g")
    assert classify("@ratchaphrueklab") == ("oa", "@ratchaphrueklab")
    assert classify("~nanoi")[0] == "personal"
    assert classify("40hUhkHZKr")[0] == "personal"
    got = handles_in('a https://lin.ee/Orxkq55 b https://line.me/R/ti/p/@288bwjse '
                     'c http://line.me/ti/p/~someone d https://page.line.me/%40gyk4392g')
    assert ("short", "Orxkq55") in got, got
    assert ("oa", "@288bwjse") in got, got
    assert ("personal", "~someone") in got, got
    assert ("oa", "@gyk4392g") in got, got
    assert parse_profile("<html>no next data</html>") is None
    assert key_of("oa", "@Gyk4392g") == "oa_gyk4392g"
    print("self-test ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-disk", action="store_true")
    ap.add_argument("--seed-search", action="store_true",
                    help="handles discover_line.py put in cache/line_oa_seeds.json")
    ap.add_argument("--ids", help="comma-separated handles or urls")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--pause", type=float, default=1.5)
    ap.add_argument("--fresh-days", type=int, default=30)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--repair", action="store_true",
                    help="re-parse cached rows with today\'s parser; no network")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    seeds = seed_from_disk() if (a.seed_disk or a.report) else {}
    if a.seed_search or a.report:
        for k, v in seed_from_search().items():
            seeds.setdefault(k, []).extend(v)
    if a.ids:
        for tok in a.ids.split(","):
            tok = tok.strip()
            if not tok:
                continue
            found = handles_in(tok) or [classify(tok)]
            for kind, val in found:
                if kind:
                    seeds.setdefault((kind, val), [])
    if a.repair:
        print(f"{repair()} cached rows re-parsed, no new requests", file=sys.stderr)
    if not (a.report or a.repair):
        print(f"{len(seeds)} handles seeded", file=sys.stderr)
        did = run(seeds, limit=a.limit, pause=a.pause, fresh_days=a.fresh_days)
        print(f"{did} probed", file=sys.stderr)
    doc = report(seeds)
    print(json.dumps(doc["counts"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
