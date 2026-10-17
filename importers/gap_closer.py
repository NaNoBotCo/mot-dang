#!/usr/bin/env python3
"""gap_closer.py — the nightly closer for "not on motdang" gaps (C125, answered (a)
by Nan 2026-10-13).

Ask AI files every web-only place it recommends and the directory lacks into the
white-label-ai D1 table `site_gaps` (kind = place, status = new). This is the
deterministic half of closing them. The Claude half (the nightly task
`motdang-gap-closer`) does the reading: for each candidate it finds two of the
place's own sources -- its site, its Facebook page, a map listing -- and writes
what each says about the name and the location.

    export [--limit N]     candidates not yet checked tonight, to
                           _incoming/gap-closer/<date>/candidates.json
    apply VERDICTS.json    check each verdict against the rule below; a pass
                           becomes a record in data/curated/additions-*.json,
                           credited "from the web, <date>"; every candidate gets
                           a row in data/gap_closer.tsv; the D1 row is marked
                           taken (placed, or already in the directory) or, after
                           three misses, rejected
    status                 the ledger in numbers
    short-list             write _incoming/gap-closer/short-list.txt (what has
                           not passed, with the reason)

THE RULE a pass has to meet (tested here, not trusted from the verdict):
  1. two sources, on two different hosts, each of kind site | facebook | map
     (a blog, a directory or an article is a lead, not a source of its own);
  2. each source states the place's name, and the two names agree with each
     other and with the record's;
  3. each source states a location, and the two agree: coordinates within
     150 m, or the same house number and street words in the address;
  4. the pin falls inside Chiang Mai or Chiang Rai province's box;
  5. no place of that name within 200 m is in the directory already (if one is,
     the candidate is closed as "already listed", nothing is added).

A closed shop can be listed for a night or two before a reader taps "not quite"
(Nan's stated worst case for (a)). Nothing here builds or publishes: the next
walk round imports the additions file like any other.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import unicodedata
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = datetime.date.today().isoformat()
WLAI = pathlib.Path.home() / "Developer" / "claude code projects" / "white-label-ai"
OUT = ROOT / "_incoming" / "gap-closer"
LEDGER = ROOT / "data" / "gap_closer.tsv"
ADD = {"cm": ROOT / "data" / "curated" / "additions-chiang-mai.json",
       "cr": ROOT / "data" / "curated" / "additions-chiang-rai.json"}
CANON = {"cm": ROOT / "data" / "canonical" / "cm.json",
         "cr": ROOT / "data" / "canonical" / "cr.json"}
BOX = {"cm": (17.2, 20.1, 97.3, 100.4), "cr": (19.05, 20.5, 99.0, 100.7)}
OWN_KINDS = {"site", "facebook", "map"}
AGREE_M = 150
DUP_M = 200
RETRY_DAYS = 14
GIVE_UP_AFTER = 3
HEAD = ["date", "gap_id", "name", "verdict", "detail"]


# ---------------------------------------------------------------- small helpers

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return re.sub(r"[\W_]+", " ", s).strip()


def tokens(s: str) -> set[str]:
    return {t for t in norm(s).split() if len(t) > 1}


def names_agree(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if (na in nb or nb in na) and min(len(na), len(nb)) >= 5:
        return True
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return False
    both = len(ta & tb)
    return both >= 2 and both / min(len(ta), len(tb)) >= 0.6


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    dy = (a[0] - b[0]) * 111_320
    dx = (a[1] - b[1]) * 111_320 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def host(url: str) -> str:
    h = (urllib.parse.urlparse(url).hostname or "").lower()
    h = re.sub(r"^(www|m|mobile|th-th|web)\.", "", h)
    if h in ("fb.com", "fb.me"):
        return "facebook.com"
    return h


def point(src: dict) -> tuple[float, float] | None:
    try:
        la, ln = float(src["lat"]), float(src["lng"])
    except (KeyError, TypeError, ValueError):
        return None
    return (la, ln) if -90 <= la <= 90 and -180 <= ln <= 180 else None


def address_key(s: str) -> tuple[set[str], set[str]]:
    toks = norm(s).split()
    digits = {t for t in toks if re.fullmatch(r"\d+(?:\d+)*", t)}
    words = {t for t in toks if not t.isdigit() and len(t) > 2}
    return digits, words


def locations_agree(a: dict, b: dict) -> tuple[bool, str]:
    pa, pb = point(a), point(b)
    if pa and pb:
        d = metres(pa, pb)
        return d <= AGREE_M, f"{d:.0f} m apart"
    da, wa = address_key(a.get("address", ""))
    db, wb = address_key(b.get("address", ""))
    if da and db and (da & db) and len(wa & wb) >= 2:
        return True, "same house number and street words"
    return False, "no two comparable locations"


def slug(s: str) -> str:
    a = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", a.lower()).strip("-")[:40]


# ---------------------------------------------------------------- D1

def d1(sql: str) -> list[dict]:
    keys = pathlib.Path.home() / ".config" / "nanobotco" / "keys.json"
    env = dict(os.environ, CLOUDFLARE_API_TOKEN=json.load(open(keys))["cloudflare"]["api_token"])
    out = subprocess.run(["npx", "wrangler", "d1", "execute", "white-label-ai", "--remote", "--json",
                          "--command", sql], cwd=WLAI, env=env, capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr[-500:])
    return json.loads(out.stdout)[0]["results"]


# ---------------------------------------------------------------- ledger

def ledger_rows() -> list[dict]:
    if not LEDGER.exists():
        return []
    lines = LEDGER.read_text(encoding="utf-8").splitlines()[1:]
    rows = []
    for ln in lines:
        p = ln.split("\t")
        if len(p) >= 5:
            rows.append(dict(zip(HEAD, p[:5])))
    return rows


def ledger_add(rows: list[list[str]]) -> None:
    new = not LEDGER.exists()
    with open(LEDGER, "a", encoding="utf-8") as f:
        if new:
            f.write("\t".join(HEAD) + "\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")


# ---------------------------------------------------------------- export

def cmd_export(limit: int) -> None:
    rows = d1("SELECT id, name, category, area, url, evidence, question, seen FROM site_gaps "
              "WHERE status = 'new' AND site = 'motdang' AND kind = 'place' ORDER BY seen DESC, ts")
    led = ledger_rows()
    cutoff = datetime.date.today() - datetime.timedelta(days=RETRY_DAYS)
    last: dict[str, str] = {}
    for r in led:
        last[r["gap_id"]] = max(last.get(r["gap_id"], ""), r["date"])
    todo = [r for r in rows
            if not last.get(str(r["id"])) or datetime.date.fromisoformat(last[str(r["id"])]) <= cutoff][:limit]
    folder = OUT / TODAY
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "candidates.json").write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} waiting, {len(todo)} to check tonight -> {folder / 'candidates.json'}")


# ---------------------------------------------------------------- directory lookup

_canon_cache: dict[str, list] = {}


def listed_near(prov: str, name: str, pt: tuple[float, float] | None) -> str | None:
    """Id of a place already in the directory with this name near this pin."""
    if prov not in _canon_cache:
        recs = []
        p = CANON[prov]
        if p.exists():
            for r in json.loads(p.read_text(encoding="utf-8")):
                if r.get("lat") is not None and r.get("lng") is not None:
                    recs.append((r["id"], [r.get("name"), r.get("nameTh"), r.get("nameEn")],
                                 (r["lat"], r["lng"])))
        _canon_cache[prov] = recs
    for rid, names, at in _canon_cache[prov]:
        if pt is not None and metres(pt, at) > DUP_M:
            continue
        if pt is None:
            continue
        if any(n and names_agree(name, n) for n in names):
            return rid
    return None


# ---------------------------------------------------------------- the check

def valid_cats(cat: list, sub: list) -> str | None:
    cats = json.loads((ROOT / "data" / "categories.json").read_text(encoding="utf-8"))["categories"]
    keys = {c["key"]: {ch["key"] for ch in c.get("children", [])} for c in cats}
    if not cat or any(c not in keys for c in cat):
        return f"cat {cat!r} is not on the shelf tree"
    allowed = set().union(*(keys[c] for c in cat))
    if any(s not in allowed for s in (sub or [])):
        return f"sub {sub!r} is not under {cat!r}"
    return None


def check(v: dict) -> tuple[bool, str, dict | None]:
    """(passes, why, record)."""
    rec = v.get("record") or {}
    srcs = v.get("sources") or []
    prov = rec.get("province")
    if prov not in ADD:
        return False, f"province {prov!r} is not cm or cr", None
    if len(srcs) < 2:
        return False, "fewer than two sources", None
    own = [s for s in srcs if s.get("kind") in OWN_KINDS and s.get("ref", "").startswith("http")]
    hosts = {host(s["ref"]) for s in own}
    if len(own) < 2 or len(hosts) < 2:
        return False, "needs two sources of its own (site, facebook, map) on two hosts", None
    a, b = own[0], own[1]
    if host(a["ref"]) == host(b["ref"]):
        a, b = own[0], next(s for s in own if host(s["ref"]) != host(own[0]["ref"]))
    name = rec.get("name") or rec.get("nameEn") or rec.get("nameTh") or ""
    if not (names_agree(a.get("name", ""), b.get("name", ""))
            and names_agree(a.get("name", ""), name) and names_agree(b.get("name", ""), name)):
        return False, f"names disagree: {a.get('name')!r} / {b.get('name')!r} / {name!r}", None
    ok, how = locations_agree(a, b)
    if not ok:
        return False, f"locations disagree ({how})", None
    pts = [p for p in (point(a), point(b)) if p]
    pin = None
    if pts:
        pin = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        lo = BOX[prov]
        if not (lo[0] <= pin[0] <= lo[1] and lo[2] <= pin[1] <= lo[3]):
            return False, f"pin {pin[0]:.4f},{pin[1]:.4f} is outside province {prov}", None
    why = valid_cats(rec.get("cat") or [], rec.get("sub") or [])
    if why:
        return False, why, None
    have = listed_near(prov, name, pin)
    if have:
        return False, f"already listed as {have}", {"_listed": have}
    rid = f"{prov}-web-{hashlib.sha1((norm(name) + str(pin)).encode()).hexdigest()[:8]}-{slug(rec.get('nameEn') or name) or 'place'}"
    credit = f"from the web, {TODAY}"
    sources = [{"type": "web", "ref": s["ref"], "fetched": s.get("fetched") or TODAY, "via": "gap-closer",
                "credit": credit, "note": (s.get("note") or f"{s['kind']}: name and location").strip()}
               for s in (a, b)]
    attrs = {k: rec[k] for k in ("kind", "kindTh") if rec.get(k)}
    attrs["pinNote"] = (f"two sources agree ({how}): {host(a['ref'])} and {host(b['ref'])}, read {TODAY}"
                        if pin else f"no pin; two sources agree on the address, read {TODAY}")
    out = {
        "id": rid, "province": prov, "cat": rec["cat"], "sub": rec.get("sub") or [],
        "name": name, "nameTh": rec.get("nameTh"), "nameEn": rec.get("nameEn"),
        "lat": round(pin[0], 6) if pin else None, "lng": round(pin[1], 6) if pin else None,
        "geoPrecision": "approx" if pin else "needs-pin",
        "address": rec.get("address") or a.get("address") or b.get("address"),
        "phone": rec.get("phone"), "website": rec.get("website"), "hours": rec.get("hours"),
        "attrs": attrs, "featured": False, "landmark": False, "sources": sources,
        "confidence": "third-party", "updatedAt": TODAY,
    }
    return True, how, out


# ---------------------------------------------------------------- apply

def cmd_apply(path: str, dry: bool, no_d1: bool) -> None:
    verdicts = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if isinstance(verdicts, dict):
        verdicts = verdicts.get("verdicts", [])
    cands = {}
    cp = OUT / TODAY / "candidates.json"
    if cp.exists():
        cands = {str(c["id"]): c for c in json.loads(cp.read_text(encoding="utf-8"))}
    added: dict[str, list] = {"cm": [], "cr": []}
    seen_ids = {r["id"] for p in ADD.values() for r in json.loads(p.read_text(encoding="utf-8"))}
    rows, taken, rejected = [], [], []
    misses = {}
    for r in ledger_rows():
        if r["verdict"] in ("miss",):
            misses[r["gap_id"]] = misses.get(r["gap_id"], 0) + 1
    for v in verdicts:
        gid = str(v.get("gap_id"))
        name = (cands.get(gid) or {}).get("name") or (v.get("record") or {}).get("name") or ""
        if v.get("verdict") != "pass":
            n = misses.get(gid, 0) + 1
            rows.append([TODAY, gid, name, "miss", (v.get("reason") or "no reason given")[:200]])
            (rejected if n >= GIVE_UP_AFTER else []).append(gid)
            continue
        ok, why, rec = check(v)
        if ok and rec["id"] in seen_ids:
            ok, why = False, f"id {rec['id']} already in the additions"
        if ok:
            seen_ids.add(rec["id"])
            added[rec["province"]].append(rec)
            rows.append([TODAY, gid, name, "placed", rec["id"]])
            taken.append(gid)
        elif rec and rec.get("_listed"):
            rows.append([TODAY, gid, name, "listed", rec["_listed"]])
            taken.append(gid)
        else:
            n = misses.get(gid, 0) + 1
            rows.append([TODAY, gid, name, "miss", why[:200]])
            if n >= GIVE_UP_AFTER:
                rejected.append(gid)
    for prov, recs in added.items():
        if not recs:
            continue
        data = json.loads(ADD[prov].read_text(encoding="utf-8"))
        data += recs
        if not dry:
            ADD[prov].write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r in rows:
        print("  " + " | ".join(r[1:]))
    if dry:
        print("dry run: nothing written")
        return
    ledger_add(rows)
    if not no_d1:
        if taken:
            d1(f"UPDATE site_gaps SET status = 'taken' WHERE id IN ({','.join(str(int(i)) for i in taken)})")
        if rejected:
            d1(f"UPDATE site_gaps SET status = 'rejected' WHERE id IN ({','.join(str(int(i)) for i in rejected)})")
    cmd_short_list()
    print(f"placed {sum(len(x) for x in added.values())}, already listed {sum(1 for r in rows if r[3]=='listed')}, "
          f"not passed {sum(1 for r in rows if r[3]=='miss')}")


def cmd_short_list() -> None:
    rows = ledger_rows()
    done = {r["gap_id"] for r in rows if r["verdict"] in ("placed", "listed")}
    last = {}
    for r in rows:
        if r["gap_id"] not in done:
            last[r["gap_id"]] = r
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"Gaps that have not passed the two-source check (as of {TODAY}). {len(last)} item(s).", ""]
    for r in sorted(last.values(), key=lambda r: r["date"], reverse=True):
        lines.append(f"{r['name']}  [gap {r['gap_id']}, last tried {r['date']}]\n  {r['detail']}\n")
    (OUT / "short-list.txt").write_text("\n".join(lines), encoding="utf-8")


def cmd_status() -> None:
    rows = ledger_rows()
    c: dict[str, int] = {}
    for r in rows:
        c[r["verdict"]] = c.get(r["verdict"], 0) + 1
    print(f"ledger rows {len(rows)}: {c}")
    try:
        left = d1("SELECT count(*) n FROM site_gaps WHERE status='new' AND site='motdang' AND kind='place'")[0]["n"]
        print(f"waiting in D1: {left}")
    except Exception as e:  # noqa: BLE001
        print(f"D1 not reachable: {e}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["export", "apply", "status", "short-list"])
    ap.add_argument("verdicts", nargs="?")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-d1", action="store_true")
    a = ap.parse_args()
    if a.command == "export":
        cmd_export(a.limit)
    elif a.command == "apply":
        if not a.verdicts:
            sys.exit("apply needs a verdicts file")
        cmd_apply(a.verdicts, a.dry_run, a.no_d1)
    elif a.command == "status":
        cmd_status()
    else:
        cmd_short_list()


if __name__ == "__main__":
    main()
