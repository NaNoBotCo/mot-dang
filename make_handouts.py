#!/usr/bin/env python3
"""Printed A4 handouts, one per trade — assets/handouts/<key>.pdf

Why paper. The whole recruitment plan used to run through a platform account,
and that account was disabled overnight with a single appeal. A sheet of A4 in
somebody's hand cannot be disabled, cannot be down-ranked, and works in a
kitchen with no signal. It is also the only channel where the person handing it
over is standing in front of the person receiving it, which is worth more than
any amount of reach.

Two sides. Front is why this is worth five minutes; back is scan-this-send-this.
Designed to survive a black-and-white photocopier and being taped to a wall:
no background fills, no light grey type, one QR big enough to scan off a
crooked copy.

Thai leads on every sheet. The housekeeper sheet is trilingual — Thai, English
and Shan — and prints an UNVERIFIED banner across both sides until a Shan
speaker has read it and data/curated/handouts.json says shanVerified: true.
The banner is not decoration: a wrong handout given to a migrant worker is
worse than no handout, and nobody who writes Shan wrote these strings.

    python3 make_handouts.py                 # all sheets
    python3 make_handouts.py krapow wat      # just these
    python3 make_handouts.py --html          # leave the HTML for hand-editing

Chrome does the rendering, for the same reason it renders the share cards:
Thai stacks vowels and tone marks, Shan stacks more, and a browser is the only
thing here that shapes either correctly.

Fonts, before the first run: macOS ships nothing that draws Shan. Install
Noto Sans Thai and Noto Sans Myanmar (both free from Google Fonts) or the Shan
column comes out as empty boxes and the sheet is worse than useless. Arial
Unicode MS, which is in the stack as a last resort, covers Thai but not this.
"""
import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "handouts"
QR_DIR = ROOT / "assets" / "qr"

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/opt/pw-browsers/chromium",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("google-chrome") or "",
]

# Bigger is better on a photocopy: the L version survives a third-generation
# copy, the S one does not.
QR_CANDIDATES = ["L_gainfriends_2dbarcodes_GW.png",
                 "M_gainfriends_2dbarcodes_GW.png",
                 "S_gainfriends_2dbarcodes_GW.png"]

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 210mm; }
body {
  font-family: "Noto Sans Thai", "IBM Plex Sans Thai", "Sarabun",
    "Noto Sans Myanmar", "Pyidaungsu", "Arial Unicode MS", Arial, sans-serif;
  color: #000; background: #fff; font-size: 11.5pt; line-height: 1.5;
}
.page {
  width: 210mm; height: 297mm; padding: 16mm 16mm 14mm;
  position: relative; page-break-after: always; overflow: hidden;
  display: flex; flex-direction: column;
}
.page:last-child { page-break-after: auto; }
.rule { border-top: 3px solid #000; border-bottom: 3px solid #000;
  height: 3px; padding-top: 3px; }
.brandrow { display: flex; justify-content: space-between; align-items: baseline;
  margin-top: 4mm; font-size: 10.5pt; letter-spacing: .04em; }
.brandrow b { font-size: 15pt; }
.who { margin-top: 9mm; font-size: 12pt; font-weight: 700; }
.who .en { display: block; font-weight: 400; font-size: 10.5pt; color: #333; }
h1 { font-size: 26pt; line-height: 1.22; margin-top: 3mm; font-weight: 700; }
h1 .en { display: block; font-size: 14pt; font-weight: 400;
  line-height: 1.3; margin-top: 2.5mm; color: #222; }
h1 .shn { display: block; font-size: 15pt; font-weight: 400;
  line-height: 1.5; margin-top: 2.5mm; }
.lede { margin-top: 6mm; font-size: 12.5pt; }
.lede .en { display: block; margin-top: 2.5mm; font-size: 10.5pt; color: #222; }
.lede .shn { display: block; margin-top: 2.5mm; font-size: 12pt; }
ul.points { margin-top: 7mm; list-style: none; }
ul.points li { margin-bottom: 5mm; padding-left: 9mm; position: relative;
  font-size: 12pt; }
ul.points li:before { content: "🐜"; position: absolute; left: 0; top: 0;
  font-size: 11pt; }
ul.points .en { display: block; font-size: 10pt; color: #222; margin-top: 1mm; }
ul.points .shn { display: block; font-size: 11.5pt; margin-top: 1mm; }
.spacer { flex: 1; }
.freebar { border: 3px solid #000; padding: 4mm 5mm; text-align: center;
  font-size: 14pt; font-weight: 700; }
.freebar .en { display: block; font-size: 10.5pt; font-weight: 400; margin-top: 1.5mm; }
.foot { margin-top: 5mm; display: flex; justify-content: space-between;
  align-items: flex-end; font-size: 10pt; }
.foot .site { font-size: 15pt; font-weight: 700; letter-spacing: .02em; }
/* ---- back ---- */
h2 { font-size: 20pt; margin-top: 8mm; }
h2 .en { display: block; font-size: 12pt; font-weight: 400; margin-top: 2mm; }
h2 .shn { display: block; font-size: 13pt; font-weight: 400; margin-top: 2mm; }
.steps { margin-top: 7mm; list-style: none; counter-reset: s; }
.steps li { counter-increment: s; margin-bottom: 6mm; padding-left: 13mm;
  position: relative; font-size: 13pt; }
.steps li:before { content: counter(s); position: absolute; left: 0; top: -1mm;
  width: 9mm; height: 9mm; border: 2.5px solid #000; border-radius: 50%;
  text-align: center; line-height: 8mm; font-size: 12pt; font-weight: 700; }
.steps .en { display: block; font-size: 10pt; color: #222; margin-top: 1mm; }
.qrwrap { margin-top: 6mm; display: flex; gap: 8mm; align-items: center; }
.qrwrap img { width: 52mm; height: 52mm; border: 2px solid #000; }
.qrwrap .lineid { font-size: 20pt; font-weight: 700; }
.qrwrap p { font-size: 11pt; margin-top: 2mm; }
.ants { font-size: 15pt; letter-spacing: -1px; }
.ladder { margin-top: 6mm; border: 2px solid #000; padding: 4mm 5mm; }
.ladder .en { display: block; font-size: 10pt; color: #222; margin-top: 1.5mm; }
.note { margin-top: 6mm; font-size: 11.5pt; }
.note .en { display: block; font-size: 10pt; color: #222; margin-top: 1.5mm; }
.note .shn { display: block; font-size: 11.5pt; margin-top: 1.5mm; }
.cut { margin-top: 4mm; border-top: 1px dashed #000; padding-top: 2mm;
  font-size: 9pt; color: #333; }
/* ---- the unverified stamp ---- */
.unverified { position: absolute; top: 0; left: 0; right: 0;
  background: #000; color: #fff; padding: 2.5mm 6mm; font-size: 10pt;
  font-weight: 700; letter-spacing: .03em; }
.unverified span { display: block; font-weight: 400; font-size: 9pt; }
.page.stamped { padding-top: 24mm; }
/* Three languages do not fit in the space two of them take. Everything on a
   trilingual sheet tightens rather than spilling onto a third page. */
.page.tri h1 { font-size: 21pt; }
.page.tri h1 .en { font-size: 12pt; margin-top: 2mm; }
.page.tri h1 .shn { font-size: 12.5pt; margin-top: 2mm; }
.page.tri .who { margin-top: 5mm; }
.page.tri .lede { margin-top: 4mm; font-size: 11pt; }
.page.tri .lede .en, .page.tri .lede .shn { margin-top: 1.5mm; font-size: 9.5pt; }
.page.tri ul.points { margin-top: 4mm; }
.page.tri ul.points li { margin-bottom: 3mm; font-size: 10.5pt; }
.page.tri ul.points .en { font-size: 8.8pt; margin-top: .6mm; }
.page.tri ul.points .shn { font-size: 10pt; margin-top: .6mm; }
.page.tri .freebar { font-size: 12pt; padding: 3mm 4mm; }
.page.tri h2 { font-size: 16pt; margin-top: 5mm; }
.page.tri .steps li { font-size: 11.5pt; margin-bottom: 4mm; }
"""

HOW_H_TH = "ทักมาทางไลน์ ใช้เวลาห้านาที"
HOW_H_EN = "Message us on LINE. Five minutes, start to finish."

BANNER_TH = "ยังไม่ได้ตรวจภาษาไทใหญ่ — ห้ามแจกจนกว่าคนไทใหญ่จะอ่านให้"
BANNER_EN = ("SHAN TEXT NOT YET CHECKED — do not hand this out until a Shan "
             "speaker has read it. Machine-written, unverifiable by its writer.")


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def find_chrome():
    for c in CHROMES:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Chromium found — install one, or edit CHROMES in this file.")


def qr_data_uri():
    for name in QR_CANDIDATES:
        p = QR_DIR / name
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f"data:image/png;base64,{b64}"
    return ""


def tri(th, en, shn=None):
    """Thai first, English under it, Shan under that when the sheet carries it."""
    out = esc(th)
    if en:
        out += f'<span class="en">{esc(en)}</span>'
    if shn:
        out += f'<span class="shn">{esc(shn)}</span>'
    return out


def sheet_html(s, common, cfg, qr, stamped):
    three = bool(s.get("trilingual"))
    banner = ""
    cls = "page tri" if three else "page"
    if stamped:
        cls += " stamped"
        banner = (f'<div class="unverified">{esc(BANNER_TH)}'
                  f"<span>{esc(BANNER_EN)}</span></div>")

    points = "".join(
        f"<li>{tri(p[0], p[1], p[2] if three and len(p) > 2 else None)}</li>"
        for p in s["points"])

    line_id = cfg.get("lineOaId", "")
    steps = "".join(f"<li>{tri(common[f'how_{i}_th'], common[f'how_{i}_en'])}</li>"
                    for i in (1, 2, 3))

    head = (f'<div class="rule"></div>'
            f'<div class="brandrow"><b>🐜 มดแดง Mot Dang</b>'
            f"<span>motdang.net</span></div>")

    front = f"""<div class="{cls}">{banner}{head}
<div class="who">{esc(s['audience_th'])}<span class="en">{esc(s['audience_en'])}</span></div>
<h1>{esc(s['headline_th'])}
<span class="en">{esc(s['headline_en'])}</span>
{f'<span class="shn">{esc(s["headline_shn"])}</span>' if three and s.get('headline_shn') else ''}</h1>
<div class="lede">{tri(s['lede_th'], s['lede_en'], s.get('lede_shn') if three else None)}</div>
<ul class="points">{points}</ul>
<div class="spacer"></div>
<div class="freebar">{esc(common['free_th'])}<span class="en">{esc(common['free_en'])}</span></div>
<div class="foot"><span>{esc(s['glyph'])} {esc(common['noapp_th'])}</span>
<span class="site">motdang.net</span></div>
</div>"""

    qr_img = f'<img src="{qr}" alt="LINE QR">' if qr else ""
    back = f"""<div class="{cls}">{banner}{head}
<h2>{esc(HOW_H_TH)}<span class="en">{esc(HOW_H_EN)}</span></h2>
<div class="qrwrap">{qr_img}
<div><span class="lineid">{esc(line_id)}</span>
<p>{esc(common['noapp_th'])}</p><p class="en">{esc(common['noapp_en'])}</p></div></div>
<ol class="steps">{steps}</ol>
<div class="ladder"><span class="ants">🐜🐜🐜🐜🐜🐜🐜🐜🐜</span><br>
{esc(common['ants_th'])}<span class="en">{esc(common['ants_en'])}</span></div>
<div class="note">{tri(s['back_th'], s['back_en'], s.get('back_shn') if three else None)}</div>
<div class="spacer"></div>
<div class="foot"><span>🐜 มดแดง · motdang.net · {esc(line_id)}</span>
<span>{esc(s['audience_th'])}</span></div>
<div class="cut">ถ่ายเอกสารแจกต่อได้เลย ไม่ต้องขอ · Photocopy and hand these out freely — no permission needed.</div>
</div>"""

    return (f'<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">'
            f"<style>{CSS}</style></head><body>{front}{back}</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*", help="sheet keys; default is all")
    ap.add_argument("--html", action="store_true", help="also keep the HTML")
    args = ap.parse_args()

    doc = json.loads((ROOT / "data" / "curated" / "handouts.json").read_text())
    cfg_path = ROOT / "data" / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    common, sheets = doc["common"], doc["sheets"]
    shan_ok = bool(doc.get("shanVerified"))
    qr = qr_data_uri()
    if not qr:
        print("warning: no LINE QR found in assets/qr — printing without it")
    if not cfg.get("lineOaId"):
        print("warning: no lineOaId in data/config.json — the sheet will print "
              "without the one thing it exists to hand over")

    chrome = find_chrome()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="handouts-"))

    wanted = [s for s in sheets if not args.keys or s["key"] in args.keys]
    if not wanted:
        sys.exit(f"no such sheet. keys: {', '.join(s['key'] for s in sheets)}")

    for s in wanted:
        stamped = bool(s.get("trilingual")) and not shan_ok
        html = sheet_html(s, common, cfg, qr, stamped)
        src = tmp / f"{s['key']}.html"
        src.write_text(html, encoding="utf-8")
        if args.html:
            (OUT / f"{s['key']}.html").write_text(html, encoding="utf-8")
        dest = OUT / f"{s['key']}.pdf"
        subprocess.run([
            chrome, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer", "--print-to-pdf=" + str(dest),
            src.as_uri()], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        flag = "  [UNVERIFIED SHAN — do not distribute]" if stamped else ""
        print(f"  {dest.relative_to(ROOT)}{flag}")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(wanted)} sheet(s) -> {OUT}")
    if not shan_ok and any(s.get("trilingual") for s in wanted):
        print("Shan is unchecked: set shanVerified true in handouts.json once a "
              "Shan speaker has read it, then re-run to drop the banner.")


if __name__ == "__main__":
    main()
