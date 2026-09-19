#!/usr/bin/env python3
"""The front page (home_layer.py), built for a frozen day and read back.

    python3 tests/test_home.py
"""
import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import home_layer  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAIL.append(name)


def main():
    day = datetime.date(2026, 9, 19)
    html = home_layer.render(day)
    payload = json.loads(re.search(r'id="md-home">(.*?)</script>', html, re.S).group(1))

    check("no search box on the front", "<input" not in html and 'role="search"' not in html)
    check("the six scenes stand", all(f'id="{s}"' in html for s in ("top", "now", "near", "day", "deep", "wander", "door")))
    check("md-where meta present and empty", '<meta name="md-where" content="">' in html)
    check("no ?v= fingerprints", "?v=" not in html)
    check("the two keys the site shares", "md-lang" in html and "md-read" in html)

    # Every picture the page names is a file on disk.
    refs = set(re.findall(r'(?:src|srcset)="(site/[^"]+)"', html))
    missing = [r for r in refs if not (ROOT / "docs" / r).exists()]
    check("every picture exists", not missing, ", ".join(missing[:5]))
    check("pictures on the page", len(refs) >= 30, str(len(refs)))

    # The frames: every scene represented, every hour of the day covered.
    pics = payload["pics"]
    check("every scene has frames", {p["s"] for p in pics} >= {"hero", "now", "near", "day", "door"})
    hero_pools = {p["p"] for p in pics if p["s"] == "hero"}
    check("hero has every hour", hero_pools >= {"morning", "day", "dusk", "night"}, str(hero_pools))
    check("an iconic set for far readers", sum(1 for p in pics if p.get("ic")) >= 20,
          str(sum(1 for p in pics if p.get("ic"))))

    # Privacy: no identifiers, and the frames the picks mark private carry no
    # coordinate. Everything else is rounded to three decimals, not finer.
    picks = json.loads((ROOT / "data" / "curated" / "hero_picks.json").read_text())
    by_slug = {r["slug"]: r for r in picks["rows"]}
    check("no photo identifiers ship", "uuid" not in json.dumps(pics))
    private = {r["slug"] for r in picks["rows"] if not r.get("pub")}
    leaked = [p["j"] for p in pics if p.get("la") is not None
              and pathlib.Path(p["j"]).stem in private]
    check("a frame marked private would carry no coordinate", not leaked, ", ".join(leaked))
    placed = sum(1 for p in pics if p.get("la") is not None)
    check("the frames are geofenced", placed == len(pics), f"{placed} of {len(pics)}")
    coarse = all(round(p["la"], 3) == p["la"] and round(p["lo"], 3) == p["lo"]
                 for p in pics if p.get("la") is not None)
    check("coordinates are coarse", coarse)

    # Aesthetic floor: Apple Photos' own score, recorded per frame.
    floor = picks["floor"]
    low = [(s, by_slug[s]["aes"]) for s in (pathlib.Path(p["j"]).stem for p in pics)
           if by_slug[s]["aes"] < floor]
    worst = min(by_slug[pathlib.Path(p["j"]).stem]["aes"] for p in pics)
    check("every frame clears the aesthetic floor", not low,
          ", ".join(f"{a} {b}" for a, b in low[:4]))
    print(f"     floor {floor} · lowest shipped {worst} · {len(pics)} frames")

    # Contrast, computed rather than eyeballed: every word sits on --plate, and
    # the worst a photograph behind it can be is pure white.
    def lum(rgb):
        f = [c / 255 for c in rgb]
        f = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in f]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]

    def ratio(fg, bg):
        a, b = sorted((lum(fg), lum(bg)), reverse=True)
        return (a + 0.05) / (b + 0.05)

    css = html[html.index("<style>"):html.index("</style>")]
    plate = re.search(r"--plate:rgba\((\d+),(\d+),(\d+),([\d.]+)\)", css)
    pr, pg, pb, pa = int(plate[1]), int(plate[2]), int(plate[3]), float(plate[4])
    worst_bg = tuple(round(pa * c + (1 - pa) * 255) for c in (pr, pg, pb))
    for name in ("ink", "dim", "gold"):
        hexv = re.search(rf"--{name}:#([0-9a-f]{{6}})", css)[1]
        fg = tuple(int(hexv[i:i + 2], 16) for i in (0, 2, 4))
        r = ratio(fg, worst_bg)
        check(f"--{name} on the plate over a white photo is AA", r >= 4.5, f"{r:.1f}:1")
        print(f"     --{name}: {r:.1f}:1")

    # Open-now grid: 7 x 96 per city, peaks at midday, quiet at 03:00.
    g = payload["open"]["cm"]
    check("open grid shape", len(g) == 7 and all(len(r) == 96 for r in g))
    check("midday busier than 3 a.m.", g[5][48] > g[5][12] * 3, f"{g[5][48]} vs {g[5][12]}")
    check("withHours per city", set(payload["withHours"]) == {"cm", "cr"})

    # Almanac: today first, 45 days or the file's end, wan phra dates ahead.
    check("almanac starts today", payload["alm"][0]["d"] == day.isoformat())
    check("almanac window", 30 <= len(payload["alm"]) <= 45, str(len(payload["alm"])))
    check("wan phra dates ahead", all(d >= day.isoformat() for d in payload["wp"]) and payload["wp"])

    # Events: a 21-day window keyed by date; titles cut, never longer than 60.
    check("21 event days", len(payload["ev"]) == 21)
    longest = max((len(i["t"]) for v in payload["ev"].values() for i in v), default=0)
    check("event titles cut", longest <= 60, str(longest))

    # The script parses.
    src = html[html.rindex("<script>") + 8:html.rindex("</script>")]
    tmp = ROOT / "cache" / "home-test.js"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(src)
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    check("script parses", r.returncode == 0, r.stderr[:200])
    tmp.unlink(missing_ok=True)

    # Style: the checker passes on the built page.
    sc = pathlib.Path.home() / ".claude" / "bin" / "stylecheck.py"
    if sc.exists():
        r = subprocess.run([sys.executable, str(sc), "--stdin"], input=html, capture_output=True, text=True)
        check("stylecheck clean", r.returncode == 0, r.stdout[:200])

    print("\n%d failed" % len(FAIL) if FAIL else "\nall green")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
