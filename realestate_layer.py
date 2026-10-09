#!/usr/bin/env python3
"""อสังหาฯ-ที่พัก — the words to ask before the deposit, the shelves, and what
nobody has asked the buildings yet.

Four things a person asks about somewhere to live in this town, in the order
they ask them, on one page (/realestate.html):

  1. HOW DO I ASK — the words. ค่าไฟหน่วยละเท่าไร decides the real monthly
     cost more than the rent line does, and no listing site prints it. A
     person who cannot say มัดจำ or ค่าส่วนกลาง signs papers they have not
     read. Thai script, RTGS, tone, and the root where the root explains the
     word — including why the cheapest buildings in the city are called
     Mansion and Court in English.
  2. WHICH BUILDINGS — the shelves after the 2026-08-21 split: condominiums
     (the buildings whose own name says so), apartments-mansions-courts (the
     monthly trade), dormitories, housing estates and agents. Until that
     split every one of them was filed as a condo, which was the barber
     shelf's lie wearing a different sign. The dorm, estate and Land Office
     shelves were then filled by three crawl doors that had never been asked
     — a dorm is tagged on the BUILDING, not in the name; an estate is a
     named residential AREA; and no selector had ever asked for a government
     office at all.
  3. WHAT NOBODY HAS ASKED THEM — the census. Across all records in both
     provinces, ZERO building names say furnished and ZERO post a rate.
     Printed every build from audit_realestate's own rules so the numbers
     cannot drift.
  4. THE REGISTERS, two of them and they are different things. What buildings
     state about THEMSELVES (data/curated/realestate.json, read from their
     own sites), and what the TREASURY states about them
     (data/curated/condo_register.json — the official อาคารชุด register with
     an assessed value per m², which is the basis for transfer fees and is
     never a market price). The second one also measures the first: the
     government counts 366 registered condominium buildings in Chiang Mai
     against the 53 this catalogue holds by name.

Rents appear as posted, with a date. Where the law decides something (the
foreign quota in a condominium, the transfer at the Land Office), the page
gives the words to ask the juristic office and the office the answer lives in.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
beauty layer. Emits realestate.html + realestate.css; prints the counts.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "data" / "curated" / "realestate.json"
CONDO_REG = ROOT / "data" / "curated" / "condo_register.json"
sys.path.insert(0, str(ROOT / "importers"))
import audit_realestate  # noqa: E402  (zero network; the หมู่บ้าน guard)

CSS = """
.re-intro{font-size:1.02rem;max-width:46rem}
.re-rule{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07);font-size:.98rem}
.re-rule b{display:block;margin-bottom:.15rem}
.re-door{margin:.8rem 0 1.2rem;padding:.85rem 1rem;border-radius:.8rem;
  border:1px solid rgba(0,0,0,.12);border-left:4px solid var(--accent,#a33d21);
  font-size:.98rem}
.re-door b{display:block;margin-bottom:.2rem}
.re-door .go{display:inline-flex;align-items:center;gap:.4rem;margin:.55rem .6rem 0 0;
  padding:.5rem .9rem;border-radius:.55rem;text-decoration:none;font-weight:600;
  background:var(--accent,#a33d21);color:#fff}
.re-door .go.q{background:transparent;color:var(--accent,#a33d21);
  border:1px solid currentColor}
.re-doors{display:grid;grid-template-columns:repeat(auto-fill,minmax(10.5rem,1fr));gap:.55rem;margin:.8rem 0 1.1rem}
.re-tile{display:flex;align-items:center;gap:.55rem;min-height:2.9rem;padding:.55rem .75rem;border-radius:.8rem;
  background:var(--soft);color:var(--ink);text-decoration:none;font-weight:600;line-height:1.25}
.re-tile:hover,.re-tile:focus-visible{outline:3px solid var(--accent,#a33d21);outline-offset:1px}
.re-ic{flex:none;color:var(--accent,#a33d21)}
.re-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.re-words{width:100%;border-collapse:collapse;margin:.6rem 0 1rem;font-size:.95rem}
.re-words th,.re-words td{padding:.45rem .4rem;border-bottom:1px solid rgba(0,0,0,.08);
  text-align:left;vertical-align:top}
.re-words th{font-size:.85rem;color:var(--mute);font-weight:600}
.re-words .th{font-size:1.12rem;white-space:nowrap}
.re-words .rtgs{color:var(--mute);font-style:italic;white-space:nowrap;font-size:.88rem}
.re-words .root{color:var(--mute);font-size:.85rem}
.re-words tr:hover{background:var(--soft)}
.re-say{margin:.5rem 0 1.2rem;padding:.7rem .9rem;border-radius:.8rem;
  border:1px dashed rgba(0,0,0,.18);background:var(--soft)}
.re-say .line{font-size:1.14rem;margin:.15rem 0}
.re-say .gloss{color:var(--mute);font-size:.9rem;margin:0 0 .5rem}
.re-gap{margin:.8rem 0 1rem;padding:.75rem .9rem;border-radius:.8rem;
  border:1px solid var(--ant-dark);background:var(--soft)}
.re-gap b{display:block;margin-bottom:.2rem}
.re-list{columns:2;column-gap:1.4rem;margin:.5rem 0 1rem;font-size:.95rem}
@media(max-width:640px){.re-list{columns:1}}
.re-list div{break-inside:avoid;padding:.16rem 0}
.re-list a{text-decoration:none;color:inherit}
.re-list a:hover{text-decoration:underline}
.re-list small{color:var(--mute);font-size:.82rem}
.re-count{color:var(--mute);font-weight:400;font-size:.9rem}
.re-note{color:var(--mute);font-size:.9rem;margin:.3rem 0 1rem}
.re-queue{font-size:.93rem;margin:.4rem 0 1rem}
.re-queue li{margin:.18rem 0}
.re-ct{margin:.5rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07)}
.re-ct .m{color:var(--mute);font-size:.85rem;white-space:nowrap}
"""

# --- the words -------------------------------------------------------------
# Thai, RTGS, tone, and the root ONLY where the root explains the word. Same
# table discipline as beauty_layer: tones as a learner needs them spoken.
WORDS = [
    ("ห้องเช่า", "hong chao", "hɔ̂ng châo", "room for rent", "ห้อง room + เช่า to rent",
     "The plain word. ห้องว่าง hɔ̂ng wâang — a vacant room — is what you ask for."),
    ("ค่าเช่า", "kha chao", "khâa châo", "the rent", "ค่า the charge for + เช่า",
     "Monthly unless somebody says otherwise. The number on the sign is rarely the whole cost — see ค่าน้ำ-ค่าไฟ."),
    ("เงินมัดจำ", "ngoen matcham", "ngən mát-jam", "deposit", "มัด to bind + จำ to hold",
     "Commonly asked as months, not baht: มัดจำกี่เดือน — how many months down?"),
    ("ค่าน้ำ-ค่าไฟ", "kha nam kha fai", "khâa náam · khâa fai", "water & electric",
     "ค่า charge + น้ำ water + ไฟ fire/electricity",
     "หน่วยละ nùai-lá = per unit. Buildings set their own per-unit rate, and it moves the real monthly cost more than the rent line."),
    ("ค่าส่วนกลาง", "kha suan klang", "khâa sùan-glaang", "common fee", "ส่วนกลาง the central part",
     "The condo maintenance fee, charged per square metre per month. อาคารชุด all have one."),
    ("แมนชั่น", "maenchan", "mɛɛn-chân", "a budget monthly building", "English mansion, borrowed whole",
     "The word drifted on arrival: in Thailand a Mansion is not a rich house, it is a plain monthly block. So is a คอร์ท (court). The grandest words name the cheapest rooms."),
    ("อพาร์ตเมนต์", "aphatmen", "à-pháat-mén", "apartment (monthly, one owner)", "English, borrowed",
     "One landlord owns the whole building, so the desk answers everything. That is the practical difference from a condo."),
    ("หอพัก", "ho phak", "hɔ̌ɔ phák", "dormitory", "หอ hall + พัก to rest",
     "Student housing, thick around the universities. หอพักหญิง / หอพักชาย — women's / men's — is on the sign, and หอใน is the on-campus one."),
    ("คอนโด-อาคารชุด", "khondo / akhan chut", "khɔɔn-doo · aa-khaan chút", "condominium",
     "อาคารชุด 'assembled building' — the legal term",
     "Units owned one by one, so the desk cannot answer for a room: each owner decides. Buying questions live at the นิติบุคคล, not the lobby."),
    ("นิติบุคคล", "nitibukkhon", "ní-tì-bùk-khon", "the juristic office", "นิติ law + บุคคล person",
     "The condo's legal management body. The foreign-quota question is answered here and nowhere else, and the answer changes with every transfer."),
    ("โฉนด", "chanot", "chà-nòot", "land title deed", "an old Khmer-route word",
     "The paper every purchase turns on. Transfers of it happen at the สำนักงานที่ดิน — the Land Office."),
    ("สัญญาเช่า", "sanya chao", "sǎn-yaa châo", "lease contract", "สัญญา promise/contract",
     "สัญญาขั้นต่ำ — the minimum term. ต่อสัญญา tɔ̀ɔ sǎn-yaa — to renew it (the same ต่อ as ต่อผม, to extend)."),
    ("เฟอร์ครบ", "foe khrop", "fəə khróp", "fully furnished", "เฟอร์นิเจอร์ clipped + ครบ complete",
     "ห้องเปล่า hɔ̂ng bplàao is the bare room. Neither is on any sign — it is a desk question."),
    ("เซ้ง", "seng", "séeng", "to take over a lease (with key money)", "Teochew Chinese, borrowed",
     "The word on a shopfront reading เซ้งร้าน: the business and its lease change hands for a lump sum. Its own trade, not a rental."),
    ("นายหน้า", "nai na", "naai nâa", "broker / agent", "นาย master + หน้า face, front",
     "Literally the face out front. The agent shelf here holds five — the trade lives on LINE and Facebook, not on the map."),
    ("หมู่บ้านจัดสรร", "mu ban chatsan", "mùu-bâan jàt-sǎn", "housing estate", "จัดสรร to allot",
     "An allotted village — the gated moobaan. Without จัดสรร, a หมู่บ้าน is simply a village, which is why that shelf cannot be filled by a name rule."),
]

# The sentences somebody actually needs, whole, at the desk.
SAYINGS = [
    ("มีห้องว่างไหมคะ / ครับ ขอดูห้องได้ไหม",
     "mii hɔ̂ng wâang mǎi ká/kráp · khɔ̌ɔ duu hɔ̂ng dâi mǎi",
     "Is there a room free? May I see it?",
     "Seeing the actual room, not the show room, is normal to ask."),
    ("ค่าไฟหน่วยละเท่าไร ค่าน้ำหน่วยละเท่าไร",
     "khâa fai nùai-lá thâo-rài · khâa náam nùai-lá thâo-rài",
     "What is the electric rate per unit? The water rate?",
     "The single most useful question on this page. Rates differ building to building, and the answer is usually posted at the desk — photograph the board."),
    ("สัญญาขั้นต่ำกี่เดือน มัดจำกี่เดือน",
     "sǎn-yaa khân-tàm gìi dʉan · mát-jam gìi dʉan",
     "How many months is the minimum contract? How many months' deposit?",
     "Both are counted in months here."),
    ("ค่าเช่ารวมอะไรบ้าง มีค่าส่วนกลางไหม",
     "khâa châo ruam à-rai bâang · mii khâa sùan-glaang mǎi",
     "What does the rent include? Is there a common fee?",
     "Wifi, water, parking and the common fee land differently in every building."),
    ("ใครแจ้ง TM30 ให้คะ / ครับ",
     "khrai jɛ̂ɛng thii-em-sǎam-sìp hâi ká/kráp",
     "Who files the TM30 report?",
     "The residence report immigration expects for a foreign tenant. Some desks file it as routine, some have never heard of it — asking before signing is how you find out which."),
    ("โควตาต่างชาติของตึกนี้ เหลือไหมคะ / ครับ",
     "khoo-tâa tàang-châat khɔ̌ɔng tʉ̀k níi · lʉ̌a mǎi ká/kráp",
     "Is any of this building's foreign quota left?",
     "For buying a condo unit. Only the นิติบุคคล can answer, the number changes with every transfer, and no listing site knows it."),
]


def load_reg():
    if REG.exists():
        return json.loads(REG.read_text())
    return {"buildings": [], "verified_on": None}


def load_condo_reg():
    """The Treasury's own register (importers/harvest_condo_register.py).
    Absent is a supported state: the section simply does not render."""
    if CONDO_REG.exists():
        return json.loads(CONDO_REG.read_text())
    return {"buildings": [], "counts": {}, "source": {}}


def _norm(s):
    """A building name reduced to the part that identifies it — case, spacing,
    punctuation and the word 'condominium' itself removed, since the register
    writes it and a shopfront usually does not."""
    s = (s or "").lower()
    s = re.sub(r"[\s\-–—_.,()\"']", "", s)
    for w in ("คอนโดมิเนียม", "คอนโด", "condominium", "condo", "อาคารชุด"):
        s = s.replace(w, "")
    return s


def join_register(reg_buildings, records):
    """(matched, unmatched) — register rows joined to catalogue records BY
    EXACT normalized name, and nothing looser.

    Substring matching was tried on 2026-08-21 and REJECTED, for the same
    reason the events layer rejected it: it matched นครพิงค์คอนโดมิเนียม to
    เพชรนครพิงค์ — a different building — and folded two separate registered
    buildings onto one record called บ้านสวน. An assessed valuation on the
    wrong building is a false statement about somebody's property, so a
    no-match is the correct default. Sixteen loose matches became eight true
    ones, and the other 377 rows are a discovery list rather than a guess.
    """
    idx = {}
    for r in records:
        for nm in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
            k = _norm(nm)
            if len(k) >= 4:
                idx.setdefault(k, r)
    matched, unmatched = [], []
    for e in reg_buildings:
        k = _norm(e.get("name"))
        r = idx.get(k) if len(k) >= 4 else None
        (matched.append((e, r)) if r else unmatched.append(e))
    return matched, unmatched


def _hav(lat1, lng1, lat2, lng2):
    p = math.pi / 180
    x = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p)
         * math.sin((lng2 - lng1) * p / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(x))


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    PROVINCES = g["PROVINCES"]
    shelf_og = g.get("shelf_og")

    reg = load_reg()
    (DOCS / "realestate.css").write_text(CSS)

    prov_of, all_recs = {}, []
    for p in PROVINCES:
        for r in data[p["key"]]:
            prov_of[r["id"]] = p["key"]
            all_recs.append(r)

    def href(r):
        return prov_of[r["id"]] + "/p/" + place_slug(r) + ".html"

    mine = [r for r in all_recs if "realestate" in (r.get("cat") or [])]

    def on(sub):
        out = [r for r in mine if sub in (r.get("sub") or [])]
        return sorted(out, key=lambda r: (r.get("name") or "").lower())

    condos, apartments, dorms, agents = on("condo"), on("apartment"), on("dorm"), on("agent")
    moobaans = on("moobaan")

    def listing(recs):
        """Alphabetical, with the reach the directory holds.

        Same shape as the elephant camps and the barbers, for the same
        reason. The one residential extra: a stated floor count (a mapper's
        building:levels) prints as a small mark, because it is the lift
        question half-answered before anyone climbs a stair.
        """
        rows = []
        for r in recs:
            a = r.get("attrs") or {}
            marks = []
            if r.get("phone"):
                marks.append("&#9742;")
            if a.get("lineId"):
                marks.append("LINE")
            if r.get("website") or a.get("facebook"):
                marks.append("&#127760;")
            if a.get("buildingLevels"):
                marks.append(esc(str(a["buildingLevels"])) + " " + bi("ชั้น", "fl"))
            ch = " <small>" + " · ".join(marks) + "</small>" if marks else ""
            cr = "" if prov_of[r["id"]] == "cm" else " <small>&middot;&#3594;&#3619;</small>"
            rows.append("<div><a href=\"" + href(r) + "\">" + name_bi(r) + "</a>" + ch + cr + "</div>")
        return "<div class=\"re-list\">" + "".join(rows) + "</div>"

    def note(th, en):
        return "<p class=\"re-note\">" + bi(th, en) + "</p>"

    def h2(th, en, n=None):
        c = "" if n is None else " <span class=\"re-count\">(" + str(n) + ")</span>"
        return "<h2>" + bi(th, en) + c + "</h2>"

    # ---- the words --------------------------------------------------------
    wrows = "".join(
        "<tr><td class=\"th\">" + esc(t) + "</td><td class=\"rtgs\">" + esc(rt)
        + "<br>" + esc(tone) + "</td><td>" + esc(en) + "<br><span class=\"root\">"
        + esc(root) + "</span></td><td>" + esc(nt) + "</td></tr>"
        for t, rt, tone, en, root, nt in WORDS)
    words_html = (
        "<table class=\"re-words\"><thead><tr><th>" + bi("คำ", "Word")
        + "</th><th>RTGS / " + bi("เสียง", "tone") + "</th><th>"
        + bi("แปล-ราก", "Meaning & root") + "</th><th>"
        + bi("ใช้ยังไง", "How it is used") + "</th></tr></thead><tbody>"
        + wrows + "</tbody></table>")

    say_html = "".join(
        "<div class=\"re-say\"><p class=\"line\">" + esc(th) + "</p><p class=\"gloss\">"
        + esc(rt) + "</p><p>" + esc(en) + "</p><p class=\"gloss\">" + esc(nt) + "</p></div>"
        for th, rt, en, nt in SAYINGS)

    # ---- the census, recomputed from the audit's own rules ---------------
    split, defaulted = audit_realestate.split_census(all_recs)
    silent = audit_realestate.silences(all_recs)
    landoffices = audit_realestate.landoffice(all_recs)
    hotelside = audit_realestate.hotel_overlap(all_recs)
    total = len(all_recs)

    import enrich_sites as _es
    linked = sorted([r for r in mine if r.get("website")],
                    key=lambda r: (r.get("name") or "").lower())
    queue = [r for r in linked if _es.first_hand(r.get("website") or "")]

    def li(th, en, val):
        return "<li>" + bi(th, en) + ": <b>" + str(val) + "</b></li>"

    census_html = (
        note("นับใหม่ทุกครั้งที่สร้างหน้า จากกฎเดียวกับ importers/audit_realestate.py",
             "Recounted on every build, from the same rules as importers/audit_realestate.py")
        + "<ul class=\"re-queue\">"
        + li("ชื่อตึกที่บอกว่าเฟอร์ครบ", "building names saying furnished", silent["furnished"])
        + li("ชื่อตึกที่บอกค่าน้ำ-ค่าไฟ หรือค่าส่วนกลาง",
             "building names posting a rate or a common fee", silent["rate"])
        + li("สำนักงานที่ดินในสารบัญทั้งสองจังหวัด",
             "Land Offices anywhere in this catalogue", len(landoffices))
        + li("ตึกที่ป้ายชื่อไม่บอกประเภทเลย (ลงชั้นอพาร์ตเมนต์ตามคำของแท็กเอง)",
             "buildings whose name states no kind (filed apartment, the tag's own word)",
             split["defaulted"])
        + li("ตึกที่บอกจำนวนชั้น (จากผู้ทำแผนที่)",
             "buildings with a stated floor count (from the mapper)",
             sum(1 for r in mine if (r.get("attrs") or {}).get("buildingLevels")))
        + li("คำเรียกที่พักรายเดือนบนชั้นโรงแรม — นับไว้ ไม่ย้าย",
             "monthly words sitting on the hotel shelf — counted, not re-filed by a rule",
             len(hotelside))
        + "</ul>"
        + note("บรรทัดแรก ๆ เป็นศูนย์ และตั้งใจพิมพ์ไว้ให้เห็น: ไม่มีกฎชื่อตึกไหนรอเขียนอยู่ ราคา เฟอร์ ค่าไฟ สัตว์เลี้ยง ตอบได้ทางเดียวคือตึกบอกเอง เจ้าของติ๊กเอง หรือมีคนไปถามหน้าโต๊ะ",
               "The zeros are printed rather than hidden: no name rule is waiting to be written. Rates, furniture, deposits and pets are answered by the building stating it, an owner ticking their own facets, or a person at the desk — and by nothing else."))

    # The Land Offices, once the door was opened. Before 2026-08-21 this block
    # printed a zero and said why; it now prints what the crawl found AND what
    # it still does not have, because a partial fill announced as a full one is
    # the failure this page exists to avoid.
    if landoffices:
        lrows = "".join(
            "<div><a href=\"" + href(r) + "\">" + name_bi(r) + "</a>"
            + ("" if prov_of[r["id"]] == "cm" else " <small>&middot;&#3594;&#3619;</small>")
            + "</div>" for r, _ in sorted(landoffices, key=lambda x: x[1]))
        gap_html = (
            "<div class=\"re-gap\"><b>" + (g.get("svg_icon") or (lambda *a, **k: ""))("i-document", 20, "re-ic") + " "
            + bi("สำนักงานที่ดิน — ที่ที่การโอนโฉนดเกิดขึ้นจริง",
                 "The Land Office — where a chanote transfer actually happens")
            + "</b><p>"
            + bi("การโอนโฉนดทุกครั้งในภาคเหนือเดินผ่านสำนักงานที่ดิน และจนถึง 21 ส.ค. สารบัญนี้ไม่มีสักแห่ง เพราะการเก็บข้อมูลไม่เคยถามหา ตอนนี้ถามแล้ว (office=government) และได้มาเท่านี้",
                 "Every chanote transfer in the north walks through a Land Office, and until 21 August this catalogue held none — the crawl had never asked. It has now (office=government), and this is what came back.")
            + "</p><div class=\"re-ct\">" + lrows + "</div><p class=\"re-note\">"
            + bi("และนี่คือส่วนที่ยังขาด: แผนที่เปิดถือสาขาของเชียงใหม่ไว้สองสาขา แต่ไม่มีสำนักงานที่ดินจังหวัดเชียงใหม่ (สาขาเมือง) ซึ่งเป็นแห่งที่คนไปกันมากที่สุด การไม่เจอในแผนที่ไม่ได้แปลว่าไม่มี — แปลว่ายังไม่มีใครปักหมุดไว้ โทรถามสำนักงานจังหวัดก่อนเดินทางเสมอ",
                 "And here is what is still missing: the open map holds two Chiang Mai branch offices but not สำนักงานที่ดินจังหวัดเชียงใหม่ itself, the Mueang seat, which is the one most people go to. Absent from a map is not absent from the world — it means nobody has pinned it. Ring the provincial office before travelling either way.")
            + "</p></div>")
    else:
        gap_html = (
            "<div class=\"re-gap\"><b>" + (g.get("svg_icon") or (lambda *a, **k: ""))("i-document", 20, "re-ic") + " "
            + bi("สำนักงานที่ดิน — ศูนย์ทั้งสารบัญ",
                 "The Land Office — zero, in the whole catalogue")
            + "</b><p>"
            + bi("การโอนโฉนดทุกครั้งในภาคเหนือเดินผ่านสำนักงานที่ดิน และสารบัญนี้ยังไม่มีสักแห่ง — ไม่ใช่เพราะไม่มีจริง แต่เพราะการเก็บข้อมูลไม่เคยถามหา (office=government)",
                 "Every chanote transfer in the north walks through a Land Office, and this catalogue holds none — not because they do not exist, but because the crawl never asked (office=government).")
            + "</p></div>")

    # ---- the Treasury's own register --------------------------------------
    creg = load_condo_reg()
    cbuild = creg.get("buildings") or []
    creg_html = ""
    if cbuild:
        matched, unmatched = join_register(cbuild, mine)
        csrc = creg.get("source") or {}
        edition = csrc.get("edition") or creg.get("generated") or ""
        cm_n = sum(1 for e in cbuild if e["province"] == "cm")
        cr_n = sum(1 for e in cbuild if e["province"] == "cr")

        def baht(e):
            lo, hi = e.get("assessed_low"), e.get("assessed_high")
            if not lo:
                return "—"
            if hi and hi != lo:
                return f"{lo:,}–{hi:,}"
            return f"{lo:,}"

        mrows = "".join(
            "<div><a href=\"" + href(r) + "\">" + name_bi(r) + "</a> <span class=\"m\">"
            + baht(e) + " " + bi("บาท/ตร.ม.", "B/m²") + "</span></div>"
            for e, r in sorted(matched, key=lambda x: (x[0].get("name") or "")))
        creg_html = (
            h2("ทะเบียนอาคารชุดของกรมธนารักษ์", "The Treasury's condominium register",
               len(cbuild))
            + "<div class=\"re-rule\"><b>&#129534; "
            + bi("ราคาประเมิน ไม่ใช่ราคาตลาด", "An assessed value is not a market price")
            + "</b>"
            + bi("ตัวเลขนี้คือราคาประเมินของกรมธนารักษ์ ซึ่งใช้คิดค่าธรรมเนียมการโอนและภาษี ไม่ใช่ราคาซื้อขาย ไม่ใช่ราคาที่ประกาศ และตามปกติจะต่ำกว่าทั้งสองอย่างมาก อาคารหนึ่งมีหลายบรรทัดตามประเภทการใช้และชั้น จึงแสดงเป็นช่วง ไม่ใช่ตัวเลขเดียว",
                 "This is the Treasury's assessed value — the figure transfer fees and taxes are reckoned from. It is not a sale price, not an asking price, and normally well below both. A building carries a row per use category and floor band, so it is shown as a spread and not as one welded number.")
            + "</div>"
            + note("ทะเบียนราชการนับอาคารชุดจดทะเบียนในเชียงใหม่ " + f"{cm_n:,}" + " แห่ง และเชียงราย "
                   + f"{cr_n:,}" + " แห่ง ก่อนหน้านี้สารบัญนี้ถือแค่ 53 แห่งที่ชื่อบอกเองว่าเป็นคอนโด เพราะแผนที่เปิดรู้เท่านั้น ตอนนี้ชั้นคอนโดมี " + str(len(condos))
                   + " แห่ง · ฉบับ " + esc(edition),
                   "The government register counts " + f"{cm_n:,}" + " registered condominium buildings in Chiang Mai and "
                   + f"{cr_n:,}" + " in Chiang Rai. This catalogue held 53 — the ones whose own name says condominium, which is all the open map knows. The condo shelf now holds " + str(len(condos))
                   + " · edition " + esc(edition))
            + "<h3>" + bi("ทะเบียนนี้กลายเป็นรายการในสารบัญแล้ว", "The register is now in the catalogue")
            + " <span class=\"re-count\">(" + str(len(matched)) + ")</span></h3>"
            + note("อาคารที่จดทะเบียนทุกหลังมีหน้าของตัวเองแล้ว ค้นเจอด้วยชื่อ และอยู่ในชั้นคอนโดของอำเภอตัวเอง แบบเดียวกับที่ทะเบียนวัดของสำนักพุทธฯ เติมชั้นวัดเมื่อก่อน · จับคู่กับรายการเดิมด้วยชื่อที่ตรงกันเท่านั้น ไม่เคยใช้การจับแบบใกล้เคียง — การจับแบบหลวมเคยจับ นครพิงค์คอนโดมิเนียม ไปหา เพชรนครพิงค์ ซึ่งคนละอาคาร การเอาราคาประเมินไปแปะผิดอาคารคือการพูดผิดเรื่องทรัพย์สินของคนอื่น ชื่อที่ใกล้เคียงกันถูกเขียนไว้ให้คนอ่านตัดสิน ไม่รวมให้เอง",
                   "Every registered building now has its own page, is findable by name, and stands on its amphoe's condo shelf — the same way the Sangha's temple register filled the wat shelf. Joined to existing records by exact name only, never by a near match: a loose join put นครพิงค์คอนโดมิเนียม onto เพชรนครพิงค์, a different building, and an assessed valuation on the wrong building is a false statement about somebody's property. Near-misses are written down for a person to settle, never merged automatically.")
            + "<div class=\"re-ct\">" + mrows + "</div>"
            + note("สิ่งที่ยังขาดคือหมุดกับเบอร์โทร ไม่ใช่ตัวรายการ ทะเบียนไม่มีพิกัดสักแห่ง อาคารที่มาจากทะเบียนจึงขึ้นว่า ยังไม่มีหมุด และอยู่ในหน้า ตามหาหมุด รอคนไปปักให้ ทะเบียนเต็มอยู่ที่ data/curated/condo_register.json",
                   "What is missing now is pins and phone numbers, not records: the register carries no coordinate at all, so every building that arrived from it says needs-pin and waits on the pin hunt for somebody to place it. The full register is at data/curated/condo_register.json.")
            + note("ที่มา: " + esc(csrc.get("publisher") or "กรมธนารักษ์") + " · "
                   + esc(csrc.get("licence") or "") + " · data.go.th",
                   "Source: " + esc(csrc.get("publisher") or "the Treasury Department") + " · "
                   + esc(csrc.get("licence") or "") + " · data.go.th"))

    # ---- the register (empty, and saying so) ------------------------------
    stated_rows = [x for x in (reg.get("buildings") or []) if x.get("stated")]
    if stated_rows:
        by_id = {r["id"]: r for r in all_recs}
        FLABEL = {k: (f["th"], f["en"], f.get("icon", ""))
                  for k, f in (g.get("FACET_DEF") or {}).get("realestate", {}).items()}
        cards = []
        for x in stated_rows:
            r = by_id.get(x["place"])
            title = ('<a href="' + href(r) + '">' + name_bi(r) + "</a>") if r else esc(x.get("name") or "")
            lines = []
            for k in x["stated"]:
                th, en, ic = FLABEL.get(k, (k, k, ""))
                lines.append("<li>" + esc(ic) + " " + bi(th, en) + "</li>")
            src = esc(x.get("source", ""))
            cards.append(
                '<div class="re-ct"><b>' + title + "</b><ul>" + "".join(lines) + "</ul>"
                + '<p class="re-note">' + bi("อ่านจากช่องทางของตึกเอง", "read from the building's own channel")
                + ' · <a href="' + att(src) + '" rel="noopener nofollow">' + esc(src)
                + "</a> · " + bi("เมื่อ", "on") + " " + esc(x.get("fetched", "")) + "</p></div>")
        reg_html = "".join(cards)
    else:
        qrows = "".join("<li><a href=\"" + href(r) + "\">" + name_bi(r) + "</a></li>"
                        for r in queue)
        reg_html = (
            "<p>"
            + bi("ยังไม่มีตึกไหนถูกอ่าน — และนั่นคือสถานะจริง ไม่ใช่การลืม การอ่านหน้าเว็บของตึกคืองานที่ต้องต่อเน็ต ส่วนงานชุดนี้สร้างแบบไม่ต่อเน็ตทั้งชุด คิวพร้อมแล้ว",
                 "No building has been read yet, and that is the true state rather than an omission: reading a building's own pages is network work, and this build was zero-network throughout. The queue is ready.")
            + "</p>"
            + note("ตึกที่มีเว็บของตัวเองให้อ่านแล้ว", "Buildings that already have a site of their own to read")
            + "<ul class=\"re-queue\">" + qrows + "</ul>"
            + "<p class=\"re-note\">"
            + bi("โครงของทะเบียนอยู่ใน", "The register's shape is in")
            + " <code>data/curated/realestate.json</code> &middot; "
            + bi("ขั้นตอนที่รอไฟเขียว", "the steps awaiting a go")
            + " <code>notes/realestate-proposal-2026-08-21.md</code></p>")

    # ---- near the Chiang Rai clock tower ----------------------------------
    # The anchor is resolved BY NAME from the catalogue's own records (the
    # WO-24 lesson: an id can be renumbered by a re-crawl; a landmark's name
    # cannot). Straight-line metres from catalogue coordinates, and the page
    # says so — a computed distance shown as anything else would be the
    # nearest-first lie the toilets page refused.
    ct_html = ""
    anchor = next((r for r in all_recs
                   if r.get("province") == "cr" and "sights" in (r.get("cat") or [])
                   and "หอนาฬิกาเฉลิมพระเกียรติ" in (r.get("name") or "")
                   and r.get("lat")), None)
    if anchor:
        near = []
        for r in mine:
            if prov_of[r["id"]] == "cr" and r.get("lat"):
                d = _hav(anchor["lat"], anchor["lng"], r["lat"], r["lng"])
                if d <= 1500:
                    near.append((int(d), r))
        near.sort(key=lambda x: x[0])
        if near:
            rows = "".join(
                "<div><span class=\"m\">" + str(d) + " " + bi("ม.", "m") + "</span> — "
                + "<a href=\"" + href(r) + "\">" + name_bi(r) + "</a></div>"
                for d, r in near)
            ct_html = (
                h2("ใกล้หอนาฬิกาเชียงราย", "Near the Chiang Rai clock tower", len(near))
                + note("จุดนัดพบของเชียงราย — ที่พักในสารบัญภายใน 1.5 กม. จาก" + "หอนาฬิกาเฉลิมพระเกียรติฯ "
                       + "ระยะเป็นเส้นตรงจากพิกัดในสารบัญ ไม่ใช่ระยะเดิน · ยังไม่มีตึกไหนแถวนี้เรียกตัวเองว่าคอนโด — ชั้นนี้พูดตามป้ายเท่านั้น",
                       "Chiang Rai's meeting point — every residential record within 1.5 km of the golden clock tower. Straight-line metres from catalogue coordinates, not a walking distance · no building this close calls itself a condominium yet; this list only says what the signs say.")
                + '<div class="re-ct">' + rows + "</div>")

    # ---- assemble ---------------------------------------------------------
    intro = bi(
        "หน้านี้มีสี่อย่าง: คำที่ใช้ถามก่อนวางมัดจำ (ภาษาไทย เสียงอ่าน และรากคำ — รวมเหตุที่ตึกถูกสุดในเมืองชื่อ แมนชั่น) · ชั้นคอนโด อพาร์ตเมนต์ หอพัก และนายหน้า หลังการแยกชั้นตามป้ายจริงของตึก · ตัวเลขจริงของสิ่งที่ยังไม่มีใครถามตึกเลย · และทะเบียนสิ่งที่ตึกบอกเอง เรียงตามตัวอักษร",
        "Four things on one page: the words to ask before the deposit, in Thai, with the sounds and the roots — including why the cheapest buildings in town are called Mansion · the condo, apartment, dorm and agent shelves, split by what each building's own sign says · the real counts of what nobody has asked the buildings yet · and the register of what buildings state for themselves. Alphabetical.")

    # THE SECTION'S DOORS (client 2026-09-27: "Motdang needs a real estate
    # section"). One row of nouns, each with its count: the offers on the
    # Listing Sheet, the buildings on this page, the words, the way in for a
    # listing agent, and the same rows as MLS-shaped data (listing-sheet
    # reso.py). Counts are read at build time from what is on disk.
    import listings_layer as _ll
    _join = _ll._load()
    live_n = sum(e.get("live", 0) for e in _join.values())
    bld_n = len(condos) + len(apartments) + len(dorms) + len(moobaans)
    icon = g.get("svg_icon") or (lambda *a, **k: "")
    # /listings/join is answered by the site Worker (publish/lister.js), which
    # ships on a separate deploy from these pages. data/config.json
    # "listerJoin": true is set when that Worker is live, so this page never
    # links a door the edge cannot answer yet.
    try:
        join_live = bool(json.loads((ROOT / "data" / "config.json").read_text()).get("listerJoin"))
    except (OSError, ValueError):
        join_live = False

    def door(href_, ic, th, en, n=None):
        c = "" if n is None else " <span class=\"re-count\">(" + str(n) + ")</span>"
        return ("<a class=\"re-tile\" href=\"" + href_ + "\">" + icon(ic, 22, "re-ic")
                + "<span>" + bi(th, en) + c + "</span></a>")

    door_html = (
        "<nav class=\"re-doors\" aria-label=\"อสังหาฯ · Real estate\">"
        + (door("listings/register/index.html", "i-home2", "ทะเบียนตึก", "The register", bld_n)
           if (_ll.SHEET / "out" / "register" / "index.html").exists()
           else door("#shelves", "i-home2", "ตึก", "Buildings", bld_n))
        + door("listings/", "i-tag", "ประกาศขาย-เช่า", "Listings", live_n or None)
        + door("#words", "i-book", "คำศัพท์", "Words")
        + door("listings/add.html", "i-plus-circle", "ลงประกาศ", "List a property")
        + (door("listings/join", "i-me", "สมัครเป็นนายหน้า", "Join as an agent")
           if join_live else "")
        + (door("listings/reso/index.json", "i-download", "ข้อมูล", "Data")
           if (_ll.SHEET / "out" / "reso" / "index.json").exists() else "")
        + "</nav>")

    # RENTS AND PRICES BY TAMBON — glean.py's aggregate of what listers sent
    # (data/gleaned/prices.json). Cells glean withheld for being too thin are
    # not in the file; an empty or missing file prints nothing.
    prices_html = ""
    try:
        _pc = json.loads((ROOT / "data" / "gleaned" / "prices.json").read_text(encoding="utf-8"))
        cells = _pc.get("cells") or []
    except (OSError, ValueError):
        cells = []
    if cells:
        KIND = {"house": ("บ้าน", "house"), "condo": ("คอนโด", "condo"),
                "apartment": ("อพาร์ตเมนต์", "apartment"), "townhouse": ("ทาวน์เฮาส์", "townhouse"),
                "land": ("ที่ดิน", "land"), "room": ("ห้อง", "room"),
                "commercial": ("อาคารพาณิชย์", "commercial"), "compound": ("บ้านหลายหลัง", "compound")}
        OFFER = {"rent": ("เช่า/เดือน", "rent/month"), "sale": ("ขาย", "sale")}

        def baht(v):
            return "&#3647;" + format(int(round(v)), ",") if v is not None else ""
        rows_ = "".join(
            "<tr><td>" + esc(c.get("tambon") or "") + "</td><td>"
            + bi(*KIND.get(c.get("kind"), (c.get("kind"), c.get("kind")))) + "</td><td>"
            + bi(*OFFER.get(c.get("offer"), (c.get("offer"), c.get("offer")))) + "</td><td>"
            + esc(str(c.get("bedrooms") if c.get("bedrooms") is not None else "")) + "</td><td>"
            + str(c.get("n", "")) + "</td><td><b>" + baht(c.get("median")) + "</b></td><td>"
            + baht(c.get("p25")) + "&ndash;" + baht(c.get("p75")) + "</td><td>"
            + esc(str(c.get("from") or "")) + "&ndash;" + esc(str(c.get("to") or "")) + "</td></tr>"
            for c in sorted(cells, key=lambda c: (c.get("province") or "", c.get("tambon") or "",
                                                  c.get("kind") or "", c.get("offer") or "")))
        prices_html = (
            h2("ราคาตามตำบล", "Prices by tambon")
            + "<div class=\"re-scroll\"><table class=\"re-words\"><thead><tr><th>" + bi("ตำบล", "Tambon") + "</th><th>"
            + bi("ประเภท", "Kind") + "</th><th>" + bi("ขาย-เช่า", "Offer") + "</th><th>"
            + bi("ห้องนอน", "Beds") + "</th><th>n</th><th>" + bi("มัธยฐาน", "Median")
            + "</th><th>" + bi("ช่วงกลาง", "Middle half") + "</th><th>" + bi("วันที่", "Dates")
            + "</th></tr></thead><tbody>" + rows_ + "</tbody></table></div>")

    og = shelf_og("cm", "realestate") if shelf_og else None
    body = (
        "<h1>" + icon("i-home2", 30, "re-ic") + " "
        + bi("อสังหาฯ-ที่พัก — คำที่ใช้ถาม ตึกที่มี และสิ่งที่ยังไม่มีใครถาม",
             "Real estate & places to live — the words to ask, the buildings, and what nobody has asked them")
        + "</h1>" + door_html + "<p class=\"re-intro\">" + intro + "</p>"
        + prices_html

        + h2("คำที่ใช้ถามก่อนวางมัดจำ", "The words to ask before the deposit").replace("<h2>", "<h2 id=\"words\">", 1)
        + note("ค่าเช่าที่เห็นไม่ใช่ราคาจริงของห้อง จนกว่าจะรู้ค่าไฟหน่วยละ ค่าน้ำ ค่าส่วนกลาง และมัดจำ — คำพวกนี้ไม่อยู่บนเว็บประกาศไหนเลย",
               "The rent on the sign is not the price of the room until you know the per-unit electric rate, the water rate, the common fee and the deposit — none of which any listing site prints.")
        + words_html

        + h2("ประโยคที่ใช้ได้จริงหน้าโต๊ะ", "Sentences that work at the desk")
        + say_html

        + h2("ชั้นหลังการแยก", "The shelves, after the split").replace("<h2>", "<h2 id=\"shelves\">", 1)
        + note("จนถึง 21 ส.ค. ตึกทุกหลังถูกจัดเป็น “อาคารคอนโด” ทั้งที่ป้ายบอกว่าเป็นคอนโดจริง 53 หลัง — ที่เหลือคือแมนชั่น คอร์ท อพาร์ตเมนต์ และหอพัก ตอนนี้แยกตามคำบนป้ายของตึกเอง ความผิดแบบเดียวกับชั้นร้านตัดผมชาย (6 จาก 62) และแก้แบบเดียวกัน: อ่านป้าย",
               "Until 21 August every building here was filed as a Condo Building, while the signs said condominium on 53. The rest are mansions, courts, apartments and dorms — now shelved by the word on each building's own sign. The same error as the barber shelf (6 of 62), corrected the same way: read the signs.")

        + "<h3>" + bi("อาคารชุด-คอนโด", "Condominiums") + " <span class=\"re-count\">(" + str(len(condos)) + ")</span></h3>"
        + note("ตึกที่ชื่อหรือผู้ทำแผนที่บอกเองว่าเป็นคอนโด · ☎ LINE 🌐 คือช่องทางที่สารบัญมี · เลขชั้นมาจากผู้ทำแผนที่",
               "Buildings whose own name (or mapper) says condominium · ☎ LINE 🌐 mark the reach the directory holds · floor counts come from the mapper")
        + listing(condos)

        + "<h3>" + bi("หอพัก", "Dormitories") + " <span class=\"re-count\">(" + str(len(dorms)) + ")</span></h3>"
        + note("หนาแน่นรอบมหาวิทยาลัย ป้ายบอกเองว่ารับใคร — หอพักหญิง หอพักชาย",
               "Thickest around the universities; the signs state who they house — หอพักหญิง women's, หอพักชาย men's")
        + listing(dorms)

        + "<h3>" + bi("หมู่บ้านจัดสรร", "Housing estates") + " <span class=\"re-count\">(" + str(len(moobaans)) + ")</span></h3>"
        + note("ชั้นนี้ว่างเปล่าจนถึง 21 ส.ค. เพราะการเก็บข้อมูลไม่เคยถามหาพื้นที่อยู่อาศัยที่มีชื่อ ตอนนี้ถามแล้ว และเข้าเฉพาะที่ชื่อบอกเองว่าเป็นโครงการ — จัดสรร หรือชื่อผู้พัฒนาบนซุ้มทางเข้า ส่วนพื้นที่อยู่อาศัยที่มีชื่ออีก 590 แห่งถูกกันไว้ เพราะเป็นหมู่บ้านจริงที่คนอยู่อาศัย ไม่ใช่โครงการที่ใครขาย คำว่า หมู่บ้าน เฉย ๆ ไม่เคยเป็นกฎ",
               "This shelf was empty until 21 August: the crawl had never asked for named residential areas. It has now, and only names that declare a development enter — จัดสรร, or a developer's name on the entrance arch. Another 590 named residential areas were held back, because they are villages where people live rather than projects somebody is selling. Bare หมู่บ้าน is never a rule.")
        + listing(moobaans)

        + "<h3>" + bi("นายหน้า-เอเจนต์", "Agents & agencies") + " <span class=\"re-count\">(" + str(len(agents)) + ")</span></h3>"
        + note("ห้าราย และหน้านี้บอกว่าห้าราย — OpenStreetMap ของสองจังหวัดมีเท่านี้ วงการนายหน้าที่นี่อยู่บน LINE กับเฟซบุ๊ก ไม่ได้อยู่บนแผนที่ และเว็บของบริษัทนายหน้าเองก็อ่านด้วยเครื่องไม่ได้ (ลองแล้ว 21 ส.ค.: รายหนึ่งตอบ 403 อีกรายหน้าเว็บว่างเปล่าเพราะเรนเดอร์ด้วยสคริปต์) ที่เหลือในผลค้นหาคือเว็บรวมประกาศ ซึ่งเป็นรายการที่คนอื่นทำถึงนายหน้า ไม่ใช่คำของนายหน้าเอง การเติมชั้นนี้จึงเป็นงานภาคสนามและความสัมพันธ์จริง",
               "Five, and this page says five — that is all OpenStreetMap holds across both provinces. The brokerage trade here lives on LINE and Facebook, not on the map, and the agencies' own sites cannot be read by machine either (tried 21 August: one answers 403, another renders its page with scripts and hands a reader nothing). Everything else in a search result is a listings portal — somebody else's listing OF an agency, not the agency speaking. Filling this shelf is field work and real relationships.")
        + listing(agents)

        + "<h3>" + bi("อพาร์ตเมนต์-แมนชั่น-คอร์ท", "Apartments, mansions & courts") + " <span class=\"re-count\">(" + str(len(apartments)) + ")</span></h3>"
        + note("ชั้นที่ใหญ่ที่สุด — ที่พักรายเดือนของเมืองทั้งเมือง เรียงหมดทุกหลังอยู่ที่หน้าชั้นของแต่ละจังหวัด",
               "The biggest shelf — the city's monthly housing. The full alphabetical list lives on each province's shelf page.")
        + "<ul class=\"re-queue\">"
        + "<li><a href=\"cm/realestate/apartment/\">" + bi("เชียงใหม่", "Chiang Mai") + "</a> ("
        + str(sum(1 for r in apartments if prov_of[r["id"]] == "cm")) + ")</li>"
        + "<li><a href=\"cr/realestate/apartment/\">" + bi("เชียงราย", "Chiang Rai") + "</a> ("
        + str(sum(1 for r in apartments if prov_of[r["id"]] == "cr")) + ")</li>"
        + "</ul>"

        + ct_html

        + h2("ยังตอบไม่ได้", "Still unanswered")
        + gap_html
        + "<h3>" + bi("สำมะโนความเงียบ", "A census of the silence") + "</h3>"
        + census_html

        + h2("ทะเบียน — ตึกบอกเองว่าอะไร", "The register — what each building states")
        + reg_html

        + creg_html

        + h2("ชั้นอื่นที่เกี่ยวข้อง", "The rest of the shelf")
        + "<ul class=\"re-queue\">"
        + "<li><a href=\"cm/realestate/\">" + bi("อสังหาฯ เชียงใหม่ ทั้งหมวด", "The whole Chiang Mai shelf") + "</a></li>"
        + "<li><a href=\"cr/realestate/\">" + bi("อสังหาฯ เชียงราย ทั้งหมวด", "The whole Chiang Rai shelf") + "</a></li>"
        + "<li><a href=\"cm/hotel/\">" + bi("โรงแรม-ที่พักรายวัน", "Hotels & nightly stays") + "</a> — "
        + bi("เรสซิเดนซ์-อพาร์ตเมนต์ที่ขายรายคืนอยู่ที่นั่น (" + str(len(hotelside)) + " ชื่อ) ตามที่ตึกประกาศเอง",
             "the residences and serviced apartments that sell by the night live there (" + str(len(hotelside)) + " names), as those buildings themselves state") + "</li>"
        + "<li><a href=\"cm/home-services/\">" + bi("ช่าง-งานบ้าน", "Home services") + "</a> — "
        + bi("หลังจากได้ห้องแล้ว", "for after you have the room") + "</li>"
        + "</ul>"
        + share_block(BASE + "realestate.html", "อสังหาฯ-ที่พัก คำที่ใช้ถามก่อนวางมัดจำ · มดแดง", card=og))

    title = ("อสังหาฯ เชียงใหม่-เชียงราย — คอนโด อพาร์ตเมนต์ หอพัก คำที่ใช้ถามก่อนวางมัดจำ"
             " · Real estate in Chiang Mai & Chiang Rai — condos, apartments, dorms")
    desc = ("คำไทยสำหรับเช่าห้อง ซื้อคอนโด ค่าไฟหน่วยละ มัดจำ ค่าส่วนกลาง โฉนด นิติบุคคล "
            "พร้อมเสียงอ่านและรากคำ · ชั้นอาคารชุด-คอนโด อพาร์ตเมนต์-แมนชั่น-คอร์ท และหอพัก "
            "ของเชียงใหม่-เชียงราย แยกตามป้ายจริงของตึก · Thai words for renting a room or "
            "buying a condo in Chiang Mai — the per-unit electric rate, the deposit, the "
            "common fee, the chanote and the juristic office, with sounds and roots; the "
            "condominium, apartment, mansion, court and dormitory shelves of Chiang Mai "
            "and Chiang Rai; and a plain census of what no building has been asked yet")
    crumbs = ("<a href=\"index.html\">" + bi("หน้าแรก", "Home") + "</a> › "
              + bi("อสังหาฯ-ที่พัก", "Real estate"))
    (DOCS / "realestate.html").write_text(page(
        title, body, depth=0, path="realestate.html", desc=desc,
        extra_head="<link rel=\"stylesheet\" href=\"realestate.css\">", og=og, crumbs=crumbs))
    return {"page": 1, "words": len(WORDS), "sentences": len(SAYINGS),
            "condo": len(condos), "apartment": len(apartments), "dorm": len(dorms),
            "agent": len(agents), "moobaan": len(moobaans), "defaulted": split["defaulted"],
            "read_queue": len(queue), "hotelside": len(hotelside),
            "landoffice": len(landoffices), "neartower": ct_html and 1 or 0,
            "official_register": len(cbuild), "register_matched": len(matched) if cbuild else 0}
