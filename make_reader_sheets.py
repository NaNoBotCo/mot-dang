#!/usr/bin/env python3
"""Printed A4 reader sheets — assets/reader/<key>.pdf

The other direction from make_handouts.py. Those sheets are Thai-leading
pitches aimed at a shop owner and end in a LINE QR: join the directory. These
are for the person standing on the pavement with thirty seconds to decide
something, so English leads the explaining while Thai carries the content and
is set large enough to hold up against a real shopfront sign. You do not have
to read Thai to match a shape.

Why paper, again. Somebody in a hurry is on a footpath, not on the site. A
directory that only answers when you already thought to look it up has not
answered the question that actually gets people into the wrong shop.

Same print discipline as the handouts: black only, no background fills, no
light grey type, one big QR, survives a third-generation photocopy and being
taped inside a guesthouse lobby. Chrome does the rendering because Thai stacks
vowels and tone marks and a browser is the only thing here that shapes them.

    python3 make_reader_sheets.py                  # all sheets
    python3 make_reader_sheets.py massage-words    # just this one
    python3 make_reader_sheets.py --html           # keep the HTML too

Fonts: macOS ships Thonburi, which draws Thai correctly. Noto Sans Thai is
better looking if it is installed; the stack prefers it and falls back.
"""
import argparse
import base64
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "reader"

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/opt/pw-browsers/chromium",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("google-chrome") or "",
]

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 210mm; }
body {
  font-family: "Noto Sans Thai", "IBM Plex Sans Thai", "Sarabun", "Thonburi",
    "Arial Unicode MS", Arial, sans-serif;
  color: #000; background: #fff; font-size: 11pt; line-height: 1.45;
}
.page {
  width: 210mm; height: 297mm; padding: 12mm 14mm 10mm;
  position: relative; page-break-after: always;
  display: flex; flex-direction: column;
  /* No overflow:hidden here on purpose. Clipping makes an over-long sheet
     LOOK like it fits — the copy just vanishes off the bottom and the page
     count still says two. Letting it spill onto a third page is what makes
     page_count() an actual check. */
}
.page:last-child { page-break-after: auto; }
.rule { border-top: 3px solid #000; border-bottom: 3px solid #000;
  height: 3px; padding-top: 3px; }
.brandrow { display: flex; justify-content: space-between; align-items: baseline;
  margin-top: 2.4mm; font-size: 10pt; letter-spacing: .04em; }
.brandrow b { font-size: 14pt; }
.who { margin-top: 4mm; font-size: 11pt; font-weight: 700; }
.who .th { display: block; font-weight: 400; font-size: 10.5pt; }
h1 { font-size: 21pt; line-height: 1.12; margin-top: 1.5mm; font-weight: 700; }
h1 .th { display: block; font-size: 14pt; font-weight: 700; margin-top: 1.2mm; }
.lede { margin-top: 2.6mm; font-size: 9.8pt; line-height: 1.34; }
.lede .th { display: block; margin-top: 1.2mm; font-size: 9.6pt; }

/* ---- the term table: Thai left and large, English right ----
   Row height is the whole budget on this page: thirteen terms, four block
   headings and a masthead have to share 273mm. The Thai does not shrink —
   it is the thing being matched against a shopfront, and the reader may not
   have good eyes. So the English gets cut instead, and the transcription and
   the gloss share one line. */
.block { margin-top: 2.4mm; }
.page .block:first-of-type { margin-top: 3mm; }
.bhead { border-top: 2.5px solid #000; border-bottom: 1px solid #000;
  padding: 1.3mm 0; font-size: 11.5pt; font-weight: 700; }
.bhead .en { font-weight: 400; font-size: 9.8pt; }
.bnote { padding: 1mm 0 0; font-size: 9pt; line-height: 1.3; }
.bnote .th { font-size: 9pt; }
.row { display: flex; gap: 4mm; padding: 1.1mm 0;
  border-bottom: 1px dotted #000; page-break-inside: avoid; }
.row:last-child { border-bottom: none; }
.term { width: 68mm; flex: 0 0 68mm; }
.term .th { font-size: 14.5pt; font-weight: 700; line-height: 1.28; }
.term .alt { display: block; font-size: 12.5pt; font-weight: 700;
  line-height: 1.28; }
.term .meta { display: block; font-size: 8pt; margin-top: .5mm;
  line-height: 1.28; }
.term .meta i { font-style: italic; }
.desc { flex: 1; font-size: 9.6pt; line-height: 1.32; }
.star { font-weight: 700; }
.lannakey { margin-top: 1.8mm; font-size: 8.8pt; }

/* The tag strip is the answer to the only question the reader has before
   saying yes: what comes off, where do I lie, how long. It reads before the
   prose does, so it is set bold and above it. */
.desc .tags { display: block; font-weight: 700; font-size: 9.2pt;
  margin-bottom: .5mm; }

/* ---- prices ---- */
table.prices { margin-top: 3mm; width: 100%; border-collapse: collapse; }
table.prices th { font-size: 9pt; text-align: right; padding: 0 0 1.4mm 3mm;
  border-bottom: 2px solid #000; }
table.prices th.kind { text-align: left; padding-left: 0; }
table.prices td { border-bottom: 1px dotted #000; padding: 1.6mm 0 1.6mm 3mm;
  font-size: 11pt; font-weight: 700; text-align: right; }
table.prices td.kind { text-align: left; padding-left: 0; font-weight: 400; }
table.prices td.kind b { font-size: 11pt; display: block; }
table.prices td.kind span { font-size: 9pt; display: block; }
table.addons { margin-top: 2.4mm; width: 100%; border-collapse: collapse; }
table.addons td { border-bottom: 1px dotted #000; padding: 1.2mm 0;
  font-size: 9.6pt; vertical-align: baseline; }
table.addons td.th { font-size: 11pt; font-weight: 700; width: 56mm; }
table.addons td.amt { text-align: right; font-size: 11pt; font-weight: 700;
  width: 26mm; }
.pricenote { margin-top: 2.2mm; font-size: 9pt; }
.pricenote .th { display: block; font-size: 8.8pt; margin-top: .5mm; }
.aob { margin-top: 2.4mm; border: 2px solid #000; padding: 2.4mm 3.4mm;
  font-size: 9.4pt; }
.aob .th { display: block; font-size: 9.2pt; margin-top: .6mm; }
ul.tips { margin-top: 3mm; list-style: none; }
ul.tips li { margin-bottom: 2.2mm; padding-left: 8.5mm; position: relative;
  font-size: 10.5pt; font-weight: 700; }
ul.tips li:before { content: "🐜"; position: absolute; left: 0; top: 0;
  font-size: 9pt; }
ul.tips .en { display: block; font-size: 9.4pt; font-weight: 400;
  margin-top: .5mm; line-height: 1.3; }

/* ---- the unverified stamp, same discipline as the Shan banner on the
   trade handouts: a sheet carrying numbers nobody has checked says so on
   every side, in black, until somebody checks them. ---- */
.unverified { position: absolute; top: 0; left: 0; right: 0;
  background: #000; color: #fff; padding: 2.2mm 6mm; font-size: 9.6pt;
  font-weight: 700; letter-spacing: .03em; }
.unverified span { display: block; font-weight: 400; font-size: 8.8pt; }
.page.stamped { padding-top: 22mm; }

/* ---- back page furniture ---- */
h2 { font-size: 15.5pt; margin-top: 3.6mm; font-weight: 700; }
h2 .th { display: block; font-size: 11.5pt; font-weight: 700; margin-top: 1mm; }
.box { border: 3px solid #000; padding: 3mm 4.5mm; margin-top: 3mm; }
.box p { font-size: 9.6pt; line-height: 1.3; }
.box .th { display: block; font-size: 9.8pt; margin-top: 1.6mm; }
.plaqueword { margin-top: 2.2mm; border-top: 1px solid #000; padding-top: 2mm;
  text-align: center; }
.plaqueword b { font-size: 17pt; display: block; line-height: 1.22; }
.plaqueword i { font-size: 9.2pt; display: block; margin-top: .8mm; }
.plaqueword span { font-size: 9.4pt; display: block; margin-top: .8mm; }
ul.look { margin-top: 2.8mm; list-style: none; }
ul.look li { margin-bottom: 2mm; padding-left: 8.5mm; position: relative;
  font-size: 10pt; font-weight: 700; }
ul.look li:before { content: ""; position: absolute; left: 0; top: .8mm;
  width: 5.5mm; height: 5.5mm; border: 2px solid #000; }
ul.look .en { display: block; font-size: 9.3pt; font-weight: 400; margin-top: .5mm;
  line-height: 1.3; }
table.say { margin-top: 4mm; width: 100%; border-collapse: collapse; }
table.say td { border-bottom: 1px dotted #000; padding: 2mm 2mm 2mm 0;
  vertical-align: baseline; }
table.say .th { font-size: 14.5pt; font-weight: 700; width: 52mm; }
table.say .rtgs { font-size: 9pt; font-style: italic; width: 42mm; }
table.say .en { font-size: 10.2pt; }
.saynote { margin-top: 3mm; font-size: 9.8pt; }
.saynote .th { display: block; font-size: 9.6pt; margin-top: .8mm; }
.qrwrap { margin-top: 3.2mm; display: flex; gap: 4.5mm; align-items: center;
  border: 3px solid #000; padding: 2.8mm 4mm; }
.qrwrap img { width: 23mm; height: 23mm; }
.qrwrap .site { font-size: 13.5pt; font-weight: 700; letter-spacing: .01em;
  line-height: 1.25; }
.qrwrap p { font-size: 9.4pt; margin-top: 1.2mm; }
.qrwrap p.th { font-size: 9.2pt; }
.spacer { flex: 1; }
.foot { margin-top: 3mm; display: flex; justify-content: space-between;
  align-items: flex-end; font-size: 9.5pt; }
.foot .site { font-size: 14pt; font-weight: 700; }
.cut { margin-top: 2.4mm; border-top: 1px dashed #000; padding-top: 1.6mm;
  font-size: 8.8pt; }
"""


# A sheet that prints baht bands nobody has walked says so on both sides, in
# black, until somebody walks them. Straight from make_handouts.py's treatment
# of the unverified Shan: the banner is not decoration, and the flag that drops
# it lives in the data file, not here.
STAMP = {
    "prices": (
        "ราคายังไม่ได้สำรวจจริง — ห้ามแจกจนกว่าจะเดินเก็บราคาก่อน",
        "DRAFT — PRICES NOT YET CHECKED. The baht bands on this sheet are a read of "
        "the market, not walked data. Do not photocopy or hand out until someone has "
        "read rate boards on three streets.",
    ),
}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def find_chrome():
    for c in CHROMES:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Chromium found — install one, or edit CHROMES in this file.")


def qr_data_uri(url):
    """A QR for the page this sheet points at — not the LINE QR.

    Error correction H and a fat scale, because these get photocopied and the
    copy is what people actually scan.
    """
    try:
        import segno
    except ImportError:
        return ""
    buf = io.BytesIO()
    segno.make(url, error="h").save(buf, kind="png", scale=9, border=2)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# Injected only by --measure. page_count() tells you a sheet spilled;
# this tells you which side and by how many millimetres, which is the
# difference between one edit and six.
PROBE = """<script>window.addEventListener('load',function(){
var o=[];document.querySelectorAll('.page').forEach(function(p,i){
var h=p.getBoundingClientRect().height,s=p.scrollHeight;
o.push('side'+(i+1)+' over '+((s-h)/(96/25.4)).toFixed(1)+'mm');});
document.title='PROBE '+o.join(' | ');});</script>"""


def measure(chrome, html):
    """Per-side overflow in millimetres, measured in the browser that renders it."""
    import re
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "probe.html"
        src.write_text(html.replace("</body>", PROBE + "</body>"), encoding="utf-8")
        out = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=3000", "--window-size=794,1123",
             "--dump-dom", src.as_uri()],
            capture_output=True, text=True).stdout
    m = re.search(r"<title>PROBE ([^<]*)</title>", out)
    return m.group(1) if m else "could not measure"


def page_count(pdf):
    """Pages in the rendered PDF, counted off the page tree.

    The format is two sides of one A4 and nothing else. A third page means the
    copy has outgrown the sheet, which is easy to do by adding one term and
    impossible to notice by reading the JSON. Cheap check, caught early.
    """
    blob = pdf.read_bytes()
    kids = blob.count(b"/Type /Page\n") + blob.count(b"/Type /Page ")
    return kids or blob.count(b"/Contents")


def term_cell(r):
    out = f'<span class="th">{esc(r["th"])}'
    if r.get("lanna"):
        out += ' <span class="star">★</span>'
    out += "</span>"
    if r.get("th_alt"):
        out += f'<span class="alt">{esc(r["th_alt"])}</span>'
    meta = []
    if r.get("rtgs"):
        meta.append(f'<i>{esc(r["rtgs"])}</i>')
    if r.get("gloss"):
        meta.append(esc(r["gloss"]))
    if meta:
        out += '<span class="meta">' + " · ".join(meta) + "</span>"
    return out


def desc_cell(r):
    """The tag strip, when the row has one, then the prose."""
    out = ""
    if r.get("tags"):
        out += '<span class="tags">' + esc(r["tags"]) + "</span>"
    return out + esc(r["en"])


def block_html(b):
    rows = "".join(
        f'<div class="row"><div class="term">{term_cell(r)}</div>'
        f'<div class="desc">{desc_cell(r)}</div></div>'
        for r in b["rows"])
    note = ""
    if b.get("note_en"):
        note = (f'<div class="bnote">{esc(b["note_en"])} '
                f'<span class="th">{esc(b.get("note_th"))}</span></div>')
    return (f'<div class="block"><div class="bhead">{esc(b["heading_th"])} — '
            f'<span class="en">{esc(b["heading_en"])}</span></div>'
            f"{note}{rows}</div>")


def sheet_html(s, qr, stamped=False):
    head = ('<div class="rule"></div>'
            '<div class="brandrow"><b>🐜 มดแดง Mot Dang</b>'
            "<span>motdang.net</span></div>")
    banner, pcls = "", "page"
    if stamped:
        th, en = STAMP[s["stamp"]]
        banner = f'<div class="unverified">{esc(th)}<span>{esc(en)}</span></div>'
        pcls = "page stamped"

    front_blocks = [b for b in s["blocks"] if b.get("page") != "back"]
    back_blocks = [b for b in s["blocks"] if b.get("page") == "back"]
    blocks = "".join(block_html(b) for b in front_blocks)
    lanna_key = ""
    if any(r.get("lanna") for b in front_blocks for r in b["rows"]):
        lanna_key = ('<div class="lannakey">★ Northern — a Lanna speciality. '
                     'You are in the right province for it. '
                     '★ ล้านนา — เป็นของทางเหนือ</div>')

    # Sections are all optional, render in this order, and each one may sit on
    # either side: page: "front" pulls it up beside the blocks. The recognition
    # sheet carries plaque + look; the money sheet leads with the price table,
    # which is the reason anybody picked that one up. No sheet needs to know
    # about another's furniture.
    def h2(sec):
        return (f'<h2>{esc(sec["heading_en"])}'
                f'<span class="th">{esc(sec["heading_th"])}</span></h2>')

    front_parts, parts = [], ["".join(block_html(b) for b in back_blocks)]

    def place(sec, html):
        (front_parts if sec.get("page") == "front" else parts).append(html)

    pl = s.get("plaque")
    if pl:
        place(pl, h2(pl) + f"""<div class="box"><p>{esc(pl['body_en'])}
<span class="th">{esc(pl['body_th'])}</span></p>
<div class="plaqueword"><b>{esc(pl['words_th'])}</b>
<i>{esc(pl['words_rtgs'])}</i><span>{esc(pl['words_en'])}</span></div></div>""")

    lk = s.get("look")
    if lk:
        looks = "".join(f'<li>{esc(th)}<span class="en">{esc(en)}</span></li>'
                        for th, en in lk["items"])
        place(lk, h2(lk) + f'<ul class="look">{looks}</ul>')

    pr = s.get("prices")
    if pr:
        cols = "".join(f"<th>{esc(c)}</th>" for c in pr["cols"])
        rows = "".join(
            f'<tr><td class="kind"><b>{esc(r[0])}</b><span>{esc(r[1])}</span></td>'
            + "".join(f"<td>{esc(v)}</td>" for v in r[2:]) + "</tr>"
            for r in pr["rows"])
        addons = "".join(
            f'<tr><td class="th">{esc(a[0])}</td><td>{esc(a[1])}</td>'
            f'<td class="amt">{esc(a[2])}</td></tr>' for a in pr["addons"])
        place(
            pr,
            h2(pr)
            + f'<table class="prices"><tr><th class="kind"></th>{cols}</tr>{rows}</table>'
            + f'<table class="addons">{addons}</table>'
            + f'<div class="pricenote">{esc(pr["note_en"])}'
              f'<span class="th">{esc(pr["note_th"])}</span></div>'
            + f'<div class="aob">{esc(pr["aob_en"])}'
              f'<span class="th">{esc(pr["aob_th"])}</span></div>')

    tp = s.get("tips")
    if tp:
        items = "".join(f'<li>{esc(th)}<span class="en">{esc(en)}</span></li>'
                        for th, en in tp["items"])
        place(tp, h2(tp) + f'<ul class="tips">{items}</ul>')

    sy = s.get("say")
    if sy:
        says = "".join(
            f'<tr><td class="th">{esc(th)}</td><td class="rtgs">{esc(rt)}</td>'
            f'<td class="en">{esc(en)}</td></tr>' for th, rt, en in sy["items"])
        place(
            sy,
            h2(sy) + f'<table class="say">{says}</table>'
            f'<div class="saynote">{esc(sy["note_en"])}'
            f'<span class="th">{esc(sy["note_th"])}</span></div>')

    front = f"""<div class="{pcls}">{banner}{head}
<div class="who">{esc(s['audience_en'])}<span class="th">{esc(s['audience_th'])}</span></div>
<h1>{esc(s['title_en'])}<span class="th">{esc(s['title_th'])}</span></h1>
<div class="lede">{esc(s['lede_en'])}<span class="th">{esc(s['lede_th'])}</span></div>
{blocks}
{"".join(front_parts)}
{lanna_key}
<div class="spacer"></div>
<div class="foot"><span>{esc(s['glyph'])} {esc(s['title_th'])}</span>
<span class="site">motdang.net</span></div>
</div>"""

    qr_img = f'<img src="{qr}" alt="QR code for {esc(s["url"])}">' if qr else ""

    back = f"""<div class="{pcls}">{banner}{head}
{"".join(parts)}
<div class="qrwrap">{qr_img}
<div><span class="site">motdang.net</span>
<p>{esc(s['url_label_en'])}</p>
<p class="th">{esc(s['url_label_th'])}</p></div></div>
<div class="spacer"></div>
<div class="foot"><span>🐜 มดแดง · motdang.net</span>
<span>{esc(s['audience_th'])}</span></div>
<div class="cut">{esc(s['foot_th'])} · {esc(s['foot_en'])}</div>
</div>"""

    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f"<style>{CSS}</style></head><body>{front}{back}</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*", help="sheet keys; default is all")
    ap.add_argument("--html", action="store_true", help="also keep the HTML")
    ap.add_argument("--measure", action="store_true",
                    help="report per-side overflow in mm instead of guessing")
    args = ap.parse_args()

    doc = json.loads(
        (ROOT / "data" / "curated" / "reader_sheets.json").read_text())
    sheets = doc["sheets"]
    verified = {"prices": bool(doc.get("_pricesVerified"))}

    chrome = find_chrome()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="reader-"))

    bad = []
    wanted = [s for s in sheets if not args.keys or s["key"] in args.keys]
    if not wanted:
        sys.exit(f"no such sheet. keys: {', '.join(s['key'] for s in sheets)}")

    for s in wanted:
        qr = qr_data_uri(s["url"])
        if not qr:
            print("warning: segno not installed — printing without the QR")
        stamped = bool(s.get("stamp")) and not verified.get(s["stamp"], False)
        html = sheet_html(s, qr, stamped)
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
        if args.measure:
            print(f"  {s['key']}: {measure(chrome, html)}")
        pages = page_count(dest)
        note = ""
        if pages != 2:
            note = (f"  [{pages} pages, wanted 2 — the copy has outgrown the "
                    f"sheet; cut words, do not shrink the Thai]")
            bad.append(s["key"])
        if stamped:
            note += "  [STAMPED — do not distribute]"
        print(f"  {dest.relative_to(ROOT)}{note}")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(wanted)} sheet(s) -> {OUT}")
    if any(s.get("stamp") == "prices" for s in wanted) and not verified["prices"]:
        print("Prices are unwalked: set _pricesVerified true in reader_sheets.json "
              "once somebody has read rate boards on three streets, then re-run to "
              "drop the stamp.")
    if bad:
        sys.exit("These sheets are not two sides of one A4: " + ", ".join(bad))


if __name__ == "__main__":
    main()
