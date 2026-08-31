#!/usr/bin/env python3
"""The share card for what.html — assets/og/what.png, 1200x630.

what.html is the page you send when somebody asks "เว็บอะไรอ่ะ", which means
its card is the first thing most people ever see of this site. The brand card
(make_card.py) says the name over the old city; that is right for a link with
no page of its own, and wrong here — a card for the page that IS the tour
should be the tour, in one picture.

So the card is built from the same files the page shows: four of the plates in
assets/show/, fanned out like the pictures on the page itself, with the ants'
three shortest promises beside them. Same source as the page means the card
cannot drift from what a reader finds when they arrive, which is the only
promise a share card can actually make.

Method is make_og_cards.py's, for its reason: Pillow here has no raqm, so Thai
marks land in the wrong places — "มดแดงคืออะไร" has a vowel above the คื and
would render broken. The card is HTML, a headless Chrome takes the picture,
and the site's own fonts come off disk, so the card is set in Chonburi and
Sriracha exactly as the page is.

    python3 make_what_card.py            # -> assets/og/what.png

Run it BEFORE build.py, which copies assets/og/ into docs/og/. If the file is
missing the page falls back to the brand card, so the site never waits here.
"""
import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOW = ROOT / "assets" / "show"
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / "assets" / "og" / "what.png"

W, H = 1200, 630

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/opt/pw-browsers/chromium",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("google-chrome") or "",
]

# The fan, back to front. Chosen because each one is legible at LINE preview
# size and each says a different thing: the year is a wheel, the ground is
# real, the city has an evening, the doors are hand-kept.
FAN = [
    # (file, degrees, left, top, width) — laid out by hand so all four stay
    # inside the frame and none is wholly hidden by the one in front. The
    # widths differ because the crops do: counts.jpg is a tall column, night
    # a wide strip, and a fan of equal boxes reads as a contact sheet rather
    # than a handful of pictures.
    ("doors.jpg", -7.0, 516, 58, 384),
    ("night.jpg", 5.5, 754, 36, 404),
    ("wheel.jpg", -4.5, 800, 210, 372),
    ("counts.jpg", 3.5, 556, 262, 322),
]

PROMISES = [
    ("ไม่มีอันดับ", "nothing is ranked"),
    ("ซื้อที่ยืนไม่ได้", "no place is for sale"),
    ("ฟรีทั้งสองทาง", "free in both directions"),
]


def find_chrome():
    for c in CHROMES:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Chromium found — install one, or edit CHROMES in this file.")


def data_uri(path, mime):
    return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode())


def font_faces():
    """The site's own faces, inlined. Chrome is given a file:// page in a temp
    directory, so a relative url(fonts/…) would miss; each face carries its
    own bytes instead and the card renders the same on any machine."""
    out = []
    for fam, stem in (("Chonburi", "chonburi-400"), ("Prompt", "prompt-400"),
                      ("Prompt6", "prompt-600"), ("Sriracha", "sriracha-400")):
        for sub in ("thai", "latin"):
            f = FONTS / f"{stem}-{sub}.woff2"
            if f.exists():
                out.append(
                    "@font-face{font-family:'%s';font-style:normal;"
                    "font-weight:400;src:url(%s) format('woff2')}"
                    % (fam, data_uri(f, "font/woff2")))
    return "".join(out)


def card_html():
    plates = []
    for name, rot, left, top, width in FAN:
        f = SHOW / name
        if not f.exists():
            continue
        plates.append(
            f'<img class="pl" style="left:{left}px;top:{top}px;'
            f'transform:rotate({rot}deg);width:{width}px" '
            f'src="{data_uri(f, "image/jpeg")}" alt="">')
    promises = "".join(
        f'<li><b>{th}</b><span>{en}</span></li>' for th, en in PROMISES)
    return f"""<!doctype html><meta charset="utf-8"><style>
{font_faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;overflow:hidden;background:#FBF6EE;
  font-family:'Prompt',sans-serif;position:relative}}
/* the ant trail the site wears at the top and bottom of every page */
.trail{{position:absolute;left:0;right:0;height:14px;
  background:repeating-linear-gradient(90deg,#A5231D 0 26px,#FBF6EE 26px 34px,
  #E4B04A 34px 46px,#FBF6EE 46px 54px)}}
.trail.t{{top:0}} .trail.b{{bottom:0}}
.fan{{position:absolute;inset:0}}
.pl{{position:absolute;border:4px solid #3A2A18;border-radius:12px;
  background:#FDF8EC;box-shadow:9px 10px 0 rgba(58,42,24,.30)}}
/* the paper the words sit on, clearing to nothing over the pictures */
.wash{{position:absolute;left:0;top:0;bottom:0;width:600px;
  background:linear-gradient(90deg,#FBF6EE 0,#FBF6EE 68%,rgba(251,246,238,0) 100%)}}
.col{{position:absolute;left:56px;top:74px;width:520px}}
.brand{{display:flex;align-items:center;gap:14px}}
.ant{{width:74px;height:74px;border-radius:14px;background:#A5231D;
  border:3px solid #7D1712;display:flex;align-items:center;
  justify-content:center;font-size:42px;line-height:1}}
.wordmark{{font-family:'Chonburi',serif;font-size:46px;color:#A5231D;
  line-height:1}}
.wordmark small{{display:block;font-family:'Prompt',sans-serif;font-size:13px;
  letter-spacing:.34em;color:#3A2A18;margin-top:5px}}
h1{{font-family:'Chonburi',serif;font-size:60px;line-height:1.16;
  color:#2C1F12;margin-top:30px}}
h1 span{{display:block;font-size:34px;color:#6E5B44;margin-top:6px}}
ul{{list-style:none;margin-top:26px;display:flex;flex-direction:column;gap:9px}}
li{{font-family:'Sriracha',cursive;font-size:25px;color:#2C1F12;
  line-height:1.2}}
li b{{font-weight:400;color:#A5231D}}
li span{{color:#6E5B44;font-size:20px;margin-left:9px}}
.count{{position:absolute;left:56px;bottom:52px;font-size:21px;
  color:#3A2A18;font-weight:600}}
.count b{{color:#A5231D;font-size:25px}}
</style>
<div class="fan">{''.join(plates)}</div>
<div class="wash"></div>
<div class="col">
  <div class="brand">
    <div class="ant">🐜</div>
    <div class="wordmark">มดแดง<small>MOT DANG</small></div>
  </div>
  <h1>มดแดงคืออะไร<span>What Mot Dang is</span></h1>
  <ul>{promises}</ul>
</div>
<div class="count"><b>20,702</b> ที่ · places · เชียงใหม่ · เชียงราย</div>
<div class="trail t"></div><div class="trail b"></div>
"""


def main():
    if not SHOW.is_dir() or not any(SHOW.glob("*.jpg")):
        sys.exit("assets/show/ has no plates — nothing to draw the card from.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "what-card.html"
        page.write_text(card_html())
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={W},{H}", "--default-background-color=FBF6EE",
             "--virtual-time-budget=4000", f"--screenshot={OUT}",
             page.as_uri()],
            check=True, capture_output=True)
    # Same palette pass as every other card here: a cream page with four
    # photographs on it is nowhere near 24-bit, and the card is served to
    # phones on mobile data.
    try:
        from PIL import Image
        with Image.open(OUT) as im:
            card = im.convert("RGB").crop((0, 0, W, H))
            card.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                          dither=Image.Dither.NONE).save(OUT, optimize=True)
    except ImportError:
        pass                      # no Pillow: the card is fine, just heavier
    print("what card -> %s (%.0f KB)" % (OUT.relative_to(ROOT),
                                         OUT.stat().st_size / 1024))


if __name__ == "__main__":
    main()
