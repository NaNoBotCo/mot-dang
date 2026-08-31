#!/usr/bin/env python3
"""/longcare.html — ดูแลระยะยาว, the long-term-care page. WO-32.

FOUR QUESTIONS people fold into one worried search, kept apart on purpose:
a place for an ageing parent (บ้านพักคนชรา), somewhere to recover after a
hospital lets you out but before you are well (พักฟื้น), a door out of an
addiction (บำบัด), and the retirement that is a LIFE and not a bed. Folding
them together is how a person hunting a convalescent bed ends up reading
rehab brochures, and how a family that needs a nursing home tonight gets a
lifestyle article.

WHAT THE CATALOGUE HELD when somebody counted (2026-08-26, both provinces,
20,700 records): บ้านพักคนชรา 0 · พักฟื้น 0 · hospice 0 · dementia 0 ·
detox 0 in any record's own words. The records that DO exist — a nursing
home, an assisted-living garden, the best-known residential rehab in the
province — stood on the VOLUNTEER shelf, because the importer filed every
amenity=social_facility as volunteering and threw the
social_facility=nursing_home|assisted_living|rehabilitation subtag away.
That rule is fixed (importers/audit_longcare.py, one copy) and this page
stands on the mended shelf.

THE RULE, same as care.html and trans-health.html: the grade rides every
row. `mapped` is a MAPPER's statement (an OSM tag, a sign's own words) —
nobody has read the place's own site yet, and the page says so. `route` is
the door this care ordinarily runs through, not confirmed for this
question. `stated` — the place's own words on its own site — is a grade NO
row here has yet reached; the empty tier is printed, because a register
that hides its best grade being empty is claiming a coverage it does not
have. No rankings, no named clinicians, no outcome claims, no medical
advice; the addiction section especially ranks nothing and recommends
nothing — each facility speaks for itself or not at all.
"""
import json

CSS = """
:root{--lc-ink:#3a2f28;--lc-line:#e4d9cd;--lc-tint:#fbf6f0;
--lc-map:#7a5c1e;--lc-route:#4a5a8a;--lc-quiet:#8a7a62;--lc-state:#2f6b46}
.lc-intro{font-size:1.05rem;line-height:1.65;max-width:62ch}
.lc-h{margin:1.9rem 0 .35rem}
.lc-note{color:var(--lc-quiet);font-size:.92rem;line-height:1.6;max-width:64ch}
.lc-card{border:1px solid var(--lc-line);border-radius:.85rem;padding:.85rem 1rem 1rem;
margin:.9rem 0;background:var(--lc-tint)}
.lc-card h3{margin:.1rem 0 .15rem;font-size:1.12rem}
.lc-where{color:var(--lc-quiet);font-size:.9rem;margin:0 0 .35rem}
.lc-where a{color:inherit}
.lc-tag{display:inline-block;font-size:.76rem;letter-spacing:.03em;text-transform:uppercase;
border:1px solid var(--lc-line);border-radius:.6rem;padding:.05rem .45rem;
background:#fff;margin-left:.35rem;vertical-align:.12em;color:var(--lc-map)}
.lc-tag.route{color:var(--lc-route)}
.lc-said{display:block;color:var(--lc-quiet);font-size:.86rem;line-height:1.5;
margin-top:.3rem;border-left:2px solid var(--lc-line);padding-left:.55rem}
.lc-dead{text-decoration:underline dotted;text-underline-offset:.18em;
opacity:.72;cursor:help}
.lc-tablewrap{overflow-x:auto}
table.lc-tab{border-collapse:collapse;width:100%;font-size:.94rem;min-width:30rem}
table.lc-tab th,table.lc-tab td{border-bottom:1px solid var(--lc-line);
padding:.45rem .6rem;text-align:left;vertical-align:top}
table.lc-tab thead th{border-bottom:2px solid var(--lc-line);white-space:nowrap}
table.lc-gloss td.th{font-size:1.05rem;white-space:nowrap}
table.lc-gloss td.rtgs{color:var(--lc-quiet);font-style:italic;white-space:nowrap}
"""

# Script · RTGS · what it means — the words on these doors, for a reader who
# cannot read the doors. The instrument every walk since womens-health has
# carried; this one covers all four questions.
GLOSSARY = [
    ("บ้านพักคนชรา", "ban phak khon chara", "a home for the aged — the plain, "
     "older phrase. บ้าน house · พัก stay · คนชรา the aged."),
    ("ศูนย์ดูแลผู้สูงอายุ", "sun dulae phu sung ayu", "elder-care centre — the "
     "phrase on most modern signs. ผู้สูงอายุ (the high-in-years) is the "
     "respectful word for the old, and the one to use."),
    ("เนอร์สซิ่งโฮม", "noesing hom", "nursing home, borrowed whole from English "
     "and written in Thai letters — on real signs both with and without ร์."),
    ("ผู้ป่วยติดเตียง", "phu puai tit tiang", "a bed-bound patient — ติดเตียง "
     "is literally 'stuck to the bed'. The phrase that changes which places "
     "can answer at all; say it early."),
    ("พักฟื้น", "phak fuen", "to convalesce — พัก rest · ฟื้น recover/revive. "
     "The gap between discharge and well, and the word the corpus holds "
     "ZERO records for."),
    ("ฟื้นฟูสมรรถภาพ", "fuen fu samatthaphap", "rehabilitation of capability — "
     "the formal word on physio departments, workers' centres and "
     "residential programmes alike; by itself it does not say WHICH."),
    ("กายภาพบำบัด", "kayaphap bambat", "physiotherapy — กายภาพ the physical · "
     "บำบัด to treat. Its own shelf on the medical tree."),
    ("บำบัดยาเสพติด", "bambat ya sep tit", "addiction treatment — บำบัด treat · "
     "ยาเสพติด narcotics (literally 'drugs one is stuck on' — the same ติด "
     "as in ติดเตียง). ธัญญารักษ์ is the state's own hospital network for it."),
    ("เลิกเหล้า", "loek lao", "to quit drink — เลิก quit · เหล้า liquor. "
     "เลิกยา is the same phrase for drugs, เลิกบุหรี่ for cigarettes."),
    ("ดูแลต่อเนื่อง", "dulae to nueang", "continuing care — the ongoing-care "
     "page's own phrase; where the chronic-condition paperwork lives."),
    ("เกษียณ", "kasian", "to retire — from Sanskrit kṣīṇa, 'exhausted, ended'. "
     "วัยเกษียณ is retirement age; the word is about leaving work, and says "
     "nothing about needing care."),
    ("ญาติเฝ้า", "yat fao", "a relative staying to watch over — Thai wards "
     "assume family attends the patient. If there is no family here, this "
     "is the exact gap a paid carer (ผู้ดูแล, phu dulae) fills; ask with "
     "this word."),
]

GRADE_LABEL = {
    "mapped": ("ตามแผนที่", "mapped"),
    "route": ("ทางที่ใช้ประจำ", "the usual route"),
    "stated": ("บอกเอง", "stated"),
}

SECTIONS = [
    ("elder", "บ้านพักคนชรา-ดูแลผู้สูงอายุ", "Nursing homes & elder care"),
    ("addiction", "บำบัด — ทางออกจากการติด", "Addiction medicine"),
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
    verdict, BROKEN = g["verdict"], g["BROKEN"]
    BROKEN_WHY = g["BROKEN_WHY"]
    LINK_HEALTH_DATE = g.get("LINK_HEALTH_DATE") or ""

    def site_a(url):
        """A register row's own site — or the address of one that has stopped
        answering. The WO-31 dead-ref rule, same as the ADHD and souvenir
        layers: a dead ref keeps its place and its address, carries the
        verdict and the date in its tooltip, and stops being a door. This
        page shipped one bare <a> to a site with a broken verdict on file
        (theriverrehab.com) and the publish gate held the whole walk shut on
        it — flagged by WO-33, fixed under WO-37."""
        url = (url or "").strip()
        if not url:
            return ""
        v = verdict(url)
        st = v.get("status")
        if st not in BROKEN:
            return (f'<a href="{att(url)}" rel="noopener nofollow">'
                    f'{esc(url[:48])}</a>')
        why_th, why_en = BROKEN_WHY.get(
            st, ("เปิดไม่ได้", "the link could not be opened"))
        when = v.get("checkedAt") or LINK_HEALTH_DATE
        tip = url + " — " + bi_text(
            why_th + " ตรวจเมื่อ " + when, why_en + ", checked " + when)
        return f'<span class="lc-dead" title="{att(tip)}">{esc(url[:48])}</span>'

    src = ROOT / "data" / "curated" / "longcare.json"
    if not src.exists():
        return "longcare.json missing — page not built"
    reg = json.loads(src.read_text(encoding="utf-8"))
    rows, unread = reg.get("rows", []), reg.get("unread", [])

    (DOCS / "longcare.css").write_text(CSS)

    byid = {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            byid[r["id"]] = (p["key"], r)

    # The shelf this page stands on — counted live so the sentence and the
    # shelf can never disagree.
    shelf = [(k, r) for k, r in byid.values()
             if (r.get("attrs") or {}).get("facilityType") == "long-care"]

    def place_link(ids):
        for pid in ids or []:
            hit = byid.get(pid)
            if hit:
                k, r = hit
                return f'<a href="{att(k)}/p/{att(place_slug(r))}.html">{esc(name_of(r))}</a>'
        return ""

    def card(row):
        th_g, en_g = GRADE_LABEL.get(row["grade"], (row["grade"], row["grade"]))
        tag = f'<span class="lc-tag {att(row["grade"])}">{bi(th_g, en_g)}</span>'
        link = place_link(row.get("placeIds"))
        site = site_a(row.get("site"))
        where = " · ".join(x for x in (link, site) if x)
        said = (f'<span class="lc-said">{bi(row.get("note_th", ""), row.get("note_en", ""))}'
                f' — {esc(row.get("src", ""))} · {esc(row.get("fetched", ""))}</span>')
        return (f'<section class="lc-card"><h3>{bi(row["name_th"], row["name_en"])}{tag}</h3>'
                f'<p class="lc-where">{where}</p>{said}</section>')

    section_html = []
    for skey, sth, sen in SECTIONS:
        srows = [r for r in rows if r.get("section") == skey]
        stated = [r for r in srows if r["grade"] == "stated"]
        head = (f'<h2 class="lc-h">{bi(sth, sen)} '
                f'<span class="count">({len(srows)})</span></h2>')
        if skey == "addiction":
            head += (f'<p class="lc-note">{bi("หน้านี้ไม่จัดอันดับ ไม่แนะนำที่ใด ไม่พูดถึงแนวทางหรือผลลัพธ์ของการบำบัด แต่ละแห่งพูดแทนตัวเองหรือยังไม่ได้พูด — และการอยากเลิกคือเรื่องปกติของคนธรรมดา ไม่ใช่เรื่องต้องกระซิบ", "This section ranks nothing, recommends nowhere, and says nothing about treatment approaches or outcomes — each place speaks for itself or has not yet. Wanting to stop is an ordinary human errand, not something to whisper.")}</p>')
        if not stated:
            head += (f'<p class="lc-note">{bi("ยังไม่มีแถวใดถึงเกรด “บอกเอง” — ยังไม่ได้อ่านเว็บของสถานที่ใดเลย ทุกแถวข้างล่างคือคำของแผนที่หรือป้าย ไม่ใช่คำของสถานที่", "No row here has reached the ‘stated’ grade — no place’s own site has been read yet. Every row below is a map’s or a sign’s word, not the place’s own.")}</p>')
        section_html.append(head + "".join(card(r) for r in srows))

    # ---- convalescence: a census, not a register ---------------------------
    conv_html = (
        f'<h2 class="lc-h">{bi("พักฟื้น — ช่องว่างระหว่างออกจากโรงพยาบาลกับหายดี", "Convalescence — the gap between discharge and well")}</h2>'
        f'<p class="lc-intro">{bi("นับแล้วตรง ๆ: ในระเบียน 20,700 แห่งของสองจังหวัด ไม่มีชื่อไหนเขียนคำว่า พักฟื้น เลยแม้แต่แห่งเดียว ไม่ใช่ว่าการพักฟื้นไม่มีอยู่ — แต่มันวิ่งผ่านช่องทางอื่น: แผนกกายภาพบำบัด คลินิกต่อเนื่องของโรงพยาบาล และคนดูแลที่บ้าน ซึ่งไม่มีป้ายให้แผนที่เก็บ", "Counted plainly: across 20,700 records in both provinces, not one name carries the word พักฟื้น. Convalescent care is not absent — it runs through other channels: the physiotherapy shelf, a hospital’s own continuing-care clinics, and carers who come to the house, who have no sign for a map to hold.")}</p>'
        f'<p class="lc-note">{bi("สามทางที่มีจริงวันนี้", "The three ways in that exist today")}: '
        f'<a href="cm/medical/physio/index.html">{bi("ชั้นกายภาพบำบัด", "the physiotherapy shelf")}</a> · '
        f'<a href="care.html">{bi("ดูแลต่อเนื่อง — แผนกและคลินิกนอกเวลาที่โรงพยาบาลบอกเอง", "ongoing care — the departments hospitals state themselves")}</a> · '
        f'{bi("และคำที่ต้องใช้ถามเคาน์เตอร์ก่อนออกจากโรงพยาบาล: ผู้ป่วยติดเตียง · ญาติเฝ้า · ผู้ดูแล (ดูตาราง)", "and the words to ask a desk with before discharge: ผู้ป่วยติดเตียง · ญาติเฝ้า · ผู้ดูแล (see the table)")}.</p>')

    # ---- active retirement: a life, not a bed ------------------------------
    retire_html = (
        f'<h2 class="lc-h">{bi("เกษียณแบบยังแข็งแรง — ชีวิต ไม่ใช่เตียง", "Active retirement — a life, not a bed")}</h2>'
        f'<p class="lc-intro">{bi("คำว่า เกษียณ พูดถึงการเลิกทำงาน ไม่ได้พูดถึงการต้องมีคนดูแล คนที่เกษียณแล้วยังแข็งแรงไม่ได้หาสถานพยาบาล — เขาหาห้องเช่ารายเดือน ชมรม สระว่ายน้ำ และตลาดเช้า ซึ่งเป็นชั้นอื่นของสารบัญนี้ทั้งหมด", "The word เกษียณ is about leaving work, not about needing care. A fit retiree is not looking for a facility — they are looking for a monthly room, a club, a pool and a morning market, all of which are OTHER shelves of this directory.")}</p>'
        f'<p class="lc-note">'
        f'<a href="realestate.html">{bi("อสังหาฯ-ที่พัก — ห้องรายเดือน คำก่อนวางมัดจำ", "housing — monthly rooms, the words before the deposit")}</a> · '
        f'<a href="cm/community/index.html">{bi("ชั้นชุมชน-ชมรม", "the community shelf & clubs")}</a> · '
        f'<a href="care.html">{bi("ดูแลต่อเนื่อง — เมื่อมีโรคประจำตัวติดกระเป๋ามาด้วย", "ongoing care — for the chronic condition that travels with you")}</a>'
        f'</p>')

    # ---- not read yet ------------------------------------------------------
    un_rows = "".join(
        f'<tr><td>{esc(u["name"])}</td><td>{esc(u.get("ref", ""))}</td>'
        f'<td>{esc(u["reason"])}</td></tr>' for u in unread)
    unread_html = (
        f'<h2 class="lc-h">{bi("ยังไม่ได้อ่าน — บอกไว้ตรง ๆ", "Not read yet — said plainly")} '
        f'<span class="count">({len(unread)})</span></h2>'
        f'<p class="lc-note">{bi("รายชื่อและทะเบียนที่รู้ว่ามี แต่ยังไม่มีใครอ่าน — สารบัญที่โชว์เฉพาะที่สำเร็จคือสารบัญที่โกหกว่าแผนที่เสร็จแล้ว", "Names and registers known to exist that nobody has read yet. A directory that shows only its successes is claiming a finished map.")}</p>'
        f'<div class="lc-tablewrap"><table class="lc-tab"><thead><tr>'
        f'<th>{bi("ชื่อ", "Name")}</th><th>{bi("อ้างอิง", "Ref")}</th>'
        f'<th>{bi("ทำไมยังไม่ได้อ่าน", "Why it is not read")}</th>'
        f'</tr></thead><tbody>{un_rows}</tbody></table></div>')

    gl_rows = "".join(
        f'<tr><td class="th">{esc(th)}</td><td class="rtgs">{esc(rtgs)}</td>'
        f'<td>{esc(en)}</td></tr>' for th, rtgs, en in GLOSSARY)
    gloss_html = (
        f'<h2 class="lc-h">{bi("คำบนป้ายพวกนี้", "The words on these signs")}</h2>'
        f'<p class="lc-note">{bi("อักษรไทย · คำอ่านแบบ RTGS · ความหมายและรากศัพท์ — เทียบรูปคำกับป้ายได้แม้อ่านไทยไม่ออก", "Thai script · RTGS spelling · the meaning and the root — enough to match a word against a sign by its shape, without reading Thai.")}</p>'
        f'<div class="lc-tablewrap">'
        f'<table class="lc-tab lc-gloss"><tbody>{gl_rows}</tbody></table></div>')

    intro = bi(
        "สี่คำถามที่คนมักพิมพ์รวมเป็นคำเดียว — หาที่อยู่ให้พ่อแม่สูงวัย หาที่พักฟื้นหลังออกจาก"
        "โรงพยาบาล หาทางออกจากการติดสุราหรือสารเสพติด และหาชีวิตวัยเกษียณที่ยังแข็งแรง — "
        "หน้านี้แยกทั้งสี่ออกจากกัน เพราะการปนกันทำให้คนที่ต้องการเตียงคืนนี้ได้บทความไลฟ์สไตล์แทน "
        "ทุกแถวมีเกรดกำกับว่าใครเป็นคนพูด: แผนที่ ทางที่ใช้ประจำ หรือสถานที่พูดเอง "
        "ไม่จัดอันดับ ไม่แนะนำ ไม่ใช่คำแนะนำทางการแพทย์ ที่ไหนไม่ได้พูด = เงียบ ไม่ใช่ 'ไม่มี'",
        "Four questions people type as one — a place for an ageing parent, somewhere "
        "to recover after a hospital, a way out of an addiction, and a retirement "
        "that is a life and not a bed. This page keeps the four apart, because "
        "folding them together is how the family that needs a bed tonight gets a "
        "lifestyle article instead. Every row carries a grade naming who is "
        "speaking: a map, the usual route, or the place itself. No rankings, no "
        "recommendations, no medical advice. Where a place says nothing, that is "
        "silence — never a 'no'.")

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "ดูแลระยะยาว เชียงใหม่-เชียงราย — Long-term care, Chiang Mai and Chiang Rai",
        "url": BASE + "longcare.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "MedicalOrganization", "name": r["name_en"],
                      **({"url": r["site"]}
                         if r.get("site")
                         and verdict(r["site"]).get("status") not in BROKEN
                         else {})}}
            for i, r in enumerate(rows)],
    }
    head = ('<link rel="stylesheet" href="longcare.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "medical") if shelf_og else None

    shelf_links = " · ".join(
        f'<a href="{att(k)}/p/{att(place_slug(r))}.html">{esc(name_of(r))}</a>'
        for k, r in sorted(shelf, key=lambda x: name_of(x[1])))
    body = (
        f'<h1>{bi("ดูแลระยะยาว — บ้านพักคนชรา พักฟื้น บำบัด และวัยเกษียณ", "Long-term care — nursing homes, convalescence, addiction medicine, and retirement")}</h1>'
        f'<p class="lc-intro">{intro}</p>'
        f'<h2 class="lc-h">{bi("ชั้นใหม่บนต้นไม้หมอ", "The new shelf on the medical tree")} '
        f'<span class="count">({len(shelf)})</span></h2>'
        f'<p class="lc-note">{bi("จนถึง 26 ส.ค. 2026 ระเบียนพวกนี้ถูกจัดเป็น “งานอาสา” เพราะตัวนำเข้าโยนแท็ก social_facility ทิ้ง — แก้ที่กฎแล้ว ชั้น ดูแลระยะยาว จึงมีของจริงยืนอยู่", "Until 26 Aug 2026 these records were filed as ‘Volunteering’, because the importer threw the social_facility tag away. The rule is mended, and the long-term-care shelf now holds its real records")}: {shelf_links}</p>'
        f'{section_html[0]}'
        f'{conv_html}'
        f'{section_html[1]}'
        f'{retire_html}'
        f'{gloss_html}'
        f'{unread_html}'
        f'<p class="lc-note">{bi("มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์ ไม่ใช่การส่งต่อคนไข้ และไม่ใช่การรับรองคุณภาพ ข้อมูลบางส่วนมาจาก OpenStreetMap (ODbL 1.0)", "Mot Dang is a directory of places. It is not medical advice, not a referral, and not a quality guarantee. Some facility data is derived from OpenStreetMap (ODbL 1.0), © OpenStreetMap contributors.")}</p>'
        f'<p class="lc-note"><a href="care.html">{bi("ดูแลต่อเนื่อง — แผนก คลินิกนอกเวลา เอกสาร", "ongoing care — departments, after-hours, paperwork")}</a> · '
        f'<a href="adhd.html">{bi("สมาธิสั้น — ทะเบียนจิตเวช", "ADHD — the psychiatric register")}</a> · '
        f'<a href="cm/medical/index.html">{bi("ชั้นหมอ-สถานพยาบาล", "the medical shelf")}</a></p>'
        f'{share_block(BASE + "longcare.html", "ดูแลระยะยาว เชียงใหม่ · มดแดง", card=og)}')

    (DOCS / "longcare.html").write_text(page(
        "ดูแลระยะยาว เชียงใหม่ · Long-term care, Chiang Mai",
        body, depth=0, path="longcare.html",
        desc=bi_text(
            "บ้านพักคนชรา พักฟื้น บำบัดยาเสพติด-สุรา และวัยเกษียณในเชียงใหม่-เชียงราย — "
            "แยกสี่คำถามออกจากกัน ทุกแถวบอกว่าใครเป็นคนพูด พร้อมคำไทยบนป้าย",
            "Nursing homes, convalescence, addiction medicine and retirement in "
            "Chiang Mai and Chiang Rai — four questions kept apart, every row "
            "naming who is speaking, with the Thai words from the signs."),
        extra_head=head, og=og))
    n_by = {}
    for r in rows:
        n_by[r["section"]] = n_by.get(r["section"], 0) + 1
    return (f"{len(shelf)} on the long-care shelf, "
            f"{n_by.get('elder', 0)} elder + {n_by.get('addiction', 0)} addiction rows, "
            f"{len(unread)} not read")
