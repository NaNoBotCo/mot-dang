#!/usr/bin/env python3
"""สมาธิสั้น — ADHD medicine and care in Chiang Mai and Chiang Rai (/adhd.html).
WO-31.

WHY THIS PAGE EXISTS. People arrive in Thailand expecting this to be the easy
part and find it is the hard part, and the reason is almost never bad luck —
it is that nobody wrote the intel down. Three separate things get folded into
one rumour ("it's illegal here", "you can get anything here"), and they have
different answers:

  1. WHICH SCHEDULE a molecule sits in. Fixed, published, and checkable — and
     the checker is a live official tool, so this page links the tool instead
     of copying a table that will rot. The fork is sharp: the amphetamine
     family is a category-1 narcotic and no permit reaches it, methylphenidate
     is a category-2 psychotropic a traveller may carry with papers.
  2. WHAT THE NATIONAL LIST STOCKS. บัญชี ค, tablet, 10 mg only. A person who
     arrives on a long-acting formulation is not facing a legal problem, they
     are facing a supply problem, and those two get solved differently.
  3. WHAT A DESK WILL DO. Mutable, varies by desk and by day. So this page
     hands over QUESTIONS TO ASK and never recites a rule as if it were fate.

Keeping those three apart is the whole design. Collapsing them is what makes
people believe there is no door at all.

WHAT THIS PAGE IS NOT. It is not medical advice, it names no dose, it
recommends no brand and no doctor, and it holds no view on what anyone should
take — said once on the page, plainly, and then not laboured. Brand names
appear in ONE place, the molecule table, and only so a reader can match the
small print on their own box to a legal class. That is a fact about import and
supply, which is a directory's job.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
trans-health layer. Emits adhd.html + adhd.css.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The name-rule scan that measures the zero. One source of truth: the audit
# (importers/audit_adhd.py) imports this, so the page's sentence and the
# audit's report cannot drift apart. สมาธิ alone is NOT a rule — it is
# meditation, and it lives in the name of half the temples in the province.
ADHD_NAME_RX = re.compile(
    r"สมาธิสั้น|ไฮเปอร์แอคทีฟ|เมทิลเฟนิเดต|อะโตม็อกซีทีน"
    r"|\bADHD\b|\battention[- ]deficit|\bmethylphenidate\b|\batomoxetine\b",
    re.I)

# The wider psychiatry scan — the door this care actually goes through here.
PSYCH_NAME_RX = re.compile(
    r"จิตเวช|จิตแพทย์|สุขภาพจิต|พัฒนาการเด็ก"
    r"|\bpsychiatr|\bmental health\b", re.I)

GRADE_ORDER = ["stated", "psychiatry", "route", "unread"]

CSS = """
.ad-intro{font-size:1.02rem;max-width:46rem}
.ad-note{font-size:.86rem;opacity:.78;max-width:46rem}
.ad-lead{max-width:46rem;border-left:3px solid rgba(0,0,0,.22);padding:.1rem 0 .1rem .9rem;
  margin:.9rem 0;font-size:1.02rem;line-height:1.6}
.ad-tool{max-width:46rem;border:1px solid rgba(0,0,0,.16);border-radius:.8rem;
  padding:.8rem 1rem;margin:1rem 0;background:rgba(0,0,0,.02)}
.ad-tool .ask{font-weight:600;display:block;margin-bottom:.25rem}
.ad-mol{list-style:none;padding-left:0;max-width:46rem;margin:.6rem 0}
.ad-mol li{padding:.6rem 0;border-bottom:1px solid rgba(0,0,0,.09);line-height:1.55}
.ad-mol .gen{font-weight:600}
.ad-mol .known{font-size:.84rem;opacity:.72;display:block}
.ad-mol .cls{display:block;font-size:.9rem;margin-top:.2rem}
.ad-mol .carry{display:block;font-size:.88rem;margin-top:.18rem}
.ad-mol .quote{display:block;font-size:.84rem;opacity:.8;margin-top:.24rem;
  border-left:2px solid rgba(0,0,0,.16);padding-left:.6rem}
.ad-mol .srcs{font-size:.76rem;opacity:.65}
.ad-flag{display:inline-block;font-size:.72rem;padding:.08rem .42rem;border-radius:.7rem;
  border:1px solid currentColor;opacity:.9;vertical-align:.08em;white-space:nowrap}
.ad-flag.no{color:#8a3a2a}
.ad-flag.limited{color:#7a5a12}
.ad-flag.ok{color:#1c6b3a}
.ad-flag.ask{color:#4a4a52}
.ad-grade{display:inline-block;font-size:.72rem;padding:.08rem .42rem;border-radius:.7rem;
  border:1px solid currentColor;opacity:.85;vertical-align:.08em;white-space:nowrap}
.ad-grade.stated{color:#1c6b3a}
.ad-grade.psych{color:#2a5a7a}
.ad-grade.route{color:#7a5a12}
.ad-grade.unread{color:#6a5a5a}
.ad-list{list-style:none;padding-left:0;max-width:46rem}
.ad-list li{padding:.34rem 0;border-bottom:1px solid rgba(0,0,0,.07);line-height:1.5}
.ad-list .states{display:block;font-size:.84rem;opacity:.82}
.ad-list .reach{font-size:.8rem;opacity:.7}
.ad-list .srcs{font-size:.76rem;opacity:.65}
.ad-dead{text-decoration:underline dotted;text-underline-offset:.18em;
  opacity:.72;cursor:help}
.ad-three{margin:.5rem 0 .2rem;padding-left:1.1rem;font-size:.94rem;line-height:1.6;
  max-width:46rem}
.ad-ask{margin:.4rem 0 .2rem;padding-left:1.1rem;font-size:.94rem;line-height:1.6;
  max-width:46rem}
.ad-reg{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.ad-reg th,.ad-reg td{text-align:left;vertical-align:top;padding:.42rem .5rem;
  border-bottom:1px solid rgba(0,0,0,.09)}
.ad-reg th{font-weight:600;white-space:nowrap}
.ad-gloss{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.ad-gloss td{padding:.34rem .5rem;border-bottom:1px solid rgba(0,0,0,.07);vertical-align:top}
.ad-gloss .th{font-size:1.06rem;white-space:nowrap}
.ad-gloss .rtgs{opacity:.72;font-style:italic;white-space:nowrap}
@media (max-width:640px){.ad-reg,.ad-gloss{font-size:.86rem}
  .ad-reg th{white-space:normal}}
"""

# Every one is an official register or an official tool, verified reachable
# 2026-08-21 from this machine. adhdthailand.com — Thailand's own ADHD site,
# linked from RICD's website — is deliberately ABSENT: its TLS handshake fails,
# and a register link has to be one. It is named in the leads instead.
REGISTERS = [
    ("ยาของฉันจัดอยู่ในประเภทไหน — ตรวจเองได้",
     "Which class is my own medicine in? Check it yourself",
     "อย. — ตรวจสอบยาสำหรับผู้เดินทาง",
     "Thai FDA — Check the Drug (for travellers)",
     "https://permitfortraveler.fda.moph.go.th/nct_permit_main/Main/FRM_checkdrug_index",
     "ค้นด้วยชื่อสามัญทางยา แล้วบอกเลยว่าเป็นยาเสพติดให้โทษ วัตถุออกฤทธิ์ หรือยาธรรมดา และนำเข้าได้หรือไม่",
     "Type the generic name and it returns the class and whether it may be "
     "carried in — the authority itself, answering about your own bottle."),
    ("ขออนุญาตพกยาเข้าประเทศ",
     "Applying for the permit to carry it in",
     "อย. — ระบบขออนุญาตสำหรับผู้เดินทาง",
     "Thai FDA — traveller permit system",
     "https://permitfortraveler.fda.moph.go.th/nct_permit_main/",
     "ยื่นออนไลน์ ล่วงหน้าอย่างน้อย 15 วันก่อนเดินทาง",
     "Filed online, at least 15 days before you travel."),
    ("คนที่ตรวจให้เป็นแพทย์จริงไหม และวุฒิบัตรสาขาอะไร",
     "Is the person assessing me a licensed doctor, and in which speciality?",
     "แพทยสภา — ตรวจสอบแพทย์", "The Medical Council of Thailand — physician lookup",
     "https://checkmd.tmc.or.th",
     "ทะเบียนแพทย์ทั้งประเทศ พร้อมวุฒิบัตรเฉพาะทาง — จิตเวชศาสตร์ และจิตเวชศาสตร์เด็กและวัยรุ่น ดูได้จากที่เดียวกัน",
     "The national register of licensed doctors with their board "
     "qualifications — psychiatry, and child and adolescent psychiatry, both "
     "show in the same lookup."),
    ("จิตแพทย์ — สังกัดราชวิทยาลัยไหน",
     "The psychiatrist — which college stands behind that?",
     "ราชวิทยาลัยจิตแพทย์แห่งประเทศไทย",
     "Royal College of Psychiatrists of Thailand", "https://www.rcpsycht.org",
     "องค์กรวิชาชีพของจิตแพทย์ในประเทศไทย",
     "The professional body for psychiatrists in Thailand."),
]

# Thai script · RTGS · what it means. Enough to match a word against a sign or
# a form by its shape, without reading Thai.
GLOSSARY = [
    ("สมาธิสั้น", "samathi san",
     "โรคสมาธิสั้น — คำที่ใช้จริงในคลินิกและในเอกสารราชการ",
     "ADHD. Literally short-samathi: สมาธิ samathi is concentration (from Pali "
     "samādhi) and สั้น san is short. This is the word on the form."),
    ("จิตเวช", "chit-wet",
     "จิตเวชศาสตร์ — แผนกที่เรื่องนี้เดินผ่าน",
     "Psychiatry — จิต chit, mind (Pali citta) + เวช wet, medicine (Pali "
     "vejja). This is the department this care goes through here."),
    ("จิตแพทย์", "chit-ta-phaet", "แพทย์เฉพาะทางจิตเวช",
     "A psychiatrist — the specialist who can start this."),
    ("ใบสั่งยา", "bai sang ya", "ใบสั่งยาจากแพทย์",
     "A prescription — bai, sheet; sang, to order; ya, medicine."),
    ("ใบรับรองแพทย์", "bai rap-rong phaet",
     "หนังสือรับรองจากแพทย์ — เอกสารที่ด่านและ อย. ขอดู",
     "A doctor's certificate. This is the paper the permit system and the "
     "customs desk actually ask to see."),
    ("วัตถุออกฤทธิ์", "wat-thu ok rit",
     "วัตถุออกฤทธิ์ต่อจิตและประสาท — เมทิลเฟนิเดตอยู่ในประเภท 2",
     "Psychotropic substance — literally a substance that exerts an effect. "
     "Methylphenidate sits in category 2 of this list."),
    ("ยาเสพติดให้โทษ", "ya sep-tit hai thot",
     "ยาเสพติดให้โทษ — แอมเฟตามีนอยู่ในประเภท 1",
     "Narcotic drug — a different list from the one above, and the harder "
     "one. The amphetamine family sits in its category 1."),
    ("ผู้ป่วยนอก", "phu puai nok", "แผนกผู้ป่วยนอก (OPD)",
     "Outpatients — the OPD desk, where a first visit starts."),
    ("คลินิกพิเศษนอกเวลา", "khli-nik phi-set nok wela",
     "คลินิกเฉพาะทางนอกเวลาราชการ ค่าบริการเพิ่มตามประกาศ",
     "The after-hours specialist clinic: the same specialists, outside "
     "government hours, at a posted extra fee. It is the tier that is rarely "
     "printed in English, and it is often the shortest way to a first "
     "appointment."),
    ("เภสัชกร", "phe-sat-cha-kon", "เภสัชกรประจำร้านยา",
     "The pharmacist — worth asking about stock, though a category-2 "
     "psychotropic is not a pharmacy-counter item."),
]


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block, channels = g["share_block"], g["channels"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")
    verdict, BROKEN = g["verdict"], g["BROKEN"]
    BROKEN_WHY = g["BROKEN_WHY"]
    LINK_HEALTH_DATE = g.get("LINK_HEALTH_DATE") or ""

    def out_a(url, label, cls=""):
        """One outbound link — or the address of one that has stopped answering.

        A source that no longer resolves is still evidence: it says what was
        tried and on what day, and several sentences on this page lean on
        exactly that. But nothing here sends a reader into a dead end, and
        tests/test_publish_gate.py is right to refuse an href to a URL
        link-health has buried — one such ref held the whole site unpublished
        from 2026-08-21 to 2026-08-22. So a dead ref keeps its number and its
        address, carries the verdict and the date of the check in its tooltip,
        and stops being a door. Same rule for a ref with no address at all.
        """
        url = (url or "").strip()
        v = verdict(url)
        st = v.get("status")
        if url and st not in BROKEN:
            return ('<a href="' + att(url) + '" rel="noopener"'
                    + (' class="' + cls + '"' if cls else "") + ">" + label + "</a>")
        if url:
            why_th, why_en = BROKEN_WHY.get(
                st, ("เปิดไม่ได้", "the link could not be opened"))
            when = v.get("checkedAt") or LINK_HEALTH_DATE
            tip = url + " — " + bi_text(
                why_th + " ตรวจเมื่อ " + when, why_en + ", checked " + when)
        else:
            tip = bi_text("ไม่มีที่อยู่เก็บไว้", "no address on file")
        return ('<span class="ad-dead' + ((" " + cls) if cls else "")
                + '" title="' + att(tip) + '">' + label + "</span>")


    (DOCS / "adhd.css").write_text(CSS)

    reg = json.loads((ROOT / "data" / "curated" / "adhd.json").read_text())

    by_id = {}
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            by_id[r["id"]] = (prov, r)

    # ---- the measured zero, taken live so the sentence heals itself --------
    n_records = sum(len(data.get(p, [])) for p in ("cm", "cr"))
    n_stating = n_psych = 0
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            blob = " ".join(str(v) for v in
                            (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)
            if ADHD_NAME_RX.search(blob):
                n_stating += 1
            if PSYCH_NAME_RX.search(blob):
                n_psych += 1

    def reach_marks(r):
        live, _ = channels(r)
        kinds = [c.get("kind") for c in live] if live and isinstance(live[0], dict) else []
        marks = []
        if r.get("phone") or "phone" in kinds:
            marks.append("☎")
        if "line" in kinds or (r.get("attrs") or {}).get("lineId"):
            marks.append("LINE")
        if "web" in kinds:
            marks.append("🌐")
        return (' <span class="reach">' + " · ".join(marks) + "</span>") if marks else ""

    GRADE_TAG = {
        "stated": ("stated", "บอกเอง", "states ADHD itself",
                   ("ที่นี่พูดถึงสมาธิสั้นไว้เองในช่องทางของตัวเอง",
                    "this place names ADHD in its own published material")),
        "psychiatry": ("psych", "ป้ายบอกว่าจิตเวช", "sign says psychiatry",
                   ("ป้ายของที่นี่บอกว่าเป็นจิตเวช ซึ่งเป็นแผนกที่เรื่องนี้เดินผ่าน — แต่ยังไม่ได้บอกเรื่องสมาธิสั้น",
                    "its own sign says psychiatry — the department this goes through — but it has not said ADHD")),
        "route": ("route", "เส้นทางโรงพยาบาล — ยังไม่ยืนยัน", "hospital route — not confirmed",
                   ("แผนกนี้เป็นแผนกมาตรฐานของโรงพยาบาลระดับนี้ แต่ยังไม่มีใครยืนยันของที่นี่ — โทรถามก่อน",
                    "the department is standard for this class of hospital, but nobody has confirmed this one — ring first")),
        "unread": ("unread", "อ่านหน้าเว็บไม่ได้ — บันทึกไว้ตรง ๆ", "its own page would not open for us",
                   ("หน้าเว็บของที่นี่เปิดไม่ได้จากเครื่องนี้ จึงไม่บันทึกว่ามีบริการอะไร",
                    "its own page could not be read from this machine, so nothing about its services is recorded")),
    }

    def srcs_html(row):
        return "".join(
            " " + out_a(s["ref"], "[" + str(i + 1) + "]")
            for i, s in enumerate(row.get("sources") or []))

    def row_html(row):
        cls, tag_th, tag_en, title_pair = GRADE_TAG.get(
            row.get("grade"), GRADE_TAG["route"])
        tag = ('<span class="ad-grade ' + cls + '" title="'
               + att(bi_text(*title_pair)) + '">' + bi(tag_th, tag_en) + "</span>")
        srcs = srcs_html(row)
        reach = ""
        if row.get("reach_th") or row.get("reach_en"):
            reach = ('<span class="states">' + bi(row.get("reach_th") or "", row.get("reach_en") or "")
                     + "</span>")
        states = ('<span class="states">' + bi(row.get("states_th") or "", row.get("states_en") or "")
                  + ('<span class="srcs">' + srcs + "</span>" if srcs else "")
                  + "</span>")
        pid = row.get("place")
        if pid and pid in by_id:
            prov, r = by_id[pid]
            link = ('<a href="' + prov + "/p/" + place_slug(r) + '.html">'
                    + name_bi(r) + "</a>")
            return "<li>" + link + " " + tag + reach_marks(r) + states + reach + "</li>"
        if pid:
            print(f"  adhd: register row {row.get('key')} names unknown id {pid} — row skipped")
            return ""
        nm = bi(row.get("name_th") or "", row.get("name_en") or "")
        return "<li>" + nm + " " + tag + states + reach + "</li>"

    sections = {k: [] for k in GRADE_ORDER}
    for row in reg.get("rows") or []:
        h = row_html(row)
        if h and row.get("grade") in sections:
            sections[row["grade"]].append(h)

    def sec(title_th, title_en, note_th, note_en, items):
        if not items:
            return ""
        return ("<h2>" + bi(title_th, title_en) + ' <span class="count">('
                + str(len(items)) + ")</span></h2>"
                + ('<p class="ad-note">' + bi(note_th, note_en) + "</p>"
                   if note_th or note_en else "")
                + '<ul class="ad-list">' + "".join(items) + "</ul>")

    # ---- the molecule fork -------------------------------------------------
    CARRY_FLAG = {
        "prohibited": ("no", "นำเข้าไม่ได้", "cannot be brought in"),
        "permitted-limited": ("limited", "พกเข้ามาได้ มีเงื่อนไข", "may be carried in, with papers"),
        "permitted": ("ok", "พกเข้ามาได้", "may be carried in"),
        # A molecule nobody has ruled on. The default below points HERE and not
        # at permitted-limited, because a missing verdict rendered as "may be
        # carried in, with papers" would be this page inventing the one fact it
        # exists to keep honest.
        "unstated": ("ask", "ยังไม่มีคำตัดสิน", "no verdict on file"),
    }
    mol_rows = []
    for m in reg.get("molecules") or []:
        fcls, fth, fen = CARRY_FLAG.get(m.get("carry"), CARRY_FLAG["unstated"])
        flag = ('<span class="ad-flag ' + fcls + '">' + bi(fth, fen) + "</span>")
        quote = ""
        if m.get("quote_th") or m.get("quote_en"):
            q = bi(m.get("quote_th") or "", m.get("quote_en") or "")
            if m.get("quote_src"):
                q += " " + out_a(m["quote_src"], bi("ที่มา", "source"))
            quote = '<span class="quote">' + q + "</span>"
        nlem = ""
        if m.get("nlem_th") or m.get("nlem_en"):
            n = bi(m.get("nlem_th") or "", m.get("nlem_en") or "")
            if m.get("nlem_src"):
                n += " " + out_a(m["nlem_src"], bi("บัญชียาหลักแห่งชาติ", "national list"))
            nlem = '<span class="quote">' + n + "</span>"
        mol_rows.append(
            "<li><span class=\"gen\">" + bi(m.get("generic_th") or "", m.get("generic_en") or "")
            + "</span> " + flag
            + '<span class="known">' + bi("ชื่อการค้าที่พบบ่อย: ", "often sold as: ")
            + esc(m.get("known_as") or "") + "</span>"
            + '<span class="cls">' + bi(m.get("class_th") or "", m.get("class_en") or "") + "</span>"
            + '<span class="carry">' + bi(m.get("carry_th") or "", m.get("carry_en") or "") + "</span>"
            + quote + nlem
            + '<span class="srcs">' + srcs_html(m) + "</span></li>")

    tv = reg.get("travel") or {}
    tool = (
        '<div class="ad-tool"><span class="ask">'
        + bi("ตรวจยาของตัวเองกับ อย. โดยตรง",
             "Check your own medicine against the authority itself")
        + "</span>"
        + "<p>" + bi(
            "อย. มีเครื่องมือออนไลน์ที่บอกได้ว่ายาที่คุณกินอยู่จัดเป็นประเภทไหน และพกเข้าประเทศไทยได้หรือไม่ — "
            "ค้นด้วยชื่อสามัญทางยา ไม่ใช่ชื่อการค้าบนกล่อง",
            "The Thai FDA runs an online checker that will tell you which class your own "
            "medicine falls in and whether it may be carried into Thailand. It searches on "
            "the generic name — the small print on the box, not the big print.")
        + "</p><p>"
        + out_a(tv.get("tool_url"),
                bi("เปิดเครื่องมือตรวจสอบยา (อย.)", "Open the FDA drug checker"))
        + " · "
        + out_a(tv.get("permit_url"), bi("ระบบขออนุญาตพกยา", "the traveller permit system"))
        + "</p>"
        + '<p class="ad-note">' + bi(
            "มดแดงลิงก์เครื่องมือแทนที่จะคัดตารางมาเอง เพราะตารางจะเก่า ส่วนเครื่องมือคือคำตอบของหน่วยงานเอง ณ วันที่คุณกด",
            "Mot Dang links the tool rather than copying its table: a copied table goes "
            "stale, and the tool is the authority's own answer on the day you ask.")
        + "</p></div>")

    reg_html = ('<table class="ad-reg"><tbody>' + "".join(
        "<tr><th>" + bi(q_th, q_en) + "</th><td>" + out_a(url, bi(n_th, n_en)) + "<br>"
        + '<span class="ad-note">' + bi(d_th, d_en) + "</span></td></tr>"
        for q_th, q_en, n_th, n_en, url, d_th, d_en in REGISTERS) + "</tbody></table>")

    gloss_html = ('<table class="ad-gloss"><tbody>' + "".join(
        '<tr><td class="th">' + esc(th) + '</td><td class="rtgs">' + esc(rtgs)
        + "</td><td>" + bi(d_th, d_en) + "</td></tr>"
        for th, rtgs, d_th, d_en in GLOSSARY) + "</tbody></table>")

    zero_note = bi(
        f"วัดเมื่อ 21 ส.ค. 2569 — จาก {n_records:,} รายชื่อในสารบัญทั้งสองจังหวัด "
        f"มี {n_stating} แห่งที่เขียนคำว่าสมาธิสั้นหรือ ADHD ไว้บนป้ายของตัวเอง "
        f"และ {n_psych} แห่งที่เอ่ยถึงจิตเวชหรือพัฒนาการเด็กเลย "
        "ไม่ใช่เพราะไม่มีการรักษา แต่เพราะคลินิกที่นี่ตั้งชื่อตามชื่อหมอ "
        "รายการข้างบนจึงเป็นงานค้นคว้าที่ลงวันที่กำกับไว้ทุกบรรทัด",
        f"Measured 2026-08-21: of {n_records:,} names in this directory, "
        f"{n_stating} state ADHD on their own sign, and {n_psych} mention psychiatry or "
        "child development at all. That is not because the care is absent — it is because "
        "clinics here are named after their doctors. So every row above is researched, "
        "and every line carries its source and its date.")

    # Citeable: an ItemList of the places this page actually resolves, so a
    # machine summarising the corpus gets the register rather than the prose.
    ld_items = []
    for row in reg.get("rows") or []:
        pid = row.get("place")
        if not (pid and pid in by_id):
            continue
        prov, r = by_id[pid]
        ld_items.append({
            "@type": "ListItem", "position": len(ld_items) + 1,
            "item": {"@type": "MedicalOrganization",
                     "name": row.get("name_th") or r.get("name") or "",
                     "url": BASE + prov + "/p/" + place_slug(r) + ".html"}})
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "สมาธิสั้น เชียงใหม่-เชียงราย — ADHD care, Chiang Mai and Chiang Rai",
          "url": BASE + "adhd.html",
          "itemListElement": ld_items}
    head = ('<link rel="stylesheet" href="adhd.css">'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + "</script>")

    og = shelf_og("cm", "medical") if shelf_og else None

    body = (
        "<h1>" + bi("สมาธิสั้น — ยาและการรักษา", "ADHD — the medicine and the care") + "</h1>"

        + '<p class="ad-intro">' + bi(
            "หลายคนมาถึงเมืองไทยโดยคิดว่าเรื่องนี้จะง่ายกว่าที่บ้าน แล้วพบว่ายากกว่า "
            "ส่วนใหญ่ไม่ใช่เรื่องดวง แต่เป็นเพราะไม่มีใครเขียนข้อมูลนี้ไว้ให้อ่าน "
            "หน้านี้เขียนไว้ให้อ่าน",
            "A lot of people arrive in Thailand expecting this to be the easy part, and "
            "find it is the hard part. That is mostly not luck — it is that nobody wrote "
            "the information down. This page is the information, written down.")
        + "</p>"

        + '<p class="ad-lead">' + bi(
            "สามเรื่องที่มักถูกรวบเป็นเรื่องเดียว: ยาตัวไหนอยู่ในบัญชีอะไร (แน่นอน ตรวจได้) · "
            "ระบบสาธารณสุขมีรูปแบบยาอะไรจริง ๆ (จำกัดกว่าที่คิด) · "
            "และเคาน์เตอร์ตรงหน้าจะทำอะไรให้ (เปลี่ยนไปตามที่ ตามวัน — จึงเป็นคำถามที่ต้องถาม ไม่ใช่กฎที่ท่องได้) "
            "เมื่อรวบสามเรื่องนี้เป็นเรื่องเดียว คนจะสรุปว่าไม่มีช่องทางเลย ทั้งที่มี",
            "Three things get folded into one rumour. Which list a molecule sits in — "
            "settled, and checkable. What the health system actually stocks — narrower "
            "than people expect. And what the desk in front of you will do — which varies "
            "by desk and by day, and is therefore a question to ask rather than a rule to "
            "recite. Folded together, they read as no way in at all. Kept apart, there is "
            "one.")
        + "</p>"

        + "<h2>" + bi("ยาของคุณอยู่ในบัญชีไหน", "Which list your medicine is on") + "</h2>"
        + '<p class="ad-note">' + bi(
            "ตารางนี้บอกสถานะทางกฎหมายของตัวยา ซึ่งเป็นเรื่องของการนำเข้าและการหาซื้อ "
            "ไม่ใช่คำแนะนำว่าใครควรกินอะไร และไม่มีขนาดยาอยู่ในหน้านี้เลย",
            "This table gives the legal status of a substance, which is a question about "
            "import and supply. It is not a recommendation about what anyone should take, "
            "and there is no dose anywhere on this page.")
        + "</p>"
        + '<ul class="ad-mol">' + "".join(mol_rows) + "</ul>"
        + tool

        + '<p class="ad-lead">' + bi(
            "ความต่างระหว่างสองบรรทัดแรกคือเหตุผลที่หน้านี้มีอยู่ "
            "ยากลุ่มแอมเฟตามีนที่หมอที่บ้านสั่งให้ทุกวัน อยู่ในบัญชีเดียวกับยาบ้าในสายตากฎหมายไทย "
            "ขณะที่ยาบ้าเป็นของที่หาได้ง่ายและถูกกว่าในตลาดมืด "
            "ช่องทางที่ถูกกฎหมายจึงแคบกว่าที่คนคาด และช่องทางที่ผิดกฎหมายกว้างกว่าที่ควร "
            "ความไม่สมดุลนี้คือสิ่งที่หน้านี้พยายามแก้ด้วยข้อมูล — รู้ว่าทางที่ถูกกฎหมายอยู่ตรงไหน มีค่ามาก",
            "The distance between the first two rows is the reason this page exists. The "
            "amphetamine-family medicine a doctor at home prescribes as a matter of routine "
            "sits, in Thai law, on the same list as the street tablet — while the street "
            "tablet is the cheap and available thing. So the lawful channel is narrower "
            "than people expect and the unlawful one is wider than it should be. That "
            "asymmetry is what information can actually fix. Knowing where that lawful "
            "channel runs, and that it exists, is worth a great deal.")
        + "</p>"

        + "<h2>" + bi("พกยาของตัวเองเข้ามา", "Bringing your own") + "</h2>"
        + '<ul class="ad-three">'
        + "<li>" + bi(
            f"วัตถุออกฤทธิ์ประเภท 2-4 — ไม่เกิน {tv.get('psychotropic_days_no_permit', 30)} วัน "
            "พกได้พร้อมใบสั่งยาหรือใบรับรองแพทย์ ไม่ต้องขออนุญาต",
            f"Psychotropic substances in categories 2–4: up to a "
            f"{tv.get('psychotropic_days_no_permit', 30)}-day supply with your prescription "
            "or a doctor's certificate, no permit needed.") + "</li>"
        + "<li>" + bi(
            f"เกิน {tv.get('psychotropic_days_no_permit', 30)} วัน ถึง {tv.get('psychotropic_days_permit', 90)} วัน "
            f"— ต้องขออนุญาต อย. ล่วงหน้าอย่างน้อย {tv.get('lead_time_days', 15)} วัน "
            f"ระบบใช้เวลาพิจารณาราว {tv.get('processing_days', 3)} วันทำการ",
            f"From {tv.get('psychotropic_days_no_permit', 30)} up to "
            f"{tv.get('psychotropic_days_permit', 90)} days: an FDA permit, applied for at "
            f"least {tv.get('lead_time_days', 15)} days before travel; the system states "
            f"roughly {tv.get('processing_days', 3)} working days to process.") + "</li>"
        + "<li>" + bi(
            "ยาเสพติดให้โทษประเภท 1 — ไม่มีใบอนุญาตให้ขอ นี่คือจุดที่ต้องรู้ก่อนซื้อตั๋ว",
            "Narcotic category 1: there is no permit to apply for. This is the thing to "
            "know before the ticket is booked, not at the airport.") + "</li>"
        + "<li>" + bi(
            esc(tv.get("customs_th") or ""), esc(tv.get("customs_en") or "")) + "</li>"
        + "</ul>"
        + '<p class="ad-note">' + bi(
            "ที่มา: หน้าคำแนะนำสำหรับผู้เดินทางของ อย. อ่านเมื่อ 21 ส.ค. 2569",
            "Source: the Thai FDA's own guidance page for travellers under treatment, read "
            "2026-08-21.")
        + " " + out_a(tv.get("guidance_url"), bi("อ่านต้นทาง", "read it at the source"))
        + "</p>"

        + "<h2>" + bi("รูปแบบยาคือของหายาก ไม่ใช่ตัวยา",
                      "The scarce thing is the formulation, not the substance") + "</h2>"
        + '<p class="ad-intro">' + bi(
            "เมทิลเฟนิเดตอยู่ในบัญชียาหลักแห่งชาติ — บัญชี ค เฉพาะรูปแบบเม็ด 10 มก. "
            "โดยระบุเงื่อนไขการใช้ไว้ว่าสำหรับ ADHD และ narcolepsy "
            "แปลว่าตัวยามีอยู่ในระบบจริง แต่คนที่ใช้ยาชนิดออกฤทธิ์นานอยู่เดิม "
            "กำลังเจอปัญหาเรื่องรูปแบบยา ไม่ใช่ปัญหาว่าตัวยาผิดกฎหมาย — "
            "และสองอย่างนี้แก้คนละวิธีกัน",
            "Methylphenidate is on the National List of Essential Medicines under บัญชี ค, "
            "as a tablet in the 10 mg strength only, with ADHD and narcolepsy named as its "
            "conditions of use. So the substance is in the system. But someone arriving on "
            "a long-acting formulation is meeting a supply problem, not a legality problem "
            "— and those two are solved in completely different ways. It is worth knowing "
            "which one you actually have.")
        + "</p>"
        + '<p class="ad-note">' + bi(
            "และเพราะเป็นวัตถุออกฤทธิ์ประเภท 2 กฎหมายให้เฉพาะกระทรวงสาธารณสุขหรือผู้ที่กระทรวงมอบหมายเท่านั้นที่นำเข้าหรือขายได้ "
            "นั่นคือเหตุผลเชิงโครงสร้างว่าทำไมของสิ่งนี้ถึงอยู่ที่โรงพยาบาล ไม่ใช่ที่ร้านขายยาหัวมุม",
            "And because it is a category-2 psychotropic, the law reserves import and sale "
            "to the Ministry of Public Health or a party it authorises. That is the "
            "structural reason this lives in a hospital rather than at the pharmacy on the "
            "corner — not a shopkeeper's caution, a schedule.")
        + "</p>"

        + sec("ที่ที่พูดถึงสมาธิสั้นไว้เอง", "Places that name ADHD themselves",
              "อ่านจากเว็บของแต่ละที่เอง ยกมาตามคำของเขา พร้อมวันที่",
              "Read on each place's own site and quoted in its own terms, with the date.",
              sections["stated"])
        + sec("จิตเวช — ป้ายบอกแค่นี้ และเราบอกแค่นี้",
              "Psychiatry — what the sign says, and no more",
              "ที่เหล่านี้บอกว่าเป็นจิตเวช ซึ่งเป็นแผนกที่เรื่องนี้เดินผ่านที่นี่ แต่ยังไม่มีใครยืนยันเรื่องสมาธิสั้น — โทรถามก่อน",
              "These state psychiatry, which is the department this care runs through here. "
              "None of them has been confirmed for ADHD specifically — ring first, and ask "
              "the questions further down this page.",
              sections["psychiatry"])
        + sec("เส้นทางโรงพยาบาล — น่าจะมี แต่ยังไม่ยืนยัน",
              "The hospital route — likely, not yet confirmed",
              "โรงพยาบาลมหาวิทยาลัยและโรงพยาบาลศูนย์คือที่ที่แผนกนี้อยู่เป็นปกติ แต่ยังไม่มีใครโทรยืนยันของที่นี่",
              "University and regional hospitals are where this department normally lives, "
              "but nobody has rung to confirm these.",
              sections["route"])
        + sec("ที่ที่เราเปิดหน้าเว็บไม่ได้ — บอกไว้ตรง ๆ",
              "Where the page would not open for us — said plainly",
              "มดแดงพิมพ์ความพยายามไว้แทนการเดา",
              "Mot Dang prints the attempt rather than a guess.",
              sections["unread"])

        + "<h2>" + bi("คำที่ควรถามที่เคาน์เตอร์", "The questions to ask at the desk") + "</h2>"
        + '<p class="ad-note">' + bi(
            "เพราะเคาน์เตอร์คือส่วนที่เปลี่ยนได้ เราจึงให้คำถาม ไม่ใช่คำตอบที่ท่องมา",
            "Because the desk is the part that varies, what follows is questions rather "
            "than answers recited in advance.")
        + "</p>"
        + '<ul class="ad-ask">'
        + "<li>" + bi("ที่นี่มีจิตแพทย์ที่ตรวจผู้ใหญ่ไหม หรือรับเฉพาะเด็กและวัยรุ่น",
                      "Do you have a psychiatrist who assesses adults, or is this clinic "
                      "for children and adolescents only? (The published clinics here are "
                      "mostly paediatric — worth asking before travelling to one.)") + "</li>"
        + "<li>" + bi("นัดแรกต้องรอกี่วัน และมีคลินิกพิเศษนอกเวลาไหม",
                      "How long is the wait for a first appointment, and do you run an "
                      "after-hours specialist clinic (คลินิกพิเศษนอกเวลา)?") + "</li>"
        + "<li>" + bi("ต้องเอาเอกสารการวินิจฉัยจากต่างประเทศมาด้วยไหม และต้องแปลเป็นไทยหรือเปล่า",
                      "Do you want my diagnosis records from abroad, and do they need a "
                      "Thai translation?") + "</li>"
        + "<li>" + bi("ที่นี่จ่ายยาเองได้ไหม หรือต้องไปรับที่ไหน",
                      "Can you dispense here, or does the prescription have to be filled "
                      "somewhere else?") + "</li>"
        + "<li>" + bi("นัดติดตามผลถี่แค่ไหน และค่าใช้จ่ายต่อครั้งประมาณเท่าไร",
                      "How often would follow-up appointments be, and roughly what does "
                      "each visit cost?") + "</li>"
        + "<li>" + bi("ขอใบรับรองแพทย์เป็นภาษาอังกฤษได้ไหม",
                      "Can I be given a doctor's certificate in English? (This is the paper "
                      "that travels.)") + "</li>"
        + "</ul>"

        + '<p><a class="bt-sheet" href="reader/adhd-words.pdf">\U0001F4C4 '
        + bi("ดาวน์โหลดแผ่นคำที่ใช้ที่เคาน์เตอร์ (PDF)",
             "Download the desk sheet (PDF) — the same words, printable, point at the Thai")
        + "</a></p>"
        + "<h2>" + bi("ตรวจสอบได้ที่ไหน", "Where to check things for yourself") + "</h2>"
        + '<p class="ad-note">' + bi(
            "ทุกแห่งเป็นทะเบียนหรือเครื่องมือของหน่วยงานทางการ ตรวจแล้วว่าเข้าถึงได้เมื่อ 21 ส.ค. 2569",
            "Every one is an official register or an official tool, verified reachable "
            "2026-08-21.")
        + "</p>" + reg_html

        + "<h2>" + bi("คำบนป้ายและบนแบบฟอร์ม", "The words on the sign and on the form") + "</h2>"
        + '<p class="ad-note">' + bi(
            "อักษรไทย · คำอ่านแบบ RTGS · ความหมาย — เทียบรูปคำกับป้ายได้แม้อ่านไทยไม่ออก",
            "Thai script · RTGS spelling · what it means — enough to match a word by its "
            "shape, without reading Thai.")
        + "</p>" + gloss_html

        + '<p class="ad-note">' + zero_note + "</p>"

        + '<p class="ad-note">' + bi(
            "มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ และไม่ใช่การรับรองคุณภาพ "
            "หน้านี้ไม่มีความเห็นว่าใครควรกินอะไร ไม่ระบุขนาดยา และไม่แนะนำยี่ห้อหรือแพทย์คนใด "
            "ข้อมูลสถานพยาบาลบางส่วนมาจาก OpenStreetMap (ODbL 1.0) และจากหน้าเว็บของแต่ละที่ตามวันที่ที่ระบุ "
            "กฎหมายและรายการยาเปลี่ยนได้ — ตรวจกับต้นทางที่ลิงก์ไว้เสมอ "
            "เห็นอะไรที่เปลี่ยนไปหรือควรเพิ่ม บอกมดได้ที่หน้าเสนอแนะ",
            "Mot Dang is a directory of places. It is not medical advice, not a referral, "
            "and not a quality guarantee. This page holds no view on what anyone should "
            "take, names no dose, and recommends no brand and no doctor. Some facility data "
            "is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap contributors, and "
            "from each place's own pages on the dates shown. Schedules and medicine lists "
            "change — always check against the linked source. If something here has changed "
            "or is missing, tell the ants via the suggestion page.")
        + "</p>"
        + share_block(BASE + "adhd.html", "สมาธิสั้น เชียงใหม่ · มดแดง", card=og))

    (DOCS / "adhd.html").write_text(page(
        "สมาธิสั้น เชียงใหม่ · ADHD medicine and care, Chiang Mai",
        body, depth=0, path="adhd.html",
        desc=bi_text(
            "สมาธิสั้นในเชียงใหม่และเชียงราย — ยาแต่ละตัวอยู่ในบัญชีไหนตามกฎหมายไทย "
            "พกยาของตัวเองเข้ามาได้แค่ไหน ตรวจกับ อย. เองได้ที่ไหน "
            "ที่ไหนพูดถึงสมาธิสั้นไว้เอง และคำไทยบนป้ายกับบนแบบฟอร์มแปลว่าอะไร",
            "ADHD in Chiang Mai and Chiang Rai: which Thai schedule each medicine sits in, "
            "how much of your own supply you may carry in and what paper it needs, the "
            "FDA's own checker for your specific medicine, which places state this care "
            "themselves, and what the Thai words on the sign and the form mean"),
        extra_head=head, og=og,
        crumbs='<a href="index.html">' + bi("หน้าแรก", "Home") + "</a> › "
               + bi("สมาธิสั้น", "ADHD")))

    return (f"{len(sections['stated'])} stated · {len(sections['psychiatry'])} psychiatry · "
            f"{len(sections['route'])} route · {len(sections['unread'])} unread · "
            f"{len(mol_rows)} molecules · {n_stating} of {n_records:,} records name "
            f"this care themselves")
