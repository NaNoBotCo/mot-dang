#!/usr/bin/env python3
"""The app layer: /app.html and the APK beside it.

The phone app is built separately (app/build_data.py then app/build_apk.py —
it needs the Android SDK, which the site build must not depend on). This
layer only PUBLISHES what that build left behind: it copies the signed APK
from app/out/ into docs/app/ and writes the download page. If no APK has
been built yet, it says so and steps aside — the site never breaks over it.

Distribution is the file itself, not a store. Android asks the reader for
one extra nod when installing outside a store; the page walks through that
calmly, in Thai first, and says exactly why this app has nothing to confess:
the map is in the box, location stays on the phone, and a report is one
word with no name on it.

Entry point: emit(globals_of_build, data), same handshake as every layer.
"""
import hashlib
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APK_SRC = ROOT / "app" / "out" / "motdang-hongnam.apk"
APK_NAME = "motdang-hongnam.apk"
WWW = ROOT / "app" / "www"

CSS = """
.apk-alt{display:inline-block;margin:.5rem 0 0;color:#fff;font-size:.9rem;
  text-decoration:underline;text-underline-offset:3px}
.app-hero{background:linear-gradient(135deg,var(--ant) 0%,var(--ant-dark) 100%);
  color:#fff;border-radius:22px;padding:26px 22px;margin:14px 0 18px;
  box-shadow:0 10px 30px rgba(143,42,33,.3)}
.app-hero h2{margin:0 0 6px;font-size:26px}
.app-hero p{margin:0 0 16px;opacity:.92;line-height:1.55}
.apk-btn{display:inline-block;background:linear-gradient(180deg,var(--gold-light),var(--gold));
  color:#3a2c07;font-weight:700;font-size:19px;text-decoration:none;
  padding:16px 28px;border-radius:16px;box-shadow:0 4px 0 #8a5f14;
  transition:transform .12s cubic-bezier(.34,1.56,.64,1)}
.apk-btn:active{transform:translateY(2px) scale(.98);box-shadow:0 2px 0 #8a5f14}
.apk-meta{display:block;margin-top:10px;font-size:12.5px;opacity:.85;word-break:break-all}
.app-steps{counter-reset:s;list-style:none;padding:0;margin:0}
.app-steps li{position:relative;padding:12px 14px 12px 58px;margin:0 0 10px;
  background:var(--card);border:1.5px solid var(--warm-border);border-radius:16px;
  box-shadow:0 2px 0 var(--shadow);line-height:1.55}
.app-steps li::before{counter-increment:s;content:counter(s,thai);
  position:absolute;left:12px;top:10px;width:34px;height:34px;border-radius:12px;
  background:var(--gold-pale);color:#6d5411;font-weight:700;font-size:17px;
  display:grid;place-items:center}
.app-quiet{background:var(--card);border:1.5px solid var(--warm-border);
  border-radius:16px;padding:14px;margin:10px 0;box-shadow:0 2px 0 var(--shadow);
  line-height:1.6}
.app-quiet b.h{display:block;margin-bottom:2px}
"""


def emit(g, data):
    docs, page, bi, esc, att = g["DOCS"], g["page"], g["bi"], g["esc"], g["att"]
    if not APK_SRC.exists():
        return "no APK at app/out/ — run app/build_apk.py; app.html skipped"

    # /app/ is the app itself, served on the open web — the same files the
    # APK carries in its assets. An iPhone has no other way in: Safari's Add
    # to Home Screen plus the service worker gives a reader there the same
    # offline map, without an App Store or a developer account in between.
    (docs / "app").mkdir(exist_ok=True)
    web_files = 0
    for f in sorted(WWW.rglob("*")):
        if not f.is_file() or f.name.startswith("."):
            continue
        dest = docs / "app" / f.relative_to(WWW)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
        web_files += 1

    # motdang.net/near/bathrooms — the link Nan drops in a Facebook comment
    # (2026-10-11). Each reader who taps it lands in the app with the location
    # question already open, so the list sorts from where that reader stands
    # at that minute. The page carries its own preview card for the crawler
    # and hands the reader on; ?near is what app.js reads.
    near_head = (
        '<meta property="og:type" content="website">'
        '<meta property="og:site_name" content="มดแดง Mot Dang">'
        '<meta property="og:title" content="ห้องน้ำใกล้ฉัน · Nearest bathroom">'
        '<meta property="og:description" content="ห้องน้ำ เรียงจากใกล้ที่สุดก่อน · '
        'เชียงใหม่ เชียงราย · Toilets, nearest first — Chiang Mai and Chiang Rai.">'
        '<meta property="og:image" content="https://motdang.net/og/toilets.png">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">')
    for word in ("bathrooms", "bathroom", "toilets", "toilet", "restroom", "restrooms"):
        d = docs / "near" / word
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            '<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex,follow">'
            '<title>ห้องน้ำใกล้ฉัน · Nearest bathroom · มดแดง</title>'
            + near_head +
            '<meta http-equiv="refresh" content="0;url=../../app/?near">'
            '<script>location.replace("../../app/?near")</script>'
            '</head><body><p><a href="../../app/?near">'
            'ห้องน้ำใกล้ฉัน · Nearest bathroom</a></p></body></html>')

    apk_bytes = APK_SRC.read_bytes()
    (docs / "app" / APK_NAME).write_bytes(apk_bytes)
    sha = hashlib.sha256(apk_bytes).hexdigest()
    mb = len(apk_bytes) / 1e6
    m = re.search(r'versionName="([^"]+)"',
                  (ROOT / "app" / "android" / "AndroidManifest.xml").read_text())
    ver = m.group(1) if m else "1.0"

    body = f"""
<h1>📱 {bi("แอปห้องน้ำใกล้ฉัน", "The nearest-toilet app")}</h1>
<div class="app-hero">
  <h2>{esc("แผนที่ทั้งเมือง อยู่ในเครื่อง")}</h2>
  <p>{esc("ถนน อาคาร วัด ตลาด และห้องน้ำทุกหมุดของหน้าเว็บนี้ — ทั้งเชียงใหม่และเชียงราย — "
          "ติดตั้งลงเครื่องครั้งเดียว ใช้ได้ทั้งวันโดยไม่ต้องมีเน็ต "
          "เปิดปุ๊บเรียงให้เลยว่าที่ใกล้ที่สุดอยู่ไหน")}<br>
  <small>{esc("The whole map — streets, buildings, temples, markets and every toilet pin, "
              "for both Chiang Mai and Chiang Rai — installs once and works with no "
              "signal. Open it and the nearest one is already first.")}</small></p>
  <a class="apk-btn" href="app/">{esc("เปิดแอป แล้วใส่ไว้ที่หน้าจอโฮม")} · Open &amp; add to Home Screen</a>
  <a class="apk-alt" href="app/{APK_NAME}" download>⬇️ {esc("หรือดาวน์โหลดไฟล์แอนดรอยด์")} · {mb:.1f} MB</a>
  <span class="apk-meta">{esc("รุ่น")} {esc(ver)} · SHA-256 {sha[:16]}…</span>
</div>

<h2>{bi("วิธีติดตั้ง", "How to install")}</h2>
<ol class="app-steps">
  <li>{bi("กดปุ่มดาวน์โหลดด้านบน แล้วเปิดไฟล์ที่ได้",
          "Tap the download button, then open the file it saves")}</li>
  <li>{bi("เครื่องจะถามหนึ่งครั้งว่า อนุญาตให้ติดตั้งจากเบราว์เซอร์ไหม — กดอนุญาต "
          "ที่ถามเพราะแอปนี้มาจากมดแดงโดยตรง ไม่ได้ผ่านสโตร์",
          "Android asks once whether the browser may install apps — allow it. "
          "It asks because this comes straight from Mot Dang, not through a store")}</li>
  <li>{bi("กดติดตั้ง เสร็จแล้วเปิดได้เลย — แอปจะขอตำแหน่งเพื่อเรียงรายการว่าอะไรใกล้",
          "Tap install and open it. It will ask for location, to sort the list by nearness")}</li>
</ol>

<h2>{bi("ใช้ไอโฟน", "On an iPhone")}</h2>
<div class="app-hero" style="background:linear-gradient(135deg,#1f6b57,#14483a)">
  <h2>{esc("ไม่ต้องโหลดไฟล์ ใส่ลงหน้าจอได้เลย")}</h2>
  <p>{esc("ไอโฟนติดตั้งไฟล์ของแอนดรอยด์ไม่ได้ แต่แอปตัวเดียวกันนี้เปิดในซาฟารีได้ "
          "แล้วกดใส่ไว้ที่หน้าจอโฮม จากนั้นใช้ได้เหมือนกันทุกอย่าง รวมทั้งตอนไม่มีเน็ต")}<br>
  <small>{esc("An iPhone cannot install an Android file — but the same app opens in "
              "Safari, and Add to Home Screen keeps the whole map on the phone. "
              "It works with no signal after that, exactly like the Android one.")}</small></p>
  <a class="apk-btn" href="app/">📲 {esc("เปิดแอปในซาฟารี")} · Open in Safari</a>
</div>
<ol class="app-steps">
  <li>{bi("เปิด motdang.net/app/ ในซาฟารี", "Open motdang.net/app/ in Safari")}</li>
  <li>{bi("กดปุ่มแชร์ข้างล่าง (รูปสี่เหลี่ยมมีลูกศรขึ้น)",
          "Tap the Share button at the bottom (the square with an arrow)")}</li>
  <li>{bi("เลื่อนหา “เพิ่มไปยังหน้าจอโฮม” แล้วกดเพิ่ม — ไอคอนมดแดงจะไปอยู่บนหน้าจอ",
          "Scroll to “Add to Home Screen” and add it — the ant icon lands on your screen")}</li>
</ol>

<h2>{bi("สิ่งที่แอปนี้ไม่ทำ", "What this app does not do")}</h2>
<div class="app-quiet"><b class="h">🗺️ {bi("ไม่เรียกแผนที่จากใคร", "It draws its own map")}</b>
{bi("แผนที่วาดจากข้อมูลในเครื่องทั้งหมด การเปิดดูไม่เรียกหาเซิร์ฟเวอร์แผนที่ใดเลย",
    "Every street and building is drawn from data inside the app. Browsing the map makes no request to any tile server.")}</div>
<div class="app-quiet"><b class="h">📍 {bi("ตำแหน่งใช้เรียงรายการ", "Location sorts the list")}</b>
{bi("ตำแหน่งใช้เรียงรายการในเครื่อง",
    "Your position sorts the list on the device.")}</div>
<div class="app-quiet"><b class="h">🙏 {bi("การบอกต่อส่งแค่คำเดียว", "A report is one word")}</b>
{bi("กดบอกสภาพห้องน้ำ = ส่งรหัสสถานที่กับคำหนึ่งคำจากห้าคำ",
    "Reporting a toilet sends the place id and one word from a closed list of five.")}</div>
<div class="app-quiet"><b class="h">🗂️ {bi("บันทึกของคุณเป็นของคุณ", "Your log is yours")}</b>
{bi("บันทึกว่าใช้ห้องน้ำที่ไหนอยู่ในเครื่องเท่านั้น และปุ่มลบ ลบจริง",
    "The visit log lives on the phone only, and the erase button really erases.")}</div>

<h2>{bi("สองเมือง และสิ่งที่ต่างกัน", "Two cities, and how they differ")}</h2>
<div class="app-quiet">
{bi("แผนที่ถนนกับอาคารครอบคลุมใจกลางเชียงใหม่ (รอบคูเมือง + ๒ กม.) และใจกลางเชียงราย "
    "(หอนาฬิกา ลงมาถึงเซ็นทรัล) — กด 🏙️ ในแอปเพื่อสลับเมือง",
    "The street-and-building map covers the Chiang Mai core (the moat plus 2 km) and "
    "the Chiang Rai core (clock tower down to Central). The 🏙️ button switches cities.")}
<br><br>
{bi("ข้อต่างข้อหนึ่ง: ในเชียงรายยังไม่มีใครปักหมุดห้องน้ำไว้ในแผนที่เปิดเลยสักแห่ง "
    "สิ่งที่แอปแสดงที่นั่นจึงเป็นชั้นของที่พึ่งตามประเภทสถานที่ทั้งหมด "
    "ใครไปยืนหน้าประตูจริงแล้วกดบอกสักคำ คือคนที่เปลี่ยนเรื่องนี้ได้",
    "One difference: nobody has yet mapped a single toilet point in "
    "Chiang Rai in OpenStreetMap, so everything the app shows there is class habit. "
    "The person who stands at the real door and taps one word is the one who changes that.")}
</div>

<p><span class="bi"><span class="th" lang="th">ยังไม่อยากติดตั้งอะไรเลย —
<a href="toilets.html">หน้าเว็บห้องน้ำใกล้ฉัน</a>ตอบคำถามเดียวกัน</span>
<span class="en" lang="en"><span class="th" lang="th"> · </span>Not ready to install
anything? <a href="toilets.html">The web page</a> answers the same
question.</span></span></p>
"""
    _og_card = Path(__file__).resolve().parent / "assets" / "og" / "toilets.png"
    (docs / "app.html").write_text(page(
        "แอปห้องน้ำใกล้ฉัน", body, 0, path="app.html",
        desc="แอปห้องน้ำใกล้ฉัน มดแดง — แผนที่ออฟไลน์ทั้งเมืองเชียงใหม่ ติดตั้งตรงจากมดแดง ไม่ผ่านสโตร์",
        og="og/toilets.png" if _og_card.exists() else None,
        extra_head=f"<style>{CSS}</style>"))
    return (f"app.html + {APK_NAME} ({mb:.1f} MB, v{ver}) + "
            f"/app/ web app ({web_files} files)")


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
