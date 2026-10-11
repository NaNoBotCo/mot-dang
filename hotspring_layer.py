#!/usr/bin/env python3
"""น้ำพุร้อน — the northern hot-springs register, the map, and what to know
before you soak, on one page (/namphuron.html). WO-23.

Three things a reader asks about a soak, in the order they ask them:

  1. WHERE, AND HOW FAR — the whole north on one drawn map: every spring the
     register holds, Chiang Mai and Chiang Rai as records, the other
     provinces harvested area-clipped from OSM and the provinces' own open
     lists. No tiles: the basemap archive covers two provinces and this page
     covers seventeen, so the map is drawn ink, the same trade the events
     page made.
  2. WHAT EACH ONE STATES — the register: temperature with who measured it,
     the posted fee spread, hours, pools/private tubs/egg baskets as the
     operator's own words. "unstated" is a column value meaning the pages
     read did not say.
  3. WHAT YOU ARE LOOKING AT — the words (โป่ง, the mineral-seep word half
     the north is named after), the egg basket, the park gate, and the one
     safety line every spring posts in its own way: the hottest pool is for
     eggs, not people.

The spring states; the measurement carries its source. What the water is said
to be good for is the operator's or the tradition's claim and renders as a
claim.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
elephant layer. Emits namphuron.html + namphuron.css, copies the register to
docs/data/hotsprings.json; prints the counts.
"""
import json
import math
import re
from pathlib import Path

import regional_ground as rg

ROOT = Path(__file__).resolve().parent
REG = ROOT / "data" / "hotsprings.json"

CSS = """
.hs-intro{font-size:1.02rem;max-width:46rem}
.hs-reg{width:100%;border-collapse:collapse;margin:.6rem 0 .4rem;font-size:.93rem}
.hs-reg th,.hs-reg td{padding:.4rem .35rem;border-bottom:1px solid rgba(0,0,0,.08);text-align:center;vertical-align:top}
.hs-reg th:first-child,.hs-reg td:first-child{text-align:left}
.hs-reg td.un{color:var(--mute);font-style:italic}
.hs-reg .venue a{text-decoration:none;color:inherit}
.hs-reg .venue a:hover{text-decoration:underline}
.hs-reg .venue small{display:block;color:var(--mute);font-weight:400;font-size:.8rem}
.hs-legend{color:var(--mute);font-size:.85rem;margin:.2rem 0 1rem}
.hs-map{margin:.6rem 0 .2rem;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;
  background:var(--card,#fff);overflow:hidden}
.hs-map svg{display:block;width:100%;height:auto}
.hs-credit{color:var(--mute);font-size:.78rem;margin:.15rem 0 1rem}
.hs-prov{margin:.9rem 0 .2rem}
.hs-prov h3{margin:.9rem 0 .2rem}
.hs-prov h3 .count{color:var(--mute);font-weight:400}
.hs-row small{color:var(--mute)}
.hs-row .src a{color:var(--mute);font-size:.82rem}
.hs-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));margin:.6rem 0}
.hs-card{padding:.8rem .95rem;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;background:var(--card,#fff)}
.hs-card h3{margin:.1rem 0 .4rem}
.hs-card .say{display:block;margin-top:.5rem;color:var(--mute);font-size:.9rem}
.hs-words{margin:.2rem 0 .2rem;padding-left:1.1rem}
.hs-words li{margin:.22rem 0}
.hs-note{color:var(--mute);font-size:.9rem}
.hs-pin{fill:var(--ant,#b3402a);stroke:#fff;stroke-width:1}
.hs-pin-far{fill:#7d6a52;stroke:#fff;stroke-width:1}
.hs-maplabel{font-size:11px;fill:#5a4f42;paint-order:stroke;stroke:#f7f1e3;stroke-width:3px;
  stroke-linejoin:round}
"""


def load_reg():
    if REG.exists():
        return json.loads(REG.read_text())
    return {"provinces": {}, "springs": [], "unverified": []}


def _map_svg(springs, provinces, bi_text, esc):
    """The north, drawn: one pin per pinned spring on regional_ground's
    provinces, rivers and main roads (Natural Earth + OSM), a km scale bar,
    the credits in the caption below. Equirectangular with cos(lat)
    correction — the same projection the events map earned, at province
    scale. Province names sit at each province's own middle."""
    pts = [s for s in springs if s.get("lat") and s.get("lng")]
    if len(pts) < 3:
        return ""
    lats = [float(s["lat"]) for s in pts]
    lngs = [float(s["lng"]) for s in pts]
    lat0 = (min(lats) + max(lats)) / 2
    kx = 111.320 * math.cos(math.radians(lat0))
    ky = 110.574
    span_x = (max(lngs) - min(lngs)) * kx
    span_y = (max(lats) - min(lats)) * ky
    W = 760
    PAD = 46
    scale = (W - 2 * PAD) / span_x
    H = int(span_y * scale) + 2 * PAD
    if H > 900:
        scale *= 900 / H
        H = 900

    def ll(lat, lng):
        return (PAD + (lng - min(lngs)) * kx * scale,
                PAD + (max(lats) - lat) * ky * scale)

    def xy(s):
        return ll(float(s["lat"]), float(s["lng"]))

    home_pins, far_pins, labels, avoid, placed = [], [], [], [], []
    for s in pts:
        x, y = xy(s)
        avoid.append((x, y, 8))
        cls = "hs-pin" if s["province"] in ("cm", "cr") else "hs-pin-far"
        (home_pins if s["province"] in ("cm", "cr") else far_pins).append(
            f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="4.6"/>')
        if s.get("curated"):
            nm = s.get("nameTh") or s.get("name") or ""
            half = len(nm) * 3.2
            # Right of the pin, else left of it; a name that fits neither
            # side of a name already placed stays in the list below.
            for anchor, tx in (("start", x + 7), ("end", x - 7)):
                if not (PAD - 30 <= (tx if anchor == "start" else tx - 2 * half)
                        and (tx + 2 * half if anchor == "start" else tx) <= W - 8):
                    continue
                cx = tx + half if anchor == "start" else tx - half
                if all(abs(cx - lx) > half + lh or abs(y - ly) > 14 for lx, ly, lh in placed):
                    placed.append((cx, y, half))
                    avoid.append((cx, y, half))
                    labels.append(f'<text class="hs-maplabel" x="{tx:.1f}" y="{y + 4:.1f}" '
                                  f'text-anchor="{anchor}">{esc(nm)}</text>')
                    break
    ground = rg.svg(rg.load(), ll, W, H, river_names=("Ping", "Nan", "Yom", "Wang"),
                    avoid=avoid)
    km50 = 50 * scale
    bar = (f'<g><line x1="{PAD}" y1="{H - 18}" x2="{PAD + km50:.1f}" y2="{H - 18}" '
           f'stroke="#7d6a52" stroke-width="2"/>'
           f'<text class="hs-maplabel" x="{PAD}" y="{H - 24}">50 km</text></g>')
    label = bi_text("แผนที่น้ำพุร้อนภาคเหนือ — หมุดหนึ่งจุดต่อหนึ่งบ่อ บนเส้นแบ่งจังหวัด แม่น้ำ และถนนสายหลัก",
                    "Map of northern Thailand hot springs, one pin per spring, on the "
                    "province lines, rivers and main roads")
    return (f'<div class="hs-map"><svg role="img" aria-label="{esc(label)}" '
            f'viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="{W}" height="{H}" fill="#f4efe4"/>'
            + ground + "".join(far_pins) + "".join(home_pins)
            + "".join(labels) + bar + "</svg></div>")


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi, name_of = g["place_slug"], g["name_bi"], g["name_of"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    PROVINCES = g["PROVINCES"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")

    reg = load_reg()
    springs = reg.get("springs", [])
    provinces = reg.get("provinces", {})
    (DOCS / "namphuron.css").write_text(CSS + rg.CSS)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "hotsprings.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1))

    by_id, prov_of = {}, {}
    for p in PROVINCES:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]

    def href(r):
        return f'{prov_of[r["id"]]}/p/{place_slug(r)}.html'

    def nm_of(s):
        th, en = s.get("nameTh"), s.get("nameEn")
        if th and en:
            return bi(th, en)
        return esc(s.get("name") or th or en or "")

    def link_of(s):
        r = by_id.get(s.get("recordId") or "")
        if r:
            return f'<a href="{href(r)}">{name_bi(r)}</a>'
        return nm_of(s)

    def where_of(s):
        """The locality line, from whichever fields the sources gave:
        บ้าน · อ. · the park — never a guessed address."""
        bits = []
        if s.get("village_th"):
            bits.append(s["village_th"])
        if s.get("amphoe_th"):
            a = s["amphoe_th"]
            bits.append(a if a.startswith(("อ.", "อำเภอ", "เมือง")) else f"อ.{a}")
        if s.get("park_th"):
            bits.append(s["park_th"])
        return " · ".join(bits)

    def out_link(s):
        """The register-only row's receipt: where this pin comes from."""
        for src in s.get("sources") or []:
            if src.get("type") == "osm" and src.get("ref"):
                return (f'<a href="https://www.openstreetmap.org/{att(src["ref"])}" '
                        f'rel="noopener nofollow">OSM</a>')
            if src.get("ref", "").startswith("http"):
                host = re.sub(r"^https?://(www\.)?", "", src["ref"]).split("/")[0]
                return (f'<a href="{att(src["ref"])}" rel="noopener nofollow">'
                        f'{esc(host)}</a>')
        return ""

    # ---- the register table: springs with curated stated-facts -----------
    def cell(v):
        if not v or v == "unstated":
            return f'<td class="un">{bi("ไม่ระบุ", "unstated")}</td>'
        if isinstance(v, dict):
            return f'<td>{bi(v.get("th", ""), v.get("en", ""))}</td>'
        return f"<td>{esc(str(v))}</td>"

    curated = [s for s in springs if s.get("curated")]
    reg_html = ""
    if curated:
        head = "".join(f"<th>{bi(th, en)}</th>" for th, en in [
            ("จังหวัด", "province"), ("อุณหภูมิ", "temp"),
            ("ค่าเข้าที่ประกาศ", "posted entry"), ("แช่", "soak"),
            ("ต้มไข่", "eggs"), ("เวลา", "hours")])
        rows = []
        for s in curated:
            pmeta = provinces.get(s["province"], {})
            dist = f'<small>{esc(where_of(s))}</small>'
            temp = s.get("tempC")
            if temp:
                who = f' <small>({esc(s.get("temp_by", ""))})</small>' if s.get("temp_by") else ""
                temp_cell = f"<td>{esc(str(temp))} °C{who}</td>"
            else:
                temp_cell = f'<td class="un">{bi("ไม่ระบุ", "unstated")}</td>'
            rows.append(
                f'<tr><td class="venue">{link_of(s)}{dist}</td>'
                f'<td>{esc(pmeta.get("th", ""))}</td>'
                + temp_cell
                + cell(s.get("fee_posted"))
                + cell(s.get("soak"))
                + cell(s.get("eggs"))
                + cell(s.get("hours_posted") or s.get("hours"))
                + "</tr>")
        reg_html = (
            f'<table class="hs-reg"><thead><tr><th>{bi("บ่อ", "Spring")}</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<p class="hs-legend">'
            + bi("ทุกช่องคือคำของผู้ดูแลบ่อหรือหน่วยงานที่วัด พร้อมที่มาและวันที่อ่าน · “ไม่ระบุ” = หน้าที่อ่านไม่ได้พูดถึง — ไม่ใช่ “ไม่มี” · ราคาคือที่ประกาศ ยังไม่มีใครเทียบป้ายหน้าบ่อ · อุณหภูมิคือของบ่อต้นทาง ไม่ใช่ของอ่างแช่",
                 "every cell is the operator's or the measuring agency's own words, with source and date read · “unstated” = the pages read did not say — not a no · prices are as posted; nobody has yet checked a board at a gate · a temperature belongs to the source pool, not the soaking tubs")
            + "</p>")

    # ---- province groups --------------------------------------------------
    prov_html = []
    for key, meta in provinces.items():
        mine = [s for s in springs if s["province"] == key]
        if not mine:
            continue
        rows = []
        for s in mine:
            bits = [link_of(s)]
            w = where_of(s)
            if w:
                bits.append(f"<small>{esc(w)}</small>")
            extra = []
            if s.get("tempC"):
                who = s.get("temp_by")
                extra.append(f'{esc(str(s["tempC"]))} °C'
                             + (f' <small>({esc(who)})</small>' if who else ""))
            if s.get("phone"):
                extra.append("☎")
            src = out_link(s) if not s.get("recordId") else ""
            if src:
                extra.append(src)
            if extra:
                bits.append('<span class="src">' + " · ".join(extra) + "</span>")
            rows.append('<li class="hs-row">' + " ".join(bits) + "</li>")
        prov_html.append(
            f'<h3>{bi(meta["th"], meta["en"])} '
            f'<span class="count">({len(mine)})</span></h3>'
            f'<ul class="dir">{"".join(rows)}</ul>')
    prov_html = f'<div class="hs-prov">{"".join(prov_html)}</div>'

    # ---- primer ----------------------------------------------------------
    P = []

    def card(h_th, h_en, *paras):
        body = "".join(f"<p>{p}</p>" if not str(p).startswith("<") else str(p)
                       for p in paras)
        P.append(f'<div class="hs-card"><h3>{bi(h_th, h_en)}</h3>{body}</div>')

    def say(th, en):
        return '<span class="say">' + bi(th, en) + "</span>"

    card("โป่ง — คำในครึ่งหนึ่งของชื่อ", "Pong — in half the names",
         bi("โป่ง (pòong) คือแอ่งแร่ธาตุที่ซึมขึ้นจากดิน — โป่งดิน โป่งเกลือ ที่สัตว์ป่ามากิน — และที่ที่น้ำร้อนผุดขึ้น คนเหนือก็เรียกโป่งเหมือนกัน: โป่งเดือด โป่งน้ำร้อน โป่งอาง ชื่อหมู่บ้านนับร้อยในภาคเหนือขึ้นต้นด้วยโป่ง เพราะหมู่บ้านตั้งใกล้โป่ง — หมู่บ้านชื่อโป่งจึงไม่ใช่บ่อน้ำร้อนเสมอไป และทะเบียนหน้านี้แยกสองอย่างนั้นออกจากกันตั้งแต่ตัวกรอง",
            "A โป่ง pòong is a mineral seep — the salt licks the wild animals visit — and where the seep runs hot, the northern word is the same: Pong Duet the boiling pong, Pong Nam Ron the hot-water pong, Pong Ang. Hundreds of northern villages begin with the word because the village stood near one, which is why a village called Pong is not always a spring — and why this page's filter keeps the two apart."),
         say("น้ำพุร้อน (nám-phú-rɔ́ɔn) คือคำกลาง: น้ำ + พุ (ผุดขึ้น) + ร้อน · บ่อน้ำร้อน (bɔ̀ɔ) คือบ่อ · ธารน้ำร้อน คือลำธาร", "น้ำพุร้อน nám-phú-rɔ́ɔn is the standard compound — water + well-up + hot; บ่อน้ำร้อน bɔ̀ɔ nám rɔ́ɔn is the pool form; ธารน้ำร้อน a hot stream"))
    card("ไข่ในตะกร้า", "The egg basket",
         bi("ที่บ่อพัฒนาแล้ว — สันกำแพง แจ้ซ้อน แม่ขะจาน — ของที่ขายหน้าบ่อคือไข่ในตะกร้าสาน หย่อนลงบ่อต้นทางที่ร้อนที่สุด นาทีที่ต้มเป็นของป้ายหน้าบ่อ (บ่อไหนกี่นาที บ่อนั้นบอกเอง) ไข่ออนเซ็นแบบไข่แดงเซตก่อนไข่ขาวคือฟิสิกส์ของน้ำ 70 องศา — และบ่อที่ต้มไข่ได้คือบ่อที่ห้ามแช่",
            "At the developed springs — San Kamphaeng, Chae Son, Mae Khachan — the thing sold at the water's edge is eggs in a woven basket, lowered into the hottest source pool. How many minutes is the sign's own business, posted pool by pool; the onsen egg with its set yolk and soft white is the physics of seventy-degree water — and the pool that cooks an egg is the pool nobody soaks in."),
         say("ต้มไข่ (tôm khài) — ต้ม ต้ม + ไข่ ไข่ · ไข่ออนเซ็น มาจากญี่ปุ่น 温泉たまご", "tôm khài — to boil + egg · khài onsen rides the Japanese loan, 温泉たまご"))
    card("ประตูอุทยาน — ค่าเข้าซ้อนค่าเข้า", "The park gate — a fee inside a fee",
         bi("บ่อหลายแห่ง — โป่งเดือด เทพพนม แจ้ซ้อน ฝาง — อยู่ในอุทยานแห่งชาติ: ค่าเข้าอุทยาน (คนไทย/ต่างชาติ คนละอัตรา ตามที่กรมอุทยานฯ ประกาศ) มาก่อนถึงบ่อ และบางบ่อมีค่าอ่างส่วนตัวเพิ่มอีกชั้น — ทุกตัวเลขในทะเบียนคือ “ตามที่ประกาศ” พร้อมวันที่อ่าน ใครยืนหน้าประตูมาแล้วเลขไม่ตรง บอกมดได้",
            "Several springs — Pong Duet, Thep Phanom, Chae Son, Fang — sit inside national parks: the park's own gate fee (Thai and foreign rates, as the department posts them) comes before the spring, and a private tub is often a second posted price inside the first. Every figure in the register is as-posted with the date it was read; if you stood at a gate and the number differed, tell the ants."),
         say("น้ำพุร้อนสันกำแพงดำเนินงานโดย ททท. ร่วมกับสหกรณ์การเกษตรหมู่บ้านสหกรณ์สันกำแพง (อบต.บ้านสหกรณ์เล่าไว้เอง) · กรมอุทยานฯ ดูแลบ่อในเขตอุทยาน · อบต. และหมู่บ้านดูแลบ่อชุมชน — ผู้ดูแลคือผู้ประกาศราคา", "San Kamphaeng runs as a TAT–village-cooperative venture (the sub-district office tells the story itself); the parks department keeps the in-park pools; sub-district offices and villages keep the community ones — whoever keeps the spring is whoever posts its prices"))
    card("น้ำร้อนจริง — ป้ายของแต่ละบ่อ", "Genuinely hot — each spring's own sign",
         bi("บ่อต้นทางหลายแห่งร้อนเกิน 90 องศา — น้ำที่ต้มไข่สุกได้ ต้มคนได้เท่ากัน กติกาที่ป้ายหน้าบ่อพูดตรงกันทุกที่: แช่ในอ่างที่จัดไว้ ไม่ใช่บ่อต้นทาง อ่านอุณหภูมิของอ่างก่อนลง และเด็กกับผู้สูงอายุแช่สั้นกว่า — ตัวเลขนาทีเป็นของป้ายแต่ละบ่อ ไม่ใช่ของเว็บนี้",
            "Several source pools run past ninety degrees — water that cooks an egg cooks a person the same way. The rule every gate's sign states in its own words: soak in the built tubs, not the source pool; read the tub's own temperature before you get in; children and elders soak shorter. The minutes belong to each spring's sign, not to this site."),
         say("สิ่งที่น้ำแร่ “ดีต่อ” อะไร เป็นคำของผู้ดูแลบ่อและของประเพณี — หน้านี้จดคำนั้นเป็นคำพูด ไม่ใช่คำแนะนำ", "what the mineral water is said to be good for is the operator's and the tradition's claim — this page records the claim as a claim, and gives no advice"))
    card("ออนเซ็นในเมือง", "The onsen in town",
         bi("ร้านออนเซ็นและสปาน้ำแร่ในเมือง เป็นธุรกิจอาบน้ำ อยู่บนชั้นของมันเอง (นวด-สปา) ไม่ได้อยู่ในทะเบียนบ่อ — บางร้านบอกว่าใช้น้ำแร่จากบ่อจริง คำนั้นเป็นของร้าน หน้านี้ชี้ทางไปหาบ่อที่พื้นดินทำเอง",
            "The onsen houses and mineral spas in town are bathing businesses and live on their own shelf (massage & spa), not in this register — some state they truck water from a real spring, and that statement is theirs. This page points at the springs the ground made."),
         say("ออนเซ็น ← ญี่ปุ่น 温泉 on-sen “บ่อน้ำร้อน” — คำยืมที่วนกลับมาแปลตัวเอง", "onsen ← Japanese 温泉, hot spring — a loanword that circles back to translate itself"))
    card("คำที่จะได้เจอ", "Words you will meet",
         '<ul class="hs-words">'
         + "".join(f"<li>{bi(th, en)}</li>" for th, en in [
             ("น้ำพุร้อน (nám-phú-rɔ́ɔn) — บ่อน้ำร้อนธรรมชาติ", "nam phu ron (น้ำพุร้อน) — a hot spring"),
             ("โป่ง (pòong) — แอ่งแร่ที่ซึมจากดิน", "pong (โป่ง) — a mineral seep; the northern spring word"),
             ("บ่อ (bɔ̀ɔ) — บ่อ · อ่าง (àang) — อ่างแช่", "bo (บ่อ) — a pool · ang (อ่าง) — a soaking tub"),
             ("แช่ (chɛ̂ɛ) — แช่น้ำ · แช่เท้า — เอาเท้าลงอย่างเดียว", "chae (แช่) — to soak · chae thao (แช่เท้า) — the free foot-soak channel"),
             ("ห้องแช่ส่วนตัว — อ่างในห้องปิด คิดราคาต่อห้องหรือต่อคน", "hong chae suan tua (ห้องแช่ส่วนตัว) — a private tub room, priced per room or per head"),
             ("ต้มไข่ (tôm khài) — หย่อนตะกร้าไข่ลงบ่อต้นทาง", "tom khai (ต้มไข่) — boiling the egg basket in the source pool"),
             ("น้ำแร่ (nám-rɛ̂ɛ) — น้ำแร่ · กำมะถัน (kam-má-thǎn) — กลิ่นไข่ต้มของบ่อ", "nam rae (น้ำแร่) — mineral water · kammathan (กำมะถัน) — sulfur, the boiled-egg smell"),
             ("บ่อน้ำอุ่น — อุ่นพอแช่ ไม่ร้อนพอต้ม", "bo nam un (บ่อน้ำอุ่น) — a warm pool, soakable, nothing to cook with"),
             ("ทางลาด/ราวจับ — บ่อพัฒนาบางแห่งประกาศไว้ ถามก่อนไปได้", "ramps and rails — some developed springs post access facts; asking ahead is fair"),
         ]) + "</ul>",
         say("รากศัพท์ต่อได้ที่ wichaa.net/thairoots — น้ำ พุ ร้อน โป่ง ล้วนเป็นคำไทแท้สายเดียวกับลาวและไทใหญ่", "follow the roots at wichaa.net/thairoots — น้ำ, พุ, ร้อน and โป่ง are all Tai-stock words, shared down the Lao and Shan lines"))
    primer_html = f'<div class="hs-grid">{"".join(P)}</div>'

    # ---- assemble --------------------------------------------------------
    n_home = sum(1 for s in springs if s["province"] in ("cm", "cr"))
    n_far = len(springs) - n_home
    n_prov = len(provinces)
    intro = bi(
        f"หน้านี้คือทะเบียนน้ำพุร้อนทั้งภาคเหนือ — {len(springs)} บ่อ ใน {n_prov} จังหวัด: เชียงใหม่กับเชียงรายอยู่ในสารบัญเต็ม ({n_home} บ่อ กดเข้าหน้าของแต่ละบ่อได้) ที่เหลืออีก {n_far} บ่อจดพิกัดและที่มาไว้ให้วางแผนเที่ยว — บ่อไหนบอกอะไรเอง (อุณหภูมิ ค่าเข้า เวลา ไข่) อยู่ในตารางพร้อมที่มา",
        f"The register of hot springs across the whole of northern Thailand — {len(springs)} springs in {n_prov} provinces: Chiang Mai and Chiang Rai are in the full directory ({n_home} springs with their own pages), the other {n_far} carry their pins and sources for planning. What each spring states for itself — temperature, fees, hours, eggs — is in the table with its source.")

    # A province whose fetch lost selectors is short, not done — the register
    # says which, and the page repeats it rather than letting an absence read
    # as an answer.
    short_provs = reg.get("incomplete_provinces") or {}
    short_html = ""
    if short_provs:
        th_names = ", ".join(provinces.get(k, {}).get("th", k) for k in short_provs)
        en_names = ", ".join(provinces.get(k, {}).get("en", k) for k in short_provs)
        short_html = ('<p class="hs-note">'
                      + bi("ถามไม่ครบ: " + th_names
                           + " — บางคำถามยังไม่ได้คำตอบจากแผนที่เปิด",
                           "Asked short: " + en_names
                           + " — some map questions went unanswered")
                      + "</p>")

    map_html = _map_svg(springs, provinces, bi_text, esc)
    credit = ('<p class="hs-credit">'
              + bi("หมุดจาก OpenStreetMap (© ผู้ร่วมแก้ไข OpenStreetMap, ODbL) และบัญชีเปิดของราชการ — กรมอุทยานฯ และจังหวัดแม่ฮ่องสอน (Open Data Common) · เส้นเขตจังหวัดและถนนสายหลักจาก Natural Earth (สาธารณสมบัติ) แม่น้ำจาก OpenStreetMap",
                   "Pins from OpenStreetMap (© OpenStreetMap contributors, ODbL) and official open lists — the national-parks department and Mae Hong Son province (Open Data Common) · province lines and main roads from Natural Earth (public domain), rivers from OpenStreetMap")
              + "</p>")

    ld = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "น้ำพุร้อนภาคเหนือ — Hot springs of northern Thailand: what each states",
        "url": BASE + "namphuron.html",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "BodyOfWater",
                      "name": s.get("name") or s.get("nameEn"),
                      **({"geo": {"@type": "GeoCoordinates",
                                  "latitude": s["lat"], "longitude": s["lng"]}}
                         if s.get("lat") else {}),
                      **({"url": BASE + href(by_id[s["recordId"]])}
                         if s.get("recordId") in by_id else {})}}
            for i, s in enumerate(springs)],
    }
    head = ('<link rel="stylesheet" href="namphuron.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = shelf_og("cm", "sights", "hot-spring") if shelf_og else None

    unv = reg.get("unverified") or []
    unv_html = ""
    if unv:
        items = "".join(
            f'<li><b>{esc(u.get("name", ""))}</b> — {bi(u.get("note_th", ""), u.get("note_en", ""))}</li>'
            for u in unv)
        unv_html = (f'<h3>{bi("ที่เล่ากันแต่ยังอ่านที่มาไม่ได้", "Told of, not yet read")}</h3>'
                    f'<p class="hs-note">'
                    + bi("ชื่อที่มีคนเล่าแต่ยังไม่เจอหน้าทางการหรือหมุดที่ยืนยันได้ — จดไว้ตรงนี้ตามตรง ไม่ลงทะเบียน ใครมีที่มา บอกมดได้",
                         "Names people tell of, with no official page or confirmable pin yet read — held here plainly, off the register; if you hold a source, tell the ants")
                    + f"</p><ul class=\"hs-note\">{items}</ul>")

    body = (
        f'<h1>♨️ {bi("น้ำพุร้อน — ทั้งภาคเหนือ", "Hot springs — the whole north")}</h1>'
        f'<p class="hs-intro">{intro}</p>'
        f'<h2>{bi("แผนที่", "The map")}</h2>'
        f"{map_html}{credit}"
        f'<h2>{bi("ทะเบียน — บ่อไหนบอกว่าอะไร", "The register — what each spring states")}</h2>'
        f"{reg_html}"
        f'<h2>{bi("ทุกบ่อ เรียงตามจังหวัด", "Every spring, by province")}</h2>'
        # Python 3.9: an apostrophe inside a bi() nested in an f'…' string is a
        # SyntaxError — concatenated instead, the same lift as the block above.
        + '<p class="hs-note">'
        + bi("เชียงใหม่และเชียงรายกดเข้าหน้าบ่อได้ · จังหวัดอื่นจดพิกัดกับที่มาไว้ · ☎ = สารบัญมีเบอร์",
             "Chiang Mai and Chiang Rai rows open the spring's own page · other provinces carry pin and source · ☎ = the directory holds a number")
        + '</p>'
        + short_html
        + f"{prov_html}{unv_html}"
        f'<h2>{bi("ก่อนแช่", "Before you soak")}</h2>'
        f"{primer_html}"
        f'<p class="hs-note">{bi("ที่มาของทะเบียน", "Register data")}: <a href="data/hotsprings.json">data/hotsprings.json</a> · '
        + bi("บ่อที่ยังไม่มีในทะเบียน หรือเลขที่ไม่ตรงป้าย — ", "A spring not in the register, or a number that no longer matches the sign — ")
        + f'<a href="suggest.html">{bi("บอกมด", "tell the ants")}</a></p>'
        + share_block(BASE + "namphuron.html", "น้ำพุร้อนทั้งภาคเหนือ · มดแดง", card=og))
    (DOCS / "namphuron.html").write_text(page(
        "น้ำพุร้อนภาคเหนือ — ทะเบียนทุกบ่อ ทุกจังหวัด · Hot springs of northern Thailand",
        body, depth=0, path="namphuron.html",
        desc="ทะเบียนน้ำพุร้อนทั้งภาคเหนือ: เชียงใหม่ เชียงราย แม่ฮ่องสอน ลำปาง และทุกจังหวัด — แผนที่ อุณหภูมิตามผู้วัด ค่าเข้าตามประกาศ บ่อแช่ บ่อต้มไข่ พร้อมที่มาทุกช่อง · Every hot spring in northern Thailand: the map, temperatures as measured, fees as posted, soaking and egg pools, sources on every cell",
        extra_head=head, og=og,
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("น้ำพุร้อน", "Hot springs")}'))
    return {"page": 1, "springs": len(springs), "provinces": n_prov,
            "records": n_home, "register_only": n_far,
            "stated": len(curated)}
