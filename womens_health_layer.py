#!/usr/bin/env python3
"""สุขภาพผู้หญิง — where women's health care is, what each place actually states,
and where a credential can be checked (/womens-health.html).

WHY THIS PAGE EXISTS. "women's health" is a term readers type, and until now the
directory answered it with 469 subdistrict health stations, because nothing in
the corpus matched both words and the search fell back to most-words-matched —
every place with สุขภาพ or "health" in its name. Meanwhile the answer was sitting
in the data unread: importers/specialty.py has labelled the obgyn key "Women's
health" in English since it landed, and the cm-womens-health harvester left a
graded `obgyn` field on 49 records that no page and no index ever looked at.

WHAT THIS PAGE IS. A directory of PLACES and a pointer to the registers. It is
not medical advice, it does not rank anybody, and it names no individual doctor —
the same rule the parent crawler settled twice over. A named physician can be
defamed by an aggregate score, most of the doctors here are competent, and a
directory that guesses at quality stops being checkable.

THE GRADE IS THE POINT, so it is on every row rather than in a footnote:

  stated             the place's own sign says สูตินรีเวช, or a mapper tagged the
                     speciality. Five of them.
  general hospital   a general hospital, which in Thailand almost always runs a
                     สูตินรีเวช department — but nobody has confirmed THIS one.
                     Forty-four of them. Shown, because a reader looking for care
                     wants to know a hospital is there; marked, because "probably"
                     is not "yes".

Competence is a credential, not a star rating, so the registers that actually
answer the question get a table of their own — แพทยสภา for the licence, ราชวิทยาลัย
สูตินรีแพทย์ for the board certification that separates an OB-GYN from a GP, สรพ.
and JCI for the hospital. Verified reachable 2026-07-19 by the parent repo.

AND A GLOSSARY, because the sign on the door is in Thai and the reader who typed
"women's health" in English could not read the results the search gave her. Every
term carries its script, its RTGS spelling and its gloss, so a word can be
matched against a sign by shape alone. รพ.สต. gets its own line: those 469
stations that flooded the old results are not noise — they are the local
primary-care clinic, and antenatal care and family planning are exactly what they
do — they were just never translated.

Entry point: emit(globals_of_build, data) — hooked in build.py after the cooking
layer. Emits womens-health.html + womens-health.css; prints the counts.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CSS = """
.wh-intro{font-size:1.02rem;max-width:46rem}
.wh-note{font-size:.86rem;opacity:.78;max-width:46rem}
.wh-grade{display:inline-block;font-size:.72rem;padding:.08rem .42rem;border-radius:.7rem;
  border:1px solid currentColor;opacity:.85;vertical-align:.08em;white-space:nowrap}
.wh-grade.stated{color:#1c6b3a}
.wh-grade.likely{color:#7a5a12}
.wh-grade.station{color:#2a5a7a}
.wh-list{list-style:none;padding-left:0;max-width:46rem}
.wh-list li{padding:.3rem 0;border-bottom:1px solid rgba(0,0,0,.07);line-height:1.5}
.wh-list .reach{font-size:.8rem;opacity:.7}
.wh-reg{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.wh-reg th,.wh-reg td{text-align:left;vertical-align:top;padding:.42rem .5rem;
  border-bottom:1px solid rgba(0,0,0,.09)}
.wh-reg th{font-weight:600;white-space:nowrap}
.wh-gloss{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.wh-gloss td{padding:.34rem .5rem;border-bottom:1px solid rgba(0,0,0,.07);vertical-align:top}
.wh-gloss .th{font-size:1.06rem;white-space:nowrap}
.wh-gloss .rtgs{opacity:.72;font-style:italic;white-space:nowrap}
@media (max-width:640px){.wh-reg,.wh-gloss{font-size:.86rem}
  .wh-reg th{white-space:normal}}
"""

# Competence is a credential. Every row verified reachable 2026-07-19 by
# cm-womens-health/README.md, which is where this table comes from — one source,
# not a second list to keep in step by hand.
REGISTERS = [
    ("ใบประกอบวิชาชีพเวชกรรม — เป็นแพทย์จริงไหม",
     "Is this person a licensed physician?",
     "แพทยสภา", "The Medical Council of Thailand", "https://tmc.or.th",
     "ทะเบียนแพทย์ทั้งประเทศ — ขอเลขใบประกอบวิชาชีพจากคลินิกแล้วค้นดูได้",
     "The national register of licensed doctors. Ask the clinic for the doctor's "
     "ใบประกอบวิชาชีพ (licence) number and look it up."),
    ("วุฒิบัตรสูตินรีเวช — เป็นหมอเฉพาะทางจริงไหม",
     "Are they board-certified in OB-GYN?",
     "ราชวิทยาลัยสูตินรีแพทย์แห่งประเทศไทย",
     "Royal Thai College of Obstetricians and Gynaecologists",
     "https://www.rtcog.or.th",
     "วุฒิบัตรสาขาสูตินรีเวชวิทยา คือสิ่งที่แยกสูตินรีแพทย์ออกจากแพทย์ทั่วไป",
     "Board certification (วุฒิบัตร) in สูตินรีเวชวิทยา is the credential that "
     "distinguishes an OB-GYN from a general practitioner."),
    ("โรงพยาบาลผ่านการรับรองไหม", "Is the hospital accredited?",
     "สรพ. — สถาบันรับรองคุณภาพสถานพยาบาล", "Healthcare Accreditation Institute",
     "https://www.ha.or.th",
     "มาตรฐานคุณภาพโรงพยาบาลของไทย", "Thailand's national hospital accreditation body."),
    ("รับรองระดับสากลไหม", "International accreditation?",
     "Joint Commission International", "Joint Commission International",
     "https://www.jointcommissioninternational.org",
     "โรงพยาบาลเอกชนในเชียงใหม่หลายแห่งได้ — เช็กสถานะปัจจุบัน อย่าเดา",
     "Several Chiang Mai private hospitals hold it; verify current status rather "
     "than assuming."),
    ("คลินิกมีใบอนุญาตไหม", "Is a private clinic licensed at all?",
     "กองสถานพยาบาลและการประกอบโรคศิลปะ กระทรวงสาธารณสุข",
     "MoPH, Dept. of Health Service Support", "",
     "คลินิกที่ถูกต้องจะติดใบอนุญาตสถานพยาบาลไว้ให้เห็นในร้าน",
     "A legitimate clinic displays its สถานพยาบาล licence on the premises."),
]

# The sign on the door, for a reader who does not read Thai. Script · RTGS ·
# gloss, so a word can be matched to a sign by shape before it can be read.
GLOSSARY = [
    ("สูตินรีเวช", "sutinariwet", "obstetrics & gynaecology — the OB-GYN department "
     "or clinic. This is the word to look for."),
    ("นรีเวช", "nariwet", "gynaecology on its own."),
    ("สูติ", "suti", "obstetrics — pregnancy and birth."),
    ("คลินิก", "khlinik", "clinic — a private practice, usually one or two doctors."),
    ("โรงพยาบาล", "rong phayaban", "hospital. Often shortened to รพ."),
    ("โรงพยาบาลส่งเสริมสุขภาพตำบล", "rong phayaban song soem sukkhaphap tambon",
     "subdistrict health-promoting hospital — the local primary-care station, "
     "shortened รพ.สต. Free or near-free, Thai-speaking, and antenatal care and "
     "family planning are routine there. There are 469 in this directory."),
    ("ฝากครรภ์", "fak khan", "antenatal care — booking in for pregnancy check-ups."),
    ("ตรวจภายใน", "truat phai nai", "internal/pelvic examination."),
    ("ตรวจมะเร็งปากมดลูก", "truat mareng pak mot luk", "cervical cancer screening "
     "— a Pap smear."),
    ("เต้านม", "tao nom", "breast — as in ตรวจเต้านม, a breast examination."),
    ("วางแผนครอบครัว", "wang phaen khropkhrua", "family planning."),
    ("คุมกำเนิด", "khum kamnoet", "contraception."),
    ("มีบุตรยาก", "mi but yak", "infertility — a fertility clinic."),
    ("วัยทอง", "wai thong", "menopause — literally 'the golden age'."),
    ("คลินิกวัยทอง", "khlinik wai thong", "menopause clinic — a named clinic "
     "inside many general hospitals. This is the sign, and the word at the "
     "information desk, to ask for."),
    ("ฮอร์โมนทดแทน", "homon thotthaen", "hormone replacement therapy (HRT) — "
     "usually seen under the วัยทอง clinic or สูตินรีเวช."),
    ("แพทย์หญิง", "phaet ying", "a woman doctor. Often abbreviated พญ. before a "
     "name; a man is นพ. Worth knowing if you would rather be seen by a woman."),
]


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block, channels = g["share_block"], g["channels"]
    PROVINCES = g["PROVINCES"]
    name_of, name_pair = g["name_of"], g["name_pair"]
    SPECIALTY_LABELS = g["SPECIALTY_LABELS"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    (DOCS / "womens-health.css").write_text(CSS)

    # ---- who is on this page ---------------------------------------------
    # Two grades, kept apart on the page the way they are kept apart in the
    # data. A place qualifies by STATING the speciality — its own sign, a
    # mapper's tag, or the graded hospital signal — never by this build's
    # reading of what a hospital probably does.
    # importers/specialty.py:obgyn_grade decides, and build.py's index asks the
    # same function, so this list and the search can never disagree about who
    # qualifies. It is also what keeps three ร้านยา and a neurological hospital
    # off a page that would otherwise be telling a reader they run an OB-GYN
    # department.
    OBGYN_GRADE = g["OBGYN_GRADE"]
    stated, likely, station = [], [], []
    n_rpsat = 0
    for p in PROVINCES:
        for r in data[p["key"]]:
            a = r.get("attrs") or {}
            if a.get("facilityType") == "health-station":
                n_rpsat += 1
            grade = OBGYN_GRADE(a, *name_pair(r))
            if grade == "tagged":
                stated.append((p["key"], r))
            elif grade == "hospital-likely":
                likely.append((p["key"], r))
            elif grade == "health-station":
                station.append((p["key"], r))

    def row(prov, r, grade):
        live, _ = channels(r)
        kinds = [c.get("kind") for c in live] if live and isinstance(live[0], dict) else []
        marks = []
        if r.get("phone") or "phone" in kinds:
            marks.append("☎")
        if "line" in kinds or (r.get("attrs") or {}).get("lineId"):
            marks.append("LINE")
        if "web" in kinds:
            marks.append("🌐")
        reach = (f' <span class="reach">{" · ".join(marks)}</span>' if marks else "")
        if grade == "stated":
            via = (r.get("attrs") or {}).get("specialtyVia")
            how = (bi_text("จากชื่อของสถานพยาบาลเอง", "from the place's own name")
                   if via == "name" else
                   bi_text("จากป้ายข้อมูลใน OpenStreetMap", "tagged in OpenStreetMap"))
            tag = (f'<span class="wh-grade stated" title="{att(how)}">'
                   + bi("ระบุเอง", "stated") + "</span>")
        elif grade == "health-station":
            tag = ('<span class="wh-grade station" title="'
                   + att(bi_text("โรงพยาบาลส่งเสริมสุขภาพตำบล — สถานีอนามัยประจำตำบล",
                                 "subdistrict health-promoting hospital — the local "
                                 "primary-care station"))
                   + '">' + bi("รพ.สต.", "รพ.สต. — health station") + "</span>")
        else:
            tag = ('<span class="wh-grade likely" title="'
                   + att(bi_text("โรงพยาบาลทั่วไป — ยังไม่ได้ยืนยันว่ามีแผนกสูตินรีเวช",
                                 "general hospital — an OB-GYN department is not confirmed"))
                   + '">' + bi("โรงพยาบาลทั่วไป — ยังไม่ยืนยัน",
                               "general hospital — not confirmed") + "</span>")
        return (f'<li><a href="{prov}/p/{place_slug(r)}.html">{name_bi(r)}</a> '
                f'{tag}{reach}</li>')

    stated.sort(key=lambda x: name_of(x[1]).lower())
    likely.sort(key=lambda x: name_of(x[1]).lower())
    station.sort(key=lambda x: name_of(x[1]).lower())
    stated_html = ('<ul class="wh-list">'
                   + "".join(row(k, r, "stated") for k, r in stated) + "</ul>")
    likely_html = ('<ul class="wh-list">'
                   + "".join(row(k, r, "likely") for k, r in likely) + "</ul>")
    station_html = ('<ul class="wh-list">'
                    + "".join(row(k, r, "health-station") for k, r in station) + "</ul>") \
        if station else ""

    # ---- the registers ----------------------------------------------------
    reg_rows = []
    for q_th, q_en, n_th, n_en, url, note_th, note_en in REGISTERS:
        who = f'<a href="{att(url)}" rel="noopener">{bi(n_th, n_en)}</a>' if url \
            else bi(n_th, n_en)
        reg_rows.append(f'<tr><th>{bi(q_th, q_en)}</th><td>{who}</td>'
                        f'<td>{bi(note_th, note_en)}</td></tr>')
    reg_html = (f'<table class="wh-reg"><thead><tr>'
                f'<th>{bi("อยากยืนยันอะไร", "What you want to confirm")}</th>'
                f'<th>{bi("ที่ไหน", "Where")}</th>'
                f'<th>{bi("หมายเหตุ", "Notes")}</th></tr></thead>'
                f'<tbody>{"".join(reg_rows)}</tbody></table>')

    # ---- the glossary -----------------------------------------------------
    gl_rows = "".join(
        f'<tr><td class="th">{esc(th)}</td><td class="rtgs">{esc(rtgs)}</td>'
        f'<td>{esc(en)}</td></tr>' for th, rtgs, en in GLOSSARY)
    gloss_html = f'<table class="wh-gloss"><tbody>{gl_rows}</tbody></table>'

    # The 469 รพ.สต. are the places that flooded the old "women's health" search,
    # in Thai, unranked and untranslated, to a reader who had asked in English.
    # They were never noise — they are the cheapest and closest women's health
    # care in both provinces. What they were was unexplained, so this explains
    # them, and links to the shelf rather than reprinting 469 names here.
    _st = f' <a href="cm/medical/index.html">{bi("ดูชั้นหมอ-สถานพยาบาล", "see the medical shelf")}</a>' \
        if n_rpsat else ""
    rpsat_note = (bi(
        f"เชียงใหม่และเชียงรายมีโรงพยาบาลส่งเสริมสุขภาพตำบล (รพ.สต.) {n_rpsat:,} แห่งในสารบัญนี้ "
        "เป็นสถานพยาบาลปฐมภูมิประจำตำบล ฝากครรภ์ วางแผนครอบครัว และตรวจมะเร็งปากมดลูก "
        "เป็นงานประจำของที่นี่ ฟรีหรือเกือบฟรีถ้ามีสิทธิ์ และอยู่ใกล้บ้านที่สุด "
        "เจ้าหน้าที่พูดไทย รายชื่อด้านล่างขึ้นเฉพาะแห่งที่มีป้ายข้อมูลระบุไว้เท่านั้น "
        "ไม่ได้แปลว่าที่อื่นไม่ทำ — แปลว่ายังไม่มีใครจดไว้",
        f"There are {n_rpsat:,} subdistrict health-promoting hospitals (รพ.สต.) in this "
        "directory. They are the local primary-care stations, and antenatal care, family "
        "planning and cervical screening are routine work there — free or near-free if you "
        "hold Thai coverage, and closer to home than any hospital. Staff speak Thai. Only "
        "the ones whose own record states the service are listed below; that is not a claim "
        "that the others do not do it, only that nobody has written it down yet.")
        + _st)

    intro = bi(
        "หน้านี้รวบรวมสถานพยาบาลที่เกี่ยวกับสุขภาพผู้หญิงในสารบัญ พร้อมบอกตรง ๆ ว่า "
        "แต่ละแห่งรู้มาแค่ไหน — บางแห่งบอกเองว่ามีสูตินรีเวช บางแห่งเป็นโรงพยาบาลทั่วไป "
        "ซึ่งมักจะมีแผนกนี้ แต่ยังไม่มีใครยืนยัน "
        "ตารางข้างล่างบอกว่าไปตรวจใบวุฒิบัตรได้ที่ไหน",
        "This page collects the places in the directory that do women's health care, "
        "and says plainly how much is actually known about each one — some state a "
        "สูตินรีเวช (OB-GYN) service themselves; others are general hospitals, which "
        "in Thailand almost always run one, but nobody has confirmed it here. "
        "Below: where to check a board certification.")

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "สุขภาพผู้หญิง เชียงใหม่-เชียงราย — Women's health, Chiang Mai and Chiang Rai",
        "url": BASE + "womens-health.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "MedicalClinic", "name": name_of(r),
                      "url": BASE + f'{k}/p/{place_slug(r)}.html'}}
            for i, (k, r) in enumerate(stated + likely)],
    }
    head = ('<link rel="stylesheet" href="womens-health.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "medical") if shelf_og else None
    body = (
        f'<h1>{bi("สุขภาพผู้หญิง — ไปตรวจที่ไหน", "Women’s health — where to go")}</h1>'
        f'<p class="wh-intro">{intro}</p>'
        f'<h2>{bi("ที่ที่บอกเองว่ามีสูตินรีเวช", "Places that state a women’s-health service")} '
        f'<span class="count">({len(stated)})</span></h2>'
        f'<p class="wh-note">{bi("แต่ละแห่งบอกเองจากชื่อร้านหรือจากป้ายข้อมูลใน OpenStreetMap — ชี้ที่ชื่อเพื่อดูว่ารู้มาจากไหน", "Each one states it, either on its own sign or in an OpenStreetMap tag — hover the mark to see which")}</p>'
        f'{stated_html}'
        f'<h2>{bi("โรงพยาบาลทั่วไป — น่าจะมี ยังไม่ยืนยัน", "General hospitals — likely, unconfirmed")} '
        f'<span class="count">({len(likely)})</span></h2>'
        f'<p class="wh-note">{bi("โรงพยาบาลทั่วไปในไทยเกือบทุกแห่งมีแผนกสูตินรีเวช แต่ยังไม่มีใครโทรไปถามให้แน่ใจ จึงขึ้นไว้แบบติดป้ายว่ายังไม่ยืนยัน — โทรถามแผนกสูตินรีเวชก่อนไปได้เลย ตู้สายโรงพยาบาลตอบเรื่องนี้เป็นประจำ", "Nearly every general hospital in Thailand runs a สูตินรีเวช department, but nobody has rung to confirm these, so they are listed and marked rather than promised. Ring the hospital’s OB-GYN department and ask — Thai hospital switchboards answer this routinely.")}</p>'
        f'{likely_html}'
        f'<h2>{bi("รพ.สต. — สถานีอนามัยประจำตำบล", "รพ.สต. — the subdistrict health station")}</h2>'
        f'<p class="wh-note">{rpsat_note}</p>'
        f'{station_html}'
        f'<h2>{bi("ตรวจใบวุฒิบัตรได้ที่นี่", "Where to check a credential")}</h2>'
        f'<p class="wh-note">{bi("ทุกแห่งเป็นทะเบียนทางการ ตรวจแล้วว่าเข้าถึงได้เมื่อ 19 ก.ค. 2569", "Every one of these is an official register, verified reachable 2026-07-19")}</p>'
        f'{reg_html}'
        f'<h2>{bi("อ่านป้ายหน้าคลินิก", "Reading the clinic sign")}</h2>'
        f'<p class="wh-note">{bi("อักษรไทย · คำอ่านแบบ RTGS · ความหมาย — เทียบรูปคำกับป้ายได้เลยแม้อ่านไทยไม่ออก", "Thai script · RTGS spelling · what it means — enough to match a word against a sign by its shape, without reading Thai")}</p>'
        f'{gloss_html}'
        f'<p class="wh-note">{bi("มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ และไม่ใช่การรับรองคุณภาพ ข้อมูลสถานพยาบาลบางส่วนมาจาก OpenStreetMap (ODbL 1.0)", "Mot Dang is a directory of places. It is not medical advice, not a referral, and not a quality guarantee. Some facility data is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap contributors.")}</p>'
        f'{share_block(BASE + "womens-health.html", "สุขภาพผู้หญิง เชียงใหม่ · มดแดง", card=og)}')
    (DOCS / "womens-health.html").write_text(page(
        "สุขภาพผู้หญิง เชียงใหม่ · Women's health, Chiang Mai",
        body, depth=0, path="womens-health.html",
        desc=bi_text(
            "สถานพยาบาลสุขภาพผู้หญิงในเชียงใหม่และเชียงราย — ที่ไหนบอกเองว่ามีสูตินรีเวช "
            "ที่ไหนเป็นโรงพยาบาลทั่วไปที่ยังไม่ยืนยัน ตรวจใบวุฒิบัตรแพทย์ได้ที่ไหน "
            "และคำไทยบนป้ายหน้าคลินิกแปลว่าอะไร",
            "Women's health care in Chiang Mai and Chiang Rai: which places state a "
            "สูตินรีเวช (OB-GYN) service, which are general hospitals that are likely "
            "but unconfirmed, where to verify a doctor's board certification, and what "
            "the Thai words on the clinic sign mean"),
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("สุขภาพผู้หญิง", "Women’s health")}'))
    return (f"{len(stated)} stated · {len(likely)} general-hospital (unconfirmed) · "
            f"{len(station)} รพ.สต. · {n_rpsat} รพ.สต. in the directory")
