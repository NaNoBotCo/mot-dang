# WO-42 — สบายขึ้น: the door for the reader who was never sent · 2026-08-29

*Nan: "Many people commented 'I really like motdang.net but I don't know how
to use it'. Come up with a plan to increase the sabai round here!" — then,
on the six moves below: "Please work your way through the list."*

**Zero network.** Five edits in `build.py` and one new test. No data, no
crawls, no new pages, no URL changed, nothing deployed.

## What the comment means

`notes/what-page.md` states the site's own theory of the confused reader:
*"the reader is never someone browsing; it is always someone sent."* The
commenters are the other reader — the one who arrived at the front door on
her own, liked the place, and stood in the hallway with no sign on any wall.
The site was built for the sent reader and the asking reader; the browsing
reader who wants to be *taught* had exactly one page written for her, and
she could not reach it.

## What was measured, before

1. **what.html had ZERO inbound links.** The page built precisely for
   "เว็บอะไรอ่ะ" — fifteen tappable plates — was
   linked from nowhere: not the chipbar, not the svcbar's five families,
   not the footer (why/who/reach/privacy are there; what was not), not the
   homepage, not the 404. `grep -rl what.html docs/` returned the sitemap
   and the page itself. Reachable only by typed URL or a sent link.
2. **search.html with no `?q=` rendered an empty page** — `q ? … : ''`. The
   richest instrument on the site (thesaurus, segmenter, 7,355-word
   segmentation dictionary, 19 curated panels, the namesake split) taught a
   hesitating reader nothing about itself. Its only teaching was the
   placeholder text.
3. **The hero had no orientation sentence.** Eyebrow, H1, one intro line.
4. **The 404 was the best wayfinding page on the site** — prefilled search,
   ways-onward chips, crawl-request. A reader who mistyped a URL got more
   help than a reader standing on the homepage.
5. **A place page's crumb was two rungs** — หน้าแรก › เชียงใหม่ › place. The
   shelf sat in the หมวด row of the table instead, below the fold on a
   phone: the path a reader walked in on was not the path shown back out.

## What was built

**Move 1 — the sign that already existed, hung.** what.html linked into
`page()` itself: the มดแดง family of the header (first door in the family)
and the footer beside why/who. Because both live in the shared shell, that
is **0 → 22,171 pages** carrying the door. Plus the hero (Move 3) and a
first-time line on the 404. Nothing renamed, nothing removed, no URL moved.

**Move 2 — teach by example, not by tour.** `search.html` opened with no
query now renders the curated panels as **words to type**: glyph, bilingual
title, and an href of `search.html?q=<the panel's own trigger term>`. All 19
panels carry a variant or a query, so all 19 speak. Tapping one puts that
word in the box and opens its rich card — one tap teaches the whole loop
(verified: tapping ช้าง fills the box, opens the elephant panel with its
live count of 30, and lists 221 rows). Below the pills, the top shelves as
a second door, and what.html for a reader who is more lost than that. **No
new fetch** — the panel file is already loaded by that page.

**Move 3 — one sentence of orientation in the hero,** ant voice, bilingual,
ending in the door: *สารบัญของคนแถวนี้ · The city's own directory* →
*เพิ่งมาครั้งแรก
เริ่มตรงนี้ · New here? Start here*. **No popup, no first-run modal, no
tour**: on the connections this site is for, an overlay is the opposite of
สบาย, and this site does not interrupt people. A sentence and a door is the
whole intervention. Set in `--ink-soft` (≈8:1 on the paper), not the mute
ink a quiet line would normally take — an orientation line nobody can read
orients nobody.

**Move 4 — the card was already there.** `make_what_card.py` and
`assets/og/what.png` (148 KB) both exist and the page already asks for it,
so a shared what.html link unfurls with its own fan of plates rather than
the brand card. Nothing to build. The paste-ready reply is below, unsent.

**Move 5 — the third rung.** Place-page crumbs now read หน้าแรก › เชียงใหม่
› **shelf** › place, in the nav *and* in the BreadcrumbList JSON-LD, so the
machine reader (persona 6) gets the same trail. The rung uses the exact href
the หมวด row has always used, so no address is invented and no link can rot
that was not already rotten. First record checked: ธนาคารกสิกรไทย now sits
under ของจำเป็นประจำเมือง instead of hanging off the province.

**Move 6 — not ours to do.** The empathy map's own closing rule is that its
six personas are hypotheses awaiting the first ten real conversations. The
commenters are volunteers — people who liked the site enough to say so. Two
questions back, and the answers dated into `notes/empathy-map.md`:

> **TH** — ขอบคุณที่บอกกันนะคะ อยากถามสองข้อสั้น ๆ ค่ะ: ตอนเปิดเข้ามา
> กำลังหาอะไรอยู่ แล้วกดตรงไหนเป็นที่แรก
> **EN** — Thank you for saying so. Two short questions: what were you
> trying to find, and what did you tap first?

## The gate

`tests/test_sabai.py` — 24 checks, zero network, no build lock taken (it
emits the 404 into a throwaway directory, so it cannot land in `docs/` while
a real build owns it). It holds all five moves: the five header families
intact **and** the door inside the มดแดง one; the footer copy; the relative
root correct two levels down; the hero line and its door and the fact that
it is not `position:fixed` (no tour creeping back in); the 404 line; the
`start()` branch and that the empty-query case renders it rather than `''`;
that the pills are search queries and come from the panels already fetched;
that every panel can supply a word and a bilingual title; and the four rungs
in both the nav and the JSON-LD. **A link that nothing enforces is a link
the next work order deletes by accident** — this is why the wiring is a gate
and not a memory.

Existing gates re-run green: test_search · test_tags · test_routing ·
test_asked · test_facets · test_seven · test_shrines · test_freshness ·
test_alt_text.

## Paste-ready — the reply to the comment (NOT SENT)

Nothing posts without Nan, and the **Messenger export runs before any
posting push** (`project_distribution_rebuild`). Draft:

> **TH** — ขอบคุณที่ชอบกันนะคะ 🐜 มดแดงมีหน้าที่อธิบายตัวเองอยู่ค่ะ ว่า
> เว็บนี้คืออะไร และใช้ยังไง — motdang.net/what.html
> **EN** — Thank you! There is a page that explains what Mot Dang is and how to
> use it — motdang.net/what.html

Every future "how do I use it" gets the same door handed over, and now the
door is also on every page of the site, so most of them will not have to ask.

## Held for Nan (numbered, none of these were done)

1. **A chipbar chip for what.html?** Deliberately not taken: the chip row is
   eight, nine is a crowd, and the header family + footer + hero + 404
   already put it on every page. One line to add if she wants it louder.
2. **The hero wording** is a first draft in her voice, not her voice. One
   string, `hero_html()`.
3. **The pill set** — currently all 19 panels. Could be a hand-picked six,
   or ordered by season. The file is ordered narrow-to-broad already.
4. **Which cat is the crumb** when a place carries several — currently the
   first that exists in `CATS`, which is the same one the หมวด row lists
   first. A curated primary-shelf rule is possible and is not built.
5. **The three WO-34 header trims** still await a numbered go, and are
   untouched here: trim the five boards from the header · move ลงโฆษณา to
   the footer · band order.
6. **Survey items 3 and 4 remain open** — the `learn/` slug-label mismatch,
   and the root → `/cm/` re-root wanted before Chiang Rai. Move 5 brushes
   against item 4 but does not depend on it: the crumb points at
   `../<cat>/index.html`, which the re-root would carry along with every
   other relative link on the page.
7. **Nothing is deployed.** `publish/deploy.py --yes` is hers to run.
