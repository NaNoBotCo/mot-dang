"""/trades.html — the words the shops write on themselves, with a reading and
an English equivalent for each.

Nan, 2026-09-08, on the trade vocabulary having no page: *"Work on this — should
also be translated/transliterated."*

data/trade_lexicon.json holds 1,782 Thai trade words read off the shops
themselves — ซ่อมมอเตอร์ไซค์, ตู้น้ำดื่มหยอดเหรียญ, ปะยางมอเตอร์ไซค์. Until
today they reached a reader only as a field on a place page and as a query the
search box would run if you already knew the word to type. 326 of them carried
an English equivalent; the rest stood in Thai with an RTGS reading beside them,
and 93 had no reading the rules would stand behind.

This page is the index that was missing, and the same pass filled the file
behind it: every one of the 1,782 now carries a gloss and a reading.

THREE COLUMNS, ONE ROW. Thai · reading · English, in that order, because that
is the order the sign, the tongue and the dictionary come in — and because the
same three parts, in the same order, already sit on every place page
(build.trade_tags_row). A word looks the same wherever the reader meets it.

A ROW IS A LINK. Every term goes to `search.html?tag=<the Thai>` — the query
the place page's own tags already run, so this page adds a door and no new
machinery behind it.

THE COUNT IS ON EVERY DOOR, and a term at zero is not drawn. Same rule as the
refine panel: a reader can see how many rows are behind a word before spending
a tap on it.

ORDERED THE THAI WAY. Not by codepoint — codepoint order files เ แ โ ใ ไ after
ฮ, so every word that begins with a leading vowel (เปลี่ยน, แก้ทรง, ไวนิล) lands
in a heap at the end where no Thai reader would look for it. thai_key() moves a
leading vowel behind its consonant and drops the tone marks, which is how a Thai
dictionary is ordered and how the reader expects to find เปลี่ยนยาง under ป.

Latin-initial terms (CNC, Invisalign, coworkingspace) get their own A–Z block
rather than being romanised into the Thai alphabet, because that is where they
are written on the sign.

THE FILTER TYPES ACROSS ALL THREE. One box, matching Thai OR reading OR gloss,
so "motorcycle" and "มอเตอร์ไซค์" and "Motoesai" all reach the same 40 rows. It
is progressive: every row is real HTML and the page is complete with JavaScript
off — the box only hides.

Called from build.py: build_trades_page() near the other single-page builders,
CSS appended where style.css is written. The script is its own trades.js rather
than a block in md.js — it runs on one page, and every other page on the site
would otherwise have carried it.
"""

# The Thai alphabet in dictionary order. The rail is drawn from this, and only
# the letters that actually carry a term are shown.
THAI_ALPHABET = (
    "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")

# Leading vowels: written before their consonant, sorted after it.
LEADING_VOWELS = "เแโใไ"

# Tone marks, the silencer, and the vowels that hang off a consonant. Dropped
# from the sort key so that ซ่อม and ซอม file together.
DIACRITICS = "ัิีึืฺุู็่้๊๋์ํ๎"

_ORDER = {c: i for i, c in enumerate(THAI_ALPHABET)}


def initial(term):
    """The letter a Thai reader would look this term up under.

    A leading vowel is not a letter you file under; the consonant it is written
    in front of is. Returns "" for a term that starts with Latin or a digit —
    those go to the A–Z block instead.
    """
    for ch in term:
        if ch in LEADING_VOWELS:
            continue
        if ch in _ORDER:
            return ch
        if ch in DIACRITICS:
            continue
        return ""
    return ""


def thai_key(term):
    """Dictionary order: leading vowel behind its consonant, tone marks gone."""
    out, i, n = [], 0, len(term)
    while i < n:
        ch = term[i]
        if ch in DIACRITICS:
            i += 1
            continue
        if ch in LEADING_VOWELS and i + 1 < n:
            nxt = term[i + 1]
            if nxt in _ORDER:
                out.append((_ORDER[nxt], 0))
                out.append((100 + LEADING_VOWELS.index(ch), 0))
                i += 2
                continue
        out.append((_ORDER.get(ch, 200 + ord(ch) % 200), ord(ch)))
        i += 1
    return out


def sort_key(term):
    """Thai terms in Thai order; Latin terms after them, case-blind."""
    ini = initial(term)
    if ini:
        return (0, thai_key(term))
    return (1, [(ord(c.lower()), 0) for c in term])


def rows(lex):
    """[(letter, [(term, entry), …]), …] — Thai letters in alphabet order, the
    Latin block last. A letter with nothing under it is never returned."""
    by = {}
    for term, e in lex.items():
        by.setdefault(initial(term) or "#", []).append((term, e))
    out = []
    for letter in THAI_ALPHABET:
        if letter in by:
            out.append((letter, sorted(by[letter], key=lambda kv: sort_key(kv[0]))))
    if "#" in by:
        out.append(("#", sorted(by["#"], key=lambda kv: sort_key(kv[0]))))
    return out


def _row(term, e, esc, att, r):
    """One term: Thai · reading · gloss · count, the whole line a link.

    NOT the .th/.en spans the rest of the site wraps bilingual text in. Those
    exist so the language toggle can hide one half, and on this page there is no
    half to hide: the Thai word IS the entry and the reading and gloss are how a
    reader who cannot read it gets in. Hiding either would empty the row. Plain
    <b>/<i> also costs 110 bytes a row less, which over 1,782 rows is the
    difference between a page that opens on a phone in a village and one that
    does not.

    The Thai rides raw in the href rather than percent-encoded (125 kB of %XX
    over this many rows); the browser encodes it on the way out, so it reaches
    search.html as the same query build.trade_tags_row sends.
    """
    href = f"{r}search.html?tag={esc(term)}"
    row = f'<li><a href="{href}"><b lang="th">{esc(term)}</b>'
    reading = (e.get("reading") or "").strip()
    if reading and reading.lower() != term.strip().lower():
        row += f' <i>{esc(reading)}</i>'
    gloss = (e.get("gloss") or "").strip()
    if gloss:
        row += f" — {esc(gloss)}"
    return row + f'</a> <s>{(e.get("n") or 0):,}</s></li>'


def body(lex, bi, esc, att, r=""):
    """The page: one line, the filter, the rail, then the terms."""
    groups = rows(lex)
    total = sum(len(v) for _, v in groups)

    rail = " ".join(
        f'<a href="#t-{i}">{esc(letter)} <span class="count">{len(items)}</span></a>'
        for i, (letter, items) in enumerate(groups))

    blocks = []
    for i, (letter, items) in enumerate(groups):
        head = (bi("อักษรละติน", "Latin letters") if letter == "#"
                else f'<span class="th solo" lang="th">{esc(letter)}</span>')
        blocks.append(
            f'<section class="tradeblock"><h2 id="t-{i}">{head} '
            f'<span class="count">({len(items):,})</span></h2>'
            f'<ul class="trades">'
            + "".join(_row(t, e, esc, att, r) for t, e in items)
            + "</ul></section>")

    lede = bi(
        f"คำที่ร้านเขียนไว้เองว่าทำอะไร {total:,} คำ พร้อมคำอ่านและคำแปล "
        "กดคำไหนก็เห็นร้านที่ลงคำนั้นไว้",
        f"{total:,} words the shops write on themselves, each with its reading "
        "and an English equivalent. Tap one for the places that list it.")

    box = (
        '<div class="tradefind">'
        f'<label for="tradeq">{bi("หาคำ", "find a word")}</label>'
        '<input id="tradeq" type="search" autocomplete="off" '
        f'placeholder="{att("มอเตอร์ไซค์ · motorcycle · Motoesai")}">'
        f'<span class="tradecount" data-total="{total}"></span></div>')

    return (f'<h1>{bi("คำบนป้าย", "Words on the signs")} '
            f'<span class="count">({total:,})</span></h1>'
            f'<p class="lede">{lede}</p>'
            f'{box}'
            f'<nav class="traderail" aria-label="{att("ตัวอักษร Letters")}">{rail}</nav>'
            + "".join(blocks))


CSS = """
/* /trades.html — the trade vocabulary */
.tradefind{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:.6rem 0}
.tradefind label{font-size:.85rem;opacity:.75}
.tradefind input{flex:1 1 14rem;min-width:0;padding:.45rem .6rem;font-size:1rem;
  border:1px solid var(--warm-border);border-radius:.3rem;
  background:var(--paper);color:inherit}
.tradecount{font-size:.85rem;opacity:.7;font-variant-numeric:tabular-nums}
.traderail{display:flex;flex-wrap:wrap;gap:.3rem .55rem;margin:.5rem 0 1rem;
  font-size:.95rem;line-height:1.9}
.traderail a{text-decoration:none;padding:0 .15rem}
.traderail a .count{font-size:.7rem;opacity:.55;margin-left:.1rem}
.tradeblock h2{font-size:1.15rem;margin:1.1rem 0 .3rem;border-bottom:1px solid var(--warm-border)}
ul.trades{list-style:none;padding:0;margin:0;
  columns:2;column-gap:1.6rem;column-rule:1px solid var(--warm-border)}
ul.trades li{break-inside:avoid;margin:0 0 .18rem;line-height:1.45}
ul.trades li[hidden]{display:none}
ul.trades a{text-decoration:none}
ul.trades a:hover b{text-decoration:underline}
ul.trades b{font-weight:600}
ul.trades i{opacity:.7;font-size:.9em;font-style:normal}
ul.trades s{text-decoration:none;opacity:.5;font-size:.8em;
  font-variant-numeric:tabular-nums}
ul.trades s::before{content:"("}
ul.trades s::after{content:")"}
.tradeblock[hidden]{display:none}
@media(max-width:44rem){ul.trades{columns:1}}
"""

JS = """
/* /trades.html — one box across Thai, reading and gloss. Progressive: the
   rows are already on the page, this only hides. */
(function(){
 var q=document.getElementById('tradeq');if(!q)return;
 var out=document.querySelector('.tradecount'),
     blocks=[].slice.call(document.querySelectorAll('.tradeblock')),
     rail=document.querySelector('.traderail'),
     rows=[].slice.call(document.querySelectorAll('ul.trades li')),
     total=out?+out.dataset.total:rows.length,t;
 /* The searchable text is read off the rows once, at load, rather than shipped
    a second time in a data- attribute: 1,782 rows of Thai + reading + gloss is
    119 kB of duplication the reader would pay for on every visit. */
 var hay=rows.map(function(li){return li.textContent.toLowerCase();});
 function say(n){if(out)out.textContent=n===total?'':n.toLocaleString()+' / '+total.toLocaleString();}
 function run(){
  var v=q.value.trim().toLowerCase(),n=0;
  rows.forEach(function(li,i){var hit=!v||hay[i].indexOf(v)>-1;li.hidden=!hit;if(hit)n++;});
  blocks.forEach(function(b){
   b.hidden=!b.querySelector('ul.trades li:not([hidden])');});
  if(rail)rail.hidden=!!v;
  say(n);
 }
 q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,90);});
 say(total);
})();
"""
