#!/usr/bin/env python3
"""Social kit — the artwork for Mot Dang's own profiles.

    python3 make_social.py            everything into brand/social/
    python3 make_social.py --list     what it would write, and why that size

Every file is named MD-<what>-<size>.png, so a download is still findable in
~/Downloads next to another site's kit (the visa desk's are CMVD-…).

The cover is the homepage hero at cover size: her photograph, the kicker, the
name in both scripts, the count read from the built docs/index.html (floored to
the thousand so it stays true between runs), and the search row.

Chrome is the renderer, as in visa-desk/tools/social_kit.py: macOS ships the
Thai (Thonburi) and the display face (Avenir Next Condensed).
"""

import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "brand" / "social"
CODE = "MD"
HERO = ROOT / "docs" / "site" / "hero" / "golden-chedi-flags.jpg"   # her own frame

INK = "#12100d"
CREAM = "#f6eee0"
DAY = "#F5C400"          # the search button
DAY_INK = "#17110c"
KICKER = "#ff8f86"

DISPLAY = "'Avenir Next Condensed','HelveticaNeue-CondensedBold','Arial Narrow',sans-serif"
THAI = "Thonburi,'Sukhumvit Set','Noto Sans Thai',sans-serif"
BODY = "'Avenir Next',Avenir,'Helvetica Neue',sans-serif"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

SEARCH_ICON = ('<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
               'stroke-width="2.2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/>'
               '<path d="M15.5 15.5 21 21"/></svg>')


def counts():
    """(places floored to the thousand, shelves) from the built homepage."""
    page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<p>([\d,]+) places · (\d+) shelves</p>", page)
    if not m:
        raise SystemExit("No 'N places · N shelves' line in docs/index.html; build the site first.")
    places = int(m.group(1).replace(",", ""))
    return f"{places // 1000 * 1000:,}+", m.group(2)


def fb_cover(w=1640, h=630):
    """Phones crop the sides to the middle ~1120px (x 260–1380): every word sits inside it.
    Facebook's profile circle overlaps the lower left, so nothing is drawn below y≈520 there."""
    places, shelves = counts()
    return f"""<div class="c" style="width:{w}px;height:{h}px">
<div class="in">
  <div class="kicker"><span class="th">เชียงใหม่ · เชียงราย</span>&ensp;—&ensp;<span class="ls">Chiang Mai &amp; Chiang Rai</span></div>
  <h1><span class="th">มดแดง</span> <span class="en">Mot Dang</span></h1>
  <p class="n"><span class="th">{places} แห่ง · {shelves} หมวด</span> <span class="dot">·</span> {places} places · {shelves} shelves</p>
  <div class="row">
    <div class="box">{SEARCH_ICON}<span>motdang.net</span></div>
    <div class="btn day">{SEARCH_ICON.replace('30', '24')}<span><span class="th">ค้นหา</span> · SEARCH</span></div>
    <div class="btn">ลองโชค · LUCKY</div>
  </div>
</div></div>"""


def style():
    return f"""
html,body{{margin:0;padding:0;background:{INK}}}
.c{{position:relative;overflow:hidden;background:{INK};
  border-top:8px solid {DAY};box-sizing:border-box;
  background-image:linear-gradient(90deg,rgba(18,16,13,.94) 0%,rgba(18,16,13,.86) 38%,
    rgba(18,16,13,.45) 70%,rgba(18,16,13,.2) 100%),url({HERO.as_uri()});
  background-size:cover,cover;background-position:center,center 44%}}
.in{{position:absolute;left:300px;top:92px;color:{CREAM};font-family:{DISPLAY}}}
.th{{font-family:{THAI}}}
.kicker{{font-size:24px;font-weight:700;color:{KICKER}}}
.kicker .ls{{font-size:21px;font-weight:800;letter-spacing:.34em;text-transform:uppercase}}
h1{{margin:18px 0 0;font-size:118px;line-height:1;font-weight:700;letter-spacing:-.01em;white-space:nowrap}}
h1 .en{{text-transform:uppercase;font-weight:700}}
.n{{margin:22px 0 0;font-size:29px;font-weight:500;font-family:{BODY};color:{CREAM};opacity:.92}}
.n .dot{{margin:0 .35em}}
.row{{display:flex;gap:16px;margin-top:34px;align-items:stretch}}
.box,.btn{{display:flex;align-items:center;gap:14px;height:84px;box-sizing:border-box;
  font-weight:700;border:3px solid {DAY_INK}}}
.box{{width:440px;padding:0 26px;background:{CREAM};color:#5d5345;font-size:34px;font-weight:600}}
.btn{{padding:0 28px;background:{CREAM};color:{DAY_INK};font-size:26px;letter-spacing:.04em}}
.btn.day{{background:{DAY}}}
"""


SPECS = [
    ("cover-facebook-1640x630.png", 1640, 630, fb_cover, "Facebook Page cover; words inside the phone crop"),
]


def find_browser():
    for path in CHROME_CANDIDATES:
        if Path(path).is_file():
            return path
    return shutil.which("chromium") or shutil.which("google-chrome")


def render(body, out, width, height):
    browser = find_browser()
    if not browser:
        raise SystemExit("No Chrome/Chromium found.")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "art.html"
        page.write_text(f"<!doctype html><meta charset=utf-8><style>{style()}</style>{body}",
                        encoding="utf-8")
        # --headless=new writes the PNG but does not exit; poll for the file.
        cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--no-sandbox", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--allow-file-access-from-files",
               "--virtual-time-budget=3000", f"--window-size={width},{height}",
               f"--screenshot={out}", "--force-device-scale-factor=1",
               f"--user-data-dir={tmp}/profile", page.as_uri()]
        if out.exists():
            out.unlink()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(600):
                if out.is_file() and out.stat().st_size > 0:
                    time.sleep(0.4)
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
        if not out.is_file() or out.stat().st_size == 0:
            err = (proc.stderr.read() or b"").decode(errors="replace")
            raise SystemExit(f"Chrome produced no image.\n{err[-1200:]}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show the kit without rendering")
    args = ap.parse_args(argv)
    if args.list:
        for name, w, h, _, why in SPECS:
            print(f"{CODE}-{name:38} {w:>5}x{h:<5} {why}")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, w, h, build, why in SPECS:
        out = OUT / f"{CODE}-{name}"
        render(build(), out, w, h)
        print(f"{CODE}-{name:38} {w:>5}x{h:<5} {out.stat().st_size / 1024:7.0f} KB  {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
