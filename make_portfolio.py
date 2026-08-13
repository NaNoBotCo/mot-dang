#!/usr/bin/env python3
"""One A4 sheet to hand a prospective venue partner — assets/handouts/portfolio.pdf

The recruitment handouts (make_handouts.py) ask people to JOIN the directory.
This sheet is the other conversation: a clinic or shop we already patronize,
being told who we are and why we'd like to photograph and write about them.
It rides the same rails — Thai leads, black on white, survives a photocopier,
Chrome shapes the Thai — and it names the bearer as our coordinator, so the
person handing it over arrives introduced, not cold.

QRs come from ClubWheel's from-scratch encoder (qr.mjs, Vision-verified):
    cd ../clubwheel && node -e "import('./src/lib/qr.mjs').then(m => { ... })"
regenerate into assets/qr/ if the URLs ever change.

    python3 make_portfolio.py
"""
import base64
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_handouts import find_chrome

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "handouts"
QR = ROOT / "assets" / "qr"

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 210mm; }
body { font-family: "Noto Sans Thai", "IBM Plex Sans Thai", "Sarabun",
  "Arial Unicode MS", Arial, sans-serif; color: #000; background: #fff;
  font-size: 11.5pt; line-height: 1.5; }
.page { width: 210mm; height: 297mm; padding: 16mm 16mm 14mm;
  display: flex; flex-direction: column; overflow: hidden; }
.rule { border-top: 3px solid #000; border-bottom: 3px solid #000;
  height: 3px; padding-top: 3px; }
.brandrow { display: flex; justify-content: space-between; align-items: baseline;
  margin-top: 4mm; font-size: 10.5pt; letter-spacing: .04em; }
.brandrow b { font-size: 15pt; }
h1 { font-size: 24pt; line-height: 1.25; margin-top: 5mm; font-weight: 700; }
h1 .en { display: block; font-size: 13pt; font-weight: 400; margin-top: 2.5mm;
  color: #222; }
.lede { margin-top: 3mm; font-size: 12pt; }
.lede .en { display: block; margin-top: 2mm; font-size: 10.5pt; color: #222; }
.props { margin-top: 6mm; display: flex; flex-direction: column; gap: 5mm; }
.prop { display: flex; gap: 7mm; align-items: flex-start; }
.prop .qr { flex: 0 0 40mm; }
.prop .qr svg { width: 40mm; height: 40mm; border: 2px solid #000; display: block; }
.prop .qr .cap { text-align: center; font-size: 12pt; font-weight: 700;
  margin-top: 1.5mm; }
.prop h2 { font-size: 16pt; }
.prop h2 .en { font-size: 11pt; font-weight: 400; color: #222; margin-left: 2mm; }
.prop p { margin-top: 2mm; font-size: 11.5pt; }
.prop p .en { display: block; font-size: 10pt; color: #222; margin-top: 1mm; }
.offer { margin-top: 6mm; border: 3px solid #000; padding: 4mm 5mm; }
.offer h3 { font-size: 14pt; }
.offer h3 .en { font-size: 10.5pt; font-weight: 400; color: #222; margin-left: 2mm; }
.offer ul { margin-top: 3mm; list-style: none; }
.offer li { padding-left: 8mm; position: relative; margin-bottom: 2mm;
  font-size: 11.5pt; }
.offer li:before { content: "✦"; position: absolute; left: 0; }
.offer li .en { display: block; font-size: 9.5pt; color: #222; margin-top: .5mm; }
.spacer { flex: 1; }
.bearer { border: 2px solid #000; padding: 3.5mm 5mm; font-size: 11.5pt;
  font-weight: 700; }
.bearer .en { display: block; font-weight: 400; font-size: 10pt; color: #222;
  margin-top: 1mm; }
.foot { margin-top: 5mm; display: flex; justify-content: space-between;
  align-items: flex-end; font-size: 10pt; }
.foot .site { font-size: 13pt; font-weight: 700; }
/* The coverage strip. Print rules the same as the rest of this sheet: it has
   to survive a black-and-white photocopier, so the ground is washed almost to
   paper and every place is a solid black dot — the dots are what has to
   arrive, and they are the only ink that matters here. */
/* The back of the sheet. The front was already a full A4 — squeezing the map
   in under the offer pushed the bearer line and the footer off the bottom, and
   the bearer line is the mechanism the whole sheet runs on. So the map gets a
   side of its own, which is also the size it deserves. */
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
.coverage img { display: block; width: 100%; border: 2px solid #000; }
.coverage h2 { font-size: 19pt; margin-bottom: 2mm; }
.coverage h2 .en { font-size: 12pt; font-weight: 400; color: #222;
  margin-left: 2mm; }
.coverage .cap { margin-top: 3mm; font-size: 11pt; }
.coverage .cap .en { display: block; font-size: 9.5pt; color: #222;
  margin-top: 1mm; }
"""


def coverage_strip() -> str:
    """Every place we hold, printed on the ground it stands on.

    The sheet claims ten thousand places in two provinces. A sentence saying
    so is a sentence; the same claim as a map is a shape a shopkeeper can
    recognise — their own town, with the density of it visible — and it is the
    one picture on this sheet that could not be faked by any small team that
    had not done the walking. Nothing here is stated that the data does not
    already say: one dot per record, no smoothing.

    Returns "" without Pillow or a tile archive, and the sheet prints exactly
    as it did before.
    """
    try:
        from PIL import Image, ImageDraw
        import map_ground
    except ImportError:
        return ""
    g = map_ground.shared()
    if not g.available:
        return ""
    recs = []
    for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
        recs += [r for r in json.loads(f.read_text())
                 if r.get("lat") is not None and r.get("lng") is not None]
    if not recs:
        return ""
    # A whole side of A4, so the two provinces get room to be two provinces.
    W, H = 1500, 1000
    lats = sorted(r["lat"] for r in recs)
    lngs = sorted(r["lng"] for r in recs)
    lo, hi = int(len(lats) * 0.01), int(len(lats) * 0.99)
    s_, n_ = lats[lo], lats[hi]
    w_, e_ = lngs[lo], lngs[hi]
    pad_la, pad_ln = (n_ - s_) * 0.06, (e_ - w_) * 0.06
    s_, n_, w_, e_ = s_ - pad_la, n_ + pad_la, w_ - pad_ln, e_ + pad_ln
    # Square the frame in projected proportion, or the two provinces come out
    # sheared and neither city is the shape anybody knows.
    kx = math.cos(math.radians((s_ + n_) / 2))
    want = (e_ - w_) * kx / (n_ - s_)
    have = W / float(H)
    if want < have:
        grow = ((n_ - s_) * have / kx - (e_ - w_)) / 2
        w_, e_ = w_ - grow, e_ + grow
    else:
        grow = ((e_ - w_) * kx / have - (n_ - s_)) / 2
        s_, n_ = s_ - grow, n_ + grow
    bbox = (s_, w_, n_, e_)

    def xy(p):
        return ((p[1] - w_) / (e_ - w_) * W, (n_ - p[0]) / (n_ - s_) * H)

    im = Image.new("RGB", (W, H), g.palette["paper"])
    if not g.paint(im, xy, bbox, width_px=W, zoom=g.zoom_for(bbox, W, 256),
                   buildings=False, fade=0.42, contrast=1.2):
        return ""
    d = ImageDraw.Draw(im)
    n_in = 0
    for r in recs:
        if not (s_ <= r["lat"] <= n_ and w_ <= r["lng"] <= e_):
            continue
        n_in += 1
        x, y = xy((r["lat"], r["lng"]))
        d.ellipse([x - 1.9, y - 1.9, x + 1.9, y + 1.9], fill=(20, 14, 10))
    map_ground.scale_bar(im, W / ((e_ - w_) * kx * 111.32))
    map_ground.credit_mark(im)
    out = ROOT / "assets" / "portfolio-coverage.png"
    im.quantize(colors=64, dither=Image.Dither.NONE).save(out, optimize=True)
    uri = "data:image/png;base64," + base64.b64encode(out.read_bytes()).decode()
    n = format(n_in, ",")
    return ('<div class="page coverage">'
            '<div class="rule"></div>'
            '<div class="brandrow"><b>NaNoBotCo</b>'
            '<span>เชียงใหม่ · CHIANG MAI</span></div>'
            '<h2>ที่เราเดินมาแล้ว<span class="en">where we have already walked'
            '</span></h2>'
            '<img src="%s" alt="">'
            '<div class="cap">ทุกจุดคือหนึ่งแห่งในสารบัญ — %s แห่งในกรอบนี้ '
            'เชียงใหม่และเชียงราย เก็บทีละซอย'
            '<span class="en">Every dot is one place on record — %s of them in '
            'this frame. Chiang Mai and Chiang Rai, gathered one soi at a '
            'time.</span></div>'
            '<div class="spacer"></div>'
            '<div class="foot"><span class="site">motdang.net · defiant.to'
            '</span><span>530kings@proton.me</span></div>'
            '<div class="rule"></div></div>'
            % (uri, n, n))


def html() -> str:
    qr_mot = (QR / "motdang_net.svg").read_text(encoding="utf-8")
    qr_def = (QR / "defiant_to.svg").read_text(encoding="utf-8")
    coverage = coverage_strip()
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>
<div class="page">
  <div class="rule"></div>
  <div class="brandrow"><b>NaNoBotCo</b><span>เชียงใหม่ · CHIANG MAI</span></div>

  <h1>เราเล่าเรื่องของดีเมืองเชียงใหม่
    <span class="en">We tell the stories of Chiang Mai's good places —
    in Thai and in English.</span></h1>

  <p class="lede">เราเป็นทีมเล็ก ๆ ในเชียงใหม่ ทำเว็บไซต์แนะนำเมืองสองเว็บ
    ผู้อ่านของเราคือคนเชียงใหม่ และชาวต่างชาติที่มาอยู่ยาวหรือมารักษาตัวที่นี่
    <span class="en">A small Chiang Mai team running two city guides. Our readers
    are locals, long-stay foreigners, and visitors who come to Thailand for
    care and services.</span></p>

  <div class="props">
    <div class="prop">
      <div class="qr">{qr_mot}<div class="cap">motdang.net</div></div>
      <div><h2>มดแดง Mot Dang <span class="en">city directory</span></h2>
        <p>สารบัญเมืองเชียงใหม่–เชียงราย กว่า 10,000 แห่ง — ร้านอาหาร คลินิก วัด
        งานเทศกาลทั้งปี แผนที่ห้องน้ำ และแอปแผนที่ออฟไลน์
        <span class="en">A directory of 10,000+ places across Chiang Mai and
        Chiang Rai — restaurants, clinics, temples, the year's festivals, and
        an offline map app.</span></p></div>
    </div>
    <div class="prop">
      <div class="qr">{qr_def}<div class="cap">defiant.to</div></div>
      <div><h2>Defiant <span class="en">guide for international patients</span></h2>
        <p>เว็บภาษาอังกฤษ แนะนำคลินิกและบริการสุขภาพในไทยให้ชาวต่างชาติ
        ช่วยให้เขาหาคลินิกดี ๆ เจอ และมาถึงพร้อมข้อมูลครบ
        <span class="en">An English-language guide to clinics and health
        services in Thailand, helping international patients find good clinics
        and arrive well-informed.</span></p></div>
    </div>
  </div>

  <div class="offer">
    <h3>สิ่งที่เราอยากชวนทำ <span class="en">what we'd love to do together</span></h3>
    <ul>
      <li>เราเป็นลูกค้าจริง จ่ายเต็มราคาเสมอ — ไม่ขอส่วนลด ไม่ขอของฟรี
        <span class="en">We are real, full-price customers — never asking for
        discounts or freebies.</span></li>
      <li>ถ้าท่านยินดี เราขอถ่ายภาพ/วิดีโอประสบการณ์จริง แล้วเขียนแนะนำลงเว็บของเรา
        โดยไม่มีค่าใช้จ่ายและไม่มีข้อผูกมัดใด ๆ
        <span class="en">With your blessing, we photograph our own visit and
        feature you on our sites — free, with no obligation.</span></li>
      <li>เรายินดีร่วมงานกับร้านและคลินิกที่เราไว้ใจ ในโปรเจกต์ต่อ ๆ ไปอีกมากมาย
        <span class="en">And we're eager to work together on many future
        projects.</span></li>
    </ul>
  </div>

  <div class="spacer"></div>
  <div class="bearer">ผู้ถือเอกสารนี้คือผู้ประสานงานของเรา — ติดต่อผ่านท่านได้เลย
    <span class="en">The bearer of this sheet is our coordinator — you can
    reach us through her.</span></div>
  <div class="foot"><span class="site">motdang.net · defiant.to</span>
    <span>530kings@proton.me</span></div>
  <div class="rule"></div>
</div>
{coverage}
</body></html>"""


def main():
    chrome = find_chrome()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="portfolio-"))
    src = tmp / "portfolio.html"
    src.write_text(html(), encoding="utf-8")
    dest = OUT / "portfolio.pdf"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--print-to-pdf=" + str(dest),
                    src.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"-> {dest.relative_to(ROOT)}")
    docs = ROOT / "docs"
    if docs.is_dir():   # live now; build.py re-copies it on every rebuild
        shutil.copy(dest, docs / "portfolio.pdf")
        print("-> docs/portfolio.pdf (motdang.net/portfolio.pdf)")


if __name__ == "__main__":
    main()
