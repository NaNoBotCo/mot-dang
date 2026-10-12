#!/usr/bin/env python3
"""Where the site's own art misses: the wrong subject, an older form, an emoji, one subject in many hands.

Nan, 2026-10-12: "incorporate motdang proprietary art more and better … a system to keep everything
mindblowing", then "Don't want art to pile up, but I want the art to be relevant and the best form of
itself, throughout the site", and "Quality, enchantment, and consistency, not quantity."

Each check prints its finds, worst first; the nightly doodle topper takes the first one it can mend.

  band     the next days' events whose scene comes from a passing word in the description, or from
           the calendar kind alone, while the title names nothing the doodler draws
  copies   minisite drawings taken into the doodle library whose minisite changed after the taking
  emoji    emoji with a drawn i-* glyph (glyphs.EMOJI) inside JS strings, where the build's sweep
           of text nodes does not reach them
  hands    one subject drawn by more than one engine (skyline sights, map doodles, band scenes,
           doodle-map spots): the reader meets two looks for one place

    python3 tools/art_check.py                 every check, a few lines each
    python3 tools/art_check.py band --all      one check, every find
    python3 tools/art_check.py --out FILE      the same text to FILE as well
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT.parent
FRONT = ROOT / "assets/front"
sys.path.insert(0, str(ROOT))
import glyphs  # noqa: E402

LIVE_EVENTS = "https://motdang.net/front/events.json"
SHOW = 6

# the doodler with every scene file, setOf on the title and venue alone and on the whole event
NODE = r"""
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm';
const FRONT = process.argv[2], noop = () => {};
const ctx = { window: { MDSKY: { paper: noop, jag: noop, circ: noop, grain: noop, sights: { cm: [], cr: [] }, landscape: () => [] } }, console, Date, Math };
ctx.window.window = ctx.window; vm.createContext(ctx);
const files = ['doodler.js', ...fs.readdirSync(FRONT).filter(f => /^doodler-.*\.js$/.test(f)).sort()];
for (const f of files) vm.runInContext(fs.readFileSync(path.join(FRONT, f), 'utf8'), ctx, { filename: f });
const D = ctx.window.MDDOODLER, E = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')).events, out = [];
for (const e of E) {
  const full = D.setOf(e), name = D.setOf({ t: e.t, v: e.v, c: '' });
  out.push({ k: e.k, t: e.t, s: e.s, city: e.city, c: e.c, full, name });
}
process.stdout.write(JSON.stringify({ scenes: D.sets(), rows: out }));
"""


def events_file():
    """The live calendar; a copy on disk when the network is down."""
    for p in (ROOT / "docs/front/events.json", ROOT / "cache/front-events.json"):
        if p.exists() and time.time() - p.stat().st_mtime < 2 * 864e2:
            return p
    dst = ROOT / "cache/front-events.json"
    try:
        req = urllib.request.Request(LIVE_EVENTS, headers={"User-Agent": "Mozilla/5.0 (motdang art_check)", "Sec-Fetch-Mode": "navigate"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dst.parent.mkdir(exist_ok=True)
            dst.write_bytes(r.read())
    except OSError as e:
        print(f"band: calendar unreachable ({e}); using the copy on disk" if dst.exists() else f"band: no calendar ({e})")
    return dst if dst.exists() else None


def band(days=7):
    ev = events_file()
    if not ev:
        return []
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
        f.write(NODE)
    try:
        r = subprocess.run(["node", f.name, str(FRONT), str(ev)], capture_output=True, text=True, timeout=120, check=True)
    finally:
        os.unlink(f.name)
    d = json.loads(r.stdout)
    today = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 7 * 3600))
    end = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 7 * 3600 + days * 86400))
    finds, seen = [], set()
    for x in d["rows"]:
        if not (today <= x["s"][:10] <= end) or x["k"] in seen:
            continue
        seen.add(x["k"])
        if x["name"] == "social" and x["full"] != "social":
            finds.append((2, f'{x["s"][:16]} {x["city"]}  "{x["t"]}" → {x["full"]}, from its description only'))
        elif x["full"] == "social" and x["c"] not in ("social", "family"):
            finds.append((1, f'{x["s"][:16]} {x["city"]}  "{x["t"]}" → social (kind {x["c"]}): no scene names it'))
    return [f for _, f in sorted(finds, key=lambda f: -f[0])]


def copies():
    led = json.loads((ROOT / "data/curated/minisite_harvest.json").read_text())["sites"]
    finds = []
    for site, row in led.items():
        if row.get("state") != "harvested" or not row.get("date"):
            continue
        src = PROJECTS / site
        if not src.is_dir():
            continue
        taken = time.mktime(time.strptime(row["date"], "%Y-%m-%d")) + 86400
        newer = [p for p in src.rglob("*") if p.suffix in (".js", ".html", ".ts", ".mjs") and "node_modules" not in p.parts
                 and ".git" not in p.parts and p.stat().st_mtime > taken]
        if newer:
            last = time.strftime("%Y-%m-%d", time.localtime(max(p.stat().st_mtime for p in newer)))
            finds.append(f'{site}: taken {row["date"]}, minisite changed {last} ({len(newer)} files) — {row["doodle"]}')
    return finds


TYPE = set("★✕✓✦♪☰⊘✆")   # typographic marks, text in the reader's own font
EMOJI = re.compile("|".join(re.escape(e) for e in sorted(glyphs.EMOJI) if len(e) == 1 and ord(e) > 0x2000 and e not in TYPE))


def emoji():
    """Emoji inside JS: assets/**/*.js and the JS = r\"\"\" … \"\"\" blocks of the build's layers."""
    finds = []
    srcs = [p for p in ROOT.glob("*.py") if not p.name.startswith(("scratch", "glyphs"))]
    srcs += [p for p in (ROOT / "assets").rglob("*.js") if "node_modules" not in p.parts and ".min." not in p.name]
    for p in sorted(srcs):
        s = p.read_text(encoding="utf8", errors="replace")
        spans = [(m.start(), m.end()) for m in re.finditer(r'(?:JS|_JS|SCRIPT)\w*\s*=\s*r?"""(.*?)"""', s, re.S)] if p.suffix == ".py" else [(0, len(s))]
        spans += [(m.start(), m.end()) for m in re.finditer(r"<script>(.*?)</script>", s, re.S)] if p.suffix == ".py" else []
        for a, b in spans:
            for m in EMOJI.finditer(s, a, b):
                line = s.count("\n", 0, m.start()) + 1
                text = s.split("\n")[line - 1].strip()
                if text.startswith(("//", "/*", "*", "#")):
                    continue
                finds.append(f"{p.relative_to(ROOT)}:{line}  {m.group(0)} → {glyphs.EMOJI[m.group(0)]}")
    return sorted(set(finds))


def _norm(s):
    s = re.sub(r"\b(wat|the|of|chiang mai|cm|cr)\b", " ", s.lower().replace("-", " "))
    return " ".join(s.split())


def hands():
    """Subjects with a drawing in more than one engine, by normalised name."""
    have = {}

    def put(name, engine):
        n = _norm(name)
        if len(n) > 3:
            have.setdefault(n, set()).add(engine)

    sky = (FRONT / "skyline.js").read_text(encoding="utf8")
    for k, en in re.findall(r"\{ k: '([a-z0-9-]+)',[^}]*?en: '([^']+)'", sky):
        put(en, "skyline.js sight")
    for r in json.loads((ROOT / "assets/sites/map-doodles/map-doodles.json").read_text()):
        if r.get("group") == "landmark" and r.get("cc") == "TH":
            put(r["en"], "map doodle")
    for f in FRONT.glob("doodler*.js"):
        for name in re.findall(r"addScene\('([a-z0-9-]+)'", f.read_text(encoding="utf8")):
            put(name.replace("clocktower", "clock tower"), f"band scene ({f.name})")
        for gate in re.findall(r"\{ ?k: '([a-z-]+-gate)'", f.read_text(encoding="utf8")):
            put(gate, f"band scene ({f.name})")
    spots = ROOT / "assets/sites/doodle-map/data/spots.json"
    if spots.exists():
        for r in json.loads(spots.read_text()).get("spots", []):
            if r.get("look"):
                put(r["en"], "doodle map")
    # a short name inside a longer one is the same subject ("clock tower" ⊂ "chiang rai clock tower")
    keys = sorted(have, key=len)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if re.search(r"\b" + re.escape(a) + r"\b", b):
                have[b] |= have[a]
    out = [(len(v), f'{n}: {" · ".join(sorted(v))}') for n, v in have.items() if len(v) > 1]
    longest = {}
    for c, line in out:
        longest[line.split(":")[0]] = (c, line)
    return [line for _, line in sorted(longest.values(), key=lambda x: (-x[0], x[1]))]


CHECKS = {"band": band, "copies": copies, "emoji": emoji, "hands": hands}


def main(argv):
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    every = "--all" in argv
    names = [a for a in argv if a in CHECKS] or list(CHECKS)
    text = []
    for n in names:
        finds = CHECKS[n]()
        text.append(f"{n}  {len(finds)}")
        text += ["  " + f for f in (finds if every else finds[:SHOW])]
        if not every and len(finds) > SHOW:
            text.append(f"  … {len(finds) - SHOW} more: python3 tools/art_check.py {n} --all")
    print("\n".join(text))
    if out:
        Path(out).write_text(time.strftime("%Y-%m-%d %H:%M\n") + "\n".join(text) + "\n", encoding="utf8")


if __name__ == "__main__":
    main(sys.argv[1:])
