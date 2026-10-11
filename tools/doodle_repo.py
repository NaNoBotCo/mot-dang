#!/usr/bin/env python3
"""Record every doodle into the repository (data/doodles/, read by doodlerepo_layer.py → /doodles/).

Nan, 2026-10-05: "All doodles, past present and future should go here. if a doodle changes, both
copies should be here."

A doodle is its drawing code plus what it draws from. Each run:
  1. bundles the drawing code (skyline.js, doodler*.js, doodles.js, replay.js, assets/doodles/repo.js)
     into data/doodles/engines/<hash>.js — kept for good, so an old version replays with its own code;
  2. gathers today's doodles: the front page's aired and planned days, every place portrait
     (docs/data/doodles/, written by the build), the minisites' drawings, every scene, the covers;
  3. draws each one small, twice, in headless Chrome (MDREPO.fp): a new fingerprint or new
     inputs make a new version; the old one stays, with its engine;
  4. notes doodles that left (a place got a photograph, a planned day changed) — kept, marked gone.

    python3 tools/doodle_repo.py            record, then write docs/doodles/
    python3 tools/doodle_repo.py --dry      count what would change, write nothing
    python3 tools/doodle_repo.py --export   also pack cache/doodle-archive/motdang-doodles-<date>.tar.gz
"""
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import doodles_layer  # noqa: E402
import doodlerepo_layer  # noqa: E402

STORE = doodlerepo_layer.STORE
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DOCS = ROOT / "docs"
BATCH = 8000


def today():
    return (dt.datetime.utcnow() + dt.timedelta(hours=7)).date().isoformat()


def engine():
    """The bundle and its hash; written to the store the first time it is seen."""
    F = ROOT / "assets/front"
    names = ["skyline.js", "doodler.js"] + sorted(p.name for p in F.glob("doodler-*.js")) + ["doodles.js"]
    parts = [(F / n).read_text() for n in names] + [(ROOT / "assets/sites/doodles/replay.js").read_text(),
                                                   (ROOT / "assets/doodles-app/repo.js").read_text()]
    js = "/* motdang doodle engine: %s */\n" % " ".join(names) + "\n;\n".join(parts)
    h = hashlib.sha256(js.encode()).hexdigest()[:12]
    f = STORE / "engines" / (h + ".js")
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(js)
    return h, f


def ridge():
    t = json.loads((ROOT / "data/terrain_profile.json").read_text())
    return {k: t[k] for k in ("lat", "lon_a", "lon_b", "step", "tick", "ele", "read")}


def chrome(eng, body, timeout=600):
    """Run body (JS that fills OUT) after the engine in headless Chrome; returns OUT's lines."""
    src = ROOT / "cache" / "doodle_repo_run.html"
    src.parent.mkdir(exist_ok=True)
    src.write_text('<!doctype html><meta charset=utf-8><body><script src="%s"></script><script>var OUT=[];%s\n'
                   'var p=document.createElement("pre");p.id="o";p.textContent=OUT.join("\\n");document.body.appendChild(p)</script>'
                   % (eng.resolve().as_uri(), body))
    r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--allow-file-access-from-files", "--dump-dom", src.resolve().as_uri()],
                       capture_output=True, text=True, timeout=timeout)
    m = re.search(r'<pre id="o">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("chrome returned nothing: " + r.stderr[-500:])
    import html as H
    return [x for x in H.unescape(m.group(1)).split("\n") if x]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def gather(eng, day):
    """{id: {c, sub, d, th, en, href, plan, p}} — every doodle there is today."""
    K = json.loads(doodlerepo_layer.KINDS.read_text())["kinds"]
    out = {}
    # the front page: what aired (data/curated/doodle_aired.json), and the days planned ahead
    led = json.loads((ROOT / "data/curated/doodle_aired.json").read_text())["aired"]
    plan = []
    dj = DOCS / "front/doodle.json"
    if dj.exists():
        evs = {}
        ef = DOCS / "front/events.json"
        for e in (json.loads(ef.read_text()).get("events", []) if ef.exists() else []):
            evs.setdefault(e["k"], e)
        for d in json.loads(dj.read_text()).get("days", []):
            if d["date"] <= day:
                continue
            for o in d.get("opts") or [d]:
                e = evs.get(o.get("k"), {})
                plan.append(dict({"date": d["date"], "k": o.get("k", ""), "set": o.get("set") or d.get("kind", ""), "variant": o.get("variant", ""),
                                  "version": o.get("version", 1)}, **{k: e[k] for k in ("t", "s", "v", "la", "lo") if e.get(k) not in (None, "")}))
    for r in led + plan:
        if not r.get("set"):
            continue
        i = "f-%s-%s%s" % (r["date"], r["set"], "-" + r["variant"] if r.get("variant") else "")
        p = {k: r[k] for k in ("date", "k", "set", "variant", "t", "s", "v", "la", "lo") if r.get(k) not in (None, "")}
        out[i] = {"c": "front", "sub": r["set"], "d": r["date"], "th": r.get("t") or r["k"], "en": r.get("t") or r["k"],
                  "href": "/#ev=" + r["k"], "plan": r["date"] > day, "p": p}
    # place portraits, as the last build drew them
    gd = DOCS / "data/doodles"
    for f in sorted(gd.glob("*-*.json")):
        scene = f.name.rsplit("-", 1)[0]
        for x in json.loads(f.read_text()):
            i = "p-" + slug(x["id"])
            nm = x.get("nameTh") or x.get("name") or ""
            out[i] = {"c": "place", "sub": scene, "d": day, "th": nm, "en": x.get("nameEn") or x.get("nameRom") or x.get("name") or nm,
                      "href": "/" + x["u"], "p": {"set": scene, "f": x}}
    # the minisites' drawings
    for m in doodles_layer._minisites():
        i = "m-%s-%s-%s" % (m["site"], m["lib"], m["k"])
        out[i] = {"c": "minisite", "sub": m["site"], "d": m.get("date") or day, "th": m["th"], "en": m["en"], "href": m["href"],
                  "p": {"lib": m["lib"], "k": m["k"], "alt": [m.get("alt_th", ""), m.get("alt_en", "")]}}
    # covers: doodles.js drawings that are not a minisite's
    for k, v in doodles_layer.kinds().items():
        if v.get("from"):
            continue
        n = K.get(k, {"th": k, "en": k})
        out["c-" + k] = {"c": "cover", "sub": "", "d": day, "th": n["th"], "en": n["en"], "href": "", "p": {"k": k, "alt": [v.get("th", ""), v.get("en", "")]}}
    # scenes: every set the engine draws that is not a place portrait, and the variants it lists
    places = {f.name.rsplit("-", 1)[0] for f in gd.glob("*-*.json")}
    lines = chrome(eng, "var D=MDDOODLER;D.sets().forEach(function(s){OUT.push(s)});"
                        "(window.MDDOODLER_FOOD||{cuisines:[]}).cuisines.forEach(function(k){OUT.push('food:'+k)});"
                        "(window.MDDOODLER_DANCE||{kinds:[]}).kinds.forEach(function(k){OUT.push('dance:'+k)});"
                        "((window.MDDOODLER_MOAT||{places:[]}).places).forEach(function(p){OUT.push('moat:'+p.k)});")
    for s in lines:
        st, _, va = s.partition(":")
        if st in places or st in ("portrait",):
            continue
        n = K.get(st, {"th": st, "en": st})
        i = "s-" + st + ("-" + va if va else "")
        out[i] = {"c": "scene", "sub": st, "d": day, "th": n["th"] + (" · " + va.replace("-", " ") if va else ""),
                  "en": n["en"] + (" · " + va.replace("-", " ") if va else ""), "href": "", "p": {"set": st, "variant": va}}
    return out


def phash(p):
    return hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def prints(eng, docs_):
    """{id: fingerprint}, BATCH at a time. A batch that hangs (a drawing that never finishes) is halved
    until the doodle that hangs is found; it is marked 'err' and kept out of that run."""
    rid = json.dumps(ridge())
    got = {}

    def run(ids):
        part = [{"id": i, "c": docs_[i]["c"], "p": docs_[i]["p"]} for i in ids]
        try:
            lines = chrome(eng, "var R=%s,RIDGE=%s;R.forEach(function(r){var f;try{f=MDREPO.fp(r,RIDGE)}catch(e){f='err'}OUT.push(r.id+' '+f)});"
                           % (json.dumps(part, ensure_ascii=False), rid), timeout=60 + len(ids) // 40)
        except subprocess.TimeoutExpired:
            subprocess.run(["pkill", "-f", "doodle_repo_run.html"])
            if len(ids) == 1:
                got[ids[0]] = "err"
                print("  hangs:", ids[0], flush=True)
                return
            run(ids[:len(ids) // 2])
            run(ids[len(ids) // 2:])
            return
        for line in lines:
            i, _, f = line.rpartition(" ")
            got[i] = f

    ids = sorted(docs_)
    for n in range(0, len(ids), BATCH):
        run(ids[n:n + BATCH])
        print("  drawn %d / %d" % (min(n + BATCH, len(ids)), len(ids)), flush=True)
    return got


def main(a):
    day = today()
    h, eng = engine()
    print("engine", h)
    now = gather(eng, day)
    print("doodles today:", len(now))
    fps = prints(eng, now)
    bad = [i for i, f in fps.items() if f == "err"]
    if bad:
        print("  %d could not be drawn (kept out this run): %s" % (len(bad), ", ".join(bad[:8])))
    vers, gone, params = doodlerepo_layer.load()
    new_rows, new_params, gone_rows, meta_rows = [], {}, [], []
    for i, d in now.items():
        f = fps.get(i)
        if not f or f == "err":
            continue
        ph = phash(d["p"])
        last = (vers.get(i) or [None])[-1]
        meta = {k: d[k] for k in ("c", "sub", "d", "th", "en", "href")}
        if d.get("plan"):
            meta["plan"] = True
        if last and last["fp"] == f and last["ph"] == ph and i not in gone:
            # the same drawing: at most new words around it (a planned day aired), noted without a new version
            if any(last.get(k) != v for k, v in meta.items()) or bool(last.get("plan")) != bool(d.get("plan")):
                meta_rows.append({"id": i, "set": dict(meta, plan=bool(d.get("plan"))), "at": day})
            continue
        if ph not in params and ph not in new_params:
            new_params[ph] = d["p"]
        new_rows.append(dict({"id": i, "v": (last["v"] + 1) if last else 1, "from": day, "e": h, "fp": f, "ph": ph}, **meta))
    for i in vers:
        if i not in now and i not in gone:
            gone_rows.append({"id": i, "gone": day})
    changed = sum(1 for r in new_rows if r["v"] > 1)
    print("new doodles %d · new versions %d · relabelled %d · gone %d" % (len(new_rows) - changed, changed, len(meta_rows), len(gone_rows)))
    if "--dry" in a:
        return
    STORE.mkdir(parents=True, exist_ok=True)
    with open(STORE / "params.jsonl", "a") as fh:
        for ph, p in new_params.items():
            fh.write(json.dumps({"ph": ph, "p": p}, ensure_ascii=False, separators=(",", ":")) + "\n")
    with open(STORE / "ledger.jsonl", "a") as fh:
        for r in new_rows + meta_rows + gone_rows:
            fh.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    (STORE / "current.txt").write_text(h + "\n")
    print("pages:", doodlerepo_layer.emit(DOCS), "doodles → docs/doodles/")
    if "--export" in a:
        export(day)


def export(day):
    """The repository and its pages in one file, for an archive (Internet Archive, a drive)."""
    out = ROOT / "cache" / "doodle-archive"
    out.mkdir(parents=True, exist_ok=True)
    f = out / ("motdang-doodles-%s.tar.gz" % day)
    with tarfile.open(f, "w:gz") as t:
        t.add(STORE, arcname="motdang-doodles/store")
        t.add(DOCS / "doodles", arcname="motdang-doodles/site/doodles")
        for n in ("skyline.js", "doodler.js", "doodles.js"):
            t.add(ROOT / "assets/front" / n, arcname="motdang-doodles/site/front/" + n)
    print("export:", f, "%.1f MB" % (f.stat().st_size / 1e6))


if __name__ == "__main__":
    main(sys.argv[1:])
