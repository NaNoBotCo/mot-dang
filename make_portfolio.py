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
import shutil
import subprocess
import tempfile
from pathlib import Path

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
"""


def html() -> str:
    qr_mot = (QR / "motdang_net.svg").read_text(encoding="utf-8")
    qr_def = (QR / "defiant_to.svg").read_text(encoding="utf-8")
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
</div></body></html>"""


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
