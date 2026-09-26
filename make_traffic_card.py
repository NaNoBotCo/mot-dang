#!/usr/bin/env python3
"""The 1200×630 share card for /traffic.html: the week as coloured squares.

Each square is one weekday hour, 05:00 to 23:00, coloured by the same bands
and the same sum the page uses (traffic_layer.forecast), for the month the
card is drawn in. Drawn as HTML with the site's own Prompt faces and
photographed by headless Chrome, the way make_shelf_cards.py does it.

    python3 make_traffic_card.py      # -> assets/og/traffic-card.png
"""
import datetime
import json
import subprocess
import tempfile
import time
from pathlib import Path

import traffic_layer as T

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "og" / "traffic-card.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def html(doc):
    city = doc["city"]
    mon = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).month - 1
    rows = []
    for d in range(7):
        cells = "".join(
            f'<i style="background:{T.band(T.forecast(city, d, h, mon)[0])[1]}"></i>'
            for h in T.GRID_HOURS)
        rows.append(f'<div class="r"><b>{T.DAYS_TH_S[d]}</b>{cells}</div>')
    worst = max(((T.forecast(city, d, h, mon), d, h) for d in range(7) for h in range(6, 23)),
                key=lambda x: x[0][0])
    (c, mins, _), wd, wh = worst
    fonts = ROOT / "assets" / "fonts"
    return f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:P;font-weight:400;src:url("{(fonts / 'prompt-400-thai.woff2').as_uri()}");unicode-range:U+0E00-0E7F}}
@font-face{{font-family:P;font-weight:400;src:url("{(fonts / 'prompt-400-latin.woff2').as_uri()}");unicode-range:U+0000-00FF,U+2000-206F}}
@font-face{{font-family:P;font-weight:600;src:url("{(fonts / 'prompt-600-thai.woff2').as_uri()}");unicode-range:U+0E00-0E7F}}
@font-face{{font-family:P;font-weight:600;src:url("{(fonts / 'prompt-600-latin.woff2').as_uri()}");unicode-range:U+0000-00FF,U+2000-206F}}
html,body{{margin:0;width:1200px;height:630px;overflow:hidden;background:#faf5ea;font-family:P,sans-serif;color:#2a1e16}}
.band{{height:18px;background:repeating-linear-gradient(90deg,#c13a2e 0 88px,#faf5ea 88px 104px,#c08a2d 104px 120px,#faf5ea 120px 136px)}}
.wrap{{display:grid;grid-template-columns:500px 1fr;gap:36px;padding:34px 48px}}
h1{{font-size:108px;line-height:1;margin:6px 0 0;font-weight:600}}
h1 small{{display:block;font-size:40px;font-weight:400;color:#685845;margin-top:10px}}
.big{{margin-top:34px;font-size:36px;line-height:1.25;font-weight:600}}
.big span{{display:block;font-size:28px;font-weight:400;color:#544636}}
.brand{{position:absolute;left:48px;bottom:34px;font-size:30px;font-weight:600;color:#c13a2e}}
.brand small{{font-weight:400;color:#685845;font-size:22px;margin-left:10px}}
.grid{{margin-top:6px}}
.r{{display:flex;align-items:center;gap:3px;margin-bottom:5px}}
.r b{{width:48px;flex:none;font-size:24px;font-weight:600}}
.r i{{display:block;flex:none;width:24px;height:56px;border-radius:5px}}
.hrs{{display:flex;gap:3px;margin-left:51px;font-size:18px;color:#685845}}
.hrs span{{flex:none;width:24px;text-align:center}}
</style><div class="band"></div><div class="wrap"><div>
<h1>รถติด<small>Chiang Mai traffic</small></h1>
<p class="big">{T.DAYS_TH[wd]} {wh:02d}:00<br>ทาง 10 นาที ใช้ {round(mins)} นาที
<span>{T.DAYS_EN[wd]} {wh:02d}:00: 10 minutes takes {round(mins)}</span></p>
</div><div class="grid">{"".join(rows)}
<div class="hrs">{"".join(f'<span>{h if h % 3 == 0 else ""}</span>' for h in T.GRID_HOURS)}</div>
</div></div><p class="brand">มดแดง motdang.net/traffic.html<small>TomTom 2025 · กรมทางหลวง</small></p>"""


def main():
    doc = json.loads((ROOT / "data" / "traffic.json").read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(html(doc), encoding="utf-8")
        # Headless Chrome writes the picture and then does not always exit;
        # wait for the file, then end it.
        if OUT.exists():
            OUT.unlink()
        pr = subprocess.Popen([CHROME, "--headless=new", "--hide-scrollbars", "--window-size=1200,630",
                               "--force-device-scale-factor=1", "--user-data-dir=" + tmp,
                               "--allow-file-access-from-files", "--virtual-time-budget=4000",
                               "--screenshot=" + str(OUT), page.as_uri()],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(120):
            if pr.poll() is not None or (OUT.exists() and OUT.stat().st_size > 0):
                break
            time.sleep(0.5)
        time.sleep(1)
        pr.kill()
    if not OUT.exists():
        raise SystemExit("Chrome wrote no card")
    print("card ->", OUT)


if __name__ == "__main__":
    main()
