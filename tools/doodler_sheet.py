#!/usr/bin/env python3
"""Look at the auto-doodler's scenes (assets/front/doodler*.js) as the front page's band
draws them: a still sheet (PNG, headless Chrome) or an animated gallery (HTML).

    python3 tools/doodler_sheet.py band market food:japanese moat:katam@18.5 --png out.png [--t 4200] [--w 1000]
    python3 tools/doodler_sheet.py all --html out.html

A spec is set[:variant][@hour]: hour is Bangkok time, 0-24 (sky, sun and night follow it);
'all' is every scene the files register. The gold disc stands where the clock sits.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONT = ROOT / "assets/front"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def scripts():
    names = ["skyline.js", "doodler.js"] + sorted(p.name for p in FRONT.glob("doodler-*.js"))
    return "\n".join((FRONT / n).read_text() for n in names if (FRONT / n).exists())


BAND = r"""
function PORTRAIT(cv, spec, t) {
  var F = FACTS[spec], m = /@([\d.]+)$/.exec(spec), now = Date.parse('2026-10-03T00:00:00+07:00') + (m ? +m[1] : 11) * 3600e3;
  return MDDOODLER.portrait(cv.getContext('2d'), cv.width, cv.height, t, { set: F.set, place: F.place, ridge: RIDGE, now: now });
}
function SUNALT(h) { return 90 * Math.sin((h - 6.2) / 12 * Math.PI) ; }
function BAND(cv, spec, t, phone) {
  if (FACTS[spec]) return PORTRAIT(cv, spec, t);
  var c = cv.getContext('2d'), W = cv.width, H = cv.height;
  var m = /^([a-z-]+)(?::([a-z0-9-]+))?(?:@([\d.]+))?$/.exec(spec), set = m[1], variant = m[2] || '', hour = m[3] ? +m[3] : (spec.length % 2 ? 20 : 11);
  var alt = SUNALT(hour), night = alt < -4;
  var sky = alt > 6 ? '#8fbfd6' : alt > -1 ? '#e39a7a' : alt > -8 ? '#4b3a6b' : '#1d1f3f', deep = alt > 6 ? '#5f9fc2' : alt > -1 ? '#b9617a' : alt > -8 ? '#2a2650' : '#121330';
  var g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, deep); g.addColorStop(1, sky); c.fillStyle = g; c.fillRect(0, 0, W, H);
  var x0 = phone ? 0 : W * 0.3, hz = H * (phone ? 0.6 : 0.62), deck = H * (phone ? 0.84 : 0.86);
  MDSKY.landscape(c, W, H, { horizon: hz, night: night, pm25: 20, ridge: RIDGE, phone: phone, x0: phone ? W * 0.02 : W * 0.3, x1: W * 0.98 });
  var R = phone ? Math.min(W * 0.15, H * 0.14) : Math.min(H * 0.17, W * 0.075), cx = W - R * 1.3 - 6, cy = R * 1.3 + 6;
  c.fillStyle = 'rgba(201,151,63,.9)'; c.beginPath(); c.arc(cx, cy, R * 1.1, 0, 7); c.fill();
  if (!phone) { c.fillStyle = 'rgba(7,9,13,.45)'; c.fillRect(0, 0, W * 0.28, H); }
  var now = Date.parse('2026-10-03T00:00:00+07:00') + hour * 3600e3;
  return MDDOODLER.scene(c, W, H, t, window.LASTO = { set: set, variant: variant, seed: MDDOODLER.hash(spec), label: '19:00 · ' + spec.replace(/@.*/, '').replace(':', ' · ').replace(/-/g, ' '), title: variant.replace(/-/g, ' '),
    night: night, phone: phone, deck: deck, x0: x0, x1: W, alt: alt, now: now, avoid: { cx: cx, cy: cy, r: R * 1.5 } });
}
"""


BENCHON = '--bench' in sys.argv
FACTS = {}   # spec → {set, place} for real places (p=<place id>[@hour], or --sample <scene> <n>)


def places(specs, sample):
    """Real place records for p=<id> specs and --sample, with their scene and facts."""
    if not sample and not any(s.startswith("p=") for s in specs):
        return specs
    sys.path.insert(0, str(ROOT))
    import doodles_layer
    recs = json.loads((ROOT / "docs/data/places.json").read_text())
    by = {r["id"]: r for r in recs}
    out = []
    for s in specs:
        if s.startswith("p="):
            pid = s[2:].split("@")[0]
            r = by.get(pid)
            if r:
                FACTS[s] = {"set": doodles_layer.place_scene(r) or "social", "place": doodles_layer.place_facts(r)}
            else:
                FACTS[s] = {"set": "social", "place": {"id": pid, "name": "Test"}}
        out.append(s)
    if sample:
        want, n = sample
        got = [r for r in recs if not r.get("photo") and doodles_layer.place_scene(r) == want]
        step = max(1, len(got) // max(1, n))
        for r in got[::step][:n]:
            s = "p=%s@%s" % (r["id"], [11, 20, 7, 17, 13, 22][len(out) % 6])
            FACTS[s] = {"set": want, "place": doodles_layer.place_facts(r)}
            out.append(s)
    return out


def page(specs, w, h, t, animate):
    built = ROOT / "docs/front/ridge.json"
    if built.exists():
        ridge = built.read_text()
    else:  # docs/ offloaded: the same fields front_layer writes, from the profile
        prof = json.loads((ROOT / "data/terrain_profile.json").read_text())
        ridge = json.dumps({k: prof[k] for k in ("lat", "lon_a", "lon_b", "step", "tick", "ele", "read")})
    phone = "true" if w < 640 else "false"
    def cap(s):
        if s in FACTS:
            p = FACTS[s]["place"]
            return "%s · %s · %s" % (FACTS[s]["set"], p.get("nameTh") or p.get("name") or "", s.split("@")[-1] + ":00")
        m = re.match(r"([a-z-]+)(?::([a-z0-9-]+))?(?:@([\d.]+))?$", s)
        hh = float(m.group(3)) if m.group(3) else None
        return " · ".join(x for x in (m.group(1).replace("-", " "), (m.group(2) or "").replace("-", " "),
                                       "%02d:%02d" % (int(hh), round(hh % 1 * 60)) if hh is not None else "") if x)
    cells = "".join('<figure><canvas id="c%d" width=%d height=%d></canvas><figcaption>%s</figcaption></figure>' % (i, w, h, cap(s))
                    for i, s in enumerate(specs))
    run = ("""var ON = {}; var io = new IntersectionObserver(function (es) { es.forEach(function (e) { ON[e.target.id] = e.isIntersecting; }); });
SPECS.forEach(function (s, i) { io.observe(document.getElementById('c' + i)); });
function f(t) { SPECS.forEach(function (s, i) { if (ON['c' + i]) try { BAND(document.getElementById('c' + i), s, t, PHONE); } catch (e) { console.error(s, e); } }); requestAnimationFrame(f); }
requestAnimationFrame(f);""" if animate else
           """var err = [], ms = []; SPECS.forEach(function (s, i) { try { var cv = document.getElementById('c' + i), t0 = performance.now(), n = BENCH ? 40 : 1;
  BAND(cv, s, T, PHONE); var cx = cv.getContext('2d'); cx.getImageData(0, 0, 1, 1); t0 = performance.now();
  for (var k = 0; k < n; k++) { if (FACTS[s]) PORTRAIT(cv, s, T + k * 33); else MDDOODLER.scene(cx, cv.width, cv.height, T + k * 33, LASTO); cx.getImageData(0, 0, 1, 1); } ms.push(s + ' ' + ((performance.now() - t0) / n).toFixed(1) + 'ms'); } catch (e) { err.push(s + ': ' + e.message); } });
document.title = err.join(' | ') || (BENCH ? ms.join(' · ') : 'ok');""")
    cols = 1 if animate else 2
    return ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Doodler</title>"
            "<style>body{margin:0;background:#07090d;color:#ddd;font:14px system-ui;display:grid;grid-template-columns:repeat(%d,%dpx);gap:4px;justify-content:center}"
            "figure{margin:0}canvas{display:block;max-width:100%%}figcaption{padding:2px 6px 10px}header{padding:10px 6px}</style>%s%s"
            "<script>%s</script><script>var RIDGE=%s,PHONE=%s,SPECS=%s,T=%d,BENCH=%s,FACTS=%s;%s%s</script>"
            % (cols, w, "<header>The gold disc marks where the clock sits.</header>" if animate else "", cells, scripts(), ridge, phone, json.dumps(specs), t, 'true' if BENCHON else 'false', json.dumps(FACTS, ensure_ascii=False), BAND, run))


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    w, h, t = int(opt("--w", 1000)), int(opt("--h", 440)), int(opt("--t", 4200))
    specs = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    if "--sample" in a:
        k = a.index("--sample")
        specs = [x for x in specs if x not in (a[k + 1], a[k + 2])]
        specs = places(specs, (a[k + 1], int(a[k + 2])))
    else:
        specs = places(specs, None)
    if specs == ["all"]:
        js = scripts()
        names = re.findall(r"^  ([a-z]+): function \(S\)", js, re.M) + re.findall(r"addScene\('([a-z-]+)'", js)
        specs = list(dict.fromkeys(names))
    if "--html" in a:
        out = Path(opt("--html", "doodler.html"))
        out.write_text(page(specs, w, h, t, True))
        print(out)
        return
    out = Path(opt("--png", "doodler.png"))
    src = out.with_suffix(".html")
    src.write_text(page(specs, w, h, t, False))
    rows = (len(specs) + 1) // 2
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--window-size=%d,%d" % (w * 2 + 4, rows * (h + 36)), "--screenshot=" + str(out.resolve()), src.resolve().as_uri()],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--dump-dom", src.resolve().as_uri()], capture_output=True, text=True)
    m = re.search(r"<title>(.*?)</title>", r.stdout)
    print(m.group(1) if m else "no title", "→", out)


if __name__ == "__main__":
    main(sys.argv[1:])
