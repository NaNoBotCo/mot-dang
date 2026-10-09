"""/doodles/ — the doodle repository, as pages (Nan, 2026-10-05: "All doodles, past present and future
should go here. if a doodle changes, both copies should be here … Subcategories should be subpages.
Every doodle should be shareable").

The store is data/doodles/ (written by tools/doodle_repo.py, nightly):
    ledger.jsonl    one row per version {id, v, from, e, fp, ph, c, sub, d, th, en, href, plan};
                    {id, set: {...}, at} for new words around the same drawing (no new version);
                    {id, gone: date} when a doodle leaves (a place gets a photograph, a planned day changes)
    params.jsonl    {ph, p}: what a version draws from, by hash
    engines/<h>.js  the drawing code a version was made with, by hash
    current.txt     the engine hash of the last run

emit(docs) writes docs/doodles/ from the store and assets/doodles-app/ (app.js, app.css): every page is the
same app with its category and subcategory in <body data-c data-sub>. Nothing here draws; the browser does.
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STORE = ROOT / "data" / "doodles"
APP = ROOT / "assets" / "doodles-app"
KINDS = ROOT / "data" / "curated" / "doodle_kinds.json"
CHUNK = 240
ORDER = ["front", "minisite", "scene", "cover", "place"]
BASE = "https://motdang.net/"
VOTE_URL = "https://mot-dang-claims.nanobotco.workers.dev"   # worker.js /doodle-vote
PAIRS_PER_GROUP = 120
PROPS = ROOT / "data" / "curated" / "portrait_props.json"
# what a drawn feature is called on a chip (Nan, 2026-10-05: sorts "by feature"); others take the props file's words
FEAT_NAMES = {"lights": ("เปิดดึก", "Open late"), "rooster": ("เปิดเช้า", "Opens early"), "aircon": ("แอร์", "Air-con"),
              "parking": ("ที่จอดรถ", "Parking"), "pool": ("สระว่ายน้ำ", "Pool")}


def fnv(s):
    h = 2166136261
    for ch in s.encode():
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def bucket(i):
    """Which data/v/<bucket>.json holds a doodle's versions (app.js computes the same)."""
    return "%03x" % (fnv(i) % 1024)


def load():
    """(versions {id: [row]}, gone {id: date}, params {ph: p}) from the store."""
    vers, gone, params = {}, {}, {}
    led = STORE / "ledger.jsonl"
    if led.exists():
        for line in led.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "gone" in r:
                gone[r["id"]] = r["gone"]
            elif "set" in r:   # new words around the same drawing (a planned day aired): no new version
                if r["id"] in vers:
                    vers[r["id"]][-1].update(r["set"])
            else:
                vers.setdefault(r["id"], []).append(r)
                gone.pop(r["id"], None)
    pf = STORE / "params.jsonl"
    if pf.exists():
        for line in pf.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                params[r["ph"]] = r["p"]
    return vers, gone, params


def _page(c, sub, K, title_th, title_en, rel):
    desc_th = "ภาพวาดเคลื่อนไหวของมดแดง ทุกภาพ ทุกรุ่น แต่ละภาพลิงก์กลับไปหน้าของมัน"
    desc_en = "Mot Dang's moving drawings, every one and every version of it, each linked back to its page."
    url = BASE + "doodles/" + rel
    e = html.escape
    vote = (' · votes and notes, for humans and bots: POST %s/doodle-vote {"id", "v", "like": 1|-1|0, "fav": 1|0, "accuracy": 1|-1|0, "aesthetics": 1|-1|0, "note"}'
            ' — <a href="/llms.txt">llms.txt</a>' % e(VOTE_URL)) if c == "one" else (
        ' · picks, for humans and bots: GET /doodles/data/pairs.json ([idA, vA, idB, vB]), then POST %s/doodle-pick'
        ' {"a": {"id", "v"}, "b": {"id", "v"}, "pick": "a"|"b"|"same"} — <a href="/llms.txt">llms.txt</a>' % e(VOTE_URL)) if c == "pick" else ""
    return f"""<!doctype html>
<html lang="th" translate="no" class="notranslate">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google" content="notranslate">
<title>{e(title_th)} · {e(title_en)} · Mot Dang</title>
<meta name="description" content="{e(desc_th)} · {e(desc_en)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title_th)} · {e(title_en)}">
<meta property="og:description" content="{e(desc_en)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{BASE}doodles/card.jpg">
<link rel="icon" href="/doodles/icon.svg">
<link rel="stylesheet" href="/doodles/app.css">
</head>
<body data-c="{e(c)}" data-sub="{e(sub)}">
<div class="wrap" id="app"><noscript>{e(title_th)} · {e(title_en)} — <a href="/doodles/data/meta.json">data</a>{vote}</noscript></div>
<script src="/doodles/app.js"></script>
</body>
</html>
"""


def emit(docs):
    """docs/doodles/: pages, data, engines. Returns the number of doodles."""
    vers, gone, params = load()
    if not vers:
        print("doodle repo: empty store, nothing written (run tools/doodle_repo.py)")
        return 0
    K = json.loads(KINDS.read_text())
    cur = (STORE / "current.txt").read_text().strip() if (STORE / "current.txt").exists() else ""
    out = docs / "doodles"
    if out.exists():
        shutil.rmtree(out)
    (out / "data" / "all").mkdir(parents=True)
    (out / "data" / "list").mkdir()
    (out / "data" / "v").mkdir()
    # the doodles, newest first; within a day by category, kind and name
    docs_ = []
    for i, vs in vers.items():
        last = vs[-1]
        docs_.append((i, last, vs))
    docs_.sort(key=lambda x: (_neg(x[1]["d"]), ORDER.index(x[1]["c"]) if x[1]["c"] in ORDER else 9, x[1].get("sub") or "",
                              (x[1].get("en") or x[1].get("th") or "").lower()))
    lists, idx, buckets, cats, feats = {}, [], {}, {}, {}
    rows = []
    for pos, (i, last, vs) in enumerate(docs_):
        c, sub = last["c"], last.get("sub") or ""
        row = {"id": i, "c": c, "s": sub, "d": last["d"], "t": [last.get("th", ""), last.get("en", "")], "h": last.get("href", ""),
               "n": len(vs), "v": last["v"], "f": vs[0]["from"], "u": last["from"], "p": params.get(last["ph"])}
        if last["e"] != cur:
            row["e"] = last["e"]
        if i in gone:
            row["g"] = gone[i]
        if last.get("plan"):
            row["pl"] = 1
        rows.append(row)
        lists.setdefault(c, []).append(pos)
        if sub:
            lists.setdefault(c + "~" + sub, []).append(pos)
        for f in ((row["p"] or {}).get("f") or {}).get("props") or []:   # the features drawn over a place portrait
            lists.setdefault("feat~" + f, []).append(pos)
            feats[f] = feats.get(f, 0) + 1
        idx.append([pos, last.get("th", ""), last.get("en", ""), last["d"], len(vs), c, sub, vs[-1]["from"]])
        cc = cats.setdefault(c, {"n": 0, "subs": {}})
        cc["n"] += 1
        if sub:
            cc["subs"][sub] = cc["subs"].get(sub, 0) + 1
        hist = []
        for k, r in enumerate(vs):
            hist.append({"v": r["v"], "f": r["from"], "to": vs[k + 1]["from"] if k + 1 < len(vs) else gone.get(i),
                         "e": r["e"], "fp": r["fp"], "p": params.get(r["ph"])})
        buckets.setdefault(bucket(i), {})[i] = {"c": c, "s": sub, "d": last["d"], "t": [last.get("th", ""), last.get("en", "")],
                                                 "h": last.get("href", ""), "g": gone.get(i), "pl": last.get("plan") or 0, "vs": hist}
    for n in range(0, len(rows), CHUNK):
        (out / "data" / "all" / ("%d.json" % (n // CHUNK))).write_text(json.dumps(rows[n:n + CHUNK], ensure_ascii=False, separators=(",", ":")))
    for k, v in lists.items():
        (out / "data" / "list" / (k + ".json")).write_text(json.dumps(v, separators=(",", ":")))
    for b, v in buckets.items():
        (out / "data" / "v" / (b + ".json")).write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")))
    (out / "data" / "pairs.json").write_text(json.dumps(pairs(docs_, gone), separators=(",", ":")))
    (out / "data" / "idx.json").write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
    upd = max(r["from"] for vs in vers.values() for r in vs)
    (out / "data" / "meta.json").write_text(json.dumps({"engine": cur, "chunk": CHUNK, "total": len(rows), "updated": upd,
                                                        "versions": sum(len(v) for v in vers.values()), "cats": cats,
                                                        "names": {"cats": K["cats"], "kinds": K["kinds"]}, "pay": pay_offer(),
                                                        "feats": feat_names(feats)},
                                                       ensure_ascii=False, separators=(",", ":")))
    (out / "engines").mkdir()
    used = {r["e"] for vs in vers.values() for r in vs} | {cur}
    for h in used:
        f = STORE / "engines" / (h + ".js")
        if f.exists():
            shutil.copy2(f, out / "engines" / f.name)
    for f in APP.iterdir():
        if f.is_file():
            shutil.copy2(f, out / f.name)
    # the pages: all, each category, each subcategory, one doodle
    kn = K["kinds"]
    (out / "index.html").write_text(_page("", "", K, "ดูเดิล", "Doodles", ""))
    for c, cc in cats.items():
        cn = K["cats"].get(c, {"th": c, "en": c, "path": c})
        d = out / cn["path"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(_page(c, "", K, "ดูเดิล · " + cn["th"], "Doodles · " + cn["en"], cn["path"] + "/"))
        for sub in cc["subs"]:
            sn = kn.get(sub) or ({"th": sub, "en": sub} if c != "minisite" else _site_name(rows, c, sub))
            (d / sub).mkdir(exist_ok=True)
            (d / sub / "index.html").write_text(_page(c, sub, K, "ดูเดิล · %s · %s" % (cn["th"], sn["th"]),
                                                      "Doodles · %s · %s" % (cn["en"], sn["en"]), "%s/%s/" % (cn["path"], sub)))
    (out / "pick").mkdir()
    (out / "pick" / "index.html").write_text(_page("pick", "", K, "ดูเดิล · ภาพไหนดีกว่า", "Doodles · Which is better?", "pick/"))
    (out / "d").mkdir()
    (out / "d" / "index.html").write_text(_page("one", "", K, "ดูเดิล", "Doodle", "d/"))
    return len(rows)


def feat_names(feats):
    """{feature: {n, th, en}} for the feature chips, commonest first."""
    P = json.loads(PROPS.read_text()).get("props", {}) if PROPS.exists() else {}
    out = {}
    for f, n in sorted(feats.items(), key=lambda x: -x[1]):
        th, en = FEAT_NAMES.get(f) or (P.get(f, {}).get("th", f), P.get(f, {}).get("en", f))
        out[f] = {"n": n, "th": th, "en": en}
    return out


def pay_offer():
    """What /doodles/ pays, once data/config.json names a `doodlePayRail` (tools/doodle_score.py); else None."""
    cfg = ROOT / "data" / "config.json"
    rail = json.loads(cfg.read_text()).get("doodlePayRail") if cfg.exists() else None
    if not rail:
        return None
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import doodle_score as ds
    return {"rail": rail, "pick": ds.PICK_PAY, "note": [ds.PAY_MIN, ds.PAY_MAX]}


def drawn_apart(c, sub, i, c2, sub2, i2):
    """Two doodles worth setting side by side: one category, drawn by different code (another scene,
    another set, another cover). Two places from one scene differ only in their names; nobody can
    pick between those (Nan, 2026-10-05: "I can't tell which of those 2 is better")."""
    return c == c2 and (sub or i) != (sub2 or i2)


def pairs(docs_, gone):
    """[[idA, vA, idB, vB]] for /doodles/pick/ (Nan, 2026-10-05: "choosing the better of 2 images"):
    every doodle's latest version against the one before it, then, in each category, one doodle from
    each piece of drawing code against one from another (drawn_apart), PAIRS_PER_GROUP at most a
    category, drawn the same way all day."""
    import random
    live = [(i, last, vs) for i, last, vs in docs_ if i not in gone]
    out = [[i, vs[-1]["v"], i, vs[-2]["v"]] for i, last, vs in live if len(vs) > 1]
    rnd = random.Random(max(last["from"] for _, last, _ in live) if live else "")
    code = {}
    for i, last, vs in sorted(live, key=lambda x: x[0]):
        code.setdefault(last["c"], {}).setdefault(last.get("sub") or i, []).append((i, last["v"]))
    for c in sorted(code):
        keys = sorted(code[c])
        if len(keys) < 2:
            continue
        seen = set()
        for _ in range(PAIRS_PER_GROUP * 3):
            ka, kb = rnd.sample(keys, 2)
            if tuple(sorted((ka, kb))) in seen:
                continue
            seen.add(tuple(sorted((ka, kb))))
            a, b = rnd.choice(code[c][ka]), rnd.choice(code[c][kb])
            out.append([a[0], a[1], b[0], b[1]])
            if len(seen) >= PAIRS_PER_GROUP:
                break
    return out


def _site_name(rows, c, sub):
    for r in rows:
        if r["c"] == c and r["s"] == sub:
            return {"th": r["t"][0], "en": r["t"][1]}
    return {"th": sub, "en": sub}


def _neg(d):
    """A date that sorts newest first inside an ascending sort."""
    return "".join(chr(0x7f - ord(ch)) for ch in d)
