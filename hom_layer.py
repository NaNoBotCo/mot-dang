#!/usr/bin/env python3
"""หม้อห้อม — indigo, the plant and the pot (/hom.html). WO-50.

WHY THIS PAGE EXISTS. The blue shirt is the most recognisable thing northern
Thailand makes, and the directory holds EIGHTY-SIX craft shops in Chiang Mai
with ห้อม on none of their signs. That is not a hole in the crawl. It is what
the trade looks like: the shirt is sold as a shirt, in a market, by people who
assume you know what it is — and the pot that makes it is two hundred
kilometres east, in Phrae, in a village named after an anvil.

So this is not a shelf. A shelf of shops would be a lie of omission twice
over: it would imply the making happens here, and it would imply that a
directory can tell a real one from a printed one on the strength of a shopfront.
What a reader standing in Warorot actually needs is four things, and none of
them is a list of addresses:

  1. WHICH PLANT. ห้อม (Strobilanthes cusia, the northern hill shrub) is not
     คราม (Indigofera tinctoria, the lowland legume), and standard Thai fuses
     them. The page keeps them apart because the north does.
  2. HOW TO TELL. And the test is backwards, which is why it is worth a page:
     real indigo CROCKS. It runs in the first washes and it fades with wear.
     A shirt whose colour never moves was never in a pot. The flaw is the proof.
  3. WHAT THE POT IS. A reduction vat is a live microbial culture with an
     appetite and a death, and the vocabulary Thai dyers use for it — หิว,
     ลักหนี, ตาย, เป็น — is not decoration. It is a diagnostic. Drawn here as
     one, because a reader who understands why the liquor goes yellow
     understands the price of the shirt.
  4. WHERE THE POT IS. Phrae. Said plainly, with the road, instead of
     pretending the walk ends in Nimman.

DRAWN, NOT DESCRIBED. Four instruments, all inline SVG, no basemap and no
script: the migration route from Xieng Khouang; the chemistry as a loop whose
nodes are painted the colour the liquor actually is at that step; the pot's
four states as a dial; and the timeline from 1834 to the GI. The colours in
the cycle are the page's one piece of real teaching — the liquor is YELLOW-GREEN
in the vat and the cloth is YELLOW-GREEN coming out, and every photograph
anyone has ever seen of indigo shows it already blue.

MEASURED, NEVER AWARDED (the /views rule). Every count on this page is taken
live from the directory at build time — the craft-shop census, the zero, and
the place-names that carry the plant. If a shop ever paints ห้อม on its sign
and the crawl catches it, the sentence changes by itself.

THE SIBLING. wichaa.net keeps the tradition: what the palm leaf records about
cloth (37 witnesses, not one about colour), the Vinaya rule that makes indigo
the one colour a monk may not wear, and the 1953 Chiang Mai dinner that turned
a work shirt into a costume. This page keeps the walk. Each links the other,
the same contract as chang.html.

Entry point: emit(globals_of_build, data) — hooked in build.py beside the
souvenir layer. Emits hom.html + hom.css.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The plant in a place-name. Northern toponyms take ห้วย + <plant>, so a creek
# called Indigo Creek is a claim about where the plant grew — but ฮ่อม in kam
# mueang is ALSO an ordinary word for a lane, so this is reported as a reading
# and never as a fact (see data/curated/hom.json → unverified).
HOM_NAME_RX = re.compile(r"ห้วยห้อม|ห้วยฮ่อม|เด่นฮ่อม|บ้านห้อม|ดอยห้อม")
# What counts as ONE place. A wat and a school both called Huai Hom in Fang are
# one toponym on two records, and counting them as two would inflate the finding
# the page rests on; two Huai Hom in different amphoe are genuinely two, and
# deduping on the bare name alone silently merged Fang's with Khun Tan's. So the
# key is (toponym, district) — read from the address, which is where the
# directory keeps the district.
AMPHOE_RX = re.compile(r"(?:อ\.\s*|อำเภอ\s*)([^\s,]+)")
# What a shop would have to say for the shelf to stop being empty. Deliberately
# the shop's OWN word in both spellings plus the Latin — the KNOWN_EMPTY lesson
# from the salon shelf, run before the shelf exists rather than after.
SHOP_NAME_RX = re.compile(r"ห้อม|ฮ่อม|ย้อมคราม|มัดย้อม|indigo|mo\s*hom|moh?\s*hom", re.I)
CRAFT_SUBS = ("crafts", "tailor", "alterations")

# The liquor's real colours, step by step. This is the page's teaching and the
# only place hex codes are hand-picked rather than taken from the site tokens:
# they are describing a physical thing, not decorating a box.
CYCLE_INK = {
    1: ("#8d9a3f", "#f2f4e2"),   # steeping — yellow-green, stinking
    2: ("#3f4f7a", "#e6e9f3"),   # lime beaten in — the paste drops, bruise-blue
    3: ("#5a4a34", "#efe7db"),   # founding the pot — ash lye, banana, tamarind
    4: ("#7f8d3a", "#f1f3e0"),   # chok — reduced, soluble, yellow-green again
    5: ("#93a04a", "#f3f5e6"),   # the cloth comes out YELLOW-GREEN
    6: ("#223f7d", "#dfe5f4"),   # air — and only now is it blue
    7: ("#14275a", "#d5dcef"),   # cured and re-dipped — deeper
}

# Mv.VIII.29. Seven colours a robe may not be entirely dyed, plus the one that
# is left. The swatches are indicative — the Pali colour terms do not map
# cleanly onto hex and the page says so.
VINAYA = [
    ("nīla", "นิล", "#26418f", True),
    ("pīta", "เหลือง", "#d8b02a", False),
    ("lohitaka", "แดงเลือด", "#a52a1f", False),
    ("mañjeṭṭha", "แดงเข้ม", "#8e2f5c", False),
    ("kaṇha", "ดำ", "#241f1c", False),
    ("mahāraṅga", "ส้ม", "#cf6a1c", False),
    ("mahānāma", "น้ำตาลอ่อน", "#c9a882", False),
]

# Marks that cannot begin a Thai syllable. A segment starting with one of these
# is the tail of the segment before it and must be glued back on — this is what
# turned "ละครั้ง" into "ละคร | ั้ง" and put a stranded ั้ง on its own line.
_TAIL = "ัิีึืุู่้๊๋็์ำะาๆๅฺ"
_HEADLESS = set(_TAIL)


def _repair(segs):
    """Glue a dictionary segmentation back into things a Thai reader recognises.

    translit._segment is tuned for SEARCH — over-splitting costs it nothing
    there, because both halves still index. On a drawn label it costs
    everything: "น้ำด่าง" came back as "น้ำ | ด่า | ง" and the line broke after
    ด่า. Two repairs, in order:

      · a segment opening with a dependent mark is a tail — merge backwards
      · a lone consonant is the head of what follows — merge forwards
    """
    out = []
    for s in segs:
        if out and s and s[0] in _HEADLESS:
            out[-1] += s
        else:
            out.append(s)
    fixed, i = [], 0
    while i < len(out):
        s = out[i]
        if len(s) == 1 and s not in _HEADLESS and i + 1 < len(out):
            fixed.append(s + out[i + 1])
            i += 2
        elif len(s) == 1 and fixed:
            fixed[-1] += s
            i += 1
        else:
            fixed.append(s)
            i += 1
    return fixed


def _pieces(s):
    """The atoms a line may break between, each flagged with whether the AUTHOR
    put a space before it.

    Thai has no interword space, but it does use the space as a phrase
    separator — and those are the breaks a Thai reader expects, so they have to
    survive. Dropping them is how "เติมน้ำด่าง กล้วยสุก มะขามเปียก" came back
    set as one unbroken run. Returns [(text, space_before)].
    """
    try:
        import translit
    except Exception:                      # translit is stdlib-only and sits in
        return [(w, i > 0)                 # the repo root; this is belt only
                for i, w in enumerate(s.split())]
    atoms = []
    for ci, chunk in enumerate(s.split(" ")):
        if not chunk:
            continue
        if any("\u0e00" <= c <= "\u0e7f" for c in chunk):
            parts = _repair(translit._segment(chunk))
        else:
            parts = [chunk]
        for pi, part in enumerate(parts):
            # a space before this atom only where the author wrote one
            atoms.append((part, ci > 0 and pi == 0))
    return atoms


def _wrap(s, n, limit=3):
    """Break a label for SVG, which has no wrapping of its own.

    Thai has no spaces, so a naive slice at `n` characters breaks mid-syllable —
    which is exactly what shipped: "เติมน้ำด่าง กล้วยสุก มะขามเปียก" came out
    with ด่าง cut in half. Breaks now land on dictionary-word boundaries, using
    the segmenter the search index already runs on (translit._segment) plus the
    repair above, and the author's own spaces are kept and preferred. A word
    longer than the measure is not chopped — it overhangs, which is visible and
    therefore fixable, where a silent cut is neither.
    """
    def pack(atoms):
        lines, line = [], ""
        for text, sp in atoms:
            glue = " " if (sp and line) else ""
            cand = line + glue + text
            if line and len(cand) > n:
                lines.append(line)
                line = text
            else:
                line = cand
        if line:
            lines.append(line)
        return lines

    # Prefer the author's own phrase breaks. Only if whole phrases will not fit
    # the measure does this fall back to breaking inside one — "ย้อมได้ วันละครั้ง"
    # should break after ได้, not split วันละครั้ง at a dictionary seam.
    phrases = [(w, i > 0) for i, w in enumerate(s.split(" ")) if w]
    if phrases and max(len(w) for w, _ in phrases) <= n:
        by_phrase = pack(phrases)
        if len(by_phrase) <= limit:
            return by_phrase

    atoms = _pieces(s)
    if not atoms:
        return []
    lines, line = [], ""
    for text, sp in atoms:
        glue = " " if (sp and line) else ""
        cand = line + glue + text
        if line and len(cand) > n:
            lines.append(line)
            line = text
        else:
            line = cand
    if line:
        lines.append(line)
    return lines[:limit]


CSS = """
.hm-wrap{max-width:56rem;margin:0 auto}
.hm-fig{margin:1.4rem 0;padding:1rem .7rem;background:var(--card);
  border:1px solid var(--warm-border);border-radius:14px;overflow-x:auto}
.hm-fig svg{display:block;width:100%;height:auto;min-width:520px}
.hm-figcap{font-size:.86rem;color:var(--mute);margin:.55rem .3rem 0;line-height:1.5}
.hm-maplabel{font-size:12.5px;fill:var(--ink);font-weight:600}
.hm-mapnote{font-size:11px;fill:var(--mute)}
.hm-route{fill:none;stroke:#26418f;stroke-width:2.4;stroke-dasharray:7 5;opacity:.75}
.hm-pin{fill:#26418f;stroke:var(--card);stroke-width:2}
.hm-pin-pot{fill:#14275a;stroke:#e8c766;stroke-width:2.6}
.hm-pin-creek{fill:none;stroke:#5f7f4a;stroke-width:2}
.hm-step{stroke:var(--warm-border);stroke-width:1.2}
.hm-stepn{font-size:13px;font-weight:700;fill:var(--ink)}
.hm-stept{font-size:12px;fill:var(--ink)}
.hm-arrow{fill:none;stroke:var(--mute);stroke-width:1.6;opacity:.6}
.hm-dialname{font-size:13.5px;font-weight:700}
.hm-dialsub{font-size:11.5px;fill:var(--mute)}
.hm-year{font-size:12px;fill:var(--mute);font-weight:600}
.hm-ev{font-size:12.5px;fill:var(--ink)}
.hm-spine{stroke:var(--warm-border);stroke-width:2}
.hm-evdot{fill:#26418f}
.hm-evdot.big{fill:#14275a;stroke:#e8c766;stroke-width:2}
.hm-grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));margin:1rem 0}
.hm-card{background:var(--card);border:1px solid var(--warm-border);border-radius:12px;padding:.8rem .9rem}
.hm-card h3{margin:.1rem 0 .45rem;font-size:1rem}
.hm-card p{margin:.3rem 0;font-size:.92rem;line-height:1.55}
.hm-tests{list-style:none;padding:0;margin:1rem 0}
.hm-tests li{background:var(--card);border:1px solid var(--warm-border);border-left:5px solid #26418f;
  border-radius:10px;padding:.7rem .9rem;margin:.5rem 0}
.hm-tests li.printed{border-left-color:#a8452e}
.hm-tests .tlab{display:inline-block;font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--mute);margin-bottom:.25rem}
.hm-swatch{display:inline-block;width:.95rem;height:.95rem;border-radius:3px;vertical-align:-2px;
  margin-right:.4rem;border:1px solid rgba(0,0,0,.18)}
.hm-vin{list-style:none;padding:0;margin:.6rem 0;display:grid;gap:.35rem;
  grid-template-columns:repeat(auto-fit,minmax(11rem,1fr))}
.hm-vin li{font-size:.9rem;padding:.3rem .45rem;border-radius:8px}
.hm-vin li.no{background:var(--soft)}
.hm-vin li.hit{background:#26418f;color:#fff;font-weight:600}
.hm-vin li.hit .hm-swatch{border-color:rgba(255,255,255,.5)}
.hm-count{background:var(--soft);border-radius:12px;padding:.85rem 1rem;margin:1.1rem 0;
  border:1px dashed var(--dashed)}
.hm-count b{font-size:1.5rem;line-height:1;color:var(--ant-dark)}
.hm-src{font-size:.82rem;color:var(--mute)}
.hm-src a{color:var(--mute)}
.hm-note{font-size:.88rem;color:var(--mute);border-top:1px solid var(--warm-border);
  margin-top:1.6rem;padding-top:.8rem;line-height:1.6}
@media (prefers-reduced-motion:no-preference){.hm-fig{scroll-behavior:smooth}}
"""


# ─────────────────────────────────────────────────────────── the drawn things

def _map_svg(reg, creeks, esc, bi_text):
    """The migration, and the plant in the map. One dashed line for the road the
    Tai Phuan were moved along, one gold pin for the pot, and hollow rings for
    every watercourse in the directory whose own name carries the plant.

    No province polygons: the directory holds none, and drawing a boundary it
    cannot cite is the mistake the hot-spring map refused. Labels are the
    cluster's, never a claim about where a line falls.
    """
    pts = [dict(p) for p in reg["route"]]
    for c in creeks:
        pts.append({"key": "creek", "th": c["th"], "en": c["en"],
                    "lat": c["lat"], "lng": c["lng"], "kind": "creek"})
    lats = [p["lat"] for p in pts]
    lngs = [p["lng"] for p in pts]
    lat0 = sum(lats) / len(lats)
    kx = 111.320 * math.cos(math.radians(lat0))
    ky = 110.574
    W, PAD = 760, 92
    span_x = max((max(lngs) - min(lngs)) * kx, 1)
    span_y = max((max(lats) - min(lats)) * ky, 1)
    scale = (W - 2 * PAD) / span_x
    H = int(span_y * scale) + 2 * PAD
    if H > 560:
        scale *= 560 / H
        H = 560

    def xy(p):
        return (PAD + (p["lng"] - min(lngs)) * kx * scale,
                PAD + (max(lats) - p["lat"]) * ky * scale)

    order = ["xiengkhouang", "nan", "thunghong"]
    line = " ".join("%.1f,%.1f" % xy(next(p for p in pts if p["key"] == k)) for k in order)
    out = [f'<polyline class="hm-route" points="{line}"/>']

    for p in pts:
        x, y = xy(p)
        if p["kind"] == "creek":
            out.append(f'<circle class="hm-pin-creek" cx="{x:.1f}" cy="{y:.1f}" r="5.4"/>')
        elif p["kind"] == "pot":
            out.append(f'<circle class="hm-pin-pot" cx="{x:.1f}" cy="{y:.1f}" r="8"/>')
        else:
            out.append(f'<circle class="hm-pin" cx="{x:.1f}" cy="{y:.1f}" r="5.6"/>')
    for p in pts:
        if p["kind"] == "creek":
            continue
        x, y = xy(p)
        anchor = "start" if x < W - 210 else "end"
        dx = 11 if anchor == "start" else -11
        out.append(f'<text class="hm-maplabel" x="{x + dx:.1f}" y="{y + 4:.1f}" '
                   f'text-anchor="{anchor}">{esc(p["th"])}</text>')
        out.append(f'<text class="hm-mapnote" x="{x + dx:.1f}" y="{y + 18:.1f}" '
                   f'text-anchor="{anchor}">{esc(p["en"])}</text>')
    if creeks:
        cx = sum(xy(p)[0] for p in pts if p["kind"] == "creek") / len(creeks)
        cy = sum(xy(p)[1] for p in pts if p["kind"] == "creek") / len(creeks)
        out.append(f'<text class="hm-mapnote" x="{cx:.1f}" y="{cy - 12:.1f}" '
                   f'text-anchor="middle">'
                   f'{esc("ห้วยห้อม · ห้วยฮ่อม · เด่นฮ่อม")}</text>')
    km100 = 100 * scale
    out.append(f'<g><line x1="{PAD}" y1="{H - 20}" x2="{PAD + km100:.1f}" y2="{H - 20}" '
               f'stroke="#7d6a52" stroke-width="2"/>'
               f'<text class="hm-mapnote" x="{PAD}" y="{H - 26}">100 km</text></g>')
    label = bi_text(
        "แผนที่ทางเดินของหม้อห้อม — จากเชียงขวางลงน่าน ถึงทุ่งโฮ้ง แพร่ "
        "และวงกลมโปร่งคือชื่อบ้านนามเมืองในเชียงใหม่-เชียงรายที่มีคำว่าห้อม",
        "The road the indigo came down: Xieng Khouang to Nan to Ban Thung Hong in Phrae. "
        "Hollow rings are places in Chiang Mai and Chiang Rai whose own names carry the plant.")
    return (f'<svg role="img" aria-label="{esc(label)}" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(out) + "</svg>")


def _cycle_svg(reg, esc, bi_text):
    """The chemistry as a flow, with every station painted the colour the liquor
    actually is there. Two rows and a return arc rather than a ring: it IS a
    cycle — the spent liquor goes back in the pot and is fed — but seven long
    bilingual labels on a circle either collide or get truncated, and a diagram
    that has to abbreviate its own steps is not teaching anything. Rows give
    each station the full width of its own box.

    The colour is the point. Green in, blue out, and TWO yellow-green stations
    in the middle that every photograph of indigo leaves out, because nobody
    photographs a vat that does not look blue yet.
    """
    steps = reg["cycle"]
    W = 760
    BW, BH, GAP = 172, 108, 16
    top, per_row = 34, 4
    rows = [steps[:per_row], steps[per_row:]]
    H = top + BH * 2 + 74 + 58   # +58 clears the return-arc caption
    out = []

    def box(s, x, y):
        ink, bg = CYCLE_INK[s["n"]]
        o = [f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" rx="12" fill="{bg}" '
             f'stroke="{ink}" stroke-width="2.4"/>',
             # the colour band: this strip IS the liquor at this step
             f'<rect x="{x}" y="{y}" width="{BW}" height="13" rx="12" fill="{ink}"/>',
             f'<rect x="{x}" y="{y + 7}" width="{BW}" height="6" fill="{ink}"/>',
             f'<circle cx="{x + 20:.0f}" cy="{y + 36}" r="13" fill="{ink}"/>',
             f'<text class="hm-stepn" x="{x + 20:.0f}" y="{y + 41}" text-anchor="middle" '
             f'fill="#fff">{s["n"]}</text>']
        o.append(f'<text class="hm-stept" x="{x + 40:.0f}" y="{y + 34}">'
                 f'{esc(s["th"][:22])}</text>')
        if len(s["th"]) > 22:
            o.append(f'<text class="hm-stept" x="{x + 40:.0f}" y="{y + 49}">'
                     f'{esc(s["th"][22:44])}</text>')
        # the English gloss wraps on words inside the box rather than clipping
        for j, ln in enumerate(_wrap(s["en"], 26, 3)):
            o.append(f'<text class="hm-mapnote" x="{x + 12:.0f}" y="{y + 70 + j * 14}">'
                     f'{esc(ln)}</text>')
        return "".join(o)

    xs = []
    for ri, row in enumerate(rows):
        y = top + ri * (BH + 74)
        span = len(row) * BW + (len(row) - 1) * GAP
        x0 = (W - span) / 2
        for ci, s in enumerate(row):
            x = x0 + ci * (BW + GAP)
            xs.append((x, y, s["n"]))
            out.append(box(s, x, y))
            if ci:
                px = x - GAP
                out.append(f'<path class="hm-arrow" d="M{px - 4:.0f},{y + BH / 2:.0f} '
                           f'h{GAP + 2}"/>')
                out.append(f'<path class="hm-arrow" d="M{px + 6:.0f},{y + BH / 2 - 4:.0f} '
                           f'l5,4 l-5,4"/>')
        # row 1 hands down to row 2 at the right edge
        if ri == 0:
            rx = x0 + span
            my = y + BH
            out.append(f'<path class="hm-arrow" d="M{rx - BW / 2:.0f},{my} '
                       f'v22 h{18} v30 h{-(rx - BW / 2 - x0 + 18):.0f}"/>')
    # the return arc: step 7's liquor goes back into the pot at step 3
    last_x, last_y, _ = xs[-1]
    third = next(v for v in xs if v[2] == 3)
    ay = last_y + BH + 26
    out.append(f'<path class="hm-arrow" stroke-dasharray="6 5" '
               f'd="M{last_x + BW / 2:.0f},{last_y + BH} v26 '
               f'H{third[0] + BW / 2:.0f} V{third[1] + BH + 6:.0f}"/>')
    out.append(f'<path class="hm-arrow" d="M{third[0] + BW / 2 - 4:.0f},'
               f'{third[1] + BH + 14:.0f} l4,-8 l4,8"/>')
    out.append(f'<text class="hm-mapnote" x="{W / 2:.0f}" y="{ay + 16}" '
               f'text-anchor="middle">'
               f'{esc("น้ำย้อมที่ใช้แล้วเทกลับหม้อ แล้วเลี้ยงต่อ · spent liquor goes back in the pot")}'
               f'</text>')
    label = bi_text(
        "วงจรการย้อมคราม 7 ขั้น แถบสีบนกล่องคือสีจริงของน้ำย้อมในขั้นนั้น "
        "ผ้าออกจากหม้อเป็นสีเหลืองแกมเขียว แล้วจึงเปลี่ยนเป็นน้ำเงินเมื่อโดนอากาศ",
        "The seven-step indigo cycle. The band on each box is the colour the liquor really is "
        "at that stage: the cloth leaves the vat yellow-green and turns blue in the air. "
        "The dashed return is the spent liquor going back into the pot to be fed.")
    return (f'<svg role="img" aria-label="{esc(label)}" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(out) + "</svg>")


def _dial_svg(reg, esc, bi_text):
    """The pot's four states as a diagnostic strip: what you see on the surface,
    what it means, what you do. Drawn as four vessels rather than four boxes,
    because the reading a dyer takes is literally a look into a pot."""
    states = reg["pot_states"]
    W, H = 760, 344
    cw = W / len(states)
    tone = {"pen": ("#14275a", "#1d6f4a"), "hiu": ("#8d9a3f", "#b08415"),
            "ni": ("#6a6f52", "#a8452e"), "tai": ("#4a4a4a", "#7a2f22")}
    out = []
    for i, s in enumerate(states):
        x0 = i * cw
        ink, flag = tone.get(s["key"], ("#26418f", "#26418f"))
        px = x0 + cw / 2
        # the vessel
        out.append(f'<path d="M{px-42:.0f},96 q0,74 42,74 q42,0 42,-74 z" '
                   f'fill="{ink}" opacity=".16" stroke="{ink}" stroke-width="2"/>')
        # the liquor line + the foam cap, which is the actual reading
        out.append(f'<ellipse cx="{px:.0f}" cy="96" rx="42" ry="9" fill="{ink}" opacity=".55"/>')
        if s["key"] == "pen":
            for j, dx in enumerate((-24, -8, 8, 24)):
                out.append(f'<circle cx="{px+dx:.0f}" cy="{90 - (j % 2) * 5}" r="7" '
                           f'fill="#26418f" opacity=".85"/>')
        elif s["key"] == "hiu":
            out.append(f'<line x1="{px-30:.0f}" y1="90" x2="{px+30:.0f}" y2="90" '
                       f'stroke="#b08415" stroke-width="2.4" stroke-dasharray="4 5"/>')
        elif s["key"] == "ni":
            out.append(f'<path d="M{px-26:.0f},88 q26,-14 52,0" fill="none" '
                       f'stroke="#a8452e" stroke-width="2.4" stroke-dasharray="3 6"/>')
        else:
            out.append(f'<line x1="{px-22:.0f}" y1="82" x2="{px+22:.0f}" y2="102" '
                       f'stroke="#7a2f22" stroke-width="2.6"/>')
            out.append(f'<line x1="{px+22:.0f}" y1="82" x2="{px-22:.0f}" y2="102" '
                       f'stroke="#7a2f22" stroke-width="2.6"/>')
        out.append(f'<text class="hm-dialname" x="{px:.0f}" y="200" text-anchor="middle" '
                   f'fill="{flag}">{esc(s["th"])}</text>')
        # Four columns of 190px. Everything below the name has to wrap or it
        # runs into the neighbour — "mo nin lak ni — the pot has stolen away"
        # is 38 characters and overlapped BOTH its neighbours before this.
        out.append(f'<text class="hm-dialsub" x="{px:.0f}" y="217" text-anchor="middle">'
                   f'{esc(s["rtgs"])}</text>')
        out.append(f'<text class="hm-dialsub" x="{px:.0f}" y="231" text-anchor="middle">'
                   f'{esc(s["en"])}</text>')
        for j, ln in enumerate(_wrap(s["do_th"], 16, 2)):
            out.append(f'<text class="hm-dialsub" x="{px:.0f}" y="{256 + j * 15}" '
                       f'text-anchor="middle">{esc(ln)}</text>')
        for j, ln in enumerate(_wrap(s["do_en"], 24, 3)):
            out.append(f'<text class="hm-dialsub" x="{px:.0f}" y="{292 + j * 14}" '
                       f'text-anchor="middle">{esc(ln)}</text>')
        if i:
            out.append(f'<line x1="{x0:.0f}" y1="40" x2="{x0:.0f}" y2="330" '
                       f'stroke="var(--warm-border)" stroke-width="1"/>')
    out.append(f'<text class="hm-maplabel" x="{W/2:.0f}" y="28" text-anchor="middle">'
               f'{esc("ดูหน้าหม้อแล้วรู้ — โพนปลวกคือสัญญาณว่าหม้อเป็น")}</text>')
    label = bi_text(
        "หน้าหม้อสี่แบบ อ่านจากฟองบนผิวน้ำ — เป็น หิว ลักหนี ตาย",
        "Four readings taken off the surface of an indigo vat: alive, hungry, fled, dead.")
    return (f'<svg role="img" aria-label="{esc(label)}" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(out) + "</svg>")


def _timeline_svg(reg, esc, bi_text):
    """One spine, true to scale in years, so the 1878–1897 chemistry and the
    1950–1975 orthography sit where they belong instead of being spaced evenly
    for tidiness. The nineteenth-century gap IS the story: nothing between the
    march and the German laboratory."""
    ev = reg["timeline"]
    W, H = 760, 250
    PAD_L, PAD_R = 58, 34
    y0, y1 = ev[0]["year"], ev[-1]["year"]
    span = max(y1 - y0, 1)
    spine = 150

    def X(yr):
        return PAD_L + (yr - y0) / span * (W - PAD_L - PAD_R)

    out = [f'<line class="hm-spine" x1="{PAD_L}" y1="{spine}" x2="{W - PAD_R}" y2="{spine}"/>']
    for d in range(1840, 2021, 20):
        x = X(d)
        out.append(f'<line x1="{x:.1f}" y1="{spine - 4}" x2="{x:.1f}" y2="{spine + 4}" '
                   f'stroke="var(--warm-border)" stroke-width="1"/>')
        if d % 40 == 0:
            out.append(f'<text class="hm-mapnote" x="{x:.1f}" y="{spine + 20}" '
                       f'text-anchor="middle">{d}</text>')
    # Labels alternate above and below so neighbouring years do not collide.
    for i, e in enumerate(ev):
        x = X(e["year"])
        up = (i % 2 == 0)
        big = e["year"] in (1834, 1953, 2020)
        ty = spine - 26 if up else spine + 44
        out.append(f'<line x1="{x:.1f}" y1="{spine}" x2="{x:.1f}" '
                   f'y2="{ty + (12 if up else -14):.1f}" class="hm-arrow"/>')
        out.append(f'<circle class="hm-evdot{" big" if big else ""}" cx="{x:.1f}" '
                   f'cy="{spine}" r="{6 if big else 4.4}"/>')
        anchor = "middle"
        tx = x
        if x < PAD_L + 60:
            anchor, tx = "start", x - 6
        elif x > W - PAD_R - 60:
            anchor, tx = "end", x + 6
        out.append(f'<text class="hm-year" x="{tx:.1f}" y="{ty:.1f}" '
                   f'text-anchor="{anchor}">{e["year"]}</text>')
        short = {1834: "ไทพวน 17 ครอบครัว", 1878: "ไขโครงสร้าง", 1897: "BASF",
                 1950: "พจนานุกรม", 1953: "ขันโตก เชียงใหม่", 1975: "ราชบัณฑิต",
                 2005: "วิสาหกิจชุมชน", 2020: "GI แพร่"}.get(e["year"], "")
        out.append(f'<text class="hm-ev" x="{tx:.1f}" y="{ty + (-15 if up else 15):.1f}" '
                   f'text-anchor="{anchor}">{esc(short)}</text>')
    out.append(f'<text class="hm-mapnote" x="{PAD_L}" y="{H - 12}">'
               f'{esc("ตามมาตราส่วนปีจริง — ช่องว่างศตวรรษที่ 19 คือเรื่องราวเอง")}</text>')
    label = bi_text(
        "เส้นเวลาหม้อห้อม พ.ศ. 2377 ถึง 2563 วางตามมาตราส่วนปีจริง",
        "A mo hom timeline from 1834 to 2020, spaced to true year scale.")
    return (f'<svg role="img" aria-label="{esc(label)}" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(out) + "</svg>")


def _week_svg(reg, esc, bi_text):
    """Two weekday colour lists that do DIFFERENT JOBS, drawn so nobody reads them
    as before-and-after.

    An earlier version of this figure captioned them "the modern scheme" and "the
    corpus's manual" and pointed at Tuesday as evidence the scheme had drifted.
    That was wrong, and a reader who wears these colours caught it immediately:
    สวัสดิรักษา's list opens "อนึ่งภูษาผ้าทรงณรงค์รบ" — the cloth worn GOING INTO
    BATTLE — and applies whatever day you were born on. Setting it against the
    everyday auspicious colours is comparing a helmet with a shirt. Both trace to
    the same มหาทักษา root; neither is the other's ancestor, and this figure no
    longer implies one.

    So the rows are labelled by PURPOSE, the axis label says so, and the two days
    that agree (Sunday, and Saturday at its dark end) are left to speak for
    themselves rather than being marked as survivals.
    """
    days = reg["week"]["days"]
    W = 760
    cw = W / len(days)
    H = 282
    out = []
    out.append(f'<text class="hm-maplabel" x="14" y="22">'
               f'{esc("สีวัน สองรายการ คนละหน้าที่กัน")}</text>')
    _sub = "two lists of weekday colours — one for any day, one for going into battle"
    out.append(f'<text class="hm-mapnote" x="14" y="38">{esc(_sub)}</text>')
    for i, d in enumerate(days):
        x = i * cw
        cx = x + cw / 2
        if d["cloth"]:
            out.append(f'<rect x="{x + 3:.0f}" y="52" width="{cw - 6:.0f}" '
                       f'height="{H - 82:.0f}" rx="9" fill="#26418f" opacity=".07"/>')
        out.append(f'<text class="hm-dialname" x="{cx:.0f}" y="70" text-anchor="middle" '
                   f'fill="var(--ink)">{esc(d["th"])}</text>')
        out.append(f'<text class="hm-mapnote" x="{cx:.0f}" y="85" text-anchor="middle">'
                   f'{esc(d["en"])}</text>')
        for key, top in (("day", 96), ("war", 168)):
            out.append(f'<rect x="{cx - 26:.0f}" y="{top}" width="52" height="34" rx="7" '
                       f'fill="{d[key]}" stroke="var(--warm-border)"/>')
            for j, ln in enumerate(_wrap(d[key + "_th"], 12, 2)):
                out.append(f'<text class="hm-dialsub" x="{cx:.0f}" y="{top + 49 + j * 14}" '
                           f'text-anchor="middle">{esc(ln)}</text>')
        if d["cloth"]:
            out.append(f'<text class="hm-mapnote" x="{cx:.0f}" y="{H - 10}" '
                       f'text-anchor="middle" fill="#26418f">{esc("วันผ้าไทย")}</text>')
    out.append(f'<text class="hm-mapnote" x="14" y="118">{esc("วันธรรมดา")}</text>')
    out.append(f'<text class="hm-mapnote" x="14" y="132">{esc("everyday")}</text>')
    out.append(f'<text class="hm-mapnote" x="14" y="190">{esc("ณรงค์รบ")}</text>')
    out.append(f'<text class="hm-mapnote" x="14" y="204">{esc("battle dress")}</text>')
    label = bi_text(
        "สีประจำวันแบบที่ใช้กันทุกวันนี้ เทียบกับสีผ้าทรงณรงค์รบในสวัสดิรักษา "
        "สองรายการนี้ทำคนละหน้าที่ ไม่ใช่ของเก่ากับของใหม่ "
        "ช่องที่มีพื้นสีคือวันอังคารกับวันศุกร์ ซึ่งเป็นวันผ้าไทยตามมติ ครม.",
        "The everyday weekday colours compared with the battle-dress colours in Sawatdirak. "
        "These are two lists with two purposes, not an old one and a new one. The tinted "
        "columns are Tuesday and Friday, the two Thai-cloth days named by the cabinet "
        "resolution.")
    return (f'<svg role="img" aria-label="{esc(label)}" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(out) + "</svg>")


# ────────────────────────────────────────────────────────────────── the page

def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")
    verdict, BROKEN = g["verdict"], g["BROKEN"]

    reg = json.loads((ROOT / "data" / "curated" / "hom.json").read_text())

    def out_a(url, label):
        """Same rule as the souvenir and ADHD layers: a source that has stopped
        answering keeps its place and its address and stops being a door."""
        url = (url or "").strip()
        if url and verdict(url).get("status") not in BROKEN:
            return f'<a href="{att(url)}" rel="noopener">{label}</a>'
        return f'<span class="sv-dead" title="{att(url)}">{label}</span>'

    def cite(key):
        s = reg["sources"].get(key) or {}
        return (' <span class="hm-src">'
                + out_a(s.get("ref"), "[" + esc(s.get("note", key)[:46]) + "]")
                + "</span>")

    # ── the census, taken live. Three numbers: how many craft shops the
    #    directory holds, how many of them say the word, and how many places
    #    are named for the plant. The middle one is expected to be zero and
    #    the page is written around it being zero — but it is MEASURED, so the
    #    day a sign is caught the sentence corrects itself.
    n_records = sum(len(data.get(p, [])) for p in ("cm", "cr"))
    n_craft = n_saysit = 0
    creeks, named, creek_seen = [], [], set()
    n_named_rows = 0
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            blob = " ".join(str(v) for v in
                            (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)
            if any(s in CRAFT_SUBS for s in (r.get("sub") or [])):
                n_craft += 1
                if SHOP_NAME_RX.search(blob):
                    n_saysit += 1
            hit = HOM_NAME_RX.search(blob)
            if hit:
                n_named_rows += 1
                amph = AMPHOE_RX.search(str(r.get("address") or ""))
                # A record with no parseable address must not invent a fifth
                # place: if this province already knows this toponym, it IS
                # that one. บ้านเด่นฮ่อม arrived twice, once addressed to
                # Samoeng and once bare, and keying on (toponym, province)
                # alone counted Samoeng twice.
                if not amph:
                    if any(k[0] == hit.group(0) and k[2] == prov for k in creek_seen):
                        continue
                key = (hit.group(0), amph.group(1) if amph else "", prov)
                if key in creek_seen:
                    continue
                creek_seen.add(key)
                nm = hit.group(0) + (" — อ." + key[1] if amph else "")
                named.append(nm)
                # Only the ones the directory can actually put somewhere go on
                # the map. A record with no coordinates is still a name that
                # carries the plant, so it counts in the sentence and not in
                # the drawing — the same split the hot-spring map makes.
                if r.get("lat") and r.get("lng"):
                    creeks.append({"th": nm, "en": r.get("nameEn") or "",
                                   "lat": float(r["lat"]), "lng": float(r["lng"]),
                                   "prov": prov})

    B = []
    B.append('<div class="hm-wrap">')
    B.append("<h1>" + bi("หม้อห้อม — ต้นไม้ หม้อ เสื้อ",
                         "Mo hom — plant, pot, shirt") + "</h1>")
    B.append("<p class=lead>" + bi(
        "เสื้อสีน้ำเงินเข้มที่ใคร ๆ ก็รู้ว่าเป็นของเหนือ ทำจากใบไม้ที่ไม่มีสีน้ำเงินอยู่เลย "
        "และหม้อที่ต้องให้อาหารทุกวันไม่งั้นมันตาย หน้านี้ไม่ใช่รายชื่อร้าน — "
        "เป็นวิธีดูของจริง กับที่อยู่ของหม้อ ซึ่งอยู่ที่แพร่ ไม่ได้อยู่เชียงใหม่",
        "The dark blue shirt everyone reads as northern is made from a leaf with no blue in it, "
        "in a pot that has to be fed daily or it dies. This is not a list of shops. "
        "It is how to tell a real one, and where the pot actually is — which is Phrae, "
        "not Chiang Mai.") + "</p>")

    # ── the zero, stated first
    B.append('<div class="hm-count">')
    B.append("<p>" + bi(
        f"ในสารบัญนี้มีร้านหัตถกรรมและร้านตัดเย็บ <b>{n_craft:,}</b> ร้าน "
        f"ที่มีคำว่าห้อมหรือย้อมครามอยู่ในชื่อ: <b>{n_saysit}</b>",
        f"The directory holds <b>{n_craft:,}</b> craft and tailoring shops across "
        f"Chiang Mai and Chiang Rai. Number with ห้อม or ย้อมคราม in the name: "
        f"<b>{n_saysit}</b>.", raw=True) + "</p>")
    B.append("<p>" + bi(
        "นั่นไม่ใช่ช่องโหว่ของการเก็บข้อมูล — เสื้อหม้อห้อมขายเป็น “เสื้อ” "
        "ไม่มีร้านไหนต้องเขียนว่าห้อมบนป้าย คนซื้อรู้อยู่แล้ว "
        "สิ่งที่แผนที่เก็บไว้จริง ๆ คือชื่อของต้นไม้",
        "That is not a gap in the crawl. The shirt is sold as a shirt: no shop has to "
        "write the word, because the buyer already knows it. What the map does keep "
        "is the name of the plant.") + "</p>")
    if named:
        _pinned = (f" — {len(creeks)} of them have coordinates and are on the map below"
                   if len(creeks) != len(named) else "")
        B.append("<p>" + bi(
            f"มีสถานที่ในเชียงใหม่-เชียงรายที่ชื่อมีคำว่าห้อม/ฮ่อม อยู่ <b>{len(named)}</b> แห่ง: "
            + esc(" · ".join(named)),
            f"<b>{len(named)}</b> places in Chiang Mai and Chiang Rai carry the plant in "
            f"their own names, on {n_named_rows} records — Indigo Creek, in valleys that do "
            f"not touch{_pinned}.",
            raw=True) + "</p>")
    B.append("</div>")

    # ── FIGURE 1 · the map
    B.append('<h2 id="map">' + bi("แผนที่ — ห้อมมาจากไหน",
                                  "Where the blue came from") + "</h2>")
    B.append('<div class="hm-fig">' + _map_svg(reg, creeks, esc, bi_text) + "</div>")
    B.append('<p class="hm-figcap">' + bi(
        "เส้นประคือทางที่ชาวไทพวนถูกโยกย้ายลงมา — เชียงขวาง (ลาว) → น่าน พ.ศ. 2377 → "
        "ทุ่งโฮ้ง แพร่ · หมุดทองคือหม้อ · วงกลมโปร่งคือลำห้วยที่ชื่อว่าห้อม",
        "The dashed line is the march: Xieng Khouang in Laos, into Nan in 1834, then Phrae. "
        "The gold pin is the pot. The hollow rings are watercourses in this directory whose "
        "names carry the plant — read as the plant, on the northern ห้วย + plant pattern, "
        "and not proved.") + "</p>")

    pot = next(p for p in reg["route"] if p["key"] == "thunghong")
    B.append("<p>" + bi(pot["note_th"], pot["note_en"]) + cite("sac") + "</p>")

    # ── the two plants
    B.append('<h2 id="plants">' + bi("ห้อม ไม่ใช่ คราม", "ห้อม is not คราม") + "</h2>")
    B.append('<div class="hm-grid">')
    for pl in reg["plants"]:
        B.append('<div class="hm-card">')
        B.append(f'<h3>{esc(pl["th"])} <span class="hm-src">{esc(pl["rtgs"])}</span></h3>')
        B.append(f'<p><i>{esc(pl["latin"])}</i>'
                 + (f'<br><span class="hm-src">= {esc(pl["syn"])}</span>' if pl["syn"] else "")
                 + "</p>")
        B.append("<p>" + bi(pl["family_th"], pl["family_en"]) + "</p>")
        B.append("<p>" + bi(pl["where_th"], pl["where_en"]) + "</p>")
        B.append("<p>" + bi(pl["also_th"], pl["also_en"]) + "</p>")
        B.append('<p class="hm-src">'
                 + " ".join(out_a(s["ref"], "[" + str(i + 1) + "]")
                            for i, s in enumerate(pl.get("sources") or [])) + "</p>")
        B.append("</div>")
    B.append("</div>")

    # ── FIGURE 2 · the cycle
    B.append('<h2 id="cycle">' + bi("ใบไม้ไม่มีสีน้ำเงิน",
                                    "There is no blue in the leaf") + "</h2>")
    B.append("<p>" + bi(
        "ในใบห้อมไม่มีเม็ดสีน้ำเงินอยู่เลย มีแต่ “อินดิแคน” ที่ไม่มีสี "
        "สีน้ำเงินต้องถูกสร้างขึ้นสามจังหวะ และช่างย้อมทำครบทั้งสามโดยไม่ต้องเรียกชื่อมันสักครั้ง",
        "There is no blue pigment in the leaf. There is indican, which is colourless. "
        "The blue has to be manufactured in three moves — hydrolysis, oxidation, reduction — "
        "and a dyer performs all three without naming any of them.") + "</p>")
    B.append('<div class="hm-fig">' + _cycle_svg(reg, esc, bi_text) + "</div>")
    B.append('<p class="hm-figcap">' + bi(
        "จุดแต่ละจุดทาสีตามสีจริงของน้ำย้อมในขั้นนั้น สังเกตขั้นที่ 5: "
        "ผ้าออกจากหม้อเป็นสีเหลืองแกมเขียว แล้วเปลี่ยนเป็นน้ำเงินตอนโดนลม",
        "Each node is painted the colour the liquor really is. Look at step 5: the cloth "
        "leaves the vat yellow-green. It goes blue in the air, in your hands. That moment is "
        "the only step in textile practice that looks like magic and is not.") + "</p>")
    B.append("<ol>")
    for s in reg["cycle"]:
        B.append("<li><b>" + bi(s["th"], s["en"]) + "</b><br>"
                 + bi(s["what_th"], s["what_en"]) + "</li>")
    B.append("</ol>" + "<p>" + cite("ubu") + "</p>")

    # ── FIGURE 3 · the dial
    B.append('<h2 id="pot">' + bi("หม้อมีชีวิต และมันหิว",
                                  "The pot is alive, and hungry") + "</h2>")
    B.append("<p>" + bi(
        "หม้อย้อมคือแบคทีเรียที่ยังมีชีวิต มันกิน มันหิว และมันตายได้ "
        "คำที่ช่างย้อมใช้เรียกอาการของหม้อจึงไม่ใช่คำเปรียบ แต่เป็นการวินิจฉัย",
        "A reduction vat is a live microbial culture with an appetite and a death. "
        "The words Thai dyers use for its states are not metaphor — they are a diagnosis, "
        "and the reading is taken off the foam on the surface.") + "</p>")
    B.append('<div class="hm-fig">' + _dial_svg(reg, esc, bi_text) + "</div>")
    B.append('<div class="hm-grid">')
    for s in reg["pot_states"]:
        B.append('<div class="hm-card">')
        B.append(f'<h3>{esc(s["th"])} <span class="hm-src">{esc(s["rtgs"])} — '
                 f'{esc(s["en"])}</span></h3>')
        B.append("<p>" + bi(s["sign_th"], s["sign_en"]) + "</p>")
        B.append("<p><b>" + bi(s["do_th"], s["do_en"]) + "</b></p>")
        B.append("</div>")
    B.append("</div>")
    B.append("<p>" + bi(
        "คำเหล่านี้บันทึกจากช่างย้อมที่อุบลราชธานี ไม่ใช่คำเมือง "
        "แต่หม้อห้อมทางเหนือทำงานแบบเดียวกัน",
        "This vocabulary was recorded from dyers in Ubon Ratchathani, not in the north — "
        "the page does not pretend otherwise. It is here because it is the fullest written "
        "record of the practice in Thai, and the northern pot is worked the same way.")
        + cite("ubu") + "</p>")

    # ── the test
    B.append('<h2 id="tell">' + bi("ข้อบกพร่องคือหลักฐาน",
                                   "The flaw is the proof") + "</h2>")
    B.append("<p>" + bi(
        "ผ้าย้อมครามแท้ “สีตก” และ “ซีด” ซึ่งคนซื้อมักคิดว่าเป็นข้อเสีย "
        "แต่นั่นคือสิ่งที่บอกว่ามันเคยอยู่ในหม้อ ผ้าที่สีไม่ตกเลยคือผ้าพิมพ์",
        "Real indigo crocks and fades, which a buyer reads as a defect. It is the opposite: "
        "it is what tells you the cloth was in a pot. A shirt whose colour never moves was "
        "printed.") + "</p>")
    B.append('<ul class="hm-tests">')
    for t in reg["tests"]:
        cls = " class=printed" if t["verdict"] == "printed" else ""
        lab = bi_text("ของจริง", "real") if t["verdict"] == "real" \
            else bi_text("ผ้าพิมพ์", "printed")
        B.append(f"<li{cls}>"
                 f'<span class="tlab">{esc(lab)}</span><br>'
                 + "<b>" + bi(t["th"], t["en"]) + "</b>"
                 + (("<br>" + bi(t["note_th"], t["note_en"])) if t["note_en"] else "")
                 + "</li>")
    B.append("</ul>")

    # ── the Vinaya panel: why the peasant colour is the peasant colour
    B.append('<h2 id="robe">' + bi("สีเดียวที่พระห่มไม่ได้",
                                   "The colour a monk may not wear") + "</h2>")
    B.append("<p>" + bi(
        "พระวินัยอนุญาตสีย้อมหกอย่าง — ราก แก่น เปลือก ใบ ดอก ผล — "
        "แล้วห้ามจีวรที่ย้อมสีล้วนเจ็ดสี สีแรกในรายการคือ นิล คือสีคราม",
        "The Vinaya allows six classes of dye — root, stem, bark, leaf, flower, fruit "
        "(Mv.VIII.10.1) — and then forbids a robe dyed entirely in any of seven colours "
        "(Mv.VIII.29). The first on the list is nīla: indigo.") + cite("bmc") + "</p>")
    B.append('<ul class="hm-vin">')
    for pali, th, hexv, hit in VINAYA:
        B.append(f'<li class="{"hit" if hit else "no"}">'
                 f'<span class="hm-swatch" style="background:{hexv}"></span>'
                 f'{esc(pali)} · {esc(th)}</li>')
    B.append("</ul>")
    B.append("<p>" + bi(
        "หมู่บ้านกับวัดที่อยู่ห่างกันห้าสิบเมตร ย้อมผ้าด้วยน้ำเดียวกันและต้นไม้เดียวกัน "
        "แต่ได้สีตรงข้ามกัน เพราะข้อความเดียวกัน — และหม้อของชาวบ้านในภาษาอีสาน "
        "ก็ชื่อ “หม้อนิล” ตรงกับคำบาลีที่ห้ามไว้พอดี",
        "A village and a monastery fifty metres apart, dyeing in the same water with the same "
        "plants, arrive at opposite colours out of one text. And the layman's vat, in the "
        "dialect with least Pali in it, is called หม้อนิล — the nīla pot, named with the very "
        "word. The blue shirt is not indifferent to the robe: it is the robe's complement. "
        "The manuscript evidence is on the sibling site.") + "</p>")
    B.append("<p>" + bi(
        "และ “นิล” ยังเป็นชื่อพลอยของพระเสาร์ในนพรัตน์ด้วย — สีนี้เป็นสีของดาว ไม่ใช่แค่สีผ้า",
        "And นิล is also the name of Saturn's stone in the นพรัตน์, the nine gems. "
        "This is a planetary colour before it is a fabric colour — which is the long "
        "version, on the sibling site.") + "</p>")
    B.append("<p>" + bi("อ่านต่อที่ wichaa — ในใบลานมีเรื่องผ้า 37 ฉบับ และไม่มีฉบับไหนพูดถึงสี",
                        "Read it on wichaa: the palm leaf holds 37 witnesses about cloth "
                        "and not one about colour", raw=True)
             + ' — <a href="https://wichaa.net/a/entity_hom/" rel="noopener">'
             + esc("wichaa.net/a/entity_hom/") + "</a>.</p>")

    # ── why Friday. The question everybody in this city actually asks, and the
    #    answer is a cabinet resolution, not a tradition — with a coincidence
    #    sitting on top of it that will become the reason people give.
    B.append('<h2 id="friday">' + bi("ทำไมต้องวันศุกร์", "Why Friday") + "</h2>")
    fr = reg["friday"]
    B.append("<p>" + bi(fr["policy_th"], fr["policy_en"]) + cite("crm2563") + "</p>")
    B.append("<p>" + bi(fr["isan_th"], fr["isan_en"]) + cite("sakon") + "</p>")
    B.append('<div class="hm-fig">' + _week_svg(reg, esc, bi_text) + "</div>")
    B.append('<p class="hm-figcap">' + bi(
        "แถวบนคือสีประจำวันที่คนใส่กันจริง ๆ แถวล่างคือสีผ้าทรง “ณรงค์รบ” ในสวัสดิรักษา "
        "ซึ่งใส่ตอนออกศึก ไม่เกี่ยวกับวันเกิด · สองรายการนี้คนละหน้าที่ ไม่ใช่ของเก่ากับของใหม่ "
        "· ช่องที่มีพื้นสีคือวันผ้าไทยตามมติ ครม.",
        "Top row: the everyday weekday colours — the ones people actually wear. Bottom row: "
        "the battle-dress colours in Sawatdirak, worn going into a fight and applying whatever "
        "day you were born on. Two lists, two purposes — not an old one and a new one. Both "
        "trace to the same มหาทักษา root and they land differently, and nothing here says "
        "which came first. The tinted columns are the two Thai-cloth days.") + "</p>")
    B.append("<p>" + bi(fr["colour_th"], fr["colour_en"]) + cite("sicolour") + "</p>")
    B.append('<p class="hm-note">' + bi(fr["caveat_th"], fr["caveat_en"]) + "</p>")

    # ── what it protects against. Three answers that do not agree, kept apart —
    #    and the third one is a CORRECTION of the other two, which is why it is
    #    on the page at all.
    B.append('<h2 id="protect">' + bi("ครามกันอะไรได้บ้าง",
                                      "What indigo actually protects against") + "</h2>")
    B.append("<p>" + bi(
        "ถามว่าครามกันอะไร จะได้คำตอบสามชุดที่ไม่ตรงกัน — และชุดที่สามค้านสองชุดแรก "
        "หน้านี้จึงแยกไว้คนละกล่อง ไม่รวบเป็นเรื่องเดียว",
        "Ask what indigo wards off and the answer comes in three registers that do not "
        "agree with each other. The third contradicts the first two, so they are kept "
        "apart here rather than folded into one story.") + "</p>")
    B.append('<div class="hm-grid">')
    for pr in reg["protection"]:
        B.append('<div class="hm-card">')
        B.append("<h3>" + bi(pr["label_th"], pr["label_en"]) + "</h3>")
        B.append("<p>" + bi(pr["th"], pr["en"]) + "</p>")
        B.append("<p>" + bi(pr["use_th"], pr["use_en"]) + "</p>")
        B.append("</div>")
    B.append("</div>")
    B.append('<p class="hm-src">' + out_a(reg["sources"]["aizome"]["ref"], "[aizome]")
             + " " + out_a(reg["sources"]["prachiat"]["ref"], "[ประเจียด]") + "</p>")

    # ── FIGURE 4 · the timeline
    B.append('<h2 id="when">' + bi("เส้นเวลา", "The timeline") + "</h2>")
    B.append('<div class="hm-fig">' + _timeline_svg(reg, esc, bi_text) + "</div>")
    B.append('<p class="hm-figcap">' + bi(
        "วางตามมาตราส่วนปีจริง ไม่ได้เกลี่ยให้เท่ากัน — ช่องว่างยาว ๆ ระหว่าง พ.ศ. 2377 "
        "กับห้องแล็บที่เยอรมนีคือส่วนหนึ่งของเรื่อง",
        "Spaced to true year scale rather than evenly. The long empty stretch between the "
        "march of 1834 and a German laboratory is part of the story.") + "</p>")
    B.append("<ol>")
    for e in reg["timeline"]:
        B.append(f'<li><b>{e["year"]}</b> <span class="hm-src">'
                 f'· พ.ศ. {e["be"]}</span><br>' + bi(e["th"], e["en"])
                 + cite(e["src"]) + "</li>")
    B.append("</ol>")

    # ── the walk
    B.append('<h2 id="go">' + bi("หม้ออยู่ที่แพร่", "The pot is in Phrae") + "</h2>")
    gt = reg["getting_there"]
    B.append("<p>" + bi(gt["th"], gt["en"]) + "</p>")
    B.append("<p>" + bi(
        "เชียงใหม่เป็นที่ที่เสื้อกลายเป็นเครื่องแบบ ไม่ใช่ที่ที่มันถูกทำ — "
        "และนั่นมีวันที่กำกับ พ.ศ. 2496",
        "Chiang Mai is where the shirt became a uniform, not where it is made — "
        "and that has a date on it: 1953.") + cite("cmnews") + "</p>")

    B.append('<p class="hm-note">' + bi(
        "ทุกตัวเลขในหน้านี้นับสดจากสารบัญตอนสร้างหน้า ไม่มีราคาใดในหน้านี้ที่เดินไปดูมาแล้ว "
        "และไม่มีร้านไหนถูกแนะนำ",
        "Every count on this page is measured live from the directory at build time. "
        "No price here has been walked, and no shop is recommended.") + "</p>")
    B.append('<p class="hm-note">')
    for u in reg.get("unverified", []):
        B.append("· " + esc(u) + "<br>")
    B.append("</p>")

    B.append(share_block(BASE + "hom.html",
                         "หม้อห้อม · Mo hom — indigo",
                         card=(shelf_og("hom") if shelf_og else None)))
    B.append("</div>")

    (DOCS / "hom.css").write_text(CSS)
    (DOCS / "hom.html").write_text(page(
        "หม้อห้อม · Mo hom — indigo",
        "".join(B), 0,
        path="hom.html",
        desc="หม้อห้อม ม่อฮ่อม — ต้นห้อมกับต้นคราม วิธีดูผ้าย้อมครามแท้ หม้อย้อมที่มีชีวิต "
             "และเส้นทางจากเชียงขวางถึงทุ่งโฮ้ง แพร่ · Mo hom indigo: which plant, how to "
             "tell a real one (it crocks), the living vat, and the road from Xieng Khouang "
             "to Ban Thung Hong.",
        extra_head='<link rel=stylesheet href="hom.css">'))
    return (f"{len(reg['timeline'])} dated rows · {n_craft} craft shops, "
            f"{n_saysit} saying the word · {len(named)} places named for the plant, {len(creeks)} mappable")
