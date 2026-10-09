#!/usr/bin/env python3
"""The fridge-door sheet — assets/chuai/chuai.pdf. WO-57 item 3.

WHY PAPER, for the third time in this repo and the first time it is literal.
make_handouts.py says a sheet of A4 cannot be disabled or down-ranked;
make_reader_sheets.py says somebody in a hurry is on a footpath, not on the
site. This one says the plainer thing: in a flood, a quake or a long outage
the phone is the first thing to go and the second thing to run out. A sheet
taped inside a kitchen door needs no power, no signal and no account, and it
photocopies for a neighbour who has none of those either.

WHAT IS ON IT, and what deliberately is not:
  FRONT   the numbers, at a size somebody reads across a room without their
          glasses, each naming the agency that issues it. Then the QR to
          /chuai.html and the one sentence that matters about it — open it
          once now, and it answers with no signal later.
  BACK    the Thai PCD PM2.5 bands, imported from importers/make_air.py so
          the paper and the site cannot disagree; the state hospitals of both
          provinces, whose Thai names carry their own amphoe; and a ruled
          box to write in the numbers no directory can know — the neighbour,
          the landlord, the local รพ.สต.
  NOT ON IT   no triage, no "what to do if", no reading, no forecast. A
          printed sheet cannot be corrected, so nothing goes on it that
          changes: only nationally-issued numbers, the standing band table,
          and names. data/curated/emergency.json wrote that rule first.

Black only, no grey type, no background fills — it has to survive a
third-generation photocopy and a bad printer, which is the same print
discipline as the other two sheets and the reason this shares their
helpers rather than re-deciding any of it.

    python3 make_chuai_sheet.py            # assets/chuai/chuai.pdf
    python3 make_chuai_sheet.py --html     # keep the HTML to hand-edit
    python3 make_chuai_sheet.py --measure  # per-side overflow in mm
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

# The print rig is already right; do not re-decide it here.
from make_reader_sheets import (esc, find_chrome, measure,  # noqa: E402
                                page_count, qr_data_uri)
from make_air import BANDS  # noqa: E402

OUT = ROOT / "assets" / "chuai"
URL = "https://motdang.net/chuai.html"

EMERGENCY = json.loads((ROOT / "data" / "curated" / "emergency.json").read_text())

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 210mm; }
body {
  font-family: "Noto Sans Thai", "IBM Plex Sans Thai", "Sarabun", "Thonburi",
    "Arial Unicode MS", Arial, sans-serif;
  color: #000; background: #fff; font-size: 11pt; line-height: 1.4;
}
.page { width: 210mm; height: 297mm; padding: 11mm 13mm 9mm;
  position: relative; page-break-after: always;
  display: flex; flex-direction: column; }
.page:last-child { page-break-after: auto; }
.rule { border-top: 3px solid #000; border-bottom: 3px solid #000;
  height: 3px; padding-top: 3px; }
.brandrow { display: flex; justify-content: space-between; align-items: baseline;
  margin-top: 2.2mm; font-size: 10pt; letter-spacing: .04em; }
.brandrow b { font-size: 14pt; }
h1 { font-size: 23pt; line-height: 1.1; margin-top: 3mm; }
h1 .en { display: block; font-size: 13pt; font-weight: 400; margin-top: 1mm; }

/* ---- the numbers. This is the whole reason the sheet exists, so it gets
   the whole top of the front and the biggest type on either side. ---- */
.num { display: flex; align-items: baseline; gap: 5mm;
  border: 2.5px solid #000; border-radius: 3mm; padding: 2.4mm 4mm;
  margin-top: 2.8mm; page-break-inside: avoid; }
.num .tel { flex: 0 0 38mm; font-size: 34pt; font-weight: 700;
  letter-spacing: .01em; line-height: 1; }
.num .what { flex: 1; }
.num .what b { display: block; font-size: 13.5pt; line-height: 1.25; }
.num .what .en { display: block; font-size: 10.5pt; font-weight: 400; }
.num .what .note { display: block; font-size: 9pt; margin-top: .8mm; }
.issuers { margin-top: 3mm; font-size: 8.6pt; line-height: 1.35; }

.qrwrap { display: flex; gap: 6mm; align-items: center; margin-top: 4mm;
  border: 2px solid #000; padding: 3mm 4mm; }
.qrwrap img { width: 32mm; height: 32mm; }
.qrwrap .say b { font-size: 12.5pt; display: block; }
.qrwrap .say .en { display: block; font-size: 9.6pt; margin-top: 1mm; }
.qrwrap .say .url { display: block; font-size: 11pt; font-weight: 700;
  margin-top: 1.4mm; letter-spacing: .02em; }

h2 { font-size: 13pt; border-top: 2.5px solid #000;
  border-bottom: 1px solid #000; padding: 1.3mm 0; margin-top: 4mm; }
h2 .en { font-weight: 400; font-size: 9.8pt; }

table.bands { width: 100%; border-collapse: collapse; margin-top: 1.5mm; }
table.bands td { border-bottom: 1px dotted #000; padding: 1.5mm 0;
  vertical-align: baseline; font-size: 10.5pt; }
/* The swatch carries the band TWICE: the colour, for a colour printer and
   for matching the app and the roadside sign, and a stepped black bar inside
   it, because this sheet's whole promise is that it survives a photocopier —
   and five colour fills go to five indistinguishable greys the moment it
   does. Width is the one signal a bad copy cannot flatten. */
table.bands td.sw { width: 18mm; }
table.bands td.sw span { display: block; height: 5.2mm; border: 1.5px solid #000;
  position: relative; }
table.bands td.sw span i { position: absolute; left: 0; top: 0; bottom: 0;
  background: #000; }
table.bands td.rng { width: 30mm; font-weight: 700;
  font-variant-numeric: tabular-nums; }
table.bands td.nm b { font-size: 11pt; }
table.bands td.nm span { font-size: 9pt; }

/* Four columns, not three: forty-five names have to share what is left of
   the back after the band table, and the names are the one thing here that
   may be set small — a number may not. */
.hosp { columns: 4; column-gap: 5mm; margin-top: 1.5mm; font-size: 8.1pt;
  line-height: 1.3; }
.hosp .p { break-inside: avoid; margin-bottom: 1.6mm; }
.hosp .p b { display: block; font-size: 9pt; border-bottom: 1px solid #000;
  margin-bottom: .8mm; }
.hosp div.h { break-inside: avoid; }

.mine { margin-top: 3mm; border: 2px solid #000; padding: 2.6mm 3.4mm; }
.mine b { font-size: 11.5pt; }
.mine .en { font-size: 9.4pt; font-weight: 400; }
.mine .lines { margin-top: 2mm; }
.mine .lines div { border-bottom: 1px solid #000; height: 8mm; }

.note { margin-top: 2.6mm; font-size: 8.6pt; line-height: 1.35; }
.spacer { flex: 1 1 auto; }
.foot { display: flex; justify-content: space-between; font-size: 9pt;
  border-top: 2px solid #000; padding-top: 1.6mm; }
.cut { margin-top: 1.6mm; font-size: 8pt; text-align: center;
  border-top: 1px dashed #000; padding-top: 1.2mm; }
"""


def head():
    return ('<div class="rule"></div>'
            '<div class="brandrow"><b>🐜 มดแดง Mot Dang</b>'
            "<span>motdang.net</span></div>")


def numbers_html():
    out = []
    for n in EMERGENCY["numbers"]:
        note = ""
        if n.get("note_th") or n.get("note_en"):
            note = (f'<span class="note">{esc(n.get("note_th"))}'
                    f' · {esc(n.get("note_en"))}</span>')
        out.append(
            f'<div class="num"><div class="tel">{esc(n["tel"])}</div>'
            f'<div class="what"><b>{esc(n["th"])}</b>'
            f'<span class="en">{esc(n["en"])}</span>{note}</div></div>')
    return "".join(out)


def bands_html():
    """The Thai PCD PM2.5 bands, from the same table the site colours by.

    Ranges are read off the ceilings rather than typed, so the paper cannot
    drift from importers/make_air.py — the failure this whole repo keeps
    finding is two copies of one fact."""
    rows, low = [], 0.0
    for ceiling, key, th, en, colour in BANDS:
        rng = (f"{low:g}–{ceiling:g}" if ceiling != float("inf")
               else f"{low:g}+")
        rows.append(
            f'<tr><td class="sw"><span style="background:{esc(colour)}">'
            f'<i style="width:{20 * (len(rows) + 1)}%"></i></span></td>'
            f'<td class="rng">{esc(rng)}</td>'
            f'<td class="nm"><b>{esc(th)}</b> <span>{esc(en)}</span></td></tr>')
        low = ceiling
    return f'<table class="bands">{"".join(rows)}</table>'


def hospitals_html():
    """State hospitals of both provinces, by name.

    Thai community hospitals are named for the amphoe they serve — โรงพยาบาล
    สันทราย is the Sansai hospital — so a plain alphabetical column IS the
    district list a Thai reader wants, and it needs no boundary file this
    repo does not hold. Only sector=state: a private hospital's name on an
    emergency sheet is a bill somebody did not choose."""
    out = []
    for key, th, en in (("cm", "เชียงใหม่", "Chiang Mai"),
                        ("cr", "เชียงราย", "Chiang Rai")):
        rows = json.loads((ROOT / "data" / "canonical" / f"{key}.json").read_text())
        names = sorted({
            (r.get("name") or r.get("nameTh") or "").strip()
            for r in rows
            if "hospital" in (r.get("sub") or [])
            and (r.get("attrs") or {}).get("sector") == "state"
            and (r.get("name") or r.get("nameTh"))})
        cells = "".join(f'<div class="h">{esc(n)}</div>' for n in names)
        out.append(f'<div class="p"><b>{esc(th)} · {esc(en)} ({len(names)})</b>'
                   f"{cells}</div>")
    return f'<div class="hosp">{"".join(out)}</div>'


def sheet_html(qr):
    issuers = " · ".join(sorted({n["issuer"] for n in EMERGENCY["numbers"]}))
    qr_img = f'<img src="{qr}" alt="QR code for {esc(URL)}">' if qr else ""

    front = f"""<div class="page">{head()}
<h1>เบอร์ที่ควรติดไว้<span class="en">The numbers worth keeping on the wall</span></h1>
{numbers_html()}
<div class="issuers">เบอร์ออกโดย · Numbers issued by {esc(issuers)}</div>
<div class="qrwrap">{qr_img}<div class="say">
<b>เปิดครั้งเดียว แล้วใช้ได้ตอนไม่มีสัญญาณ</b>
<span class="en">Open this page once on your phone and it keeps working with no
signal: the numbers, and the nearest hospital, health station, pharmacy, fuel
and drinking water — searched on your own device.</span>
<span class="url">motdang.net/chuai.html</span></div></div>
<div class="spacer"></div>
<div class="foot"><span>🐜 เบอร์ที่ควรติดไว้</span>
<span class="site">motdang.net/chuai.html</span></div>
</div>"""

    back = f"""<div class="page">{head()}
<h2>ค่าฝุ่น PM2.5 อ่านยังไง <span class="en">Reading the PM2.5 number — Thailand PCD bands, µg/m³</span></h2>
{bands_html()}
<div class="note">ค่าที่ประกาศเป็นค่าเฉลี่ย 24 ชั่วโมง แถบสีนี้เป็นเกณฑ์ของกรมควบคุมมลพิษ ·
Bands are the Thai Pollution Control Department's own, on the 24-hour average.
แผ่นนี้บอกว่าตัวเลขแปลว่าอะไร ไม่ได้บอกว่าวันนี้เท่าไร — ค่าปัจจุบันอยู่ที่ motdang.net/chuai.html ·
This sheet says what the number means, never what today's number is.</div>
<h2>โรงพยาบาลรัฐ <span class="en">State hospitals — the name carries the amphoe</span></h2>
{hospitals_html()}
<div class="mine"><b>เบอร์ของเราเอง <span class="en">— our own numbers</span></b>
<div class="lines"><div></div><div></div><div></div></div></div>
<div class="note">เขียนเบอร์ที่ไม่มีในสารบัญไหนลงตรงนี้ — เพื่อนบ้าน เจ้าของบ้าน รพ.สต. ใกล้บ้าน ·
The numbers no directory can hold: the neighbour, the landlord, your own
health station.</div>
<div class="spacer"></div>
<div class="foot"><span>🐜 มดแดง · motdang.net</span>
<span>ถ่ายเอกสารแจกได้ · copy this and give it away</span></div>
<div class="cut">แผ่นนี้ไม่ใช่คำแนะนำทางการแพทย์ เป็นเบอร์และชื่อเท่านั้น ·
This sheet is numbers and names, never medical advice.</div>
</div>"""

    return ('<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">'
            f"<style>{CSS}</style></head><body>{front}{back}</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true", help="also keep the HTML")
    ap.add_argument("--measure", action="store_true",
                    help="report per-side overflow in mm instead of guessing")
    args = ap.parse_args()

    chrome = find_chrome()
    OUT.mkdir(parents=True, exist_ok=True)
    qr = qr_data_uri(URL)
    if not qr:
        print("warning: segno not installed — printing without the QR")  # stylecheck: allow — console output
    html = sheet_html(qr)
    if args.html:
        (OUT / "chuai.html").write_text(html, encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="chuai-"))
    src = tmp / "chuai.html"
    src.write_text(html, encoding="utf-8")
    dest = OUT / "chuai.pdf"
    subprocess.run([
        chrome, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--print-to-pdf=" + str(dest),
        src.as_uri()], check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if args.measure:
        print("  overflow:", measure(chrome, html))
    pages = page_count(dest)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  {dest.relative_to(ROOT)}  ({pages} pages)")
    if pages != 2:
        sys.exit("This sheet is not two sides of one A4 — cut words, "
                 "do not shrink the numbers.")


if __name__ == "__main__":
    main()
