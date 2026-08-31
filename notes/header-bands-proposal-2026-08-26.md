# WO-34 — ห้าครอบครัว: banding the quiet row · 2026-08-26

*Nan asked: "based on how motdang.net is growing, could it be organized/
navigated better?" and, of the four findings, said "one at a time." This is
item 1 and only item 1.*

**Zero network.** One markup block and two CSS rules in `build.py`, nothing
else touched. No data, no crawls, no new pages.

## What was measured

The header's secondary row (`.svcbar`, the "quiet row" in the CSS's own
words) had grown to **21 links in one undifferentiated run**, on every page
of the site — each work order since WO-12 adding one more door to the end of
the line. For a reader tabbing through with a screen reader or low vision,
that is 21 stops of mixed purpose between the search box and the directory.
Six of those labels also appear again in the homepage category grid
(transport, beauty, muay thai, cooking, chang, festivals ×2), so the same
word sat on the page twice pointing at two different addresses with nothing
saying why.

## What was built

The same 21 links + Ko-fi, none removed, none renamed, regrouped into
**five labeled families** (`.svcgrp`, opened by a `.svclbl` that is a label,
not a door):

1. **เมือง · The city** — tags · roads-and-sois · getting around · open now
2. **กิจกรรม · Things to do** — muay thai tonight · cooking classes ·
   elephants · hot springs · hair-and-barbers *(the boards — the pages that
   say what places STATE, kept apart from the shelves that list places)*
3. **ดวง-เทศกาล · Stars & seasons** — horoscopes · four pillars · festivals ·
   festival dates · nine temples
4. **ช่วยมด · Help the ants** — add contacts · request a crawl · ask the ants
5. **มดแดง · The ants** — widgets · stats · advertise · Ko-fi

Desktop: each family keeps its own line, label in the mute ink with a gold
bead after it — quiet stays quiet. Phone: the one swipeable row survives
untouched; the labels now ride along in it as milestones, so a thumb learns
where it is without a map. Both the URL of every door and the words on every
door are exactly what they were — no link rot, no bookmark broken, no
retraining anyone's hand.

## What this does to the twice-listed six

Nothing is removed. The band label now *says* why the word appears twice:
"กิจกรรม" in the header is the board (states, nights, prices); the category
grid below is the shelf (places). The legibility was the problem, not the
duplication itself.

## Only Nan can decide (numbered, for later — none of these were done)

1. **Trim the boards from the header entirely?** They would remain one click
   away via their shelf's band (the `mtband` pattern already built). Saves
   five links on every page; costs the one-tap "muay thai tonight" reach.
2. **Move ลงโฆษณา · Advertise down to the footer?** It already lives in the
   ad boxes; header space is the dearest on the site.
3. **Band order.** Current: city → things to do → stars → help → ants.
   Any other order is a one-line swap.

## Still on the list from the same survey (untouched, in order)

- **Item 2** — the food shelf is a 4.2 MB single page (4,151 places, 4,227
  links) while ten sub-shelves already exist as folders beside it; make the
  index a hub, complete roll stays under `lists/`.
- **Item 3** — `learn/` slug vs "กีฬา-ฟิตเนส · Sport & Fitness" label
  mismatch.
- **Item 4** — CM feature pages sit at site root while categories live under
  `/cm/`; a re-root plan (redirects included) before Chiang Rai makes every
  root page ambiguous.
