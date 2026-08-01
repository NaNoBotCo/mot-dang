#!/usr/bin/env python3
"""Photograph today's sky off Nan's own working instruments, once a day.

Mot Dang had three different home-made drawings of the moon and none of them
was the real thing. The worst of it was stated on the page in the site's own
words — "มุมโดยประมาณ ไม่ใช้เอฟีเมอริส · angle approximated, no ephemeris here".
Meanwhile three finished instruments already exist and are right:

    wichaa.net/moon      the moon complication  — one dial, two moons
    wichaa.net/jovilabe  the jovilabe           — Jupiter's four moons, geared
    wichaa.net/redspot   the Red Spot dial      — the same four, from inside

So stop drawing and take a photograph. Each shot links back to the instrument
it came from, which is the point: the tile is a doorway, not a copy.

HOW THE CROP IS DONE, and why not with pixel coordinates. The page is fetched,
a `<base>` is injected so its own CSS and scripts still load from wichaa, and a
stylesheet is added that hides everything except one named element and pins it
to the corner of the window. Chrome then photographs a window exactly that
size. The crop is therefore defined by a CSS selector, not by a measured box,
so it survives the header growing a row — which it does, every time she ships
a new tool.

    python3 importers/make_widget_shots.py           # refresh anything stale
    python3 importers/make_widget_shots.py --force   # refresh all of them
    python3 importers/make_widget_shots.py --list    # show what is on file

Writes assets/widgets/<id>.png and data/widget_shots.json.
Needs Chrome (same dependency as make_og_cards.py) and Pillow, and is the ONLY
part of this build that looks at the network at render time — build.py reads
the JSON and never fetches anything.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "widgets")
OUT_JSON = os.path.join(ROOT, "data", "widget_shots.json")
UA = "MotDangWidgetShots/1.0 (+https://motdang.net; photographing our own instruments)"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

# id, page, the element to photograph, the square to photograph it at, and what
# the tile should say. `sel` is the crop: change it here, not in build.py.
WIDGETS = [
    {"id": "moon", "url": "https://wichaa.net/moon/", "sel": ".dialbox", "size": 760,
     "th": "ข้างขึ้นข้างแรม", "en": "The moon complication",
     "cap_th": "หน้าปัดจริงจาก wichaa.net/moon", "cap_en": "the working dial at wichaa.net/moon"},
    {"id": "jovilabe", "url": "https://wichaa.net/jovilabe/", "sel": "svg.dial", "size": 760,
     "th": "ดวงจันทร์ของพฤหัสบดี", "en": "Jupiter's four moons",
     "cap_th": "โจวิลาบจาก wichaa.net/jovilabe", "cap_en": "the jovilabe at wichaa.net/jovilabe"},
    {"id": "redspot", "url": "https://wichaa.net/redspot/", "sel": "figure", "size": 760,
     "th": "มองจากจุดแดงใหญ่", "en": "From inside the Great Red Spot",
     "cap_th": "หน้าปัดจุดแดงจาก wichaa.net/redspot", "cap_en": "the Red Spot dial at wichaa.net/redspot"},
]

# Mark ONE element and style the mark, rather than styling the selector.
# Styling `.instrument` directly pinned every match to the corner at once and
# the jovilabe shot came back as a stack of its stat cards and sub-dials with
# the geared dial nowhere in it. A selector that matches twice is normal on a
# real page; a crop that matches twice is a wrong picture.
ISOLATE = """
<script id="md-shot-js">
(function(){function mark(){
  var el=document.querySelector(%(sel_js)s);
  if(!el)return;
  document.querySelectorAll('[data-mdshot]').forEach(function(o){o.removeAttribute('data-mdshot')});
  el.setAttribute('data-mdshot','1');}
mark();
document.addEventListener('DOMContentLoaded',mark);
window.addEventListener('load',mark);
setTimeout(mark,1500); setTimeout(mark,3500);})();
</script>
<style id="md-shot">
html,body{margin:0!important;padding:0!important;overflow:hidden!important;
  width:%(size)dpx!important;height:%(size)dpx!important;background:#fff!important}
body *{visibility:hidden!important}
[data-mdshot],[data-mdshot] *{visibility:visible!important}
[data-mdshot]{position:fixed!important;inset:0!important;margin:0!important;padding:0!important;
  width:%(size)dpx!important;height:%(size)dpx!important;max-width:none!important;
  max-height:none!important;border-radius:0!important;box-shadow:none!important;
  z-index:2147483647!important;display:flex!important;align-items:center!important;
  justify-content:center!important}
[data-mdshot]>svg,svg[data-mdshot]{width:100%%!important;height:100%%!important;display:block!important}
/* Anything that floats over the page — the support button, the share bar —
   is chrome, not instrument. */
.sharebar,.supportfab,[class*="support"],[class*="share"]{display:none!important}
</style>
"""


def chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    raise SystemExit("No Chrome found. Same dependency as make_og_cards.py — "
                     "install Chrome, or skip this importer and build.py will "
                     "simply not render the sky tiles.")


def looks_drawn(path, sel_desc):
    """Refuse a blank photograph.

    A screenshot pipeline fails silently by default: the page did not finish,
    the selector matched nothing, and out comes a clean white square that looks
    deliberate. So count distinct colours and how much of the frame is not the
    background. Either being tiny means the shot did not take.
    """
    try:
        from PIL import Image
    except ImportError:
        print("  (Pillow missing — cannot verify %s is not blank)" % sel_desc)
        return True
    im = Image.open(path).convert("RGB")
    small = im.resize((120, 120))
    px = list(small.getdata())
    colours = len(set(px))
    bg = max(set(px), key=px.count)
    inked = sum(1 for p in px if p != bg) / float(len(px))
    ok = colours >= 24 and inked >= 0.12
    if not ok:
        print("  BLANK-LOOKING: %s — %d colours, %.0f%% inked" % (sel_desc, colours, inked * 100))
    return ok


def capture(w, binary):
    html = urllib.request.urlopen(
        urllib.request.Request(w["url"], headers={"User-Agent": UA}), timeout=45
    ).read().decode("utf-8", "replace")

    # <base> first, so the page's own stylesheets, scripts and images still
    # resolve against wichaa once the copy is sitting on a file:// path.
    inject = '<base href="%s">' % w["url"]
    if re.search(r"<head[^>]*>", html, re.I):
        html = re.sub(r"(<head[^>]*>)", r"\1" + inject, html, count=1, flags=re.I)
    else:
        html = inject + html
    block = ISOLATE % {"sel_js": json.dumps(w["sel"]), "size": w["size"]}
    html = html.replace("</body>", block + "</body>", 1)

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()
    dest = os.path.join(OUT_DIR, w["id"] + ".png")
    subprocess.run(
        [binary, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=2",          # a dial deserves a retina tile
         "--screenshot=" + dest,
         "--window-size=%d,%d" % (w["size"], w["size"]),
         "--virtual-time-budget=12000", "file://" + tmp.name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    os.unlink(tmp.name)
    if not os.path.exists(dest):
        return None
    if not looks_drawn(dest, "%s (%s)" % (w["id"], w["sel"])):
        os.unlink(dest)
        return None
    # Shrink for the web: 1520 px of dial is more than any tile shows.
    try:
        from PIL import Image
        im = Image.open(dest)
        if im.width > 900:
            im.resize((900, 900), Image.LANCZOS).save(dest, optimize=True)
    except ImportError:
        pass
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="refresh even today's shots")
    ap.add_argument("--list", action="store_true", help="print what is on file, fetch nothing")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    have = {}
    if os.path.exists(OUT_JSON):
        have = {s["id"]: s for s in json.load(open(OUT_JSON, encoding="utf-8"))["shots"]}

    if args.list:
        for w in WIDGETS:
            s = have.get(w["id"])
            print("%-10s %s" % (w["id"], (s["taken"] + "  " + s["file"]) if s else "— never taken"))
        return 0

    today = date.today().isoformat()
    binary, shots = None, []
    for w in WIDGETS:
        prev = have.get(w["id"])
        fresh = prev and prev.get("taken") == today and \
            os.path.exists(os.path.join(ROOT, "assets", prev["file"].replace("widgets/", "widgets/")))
        if fresh and not args.force:
            print("%-10s already taken today" % w["id"])
            shots.append(prev)
            continue
        binary = binary or chrome()
        print("%-10s photographing %s" % (w["id"], w["url"]))
        try:
            got = capture(w, binary)
        except Exception as e:                                   # noqa: BLE001
            print("  failed: %s" % e)
            got = None
        if not got:
            # Yesterday's sky is wrong but it is not a broken image, and it says
            # its own date on the tile. Keeping it beats a hole.
            if prev:
                print("  keeping the shot from %s" % prev["taken"])
                shots.append(prev)
            continue
        shots.append({"id": w["id"], "file": "widgets/%s.png" % w["id"], "url": w["url"],
                      "taken": today, "th": w["th"], "en": w["en"],
                      "cap_th": w["cap_th"], "cap_en": w["cap_en"]})

    json.dump({"note": ("Photographs of the live instruments at wichaa.net, taken "
                        "daily. build.py renders these and links each back to the "
                        "page it came from; it never fetches anything itself."),
               "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
               "shots": shots},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote data/widget_shots.json — %d shot(s), %d taken today"
          % (len(shots), sum(1 for s in shots if s["taken"] == today)))
    return 0 if shots else 1


if __name__ == "__main__":
    sys.exit(main())
