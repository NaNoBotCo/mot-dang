#!/usr/bin/env python3
"""ของฝากที่เดินทางได้ — souvenirs and the wild things (/souvenir.html). WO-32.

WHY THIS PAGE EXISTS. The conservation status of Thailand's animals and
plants meets a traveller twice: once in a shop, where a beautiful thing has
no label saying what it is made of, and once at an airport, where the label
is suddenly the only thing that matters. The gap between those two moments
is where souvenirs get seized and holidays end in an interview room — and it
is an information gap, which is a directory's kind of problem.

Three things get folded into one rumour ("you can't take anything",
"everything's fine if you bought it in a shop"), and they have different
answers:

  1. WHICH CLASS a thing sits in — Thai law's tiers (สงวน · คุ้มครอง ·
     ควบคุม) and the CITES appendix. Fixed, published, checkable; and the
     checker is the convention's own live list, so this page links it
     rather than copying a table that will rot. The lists move: the
     preserved list has grown twice since the 2019 act, and the protected
     list has a second edition dated this year.
  2. WHAT PAPER exists where one does — nursery orchids and farmed
     crocodile leather travel every day on documents the seller arranges.
     The question belongs at the till, not the check-in desk.
  3. WHAT HAS NO PAPER for a traveller at all — ivory above everything:
     lawfully sold inside Thailand under its own registration act, and
     still nothing puts a piece of it on a plane. Legal to buy here is not
     legal to fly with. That asymmetry is the page's reason.

WHAT THIS PAGE IS NOT. Not legal advice, and it says so once, plainly. It
recites no penalty tables and hangs no warning skulls — the frame is the
things that DO travel well, which are the region's best work anyway.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
ADHD layer. Emits souvenir.html + souvenir.css.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The census scans, measured live so the page's sentence heals itself.
# A bare word-scan ("tiger", "butterfly") meets namesakes almost entirely —
# ตำบลสันผีเสื้อ, Tiger Mart, orchid hotels — the WO-24 namesake lesson
# again, so the scan the page reports is the targeted one: places whose own
# name says a traveller meets these goods there.
FARM_NAME_RX = re.compile(
    r"ฟาร์ม(?:กล้วยไม้|ผีเสื้อ|งู|จระเข้)|สวนกล้วยไม้"
    r"|orchid\s+farm|butterfly\s+farm|snake\s+farm|crocodile\s+farm",
    re.I)
SHELF_NAME_RX = re.compile(
    r"OTOP|โอทอป|ของที่ระลึก|ของฝาก|หัตถกรรม|souvenir|handicraft", re.I)
NAMESAKE_RX = re.compile(r"เสือ|ผีเสื้อ|กล้วยไม้|tiger|butterfly|orchid", re.I)

CSS = """
.sv-intro{font-size:1.02rem;max-width:46rem}
.sv-note{font-size:.86rem;opacity:.78;max-width:46rem}
.sv-lead{max-width:46rem;border-left:3px solid rgba(0,0,0,.22);padding:.1rem 0 .1rem .9rem;
  margin:.9rem 0;font-size:1.02rem;line-height:1.6}
.sv-tool{max-width:46rem;border:1px solid rgba(0,0,0,.16);border-radius:.8rem;
  padding:.8rem 1rem;margin:1rem 0;background:rgba(0,0,0,.02)}
.sv-tool .ask{font-weight:600;display:block;margin-bottom:.25rem}
.sv-items{list-style:none;padding-left:0;max-width:46rem;margin:.6rem 0}
.sv-items li{padding:.6rem 0;border-bottom:1px solid rgba(0,0,0,.09);line-height:1.55}
.sv-items .nm{font-weight:600}
.sv-items .seen{font-size:.84rem;opacity:.72;display:block}
.sv-items .cls{display:block;font-size:.9rem;margin-top:.2rem}
.sv-items .carry{display:block;font-size:.88rem;margin-top:.18rem}
.sv-items .srcs{font-size:.76rem;opacity:.65}
.sv-flag{display:inline-block;font-size:.72rem;padding:.08rem .42rem;border-radius:.7rem;
  border:1px solid currentColor;opacity:.9;vertical-align:.08em;white-space:nowrap}
.sv-flag.no{color:#8a3a2a}
.sv-flag.papers{color:#7a5a12}
.sv-flag.ok{color:#1c6b3a}
.sv-flag.ask{color:#4a4a52}
.sv-laws{list-style:none;padding-left:0;max-width:46rem}
.sv-laws li{padding:.5rem 0;border-bottom:1px solid rgba(0,0,0,.07);line-height:1.55}
.sv-laws .nm{font-weight:600}
.sv-dead{text-decoration:underline dotted;text-underline-offset:.18em;
  opacity:.72;cursor:help}
.sv-ask{margin:.4rem 0 .2rem;padding-left:1.1rem;font-size:.94rem;line-height:1.6;
  max-width:46rem}
.sv-reg{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.sv-reg th,.sv-reg td{text-align:left;vertical-align:top;padding:.42rem .5rem;
  border-bottom:1px solid rgba(0,0,0,.09)}
.sv-reg th{font-weight:600;white-space:nowrap}
.sv-gloss{border-collapse:collapse;width:100%;max-width:52rem;font-size:.92rem}
.sv-gloss td{padding:.34rem .5rem;border-bottom:1px solid rgba(0,0,0,.07);vertical-align:top}
.sv-gloss .th{font-size:1.06rem;white-space:nowrap}
.sv-gloss .rtgs{opacity:.72;font-style:italic;white-space:nowrap}
@media (max-width:640px){.sv-reg,.sv-gloss{font-size:.86rem}
  .sv-reg th{white-space:normal}}
"""

# Every one an official register or tool, verified reachable 2026-08-26 from
# this machine. The two CITES.org pages that refused a plain fetch that day
# are in wildlife.json attempted[] and are named on the page as refusals,
# not linked as registers.
REGISTERS = [
    ("ชนิดนี้อยู่บัญชีไซเตสไหน — ตรวจเองได้",
     "Which CITES appendix is this species in? Check it yourself",
     "Checklist of CITES Species",
     "The convention's own species checklist",
     "https://checklist.cites.org/",
     "พิมพ์ชื่อชนิด (ไทยหรือชื่อวิทยาศาสตร์) แล้วบัญชีที่ชนิดนั้นอยู่จะแสดงทันที — บัญชีของอนุสัญญาเอง ณ วันที่คุณกด",
     "Type the species and its appendix comes back — the convention's own "
     "list, current on the day you ask."),
    ("ใบอนุญาตไซเตสของไทย ขอที่ไหน",
     "Where Thailand's CITES permits come from",
     "ระบบไซเตสไทย — กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช",
     "CITES Thailand e-permit portal (DNP)",
     "https://cites.dnp.go.th/",
     "ระบบยื่นขอใบอนุญาตนำเข้า-ส่งออกสัตว์ป่าและพืชป่าตามอนุสัญญา พร้อมคู่มือประชาชน · โทร 02-561-4838",
     "The national permit system for CITES import and export, with its own "
     "public manual · tel 02-561-4838."),
    ("ของต้องห้าม-ต้องกำกัด ที่สนามบิน",
     "What the airport's own list says",
     "กรมศุลกากร — ข้อแนะนำผู้โดยสาร",
     "Thai Customs — guidelines for airport passengers",
     "https://www.customs.go.th/content.php?ini_content=individual_160426_01&lang=en&left_menu=menu_individual_submenu_01_160421_01",
     "รายการของต้องห้ามระบุสัตว์ป่าสงวนและสัตว์ป่าตามไซเตสไว้ตรง ๆ และบอกว่าใบอนุญาตพืชอยู่ที่กรมวิชาการเกษตร สัตว์มีชีวิตอยู่ที่กรมปศุสัตว์",
     "The prohibited list names reserved and CITES-listed wildlife in so "
     "many words, and says which department issues which permit — plants "
     "at the Department of Agriculture, live animals at Livestock "
     "Development."),
    ("ตัวบทกฎหมายไทย — ทั้งชุด",
     "The Thai statutes themselves, as a set",
     "กองกฎหมาย กรมอุทยานฯ — พ.ร.บ.สงวนและคุ้มครองสัตว์ป่า 2562 และกฎหมายลูก",
     "DNP legal affairs — the 2019 act and its subordinate regulations",
     "https://portal.dnp.go.th/Content/LegalAffairs?contentId=22540",
     "พ.ร.บ. ฉบับไทยและอังกฤษ พระราชกฤษฎีกาสัตว์ป่าสงวน กฎกระทรวงสัตว์ป่าคุ้มครอง และประกาศสัตว์ป่าควบคุม รวมไว้หน้าเดียว",
     "The act in Thai and English, the preserved-species decree, the "
     "protected-species regulations and the controlled-wildlife "
     "announcements, on one page."),
]

# Thai script · RTGS · what it means. Enough to match a word on a sign, a
# receipt or a customs form by its shape, without reading Thai.
GLOSSARY = [
    ("สัตว์ป่าสงวน", "sat pa sa-nguan",
     "ชนิดหายากที่สุด 21 ชนิด ห้ามค้าห้ามครอบครอง",
     "Preserved wildlife — the rarest tier, 21 species. สัตว์ sat, animal "
     "(Sanskrit sattva) + ป่า pa, forest/wild + สงวน sa-nguan, to reserve."),
    ("สัตว์ป่าคุ้มครอง", "sat pa khum-khrong",
     "บัญชียาวตามกฎกระทรวง — ค้าหรือส่งออกต้องมีใบอนุญาต",
     "Protected wildlife — the long list. คุ้มครอง khum-khrong, to protect. "
     "This is the phrase on the poster at the wildlife checkpoint."),
    ("สัตว์ป่าควบคุม", "sat pa khuap-khum",
     "ชนิดตามอนุสัญญาไซเตสที่ต้องแจ้งครอบครอง",
     "Controlled wildlife — the CITES-convention tier, possession notified "
     "rather than banned."),
    ("ไซเตส", "sai-tet",
     "อนุสัญญาว่าด้วยการค้าระหว่างประเทศซึ่งชนิดสัตว์ป่าและพืชป่าที่ใกล้สูญพันธุ์",
     "CITES, said the Thai way — the convention on international trade in "
     "endangered species. The word on the permit and on the seizure notice "
     "alike."),
    ("งาช้าง", "nga chang",
     "งา nga คืองาช้าง — คำนี้บนป้ายร้านคือสัญญาณให้ถามให้ชัด",
     "Ivory — งา nga, tusk + ช้าง chang, elephant. On a shop sign, it is "
     "the word to recognise before falling in love with a bangle."),
    ("กล้วยไม้ป่า", "kluai-mai pa",
     "กล้วยไม้ที่ขุดจากป่า ต่างจากของสวนเพาะเลี้ยง",
     "A wild orchid — กล้วยไม้ kluai-mai, orchid (literally banana-wood) + "
     "ป่า pa, wild. The one word separating the lawful pot from the "
     "unlawful clump."),
    ("ใบอนุญาตส่งออก", "bai a-nu-yat song-ok",
     "เอกสารที่ทำให้ของบัญชี 2 ขึ้นเครื่องได้",
     "An export permit — the paper that puts an Appendix-II thing on a "
     "plane. บาย bai, sheet; อนุญาต a-nu-yat, permission (Pali anuñāta)."),
    ("ใบรับรองสุขอนามัยพืช", "bai rap-rong suk-a-na-mai phuet",
     "เอกสารพืชจากกรมวิชาการเกษตร ที่สวนกล้วยไม้จัดให้ได้",
     "The phytosanitary certificate — the plant-health paper from the "
     "Department of Agriculture that an exporting orchid farm arranges."),
    ("ด่านตรวจสัตว์ป่า", "dan truat sat pa",
     "ด่านของกรมอุทยานฯ ที่สนามบินและชายแดน",
     "The wildlife checkpoint — the DNP desk at airports and land "
     "borders, separate from customs and looking for exactly this page's "
     "subject matter."),
]


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")
    verdict, BROKEN = g["verdict"], g["BROKEN"]
    BROKEN_WHY = g["BROKEN_WHY"]
    LINK_HEALTH_DATE = g.get("LINK_HEALTH_DATE") or ""

    def out_a(url, label, cls=""):
        """One outbound link — or the address of one that has stopped answering.

        Same rule as the ADHD layer, for the same reason: a dead ref keeps
        its place and its address, carries the verdict and the date of the
        check in its tooltip, and stops being a door
        (tests/test_publish_gate.py holds the whole site to it).
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
        return ('<span class="sv-dead' + ((" " + cls) if cls else "")
                + '" title="' + att(tip) + '">' + label + "</span>")

    (DOCS / "souvenir.css").write_text(CSS)

    reg = json.loads((ROOT / "data" / "curated" / "wildlife.json").read_text())

    # ---- the census, taken live so the sentence heals itself ---------------
    n_records = sum(len(data.get(p, [])) for p in ("cm", "cr"))
    n_farm = n_shelf = n_namesake = 0
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            blob = " ".join(str(v) for v in
                            (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)
            if FARM_NAME_RX.search(blob):
                n_farm += 1
            if SHELF_NAME_RX.search(blob):
                n_shelf += 1
            if NAMESAKE_RX.search(blob):
                n_namesake += 1

    def srcs_html(row):
        return "".join(
            " " + out_a(s["ref"], "[" + str(i + 1) + "]")
            for i, s in enumerate(row.get("sources") or []))

    CARRY_FLAG = {
        "no": ("no", "ไม่มีทางพาไป", "no traveller path exists"),
        "papers": ("papers", "ไปได้เมื่อมีเอกสาร", "travels with papers"),
        "ask": ("ask", "แล้วแต่ชนิด — ถามก่อนจ่าย", "species-dependent — ask before paying"),
        "ok": ("ok", "เดินทางได้สบาย", "travels easily"),
    }

    item_rows = []
    for it in reg.get("items") or []:
        fcls, fth, fen = CARRY_FLAG.get(it.get("carry"), CARRY_FLAG["ask"])
        flag = '<span class="sv-flag ' + fcls + '">' + bi(fth, fen) + "</span>"
        check = ""
        if it.get("check"):
            check = " " + out_a(it["check"], bi("ตรวจชนิดนี้", "check this species"))
        item_rows.append(
            '<li><span class="nm">' + bi(it.get("name_th") or "", it.get("name_en") or "")
            + "</span> " + flag
            + '<span class="seen">' + bi("ที่เจอบ่อย: " + (it.get("seen_th") or ""),
                                         "seen as: " + (it.get("seen_en") or "")) + "</span>"
            + '<span class="cls">' + bi(it.get("class_th") or "", it.get("class_en") or "")
            + check + "</span>"
            + '<span class="carry">' + bi(it.get("carry_th") or "", it.get("carry_en") or "")
            + "</span>"
            + '<span class="srcs">' + srcs_html(it) + "</span></li>")

    law_rows = []
    for lw in reg.get("laws") or []:
        law_rows.append(
            '<li><span class="nm">' + bi(lw.get("name_th") or "", lw.get("name_en") or "")
            + "</span><br>" + bi(lw.get("what_th") or "", lw.get("what_en") or "")
            + '<span class="srcs">' + srcs_html(lw) + "</span></li>")

    tool = (
        '<div class="sv-tool"><span class="ask">'
        + bi("ตรวจชนิดกับบัญชีของอนุสัญญาเอง",
             "Check any species against the convention's own list")
        + "</span>"
        + "<p>" + bi(
            "อนุสัญญาไซเตสมีบัญชีชนิดออนไลน์ให้ค้นเอง — พิมพ์ชื่อชนิดแล้วบัญชีที่ชนิดนั้นอยู่จะแสดงทันที "
            "มดแดงลิงก์เครื่องมือแทนการคัดตาราง เพราะตารางจะเก่า แต่บัญชีของอนุสัญญาคือคำตอบ ณ วันที่คุณกด",
            "CITES keeps its species list online and searchable — type a species and "
            "its appendix comes back. Mot Dang links the tool rather than copying its "
            "table: a copied table goes stale, and the checklist is the convention's "
            "own answer on the day you ask.")
        + "</p><p>"
        + out_a("https://checklist.cites.org/",
                bi("เปิดบัญชีชนิดไซเตส", "Open the CITES species checklist"))
        + " · "
        + out_a("https://cites.dnp.go.th/",
                bi("ระบบใบอนุญาตไซเตสไทย (กรมอุทยานฯ)", "Thailand's CITES permit portal (DNP)"))
        + "</p></div>")

    reg_html = ('<table class="sv-reg"><tbody>' + "".join(
        "<tr><th>" + bi(q_th, q_en) + "</th><td>" + out_a(url, bi(n_th, n_en)) + "<br>"
        + '<span class="sv-note">' + bi(d_th, d_en) + "</span></td></tr>"
        for q_th, q_en, n_th, n_en, url, d_th, d_en in REGISTERS) + "</tbody></table>")

    gloss_html = ('<table class="sv-gloss"><tbody>' + "".join(
        '<tr><td class="th">' + esc(th) + '</td><td class="rtgs">' + esc(rtgs)
        + "</td><td>" + bi(d_th, d_en) + "</td></tr>"
        for th, rtgs, d_th, d_en in GLOSSARY) + "</tbody></table>")

    attempted_html = ""
    if reg.get("attempted"):
        attempted_html = (
            '<p class="sv-note">' + bi(
                "สองหน้าเว็บทางการที่เปิดไม่ได้จากเครื่องนี้ (2026-08-26) บันทึกไว้ตรง ๆ แทนการเดา: ",
                "Two official pages would not open from this machine (2026-08-26), "
                "recorded plainly rather than guessed at: ")
            + " · ".join(esc(a["ref"]) for a in reg["attempted"])
            + "</p>")

    census_note = bi(
        f"วัดเมื่อ 26 ส.ค. 2569 — จาก {n_records:,} รายชื่อในสารบัญทั้งสองจังหวัด "
        f"มี {n_farm} แห่งที่ชื่อบอกเองว่าเป็นฟาร์มหรือสวนของสิ่งเหล่านี้ "
        f"และ {n_shelf} แห่งบนชั้นของฝาก-หัตถกรรม "
        f"ส่วนการค้นคำว่า เสือ ผีเสื้อ กล้วยไม้ ตรง ๆ เจอ {n_namesake} รายชื่อ "
        "ซึ่งเกือบทั้งหมดเป็นชื่อพ้อง — ตำบลสันผีเสื้อ ร้านไทเกอร์มาร์ท โรงแรมออร์คิด — "
        "ร้านที่ขายของแบบนี้จริงแทบไม่เขียนไว้บนป้าย หน้านี้จึงเป็นตัวความรู้เอง",
        f"Measured 2026-08-26: of {n_records:,} names in this directory, {n_farm} "
        f"say in their own name that they are a farm or nursery for these things, "
        f"and {n_shelf} sit on the souvenir-and-handicraft rows. A bare scan for "
        f"tiger, butterfly or orchid meets {n_namesake} names — nearly all of them "
        "namesakes: a moth-named subdistrict, Tiger Mart, orchid hotels. The shops "
        "where a traveller actually meets these goods rarely say so on the sign, "
        "which is why this page is the coverage.")

    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "name": "ของฝากที่เดินทางได้ — Souvenirs that travel well",
          "url": BASE + "souvenir.html",
          "inLanguage": ["th", "en"],
          "about": ["CITES", "wildlife protection Thailand",
                    "สัตว์ป่าสงวน", "สัตว์ป่าคุ้มครอง"]}
    head = ('<link rel="stylesheet" href="souvenir.css">'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + "</script>")

    og = shelf_og("cm", "shopping") if shelf_og else None

    body = (
        "<h1>" + bi("ของฝากที่เดินทางได้", "Souvenirs that travel well") + "</h1>"

        + '<p class="sv-intro">' + bi(
            "สถานะคุ้มครองของสัตว์และพืชในเมืองไทยมาเจอนักเดินทางสองครั้ง — "
            "ครั้งแรกในร้าน ที่ของสวยไม่มีป้ายบอกว่าทำจากอะไร "
            "และอีกครั้งที่สนามบิน ที่คำตอบของคำถามนั้นกลายเป็นเรื่องเดียวที่สำคัญ "
            "หน้านี้เขียนช่องว่างระหว่างสองจังหวะนั้นไว้ให้อ่านก่อนควักเงิน",
            "The protection status of Thailand's animals and plants meets a "
            "traveller twice: once in a shop, where a beautiful thing carries no "
            "label saying what it is made of, and once at an airport, where that "
            "answer is suddenly the only thing that matters. This page writes down "
            "the gap between those two moments, to be read before the money moves.")
        + "</p>"

        + '<p class="sv-lead">' + bi(
            "หลักข้อเดียวที่คุ้มครองนักเดินทางได้จริง: ถูกกฎหมายที่จะซื้อในไทย ไม่ได้แปลว่าถูกกฎหมายที่จะพาขึ้นเครื่อง "
            "งาช้างคือตัวอย่างที่คมที่สุด — ร้านในประเทศขายได้ตามระบบทะเบียนของ พ.ร.บ.งาช้าง "
            "แต่ไม่มีเอกสารใดในโลกที่พางาช้างชิ้นนั้นออกนอกประเทศได้อย่างถูกกฎหมายสำหรับนักท่องเที่ยว "
            "ของที่ควรถามคือถามก่อนจ่าย ไม่ใช่ถามที่ด่าน",
            "The one rule that actually protects a traveller: legal to buy in "
            "Thailand is not legal to fly with. Ivory is the sharpest case — shops "
            "here sell it lawfully under a domestic registration act, and no "
            "document anywhere turns that purchase into a lawful export for a "
            "tourist. The moment for the question is at the till, not at the desk.")
        + "</p>"

        + "<h2>" + bi("ของแต่ละอย่าง อยู่ตรงไหนของกฎหมาย",
                      "Where each thing stands") + "</h2>"
        + '<p class="sv-note">' + bi(
            "สถานะทางกฎหมายของสิ่งของ ไม่ใช่คำพิพากษาใคร — ป้ายบอกบัญชี ลิงก์พาไปตรวจชนิดเอง และแหล่งอ้างอิงลงวันที่ทุกแถว",
            "The legal standing of things, not a judgement of anyone. Each row "
            "carries its class, a link to check the species yourself, and dated "
            "sources.")
        + "</p>"
        + '<ul class="sv-items">' + "".join(item_rows) + "</ul>"
        + tool

        + "<h2>" + bi("สี่ชั้นของกฎหมาย ที่ป้ายและใบเสร็จอ้างถึง",
                      "The four tiers the signs and receipts refer to") + "</h2>"
        + '<p class="sv-note">' + bi(
            "บัญชีพวกนี้ขยับได้ — บัญชีสัตว์ป่าสงวนโตขึ้นสองครั้งหลัง พ.ศ. 2562 และกฎกระทรวงสัตว์ป่าคุ้มครองมีฉบับที่สองลงปีนี้ "
            "หน้านี้จึงลิงก์ทะเบียนแทนการลอกรายชื่อ",
            "These lists move — the preserved list has grown twice since 2019, and "
            "the protected-species regulation has a second edition dated this year. "
            "That is why this page links the registers instead of copying names out "
            "of them.")
        + "</p>"
        + '<ul class="sv-laws">' + "".join(law_rows) + "</ul>"

        + "<h2>" + bi("คำที่ควรถามก่อนจ่าย", "The questions to ask before paying") + "</h2>"
        + '<ul class="sv-ask">'
        + "<li>" + bi("ทำจากอะไร ชนิดไหน — ขอชื่อชนิดลงใบเสร็จได้ไหม",
                      "What is it made of, and which species? Can the species go "
                      "on the receipt?") + "</li>"
        + "<li>" + bi("เป็นของเพาะเลี้ยง-เพาะปลูกไหม หรือมาจากป่า",
                      "Is it farmed or nursery-grown, or did it come from the "
                      "wild?") + "</li>"
        + "<li>" + bi("ส่งออกได้ไหม ร้านจัดเอกสารให้หรือเปล่า — ใบอนุญาตไซเตส ใบรับรองสุขอนามัยพืช",
                      "Can it travel, and do you arrange the papers — the CITES "
                      "permit, the phytosanitary certificate?") + "</li>"
        + "<li>" + bi("ประเทศปลายทางของฉันรับของแบบนี้ไหม (ด่านเกษตรปลายทางเป็นประตูที่สอง)",
                      "Will my destination accept it? Its agriculture desk is the "
                      "second gate, after Thailand's.") + "</li>"
        + "<li>" + bi("ร้านที่ตอบคำถามพวกนี้ได้ทันทีคือร้านที่ค้าถูกต้อง — ร้านที่ตอบไม่ได้ ตอบแทนเราแล้ว",
                      "A shop that answers these at once is a shop trading "
                      "properly. A shop that cannot has answered anyway.") + "</li>"
        + "</ul>"

        + "<h2>" + bi("ตรวจสอบได้ที่ไหน", "Where to check things for yourself") + "</h2>"
        + '<p class="sv-note">' + bi(
            "ทุกแห่งเป็นทะเบียนหรือเครื่องมือของหน่วยงานทางการ ตรวจแล้วว่าเข้าถึงได้เมื่อ 26 ส.ค. 2569",
            "Every one is an official register or an official tool, verified "
            "reachable 2026-08-26.")
        + "</p>" + reg_html
        + attempted_html

        + "<h2>" + bi("คำบนป้าย บนใบเสร็จ และที่ด่าน",
                      "The words on the sign, the receipt and the desk") + "</h2>"
        + '<p class="sv-note">' + bi(
            "อักษรไทย · คำอ่านแบบ RTGS · ความหมาย — เทียบรูปคำกับป้ายได้แม้อ่านไทยไม่ออก",
            "Thai script · RTGS spelling · what it means — enough to match a word "
            "by its shape, without reading Thai.")
        + "</p>" + gloss_html

        + '<p class="sv-note">' + census_note + "</p>"

        + '<p class="sv-note">' + bi(
            "มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำปรึกษาทางกฎหมาย "
            "กฎหมายและบัญชีชนิดเปลี่ยนได้ — ตรวจกับต้นทางที่ลิงก์ไว้เสมอ และของที่ไม่แน่ใจ อย่าซื้อคือคำตอบที่ปลอดภัยเสมอ "
            "เรื่องช้างและงาช้างต่อได้ที่หน้าช้างของมดแดง "
            "เห็นอะไรที่เปลี่ยนไปหรือควรเพิ่ม บอกมดได้ที่หน้าเสนอแนะ",
            "Mot Dang is a directory of places, not legal advice. Laws and species "
            "lists change — always check against the linked source, and for "
            "anything uncertain, not buying is the answer that always works. The "
            "elephant side of this story continues on Mot Dang's elephant page. If "
            "something here has changed or is missing, tell the ants via the "
            "suggestion page.")
        + ' <a href="chang.html">' + bi("หน้าช้าง →", "the elephant page →") + "</a>"
        + "</p>"
        + share_block(BASE + "souvenir.html",
                      "ของฝากที่เดินทางได้ · มดแดง", card=og))

    (DOCS / "souvenir.html").write_text(page(
        "ของฝากที่เดินทางได้ · Souvenirs that travel well",
        body, depth=0, path="souvenir.html",
        desc=bi_text(
            "สถานะคุ้มครองของสัตว์และพืชไทยสำหรับนักเดินทาง — ของฝากชิ้นไหนขึ้นเครื่องได้ "
            "ชิ้นไหนต้องมีเอกสาร และชิ้นไหนไม่มีทางพาไป ตรวจชนิดกับบัญชีไซเตสเองได้ "
            "พร้อมคำที่ควรถามก่อนจ่าย",
            "The protection status of Thailand's animals and plants, for "
            "travellers: which souvenirs board the plane, which travel on papers, "
            "which have no path at all — with the CITES checklist to verify any "
            "species yourself and the questions to ask before paying"),
        extra_head=head, og=og,
        crumbs='<a href="index.html">' + bi("หน้าแรก", "Home") + "</a> › "
               + bi("ของฝากที่เดินทางได้", "Souvenirs that travel well")))

    return (f"{len(item_rows)} items · {len(law_rows)} tiers · "
            f"{n_farm} farm-named · {n_shelf} on the souvenir rows · "
            f"{n_namesake} namesake hits set aside · {n_records:,} records scanned")
