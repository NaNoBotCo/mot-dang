#!/usr/bin/env python3
"""ถามมด — one evergreen page for questions readers actually ask that don't
fit any existing shelf: sometimes the catalogue already holds a real answer
under a name nobody thought to search for, sometimes the OPEN WEB holds one
the crawl never could, and sometimes there's a real reason to say nothing at
all — this page tells which, out loud, instead of returning empty.

Each entry is FOUND (real records, filtered from `data` and rendered with
entry_li() exactly like every other list on the site — including a handful
hand-added to data/curated/additions-chiang-mai.json from an open-web check
the OSM crawl structurally can't do, each with a fetched, dated source) or a
CANDID GAP (what's missing, why, and the concrete next step).

Shibari is the one entry that stays a gap on purpose even after a real lead
turned up: press coverage shows a rope-teaching scene has existed in Chiang
Mai, but the source was a single old, paywalled article naming one private
individual in a sensitive practice — not something this site will publish
without that person's own consent, no matter how citable. The house rule
(add.html, self-submitted, no address required) is the correct path here,
not a name pulled from someone else's reporting.

House rules as everywhere: Thai canonical with EN as a display layer, nothing
that reports a reader to anybody, no invented ratings, silence never dressed
up as "no". No map on this page, so it fetches nothing at read time.

Entry point: emit(globals_of_build, data) — call after answers_layer.emit so
this page's stylesheet (answers.css) already exists on disk.
"""
DOCS = None


def _obgyn_recs(data):
    return {p: [r for r in data[p] if (r.get("attrs") or {}).get("obgyn")]
            for p in ("cm", "cr")}


def _physio_recs(data):
    out = {}
    for p in ("cm", "cr"):
        out[p] = [r for r in data[p] if "medical" in (r.get("cat") or [])
                  and ((r.get("attrs") or {}).get("physio")
                       or "physical therapy" in ((r.get("name") or "") + (r.get("nameEn") or "")).lower()
                       or "กายภาพบำบัด" in (r.get("name") or ""))]
    return out


def _pole_recs(data):
    return [r for r in data["cm"] if r["id"] == "cm-curated-cnxpole"]


def asked_page(g, data):
    bi, esc = g["bi"], g["esc"]

    def li_block(recs, prov):
        recs = sorted(recs, key=lambda r: 0 if r.get("phone") else 1)
        lis = "".join(g["entry_li"](r, f'{prov}/p/{g["place_slug"](r)}.html')
                      for r in recs)
        return f'<ul class="dir">{lis}</ul>'

    obgyn = _obgyn_recs(data)
    physio = _physio_recs(data)
    pole = _pole_recs(data)

    # ---- card 1: pap smear / well-woman care — a real, sizeable answer -----
    n_cm = len(obgyn["cm"])
    phoned = [r for r in obgyn["cm"] if r.get("phone")]
    rest = n_cm - len(phoned)
    card1 = (
        '<div class="qacard">'
        f'<b>{bi("ตรวจแปปสเมียร์ที่ไหนได้บ้าง", "Where can I get a pap smear?")}</b>'
        f'<p>{bi(f"เท่าที่มดแดงถือข้อมูลอยู่ตอนนี้ เชียงใหม่มี {n_cm} แห่งที่ทำเรื่องสูติ-นรีเวชได้ — โรงพยาบาลใหญ่ทุกแห่งมีแผนกนี้ คลินิกสูติ-นรีเวชเฉพาะทางอีกสองสามแห่ง และคลินิกผู้หญิงโดยตรงอีกแห่ง {len(phoned)} แห่งข้างล่างนี้มีเบอร์โทรที่เรายืนยันได้แล้ว", f"The catalogue currently holds {n_cm} Chiang Mai facilities with obstetrics-gynaecology capacity — every major hospital runs one, a few dedicated OB-GYN clinics, plus a standalone clinic for women. The {len(phoned)} below carry a phone number we can confirm.")}</p>'
        + li_block(phoned, "cm")
        + f'<p class="tinynote">{bi(f"อีก {rest} แห่งอยู่ในหมวดหมอ-คลินิกด้วยเช่นกัน แต่ยังไม่มีเบอร์โทรที่ยืนยันได้ — ดูทั้งหมดที่", f"{rest} more sit in the doctors & hospitals shelf but without a confirmed phone number yet — see all of them at")} '
        f'<a href="cm/medical/index.html">{bi("หมอ-คลินิก-โรงพยาบาล เชียงใหม่", "Doctors & Hospitals, Chiang Mai")}</a></p>'
        f'<p class="tinynote">{bi("เชียงรายยังไม่มีแห่งไหนติดธงนี้ในข้อมูลของเรา — ไม่ได้แปลว่าไม่มีบริการจริง แค่ยังไม่มีใครยืนยันให้มดแดง", "Chiang Rai has zero facilities flagged for this yet in our data — that means unconfirmed, not unavailable.")} '
        f'<a href="crawl-request.html">{bi("ส่งมดไปสำรวจ", "request a crawl")}</a></p>'
        '</div>')

    # ---- card 2: western-style / table physiotherapy — thin but real -------
    n_physio = len(physio["cm"])
    card2 = (
        '<div class="qacard">'
        f'<b>{bi("หมอกายภาพบำบัดแบบตะวันตก (นวดบนเตียง) มีที่ไหน", "Western-style physiotherapists who work on a table?")}</b>'
        f'<p>{bi(f"เท่าที่มดแดงถือข้อมูลอยู่ตอนนี้มี {n_physio} แห่งที่ระบุชัดว่าเป็นกายภาพบำบัด — สองแห่งจากการสำรวจแผนที่ อีกสองแห่งเช็กจากเว็บของคลินิกเอง — บวกกับแผนกกายภาพบำบัด-เวชศาสตร์ฟื้นฟูของโรงพยาบาลใหญ่ ซึ่งทำงานบนเตียงตรวจแบบตะวันตกเป็นปกติอยู่แล้ว: โรงพยาบาลแมคคอมิก เชียงใหม่ราม กรุงเทพ และมหาราชนครเชียงใหม่ (สวนดอก)", f"The catalogue currently holds {n_physio} places named specifically as physiotherapy — two from the map survey, two more checked against the clinics own websites — plus the physiotherapy/rehabilitation departments at the major hospitals, which work on a Western-style table as a matter of course: McCormick, Chiang Mai Ram, Bangkok Hospital, and Maharaj Nakorn (Suan Dok).")}</p>'
        + li_block(physio["cm"], "cm")
        + f'<p class="tinynote">{bi("หมวดนวด-สปาของเรามี 294 แห่งในเชียงใหม่ แต่ยังไม่มีข้อมูลแยกว่าร้านไหนนวดแผนไทยแบบนั่งพื้น ร้านไหนนวดบนเตียงแบบตะวันตก — คลินิกกายภาพจริงๆ อาจซ่อนอยู่ในนั้นโดยไม่มีป้ายบอก การแก้ที่ตรงจุดคือให้เจ้าของร้านยืนยันร้านของตัวเองแล้วบอกสไตล์การนวด", "The massage & spa shelf holds 294 Chiang Mai places, but nothing in the data distinguishes floor-seated Thai massage from Western table work — a real physio practice could be sitting in there unlabelled. The right fix belongs to the owner: claim your place and tell us your style.")} '
        f'<a href="claim.html">{bi("ยืนยันร้านของคุณ", "claim your place")}</a></p>'
        '</div>')

    # ---- card 3: shibari / rope — evidence exists, staying a candid gap ----
    card3 = (
        '<div class="qacard">'
        f'<b>{bi("ชิบาริ (มัดเชือกแบบญี่ปุ่น) เรียนหรือหาผู้สอนได้ที่ไหน", "Where can I find shibari (Japanese rope) instructors or practice space?")}</b>'
        f'<p>{bi("ไม่มีในสารบัญเลยสักแห่ง แต่ไม่ใช่เพราะไม่มีอยู่จริง — สื่อสิ่งพิมพ์เคยเขียนถึงผู้สอนมัดเชือกที่ย้ายมาอยู่เชียงใหม่และสอนจริงในเมืองนี้ แปลว่าวงการนี้มีอยู่ ไม่ใช่ความว่างเปล่า", "Nothing in the catalogue, but not because it does not exist — press coverage has profiled a rope teacher who relocated to Chiang Mai and taught here for real. So the scene is real, not a blank.")}</p>'
        f'<p>{bi("สิ่งที่มดแดงจะไม่ทำ: ขุดชื่อคนจากบทความเก่าที่ต้องเสียเงินอ่าน แล้วเอาชื่อ-ตัวตนของใครสักคนในวงการที่อ่อนไหวแบบนี้มาลงหน้าสารบัญสาธารณะโดยเขาไม่ได้ยินยอม ต่อให้มีแหล่งอ้างอิงก็ตาม การหาแบบเดินสำรวจหน้าร้านก็ไม่มีทางเจอวงการที่รวมตัวกันแบบปิดอยู่แล้วเป็นปกติ — ผ่านกลุ่มไลน์ เทเลแกรม หรือ FetLife ไม่ใช่ป้ายร้าน", "What Mot Dang will not do: pull a name out of an old, paywalled article and publish the identity of someone in a sensitive practice on a public directory without their consent, citable source or not. And storefront-survey methods were never going to find a scene that organises privately in the first place — closed LINE or Telegram groups, FetLife — not a shop sign.")}</p>'
        f'<p class="myhint">{bi("จะช่วยได้ยังไง: ถ้าคุณเป็นผู้สอนหรือรู้จักผู้จัดที่เปิดรับคนนอกกลุ่ม ส่งข้อมูลติดต่อ (ไม่จำเป็นต้องมีที่อยู่ร้าน) มาทางหน้าเพิ่มข้อมูลได้เลย — ลงเฉพาะสิ่งที่มีคนตั้งใจส่งมาให้เท่านั้น ไม่ใช่สิ่งที่เราไปขุดมาเอง", "How to help close this: if you teach, or know an organiser who welcomes newcomers, send a contact channel (no shop address needed) through Add a place — listed only from what someone hands us on purpose, never from what we dig up ourselves.")} '
        f'<a href="add.html">{bi("เพิ่มข้อมูล", "add a place")}</a></p>'
        '</div>')

    # ---- card 4: pole dancing classes — a real find, plus one open lead ----
    card4 = (
        '<div class="qacard">'
        f'<b>{bi("เรียนโพลแดนซ์ (pole dance) ได้ที่ไหน", "Where can I take pole dancing classes?")}</b>'
        f'<p>{bi("หมวดเรียน-กีฬาของเชียงใหม่มี 149 แห่งจากการสำรวจแผนที่เปิด — ยิม โยคะ มวยไทย เต็มไปหมด — แต่ไม่มีสตูดิโอโพลแดนซ์เลยสักแห่ง เพราะข้อมูลแผนที่เปิดมักไม่แยกสตูดิโอแบบนี้ออกจากฟิตเนสทั่วไป ตามหาทางเว็บแทนแล้วเจอสตูดิโอที่เปิดสอนจริง เพิ่มเข้าสารบัญให้แล้วด้านล่าง", "Chiang Mai learning & sport shelf holds 149 places from the open-map survey — gyms, yoga, Muay Thai — but zero pole studios, because open-map data rarely distinguishes one from generic fitness. A web check instead turned up a real, currently-teaching studio, added to the catalogue below.")}</p>'
        + li_block(pole, "cm")
        + f'<p class="tinynote">{bi("มีอีกสตูดิโอหนึ่งที่หาเจอชื่อ (Vivid Dance Studio) แต่เว็บไซต์ของเขาใบรับรอง TLS หมดอายุตอนที่เราเช็ก ยืนยันเนื้อหาไม่ได้จริงๆ เลยยังไม่ใส่ในสารบัญ — ยืนยันได้เมื่อไรจะเพิ่มให้", "One more studio surfaced by name — Vivid Dance Studio — but its website TLS certificate had expired when we checked, so we could not actually verify its content and have not added it yet. It will go in once confirmable.")}</p>'
        f'<p class="myhint">{bi("รู้จักสตูดิโอไหนอยู่แล้ว บอกชื่อ-ย่านมาทางหน้าส่งมดไปสำรวจ หรือเพิ่มเข้าไปเองที่หน้าเพิ่มข้อมูลได้เลย", "Know another studio? Name it and its area on Request a crawl, or add it yourself on Add a place.")} '
        f'<a href="crawl-request.html">{bi("ส่งมดไปสำรวจ", "request a crawl")}</a> · '
        f'<a href="add.html">{bi("เพิ่มข้อมูล", "add a place")}</a></p>'
        '</div>')

    intro_th = ("บางคำถามไม่มีหมวดของตัวเอง แต่ก็เป็นคำถามจริงที่คนถามมด — หน้านี้รวบรวมไว้ "
                "บางข้อมดแดงมีคำตอบจริงอยู่แล้วในสารบัญ บางข้อต้องออกไปเช็กนอกสารบัญก่อนถึงเจอ "
                "(ทุกแหล่งมีลิงก์ที่มา) และบางข้อยังไม่มีคำตอบ บอกตรงๆ ว่าทำไม พร้อมทางช่วยเติมให้ครบ")
    intro_en = ("Some questions don't have their own shelf, but people ask the ants anyway "
                "— this page collects them. Some already have a real answer sitting in the "
                "catalogue. Some needed a check beyond the catalogue to find (every source is "
                "linked). And one stays open on purpose, explained plainly, with a concrete way "
                "to help close it.")

    body = (
        f'<h1>❓ {bi("ถามมด", "Ask the ants")}</h1>'
        f'<p>{bi(intro_th, intro_en)}</p>'
        f'<div class="qagrid">{card1}{card2}{card3}{card4}</div>'
        f'<p class="tinynote">{bi("ที่มา: ข้อมูลเปิด OpenStreetMap การเดินเก็บจริง และการตรวจสอบเว็บของแต่ละแห่งเอง (มีลิงก์ที่มาในข้อมูลแต่ละรายการ) ปรับปรุง", "From OpenStreetMap, field surveys, and a direct check of each business website where noted (source linked per record) · updated")} '
        f'{g["BUILD_DATE"]} · '
        f'<a href="lists/index.html">{bi("รายชื่อครบทั้งหมวด", "Complete lists")}</a></p>'
        + g["share_block"](g["BASE"] + "asked.html", "ถามมด · Ask the ants — มดแดง"))

    return g["page"](
        "ถามมด — คำถามที่คนถามจริง เชียงใหม่ เชียงราย",
        body, depth=0, path="asked.html",
        extra_head='<link rel="stylesheet" href="answers.css">',
        desc="แปปสเมียร์ กายภาพบำบัด ชิบาริ โพลแดนซ์ — สี่คำถามจริงที่คนถามมดแดง คำตอบเท่าที่มี "
             "และช่องว่างที่ยังไม่มี บอกตรงๆ ทั้งคู่ · Real questions, real answers where we have "
             "them, and honest gaps where we don't.",
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("ถามมด", "Ask the ants"))


def emit(g, data):
    global DOCS
    DOCS = g["DOCS"]
    (DOCS / "asked.html").write_text(asked_page(g, data))
    return {"asked": 1}
