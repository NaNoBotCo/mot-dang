#!/usr/bin/env python3
"""/care.html — ดูแลต่อเนื่อง, the ongoing-care page. WO-25.

WHO THIS IS FOR. Not the visitor with a fever: the person who lives here with
something lifelong and has to keep managing it — a heart rhythm, a thyroid,
menopause, a joint, a kidney — and who often pays out of pocket, in a second
language, while also feeding paperwork to somebody far away (a US insurer, the
VA's Foreign Medical Program, a visa desk). The directory could not answer any
of that on 2026-08-21: `cardiologist`, `menopause`, `endocrinologist`,
`insurance`, `FMP` and `DTV` all returned NOTHING, and the corpus held zero
records carrying menopause, hormone, endocrine, internal-medicine or checkup
vocabulary. OpenStreetMap maps BUILDINGS; ongoing specialist care lives in
DEPARTMENTS, and no crawl was ever going to find a คลินิกต่อมไร้ท่อ that meets
on Monday evenings inside a hospital that is already one pin on the map.

SO THE DEPARTMENTS WERE READ, one hospital site at a time, and what each one
STATES is what this page prints — `data/curated/care.json`, every claim
carrying the sentence it came from, the URL it was read at, and the date.

THE RULE: the desk states; the paper carries its date; nothing is awarded.
No rankings, no "best hospital for X", no named doctors, no medical advice.
A hospital that says nothing about a service gets NOTHING here — absence is
silence, never a "no" — and the silences are printed too, by name, in the
could-not-read table. A directory that shows only its successes is telling
the reader the map is finished.

TWO SILENCES WORTH THE WORDS. The Kasemrad chain site lists 73 centres across
ten branches behind a client-side picker, and its package prices are tagged to
Pathum Thani — reading that as the Sriburin branch's departments would invent
facts about a named hospital, so no claim is made at all. And the Thai
government's own DTV pages could not be read by a plain fetch (React shells and
a nav-only body), so this page carries NO visa requirements: it says it could
not read them and sends the reader to the official portal. Writing visa rules
from memory is exactly the failure this repo has a rule against.
"""
import json

CSS = """
:root{--care-ink:#3a2f28;--care-line:#e4d9cd;--care-tint:#fbf6f0;
--care-state:#2f6b46;--care-quiet:#8a7a62;--care-paper:#b1471f}
.care-intro{font-size:1.05rem;line-height:1.65;max-width:62ch}
.care-lede{margin:.2rem 0 1rem;color:var(--care-ink)}
.care-h{margin:1.9rem 0 .35rem}
.care-note{color:var(--care-quiet);font-size:.92rem;line-height:1.6;max-width:64ch}
.care-card{border:1px solid var(--care-line);border-radius:.85rem;padding:.85rem 1rem 1rem;
margin:.9rem 0;background:var(--care-tint)}
.care-card h3{margin:.1rem 0 .15rem;font-size:1.12rem}
.care-where{color:var(--care-quiet);font-size:.9rem;margin:0 0 .55rem}
.care-where a{color:inherit}
.care-grid{display:grid;gap:.5rem}
.care-row{display:grid;grid-template-columns:minmax(9rem,15rem) 1fr;gap:.15rem .9rem;
padding:.4rem 0;border-top:1px dashed var(--care-line)}
.care-row:first-child{border-top:0}
.care-key{font-weight:600}
.care-hours{color:var(--care-quiet);font-size:.9rem;display:block}
.care-said{display:block;color:var(--care-quiet);font-size:.86rem;line-height:1.5;
margin-top:.15rem;border-left:2px solid var(--care-line);padding-left:.55rem}
.care-said a{color:inherit}
.care-tag{display:inline-block;font-size:.76rem;letter-spacing:.03em;text-transform:uppercase;
border:1px solid var(--care-line);border-radius:.6rem;padding:.05rem .45rem;
color:var(--care-state);background:#fff;margin-left:.3rem;vertical-align:.08em}
.care-tag.paper{color:var(--care-paper)}
.care-contact{margin:.6rem 0 0;font-size:.95rem}
.care-tablewrap{overflow-x:auto}
table.care-tab{border-collapse:collapse;width:100%;font-size:.94rem;min-width:34rem}
table.care-tab th,table.care-tab td{border-bottom:1px solid var(--care-line);
padding:.45rem .6rem;text-align:left;vertical-align:top}
table.care-tab thead th{border-bottom:2px solid var(--care-line);white-space:nowrap}
table.care-gloss td.th{font-size:1.05rem;white-space:nowrap}
table.care-gloss td.rtgs{color:var(--care-quiet);font-style:italic;white-space:nowrap}
@media (max-width:34rem){.care-row{grid-template-columns:1fr}}
"""

# The words on the department board, for a reader who cannot read the board.
# Script · RTGS · what it means — the same instrument as the women's-health
# glossary, aimed at the ongoing-care corridor rather than the OB-GYN one.
GLOSSARY = [
    ("อายุรกรรม", "ayurakam", "internal medicine — the department that manages "
     "long-term illness with medicine rather than surgery. If you have one "
     "lifelong condition and do not know which door, this is usually it."),
    ("อายุรกรรมเฉพาะโรค", "ayurakam chapho rok", "specialist internal medicine — "
     "the sub-clinics (heart, kidney, diabetes) inside อายุรกรรม, usually by "
     "appointment only."),
    ("คลินิกพิเศษ", "khlinik phiset", "the 'special clinic' — a hospital's own "
     "specialists seeing patients OUTSIDE normal hours, for a posted extra fee. "
     "This is the one that makes a working life and a chronic condition fit "
     "together, and it is rarely advertised in English."),
    ("นอกเวลา", "nok wela", "out of hours. Seen as คลินิกนอกเวลา or "
     "คลินิกเฉพาะทางนอกเวลาราชการ — after the government workday ends."),
    ("ต่อมไร้ท่อ", "tom rai tho", "endocrinology — thyroid, diabetes, hormones. "
     "The department behind menopause care as well; see the women's-health page."),
    ("โรคหัวใจ", "rok huachai", "heart disease — a คลินิกโรคหัวใจ is the heart clinic."),
    ("ระบบประสาทและสมอง", "rabop prasat lae samong", "the brain and nervous system."),
    ("เวชระเบียน", "wet rabian", "medical records. The office to ask for a copy "
     "of your own file, and usually where consent forms are signed."),
    ("ใบรับรองแพทย์", "bai raprong phaet", "a medical certificate — the signed "
     "document a visa desk, an insurer or an employer asks for."),
    ("ใบเสร็จรับเงิน", "bai set rap ngoen", "the official receipt. For a foreign "
     "claim you want it itemised — ask for แบบแยกรายการ."),
    ("แยกรายการ", "yaek rai kan", "itemised, line by line. The word that turns a "
     "total into something an insurer will read."),
    ("ประวัติการรักษา", "prawat kan raksa", "treatment history — the record of "
     "what has been done, which is what a continuing-care plan is built from."),
    ("เบิกจ่ายตรง", "boek chai trong", "direct billing — the hospital bills the "
     "scheme instead of the patient. Thai schemes; ask whether yours is one."),
    ("ประกันสังคม", "prakan sangkhom", "Thai social security. Not for most "
     "foreigners paying out of pocket, but it is on every hospital's signage "
     "and worth recognising so you can walk past it."),
    ("ผู้ป่วยนอก", "phu puai nok", "outpatient (OPD). ผู้ป่วยใน / phu puai nai is "
     "inpatient."),
    ("นัด", "nat", "an appointment. รับเฉพาะนัด means by appointment only."),
    ("ศูนย์บริการผู้ป่วยต่างชาติ", "sun borikan phu puai tang chat",
     "international patient service centre — the desk that handles foreign "
     "paperwork and interpreters, where a hospital keeps one."),
]

# Which register keys render as what, in order. Keys are shared with
# importers/specialty.py so this page and the search cannot disagree.
CLINIC_ORDER = [
    ("heart", "โรคหัวใจ", "Heart"),
    ("endocrine", "ต่อมไร้ท่อ", "Endocrine — thyroid, diabetes, hormones"),
    ("internal-med", "อายุรกรรม", "Internal medicine"),
    ("neuro", "ระบบประสาทและสมอง", "Brain & nervous system"),
    ("obgyn", "สูตินรีเวช", "Women's health"),
    ("physio", "กายภาพบำบัด-ฟื้นฟู", "Physiotherapy & rehab"),
    ("kidney", "ไตเทียม-ฟอกไต", "Dialysis"),
    ("checkup", "ตรวจสุขภาพ", "Health check-up"),
]
PAPER_ORDER = [
    ("us_claims", "เอกสารเคลมสหรัฐฯ", "US claim paperwork"),
    ("intl_desk", "ศูนย์ผู้ป่วยต่างชาติ", "International patient desk"),
    ("insurance", "ประกัน", "Insurance"),
    ("records", "เวชระเบียน-ใบรับรอง", "Records & certificates"),
]
CONT_ORDER = [
    ("after_hours", "คลินิกนอกเวลา", "After-hours clinic"),
    ("telemed", "ปรึกษาทางไกล", "Telehealth"),
]


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug = g["place_slug"]
    BASE, DOCS, ROOT = g["BASE"], g["DOCS"], g["ROOT"]
    share_block = g["share_block"]
    PROVINCES = g["PROVINCES"]
    name_of = g["name_of"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    src = ROOT / "data" / "curated" / "care.json"
    if not src.exists():
        return "care.json missing — page not built"
    reg = json.loads(src.read_text(encoding="utf-8"))
    entries, official = reg.get("entries", {}), reg.get("official", {})

    (DOCS / "care.css").write_text(CSS)

    # A register entry names catalogue ids; resolve them to real pages so the
    # card can send the reader to the place record. An id that no longer exists
    # (a re-crawl, a merge) simply does not link — it never invents a target.
    byid = {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            byid[r["id"]] = (p["key"], r)

    def place_link(ids):
        for pid in ids or []:
            hit = byid.get(pid)
            if hit:
                k, r = hit
                return f'<a href="{att(k)}/p/{att(place_slug(r))}.html">{esc(name_of(r))}</a>'
        return ""

    def said(block):
        """The sentence this claim was read from, its url, and its date. Every
        line on this page can be checked without leaving it."""
        ev, s, f = block.get("evidence"), block.get("src", ""), block.get("fetched", "")
        if not ev:
            return ""
        where = (f'<a href="{att(s)}" rel="noopener nofollow">{esc(s[:60])}</a>'
                 if s.startswith("http") else esc(s))
        return (f'<span class="care-said">{bi("ที่หน้าเว็บเขียนว่า", "read on the page")}: '
                f'“{esc(ev[:260])}” — {where} · {esc(f)}</span>')

    def rows(block_map, order, tag_class=""):
        out = []
        for key, th, en in order:
            b = (block_map or {}).get(key)
            if not b:
                continue
            hours = (f'<span class="care-hours">{esc(b["hours"])}</span>'
                     if b.get("hours") else "")
            label = bi(b.get("th") or th, b.get("en") or en)
            tag = (f'<span class="care-tag {tag_class}">'
                   f'{bi("บอกเอง", "stated")}</span>')
            out.append(f'<div class="care-row"><div class="care-key">{bi(th, en)}</div>'
                       f'<div>{label}{tag}{hours}{said(b)}</div></div>')
        return "".join(out)

    cards, n_claims = [], 0
    for key, e in entries.items():
        body = (rows(e.get("clinics"), CLINIC_ORDER)
                + rows(e.get("paperwork"), PAPER_ORDER, "paper")
                + rows(e.get("continuity"), CONT_ORDER))
        n_claims += (len(e.get("clinics") or {}) + len(e.get("paperwork") or {})
                     + len(e.get("continuity") or {}))
        c = e.get("contacts") or {}
        bits = []
        if c.get("phone"):
            bits.append(f'<a href="tel:{att(c["phone"].replace("-", ""))}">☎ {esc(c["phone"])}</a>')
        if c.get("email"):
            bits.append(f'<a href="mailto:{att(c["email"])}">✉ {esc(c["email"])}</a>')
        desk = c.get("us_claims_desk") or {}
        if desk:
            d = [bi(desk.get("th", ""), desk.get("en", ""))]
            if desk.get("email"):
                d.append(f'<a href="mailto:{att(desk["email"])}">{esc(desk["email"])}</a>')
            if desk.get("role_th"):
                d.append(f'<span class="care-said">{bi(desk["role_th"], desk["role_en"])}</span>')
            bits.append(" · ".join(d))
        if c.get("address_th"):
            bits.append(bi(c["address_th"], c.get("address_en", "")))
        contact = (f'<p class="care-contact">{" · ".join(bits)}</p>' if bits else "")
        link = place_link(e.get("placeIds"))
        site = (f'<a href="{att(e["site"])}" rel="noopener nofollow">'
                f'{esc(e["site"][:52])}</a>' if e.get("site") else "")
        where = " · ".join(x for x in (link, site) if x)
        note = (f'<p class="care-note">{esc(e["note"])}</p>' if e.get("note") else "")
        cards.append(
            f'<section class="care-card"><h3>{bi(e["name_th"], e["name_en"])}</h3>'
            f'<p class="care-where">{where}</p>{note}'
            f'<div class="care-grid">{body}</div>{contact}</section>')

    # ---- the official paper ------------------------------------------------
    fmp = official.get("fmp") or {}
    fmp_rows = "".join(
        f'<tr><td>{bi(s["th"], s["en"])}'
        f'<span class="care-said">“{esc(s["evidence"][:200])}”</span></td></tr>'
        for s in fmp.get("states", []))
    fmp_html = (
        f'<div class="care-tablewrap"><table class="care-tab"><thead><tr>'
        f'<th>{bi("หน้าเว็บของ VA ระบุว่า", "What the VA’s own page states")}</th>'
        f'</tr></thead><tbody>{fmp_rows}</tbody></table></div>'
        f'<p class="care-note">{bi(fmp.get("note_th", ""), fmp.get("note_en", ""))} — '
        f'<a href="{att(fmp.get("src", ""))}" rel="noopener nofollow">va.gov</a> · '
        f'{bi("อ่านเมื่อ", "read")} {esc(fmp.get("fetched", ""))}'
        f'{bi(" · หน้าเว็บระบุปรับปรุงล่าสุด ", " · the page states it was last updated ")}'
        f'{esc(fmp.get("page_last_updated", ""))}</p>') if fmp else ""

    dtv = official.get("dtv") or {}
    dtv_rows = "".join(
        f'<tr><td>{esc(t["url"])}</td><td>{esc(t["verdict"])}</td></tr>'
        for t in dtv.get("tried", []))
    dtv_html = (
        f'<p class="care-note">{bi(dtv.get("note_th", ""), dtv.get("note_en", ""))}</p>'
        f'<div class="care-tablewrap"><table class="care-tab"><thead><tr>'
        f'<th>{bi("ลองอ่านจาก", "Tried")}</th><th>{bi("ผลที่ได้", "What came back")}</th>'
        f'</tr></thead><tbody>{dtv_rows}</tbody></table></div>') if dtv else ""

    # ---- what could not be read -------------------------------------------
    unread = reg.get("unread", [])
    un_rows = "".join(
        f'<tr><td>{esc(u["name"])}</td><td>{esc(u.get("url", ""))}</td>'
        f'<td>{esc(u["reason"])}</td></tr>' for u in unread)
    unread_html = (
        f'<div class="care-tablewrap"><table class="care-tab"><thead><tr>'
        f'<th>{bi("โรงพยาบาล", "Hospital")}</th><th>{bi("ที่อยู่เว็บ", "Address tried")}</th>'
        f'<th>{bi("ทำไมยังไม่ได้อ่าน", "Why it is not read")}</th>'
        f'</tr></thead><tbody>{un_rows}</tbody></table></div>')

    gl_rows = "".join(
        f'<tr><td class="th">{esc(th)}</td><td class="rtgs">{esc(rtgs)}</td>'
        f'<td>{esc(en)}</td></tr>' for th, rtgs, en in GLOSSARY)
    gloss_html = (f'<div class="care-tablewrap">'
                  f'<table class="care-tab care-gloss"><tbody>{gl_rows}</tbody></table></div>')

    intro = bi(
        "หน้านี้สำหรับคนที่อยู่ที่นี่และต้องดูแลอาการระยะยาว — ไม่ใช่คนที่เป็นไข้วันเดียว "
        "แผนที่บอกได้แค่ว่าโรงพยาบาลอยู่ตรงไหน แต่การรักษาต่อเนื่องอยู่ที่ 'แผนก' "
        "ไม่ใช่ที่ตัวอาคาร เราจึงไปอ่านเว็บของโรงพยาบาลเองทีละแห่ง "
        "แล้วพิมพ์เฉพาะสิ่งที่แต่ละแห่งเขียนไว้เอง พร้อมประโยคต้นทาง ลิงก์ และวันที่อ่าน "
        "ไม่จัดอันดับ ไม่ให้คะแนน ไม่ระบุชื่อหมอ และไม่ใช่คำแนะนำทางการแพทย์ "
        "ที่ไหนไม่ได้เขียนไว้ = เงียบ ไม่ได้แปลว่าไม่มี",
        "This page is for people who live here and manage something long-term — not "
        "for a one-day fever. A map can only say where a hospital is; ongoing care "
        "lives in DEPARTMENTS, not in buildings. So each hospital's own site was read, "
        "one at a time, and only what it states itself is printed here — with the "
        "sentence it came from, the link, and the date it was read. No rankings, no "
        "scores, no named doctors, and no medical advice. Where a hospital says "
        "nothing, that is silence, not a 'no'.")

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "ดูแลต่อเนื่อง เชียงใหม่-เชียงราย — Ongoing care, Chiang Mai and Chiang Rai",
        "url": BASE + "care.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "Hospital", "name": e["name_en"],
                      **({"url": e["site"]} if e.get("site") else {})}}
            for i, e in enumerate(entries.values())],
    }
    head = ('<link rel="stylesheet" href="care.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "medical") if shelf_og else None
    body = (
        f'<h1>{bi("ดูแลต่อเนื่อง — แผนก คลินิกนอกเวลา และกระดาษที่ต้องใช้", "Ongoing care — departments, after-hours clinics, and the paperwork")}</h1>'
        f'<p class="care-intro care-lede">{intro}</p>'

        f'<h2 class="care-h">{bi("โรงพยาบาลที่อ่านเว็บของตัวเองได้แล้ว", "Hospitals whose own site has been read")} '
        f'<span class="count">({len(entries)})</span></h2>'
        f'<p class="care-note">{bi("ทุกบรรทัดมีประโยคที่อ่านมา ลิงก์ต้นทาง และวันที่ — เวลาทำการเป็นเวลาที่โรงพยาบาลประกาศเอง และเก่าได้เหมือนป้ายทุกป้าย โทรถามก่อนไปเสมอ", "Every line carries the sentence it was read from, its link, and its date. Hours are the hospital’s own posted hours and go stale like any posted hours — ring before you travel.")}</p>'
        f'{"".join(cards)}'

        f'<h2 class="care-h">{bi("FMP — โครงการรักษาพยาบาลต่างประเทศของ VA", "FMP — the VA’s Foreign Medical Program")}</h2>'
        f'<p class="care-note">{bi("นี่คือสิ่งที่หน้าเว็บทางการของ VA เขียนไว้ ไม่ใช่คำแนะนำของเรา และไม่ใช่การตีความ", "This is what the VA’s own page states — not our advice, and not our reading of it.")}</p>'
        f'{fmp_html}'

        f'<h2 class="care-h">{bi("วีซ่า DTV — ยังอ่านจากต้นทางไม่ได้", "The DTV visa — not readable from the source")}</h2>'
        f'{dtv_html}'

        f'<h2 class="care-h">{bi("ยังอ่านไม่ได้ — บอกไว้ตรง ๆ", "Not read yet — said plainly")} '
        f'<span class="count">({len(unread)})</span></h2>'
        f'<p class="care-note">{bi("สารบัญที่โชว์เฉพาะที่สำเร็จ คือสารบัญที่บอกว่าแผนที่เสร็จแล้ว ทั้งที่ยังไม่เสร็จ รายชื่อนี้คือช่องว่างที่รู้ตัว และคือคิวงานรอบต่อไป", "A directory that shows only its successes is telling you the map is finished. These are the known gaps, and they are the next round’s queue.")}</p>'
        f'{unread_html}'

        f'<h2 class="care-h">{bi("แผ่นพกไปเคาน์เตอร์ — เจ็ดคำถาม", "The sheet to carry to the desk — seven questions")}</h2>'
        f'<p class="care-note">{bi("แผ่น A4 พิมพ์ได้ ชี้ที่ภาษาไทยได้เลย ทุกบรรทัดเป็นคำถามที่เคาน์เตอร์ตอบเป็นประจำ — ขอใบเสร็จแยกรายการ ขอเวชระเบียน ถามคลินิกนอกเวลา จดคำตอบพร้อมวันที่แล้วส่งกลับมาบอกมดแดงได้ จะขึ้นเป็นข้อมูลสาธารณะ", "A printable A4 sheet — point at the Thai. Every line is a question a hospital front desk answers routinely: an itemised receipt, a copy of your records, what time the after-hours clinic opens, and whether they have filed US FMP or TRICARE claims before. Write the answer down with the date and send it back; it becomes a public, dated fact on that hospital’s page.")}</p>'
        f'<p><a class="bt-sheet" href="reader/care-words.pdf">📄 '
        f'{bi("ดาวน์โหลดแผ่นคำถาม (PDF)", "Download the desk sheet (PDF)")}</a></p>'
        f'<h2 class="care-h">{bi("อ่านป้ายหน้าแผนก — คำที่ควรรู้", "Reading the department board — the words to know")}</h2>'
        f'<p class="care-note">{bi("อักษรไทย · คำอ่านแบบ RTGS · ความหมาย — เทียบรูปคำกับป้ายได้แม้อ่านไทยไม่ออก", "Thai script · RTGS spelling · what it means — enough to match a word against a sign by its shape, without reading Thai.")}</p>'
        f'{gloss_html}'

        f'<p class="care-note">{bi("มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ ไม่ใช่คำแนะนำเรื่องประกันหรือวีซ่า และไม่ใช่การรับรองคุณภาพ ข้อมูลสถานพยาบาลบางส่วนมาจาก OpenStreetMap (ODbL 1.0)", "Mot Dang is a directory of places. It is not medical advice, not a referral, not insurance or visa advice, and not a quality guarantee. Some facility data is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap contributors.")}</p>'
        f'<p class="care-note"><a href="womens-health.html">{bi("สุขภาพผู้หญิง — วัยทอง ฮอร์โมน สูตินรีเวช", "Women’s health — menopause, hormones, OB-GYN")}</a> · '
        f'<a href="cm/medical/index.html">{bi("ชั้นหมอ-สถานพยาบาล", "the medical shelf")}</a></p>'
        f'{share_block(BASE + "care.html", "ดูแลต่อเนื่อง เชียงใหม่ · มดแดง", card=og)}')

    (DOCS / "care.html").write_text(page(
        "ดูแลต่อเนื่อง เชียงใหม่ · Ongoing care, Chiang Mai",
        body, depth=0, path="care.html",
        desc=bi_text(
            "การรักษาต่อเนื่องในเชียงใหม่-เชียงราย — แผนกที่โรงพยาบาลบอกเอง "
            "คลินิกนอกเวลา เอกสารเคลมประกันสหรัฐฯ FMP และคำไทยบนป้ายหน้าแผนก",
            "Ongoing care in Chiang Mai and Chiang Rai: the departments each hospital "
            "states itself, after-hours clinics, US insurance and VA Foreign Medical "
            "Program paperwork, and the Thai words on the department board."),
        extra_head=head, og=og))
    return (f"{len(entries)} hospitals read, {n_claims} stated facts, "
            f"{len(unread)} not read")
