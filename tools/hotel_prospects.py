#!/usr/bin/env python3
"""Lodgings to approach for a direct deal, from files already on disk.

    python3 tools/hotel_prospects.py            # write the file, print counts
    python3 tools/hotel_prospects.py --top 30   # also print the top 30 rows

Reads (no network):
  data/canonical/{cm,cr}.json            lodging records (same set as tools/hotel_monthly.py)
  ../motdangify/out/batch.tsv            website check: status 0 or 4xx/5xx (not 401/403/429) = down
  data/curated/hotel_monthly.json        monthly price / long stay / minimum stay, from own sites
  data/curated/hotel_amenities.json      pool / shuttle / bar / food, from own sites and tags

Output: data/curated/hotel_prospects.json
  {"_meta": {...}, "rows": [{id, prov, name, name_th, phone, line, site, site_state,
                             reasons: [...], monthly_from, pool, shuttle, score}]}
reasons: dead-site (motdangify prospect; a site the page caches read without error is not dead) · long-stay (states monthly or long stay) ·
         pool · shuttle · no-site (phone or LINE, no website on record)
score: dead-site 3, long-stay 3 (+1 with a monthly price), pool 1, shuttle 1, phone or LINE 1.
"""
import argparse
import csv
import hashlib
import urllib.parse
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH = ROOT.parent / "motdangify" / "out" / "batch.tsv"
MONTHLY = ROOT / "data" / "curated" / "hotel_monthly.json"
AMEN = ROOT / "data" / "curated" / "hotel_amenities.json"
OUT = ROOT / "data" / "curated" / "hotel_prospects.json"
LODGING_SUB = re.compile(r"hotel|hostel|guest-?house|resort|homestay|serviced|apartment")
SOCIAL = re.compile(r"facebook\.com|fb\.com|fb\.me|instagram\.com|line\.me|lin\.ee|booking\.|agoda\.|airbnb|tripadvisor", re.I)


def load(p, empty):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return empty


def host_of(u):
    u = re.sub(r"^https?://", "", (u or "").strip().lower())
    h = u.split("/")[0]
    return h[4:] if h.startswith("www.") else h


CACHES = [ROOT / "cache" / "hotel_amenities" / "pages", ROOT / "cache" / "hotel_monthly" / "pages"]


def answered_today(url):
    """A page cache holds a good answer from this site (a later read than the batch can be)."""
    if not url:
        return False
    u = url.strip()
    if not re.match(r"https?://", u, re.I):
        u = "http://" + u.lstrip("/")
    u = u.split("#")[0]
    sp = urllib.parse.urlsplit(u)
    h = sp.hostname or ""
    hosts = [h, h[4:] if h.startswith("www.") else "www." + h]
    cands = {u} | {urllib.parse.urlunsplit((sc, ho, sp.path or "/", sp.query, "")) for sc in ("http", "https") for ho in hosts}
    for c in cands:
        for d in CACHES:
            f = d / (hashlib.sha1(c.encode()).hexdigest() + ".json")
            if f.exists():
                try:
                    rec = json.loads(f.read_text())
                except ValueError:
                    continue
                if not rec.get("error") and (rec.get("status") or 0) < 400 and rec.get("text"):
                    return True
    return False


def down(status):
    try:
        c = int(status or 0)
    except ValueError:
        c = 0
    return c == 0 or (400 <= c < 600 and c not in (401, 403, 429))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=0)
    args = ap.parse_args()

    sites = {}
    if BATCH.exists():
        csv.field_size_limit(1 << 30)
        with BATCH.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                st = "down" if down(row.get("status")) else "up"
                for rid in (row.get("ids") or "").split():
                    sites[rid] = (st, row.get("status") or "", row.get("error") or "")
    month = {k: v for k, v in load(MONTHLY, {}).items() if k != "_meta"}
    amen = {k: v for k, v in load(AMEN, {}).items() if k != "_meta"}

    rows = []
    n_lodging = 0
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            cat = r.get("cat") or []
            sub = r.get("sub") or []
            cat = [cat] if isinstance(cat, str) else cat
            sub = [sub] if isinstance(sub, str) else sub
            if not (any("hotel" in c for c in cat) or any(LODGING_SUB.search(s) for s in sub)):
                continue
            a = r.get("attrs") or {}
            if r.get("closed") or a.get("closed") or a.get("permanentlyClosed"):
                continue
            n_lodging += 1
            site = r.get("website") or ""
            own = site if site and not SOCIAL.search(site) else ""
            line = a.get("lineUrl") or a.get("lineId") or ""
            phone = r.get("phone") or ""
            reasons, score = [], 0
            st = sites.get(r["id"])
            if own and st and st[0] == "down" and answered_today(own):
                st = ("up", st[1], "")
            if own and st and st[0] == "down":
                reasons.append("dead-site")
                score += 3
            m = month.get(r["id"]) or {}
            mfrom = (m.get("monthly") or [{}])[0].get("thb")
            if m.get("long_stay") or mfrom:
                reasons.append("long-stay")
                score += 3 + (1 if mfrom else 0)
            am = amen.get(r["id"]) or {}
            pool = (am.get("pool") or {}).get("value") == "yes"
            sh = am.get("shuttle") or {}
            shuttle = sh.get("value") == "yes"
            if pool:
                reasons.append("pool")
                score += 1
            if shuttle:
                reasons.append("shuttle")
                score += 1
            if not own and (phone or line):
                reasons.append("no-site")
            if phone or line:
                score += 1
            if not reasons or reasons == ["no-site"]:
                continue
            rows.append({
                "id": r["id"], "prov": prov, "name": r.get("nameEn") or r.get("name"), "name_th": r.get("nameTh"),
                "phone": phone, "line": line, "site": own or site, "site_state": st[0] if st else None,
                "site_error": (st[2][:90] if st and st[0] == "down" else None) or None,
                "reasons": reasons, "monthly_from": mfrom,
                "min_stay_months": (m.get("min_stay") or {}).get("months"),
                "pool": pool or None, "shuttle": (sh.get("cost") or "yes") if shuttle else None,
                "score": score, "rank": float(r.get("rank") or 0),
            })
    rows.sort(key=lambda x: (-x["score"], -x["rank"], x["name"] or ""))
    counts = {}
    for x in rows:
        for k in x["reasons"]:
            counts[k] = counts.get(k, 0) + 1
    combo = {
        "dead-site+long-stay": sum(1 for x in rows if {"dead-site", "long-stay"} <= set(x["reasons"])),
        "dead-site+pool": sum(1 for x in rows if {"dead-site", "pool"} <= set(x["reasons"])),
        "long-stay+pool": sum(1 for x in rows if {"long-stay", "pool"} <= set(x["reasons"])),
        "dead-site with phone or LINE": sum(1 for x in rows if "dead-site" in x["reasons"] and (x["phone"] or x["line"])),
    }
    meta = {"built": dt.date.today().isoformat(), "lodging_records": n_lodging, "rows": len(rows),
            "counts": counts, "combos": combo,
            "batch_tsv_date": dt.date.fromtimestamp(BATCH.stat().st_mtime).isoformat() if BATCH.exists() else None,
            "score": "dead-site 3, long-stay 3 (+1 with a monthly price), pool 1, shuttle 1, phone or LINE 1"}
    OUT.write_text(json.dumps({"_meta": meta, "rows": rows}, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    for x in rows[:args.top]:
        print(x["score"], x["prov"], x["name"], "|", x["name_th"] or "", "|", ",".join(x["reasons"]), "|",
              x["monthly_from"] or "", "|", x["phone"], "|", x["site"])


if __name__ == "__main__":
    main()
