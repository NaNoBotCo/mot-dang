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

Run it before build.py. build.py copies assets/og/ into docs/og/ and points
each place page's og:image at its own card; anything missing falls back to the
brand card, so the site never waits on this script.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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

TEMPLATE = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF6EE;color:#2A1E16;
font-family:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Arial Unicode MS",
 "Helvetica Neue",Arial,sans-serif;
position:relative;padding:0}}
.rule{{position:absolute;left:60px;right:60px;height:5px;
border-top:5px solid #C2401C;border-bottom:5px solid #C2401C;box-sizing:content-box}}
.rule.t{{top:44px}} .rule.b{{top:571px}}
.mid{{position:absolute;left:60px;right:60px;top:110px;bottom:210px;
display:flex;flex-direction:column;justify-content:center}}
.bot{{position:absolute;left:60px;right:60px;bottom:80px}}
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
</style></head><body>
<div class="rule t"></div>
<div class="mid">
<div class="top"><span class="glyph">{glyph}</span><span>{cat}</span></div>
<h1 class="name">{name}</h1>
<div class="en">{en}</div>
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


def crop(png):
    """Cut the 1200x630 card out of the taller render."""
    try:
        from PIL import Image
    except ImportError:
        return  # no Pillow: the card is simply taller than spec, still usable
    with Image.open(png) as im:
        if im.size != (W, H):
            im.convert("RGB").crop((0, 0, W, H)).save(png)


def esc(s):
    return ((s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def find_chrome():
    for c in CHROMES:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Chromium found — install one, or edit CHROMES in this file.")


def name_size(name):
    """Long names step down rather than spill out of the frame."""
    n = len(name or "")
    return 96 if n <= 18 else 76 if n <= 30 else 60 if n <= 48 else 46


def card_html(r, cats, rank):
    key = (r.get("cat") or ["food"])[0]
    cat = cats.get(key, {}).get("th", "")
    en_name = r.get("nameEn") or ""
    if en_name == r.get("name"):
        en_name = ""
    return TEMPLATE.format(
        size=name_size(r.get("name")),
        glyph=CAT_GLYPH.get(key, "🐜"),
        cat=esc(cat),
        name=esc(r.get("name") or r.get("nameEn") or r["id"]),
        en=esc(en_name),
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
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    chrome = find_chrome()
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
        if dest.exists() and not args.force:
            continue
        todo.append((r, rank, dest))
    if args.limit:
        todo = todo[:args.limit]

    print(f"{len(todo):,} card(s) to draw -> {OUT}")
    tmp = Path(tempfile.mkdtemp(prefix="ogcards-"))
    for i, (r, rank, dest) in enumerate(todo, 1):
        src = tmp / "card.html"
        src.write_text(card_html(r, cats, rank), encoding="utf-8")
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
