#!/usr/bin/env python3
"""ถามมด — reader questions as DATA, and everything a question needs made
from that one record.

A reader asks something in a group that no shelf answers by name. What has to
exist afterwards, every time, is the same four things:

  1. the records — real places, in the canonical data, with dated sources
  2. an entry on asked.html, so the next person who asks finds it here
  3. a page and share card of its own, so the answer can be posted as ONE
     link (or one picture) instead of five links and a paragraph
  4. the text to paste into the group — made from the same data, so it
     never disagrees with the site and is remade, not retyped, when a
     price is walked

Until 2026-08-19 each question was a hand-built block of Python in this
file: five questions, five different shapes, and the reply that went back to
the reader was typed by hand and lived only in that thread. Now the question
lives in `data/asked.json` and this module is the one renderer:

  data/asked.json entry
    ├─ asked.html            card, in the order of the file
    ├─ asked/<key>.html      the page: same card, its own og:image, share row
    ├─ assets/og/asked-<key>.png    drawn by make_shelf_cards.py
    └─ make_post.py <key>    the reply, plain text, with both links

An entry is FOUND (a `find` selector over the canonical data — a shelf, a
facet, a name, explicit ids — rendered with entry_li() exactly like every
other list on the site) or a CANDID GAP (`gap: true`: what is missing, why,
and the concrete next step, said out loud instead of returning empty).

Prose stays in the data file, Thai canonical with EN as a display layer, and
may carry `{n}` `{phoned}` `{rest}` for the counts the selector produces, so
a sentence like "the catalogue holds {n}" stays true after the next import
without anybody editing it.

Shibari is the one entry that stays a gap on purpose even after a real lead
turned up: press coverage shows a rope-teaching scene has existed in Chiang
Mai, but the source was a single old, paywalled article naming one private
individual in a sensitive practice — not something this site will publish
without that person's own consent, no matter how citable. The practice
(add.html, self-submitted, no address required) is the correct path here,
not a name pulled from someone else's reporting.

As everywhere: no invented ratings, and silence is not dressed up
as "no". No map on these pages, so they fetch nothing at read time.

Entry point: emit(globals_of_build, data) — call after answers_layer.emit so
this page's stylesheet (answers.css) already exists on disk. `load()` and
`select()` are also imported by make_shelf_cards.py and make_post.py, so the
card and the reply are made from the same selection as the page.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASKED = ROOT / "data" / "asked.json"
DOCS = None


def load(include_drafts=False):
    """The questions. `draft: true` (set by asked_new.py) keeps an entry out of
    every renderer — no card on asked.html, no page, no share card, no reply —
    until somebody deletes the flag. That is the release valve for the walk:
    tests/test_asked.py is a hard gate, and a half-answered question must not
    hold the whole site's publish."""
    rows = json.loads(ASKED.read_text())["asked"]
    return rows if include_drafts else [e for e in rows if not e.get("draft")]


# ------------------------------------------------------------------ selection
def _name_has(r, needle):
    hay = ((r.get("name") or "") + " " + (r.get("nameEn") or "")).lower()
    return needle.lower() in hay


def _match(r, f):
    """One selector clause. All keys given must hold; `any` is a list of
    clauses of which one must hold. Kept deliberately small — a question
    that needs more than this needs a facet, not a cleverer selector."""
    a = r.get("attrs") or {}
    if "ids" in f and r["id"] not in f["ids"]:
        return False
    if "cat" in f and f["cat"] not in (r.get("cat") or []):
        return False
    if "sub" in f and f["sub"] not in (r.get("sub") or []):
        return False
    if "attr" in f and not a.get(f["attr"]):
        return False
    if "name" in f and not _name_has(r, f["name"]):
        return False
    if "any" in f and not any(_match(r, g) for g in f["any"]):
        return False
    return True


def select(entry, data):
    """The records an entry stands on, in the order the page shows them.

    Returns (shown, counts): `shown` is what gets listed; `counts` feeds the
    prose placeholders. `show: "phone"` lists only records with a number
    (the pap-smear card: a facility we cannot phone is not yet an answer).
    `first` pins ids to the top — the scrub card leads with the one shop
    that has evidence of a mitt, and that is a decision, not an accident of
    sort order.
    """
    f = entry.get("find")
    if not f or entry.get("gap"):
        return [], {"n": 0, "phoned": 0, "rest": 0}
    provs = [f["prov"]] if f.get("prov") else list(data)
    found = [r for p in provs for r in data[p] if _match(r, f)]
    phoned = [r for r in found if r.get("phone")]
    shown = phoned if entry.get("show") == "phone" else list(found)
    # phone-first, then the pinned ids in front — both stable sorts
    shown.sort(key=lambda r: 0 if r.get("phone") else 1)
    first = entry.get("first") or []
    shown.sort(key=lambda r: first.index(r["id"]) if r["id"] in first else len(first))
    return shown, {"n": len(found), "phoned": len(phoned), "rest": len(found) - len(phoned)}


def prov_of(r):
    return "cr" if r["id"].startswith("cr-") else "cm"


# ------------------------------------------------------------------ rendering
def _fill(s, counts):
    return s.format_map(counts) if "{" in s else s


def _para(g, p, counts, up):
    bi = g["bi"]
    cls = f' class="{p["cls"]}"' if p.get("cls") else ""
    links = " · ".join(
        f'<a href="{up}{l["href"]}">{bi(l["th"], l["en"])}</a>' for l in p.get("links", []))
    text = bi(_fill(p["th"], counts), _fill(p["en"], counts))
    return f"<p{cls}>{text}{' ' + links if links else ''}</p>"


def card_html(g, entry, data, depth=0, heading_link=True):
    """One question, one card. The same markup on asked.html (depth 0, where
    the title links to the question's own page) and on that page (depth 1,
    where it is the page)."""
    bi = g["bi"]
    up = "../" * depth
    shown, counts = select(entry, data)
    title = bi(entry["q"]["th"], entry["q"]["en"])
    if heading_link:
        title = f'<a href="{up}asked/{entry["key"]}.html">{title}</a>'
    lis = "".join(g["entry_li"](r, f'{up}{prov_of(r)}/p/{g["place_slug"](r)}.html')
                  for r in shown)
    return (
        f'<div class="qacard" id="{entry["key"]}"><b>{title}</b>'
        + "".join(_para(g, p, counts, up) for p in entry.get("lead", []))
        + (f'<ul class="dir">{lis}</ul>' if lis else "")
        + "".join(_para(g, p, counts, up) for p in entry.get("notes", []))
        + "</div>")


def question_page(g, entry, data):
    """The question's own page: the card, and a share row whose picture is
    the question's own — the thing that makes the answer postable."""
    bi = g["bi"]
    key = entry["key"]
    stem = f"asked-{key}"
    og = f"og/{stem}.png" if stem in g["OG_FILES"] else None
    body = (
        f'<h1>❓ {bi("ถามมด", "Ask the ants")}</h1>'
        f'<div class="qagrid">{card_html(g, entry, data, depth=1, heading_link=False)}</div>'
        f'<p class="tinynote"><a href="../asked.html">{bi("คำถามอื่นที่คนถามมด", "Other questions people asked the ants")}</a> · '
        f'<a href="../lists/index.html">{bi("รายชื่อครบทั้งหมวด", "Complete lists")}</a> · '
        f'{bi("ปรับปรุง", "updated")} {g["BUILD_DATE"]}</p>'
        + g["share_block"](g["BASE"] + f"asked/{key}.html", entry["q"]["th"], card=og))
    return g["page"](
        f'{entry["q"]["th"]} — ถามมด',
        body, depth=1, path=f"asked/{key}.html",
        extra_head='<link rel="stylesheet" href="../answers.css">',
        desc=f'{entry["q"]["th"]} · {entry["q"]["en"]} — คำตอบเท่าที่มดแดงมี',
        og=og,
        crumbs=(f'<a href="../index.html">มดแดง</a> › <a href="../asked.html">{bi("ถามมด", "Ask the ants")}</a> › '
                + bi(entry["q"]["th"], entry["q"]["en"])))


def asked_page(g, data, entries):
    bi = g["bi"]
    intro_th = ("บางคำถามไม่มีหมวดของตัวเอง แต่ก็เป็นคำถามจริงที่คนถามมด — หน้านี้รวบรวมไว้ "
                "บางข้อมดแดงมีคำตอบจริงอยู่แล้วในสารบัญ บางข้อต้องออกไปเช็กนอกสารบัญก่อนถึงเจอ "
                "(ทุกแหล่งมีลิงก์ที่มา) และบางข้อยังไม่มีคำตอบ บอกตรงๆ ว่าทำไม พร้อมทางช่วยเติมให้ครบ")
    intro_en = ("Some questions don't have their own shelf, but people ask the ants anyway "
                "— this page collects them. Some already have a real answer sitting in the "
                "catalogue. Some needed a check beyond the catalogue to find (every source is "
                "linked). And one stays open on purpose, explained plainly, with a concrete way "
                "to help close it.")
    cards = "".join(card_html(g, e, data) for e in entries)
    # The door in. Same Worker queue as every other "tell the ants" link, kind
    # `question`; the answer, when it comes, is a new entry in this file.
    ask = g["tell_url"]("question", prefill=("ถาม / Question: \n"
                                            "อ่านเจอที่ (ถ้ามี) / where you saw it asked (optional): "))
    body = (
        f'<h1>❓ {bi("ถามมด", "Ask the ants")}</h1>'
        f'<p>{bi(intro_th, intro_en)}</p>'
        f'<p class="myhint">❓ <a href="{ask}">{bi("มีคำถามที่ยังไม่มีในนี้? ถามมด", "Have a question that is not here? Ask the ants")}</a> — '
        f'{bi("หาอะไรอยู่แล้วหาไม่เจอ พิมพ์มาได้เลย มดจะไปหาให้แล้วเอามาตอบไว้ตรงนี้", "Looking for something you cannot find? Type it in; the ants go and look, and the answer lands on this page.")}</p>'
        f'<div class="qagrid">{cards}</div>'
        f'<p class="tinynote">{bi("ที่มา: ข้อมูลเปิด OpenStreetMap การเดินเก็บจริง และการตรวจสอบเว็บของแต่ละแห่งเอง (มีลิงก์ที่มาในข้อมูลแต่ละรายการ) ปรับปรุง", "From OpenStreetMap, field surveys, and a direct check of each business website where noted (source linked per record) · updated")} '
        f'{g["BUILD_DATE"]} · '
        f'<a href="lists/index.html">{bi("รายชื่อครบทั้งหมวด", "Complete lists")}</a></p>'
        + g["share_block"](g["BASE"] + "asked.html", "ถามมด · Ask the ants — มดแดง"))
    # The description names every question, so it stays true as the file grows.
    desc = " ".join(e["q"]["th"] for e in entries)
    return g["page"](
        "ถามมด — คำถามที่คนถามจริง เชียงใหม่ เชียงราย",
        body, depth=0, path="asked.html",
        extra_head='<link rel="stylesheet" href="answers.css">',
        desc=f"{desc} — คำถามจริงที่คนถามมดแดง คำตอบเท่าที่มี "
             "และช่องว่างที่ยังไม่มี · Real questions, the answers we hold, and the gaps.",
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("ถามมด", "Ask the ants"))


def emit(g, data):
    global DOCS
    DOCS = g["DOCS"]
    entries = load()
    (DOCS / "asked.html").write_text(asked_page(g, data, entries))
    (DOCS / "asked").mkdir(exist_ok=True)
    for e in entries:
        (DOCS / "asked" / f'{e["key"]}.html').write_text(question_page(g, e, data))
    return {"asked": 1, "questions": len(entries)}
