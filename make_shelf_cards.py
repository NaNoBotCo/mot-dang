#!/usr/bin/env python3
"""Shelf share cards — assets/og/shelf-<prov>[-<cat>[-<sub>]].png, 1200x630.

A reader asked where in Chiang Mai does the glove scrub, and the answer was
five shops. Posting that answer meant posting five links, or one link that
unfurled as the generic brand card and said nothing. Every per-place card we
own (make_og_cards.py) answers "what is this place"; nothing answered the
question people actually ask each other, which is "who does THIS".

So: one card per shelf. A sub-shelf card names the places on it — ขัดขี้ไคล
becomes a poster with five names on it. A category card lists its sub-shelves
with their counts, because that is what a category page is (the Yahoo genre
row, in a picture). A province card lists its categories. Between them every
list page on the site now unfurls as its own list.

Same method as make_og_cards.py and for the same reason: Pillow here has no
raqm, so Thai marks land in the wrong places — the card is HTML and a headless
Chrome takes the picture. This file borrows that file's Chrome lookup, its
crop-and-quantize, and its glyphs rather than owning a second copy.

Shelf membership changes with every import, so each card carries a signature —
the shelf's title, its count, and the rows drawn on it — in
`assets/og/_shelf-index.json`. A re-run redraws only the shelves whose picture
would actually differ, which makes this cheap enough to run on every build:

    python3 make_shelf_cards.py            # only what changed
    python3 make_shelf_cards.py --force    # everything
    python3 make_shelf_cards.py --only massage
    python3 make_shelf_cards.py --list     # what would be drawn, no Chrome

Reader questions (`data/asked.json`) draw here too, as `asked-<key>.png` —
the question is the headline, the places it stands on are the rows, and a
candid gap says so on the panel instead of pretending to a list. Same
template on purpose: a question IS a shelf, one that a reader named before
the catalogue did.

Run it BEFORE build.py: build.py copies assets/og/ into docs/og/ and points
each shelf page's og:image at its own card. Anything missing falls back to the
brand card, so the site never waits on this script.

Needs python3.13 (build.py is imported for the shelving rules, and does not
parse under the 3.9 on the system path).
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from make_og_cards import CAT_GLYPH, SHOT_H, crop, esc, find_chrome, where_line

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "og"
INDEX = OUT / "_shelf-index.json"

# Bump when a change here alters what a card looks like; every card redraws.
DESIGN_STAMP = "2026-08-19 10:00"      # the shelf card

ROWS = 5                # names on a sub-shelf card, before "+ N more"
CAT_ROWS = 8            # sub-shelves on a category card: they are one line each
PANEL_W = 520           # the list panel, full-bleed down the right-hand edge

TEMPLATE = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF6EE;color:#2A1E16;
font-family:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Arial Unicode MS",
 "Helvetica Neue",Arial,sans-serif;position:relative}}
.rule{{position:absolute;left:60px;right:{text_r}px;height:5px;
border-top:5px solid #C2401C;border-bottom:5px solid #C2401C;box-sizing:content-box}}
.rule.t{{top:44px}} .rule.b{{top:571px}}
.mid{{position:absolute;left:60px;right:{text_r}px;top:110px;bottom:190px;
display:flex;flex-direction:column;justify-content:center}}
.bot{{position:absolute;left:60px;right:{text_r}px;bottom:80px}}
.top{{display:flex;align-items:center;gap:16px;font-size:26px;color:#8F2E13}}
.glyph{{font-size:40px;line-height:1}}
.name{{font-size:{size}px;line-height:1.12;font-weight:700;margin:12px 0 0;
max-height:230px;overflow:hidden}}
.en{{font-size:{en_size}px;color:#6B5A48;margin-top:10px;line-height:1.2;
max-height:{en_max}px;overflow:hidden}}
/* The count is the card's second claim after the name: not "we have a page
   about scrubs" but "there are five of them and here they are". */
.count{{margin-top:20px;font-size:34px;font-weight:700;color:#C2401C}}
.count small{{font-size:24px;font-weight:400;color:#6B5A48;margin-left:10px}}
.trail{{height:2px;margin:0 0 18px;
background:repeating-linear-gradient(90deg,#8F2E13 0 4px,transparent 4px 20px);
opacity:.35}}
.foot{{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;
padding-bottom:14px}}
.url{{font-size:22px;color:#6B5A48;word-break:break-all;line-height:1.25}}
.brand{{text-align:right;font-size:32px;font-weight:700;color:#C2401C;
white-space:nowrap;line-height:1.15}}
.brand small{{display:block;font-size:20px;font-weight:400;color:#6B5A48;
letter-spacing:.06em}}
/* The list, full-bleed to three edges — same geometry as the map panel on a
   place card, so the two read as one family seen from different sides. */
.panel{{position:absolute;top:0;right:0;bottom:0;width:{panel_w}px;
background:#FFFCF6;border-left:3px solid #E4D8C4;
padding:52px 44px 44px 40px;display:flex;flex-direction:column}}
.rows{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:{gap}px}}
.row{{overflow:hidden}}
.row .n{{font-size:{row_size}px;font-weight:700;line-height:1.2;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.row .m{{font-size:{meta_size}px;color:#8F2E13;margin-top:3px;line-height:1.25;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.row .c{{color:#C2401C;font-weight:700}}
.more{{margin-top:20px;font-size:24px;color:#8F2E13;font-weight:700}}
.asked{{margin-top:10px;font-size:19px;color:#6B5A48;line-height:1.3}}
</style></head><body>
<div class="panel">
<div class="rows">{rows}</div>
{more}{note}
</div>
<div class="rule t"></div>
<div class="mid">
<div class="top"><span class="glyph">{glyph}</span><span>{eyebrow}</span></div>
<h1 class="name">{name}</h1>
<div class="en">{en}</div>
<div class="count">{n_th}<small>{n_en}</small></div>
</div>
<div class="bot">
<div class="trail"></div>
<div class="foot">
<div class="url">{url}</div>
<div class="brand">🐜 มดแดง<small>motdang.net</small></div>
</div>
</div>
<div class="rule b"></div>
</body></html>
"""


def name_size(name):
    """The headline steps down rather than spilling out of a 620px column."""
    n = len(name or "")
    return 76 if n <= 14 else 62 if n <= 24 else 50 if n <= 38 else 40


def en_size(en):
    """A shelf name in English is three words; a reader's question is a
    sentence. The first asked card clipped its own question mid-clause, so
    the English line steps down and gets a third line when it needs one."""
    n = len(en or "")
    size = 30 if n <= 40 else 24 if n <= 75 else 20
    lines = 2 if n <= 40 else 3
    return size, int(size * 1.2 * lines) + 2


def row_metrics(n):
    """Few rows are set larger. A shelf with two places on it should not look
    like a shelf with eight and a lot of cream."""
    if n <= 2:
        return 40, 24, 34
    if n <= 4:
        return 34, 21, 26
    if n <= 6:
        return 30, 20, 18
    return 26, 18, 12


PRICE_KEYS = ("priceHeard", "priceBoard")
BAHT = re.compile(r"([\d,]+)\s*บาท")
DUR = re.compile(r"([\d.]+\s*(?:ชม\.|ชั่วโมง|นาที))")


def short_price(s):
    """"ระเบิดขี้ไคล + สปาน้ำมัน รวม 1.5 ชม. 700 บาท" -> "700 บาท / 1.5 ชม."

    A price board sentence is written to be read standing in front of it; a
    card row is 430 px wide and truncates it mid-word, which reads as a
    cheaper number than it is. So the row carries the figures and nothing
    else — with two rules that exist because breaking either invents a price:

    A board with several tiers on it ("ขัดผิว 45 นาที 900 บาท · ขัดผิวทองคำ
    45 นาที 1,200 บาท · เสริมขัดผิว 60 นาที 700 บาท") becomes the spread,
    700–1,200 บาท, never one of its numbers welded to one of its durations —
    the first attempt here printed "700 บาท / 45 นาที", a rate that shop does
    not offer. A duration is carried only when the sentence holds exactly one
    price and one duration, so the pairing cannot be wrong.

    And โปรฯ stays, because a promotional rate printed as the standing rate is
    also a price we made up.
    """
    nums = [(int(x.replace(",", "")), x) for x in BAHT.findall(s)]
    if not nums:
        return s if len(s) <= 34 else s[:33] + "…"
    lo, hi = min(nums)[1], max(nums)[1]
    if lo != hi:
        return f"{lo}–{hi} บาท"
    durs = DUR.findall(s)
    out = f"{lo} บาท"
    if len(durs) == 1:
        out += f" / {durs[0].strip()}"
    if "โปร" in s:
        out += " (โปรฯ)"
    return out


def price_of(r):
    a = r.get("attrs") or {}
    for k in PRICE_KEYS:
        if a.get(k):
            return short_price(str(a[k])), bool(a.get("_pricesVerified"))
    return "", True


REAL_NAME = re.compile(r"[0-9A-Za-z\u0E01-\u0E2E]")


def best_five(records, rank, is_featured, name_of, limit):
    """Which places a card names when the shelf is bigger than the card.

    Not the page's own order. The page sorts alphabetically because a person
    browsing a shelf of 1,300 cafés needs to be able to find their way back to
    one; a card is a single claim about the shelf, and alphabetical order made
    that claim out of the five names that happen to start with punctuation and
    digits — the first draft of the café card led with a lone vowel mark.

    So: featured first (the site's own showcase), then by ant rank, which is
    already the site's word for how much we actually know about a place, then
    by name. A record whose name carries no letter at all is held back unless
    the shelf has nothing better, because a card is not the place to publish
    a name we clearly hold wrong.
    """
    good = [r for r in records if REAL_NAME.search(name_of(r) or "")]
    pool = good if len(good) >= min(limit, len(records)) else records
    return sorted(pool, key=lambda r: (not is_featured(r), -rank(r), name_of(r)))[:limit]


def place_rows(records, limit):
    """A place per row: its name, then where it is and what it costs.

    Price goes on the card when we hold one, because a price is the second
    thing anybody asks and a directory that hides it is a directory that
    wastes a phone call. An unwalked price
    is captioned as the shop's own quote under the panel.
    """
    rows, unverified = [], False
    for r in records:
        price, verified = price_of(r)
        if price and not verified:
            unverified = True
        meta = " · ".join(x for x in (where_line(r), price) if x)
        rows.append((r.get("name") or r.get("nameEn") or r["id"], meta, ""))
    return rows, unverified


def child_rows(children, limit):
    """A sub-shelf per row, with its count — the category page in a picture."""
    return [(th, "", f"{n:,}") for th, n in children[:limit]], False


def card_html(sh):
    n = len(sh["rows"])
    row_size, meta_size, gap = row_metrics(n)
    rows = "".join(
        '<div class="row"><div class="n">%s%s</div>%s</div>' % (
            esc(name),
            f' <span class="c">({count})</span>' if count else "",
            f'<div class="m">{esc(meta)}</div>' if meta else "")
        for name, meta, count in sh["rows"])
    # The overflow counts whatever the rows are. A province card whose rows
    # are categories saying "+ อีก 17 แห่ง" claims seventeen more PLACES in
    # Chiang Mai, which is off by eleven thousand.
    more_th, more_en = sh.get("more_unit", ("แห่ง", "more"))
    more = (f'<div class="more">+ อีก {sh["more"]:,} {more_th} · '
            f'{sh["more"]:,} {more_en}</div>' if sh["more"] else "")
    note = ('<div class="asked">ราคาตามที่ร้านบอก ยังไม่ได้เดินตรวจ<br>'
            'prices as quoted, not yet walked</div>') if sh["unverified"] else ""
    if sh.get("panel"):
        # a gap card: the panel says what the panel is, in place of a list
        note = f'<div class="more">{esc(sh["panel"][0])}</div>' \
               f'<div class="asked">{esc(sh["panel"][1])}</div>'
    es, em = en_size(sh["en"])
    return TEMPLATE.format(
        size=name_size(sh["th"]), en_size=es, en_max=em,
        glyph=sh["glyph"], eyebrow=esc(sh["eyebrow"]),
        name=esc(sh["th"]), en=esc(sh["en"]),
        n_th=f'{sh["n"]:,} แห่ง' if sh["n"] else "", n_en=esc(sh["n_en"]),
        rows=rows, more=more, note=note,
        url=esc(sh["url"]), panel_w=PANEL_W, text_r=PANEL_W + 60,
        row_size=row_size, meta_size=meta_size, gap=gap)


def shelves():
    """Every list page on the site, shelved exactly as build.py shelves it.

    Imported rather than reimplemented: a card that disagreed with its own
    page about who is on the shelf would be worse than no card.
    """
    sys.path.insert(0, str(ROOT))
    import build

    data = build.load()
    out = []
    for p in build.PROVINCES:
        key = p["key"]
        records = data[key]
        counts = {}
        for r in records:
            for c in r["cat"]:
                counts[c] = counts.get(c, 0) + 1
        live = [c for c in build.CAT_ORDER if counts.get(c)]

        # province: its categories, in the order the province page lists them
        prov_rows, _ = child_rows(
            [(build.CATS[c]["th"], counts[c]) for c in live], CAT_ROWS)
        out.append(dict(
            stem=f"shelf-{key}", glyph="🐜",
            eyebrow=f'มดแดง · {p["en"]}', th=p["th"], en=p["en"],
            n=len(records), n_en=f'places in {p["en"]}',
            url=f'motdang.net/{key}/',
            rows=prov_rows, unverified=False,
            more=max(0, len(live) - CAT_ROWS),
            more_unit=("หมวด", "more categories")))

        for c in live:
            cdef = build.CATS[c]
            in_cat = sorted([r for r in records if c in r["cat"]],
                            key=lambda r: (not build.is_featured(r), build.name_of(r)))
            kids = []
            for child in cdef.get("children", []):
                in_sub = [r for r in in_cat if build.matches(r, child.get("match"))]
                if not in_sub:
                    continue
                kids.append((child["th"], len(in_sub)))
                rows, unver = place_rows(best_five(
                    in_sub, build.ant_rank, build.is_featured, build.name_of, ROWS), ROWS)
                out.append(dict(
                    stem=f'shelf-{key}-{c}-{child["key"]}',
                    glyph=CAT_GLYPH.get(c, "🐜"),
                    eyebrow=f'{cdef["th"]} · {p["th"]}',
                    th=child["th"], en=child["en"],
                    n=len(in_sub), n_en=f'in {p["en"]}',
                    url=f'motdang.net/{key}/{c}/{child["key"]}/',
                    rows=rows, unverified=unver,
                    more=max(0, len(in_sub) - ROWS)))

            # a category with sub-shelves shows the sub-shelves; one without
            # them shows its places, because otherwise its card is empty
            if kids:
                rows, unver = child_rows(kids, CAT_ROWS)
                more = max(0, len(kids) - CAT_ROWS)
                unit = ("หมวดย่อย", "more shelves")
            else:
                rows, unver = place_rows(best_five(
                    in_cat, build.ant_rank, build.is_featured, build.name_of, ROWS), ROWS)
                more = max(0, len(in_cat) - ROWS)
                unit = ("แห่ง", "more")
            out.append(dict(
                stem=f"shelf-{key}-{c}", glyph=CAT_GLYPH.get(c, "🐜"),
                eyebrow=f'มดแดง · {p["th"]}', th=cdef["th"], en=cdef["en"],
                n=len(in_cat), n_en=f'in {p["en"]}',
                url=f'motdang.net/{key}/{c}/',
                rows=rows, unverified=unver, more=more, more_unit=unit))
    out += asked_shelves(build, data)
    return out


def asked_shelves(build, data):
    """One card per reader question, from the same selection the page uses."""
    import asked_layer
    out = []
    for e in asked_layer.load():
        if e.get("gap"):
            # A candid gap gets its page and its note, not a share card: a
            # poster that says "nobody does this" is the one card that would
            # travel further than the sentence under it. (Decision 2026-08-19.)
            continue
        shown, counts = asked_layer.select(e, data)
        rows, unver = place_rows(shown[:ROWS], ROWS)
        sh = dict(
            stem=f'asked-{e["key"]}', glyph="❓",
            eyebrow="ถามมด · Ask the ants",
            th=e["q"]["th"], en=e["q"]["en"],
            n=len(shown), n_en="places that answer it" if shown else "",
            url=f'motdang.net/asked/{e["key"]}.html',
            rows=rows, unverified=unver,
            more=max(0, len(shown) - ROWS), more_unit=("แห่ง", "more"))
        if e.get("gap"):
            pn = e.get("panel") or {"th": "ยังไม่มีในสารบัญ", "en": "not in the catalogue yet"}
            sh["panel"] = (pn["th"], pn["en"])
        out.append(sh)
    return out


def signature(sh):
    """What the picture depends on — nothing else. A shelf whose 900th place
    changed its address does not need a new card; a shelf whose count or whose
    named five changed does."""
    return hashlib.sha1(json.dumps(
        [DESIGN_STAMP, sh["th"], sh["en"], sh["eyebrow"], sh["n"], sh["url"],
         sh["more"], sh.get("more_unit"), sh["unverified"], sh["rows"]]
        # appended only when present, so adding this field did not invalidate
        # 231 cards that do not carry it
        + ([sh["panel"]] if sh.get("panel") else []),
        ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="redraw every card")
    ap.add_argument("--only", default="", help="substring match on the card name")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--list", action="store_true", help="print the shelves, draw nothing")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    seen = json.loads(INDEX.read_text()) if INDEX.exists() else {}
    all_shelves = shelves()
    if args.only:
        all_shelves = [s for s in all_shelves if args.only in s["stem"]]

    todo, index = [], {}
    for sh in all_shelves:
        sig = signature(sh)
        index[sh["stem"]] = sig
        dest = OUT / f'{sh["stem"]}.png'
        if args.force or seen.get(sh["stem"]) != sig or not dest.exists():
            todo.append((sh, dest))
    if args.limit:
        todo = todo[:args.limit]

    if args.list:
        for sh in all_shelves:
            print(f'{sh["stem"]:44} {sh["n"]:>6,}  {len(sh["rows"])} rows  {sh["th"]}')
        print(f'\n{len(all_shelves):,} shelves · {len(todo):,} would be drawn')
        return

    print(f'{len(todo):,} of {len(all_shelves):,} shelf card(s) to draw -> {OUT}')
    if todo:
        chrome = find_chrome()
        tmp = Path(tempfile.mkdtemp(prefix="shelfcards-"))
        for i, (sh, dest) in enumerate(todo, 1):
            src = tmp / "card.html"
            src.write_text(card_html(sh), encoding="utf-8")
            subprocess.run([
                chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                "--no-sandbox", "--force-device-scale-factor=1",
                "--window-size=1200,%d" % SHOT_H, "--screenshot=" + str(dest),
                src.as_uri()],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            crop(dest)
            if i % 25 == 0 or i == len(todo):
                print(f"  {i:,}/{len(todo):,}")
        shutil.rmtree(tmp, ignore_errors=True)

    # Written only after the run, so a run that stops half way redraws the
    # rest next time instead of recording work it did not do.
    drawn = {sh["stem"] for sh, _ in todo}
    INDEX.write_text(json.dumps(
        {k: v for k, v in index.items()
         if k in drawn or (seen.get(k) == v and (OUT / f"{k}.png").exists())},
        ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"stamped {datetime.datetime.now():%Y-%m-%d %H:%M} — "
          "now run build.py to copy them into docs/og/")


if __name__ == "__main__":
    main()
