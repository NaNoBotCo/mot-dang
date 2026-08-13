#!/usr/bin/env python3
"""Per-place share cards — assets/og/<id>.png, 1200x630.

Why this exists: most people meet a listing inside a LINE or Facebook preview,
never on the site. One generic card on ten thousand links means every share
looks like every other share. A card carrying the place's own name, its
category and its ant rank turns each share into a small poster.

Why Chrome and not Pillow: Thai needs complex-text shaping — สระ above and
below, tone marks stacked on top of those. Pillow here has no raqm, so it
would set the marks in the wrong places, which is worse than no card at all.
A browser shapes Thai correctly by definition, so the card is HTML and Chrome
takes the picture.

    python3 make_og_cards.py                 # rank >= 3, plus featured/claimed
    python3 make_og_cards.py --all           # every place (slow: ~1s each)
    python3 make_og_cards.py --min-rank 5
    python3 make_og_cards.py --force         # redraw cards that already exist
    python3 make_og_cards.py --stale         # redraw only what the design outran
                                             #   (resumable: safe to re-run)

Run it before build.py. build.py copies assets/og/ into docs/og/ and points
each place page's og:image at its own card; anything missing falls back to the
brand card, so the site never waits on this script.
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import map_ground

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "og"
CANON = ROOT / "data" / "canonical"

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/opt/pw-browsers/chromium",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("google-chrome") or "",
]

CAT_GLYPH = {
    "wat": "🛕", "food": "🍜", "massage": "💆", "medical": "⚕", "essentials": "🏧",
    "hotel": "🛏", "school-intl": "🎓", "market": "🧺", "shopping": "🛍",
    "realestate": "🏘", "transport": "🛵", "repair": "🔧", "beauty": "✂",
    "pets": "🐕", "learn": "📚", "home-services": "🧹", "community": "🫂",
    "business": "🗂", "whats-on": "🎬", "museums-galleries": "🖼", "sights": "⛰",
}

MAP_W = 500          # the ground panel, full-bleed down the right-hand edge
TEXT_R = MAP_W + 60  # where the rules and the text stop

TEMPLATE = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF6EE;color:#2A1E16;
font-family:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Arial Unicode MS",
 "Helvetica Neue",Arial,sans-serif;
position:relative;padding:0}}
.rule{{position:absolute;left:60px;right:{text_r}px;height:5px;
border-top:5px solid #C2401C;border-bottom:5px solid #C2401C;box-sizing:content-box}}
.rule.t{{top:44px}} .rule.b{{top:571px}}
.mid{{position:absolute;left:60px;right:{text_r}px;top:110px;bottom:210px;
display:flex;flex-direction:column;justify-content:center}}
.bot{{position:absolute;left:60px;right:{text_r}px;bottom:80px}}
/* The ground. Full-bleed to three edges — a map panel with a margin round it
   reads as an illustration of a map, and a map that runs off the edge reads as
   a piece of somewhere bigger, which is what it is. */
.map{{position:absolute;top:0;right:0;bottom:0;width:{map_w}px;
background:#FBF6EE;border-left:3px solid #E4D8C4}}
.map img{{display:block;width:{map_w}px;height:630px}}
.map::after{{content:"";position:absolute;top:0;left:0;bottom:0;width:70px;
background:linear-gradient(90deg,#FBF6EE 0%,rgba(251,246,238,0) 100%)}}
/* The pin sits dead centre because the ground was drawn centred on the place.
   Its ring is what lifts it off a busy street grid. */
.pin{{position:absolute;top:50%;left:50%;width:38px;height:38px;margin:-19px 0 0 -19px;
border-radius:50%;background:#C2401C;border:6px solid #FFFCF6;
box-shadow:0 3px 10px rgba(42,30,22,.35);z-index:3}}
/* Where the pin is a block rather than a doorway, say so with a soft disc
   instead of a hard point. Claiming a doorway we do not have is the one thing
   a map must not do. */
.halo{{position:absolute;top:50%;left:50%;width:190px;height:190px;
margin:-95px 0 0 -95px;border-radius:50%;background:rgba(194,64,28,.13);
border:2px dashed rgba(143,46,19,.45);z-index:2}}
.prec{{position:absolute;left:50%;transform:translateX(-50%);top:20px;font-size:18px;
color:#8F2E13;z-index:4;background:rgba(255,252,246,.92);padding:5px 14px;
border:1px solid #E4D8C4;border-radius:999px;white-space:nowrap}}
.top{{display:flex;align-items:center;gap:16px;font-size:28px;color:#8F2E13}}
.glyph{{font-size:42px;line-height:1}}
.name{{font-size:{size}px;line-height:1.12;font-weight:700;margin:10px 0 0;
max-height:250px;overflow:hidden}}
.en{{font-size:30px;color:#6B5A48;margin-top:10px;line-height:1.2;
max-height:74px;overflow:hidden}}
.trail{{height:2px;margin:0 0 18px;
background:repeating-linear-gradient(90deg,#8F2E13 0 4px,transparent 4px 20px);
opacity:.35}}
.foot{{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;
padding-bottom:14px}}
.ants{{font-size:32px;letter-spacing:-2px;white-space:nowrap;line-height:1.1}}
.ants .off{{opacity:.16}}
.rank{{font-size:22px;color:#8F2E13;margin-top:4px}}
.brand{{text-align:right;font-size:32px;font-weight:700;color:#C2401C;
white-space:nowrap;line-height:1.15}}
.brand small{{display:block;font-size:20px;font-weight:400;color:#6B5A48;
letter-spacing:.06em}}
.where{{font-size:24px;color:#8F2E13;margin-top:14px;line-height:1.25}}
</style></head><body>
{map}
<div class="rule t"></div>
<div class="mid">
<div class="top"><span class="glyph">{glyph}</span><span>{cat}</span></div>
<h1 class="name">{name}</h1>
<div class="en">{en}</div>
<div class="where">{where}</div>
</div>
<div class="bot">
<div class="trail"></div>
<div class="foot">
<div>
<div class="ants"><span class="on">{ants_on}</span><span class="off">{ants_off}</span></div>
<div class="rank">{rank}/9 {rank_label}</div>
</div>
<div class="brand">🐜 มดแดง<small>motdang.net</small></div>
</div>
</div>
<div class="rule b"></div>
</body></html>
"""


W, H, SHOT_H = 1200, 630, 720

# When the card DESIGN last changed. Bump it — deliberately — whenever a change
# here alters what a card looks like; --stale then redraws everything older.
#
# An explicit stamp rather than this file's mtime, which was the first attempt:
# mtime says a card is stale because somebody added a command-line flag, and a
# thousand needless redraws is an hour of somebody's afternoon. The person
# changing the design is the only one who knows they changed it.
#
# --stale exists because --force and no-flag are both wrong for the common
# case. A thousand-card redraw takes an hour and does not always survive the
# hour; when it stops half way, --force starts again from the beginning and
# redoes every card it already did, and no flag at all skips exactly the ones
# still needing it. This makes the run resumable and idempotent: run it again
# and it picks up where it stopped, and running it twice costs nothing.
DESIGN_STAMP = "2026-08-12 20:00"      # the map panel landed on the card

DESIGN_MTIME = datetime.datetime.strptime(
    DESIGN_STAMP, "%Y-%m-%d %H:%M").timestamp()


def crop(png):
    """Cut the 1200x630 card out of the taller render, and flatten the palette.

    The palette pass is what makes a basemap on ten thousand cards affordable.
    A 24-bit screenshot of a map card is ~130 KB; the same card has perhaps
    forty actual colours in it — cream, three greens, the road whites, the ant
    red, ink — so 256 indexed colours is visually lossless here and lands
    around 45 KB. Across the catalogue that is the difference between adding
    100 MB to docs/ and adding 15.
    """
    try:
        from PIL import Image
    except ImportError:
        return  # no Pillow: the card is simply taller than spec, still usable
    with Image.open(png) as im:
        card = im.convert("RGB").crop((0, 0, W, H))
        card.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                      dither=Image.Dither.NONE).save(png, optimize=True)


def esc(s):
    return ((s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def find_chrome():
    for c in CHROMES:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Chromium found — install one, or edit CHROMES in this file.")


def name_size(name, narrow=False):
    """Long names step down rather than spill out of the frame.

    `narrow` is the card with a map panel on it: the text column is 640 px
    instead of 1080, so every step comes down with it. Set at the full-width
    sizes it wrapped to four lines and the last one was clipped mid-word.
    """
    n = len(name or "")
    if narrow:
        return 68 if n <= 18 else 54 if n <= 30 else 44 if n <= 48 else 36
    return 96 if n <= 18 else 76 if n <= 30 else 60 if n <= 48 else 46


TAMBON = re.compile(r"(ต\.[^\s,]+)")
AMPHOE = re.compile(r"(อ\.[^\s,]+)")


def where_line(r):
    """ตำบล and อำเภอ off the address — the two words a local uses to place
    somewhere before they have heard the name. The map panel shows WHICH soi;
    this line says which part of town, which is the question a share preview
    is actually being asked."""
    a = r.get("address") or ""
    bits = [m.group(1) for m in (TAMBON.search(a), AMPHOE.search(a)) if m]
    return " ".join(bits)


def map_panel(r, ground):
    """The ground under the place, as an <img> plus its pin.

    Returns "" when there is no basemap on this machine or the place has no
    usable point, and the card falls back to the full-width text it has always
    been. A card is never held up by the tiles.
    """
    lat, lng = r.get("lat"), r.get("lng")
    if not ground or not ground.available or lat is None or lng is None:
        return ""
    prec = r.get("geoPrecision") or "exact"
    if prec == "needs-pin":
        return ""
    # A landmark is looked at from further off than a noodle stall: 1.1 km
    # shows the wat and its neighbourhood, 600 m shows the doorway and the two
    # sois that reach it.
    span = 1100 if r.get("landmark") else 600 if prec == "exact" else 900
    im = ground.picture((lat, lng), (MAP_W, 630), span_m=span, fade=0.97)
    if im is None:
        return ""
    if prec == "exact":
        mark, note = '<div class="pin"></div>', ""
    else:
        mark = '<div class="halo"></div><div class="pin"></div>'
        note = '<div class="prec">ตำแหน่งโดยประมาณ · approximate</div>'
    return ('<div class="map"><img src="%s" alt="">%s%s</div>'
            % (map_ground.data_uri(im), mark, note))


def card_html(r, cats, rank, ground=None):
    key = (r.get("cat") or ["food"])[0]
    cat = cats.get(key, {}).get("th", "")
    en_name = r.get("nameEn") or ""
    if en_name == r.get("name"):
        en_name = ""
    panel = map_panel(r, ground)
    return TEMPLATE.format(
        size=name_size(r.get("name"), narrow=bool(panel)),
        glyph=CAT_GLYPH.get(key, "🐜"),
        cat=esc(cat),
        name=esc(r.get("name") or r.get("nameEn") or r["id"]),
        en=esc(en_name),
        where=esc(where_line(r)) if panel else "",
        map=panel,
        map_w=MAP_W,
        text_r=TEXT_R if panel else 60,
        ants_on="🐜" * rank,
        ants_off="🐜" * (9 - rank),
        rank=rank,
        rank_label=esc("ข้อมูลที่มดแดงมี"),
    )


def load_ranks():
    """Ant ranks straight from build.py, so the card can never disagree
    with the page it is the preview for."""
    sys.path.insert(0, str(ROOT))
    import build  # noqa: E402  — imported for ant_rank and its data loading
    return build.ant_rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--min-rank", type=int, default=3)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stale", action="store_true",
                    help="redraw only cards older than the code that draws them")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    chrome = find_chrome()
    ground = map_ground.shared()
    if not ground.available:
        print("no basemap archive (%s) — cards fall back to text only"
              % (ground.error or ground.path))
    OUT.mkdir(parents=True, exist_ok=True)
    cats = {c["key"]: c for c in json.loads(
        (ROOT / "data" / "categories.json").read_text())["categories"]}
    ant_rank = load_ranks()

    records = []
    for f in sorted(CANON.glob("*.json")):
        records += json.loads(f.read_text())

    todo = []
    for r in records:
        rank = ant_rank(r)
        if not args.all and rank < args.min_rank and not r.get("featured"):
            continue
        dest = OUT / f"{r['id']}.png"
        if dest.exists() and not args.force and not (
                args.stale and dest.stat().st_mtime < DESIGN_MTIME):
            continue
        todo.append((r, rank, dest))
    if args.limit:
        todo = todo[:args.limit]

    print(f"{len(todo):,} card(s) to draw -> {OUT}")
    tmp = Path(tempfile.mkdtemp(prefix="ogcards-"))
    for i, (r, rank, dest) in enumerate(todo, 1):
        src = tmp / "card.html"
        src.write_text(card_html(r, cats, rank, ground), encoding="utf-8")
        subprocess.run([
            chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--no-sandbox", "--force-device-scale-factor=1",
            # Headless Chrome's screenshot viewport comes up ~70px short of
            # the requested window, silently cropping the foot of the card.
            # Render tall, then cut the card out of the top.
            "--window-size=1200,%d" % SHOT_H, "--screenshot=" + str(dest),
            src.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        crop(dest)
        if i % 100 == 0 or i == len(todo):
            print(f"  {i:,}/{len(todo):,}")
    shutil.rmtree(tmp, ignore_errors=True)
    print("done — now run build.py to copy them into docs/og/")


if __name__ == "__main__":
    main()
