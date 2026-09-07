#!/usr/bin/env python3
"""ไม้แกะสลักบ้านถวาย — the carving village, south of the city (/tawai.html). WO-51.

WHY THIS PAGE EXISTS. Fifteen kilometres down Route 108 there is a village
where, on the operators' own count given to the Prime Minister in June 2024,
about five hundred shops were still trading — down from about a thousand
before COVID. This directory holds ONE record that says บ้านถวาย, and it is
filed as a wet market. That is not a hole in the crawl so much as a hole in
what any crawl can see: OSM has no tag for a village that carves, the shops
are named for their owners, and the province's own 2567 figure for Hang Dong
— 148 souvenir and OTOP outlets — is a district count with no pins under it.

So this is not a shelf. It is the five things a reader on that road actually
needs, and none of them is a list of addresses:

  1. WHICH LINK OF THE CHAIN YOU ARE STANDING IN. Carving is not one trade.
     The block is cut by one pair of hands, the line work is done by another
     (and did not come from the carving shop at all — a women's group learned
     the patterns at the cultural centre and married them to the wood), the
     lacquer and gold is a third, and the shopfront is a fourth. The price
     moves most at the fourth, and that is documented rather than implied:
     in 2549 a carved dragon was 800 baht in a village shop on the canal and
     3,000 at a frontage shop, and the room a shop stood in cost 1,000 or
     10,000 a month depending on who you were.
  2. WHICH WOOD. Teak, rain tree, mango, santol, hog plum — and the two that
     change what you may carry home, rosewood and agarwood. The species is
     the question, and the receipt is where the answer has to land.
  3. WHEN THE FAIR IS, WHICH IS NOT WHEN IT WAS. The fair runs on the FISCAL
     year: it sat on 29 Jan–4 Feb for fifteen years, was moved to the turn of
     the year in 2548 to suit the Night Safari's opening, and in 2568 it
     happened TWICE inside one calendar year — the 34th in January and the
     35th in December. Any page that prints "every January" is wrong.
  4. THAT A CARVED BUDDHA IS A DIFFERENT OBJECT IN LAW from a carved
     elephant. Buddha and sacred images fall under the Antiquities Act
     B.E. 2504 (amended 2535), not under the wood rules and not under
     CITES — form ศก.6, the Fine Arts Department's National Museums office,
     a fee per piece, two colour photographs, and PROOF YOU OWN IT, which is
     what makes the receipt worth asking for at the till. The souvenir page
     cannot carry this: its handicraft row says the law leaves handicraft
     wide open, and that is true of the elephant and false of the Buddha.
  5. THAT THE ROAD IS THE POINT. Muang Kung's pots and Wat Ton Kwen's
     carpentry are on the same 15 km, and the directory holds ZERO records
     for Muang Kung under its own name. Measured here, not assumed.

MEASURED, NEVER AWARDED (the /views rule). Every count on this page is taken
live from the directory at build time: what stands within 2.5 km of the
village pin, what the craft shelves hold, and the steak trap below. Nothing
here ranks a shop, and no shop is recommended. Importance reads off a
register — the OTOP designation with the ministry that granted it, the SACIT
master craftsman with his year — exactly the WO-10 rule.

THE STEAK TRAP, and it is a house-style warning worth the line: a bare
case-insensitive `teak` matches **steak**, and on this corpus that is not a
near miss — it is nearly the whole result set. Forty-odd steakhouses answer
to a search for teak furniture. Same family as `(?<!ห)วัด` (จังหวัด ends in
วัด) and `\\bse-ed\\b` (which filed a coffee roaster as a bookshop). The count
is printed on the page rather than fixed silently, because the reader typing
"teak" into any search box anywhere has the same problem.

DRAWN, NOT DESCRIBED. Three instruments, all inline SVG, no script and no
basemap: what the directory holds on the ground around the village; the chain
of hands with the place the price moves marked on it; and the timeline on
true year scale from the drought to the two fairs of 2568.

THE SIBLING PAGE. Carry-flags, the four legal tiers and the CITES sources
live on /souvenir.html and are NOT restated here — this page adds only which
woods are worked in this village and what to ask at the till.

Entry point: emit(globals_of_build, data) — hooked in build.py beside the
hom layer. Emits tawai.html + tawai.css.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# How far out to count. 2.5 km is the village plus its approach road and the
# canal, and it is deliberately generous: a tighter ring would make the
# emptiness look like a cropping choice rather than a finding.
NEAR_KM = 2.5

# What the corpus would have to SAY for this trade to be visible to a crawl.
# The Thai terms are compounds on purpose (WO-10's rule): bare แกะ is an
# ordinary verb, bare ไม้ is wood, and neither is a claim about a shop.
CARVE_RX = re.compile(r"แกะสลัก|ไม้แกะ|หัตถกรรม|woodcarv|wood carv|handicraft", re.I)
# The trap, kept as its own expression so the page can print both numbers.
TEAK_RX = re.compile(r"teak", re.I)
STEAK_RX = re.compile(r"steak|สเต็ก|สเต๊ก|สเต็ค|สเต๊ค", re.I)
# The shelves a carving shop would land on if the crawl ever caught one.
CRAFT_SUBS = ("crafts", "gallery", "gallery-commercial", "antiques")

CARRY_INK = {
    "ok":     ("#3d6b4a", "#e8f1e6", "พาไปได้", "travels"),
    "ask":    ("#80621c", "#f6efdc", "ต้องถาม", "ask first"),
    "papers": ("#7a4a1c", "#f3e8dc", "ต้องมีเอกสาร", "papers"),
    "no":     ("#8f3b2c", "#f6e3de", "ไม่ได้", "no"),
}


def _km(lat1, lng1, lat2, lng2):
    x = (lat2 - lat1) * 111.320
    y = (lng2 - lng1) * 111.320 * math.cos(math.radians(lat1))
    return math.hypot(x, y)


# ───────────────────────────────────────────────────── FIGURE 1 · the ground

def _ground_svg(reg, near, esc, bi_text):
    """Everything the directory holds within 2.5 km of the village pin.

    Drawn from real coordinates only. No boundary, no road line, no shading —
    the directory holds none of those for this ground, and a drawn approach
    road would be a claim the data cannot carry. What the picture is FOR is
    the shape of the absence: a village of carvers with a ring of cafes,
    schools and health stations around it and not one carving shop in it.
    """
    v = reg["village"]
    lat0, lng0 = v["lat"], v["lng"]
    W, H = 720, 400
    pad = 46
    kx = 111.320 * math.cos(math.radians(lat0))
    # metres per pixel chosen so the 2.5 km ring fits with room for labels
    span = NEAR_KM * 2.15
    sc = min((W - 2 * pad), (H - 2 * pad)) / span

    def xy(la, ln):
        return (W / 2 + (ln - lng0) * kx * sc,
                H / 2 - (la - lat0) * 111.320 * sc)

    o = ['<svg viewBox="0 0 %d %d" role="img" xmlns="http://www.w3.org/2000/svg" '
         'aria-label="%s">' % (W, H, esc(bi_text(
             "แผนภาพสิ่งที่สารบัญมีในรัศมี 2.5 กิโลเมตรรอบหมุดบ้านถวาย "
             "หมุดทองคือหมู่บ้าน วงเล็กคือร้านและสถานที่อื่นทั้งหมด",
             "A plot of everything this directory holds within 2.5 km of the Ban "
             "Tawai pin. The gold pin is the village; every small ring is some "
             "other kind of place.")))]
    # the rings, at 1 and 2 km
    cx, cy = W / 2, H / 2
    # Labels go at twelve o'clock, not at three. On the right of the ring they
    # landed on top of the village pin's own label, which is the one word on
    # the drawing that has to be readable.
    for km, lab in ((1, "1 กม. · 1 km"), (2, "2 กม. · 2 km")):
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" class="cv-ring"/>'
                 % (cx, cy, km * sc))
        o.append('<text x="%.1f" y="%.1f" class="cv-ringlab" '
                 'text-anchor="middle">%s</text>'
                 % (cx, cy - km * sc - 5, esc(lab)))
    for d in near:
        x, y = xy(d["lat"], d["lng"])
        cls = "cv-dot"
        if d["craft"]:
            cls += " craft"
        o.append('<circle cx="%.1f" cy="%.1f" r="4.2" class="%s"><title>%s</title></circle>'
                 % (x, y, cls, esc(d["name"] + " — " + d["shelf"])))
    x, y = xy(lat0, lng0)
    o.append('<circle cx="%.1f" cy="%.1f" r="9" class="cv-pin"><title>%s</title></circle>'
             % (x, y, esc(bi_text("บ้านถวาย — หมุดเดียวที่มีชื่อหมู่บ้าน",
                                  "Ban Tawai — the one pin carrying the name"))))
    o.append('<text x="%.1f" y="%.1f" class="cv-pinlab">%s</text>'
             % (x + 14, y + 4, esc("บ้านถวาย · Ban Tawai")))
    o.append('<text x="%d" y="%d" class="cv-ringlab">%s</text>'
             % (pad - 30, H - 12, esc(bi_text(
                 "วาดจากพิกัดจริงเท่านั้น ไม่มีเส้นถนนเพราะสารบัญไม่มีให้วาด",
                 "Real coordinates only. No road line: the directory holds none to draw."))))
    o.append("</svg>")
    return "".join(o)


# ────────────────────────────────────────────────── FIGURE 2 · chain of hands

def _chain_svg(reg, esc, bi_text):
    """The trades, in the order the wood meets them, with the place the price
    moves marked. Six boxes and five arrows: the point is that they are
    SEPARATE people, which is the fact a shopper needs and the fact a village
    -as-one-craftsman story hides."""
    hands = reg["hands"]
    W = 760
    bw, bh, gap = 112, 84, 16
    H = 190
    x0 = (W - (len(hands) * bw + (len(hands) - 1) * gap)) / 2
    o = ['<svg viewBox="0 0 %d %d" role="img" xmlns="http://www.w3.org/2000/svg" '
         'aria-label="%s">' % (W, H, esc(bi_text(
             "แผนภาพลำดับมือที่ไม้ผ่าน: สล่า แกะสลัก เดินเส้น ลงรักปิดทอง ทำเก่า และหน้าร้าน",
             "A diagram of the hands the wood passes through: the carver, the "
             "cutting, the line work, the lacquer and gold, the ageing, and the "
             "shopfront.")))]
    for i, h in enumerate(hands):
        x = x0 + i * (bw + gap)
        cls = "cv-box" + (" last" if i == len(hands) - 1 else "")
        o.append('<rect x="%.1f" y="40" width="%d" height="%d" rx="11" class="%s"/>'
                 % (x, bw, bh, cls))
        o.append('<text x="%.1f" y="66" class="cv-boxth" text-anchor="middle">%s</text>'
                 % (x + bw / 2, esc(h["th"].split(" · ")[0])))
        # the English gloss wraps to two lines at the space nearest the middle
        g = h["en"]
        parts = g.split(" ")
        mid = len(g) // 2
        best, run = 0, 0
        for j, p in enumerate(parts[:-1]):
            run += len(p) + 1
            if abs(run - mid) < abs(best - mid):
                best, cut = run, j + 1
        l1 = " ".join(parts[:cut]) if len(parts) > 1 else g
        l2 = " ".join(parts[cut:]) if len(parts) > 1 else ""
        o.append('<text x="%.1f" y="86" class="cv-boxen" text-anchor="middle">%s</text>'
                 % (x + bw / 2, esc(l1)))
        if l2:
            o.append('<text x="%.1f" y="100" class="cv-boxen" text-anchor="middle">%s</text>'
                     % (x + bw / 2, esc(l2)))
        o.append('<text x="%.1f" y="118" class="cv-boxrt" text-anchor="middle">%s</text>'
                 % (x + bw / 2, esc(h["rtgs"].split(" · ")[0])))
        if i:
            # inside the gutter only. An earlier version started the line
            # twelve pixels inside the previous box and drew the arrow across
            # its own label.
            o.append('<path d="M%.1f 82 L%.1f 82" class="cv-arrow" '
                     'marker-end="url(#cvhead)"/>' % (x - gap + 2, x - 4))
    o.append('<defs><marker id="cvhead" viewBox="0 0 10 10" refX="8" refY="5" '
             'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
             '<path d="M0 0 L10 5 L0 10 z" class="cv-arrowhead"/></marker></defs>')
    lx = x0 + (len(hands) - 1) * (bw + gap) + bw / 2
    o.append('<text x="%.1f" y="150" class="cv-note" text-anchor="middle">%s</text>'
             % (lx, esc("ราคาขยับมากที่สุดตรงนี้")))
    o.append('<text x="%.1f" y="166" class="cv-note" text-anchor="middle">%s</text>'
             % (lx, esc("the price moves most here")))
    o.append("</svg>")
    return "".join(o)


# ─────────────────────────────────────────────────── FIGURE 3 · the timeline

def _timeline_svg(reg, esc, bi_text):
    """True year scale, not evenly spaced. The forty years between the three
    men coming home and the village being named a national model are most of
    the story, and evenly spaced dots would hide exactly that."""
    ev = sorted(reg["timeline"], key=lambda e: e["sort"])
    y0, y1 = ev[0]["sort"] - 3, 2027
    W = 760
    left, right = 60, W - 24
    def px(y):
        return left + (y - y0) / (y1 - y0) * (right - left)
    o = []
    o.append('<line x1="%d" y1="46" x2="%d" y2="46" class="cv-spine"/>' % (left, right))
    for y in range(1960, 2030, 10):
        x = px(y)
        o.append('<line x1="%.1f" y1="40" x2="%.1f" y2="52" class="cv-tick"/>' % (x, x))
        o.append('<text x="%.1f" y="32" class="cv-year" text-anchor="middle">%d</text>'
                 % (x, y))
    # Labels are packed into rows greedily, left to right, so that no two in
    # the same row can overlap. The first version anchored every label at its
    # own dot and stepped down one row each time, which is fine while the
    # events are spread and unreadable the moment they cluster — and this
    # timeline clusters hard after 2019, which is the thing it exists to show.
    placed = []          # (row, right edge x)
    CH, ROW_H, TOP = 6.2, 21, 76
    for e in ev:
        x = px(e["sort"])
        big = e["sort"] in (2004, 2024)
        o.append('<circle cx="%.1f" cy="46" r="%s" class="cv-evdot%s"/>'
                 % (x, "6" if big else "4", " big" if big else ""))
        label = str(e["ce"]) + " · พ.ศ. " + str(e["year"])
        w = len(label) * CH + 8
        # anchor at the dot, but never let the label run off the right edge
        lx = min(x + 5, right - w)
        row = 0
        while any(r == row and lx < edge + 10 for r, edge in placed):
            row += 1
        placed.append((row, lx + w))
        ty = TOP + row * ROW_H
        o.append('<line x1="%.1f" y1="52" x2="%.1f" y2="%.1f" class="cv-leader"/>'
                 % (x, x, ty - 9))
        o.append('<text x="%.1f" y="%.1f" class="cv-ev">%s</text>'
                 % (lx, ty, esc(label)))
    # The canvas is sized to the rows the packer actually used, so adding an
    # event never leaves a band of empty card under the drawing (or, worse,
    # pushes a label out of the frame).
    H = TOP + (max(r for r, _ in placed) + 1) * ROW_H + 12
    return ('<svg viewBox="0 0 %d %d" role="img" xmlns="http://www.w3.org/2000/svg" '
            'aria-label="%s">' % (W, H, esc(bi_text(
                "เส้นเวลาบ้านถวาย วางตามมาตราส่วนปีจริง ตั้งแต่ปีฝนแล้ง 2500 "
                "ถึงงานประจำปีสองครั้งใน 2568",
                "A Ban Tawai timeline drawn to true year scale, from the drought of "
                "1957 to the two fairs of 2025."))) + "".join(o) + "</svg>")


CSS = """
.cv-wrap{max-width:56rem;margin:0 auto}
.cv-fig{margin:1.4rem 0;padding:1rem .7rem;background:var(--card);
  border:1px solid var(--warm-border);border-radius:14px;overflow-x:auto}
.cv-fig svg{display:block;width:100%;height:auto;min-width:560px}
.cv-figcap{font-size:.86rem;color:var(--mute);margin:.55rem .3rem 0;line-height:1.5}
.cv-ring{fill:none;stroke:var(--warm-border);stroke-width:1.1;stroke-dasharray:4 5}
.cv-ringlab{font-size:11px;fill:var(--mute)}
.cv-dot{fill:none;stroke:var(--mute);stroke-width:1.5;opacity:.8}
.cv-dot.craft{fill:#7a4a1c;stroke:#7a4a1c}
.cv-pin{fill:#8a6a1f;stroke:var(--card);stroke-width:2.5}
.cv-pinlab{font-size:13px;font-weight:700;fill:var(--ink)}
.cv-box{fill:var(--soft);stroke:var(--warm-border);stroke-width:1.2}
.cv-box.last{stroke:#7a4a1c;stroke-width:2}
.cv-boxth{font-size:14px;font-weight:700;fill:var(--ink)}
.cv-boxen{font-size:11px;fill:var(--ink)}
.cv-boxrt{font-size:10.5px;fill:var(--mute);font-style:italic}
.cv-arrow{fill:none;stroke:var(--mute);stroke-width:1.5;opacity:.7}
.cv-arrowhead{fill:var(--mute);opacity:.7}
.cv-note{font-size:11.5px;fill:#7a4a1c;font-weight:600}
.cv-spine{stroke:var(--warm-border);stroke-width:2}
.cv-tick{stroke:var(--warm-border);stroke-width:1}
.cv-year{font-size:11px;fill:var(--mute);font-weight:600}
.cv-ev{font-size:12px;fill:var(--ink)}
.cv-evdot{fill:#8a6a1f}
.cv-evdot.big{fill:#7a4a1c;stroke:var(--card);stroke-width:2}
.cv-leader{stroke:var(--warm-border);stroke-width:1}
.cv-count{background:var(--soft);border-radius:12px;padding:.85rem 1rem;margin:1.1rem 0;
  border:1px dashed var(--dashed)}
.cv-count b{font-size:1.5rem;line-height:1;color:var(--ant-dark)}
.cv-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));margin:1rem 0}
.cv-card{background:var(--card);border:1px solid var(--warm-border);border-radius:12px;padding:.8rem .9rem}
.cv-card h3{margin:.1rem 0 .45rem;font-size:1rem}
.cv-card p{margin:.3rem 0;font-size:.92rem;line-height:1.55}
.cv-tbl{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.92rem}
.cv-tbl th,.cv-tbl td{text-align:left;padding:.5rem .55rem;border-bottom:1px solid var(--warm-border);
  vertical-align:top}
.cv-tbl th{font-size:.8rem;letter-spacing:.04em;text-transform:uppercase;color:var(--mute)}
.cv-tbl .lat{font-style:italic;color:var(--mute);font-size:.86rem}
.cv-flag{display:inline-block;font-size:.76rem;font-weight:700;border-radius:999px;
  padding:.12rem .5rem;white-space:nowrap}
.cv-asks{list-style:none;padding:0;margin:1rem 0}
.cv-asks li{background:var(--card);border:1px solid var(--warm-border);border-left:5px solid #8a6a1f;
  border-radius:10px;padding:.7rem .9rem;margin:.5rem 0}
.cv-asks .why{display:block;font-size:.86rem;color:var(--mute);margin-top:.25rem}
.cv-road{list-style:none;padding:0;margin:1rem 0;display:grid;gap:.7rem}
.cv-road li{background:var(--card);border:1px solid var(--warm-border);border-radius:12px;
  padding:.75rem .9rem}
.cv-road .zero{color:#8f3b2c;font-weight:600;font-size:.86rem}
.cv-src{font-size:.82rem;color:var(--mute)}
.cv-src a{color:var(--mute)}
.cv-note-p{font-size:.88rem;color:var(--mute);border-top:1px solid var(--warm-border);
  margin-top:1.6rem;padding-top:.8rem;line-height:1.6}
.cv-hon{list-style:none;padding:0;margin:.8rem 0}
.cv-hon li{padding:.45rem 0;border-bottom:1px dotted var(--warm-border)}
.cv-hon .by{color:var(--mute);font-size:.88rem}
.cv-sheet{display:inline-block;padding:.45rem .8rem;border-radius:.7rem;
  border:1px solid var(--ant-dark);text-decoration:none;font-weight:600}
"""


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: "%s · %s" % (th, en))
    verdict, BROKEN = g["verdict"], g["BROKEN"]

    reg = json.loads((ROOT / "data" / "curated" / "carve.json").read_text())
    v = reg["village"]

    def out_a(url, label):
        """The WO-31 dead-ref rule: a source that has stopped answering keeps
        its place and its address and stops being a door."""
        url = (url or "").strip()
        if url and verdict(url).get("status") not in BROKEN:
            return '<a href="%s" rel="noopener">%s</a>' % (att(url), label)
        return '<span class="sv-dead" title="%s">%s</span>' % (att(url), label)

    def cite(key):
        """The bracketed source note after a claim.

        Trimming is done at a SPACE, not at a character count. Cutting Thai at
        an arbitrary index produced `[วิกิชุมชน … — บ้านถวาย (]` on the page: a
        dangling open bracket that reads as a rendering fault rather than as
        an abbreviation, and the site's own citation line was where it showed.
        """
        s = reg["sources"].get(key) or {}
        note = (s.get("note") or key).strip()
        if len(note) > 62:
            cut = note.rfind(" ", 0, 62)
            note = (note[:cut] if cut > 30 else note[:62]).rstrip(" ·—-([") + "…"
        return (' <span class="cv-src">'
                + out_a(s.get("ref"), "[" + esc(note) + "]") + "</span>")

    # ── the census, taken live at build time ───────────────────────────────
    # Three separate measurements, and they are separate on purpose:
    #   near      — what stands on the ground round the village pin
    #   craft     — how many of those sit on a shelf a carving shop would land on
    #   teak/steak— the regex trap, printed rather than quietly fixed
    # Is the shelves.json fix actually in the data, or only written down? The
    # entry lands at import, not at build, so a page that ASSERTS the fix can
    # be wrong for a whole build cycle. Measured instead, and the sentence
    # below says whichever is true today.
    TAWAI_ID = "cm-osm-node-2055923138"
    vrec = next((r for r in data.get("cm", []) if r.get("id") == TAWAI_ID), None)
    fix_landed = bool(vrec and "crafts" in (vrec.get("sub") or []))
    kept_market = bool(vrec and "market" in (vrec.get("cat") or []))

    near, n_craft, n_near_says = [], 0, 0
    n_teak = n_steak = n_teak_craft = 0
    n_carve_named = n_carve_here = 0
    muangkung = 0
    mk_rx = re.compile(r"เหมืองกุง|Muang Kung|Mueang Kung", re.I)
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            blob = " ".join(str(x) for x in
                            (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)
            if TEAK_RX.search(blob):
                n_teak += 1
                if STEAK_RX.search(blob):
                    n_steak += 1
                elif any(s in CRAFT_SUBS for s in (r.get("sub") or [])):
                    # the number that matters: how many teak hits are a wood
                    # shop at all. It has been zero every build so far, and
                    # the sentence below is written to correct itself.
                    n_teak_craft += 1
            if CARVE_RX.search(blob):
                # fruit carving is a cooking class, not this trade — the
                # cooking shelf already holds it and claiming it here would
                # be the จังหวัด/วัด mistake in another costume
                if "carving" not in (r.get("sub") or []):
                    n_carve_named += 1
            if mk_rx.search(blob):
                muangkung += 1
            if prov == "cm" and r.get("lat") and r.get("lng"):
                d = _km(v["lat"], v["lng"], r["lat"], r["lng"])
                # counted BEFORE the village pin is set aside, because the
                # sentence below turns on the village being the only one
                if d <= NEAR_KM and CARVE_RX.search(blob):
                    n_carve_here += 1
                if d <= NEAR_KM and r.get("id") != "cm-osm-node-2055923138":
                    craft = any(s in CRAFT_SUBS for s in (r.get("sub") or []))
                    n_craft += craft
                    if CARVE_RX.search(blob):
                        n_near_says += 1
                    near.append({"lat": float(r["lat"]), "lng": float(r["lng"]),
                                 "name": r.get("name") or "",
                                 "shelf": "/".join((r.get("cat") or [])[:1]
                                                   + (r.get("sub") or [])[:1]),
                                 "craft": craft})

    B = []
    B.append('<div class="cv-wrap">')
    B.append("<h1>" + bi("ไม้แกะสลักบ้านถวาย — หมู่บ้านที่แกะไม้ ใต้เมืองลงไป 15 กิโลเมตร",
                         "Ban Tawai — the carving village, fifteen kilometres south")
             + "</h1>")
    B.append("<p class=lead>" + bi(
        "หมู่บ้านที่คนทั้งหมู่บ้านทำงานไม้ อยู่ที่หมู่ 2 ตำบลขุนคง อำเภอหางดง "
        "หน้านี้ไม่ใช่รายชื่อร้าน — เป็นวิธีอ่านสายพานว่าใครทำอะไรตรงไหน "
        "ไม้อะไรพากลับบ้านได้ และงานประจำปีจัดเมื่อไหร่กันแน่ ซึ่งไม่ใช่เดือนเดิมทุกปี",
        "A village where the work is wood, at Moo 2 in Khun Khong, Hang Dong. This is "
        "not a list of shops. It is how to read the chain — who does which part, and "
        "where — which woods can come home with you, and when the fair actually is, "
        "which is not the same month every year.") + "</p>")

    # ── FIGURE 1 · the ground, and the finding ────────────────────────────
    B.append('<h2 id="ground">' + bi("สารบัญนี้มีอะไรอยู่ตรงนั้น",
                                     "What this directory holds there") + "</h2>")
    B.append('<div class="cv-fig">' + _ground_svg(reg, near, esc, bi_text) + "</div>")
    B.append('<p class="cv-figcap">' + bi(
        "แต่ละวงคือหนึ่งบันทึกในรัศมี 2.5 กิโลเมตรจากหมุดหมู่บ้าน หมุดทองคือหมู่บ้านเอง "
        "วาดจากพิกัดจริงล้วน ไม่มีเส้นถนนเพราะสารบัญไม่มีเส้นถนนตรงนั้นให้วาด",
        "Every ring is one record within 2.5 km of the village pin; the gold pin is the "
        "village itself. Drawn from real coordinates only — there is no road line "
        "because the directory holds none there to draw.") + "</p>")

    B.append('<div class="cv-count">')
    B.append("<p><b>%d</b> " % len(near) + bi(
        "บันทึกในรัศมี 2.5 กิโลเมตรรอบหมุดบ้านถวาย",
        "records within 2.5 km of the Ban Tawai pin") + "</p>")
    B.append("<p><b>%d</b> " % n_craft + bi(
        "ในจำนวนนั้นอยู่บนชั้นที่ร้านแกะไม้ควรจะอยู่ — และ <b>%d</b> รายการที่ชื่อของมันเอง "
        "บอกว่าแกะไม้" % n_near_says,
        "of them sit on a shelf a carving shop would land on — and <b>%d</b> whose own "
        "name says it carves." % n_near_says, raw=True) + "</p>")
    B.append("<p>" + bi(
        "และบันทึกเดียวที่มีคำว่า “บ้านถวาย” อยู่ในชื่อ ถูกครอว์ลเก็บมาเป็น “ตลาดสด” — "
        "OSM ให้ป้ายหลักได้ป้ายเดียว คนแท็กเห็นตลาดก็แท็กตลาด หน้านี้ไม่ได้แก้ข้อเท็จจริงของใคร "
        "แต่เพิ่มชั้นหัตถกรรมให้บันทึกนั้นผ่าน shelves.json แบบเดียวกับที่ Hub 53 "
        "ได้ชั้นโคเวิร์กกิ้งโดยไม่หลุดจากชั้นที่พัก",
        "And the one record whose name says บ้านถวาย was crawled as a fresh market. OSM "
        "allows a place one primary tag, so a mapper who saw a market tagged a market. "
        "Nothing here argues with that: the record GAINS a craft shelf through "
        "shelves.json, the same additive move that put Hub 53 on the coworking shelf "
        "without taking it off the guesthouse one.") + "</p>")
    B.append("<p>" + (bi(
        "ตอนนี้บันทึกนั้นอยู่ทั้งสองชั้นแล้ว — วัดสดตอนสร้างหน้า และชั้นตลาดกับ URL เดิมยังอยู่ครบ",
        "As of this build the record sits on both shelves — measured, not asserted — and "
        "the market shelf and its URL are still there.")
        if fix_landed and kept_market else bi(
        "รายการแก้เขียนไว้แล้วแต่ยังไม่เข้าสารบัญ ต้องรัน import_all อีกครั้งก่อน — "
        "หน้านี้วัดสดตอนสร้าง จึงบอกตามที่เป็นจริงวันนี้",
        "The entry is written but has not reached the catalogue yet — it lands on the "
        "next import. This is measured at build time, so the page says what is true "
        "today rather than what was intended.")) + "</p>")
    B.append("<p>" + bi(
        "เทียบกับตัวเลขของจังหวัดเอง ปี 2567: อำเภอหางดงมีแหล่งจำหน่ายของฝาก-ของที่ระลึก-OTOP "
        "148 แห่ง — เป็นตัวเลขระดับอำเภอที่ไม่มีหมุดอยู่ข้างใต้",
        "Set that against the province's own 2567 count: 148 souvenir and OTOP outlets "
        "in Hang Dong district. That is a district total with no pins under it.")
        + cite("otop-outlets") + "</p>")
    B.append("</div>")

    # the steak trap
    B.append('<h2 id="teak">' + bi("กับดักคำว่า teak", "The teak trap") + "</h2>")
    B.append("<p>" + bi(
        "กับดักหนึ่งอันที่ควรพิมพ์ไว้ให้เห็น มากกว่าจะแอบแก้: ค้นคำว่า <b>teak</b> "
        "แบบไม่สนตัวพิมพ์ใหญ่เล็ก ได้ %d รายการในสารบัญนี้ %d รายการเป็นร้านสเต็ก "
        "เพราะ steak มี teak อยู่ข้างใน ที่เหลืออีก %d รายการเป็นคาเฟ่ เกสต์เฮาส์ รีสอร์ต "
        "สวนสาธารณะ และวัดผาแตกซึ่งสะกดเป็นอังกฤษว่า Pha Teak — "
        "และในทั้งหมดนั้น <b>%d</b> รายการเป็นร้านไม้"
        % (n_teak, n_steak, n_teak - n_steak, n_teak_craft),
        "One trap worth printing rather than quietly patching. A case-insensitive search "
        "for <b>teak</b> returns %d records here. %d of them are steakhouses, because "
        "<i>steak</i> contains <i>teak</i>. The other %d are cafes, guesthouses, resorts, "
        "a public garden, and a temple whose name romanises as Pha Teak. Of all %d, the "
        "number that are a wood shop is <b>%d</b>."
        % (n_teak, n_steak, n_teak - n_steak, n_teak, n_teak_craft), raw=True)
        + "</p>")
    B.append("<p>" + bi(
        "นี่เป็นตระกูลเดียวกับกับดักที่ไฟล์งานของเว็บนี้จดไว้แล้วสองอัน — (?&lt;!ห)วัด "
        "เพราะคำว่า จังหวัด ลงท้ายด้วยตัวอักษร วัด และ se-ed ที่ไปตรงกับคำว่า Seed "
        "จนร้านคั่วกาแฟกลายเป็นร้านหนังสือ ต่างกันตรงที่อันนี้ไม่ได้อยู่แค่ในโค้ดของเรา: "
        "ใครพิมพ์คำว่า teak ลงช่องค้นหาที่ไหนก็เจอปัญหาเดียวกัน",
        "This is the same family as two traps already written into this site's own notes "
        "— (?&lt;!ห)วัด, because จังหวัด <i>province</i> ends in the letters วัด "
        "<i>temple</i>; and se-ed, which matched the English word Seed and filed a coffee "
        "roaster as a bookshop. The difference is that this one is not confined to our "
        "code: anyone typing teak into any search box has it too.", raw=True) + "</p>")
    B.append("<p>" + bi(
        "คำไทยที่ควรใช้แทนคือ ไม้แกะสลัก — ทั้งสองจังหวัดมี %d บันทึกที่ชื่อของมันเองบอกว่า "
        "ทำงานแกะหรืองานหัตถกรรม (ไม่นับคลาสแกะสลักผักผลไม้ ซึ่งเป็นคนละอาชีพและมีชั้นของ "
        "ตัวเองอยู่แล้ว) และในรัศมี 2.5 กิโลเมตรรอบหมู่บ้านมี %d รายการ — คือชื่อหมู่บ้านเอง "
        "บนหมุดตลาดสด" % (n_carve_named, n_carve_here),
        "The Thai to search is ไม้แกะสลัก, carved wood. Across both provinces %d records "
        "say in their own name that they carve or make handicraft — fruit carving classes "
        "excluded, since that is a different trade and already has a shelf of its own. "
        "Within 2.5 km of the village there are %d of them, and it is the village's own "
        "name, sitting on the wet-market pin."
        % (n_carve_named, n_carve_here)) + "</p>")

    # ── how it started ────────────────────────────────────────────────────
    B.append('<h2 id="start">' + bi("เริ่มจากปีที่ฝนไม่ตก", "It starts with a drought")
             + "</h2>")
    B.append("<p>" + bi(
        "ระหว่าง พ.ศ. 2500–2505 นาไม่ได้ผล ชาวบ้านสามคนออกไปรับจ้างที่ประตูเชียงใหม่ "
        "แล้วไปเรียนแกะสลักที่ร้านน้อมศิลป์ บ้านวัวลาย กลับมาคนละความถนัด — องค์พระ สิงห์ ครุฑ — "
        "แล้วสอนต่อ นั่นคือทั้งหมดของจุดเริ่ม: ไม่ใช่ประเพณีเก่าแก่ที่สืบมาแต่โบราณ "
        "แต่เป็นงานรับจ้างที่เรียนมาแล้วเอากลับบ้านในช่วงชีวิตคนคนเดียว",
        "Between 1957 and 1962 the rice failed. Three men took wage work at Chiang Mai "
        "Gate and learned to carve at the Nom Sin shop in Ban Wua Lai. They came home "
        "with one subject each — Buddha images, lions, garuda — and taught it on. That "
        "is the whole origin, and it is worth saying plainly: not an ancient inheritance, "
        "but a trade learned for wages and carried home inside one lifetime.")
        + cite("sac") + "</p>")
    B.append("<p>" + bi(
        "อีกเจ็ดปีต่อมากรมชลประทานขุดคลองผ่านหมู่บ้าน น้ำมาถึงไร่นา — และคลองเส้นนั้น "
        "คือถนนที่ตลาดไปยืนอยู่ในอีกยี่สิบปี",
        "Seven years later the Irrigation Department cut a canal through the village. It "
        "brought water to the fields — and it is the street the market would later stand "
        "on, both banks of it.") + cite("sac") + "</p>")
    B.append("<p>" + bi(
        "ส่วนชื่อหมู่บ้าน ผู้เฒ่าเล่าไว้หลายทางและหน้านี้เก็บไว้ทุกทางแทนที่จะเลือกข้าง: "
        + v["name_story_th"].split("—", 1)[-1].strip(),
        v["name_story_en"]) + cite("sac") + "</p>")

    B.append('<div class="cv-fig">' + _timeline_svg(reg, esc, bi_text) + "</div>")
    B.append('<p class="cv-figcap">' + bi(
        "วางตามมาตราส่วนปีจริง ช่องว่างสี่สิบปีระหว่างสามคนนั้นกับวันที่หมู่บ้านถูกตั้งเป็นต้นแบบ "
        "ระดับประเทศ คือส่วนที่ยาวที่สุดของเรื่อง",
        "Spaced to true year scale. The forty-year gap between those three men and the "
        "day the village was made a national model is the longest part of the story.")
        + "</p>")
    B.append("<ol>")
    for e in sorted(reg["timeline"], key=lambda x: x["sort"]):
        B.append('<li><b>%s</b> <span class="cv-src">· พ.ศ. %s</span><br>'
                 % (esc(str(e["ce"])), esc(str(e["year"])))
                 + bi(e["th"], e["en"]) + cite(e["src"]) + "</li>")
    B.append("</ol>")

    # ── the chain of hands ────────────────────────────────────────────────
    B.append('<h2 id="hands">' + bi("ไม้หนึ่งชิ้นผ่านมือกี่คู่",
                                    "How many pairs of hands one piece passes") + "</h2>")
    B.append('<div class="cv-fig">' + _chain_svg(reg, esc, bi_text) + "</div>")
    B.append('<p class="cv-figcap">' + bi(
        "แต่ละกล่องคือคนละคน ไม่ใช่คนละขั้นตอนของคนเดียว — และนั่นคือเหตุผลที่ราคาที่ปลายทาง "
        "ไม่ได้บอกว่าใครแกะ",
        "Each box is a different person, not a different step by the same one — which is "
        "why the price at the end does not tell you who carved it.") + "</p>")
    B.append('<div class="cv-grid">')
    for h in reg["hands"]:
        B.append('<div class="cv-card"><h3>' + bi(h["th"], h["en"]) + "</h3>"
                 + "<p>" + bi(h["note_th"], h["note_en"]) + cite(h["src"])
                 + (cite(h["src2"]) if h.get("src2") else "") + "</p></div>")
    B.append("</div>")
    B.append("<p>" + bi(
        "ที่ลิงก์สุดท้ายมีตัวเลขจริงอยู่ชุดหนึ่ง และเป็นของปี 2549 ไม่ใช่ของวันนี้: "
        "ห้องเช่า 3×4 เมตรริมทางเข้าคิดกับพ่อค้าต่างถิ่นหมื่นกว่าบาท คิดกับคนในชุมชนราวพันบาท "
        "และมังกรแกะที่ร้านชุมชนขาย 800 บาท ไปโผล่ที่ร้านหน้า 3,000 บาท — "
        "หน้านี้ไม่ได้บอกว่าใครควรได้ขายของ แต่บอกว่าคุณกำลังยืนอยู่ตรงไหนของสายพาน",
        "There is one set of real numbers on that last link, and they are from 2006, not "
        "from today: a 3×4 m room on the approach let at over 10,000 baht to an incoming "
        "trader and about 1,000 to a villager, and a carved dragon that was 800 baht in a "
        "canal shop was 3,000 at a frontage one. This page is not saying who should be "
        "allowed to sell. It is saying where on the chain you are standing.")
        + cite("mgr-capital") + "</p>")

    # ── the woods ─────────────────────────────────────────────────────────
    B.append('<h2 id="wood">' + bi("ไม้อะไรบ้าง", "Which woods") + "</h2>")
    B.append('<table class="cv-tbl"><thead><tr>'
             + "<th>" + bi("ไม้", "Wood") + "</th>"
             + "<th>" + bi("ใช้ทำอะไร", "What it is for") + "</th>"
             + "<th>" + bi("พากลับบ้าน", "Carrying it home") + "</th>"
             + "</tr></thead><tbody>")
    for w in reg["woods"]:
        ink, bg, fth, fen = CARRY_INK[w["carry"]]
        B.append("<tr><td>" + bi(w["th"], w["en"])
                 + '<br><span class="lat">' + esc(w["latin"]) + "</span></td>"
                 + "<td>" + bi(w["use_th"], w["use_en"]) + cite(w["src"]) + "</td>"
                 + '<td><span class="cv-flag" style="color:%s;background:%s">' % (ink, bg)
                 + bi(fth, fen) + "</span></td></tr>")
    B.append("</tbody></table>")
    cn = reg["carry_note"]
    B.append("<p>" + bi(cn["th"], cn["en"]) + " — "
             + '<a href="%s">%s</a>.' % (cn["href"], esc(bi_text(
                 "ของฝากที่เดินทางได้", "Souvenirs and the law"))) + "</p>")
    B.append("<p>" + bi(
        "และมีการเปลี่ยนกฎหมายหนึ่งข้อที่เปลี่ยนคำถามเรื่องไม้ทั้งข้อ: พ.ร.บ.ป่าไม้ (ฉบับที่ 8) "
        "พ.ศ. 2562 แก้มาตรา 7 ให้ไม้ทุกชนิดที่ขึ้นในที่ดินมีกรรมสิทธิ์ไม่เป็นไม้หวงห้าม "
        "— ไม้สักจากสวนของตัวเองจึงคนละเรื่องกับไม้สักจากป่า",
        "And one change in the law reshaped the whole wood question: the Forest Act "
        "(No. 8) of 2019 rewrote section 7 so that no tree grown on titled land is "
        "restricted timber. Teak off your own land and teak off the forest floor stopped "
        "being the same object in law.") + cite("forest2562") + "</p>")

    # ── the Buddha image, which is a different object in law ──────────────
    # This is the section the souvenir page cannot carry: its wood row is
    # about species and CITES, and its handicraft row says the law leaves
    # handicraft wide open — true of an elephant, not true of a Buddha. The
    # sheet quoted here is the Department of International Trade Promotion's
    # own, and the fee/office/documents are its words rather than ours.
    ex = reg["export"]
    B.append('<h2 id="phra">' + bi(ex["title_th"], ex["title_en"]) + "</h2>")
    B.append("<p>" + bi(ex["lead_th"], ex["lead_en"]) + cite(ex["src"]) + "</p>")
    B.append('<ul class="cv-asks">')
    for r in ex["rows"]:
        B.append("<li>" + bi(r["th"], r["en"]) + "</li>")
    B.append("</ul>")
    B.append("<p>" + bi(ex["ask_th"], ex["ask_en"]) + "</p>")
    B.append('<p class="cv-src">' + bi(ex["caveat_th"], ex["caveat_en"]) + "</p>")

    # ── what to ask ───────────────────────────────────────────────────────
    B.append('<h2 id="ask">' + bi("ห้าคำถามที่ถามได้ตรง ๆ",
                                  "Five things you can just ask") + "</h2>")
    B.append("<p>" + bi(
        "ทั้งงานมือและงานเครื่องมีขายที่นี่ตามปกติ และงานทำเก่าเป็นของขึ้นชื่อของหมู่บ้าน "
        "ไม่ใช่ของแอบทำ ถามจึงเป็นเรื่องปกติของการซื้อขาย ไม่ใช่การกล่าวหา",
        "Hand work and machine work are both sold here openly, and reproduction antiques "
        "are something this village is known for rather than something it hides. Asking "
        "is part of the transaction, not an accusation.") + cite("sawa") + "</p>")
    B.append('<ul class="cv-asks">')
    for a in reg["asks"]:
        B.append("<li>" + bi(a["th"], a["en"])
                 + '<span class="why">' + bi(a["why_th"], a["why_en"]) + "</span></li>")
    B.append("</ul>")
    # The paper version, because the person who needs these words is on a
    # footpath and not on this site. Same argument as the other reader sheets.
    B.append('<p><a class="cv-sheet" href="reader/carve-words.pdf">📄 '
             + bi("แผ่นคำศัพท์งานไม้ — พิมพ์ พับ พกไปหมู่บ้าน (PDF, A4)",
                  "The carving-words sheet — print it, fold it, take it to the "
                  "village (PDF, A4)") + "</a></p>")

    # ── the two centres ───────────────────────────────────────────────────
    B.append('<h2 id="walk">' + bi("เดินสองแบบ", "Two different walks") + "</h2>")
    B.append('<div class="cv-grid">')
    for z in reg["zones"]:
        B.append('<div class="cv-card"><h3>' + bi(z["th"], z["en"]) + "</h3>"
                 + "<p>" + bi(z["what_th"], z["what_en"]) + cite(z["src"]) + "</p></div>")
    B.append("</div>")
    B.append("<p>" + bi(
        "และไม่ใช่ที่ซื้อของฝากอย่างเดียว — อบต.ขุนคงเขียนไว้เองว่าคนไทยและคนต่างชาติมาหาซื้อ "
        "ของตกแต่ง “บ้าน ร้านค้า และโรงแรม” ที่นี่ ใครกำลังจะเปิดร้าน แต่งคอนโด หรือทำห้องพัก "
        "ในเชียงใหม่ นี่คือที่ที่เฟอร์นิเจอร์ไม้ในเมืองนี้จำนวนมากเดินทางมาจาก",
        "And it is not only a souvenir errand. The Khun Khong SAO's own description says "
        "Thais and foreigners come here for fittings for “homes, shops and hotels” — so "
        "if you are opening a room, furnishing a condo, or fitting out a guesthouse in "
        "Chiang Mai, this is where a great deal of the city's wooden furniture comes from, "
        "at the end of the chain rather than the middle of it.") + cite("khunkhong") + "</p>")
    gt = reg["getting_there"]
    B.append("<p>" + bi(gt["th"], gt["en"]) + "</p>")

    # Two published organisational numbers. Not a shop between them, which is
    # the point: the questions this page raises — is the fair on, does anyone
    # take visitors into a workshop — are answered by the enterprise or the
    # SAO, and nobody has to guess which shopfront to phone.
    co = reg["contacts"]
    B.append("<p>" + bi(co["note_th"], co["note_en"]) + "<br>")
    for c in co["rows"]:
        B.append(bi(c["th"], c["en"]) + " · <a href=\"tel:%s\">%s</a>"
                 % (att("+66" + c["tel"].replace("-", "")[1:]), esc(c["tel"]))
                 + cite(c["src"]) + "<br>")
    B.append("</p>")

    # ── the fair ──────────────────────────────────────────────────────────
    f = reg["fair"]
    B.append('<h2 id="fair">' + bi(f["th"], f["en"]) + "</h2>")
    B.append("<p>" + bi(f["drift_th"], f["drift_en"]) + cite(f["src"]) + "</p>")
    B.append("<ul>")
    for ed in f["editions"]:
        B.append("<li>" + bi("ครั้งที่ %d — %s" % (ed["n"], ed["th"]),
                             "%s edition — %s" % (_ord(ed["n"]), ed["en"]))
                 + cite(ed["src"]) + "</li>")
    B.append("</ul>")
    B.append("<p>" + bi("จัดที่ " + f["where_th"] + " โดย " + f["by_th"],
                        "At " + f["where_en"] + ", run by " + f["by_en"]) + "</p>")

    # ── the road ──────────────────────────────────────────────────────────
    B.append('<h2 id="road">' + bi("ถนนสาย 108 ไม่ได้มีหมู่บ้านเดียว",
                                   "Route 108 is not one village") + "</h2>")
    B.append('<ul class="cv-road">')
    for s in reg["road"]:
        B.append("<li><b>" + bi(s["th"], s["en"]) + "</b><br>"
                 + bi(s["craft_th"], s["craft_en"]) + "<br>"
                 + '<span class="cv-src">' + bi(s["where_th"], s["where_en"]) + "</span><br>"
                 + bi(s["note_th"], s["note_en"]) + cite(s["src"]))
        if s["key"] == "muangkung" and muangkung == 0:
            B.append('<br><span class="zero">' + bi(
                "สารบัญนี้ยังไม่มีบันทึกใดที่ชื่อบอกว่าเป็นบ้านเหมืองกุงเลยสักรายการ — "
                "วัดสดตอนสร้างหน้า และถ้าวันไหนมี ประโยคนี้จะหายไปเอง",
                "This directory holds no record at all whose name says Muang Kung — "
                "measured live at build time, and the sentence removes itself the day "
                "one arrives.") + "</span>")
        B.append("</li>")
    B.append("</ul>")

    # ── the registers: honours and masters ────────────────────────────────
    B.append('<h2 id="register">' + bi("ทะเบียน", "The register") + "</h2>")
    B.append('<ul class="cv-hon">')
    for h in reg["honours"]:
        B.append("<li>" + bi(h["th"], h["en"])
                 + '<br><span class="by">' + bi(h["by_th"], h["by_en"])
                 + " · " + esc("%s / พ.ศ. %s" % (h["ce"], h["be"])) + "</span>"
                 + cite(h["src"]) + "</li>")
    for m in reg["masters"]:
        B.append("<li>" + bi(m["name_th"] + " — " + m["honour_th"],
                             m["name_en"] + " — " + m["honour_en"])
                 + '<br><span class="by">' + bi(m["by_th"], m["by_en"])
                 + " · " + esc("%s / พ.ศ. %s" % (m["ce"], m["be"])) + "</span><br>"
                 + bi(m["for_th"], m["for_en"]) + cite(m["src"]) + "</li>")
    B.append("</ul>")
    rn = reg["royal_note"]
    B.append("<p>" + bi(rn["th"], rn["en"]) + "</p>")

    # ── the closing notes ─────────────────────────────────────────────────
    B.append('<p class="cv-note-p">' + bi(
        "ทุกตัวเลขที่นับได้ในหน้านี้นับสดจากสารบัญตอนสร้างหน้า ตัวเลขที่เหลือเป็นของคนอื่น "
        "มีวันที่กำกับ และไม่มีราคาใดในหน้านี้ที่เดินไปดูมาเอง ไม่มีร้านไหนถูกแนะนำ",
        "Every count on this page is measured live from the directory at build time. The "
        "rest of the figures are other people's, dated where they were said. No price "
        "here has been walked, and no shop is recommended.") + "</p>")
    B.append('<p class="cv-note-p">')
    for u in reg.get("unverified", []):
        B.append("· " + esc(u) + "<br>")
    B.append("</p>")

    # What refused us, said out loud. The WO-33 rule: a source that would not
    # answer is printed as a refusal with its address, because "we could not
    # read it" and "it does not say that" are different sentences and only one
    # of them is true here.
    if reg.get("attempted"):
        B.append('<p class="cv-note-p"><b>'
                 + bi("แหล่งที่ไม่ยอมตอบเรา", "Sources that would not answer us")
                 + "</b><br>")
        for a in reg["attempted"]:
            B.append("· " + bi(a["th"], a["en"]) + " "
                     + '<span class="cv-src">' + out_a(a["ref"], esc(a["what"]))
                     + " · " + esc(a["tried"]) + "</span><br>")
        B.append("</p>")

    B.append(share_block(BASE + "tawai.html",
                         "ไม้แกะสลักบ้านถวาย · Ban Tawai — the carving village",
                         card=(shelf_og("tawai") if shelf_og else None)))
    B.append("</div>")

    (DOCS / "tawai.css").write_text(CSS)
    (DOCS / "tawai.html").write_text(page(
        "ไม้แกะสลักบ้านถวาย · Ban Tawai — the carving village",
        "".join(B), 0,
        path="tawai.html",
        desc="บ้านถวาย อ.หางดง — หมู่บ้านไม้แกะสลัก ใครทำอะไรตรงไหนในสายพาน ไม้อะไรพากลับบ้านได้ "
             "งานประจำปีจัดเมื่อไหร่ และถนนสาย 108 กับบ้านเหมืองกุง วัดต้นเกว๋น · Ban Tawai "
             "woodcarving village, Hang Dong: the chain of hands, which woods travel, when "
             "the fair really is, and the rest of the craft road south.",
        extra_head='<link rel=stylesheet href="tawai.css">'))
    return ("%d dated rows · %d records within %.1f km, %d on a craft shelf · "
            "teak %d of which steak %d · %d named carvers province-wide · muang kung %d"
            % (len(reg["timeline"]), len(near), NEAR_KM, n_craft,
               n_teak, n_steak, n_carve_named, muangkung))


def _ord(n):
    if 10 <= n % 100 <= 20:
        s = "th"
    else:
        s = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, s)
