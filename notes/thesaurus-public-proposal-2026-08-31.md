# คำที่ร้านใช้ — the thesaurus made a page

Nan, 2026-08-31, on the flat-sheet order: *"I think the thesaurus itself could
benefit the public if it's made available in a friendly UX kind of way…
shouldn't just be background knowledge."*

She is right, and the site has been half-admitting it for a while. When search
widens a query through the table it already tells the reader it did —
`build.py:3448` prints **รวมคำที่ความหมายเดียวกัน · including words that mean
the same thing**. So a reader is informed that a table of words exists, acted
on their query, and changed what they saw. They are given no way to look at it.

## What the table already is — measured

`data/search_thesaurus.json`, mined by `mine.py` from Mot Dang's own data:

- **2,753 groups · 7,427 terms**, 2.7 terms per group, largest group 25.
- **Every one of the 2,753 is bilingual.** There is no monolingual group in
  the file. That is unusual enough to be the whole product.
- Its own note: *"synonymy only, spelling variants are the phonetic key's
  job"* — so this is a meaning table, not a misspelling table, which is
  precisely what makes it readable by a human.
- **Fetched, not baked** (`build.py:3350–3356`). It is already a public URL
  that a reader's browser downloads. Publishing it is not a new exposure; it
  is putting a door on a room the site already ships.
- An edit busts the asset hash (`build.py:5408`), so the page cannot go stale
  against the search.
- Mining took it from 76 groups to 2,290 and it now stands at 2,753 — the
  growth is the point. Nobody hand-wrote this.

## What it is not, and this decides the design

Only **1,149 of the 2,753 groups have any footprint in the 20,778-record
catalogue** — a term matching a category value, or appearing in three or more
place names. The other **1,604 are general-language synonymy**:

    ["abate", "allay", "decrease", "ease", "meliorate", "บรรเทา"]
    ["-less", "absence", "lack", "ขาด"]
    ["abject", "buns", "dire", "terrible", "แย่"]

Useful to a search engine widening a query. Useless on a page, and worse than
useless as a publication: it would make Mot Dang look like it is offering a
Thai–English dictionary, which it is not, has not audited, and should not be
judged as. **The publishable set is the 1,149, and the filter is the design.**

### A finding I nearly published, and it was false

I first measured that 34 of 165 category values carry no thesaurus term —
`hotel-full` (911 records), `health-station` (469), `bar-pub` (460),
`street-food` (232) — and was about to write it up as a coverage hole. It is
not one. Those are internal slugs. Checked directly, the trade words behind
them are all present: hotel · โรงแรม · bar · บาร์ · ผับ · street food ·
อาหารริมทาง · bakery · เบเกอรี่ · spa · สปา · museum · พิพิธภัณฑ์. Recorded
here because the next person to run that query will get the same wrong answer.

## The shape

**A browsable page, `/kham.html`** — คำ, *kham*, word. Yahoo-directory
discipline, which this site already uses elsewhere: **Term (count)**, quiet,
scannable, no search box required to begin.

The reverse direction is the actual product. Search answers *"I typed this,
what did you find?"* The page answers ***"what do they call this here?"*** —
which is the question a reader has before they know a word to type, and the
one that made the ขัดขี้ไคล shelf and will make the bedding one.

1. **Group pages for the 1,149.** Each shows every term in both scripts, how
   many catalogue records each term reaches, and a link to the shelf it opens.
   A dead term — one in the table with zero records behind it — is shown as
   dead rather than hidden, because that is a reader telling us where to crawl.
2. **The search line becomes a link.** The single highest-value change in this
   order and the smallest: where the search already says *including words that
   mean the same thing*, name the words and link the group. One line of
   `md.js`, and the invisible machinery becomes visible at the exact moment
   the reader is wondering what just happened.
3. **Entry from the shelves.** A shelf header carries the words its trade is
   known by, so ขัดขี้ไคล / ระเบิดขี้ไคล sit on the scrub shelf and are
   readable without a search.
4. **No new mining, no network.** Every measurement above came from files on
   disk.

## What must not ship

- **Not as a dictionary, and not with a translation voice.** This is a record
  of what businesses in two provinces call themselves. Every gloss must read
  as *"shops here say this"*, never as *"the Thai for X is Y"*. The site is not
  a language authority and the moment it sounds like one it is wrong.
- **Provenance is the blocker, and it is real.** House law is that provenance
  travels with every fact. Right now 7,427 terms travel with one sentence —
  *mined by mine.py from motdang data*. That is adequate for machinery nobody
  reads and thin for a page with a byline on it. Two ways out: per-group
  provenance written by `mine.py` on its next run, which is the correct fix and
  costs a mining pass; or the page states plainly and prominently that these
  are mined from listings and unaudited, which is cheap, true, and available
  today. **This is a fork for Nan, not a decision I should make.**
- **The 1,604 stay behind the search.** They keep working; they do not get
  pages.
- **Northern Thai needs its own handling before it is displayed.** The table
  already carries กาด beside ตลาด and เฮือง beside เรือง. Presented flatly as
  synonyms, that flattens Lanna into a spelling variant of Central Thai, which
  is exactly the error this site exists not to make. Marked as คำเมือง, it
  becomes one of the better reasons to visit the page.

## Why now

WO-46 is this page's proof case. A reader wants a flat sheet, has no Thai word
for one, and the catalogue holds nothing under any word they own. Fixing that
one question means adding a thesaurus group. Doing it as a page means the next
thousand readers with the next thousand questions can find the word without
anyone writing them a bespoke answer.

The site's own lesson, third time stated: the fix was never a better crawl. It
was asking what the shops call it. That knowledge currently lives in a JSON
file that only a search box can read.
