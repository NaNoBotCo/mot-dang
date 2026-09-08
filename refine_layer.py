"""WO-75 — กรองเอง · THE READER'S OWN BOOLEAN, and the bare shell around it.

Nan, 2026-09-07: *"Users should be able to easily access boolean tools to
refine their own searches. Make it intuitive for the krapow grannies. Remove
all other forms of navigation, other than what I'm describing in the current
workflows. Start with a blank homepage, minimal footer, logo top left links
back to homepage from other navved pages."*

Two jobs, one module, because they are the same decision seen twice: if the
box and the refine panel are the whole way through the site, then everything
else that was carrying readers around has to go, or it competes.


A. THE BOOLEAN, WITHOUT THE WORD

A krapow granny has never typed AND, OR or NOT and never will. She has,
however, pointed at two things she wanted and pushed one away, her whole life.
So the three operators are three gestures, and the panel says out loud in Thai
what it just did:

    AND   two different drawers        ก๋วยเตี๋ยว + ช้างเผือก
    OR    two values in ONE drawer     ช้างเผือก หรือ สันติธรรม
    NOT   the ⊘ beside a value         − เจ  (struck through, in the bar)

Nothing is typed. Nothing is parsed. The bar across the top of the results IS
the expression, rendered as a sentence you can read aloud, and every chip in
it is a tap that removes that term. That was already half-built: WO-69 gave
every active filter a chip whose tap removes it. What was missing was any way
to ADD one without knowing the URL, any way to say NOT at all, and any
statement of what OR meant when two chips of the same kind sat side by side.

THE COUNT IS THE WHOLE AFFORDANCE. Every value carries the number of rows it
would leave standing, counted against the current result set with its own
drawer's filters lifted — so within a drawer the numbers add up and across
drawers they narrow. A value at zero is never drawn. That is the difference
between a tool and a maze: she cannot open an empty door, because the door
said how many were behind it before she touched it.

UNKNOWN IS NOT NO. The parking bug (go/parking-bug) was one field read as a
denial: 1,632 car parks excluded from a parking search because nobody had
written `parking=yes` on them. Every drawer here states its own silence —
"เปิดอยู่ (1,204) · อีก 21,555 ร้านไม่ได้บอกเวลาไว้" — and a filter never
removes a row for lacking the field, only for carrying a value that fails.
`ไม่ได้บอกไว้` is itself a tappable value in every drawer, because "show me
the ones nobody has filled in yet" is a real question and it is the one the
add/claim flow is for.

THE STATE IS THE URL, so the back button is undo and every refinement is a
link she can send on LINE. The grammar was already there and is not changed:

    q=          the words
    tag= cat= sub= st= ar=      comma-separated — OR inside one key
    (across keys)               AND
    not=tag:vegetarian,ar:สันกำแพง      NEW — one key holds every exclusion

`not=` is a new key rather than a `!` inside the existing ones, so nothing
that reads the old keys has to learn anything, and stripping every exclusion
is one delete.


B. THE BARE SHELL

Nan's calls, 2026-09-07, taken as answers to a named inventory:

    KEPT    logo → home · the search box · this panel · the language toggle
            the links inside a record (its tags, street, nearby) — they are
              refine tools wearing another hat: a tag on a place page is the
              same tap as a tag in the drawer
            the map as a SECOND workflow (WO-74 / go/tap), peer to the box
            the NOW·NEAR line — HOMEPAGE ONLY, not every page
    CUT     the ☰ drawer: 9 chipbar chips + 27 svcbar links, every page
            breadcrumbs · the tagline · the empty-search pills
            the homepage body entire — events, postcard, eight paths, five
              folds, the 175-shelf finder
            8 of the 10 footer links
    FOOTER  updated date · OSM ODbL · the licence line · the emergency
            numbers · terms · privacy · the ant. Subtle (her word): one
            muted line at 0.78rem, no boxes, no headings.

The homepage is blank in the sense she asked for: the box, grown, and the one
line under it. No body. A reader who wants a shelf types its name.

WHAT THIS COSTS, stated rather than discovered later:
  · 25,889 pages lose their crawlable outbound links. Internal linking is how
    the shelves were reachable at all ([[project_motdang_arrivals]]); the
    record-internal links Nan kept are now the ENTIRE link graph, and
    sitemap.xml carries the rest of the weight alone.
  · /here.html, /plan.html, /events.html, /toilets.html, /my.html, /add.html,
    /claim.html and the 27 svcbar destinations still exist and are still
    built. Nothing is deleted. They are reachable by search, by their own
    URLs, and by nothing else.
  · The emergency numbers survive only because they are in the footer. That
    was the one removal worth flagging and she kept them.

Called from build.py — five hooks, listed verbatim in
notes/boolean-refine-2026-09-07.txt §5. Nothing here runs a build; build.py
was hot (edited 21:09 with a build running from 20:54) when this was written,
so it is staged the way here_layer and nownear_layer were staged before it.
"""

# ─────────────────────────────────────────────────── the form, as Google's is
#
# Nan, 2026-09-07, on the ranked chip rail that stood here before: *"I want
# the boolean to look a lot more like Google's advanced search tools than
# this. This is hard to understand."*
#
# She is right and the rail was the mistake. It was clever — offers ranked by
# the split they would make, no headings, one chrome word — and clever is
# exactly what a boolean must not be. A person who has used a computer has
# filled in Google's advanced search form, or one built to look like it, and
# has never once had to be taught it. It is verbose and it is legible, and
# between those two the legible one wins every time.
#
# So: the same shape Google has had since 2003. Two labelled groups, one
# button.
#
#     หาที่มี…                       Find places with…
#       มีทุกคำนี้                     all these words
#       วลีตรงตัวนี้                    this exact phrase
#       มีคำใดคำหนึ่ง                   any of these words
#       ไม่มีคำเหล่านี้                   none of these words
#
#     แล้วกรองให้แคบลง…              Then narrow by…
#       ประเภท · ย่าน · ถนน · มีอะไรบ้าง · ชั้น        [ทั้งหมด ▾]
#       เปิดอยู่ตอนนี้                                 [ ]
#
# AND / OR / NOT ARE THE ROW LABELS. Nobody has to know that "มีทุกคำนี้" is
# AND, that "มีคำใดคำหนึ่ง" is OR and that "ไม่มีคำเหล่านี้" is NOT — they
# just fill in the row that says what they want. That is the whole reason
# Google's form has outlived every clever faceted-search UI built since.
#
# TWO SURFACES, and they are the two Google has:
#   /advanced.html   the full form. Its dropdowns are BAKED at build time
#                    with global counts, so the page is static and instant
#                    and never fetches the 6 MB index to show a list of
#                    districts.
#   the results page a compact row of the same labelled dropdowns — Google's
#                    Tools row — whose counts are recomputed from the answer
#                    actually on screen, plus the active-filter sentence.
#
# THE URL PARAMS take Google's own names for the four word fields, which
# collide with nothing this site already reads:
#   as_q    all these words        as_oq   any of these words
#   as_epq  this exact phrase      as_eq   none of these words
# and the structured narrowing keeps the keys search.html already spoke:
#   tag= su= ar= st= f= cat=  ·  open=1  ·  not=key:value  ·  blank=key
# (`blank=` is the old `none=`, renamed the day `none of these words` arrived
#  and made the old name a trap.)

# The four word rows, in order. (param, ไทย, English, placeholder hint)
WORD_ROWS = (
    ("as_q",   "มีทุกคำนี้",       "all these words",     "ก๋วยเตี๋ยว เนื้อ"),
    ("as_epq", "วลีตรงตัวนี้",     "this exact phrase",   "ก๋วยเตี๋ยวเรือ"),
    ("as_oq",  "มีคำใดคำหนึ่ง",    "any of these words",  "นวด สปา"),
    ("as_eq",  "ไม่มีคำเหล่านี้",   "none of these words", "เจ"),
)

# The narrowing rows. (key, ไทย, English, how a row carries it)
NARROW_ROWS = (
    ("tag", "ประเภท",      "what it is",   "many"),
    ("ar",  "ย่าน",         "district",     "one"),
    ("st",  "ถนน",         "road",         "one"),
    ("f",   "มีอะไรบ้าง",    "what it has",  "many"),
    ("su",  "ชั้น",          "shelf",        "many"),
)

KEYS = tuple(k for k, _, _, _ in NARROW_ROWS) + ("cat", "open")
WORD_KEYS = tuple(k for k, _, _, _ in WORD_ROWS)

# The facet keys, in words. Anything not named here falls back to its own key
# rather than being dropped: a refinement we cannot spell is still a
# refinement, and hiding it would be the empty-shelf mistake again.
FACET_WORDS = {
    "wifi": ("ไวไฟ", "wifi"),
    "aircon": ("แอร์", "air-con"),
    "coin": ("หยอดเหรียญ", "coin-op"),
    "open24": ("เปิด 24 ชม.", "open 24h"),
    "openlate": ("เปิดดึก", "open late"),
    "seating": ("มีที่นั่ง", "somewhere to sit"),
    "wheelchair": ("รถเข็นเข้าได้", "wheelchair"),
    "takeaway": ("ซื้อกลับบ้าน", "takeaway"),
    "delivery": ("ส่งถึงบ้าน", "delivery"),
    "atm": ("ตู้เอทีเอ็ม", "ATM"),
    "toilet": ("ห้องน้ำ", "toilet"),
    "atstation": ("อยู่ในสถานี", "at the station"),
    "rental": ("ให้เช่า", "rental"),
    "printphone": ("ปริ้นท์จากมือถือ", "print from your phone"),
    "dryclean": ("ซักแห้ง", "dry clean"),
    "uniform": ("ชุดนักเรียน", "school uniforms"),
    "binding": ("เข้าเล่ม", "binding"),
    "zip": ("ซ่อมซิป", "zip repair"),
    "hem": ("เย็บชาย", "hemming"),
    "eveningwear": ("ชุดราตรี", "evening wear"),
    "thaiformal": ("ชุดไทย", "Thai formal"),
    "ortho": ("จัดฟัน", "braces"),
    "denture": ("ฟันปลอม", "dentures"),
    "implant": ("รากฟันเทียม", "implants"),
    "veneer": ("วีเนียร์", "veneers"),
}

# How many options a baked dropdown carries. 300 tambon is a scroll; 8,000
# trade words is a download. Past the cap the words fields are the way in,
# which is what they are for — and the page says so once rather than
# pretending the list is complete.
# Five derived tags are facts about OUR RECORD rather than about the place —
# whether we hold a phone number, a website, a Facebook page, opening hours, or
# nothing at all. They are the commonest tags in the catalogue, so they were the
# top three values in "ประเภท · what it is", which is not the question they
# answer. They move to "มีอะไรบ้าง · what it has", where "show me the ones with
# a phone number" is exactly what a reader means.
RECORD_TAGS = ("no-contact", "has-phone", "has-hours", "has-website", "has-facebook")

OPTION_CAP = 300


def js_version():
    """The hash build.py stamps on refine.js, computed off this module's own
    source so a change here cannot be served from a reader's cache.

    style.css went unversioned until 2026-09-07 and every layout fix shipped
    in a seven-day window reached first-time visitors and nobody else. This
    file is not going to repeat it.
    """
    import zlib
    return f"{zlib.crc32((JS + CSS).encode()) & 0xFFFFFFFF:08x}"


def head(r):
    """The one script tag. `defer` because both surfaces are real HTML before
    any script runs — the form submits with JavaScript off."""
    return f'<script src="{r}refine.js?v={js_version()}" defer></script>'


def _opts(key, rows, bi, att, cap=OPTION_CAP):
    """One dropdown's options, with counts, longest list first.

    A value nobody carries is not offered — the same rule the whole panel
    runs on. The count rides in the option's own text because a dropdown
    cannot show a count any other way, and a district that would return
    three places should say three before it is chosen, not after.
    """
    out = [f'<option value="">{att(bi_text("ทั้งหมด", "any"))}</option>']
    for value, th, en, n in (rows or [])[:cap]:
        word = bi_text(th, en) if en and en != th else (th or value)
        out.append(f'<option value="{att(value)}">{att(word)} ({n:,})</option>')
    return "".join(out)


def bi_text(th, en, sep=" · "):
    """The bilingual pair as plain text, for the places markup cannot go.

    An <option> is one of those places — a <span> inside it is drawn as
    literal tag soup by every browser — and so are title= and aria-label=.
    build.py's own bi_text() is the right function and is not importable here
    without a cycle. Both languages, because the screen shows both and a
    reader who has switched to ไทย still gets a readable option: the language
    toggle cannot reach inside an <option>, and half a word is worse than two.
    """
    th, en = (th or "").strip(), (en or "").strip()
    if not th:
        return en
    if not en or en == th:
        return th
    return th + sep + en


def advanced_form(bi, att, options, r="", action="search.html"):
    """/advanced.html — Google's form, in two labelled groups and one button.

    `options` is {key: [(value, th, en, count), …]} computed at BUILD time by
    build.py off the same index rows it has just written. Baked, so this page
    is static HTML that needs no fetch and no script: it is a <form method=get>
    and it works with JavaScript off, which is more than the results page can
    say.
    """
    words = "".join(
        f'<div class="afrow"><label for="af-{k}">{bi(th, en)}</label>'
        f'<input id="af-{k}" name="{k}" type="search" '
        f'placeholder="{att(hint)}"></div>'
        for k, th, en, hint in WORD_ROWS)
    narrow = "".join(
        f'<div class="afrow"><label for="af-{k}">{bi(th, en)}</label>'
        f'<select id="af-{k}" name="{k}">{_opts(k, options.get(k), bi, att)}</select></div>'
        for k, th, en, _ in NARROW_ROWS)
    narrow += (
        '<div class="afrow"><span class="aflbl">'
        + bi("เปิดอยู่ตอนนี้", "open now") + '</span>'
        '<label class="afcheck"><input type="checkbox" name="open" value="1"> '
        + bi("เฉพาะที่เปิดอยู่", "only places open right now") + '</label></div>'
        # PRESENCE AND ABSENCE. "ยังไม่มี" is what the add and claim flows are
        # for: working through a gap on purpose needs a way to ask for it.
        + '<div class="afrow"><label for="af-has">' + bi("ต้องมี", "must have")
        + '</label><select id="af-has" name="has" multiple size="4">'
        + "".join(f'<option value="{att(k)}">{att(bi_text(th, en))}</option>'
                  for k, th, en in PRESENCE_ROWS) + '</select>'
        + f'<span class="afmulti">{bi("เลือกได้หลายอย่าง", "pick as many as you like")}</span></div>'
        + '<div class="afrow"><label for="af-blank">' + bi("ยังไม่มี", "does not have yet")
        + '</label><select id="af-blank" name="blank" multiple size="4">'
        + "".join(f'<option value="{att(k)}">{att(bi_text(th, en))}</option>'
                  for k, th, en in PRESENCE_ROWS) + '</select></div>')

    order = (
        '<div class="afrow"><label for="af-sort">' + bi("เรียงลำดับ", "sort by")
        + '</label><select id="af-sort" name="sort">'
        + "".join(f'<option value="{att(v)}">{att(bi_text(th, en))}</option>'
                  for v, th, en in SORT_ROWS) + '</select></div>'
        + '<div class="afrow"><span class="aflbl">' + bi("ระยะทาง", "distance")
        + '</span><label class="afcheck"><input type="checkbox" name="mypos" value="1"> '
        + bi("วัดจากตำแหน่งของฉัน — ต้องอนุญาตให้ใช้ตำแหน่ง",
             "measure from where I am — asks permission when you tick it")
        + '</label></div>'
        + '<div class="afrow"><label for="af-radius">' + bi("ในระยะ", "within")
        + '</label><select id="af-radius" name="radius">'
        + f'<option value="">{att(bi_text("ไม่จำกัด", "any distance"))}</option>'
        + "".join(f'<option value="{km}">{att(bi_text(th, en))}</option>'
                  for km, th, en in RADII) + '</select></div>')
    return f"""<form class="advform" action="{r}{action}" method="get">
  <fieldset>
    <legend>{bi("หาที่มี…", "Find places with…")}</legend>
    {words}
  </fieldset>
  <fieldset>
    <legend>{bi("แล้วกรองให้แคบลง…", "Then narrow by…")}</legend>
    {narrow}
  </fieldset>
  <fieldset>
    <legend>{bi("แล้วเรียงผลลัพธ์…", "Then order the answer…")}</legend>
    {order}
  </fieldset>
  <div class="afgo"><button type="submit">{bi("ค้นหาขั้นสูง", "Advanced search")}</button></div>
  <p class="afnote">{bi(
    "รายการในช่องเลือกคือคำที่พบบ่อยที่สุด ถ้าไม่เจอที่ต้องการ พิมพ์ลงในช่องด้านบน",
    "the dropdowns carry the most common values; if what you want is not there, type it in a box above")}</p>
</form>"""


def tools_row(bi, att, r=""):
    """The results page's own row of the same dropdowns — Google's Tools row.

    Rendered empty at build time and filled by refine.js from the answer
    actually on screen, so every count says how many of THESE results the
    choice would leave. It is a <details> closed by default: the reader who
    got what they wanted never opens it, and it costs one line when shut.
    """
    sels = "".join(
        f'<label class="tool"><span>{bi(th, en)}</span>'
        f'<select data-refkey="{k}"><option value="">'
        f'{att(bi_text("ทั้งหมด", "any"))}</option></select></label>'
        for k, th, en, _ in NARROW_ROWS)
    return (
        '<div class="refine" id="refine" hidden>'
        '<p class="refbar" id="refbar"></p>'
        '<details class="reftools" id="reftools">'
        f'<summary>{bi("เครื่องมือค้นหา", "Search tools")}</summary>'
        f'<div class="toolrow" id="toolrow">{sels}'
        f'<label class="tool tickbox"><input type="checkbox" data-refkey="open" value="1"> '
        f'<span>{bi("เปิดอยู่ตอนนี้", "open now")}</span></label>'
        f'<label class="tool"><span>{bi("เรียงลำดับ", "sort by")}</span>'
        f'<select data-refkey="sort">'
        + "".join(f'<option value="{att(v)}">{att(bi_text(th, en))}</option>'
                  for v, th, en in SORT_ROWS) + '</select></label>'
        f'<label class="tool tickbox"><input type="checkbox" data-refkey="mypos" value="1"> '
        f'<span>{bi("ใกล้ฉัน", "near me")}</span></label>'
        f'<a class="advlink" href="{r}advanced.html">'
        f'{bi("ค้นหาขั้นสูง", "Advanced search")} →</a></div>'
        '</details>'
        '</div>')


def doors_row():
    """The two doors on the answer, mounted empty and filled by refine.js.

    Empty because both counts are counts of THIS answer — the rows left after
    the reader's own boolean — and that number does not exist until the page
    has run the search. Neither door is drawn at zero: a 🗺 over a result set
    with no pins and a 🗓 over one with nothing on are two offers that go
    nowhere, and an offer that goes nowhere is worse than no offer.
    """
    return '<p class="resdoors" id="resdoors" hidden></p>'


def event_places_json(events):
    """{place id: how many events stand there} — the calendar door's count.

    Baked into search.html rather than fetched. 75 ids is about 2 kB; the
    260 kB of event records behind them is fetched by the reader who taps the
    door and by nobody else. A door that had to download the whole calendar
    before it could work out whether to draw itself would charge every search
    on the site for a door that almost no search draws.

    Counted the way events.ics is written — an event with no date is not in
    the file, so it is not in the number either.
    """
    n = {}
    for e in events or []:
        pid = (e.get("place") or {}).get("id")
        if not pid or not (e.get("dt") or e.get("start")):
            continue
        n[pid] = n.get(pid, 0) + 1
    return _json.dumps(n, ensure_ascii=False, separators=(",", ":"))


def panel_mount(bi, att=None, r=""):
    """Kept under its old name so §5(d) of the note still applies."""
    return doors_row() + tools_row(bi, att or (lambda s: s), r)


# Where the words are allowed to match. THIS IS THE CERTAINTY CONTROL: the
# index matches on seven fields, and a search that hits `k` (shelf words,
# cuisine, brand, road) or `a` (alt names, other-language names, the RTGS
# reading) is wide by design. Scoping to the name is how a reader who knows
# what a place is called gets that place and nothing else.
WORD_SCOPES = (
    ("any",  "ทุกที่",                "anywhere",            "n e nm em r a k"),
    ("read", "ชื่อและคำอ่าน",          "the name and its reading", "n e nm em r"),
    ("name", "ชื่อเท่านั้น",            "the name only",       "n e nm em"),
)

# HOW THE ANSWER IS ORDERED. Only what the index can actually order on:
# there is no updatedAt in a row and no popularity anywhere, so neither is
# offered. "ครบที่สุด" counts how many of a row's fields are filled in — the
# honest stand-in for "the one we know most about", and the only ranking here
# that is about the record rather than the query.
SORT_ROWS = (
    ("",     "ตรงที่สุด",    "best match"),
    ("name", "ก-ฮ / A-Z",  "by name"),
    ("near", "ใกล้ที่สุด",    "nearest first"),
    ("full", "ครบที่สุด",    "most complete"),
)

# The radii a person actually thinks in, on foot and on a motorbike.
RADII = ((0.5, "500 ม.", "500 m"), (1, "1 กม.", "1 km"), (2, "2 กม.", "2 km"),
         (5, "5 กม.", "5 km"), (10, "10 กม.", "10 km"), (25, "25 กม.", "25 km"))

# Presence and absence, as their own controls. `blank=` is what the add and
# claim flows are for — "show me what nobody has filled in yet" is a real
# question and the only way to work through a gap on purpose.
PRESENCE_ROWS = (
    ("pin", "หมุดบนแผนที่", "a pin on the map"),
    ("hk",  "เวลาเปิด-ปิด",  "opening hours"),
    ("ar",  "ย่าน",         "a district"),
    ("st",  "ถนน",         "a road"),
)


# ──────────────────────────────────────────────────────────────────── the look
#
# Google's form is a two-column grid — label left, control right — and it has
# been legible for twenty years because it never moved. The results page's
# Tools row is a shut <details> that costs one line until somebody opens it.
CSS = """
/* ── ค้นหาขั้นสูง · the advanced form ────────────────────────────── */
.advform{max-width:44rem;margin:.4rem 0 1rem}
.advform fieldset{border:0;border-top:1px solid var(--rule);margin:0 0 1.2rem;
  padding:.2rem 0 0}
.advform legend{padding:0 .5rem 0 0;color:var(--ant-dark);font-weight:600;
  font-size:.95rem}
.afrow{display:grid;grid-template-columns:13rem 1fr;gap:.5rem .9rem;
  align-items:center;padding:.22rem 0}
.afrow>label,.afrow>.aflbl{color:var(--ink-soft,#544636);font-size:.92rem}
.afrow input[type=search],.afrow select{font:inherit;font-size:.95rem;
  width:100%;max-width:24rem;padding:.32rem .5rem;border:1px solid var(--dashed,#c4b28d);
  border-radius:.3rem;background:#fff;color:var(--ink);min-height:40px}
.afrow select[multiple]{min-height:7.5rem;padding:.2rem}
.afrow input[type=search]:focus,.afrow select:focus{border-color:var(--ant);
  outline:2px solid var(--ant);outline-offset:1px}
.afcheck{display:inline-flex;align-items:center;gap:.45rem;font-size:.92rem}
.afcheck input,.tickbox input{width:1.1rem;height:1.1rem;accent-color:var(--ant)}
.afmulti{font-size:.78rem;color:var(--mute);grid-column:2}
.afgo{display:flex;justify-content:flex-end;max-width:37.9rem;margin:.3rem 0 0}
.afgo button{font:inherit;font-weight:600;border:2px solid var(--ant);
  background:var(--ant);color:#fff;border-radius:.4rem;padding:.45rem 1.4rem;
  cursor:pointer;min-height:44px}
.afgo button:hover,.afgo button:focus{background:var(--ant-dark);border-color:var(--ant-dark)}
.afnote{font-size:.8rem;color:var(--mute);max-width:37.9rem;margin:.7rem 0 0}
@media(max-width:640px){
  .afrow{grid-template-columns:1fr;gap:.15rem;padding:.35rem 0}
  .afrow input[type=search],.afrow select{max-width:100%}
  .afgo,.afnote{max-width:100%}
  .afmulti{grid-column:1}
}
/* ── the results page: the sentence, and the Tools row ──────────── */
.refine{margin:.3rem 0 1rem;font-size:.92rem}
.refbar{margin:0 0 .45rem;display:flex;flex-wrap:wrap;align-items:center;
  gap:.3rem .32rem;line-height:2}
.refbar:empty{display:none}
.refbar .join{color:var(--mute);font-size:.82rem;padding:0 .05rem}
.refterm{display:inline-flex;align-items:center;gap:.3rem;padding:.08rem .55rem;
  border:1px solid var(--ant-dark);border-radius:999px;background:var(--ant-dark);
  color:#fff;text-decoration:none}
.refterm:visited{color:#fff}
.refterm:hover,.refterm:focus{background:var(--ant)}
.refterm .x{font-size:.78rem;opacity:.7}
.refterm.no{background:transparent;color:var(--mute);border-style:dashed;
  border-color:var(--mute);text-decoration:line-through}
.refterm.no:hover,.refterm.no:focus{background:var(--mute);color:#fff}
.refclear{font-size:.82rem;color:var(--mute);margin-inline-start:.25rem}
.reftools>summary{cursor:pointer;list-style:none;display:inline-block;
  color:var(--mute);font-size:.85rem;padding:.1rem 0}
.reftools>summary::-webkit-details-marker{display:none}
.reftools>summary::after{content:" ▾"}
.reftools[open]>summary{color:var(--ant-dark)}
.reftools[open]>summary::after{content:" ▴"}
.reftools>summary:hover{color:var(--ant-dark);text-decoration:underline}
.toolrow{display:flex;flex-wrap:wrap;gap:.5rem .9rem;align-items:center;
  margin:.4rem 0 .2rem;padding:.5rem 0 .1rem;border-top:1px dotted var(--rule)}
.tool{display:inline-flex;align-items:center;gap:.35rem;font-size:.85rem;
  color:var(--mute)}
.tool select{font:inherit;font-size:.85rem;padding:.2rem .4rem;
  border:1px solid var(--dashed,#c4b28d);border-radius:.3rem;background:#fff;
  color:var(--ink);max-width:12rem;min-height:36px}
.tool select:disabled{opacity:.45}
.tickbox{gap:.4rem}
.advlink{font-size:.85rem;margin-inline-start:auto;white-space:nowrap}
@media(max-width:560px){.advlink{margin-inline-start:0}
  .tool{width:100%}.tool select{flex:1;max-width:none}}
/* ── the two doors on the answer ────────────────────────────────── */
/* Underlined, worded and sized like something a thumb is meant to hit. The
   pair they replace were two bare emoji in the heading with nothing but an
   aria-label to say what they did, which is a label only a screen reader
   ever read. */
.resdoors{margin:.15rem 0 .55rem;display:flex;flex-wrap:wrap;
  gap:.1rem .95rem;align-items:center;line-height:1.8}
.resdoors[hidden]{display:none}
.resdoor{display:inline-flex;align-items:center;gap:.35rem;min-height:36px;
  color:var(--ant-dark);font-size:.95rem;text-decoration:underline;
  text-underline-offset:.18em}
.resdoor:visited{color:var(--ant-dark)}
.resdoor:hover,.resdoor:focus{color:var(--ant)}
.resdoor .count{color:var(--mute);font-size:.85rem;text-decoration:none}
.resdoor .dooricon{font-size:1.05rem;text-decoration:none}
.resdoor[aria-busy=true]{opacity:.55}
/* ── the bare shell ─────────────────────────────────────────────── */
/* logo · language · อ่านง่าย, one line, and the controls to the right where
   they are out of the way of the name. Under 34rem they wrap and the logo
   keeps the first line to itself. */
header.site.bare{border-bottom:3px solid var(--day);padding:.7rem 0 .6rem;margin-bottom:.5rem}
.mast{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}
.mast .langgroup{margin-left:auto}
.mast .readbtn{flex:0 0 auto}
@media(max-width:34rem){
  .mast .logo{flex:1 0 100%}
  .mast .langgroup{margin-left:0}
}
body.home .homebare{margin:.6rem 0 0;font-size:.9rem;color:var(--mute)}
body.home header.site .seek input{font-size:1.15rem;padding:.75rem .9rem}
body.home header.site .seek{margin-top:.5rem}
body.home main{min-height:38vh}
footer.bare{margin-top:2.4rem;padding-top:.7rem;border-top:1px solid var(--rule);
  font-size:.78rem;color:var(--mute);line-height:1.9}
footer.bare a{color:var(--mute)}
footer.bare a:visited{color:var(--mute)}
footer.bare a:hover,footer.bare a:focus{color:var(--ant-dark)}
footer.bare .footline{display:block}
footer.bare .licence{display:block;opacity:.8}
footer.bare .footsos{margin-bottom:.35rem;font-size:.82rem}
footer.bare .footsos a.sos{color:var(--ant-dark);font-weight:600}
"""


# ──────────────────────────────────────────────────────────────── the engine
JS = r"""
(function(){
'use strict';
var RECTAG=__RECORD_TAGS__;
var NARROW=__NARROW__, WORDF=__WORD_FIELDS__, FW=__FACET_WORDS__,
    SCOPES=__SCOPES__, PRESENCE=__PRESENCE__, SORTS=__SORTS__;
var KEYS=NARROW.concat(['cat','kd','p','open']);
function H(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function BI(th,en){th=th||'';en=en||'';
  if(!th)return '<span class="en" lang="en">'+H(en)+'</span>';
  if(!en||en===th)return '<span class="th" lang="th">'+H(th)+'</span>';
  return '<span class="bi"><span class="th" lang="th">'+H(th)+'</span>'+
    '<span class="en" lang="en"><span class="th" lang="th"> · </span>'+H(en)+'</span></span>';}
// BOTH SHAPES, because both arrive. A link this engine builds carries
// `tag=a,b`; a <select multiple> in the advanced form submits `tag=a&tag=b`,
// and URLSearchParams.get() would have returned only `a` — the form would
// have quietly dropped every choice after the first.
function list(u,k){var out=[];
  u.getAll(k).forEach(function(v){
    String(v||'').split(',').forEach(function(x){if(x&&out.indexOf(x)<0)out.push(x);});});
  return out;}
function toks(s){return (s||'').trim().split(/\s+/).filter(Boolean)
  .map(function(x){return x.toLowerCase();});}
var openTest=null;

// ── state ────────────────────────────────────────────────────────────────
function parse(search){
  var u=new URLSearchParams(search==null?location.search:search);
  var st={u:u,inc:{},not:[],blank:{},has:{},
          q:u.get('as_q')||u.get('q')||'', epq:u.get('as_epq')||'',
          oq:u.get('as_oq')||'', eq:u.get('as_eq')||'',
          scope:u.get('as_in')||'any'};
  KEYS.forEach(function(k){var v=list(u,k);if(v.length)st.inc[k]=v;});
  list(u,'not').forEach(function(p){var i=p.indexOf(':');if(i>0){
    var k=p.slice(0,i);if(KEYS.indexOf(k)>=0)st.not.push([k,p.slice(i+1)]);}});
  list(u,'blank').forEach(function(k){st.blank[k]=1;});
  list(u,'has').forEach(function(k){st.has[k]=1;});
  return st;
}

// ── the words, and where they are allowed to match ───────────────────────
// THE CERTAINTY CONTROL. `k` carries shelf words, cuisine, brand and road;
// `a` carries alt names, other-language names and the RTGS reading. Both are
// matched and never shown, which is right for a wide search and wrong for
// somebody who knows the name of the shop they want. as_in picks the field
// set, so "ชื่อเท่านั้น" returns that shop and nothing standing near it.
function text(e,scope){
  var fields=WORDF[scope]||WORDF.any,out=[];
  for(var i=0;i<fields.length;i++){var v=e[fields[i]];if(v)out.push(v);}
  return out.join(' ').toLowerCase();
}
function wordsOk(e,st){
  if(!st.q&&!st.epq&&!st.oq&&!st.eq)return true;
  var s=text(e,st.scope),i,t;
  if(st.epq&&s.indexOf(st.epq.trim().toLowerCase())<0)return false;
  if(st.q){t=toks(st.q);for(i=0;i<t.length;i++)if(s.indexOf(t[i])<0)return false;}
  if(st.oq){t=toks(st.oq);var any=false;
    for(i=0;i<t.length;i++)if(s.indexOf(t[i])>=0){any=true;break;}
    if(!any)return false;}
  // "none of these words" is tested against the WIDEST field set whatever the
  // scope: a reader who says they do not want เจ does not want it hiding in
  // the cuisine tag either.
  if(st.eq){var wide=text(e,'any');t=toks(st.eq);
    for(i=0;i<t.length;i++)if(wide.indexOf(t[i])>=0)return false;}
  return true;
}

// ── the structured fields ────────────────────────────────────────────────
function vals(e,k,T){
  var o=[],i;
  if(k==='tag'){
    if(e.t)for(i=0;i<e.t.length;i++){var g=T.tags[e.t[i]];if(g&&g[0]&&!RECTAG[g[0]])o.push(g[0]);}
    if(e.tt)for(i=0;i<e.tt.length;i++){var r=T.trade[e.tt[i]];if(r&&r[0])o.push(r[0]);}
  }else if(k==='ar'){var a=e.ar!=null?T.areas[e.ar]:null;if(a&&(a[0]||a[1]))o.push(a[0]||a[1]);}
  else if(k==='st'){var s=e.st!=null?T.streets[e.st]:null;if(s&&s[0])o.push(s[0]);}
  else if(k==='f'){if(e.f)o=e.f.slice();
    // …and they belong in "what it has", which is the question they answer.
    if(e.t)for(i=0;i<e.t.length;i++){var q=T.tags[e.t[i]];if(q&&q[0]&&RECTAG[q[0]])o.push(q[0]);}}
  else if(k==='su'){if(e.su)o=e.su.slice();}
  else if(k==='cat'){if(e.c)o=e.c.slice();}
  else if(k==='kd'){if(e.kd)o=e.kd.slice();}
  else if(k==='p'){if(e.p)o=[e.p];}
  else if(k==='pin'){if(e.lat!=null&&e.lng!=null)o=['1'];}
  else if(k==='hk'){if(e.hk!=null)o=['1'];}
  else if(k==='open'){
    // mdOpen returns null — never false — where nobody recorded hours. A
    // silence must not be counted as a closed door (go/parking-bug), so a
    // row we cannot answer for carries no value and no open filter touches it.
    if(openTest&&e.hk!=null){if(openTest(e)===true)o.push('1');}}
  return o;
}
function has(e,k,v,T){return vals(e,k,T).indexOf(v)>=0;}
function ok(e,st,T,skip){
  if(!wordsOk(e,st))return false;
  for(var k in st.inc){if(k===skip)continue;
    var any=false,vs=st.inc[k];
    for(var i=0;i<vs.length;i++)if(has(e,k,vs[i],T)){any=true;break;}
    if(!any)return false;}
  for(var j=0;j<st.not.length;j++){var n=st.not[j];
    if(n[0]===skip)continue;if(has(e,n[0],n[1],T))return false;}
  // NOTHING IS DROPPED FOR SILENCE unless the reader asked for silence.
  for(var b in st.blank){if(b===skip)continue;if(vals(e,b,T).length)return false;}
  for(var h in st.has){if(h===skip)continue;if(!vals(e,h,T).length)return false;}
  return true;
}

// ── distance ─────────────────────────────────────────────────────────────
// The pin is on 97.7% of the catalogue — the one field we hold on nearly
// everything, against hours at 17% and tags at 10%. So distance is the
// strongest filter and the strongest ordering this site owns, and it is the
// last one it grew.
function dist(a,b,c,d){
  var R=6371,p=Math.PI/180,x=(c-a)*p,y=(d-b)*p;
  var h=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*p)*Math.cos(c*p)*
        Math.sin(y/2)*Math.sin(y/2);
  return 2*R*Math.asin(Math.sqrt(h));
}
function point(st){
  var n=(st.u.get('near')||'').split(',');
  if(n.length!==2)return null;
  var la=parseFloat(n[0]),ln=parseFloat(n[1]);
  return (isFinite(la)&&isFinite(ln))?[la,ln]:null;
}
function far(e,st){
  var p=point(st),r=parseFloat(st.u.get('radius')||'');
  if(!p||!isFinite(r)||r<=0)return null;
  // A place with no pin is NOT beyond the radius — it is unmeasured, and
  // dropping it would be unknown read as no all over again. It is kept, and
  // sorted to the end.
  if(e.lat==null||e.lng==null)return null;
  return dist(p[0],p[1],e.lat,e.lng)>r;
}
// How much of a row is filled in. The honest stand-in for "the one we know
// most about": there is no popularity in this index and no updatedAt, so
// neither is offered as an order.
var FULLF=['e','r','st','ar','t','tt','f','hk','su','kd','lat'];
function fullness(e){var n=0;for(var i=0;i<FULLF.length;i++){
  var v=e[FULLF[i]];if(v!=null&&(!v.length||v.length>0))n++;}return n;}
function sortRows(rows,st,T){
  var s=st.u.get('sort')||'',p=point(st);
  if(!s)return rows;
  var out=rows.slice();
  if(s==='name')out.sort(function(a,b){
    return String(a.n||'').localeCompare(String(b.n||''),'th');});
  else if(s==='full')out.sort(function(a,b){return fullness(b)-fullness(a);});
  else if(s==='near'&&p)out.sort(function(a,b){
    // Unpinned rows go last rather than first: Infinity, never 0.
    var da=(a.lat==null?Infinity:dist(p[0],p[1],a.lat,a.lng));
    var db=(b.lat==null?Infinity:dist(p[0],p[1],b.lat,b.lng));
    return da-db;});
  return out;
}
// Filters, then orders. One call, so md.js's hook stays one line.
// The answer is kept as well as returned: draw() is handed the UNFILTERED set
// (that is what makes every count read "how many would be left"), and the two
// doors under the count are about the filtered one — the rows on screen.
function apply(rows,T){
  var st=parse();
  lastRows=sortRows(rows.filter(function(e){
    return ok(e,st,T)&&far(e,st)!==true;}),st,T);
  return lastRows;
}

// ── the URL is the state ─────────────────────────────────────────────────
function href(st,op,k,v){
  var u=new URLSearchParams(st.u.toString());
  function set(key,arr){if(arr.length)u.set(key,arr.join(','));else u.delete(key);}
  var cur=list(u,k),nots=list(u,'not'),bl=list(u,'blank'),hs=list(u,'has'),tag=k+':'+v;
  if(op==='add'){if(cur.indexOf(v)<0)cur.push(v);set(k,cur);
    set('not',nots.filter(function(x){return x!==tag;}));}
  else if(op==='only'){set(k,v?[v]:[]);}
  else if(op==='del'){set(k,cur.filter(function(x){return x!==v;}));}
  else if(op==='not'){set(k,cur.filter(function(x){return x!==v;}));
    if(nots.indexOf(tag)<0)nots.push(tag);set('not',nots);}
  else if(op==='unnot'){set('not',nots.filter(function(x){return x!==tag;}));}
  else if(op==='unblank'){set('blank',bl.filter(function(x){return x!==k;}));}
  else if(op==='unhas'){set('has',hs.filter(function(x){return x!==k;}));}
  else if(op==='word'){u.delete(k);}
  else if(op==='clear'){u=new URLSearchParams();}
  var s=u.toString();
  return location.pathname+(s?'?'+s:'');
}

// ── words for values ─────────────────────────────────────────────────────
var IX=null;
function tables(T){
  if(IX)return IX;
  IX={tag:{},ar:{},st:{}};
  (T.tags||[]).forEach(function(g){if(g&&g[0])IX.tag[g[0]]=[(g[3]?g[3]+' ':''),g[1],g[2]];});
  (T.trade||[]).forEach(function(r){if(r&&r[0]&&!IX.tag[r[0]])IX.tag[r[0]]=['',r[0],r[2]||''];});
  (T.areas||[]).forEach(function(a){if(a&&(a[0]||a[1]))IX.ar[a[0]||a[1]]=['',a[0]||a[1],a[3]||''];});
  (T.streets||[]).forEach(function(s){if(s&&s[0])IX.st[s[0]]=['',s[1]||s[2],s[2]||s[1]];});
  return IX;
}
function plain(k,v,T){
  // Plain text, because an <option> cannot hold a <span>: a bilingual pair
  // built with markup is drawn as literal tag soup inside a dropdown.
  if(k==='open')return 'เปิดอยู่ · open now';
  if(k==='f'){
    if(FW[v])return FW[v][0]+' · '+FW[v][1];
    // the five record tags arrive in this drawer and their words live in the
    // tag table, not in FACET_WORDS
    if(RECTAG[v]){var tr=tables(T).tag&&tables(T).tag[v];
      if(tr)return (tr[1]||'')+(tr[2]&&tr[2]!==tr[1]?' · '+tr[2]:'');}
    return v;}
  var ix=tables(T),row=ix[k]&&ix[k][v];
  if(row){var th=row[1]||'',en=row[2]||'';
    return row[0]+(en&&en!==th?th+' · '+en:(th||v));}
  if(k==='cat'&&typeof MD_CATWORDS!=='undefined'&&MD_CATWORDS[v])
    return String(MD_CATWORDS[v]).replace(/<[^>]*>/g,'');
  if(k==='su'&&T.subs&&T.subs[v])return T.subs[v][0]+' · '+T.subs[v][1];
  return v;
}
function label(k,v,T){
  if(k==='open')return BI('เปิดอยู่','open now');
  if(k==='f')return FW[v]?BI(FW[v][0],FW[v][1]):H(v);
  var ix=tables(T),row=ix[k]&&ix[k][v];
  if(row)return row[0]+BI(row[1],row[2]);
  if(k==='cat')return (typeof MD_CATWORDS!=='undefined'&&MD_CATWORDS[v])||H(v);
  if(k==='su'&&T.subs&&T.subs[v])return BI(T.subs[v][0],T.subs[v][1]);
  return H(v);
}
function presWord(k){var p=PRESENCE[k];return p?BI(p[0],p[1]):H(k);}

// ── the sentence: what is switched on, and how to switch it off ──────────
// Google shows the state inside its own controls; this site cannot, because
// the Tools row is shut by default and the four word fields live on another
// page. So the state is said in one line above the answer, and every part of
// it is a tap that removes that part.
function bar(st,T){
  var out=[],first=true;
  function push(html){if(!first)out.push('<span class="join">+</span>');
    first=false;out.push(html);}
  [['as_q','ทุกคำ','all'],['as_epq','วลี','phrase'],
   ['as_oq','คำใดคำหนึ่ง','any'],['as_eq','ไม่มีคำ','none']].forEach(function(w){
    var v=st.u.get(w[0]);if(!v)return;
    push('<a class="refterm'+(w[0]==='as_eq'?' no':'')+'" href="'+
      H(href(st,'word',w[0]))+'">'+BI(w[1],w[2])+': '+H(v)+
      '<span class="x" aria-hidden="true">×</span></a>');});
  if(st.scope&&st.scope!=='any'){
    var sc=null;SCOPES.forEach(function(s){if(s[0]===st.scope)sc=s;});
    if(sc)push('<a class="refterm" href="'+H(href(st,'word','as_in'))+'">'+
      BI(sc[1],sc[2])+'<span class="x" aria-hidden="true">×</span></a>');}
  KEYS.forEach(function(k){
    var vs=st.inc[k];if(!vs||!vs.length)return;
    if(!first)out.push('<span class="join">+</span>');
    first=false;
    vs.forEach(function(v,i){
      if(i)out.push('<span class="join">'+BI('หรือ','or')+'</span>');
      out.push('<a class="refterm" href="'+H(href(st,'del',k,v))+'">'+
        label(k,v,T)+'<span class="x" aria-hidden="true">×</span></a>');});});
  for(var b in st.blank)push('<a class="refterm" href="'+H(href(st,'unblank',b))+'">'+
    BI('ยังไม่มี','not yet: ')+presWord(b)+'<span class="x" aria-hidden="true">×</span></a>');
  for(var h in st.has)push('<a class="refterm" href="'+H(href(st,'unhas',h))+'">'+
    BI('มี','has: ')+presWord(h)+'<span class="x" aria-hidden="true">×</span></a>');
  st.not.forEach(function(n){
    out.push('<span class="join">−</span>');
    out.push('<a class="refterm no" href="'+H(href(st,'unnot',n[0],n[1]))+'">'+
      label(n[0],n[1],T)+'<span class="x" aria-hidden="true">×</span></a>');});
  var rad=st.u.get('radius'),pt=point(st);
  if(pt&&rad)push('<a class="refterm" href="'+H(href(st,'word','radius'))+'">'+
    BI('ในระยะ '+rad+' กม.','within '+rad+' km')+'<span class="x" aria-hidden="true">×</span></a>');
  else if(pt)push('<a class="refterm" href="'+H(href(st,'word','near'))+'">'+
    BI('วัดจากตำแหน่งของฉัน','measured from where you are')+'<span class="x" aria-hidden="true">×</span></a>');
  var so=st.u.get('sort');
  if(so){var sw=null;SORTS.forEach(function(x){if(x[0]===so)sw=x;});
    if(sw)push('<a class="refterm" href="'+H(href(st,'word','sort'))+'">'+
      BI('เรียง: '+sw[1],'sorted '+sw[2])+'<span class="x" aria-hidden="true">×</span></a>');}
  if(!out.length)return '';
  out.push('<a class="refclear" href="'+H(href(st,'clear'))+'">'+BI('ล้าง','clear')+'</a>');
  return out.join(' ');
}

// ── the Tools row: the same dropdowns, counted on THIS answer ────────────
function tally(base,st,k,T){
  var n={},total=0;
  for(var i=0;i<base.length;i++){var e=base[i];
    if(!ok(e,st,T,k))continue;total++;
    var vs=vals(e,k,T),seen={};
    for(var j=0;j<vs.length;j++){var v=vs[j];if(seen[v])continue;seen[v]=1;
      n[v]=(n[v]||0)+1;}}
  var rows=Object.keys(n).map(function(v){return [v,n[v]];});
  rows.sort(function(a,b){return b[1]-a[1]||(a[0]<b[0]?-1:1);});
  return {rows:rows,total:total};
}
function fillTools(base,T){
  var st=parse(),row=document.getElementById('toolrow');
  if(!row)return false;
  var anyOffer=false;
  row.querySelectorAll('select[data-refkey]').forEach(function(sel){
    var k=sel.dataset.refkey;
    if(NARROW.indexOf(k)<0)return;   // sort is not a narrowing key
    var t=tally(base,st,k,T),on=(st.inc[k]||[])[0]||'';
    var html='<option value="">'+H('ทั้งหมด · any')+'</option>';
    t.rows.forEach(function(r){
      // A value every row already carries narrows nothing, and a value at
      // zero is never reached. Neither is offered.
      if(r[1]>=t.total&&r[0]!==on)return;
      html+='<option value="'+H(r[0])+'"'+(r[0]===on?' selected':'')+'>'+
        H(plain(k,r[0],T))+' ('+r[1].toLocaleString()+')</option>';});
    sel.innerHTML=html;
    var none=t.rows.length===0;
    sel.disabled=none&&!on;
    if(!sel.disabled)anyOffer=true;});
  var box=row.querySelector('input[data-refkey="open"]');
  if(box){box.checked=!!(st.inc.open&&st.inc.open.length);
    box.disabled=!openTest;if(!box.disabled)anyOffer=true;}
  var sort=row.querySelector('select[data-refkey="sort"]');
  if(sort){sort.value=st.u.get('sort')||'';
    // Nearest-first is offered only once there is a point to measure from.
    var np=!point(st);
    sort.querySelectorAll('option[value="near"]').forEach(function(o){o.disabled=np;});
    anyOffer=true;}
  var mp=row.querySelector('input[data-refkey="mypos"]');
  if(mp){mp.checked=!!point(st);
    mp.disabled=!('geolocation' in navigator);if(!mp.disabled)anyOffer=true;}
  return anyOffer;
}
// ONE PLACE THE PANEL LEAVES THE PAGE. Every control here is a real
// navigation to a real URL, which is why the back button is undo and why a
// refinement can be sent to somebody. A host that would rather re-render in
// place — the prototype does, and md.js may one day (fork R4) — sets
// MDREFINE.onNav and gets the URL instead of losing the page.
function nav(url){
  if(window.MDREFINE&&typeof window.MDREFINE.onNav==='function'){
    window.MDREFINE.onNav(url);return;}
  location.href=url;
}
function wire(){
  var row=document.getElementById('toolrow');
  if(!row||row._wired)return;row._wired=true;
  row.addEventListener('change',function(ev){
    var el=ev.target,k=el.dataset&&el.dataset.refkey;
    if(!k)return;
    var st=parse();
    // NEAR ME ASKS ONLY WHEN IT IS TICKED, and a refusal is not an error:
    // the box goes back to unticked and everything else keeps working. The
    // page never asks for a position on its own.
    if(k==='mypos'){
      if(!el.checked){nav(href(st,'word','near'));return;}
      if(!navigator.geolocation){el.checked=false;return;}
      el.disabled=true;
      navigator.geolocation.getCurrentPosition(function(pos){
        var u=new URLSearchParams(st.u.toString());
        u.set('near',pos.coords.latitude.toFixed(5)+','+pos.coords.longitude.toFixed(5));
        if(!u.get('sort'))u.set('sort','near');
        nav(location.pathname+'?'+u.toString());
      },function(){el.checked=false;el.disabled=false;},{maximumAge:300000,timeout:8000});
      return;}
    if(k==='sort'||k==='radius'){
      var u2=new URLSearchParams(st.u.toString());
      if(el.value)u2.set(k,el.value);else u2.delete(k);
      var s2=u2.toString();
      nav(location.pathname+(s2?'?'+s2:''));return;}
    nav((el.type==='checkbox')
      ? href(st,'only',k,el.checked?'1':'')
      : href(st,'only',k,el.value));});
}
// ── the two doors on the answer ──────────────────────────────────────────
//
// A result is a set of PLACES, and there are exactly two other things a person
// does with a set of places: look at where they are, and put what is on at
// them in a diary. Both were reachable before this and neither was legible.
// The map was a bare 🗺 in the heading — no word, no number, and hidden until
// it was not — and the calendar existed one event at a time on a page nobody
// reaches from a search. They are links now. Each says what it will do, each
// carries the count of the answer in front of the reader, and neither is
// drawn at zero.
//
// WHAT THEY DO IS WHAT A PERSON WOULD EXPECT THEM TO DO:
//   🗺 draws THESE results on the map already sitting above them — not the
//      city map with its shelves switched on, which is a different question
//      wearing the same word (go/wrongtool). Tap again and it shuts, and the
//      label says so.
//   🗓 hands over the events standing at THESE places as one .ics file — the
//      same VEVENTs build.py writes, so what a reader gets from the door and
//      what they get from events.ics cannot disagree.
var MAPCAP=200;      // what md.js hands the results map, and what it draws
var lastRows=null;   // the filtered answer, stashed by apply()
function root(){return document.documentElement.getAttribute('data-root')||'';}
function nfmt(n){return Number(n).toLocaleString();}
// {place id: how many events stand there}, baked into search.html. Absent —
// on a page that carries no such table, or a build that has not written one
// yet — the calendar door is simply not drawn, and nothing is fetched.
function evTable(){
  var el=document.getElementById('evplaces');
  if(!el)return {};
  if(el._md)return el._md;
  var t={};
  try{t=JSON.parse(el.textContent)||{};}catch(e){t={};}
  el._md=t;
  return t;
}
// 184 of 1,796 rather than 184: the difference between the two numbers is the
// rows nobody has pinned yet. They are unmeasured, not absent, and saying so
// in the count is cheaper than a sentence saying so underneath.
function doorCount(shown,total){
  return total>shown
    ?'('+BI(nfmt(shown)+' จาก '+nfmt(total),nfmt(shown)+' of '+nfmt(total))+')'
    :'('+nfmt(shown)+')';
}
function drawDoors(rows){
  var el=document.getElementById('resdoors');
  if(!el)return;
  rows=rows||[];
  var out=[],shown=rows.slice(0,MAPCAP),pinned=0,i;
  for(i=0;i<shown.length;i++)if(shown[i].lat!=null&&shown[i].lng!=null)pinned++;
  var btn=document.getElementById('resmapbtn'),rm=document.getElementById('resmap');
  if(btn&&rm&&pinned){
    var open=!rm.hidden;
    out.push('<a class="resdoor" id="resdoor-map" href="#resmap">'+
      '<span class="dooricon" aria-hidden="true">🗺</span> '+
      (open?BI('ซ่อนแผนที่','hide the map')
           :BI('ดูบนแผนที่','see these on the map')+
             ' <span class="count">'+doorCount(pinned,rows.length)+'</span>')+'</a>');}
  // The join is the index row's own id against the event's place id, which is
  // the join md.js already makes to paint 🎪 into an opened row. A row with no
  // id joins to nothing — never to the string "undefined", which would hand
  // every row in the answer the same events.
  var T=evTable(),ids=[],n=0;
  for(i=0;i<rows.length;i++){var rid=rows[i].id;
    if(rid==null)continue;
    var c=T[rid];
    if(c){ids.push(rid);n+=c;}}
  if(n)out.push('<a class="resdoor" id="resdoor-cal" href="'+H(root()+'events.ics')+
    '" data-ids="'+H(ids.join(' '))+'">'+
    '<span class="dooricon" aria-hidden="true">🗓</span> '+
    BI('ใส่ปฏิทิน','add to calendar')+
    ' <span class="count">('+nfmt(n)+')</span></a>');
  el.innerHTML=out.join('');
  el.hidden=!out.length;
  wireDoors();
}

// ── the calendar file, mirrored from build.py's own ics_document ─────────
// Asia/Bangkok wall time, and the arithmetic is done in UTC so that adding
// two hours to an event cannot pick up the READER's daylight saving. Thailand
// has none; a browser in Berlin does.
//
// Escaped in build.py's order and not a tidier one. Folding [\r\n]+ to a
// single space instead of replacing each newline separately was five events
// out of 201 whose DESCRIPTION differed from the shipped events.ics by the
// width of a blank line — which tests/test_refine.py catches by comparing
// every VEVENT against the file build.py wrote.
function icsEsc(s){return String(s==null?'':s).replace(/\\/g,'\\\\')
  .replace(/;/g,'\\;').replace(/,/g,'\\,').replace(/\n/g,' ').replace(/\r/g,'');}
function wall(s){
  var m=/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(String(s||''));
  if(!m)return null;
  return new Date(Date.UTC(+m[1],+m[2]-1,+m[3],+(m[4]||0),+(m[5]||0),+(m[6]||0)));
}
function icsStamp(d){function p(n){return (n<10?'0':'')+n;}
  return d.getUTCFullYear()+p(d.getUTCMonth()+1)+p(d.getUTCDate())+'T'+
    p(d.getUTCHours())+p(d.getUTCMinutes())+p(d.getUTCSeconds());}
var BYDAY=['MO','TU','WE','TH','FR','SA','SU'];
var VTZ='BEGIN:VTIMEZONE\r\nTZID:Asia/Bangkok\r\nBEGIN:STANDARD\r\n'+
  'DTSTART:19700101T000000\r\nTZOFFSETFROM:+0700\r\nTZOFFSETTO:+0700\r\n'+
  'TZNAME:+07\r\nEND:STANDARD\r\nEND:VTIMEZONE\r\n';
function vevent(e){
  var s=wall(e.start);if(!s)return '';
  var t=wall(e.end)||new Date(s.getTime()+7200000);
  var p=e.place||{},where=p.name||e.venue_name||'';
  var L=['BEGIN:VEVENT',
    'UID:'+icsEsc((e.source||'md')+'-'+(e.uid||e.title||'')+'@motdang.net'),
    'DTSTAMP:'+icsStamp(new Date(Date.UTC(2026,0,1))),
    'DTSTART;TZID=Asia/Bangkok:'+icsStamp(s),
    'DTEND;TZID=Asia/Bangkok:'+icsStamp(t),
    'SUMMARY:'+icsEsc(e.title)];
  if(e.recurring&&e.weekday!=null&&BYDAY[e.weekday])
    L.push('RRULE:FREQ=WEEKLY;BYDAY='+BYDAY[e.weekday]);
  else if(e.recurring&&e.byday&&e.byday.length)
    L.push('RRULE:FREQ=WEEKLY;BYDAY='+e.byday.join(','));
  if(where)L.push('LOCATION:'+icsEsc(where));
  // FOUR HUNDRED CHARACTERS, NOT FOUR HUNDRED CODE UNITS. build.py cuts the
  // description in Python, where an emoji is one character; a JavaScript
  // slice counts it as two and cut five of the 201 events short of where the
  // shipped events.ics cut them. Array.from splits on code points.
  if(e.description)L.push('DESCRIPTION:'+
    icsEsc(Array.from(String(e.description)).slice(0,400).join('')));
  if(e.url)L.push('URL:'+icsEsc(e.url));
  L.push('END:VEVENT');
  return L.join('\r\n')+'\r\n';
}
function icsDoc(evs,name){
  var body='';for(var i=0;i<evs.length;i++)body+=vevent(evs[i]);
  return 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Mot Dang//motdang.net//EN\r\n'+
    'CALSCALE:GREGORIAN\r\nMETHOD:PUBLISH\r\nX-WR-CALNAME:'+icsEsc(name)+'\r\n'+
    'X-WR-TIMEZONE:Asia/Bangkok\r\n'+VTZ+body+'END:VCALENDAR\r\n';
}
// The file is named after the search, so a reader who saves two of them can
// tell them apart in a downloads folder. A Thai query leaves no ascii to name
// it with and gets the plain name rather than a row of escapes.
function calName(){var q=(parse().q||'').trim();
  return q?('มดแดง · '+q):'มดแดง · Mot Dang';}
function calFile(){
  var q=(parse().q||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
  return 'motdang-'+(q?q.slice(0,40):'events')+'.ics';}
function save(text,name){
  try{
    var b=new Blob([text],{type:'text/calendar;charset=utf-8'});
    var u=URL.createObjectURL(b),a=document.createElement('a');
    a.href=u;a.download=name;a.style.display='none';
    document.body.appendChild(a);a.click();
    setTimeout(function(){URL.revokeObjectURL(u);
      if(a.parentNode)a.parentNode.removeChild(a);},4000);
  }catch(e){}
}
function wireDoors(){
  var el=document.getElementById('resdoors');
  if(!el||el._wired)return;el._wired=true;
  el.addEventListener('click',function(ev){
    var a=ev.target&&ev.target.closest?ev.target.closest('a.resdoor'):null;
    if(!a)return;
    if(a.id==='resdoor-map'){
      ev.preventDefault();
      var btn=document.getElementById('resmapbtn');if(!btn)return;
      btn.click();
      var rm=document.getElementById('resmap');
      if(rm&&!rm.hidden&&rm.scrollIntoView)rm.scrollIntoView({block:'nearest'});
      drawDoors(lastRows);
      // openMap() gives up after eight seconds when no basemap arrives and
      // shuts the box again. The label has to follow it back, or it sits
      // there offering to hide a map that is not there.
      setTimeout(function(){drawDoors(lastRows);},8600);
      return;}
    if(a.id!=='resdoor-cal')return;
    // THE EVENTS ARE FETCHED ONLY BY THE READER WHO ASKS FOR THEM. The count
    // above comes from a 2 kB table baked into the page; the 260 kB of event
    // records behind it is downloaded on this tap and on no other search.
    ev.preventDefault();
    if(a._busy)return;
    a._busy=1;a.setAttribute('aria-busy','true');
    var want={};(a.getAttribute('data-ids')||'').split(' ')
      .forEach(function(x){if(x)want[x]=1;});
    var done=function(){a._busy=0;a.removeAttribute('aria-busy');};
    fetch(root()+'data/events.json').then(function(r){return r.ok?r.json():null;})
      .then(function(d){done();
        if(!d)return;
        var mine=(d.events||[]).filter(function(e){
          return e&&e.place&&want[e.place.id]&&e.start;});
        if(mine.length)save(icsDoc(mine,calName()),calFile());})
      .catch(done);
  });
}

function draw(base,T,el){
  el=el||document.getElementById('refine');if(!el)return;
  var st=parse(),b=bar(st,T),bx=document.getElementById('refbar');
  if(bx)bx.innerHTML=b;
  wire();
  var offers=fillTools(base,T);
  var tools=document.getElementById('reftools');
  if(tools)tools.hidden=!offers;
  el.hidden=!(b||offers);
  // The doors are about the rows on screen, not about the set the counts are
  // drawn against, so they take the answer apply() kept — never `base`.
  drawDoors(lastRows||base);
}
window.MDREFINE={parse:parse,apply:apply,draw:draw,href:href,vals:vals,ok:ok,
  bar:bar,tally:tally,fillTools:fillTools,wordsOk:wordsOk,text:text,KEYS:KEYS,
  sort:sortRows,dist:dist,fullness:fullness,onNav:null,
  doors:drawDoors,ics:icsDoc,
  setOpenTest:function(fn){openTest=fn;}};
})();
"""

import json as _json


def _js_consts():
    """The tables the engine needs, poured in at import time.

    Written once here rather than twice — the Python side owns the vocabulary
    and the JavaScript reads a copy, so a facet word or a scope cannot be
    right on one surface and stale on the other.
    """
    fields = {code: names.split() for code, _, _, names in WORD_SCOPES}
    return {
        "__NARROW__": _json.dumps([k for k, _, _, _ in NARROW_ROWS]),
        "__RECORD_TAGS__": _json.dumps({t: 1 for t in RECORD_TAGS}),
        "__WORD_FIELDS__": _json.dumps(fields),
        "__FACET_WORDS__": _json.dumps(FACET_WORDS, ensure_ascii=False),
        "__SCOPES__": _json.dumps([[c, th, en] for c, th, en, _ in WORD_SCOPES],
                                  ensure_ascii=False),
        "__PRESENCE__": _json.dumps({k: [th, en] for k, th, en in PRESENCE_ROWS},
                                    ensure_ascii=False),
        "__SORTS__": _json.dumps([[v, th, en] for v, th, en in SORT_ROWS if v],
                                 ensure_ascii=False),
    }


for _k, _v in _js_consts().items():
    JS = JS.replace(_k, _v)
def header(r, bi, att, svg_icon, logo_html, lang_html, strip_html=""):
    """logo · language · the box — and on the front page, the one line.

    What is gone from here, and it is most of what was here: the tagline, the
    ☰ <details>, the nine chipbar chips, the five svcbar families and their
    27 links. The logo keeps its href to the front page, which is the whole
    of the site's up-navigation now and was always the part readers used.

    `strip_html` is nownear_layer.strip() and arrives EMPTY on every page but
    the front one — her call, 2026-09-07: the line is a front-page thing.
    """
    return f"""<header class="site slim bare">
  <div class="mast">
    {logo_html}
    {lang_html}
    <button type="button" class="readbtn" data-read aria-pressed="false"
            aria-label="{att(bi_text("อ่านง่าย — แบบอักษรสำหรับผู้มีปัญหาการอ่านและสายตาเลือนราง",
                                     "Easy read — a typeface for dyslexia and low vision"))}">{bi("อ่านง่าย", "Easy read")}</button>
  </div>
  <form class="seek" action="{r}search.html" method="get">
    <label class="vh" for="q">{bi("ค้นหา", "Search")}</label>
    <input id="q" name="q" type="search" placeholder="ค้นหาชื่อร้าน วัด คลินิก… / search">
    <button aria-label="{att(bi_text("ค้นหา", "Search"))}">{svg_icon("i-search", 22, "rowicon")}{bi("ค้นหา", "Search")}</button>
  </form>
  {strip_html}
</header>"""


# ─────────────────────────────────────────────── the Python side of the engine
#
# `vals` above, in Python, so build.py can bake the advanced form's dropdowns
# off the same reading of a row that the results page filters by. Two readings
# of one row is how a form comes to offer a district that returns nothing: the
# count said 41 because the tally counted `ar` one way and the engine read it
# another. One function, mirrored, and tests/test_refine.py checks the mirror.
def row_values(e, k, T):
    """Every value row `e` carries under narrowing key `k`. Mirrors vals()."""
    out = []
    if k == "tag":
        for i in e.get("t") or []:
            g = _tbl(T, "tags", i)
            if g and g[0] and g[0] not in RECORD_TAGS:
                out.append(g[0])
        for i in e.get("tt") or []:
            g = _tbl(T, "trade", i)
            if g and g[0]:
                out.append(g[0])
    elif k == "ar":
        a = _tbl(T, "areas", e.get("ar"))
        if a and (a[0] or a[1]):
            out.append(a[0] or a[1])
    elif k == "st":
        s = _tbl(T, "streets", e.get("st"))
        if s and s[0]:
            out.append(s[0])
    elif k in ("f", "su", "kd"):
        out = list(e.get(k) or [])
        if k == "f":
            for i in e.get("t") or []:
                g = _tbl(T, "tags", i)
                if g and g[0] in RECORD_TAGS:
                    out.append(g[0])
    elif k == "cat":
        out = list(e.get("c") or [])
    elif k == "p":
        out = [e["p"]] if e.get("p") else []
    elif k == "pin":
        out = ["1"] if e.get("lat") is not None and e.get("lng") is not None else []
    elif k == "hk":
        out = ["1"] if e.get("hk") is not None else []
    # `open` is deliberately absent: it is answered against a clock, and a
    # dropdown baked at build time cannot carry a count that changes hourly.
    return out


def _tbl(T, name, i):
    if i is None:
        return None
    rows = (T or {}).get(name) or []
    return rows[i] if isinstance(i, int) and 0 <= i < len(rows) else None


def bake_options(rows, T, cap=OPTION_CAP):
    """{key: [(value, th, en, count), …]} for advanced_form(), tallied off the
    index rows build.py has just written. Longest list first; a value nobody
    carries is never offered."""
    import collections
    out = {}
    for k, _th, _en, _ in NARROW_ROWS:
        c = collections.Counter()
        for e in rows:
            for v in set(row_values(e, k, T)):
                c[v] += 1
        words = FACET_WORDS if k == "f" else {}
        out[k] = [(v, words.get(v, (v, ""))[0], words.get(v, (v, ""))[1], n)
                  for v, n in c.most_common(cap)]
    return out


# ────────────────────────────────────────────────────────────── the bare shell
def home_body(strip_html=""):
    """The front page below the box. `strip_html` is nownear_layer.strip(),
    which the header already carries on the front page, so this is normally
    empty — the argument stays so a caller can put the line here instead.

    An h1 for the page still exists and is read aloud; it is not drawn. A
    document with no heading is a document a screen reader cannot summarise,
    and drawing one would put a second line of type above an empty page."""
    return (f'<h1 class="vh">มดแดง · Mot Dang</h1>{strip_html}')


def bare_footer(r, bi, emergency_foot, build_date, be_build, lic_th, lic_en,
                extra_html=""):
    """The minimal footer. What is here is here for a reason that is not
    housekeeping: the four numbers, because a person looking for a hospital at
    2 a.m. is the reader this site was built for; the OSM line, because it is
    a licence condition and not decoration; the date, because a directory that
    will not say when it was last read is not a directory; ทุกชั้น, because
    without it 25,889 pages have no inbound link but the sitemap.

    Everything else that stood here — RSS, partners, the fix log, Ko-fi,
    llms.txt, the picture credits — is still built and still at its own
    address. `extra_html` is where a caller puts any of it back."""
    return f"""<footer class="bare">
  <div class="footsos">{emergency_foot(r)}</div>
  <span class="footline"><a href="{r}all.html">{bi("ทุกชั้น ทุกหมวด", "every shelf")}</a> ·
  <a href="{r}source/">{bi("โค้ดและข้อมูลดิบ", "source and raw data")}</a> ·
  <a href="{r}api/">API</a> ·
  <a href="{r}privacy.html">{bi("ความเป็นส่วนตัว", "Privacy")}</a> ·
  <a href="{r}terms.html">{bi("เงื่อนไขการใช้ข้อมูล", "Terms of use")}</a>{extra_html}</span>
  <span class="footline">{bi(f"ปรับปรุง {build_date} (พ.ศ. {be_build})",
      f"updated {build_date} (B.E. {be_build})")} ·
  © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap contributors</a> (ODbL)</span>
  <span class="licence">{bi(lic_th, lic_en)}</span>
</footer>"""
