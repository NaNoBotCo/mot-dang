# นวด — making the massage shelf granular enough to walk into

Proposal, 2026-08-17. Status: draft for reaction, nothing built.

## Where we stand

294 massage records across CM + CR. Their entire enrichment is:

```
attrs: { inOldCity: true|false }
```

`sub` is empty on all but four (and those four are miscodes — a laundry, a
café). The category tree gives the shelf two children, ในเวียง / นอกเวียง,
which `build.py` already notes is a split the tree does not really have.
So today the shelf answers exactly one question: *is it inside the moat*.

Name-mining test over all 294 (script in this note's commit message):
36% of names declare anything at all — 53 say some form of "Thai massage",
36 say "spa", 12 say "health", 2 say "blind", 2 "herbal", 2 "oil", 2 "foot",
0 say ตอกเส้น. Names are a seed, not an answer. The fill has to come from
somebody standing at the door.

## The mistake we are actually preventing

It is not one mistake, it is four, and only one of them is the one people
joke about:

1. Wants an ordinary shop, walks into an **อาบอบนวด** (àap òp nûat, "bathe-
   steam-massage") — a different licence, a different trade, and one that
   advertises itself plainly if you can read the sign.
2. Wants to relax, books **นวดจับเส้น** (càp sên, "seize the sen-lines") and
   gets an hour of therapeutic pain they did not consent to.
3. Wants oil and a table, gets a floor mat in a shared room, fully clothed.
4. Wants a table and privacy, gets a curtained room and then cannot read the
   situation — which is the same information gap as (1), only from inside.

All four are the same failure: **the encounter is not described anywhere
before you are in it.** Granularity is the fix, but only if it describes the
service, never the suspicion.

## House rule this must obey

`data/facets.json` already says it, and it governs here more than anywhere:

> A facet with no evidence renders as nothing at all: absent is not the same
> as false, and a directory that guesses 'no ATM' is worse than one that says
> nothing.

A directory that guesses about a massage shop is worse still — it is a slur
on a business and on the women who work there, published at scale, with our
name on it. So the whole design rests on one line:

**We record what the venue declares about itself and what a person can see
from the pavement. We never infer, score, rank, or sort shops by respect-
ability.** No "PG" flag. No safe/unsafe. No authentic/tourist. The card says
what is sold; the reader draws their own conclusion, which they are perfectly
able to do once the words are in front of them.

## Three axes

Same emic-axis shape as the amulet reader (`project_amulet_axes`): each axis
answers a different question, none of them collapses into the others.

### Axis 1 — วิธี (wí-thii, "method"): what the hands do

Multi-valued; becomes the children of the `massage` category. Every one of
these is a term a shop puts on its own sign.

| key | Thai | RTGS / tone | literal / root | what it is |
|---|---|---|---|---|
| `thai-traditional` | นวดแผนไทย / นวดแผนโบราณ | nûat phɛ̌ɛn thai / phɛ̌ɛn boo-raan | แผน "plan, system"; โบราณ < Pali *purāṇa* "ancient" | clothed, floor mat, stretches, no oil |
| `chap-sen` | นวดจับเส้น | nûat càp sên | จับ "seize" + เส้น "line, sinew" — the *sen* channels | deep therapeutic, complaint-led, expected to hurt |
| `tok-sen` | ตอกเส้น | tɔ̀ɔk sên | ตอก "to hammer, drive in" | **Lanna.** wooden mallet and wedge tapped along the sen |
| `yam-khang` | ย่ำขาง | yâm khǎang | ย่ำ "to tread" + ขาง (Northern) "heated ploughshare" | **Lanna.** oiled foot off a hot iron, trodden along the limb |
| `ratchasamnak` | นวดราชสำนัก | nûat râat-chá-sǎm-nàk | "royal court" | court lineage — hands only, no elbows or knees, practitioner keeps an arm's length |
| `chaloeisak` | นวดเชลยศักดิ์ | nûat chá-loei-sàk | "commoner's" | the village lineage — the counterpart term to the above, and the one most shops actually practise |
| `foot` | นวดเท้า / กดจุดฝ่าเท้า | nûat tháo / kòt cùt fàa tháo | กดจุด "press the point" | foot and lower leg, chair, clothed |
| `oil` | นวดน้ำมัน / อโรมา | nûat nám-man | น้ำมัน "oil" | table, oil, undressed to some degree |
| `prakhop` | นวดประคบสมุนไพร | nûat prà-khóp sà-mǔn-phrai | ประคบ "to poultice" | steamed herb compress |
| `postpartum` | ทับหม้อเกลือ / อยู่ไฟ | tháp mɔ̂ɔ klʉa / yùu fai | "press the salt pot" / "stay by the fire" | postnatal confinement care |
| `khrop-kaeo` | ครอบแก้ว / กัวซา | khrɔ̂ɔp kɛ̂ɛo / kua saa | ครอบ "to cap" + แก้ว "glass" | cupping, gua sha |
| `spa-body` | สปา ขัดผิว อบไอน้ำ | sà-paa | | scrub, wrap, steam, sauna |
| `ap-ob-nuat` | อาบอบนวด | àap òp nûat | "bathe, steam, massage" | the venue's own word for itself, and its own licence regime — see Axis 3 |

Two of those thirteen are ours and nobody else's category tree has them.
ตอกเส้น and ย่ำขาง are Chiang Mai's, and a CM directory that cannot name them
is a worse directory than one that can, entirely apart from the safety
question. This is the Lanna material, not a compliance exercise.

### Axis 2 — the frame: what the encounter looks like

The sharpest discriminator in the whole design, and the one that needs no
judgement at all: **what you wear and where you lie down.**

- `clothed` / `undress` — do you keep your clothes on
- `mat` / `table` / `chair`
- `shared-room` / `private-room` / `curtained`
- `walkin` / `appointment`
- `price-posted` — is there a board at the door (with the number)
- `menu-posted` — services and durations listed
- `therapist-women` / `therapist-men` / `therapist-either` — availability, as
  the shop states it
- `closes` — the closing hour, which we already collect and which is plain
  fact either way

A shop recorded as *clothed, mat, shared room, price board at the door* is
unambiguous to any reader, and we never had to characterise it.

### Axis 3 — ทะเบียน (thá-biian, "the register"): who says so

The clean, public, photographable line — drawn by Thai law rather than by us.

- `hss-health` — **สถานประกอบการเพื่อสุขภาพ** (sà-thǎan prà-kɔ̀ɔp kaan phʉ̂a
  sùk-khà-phâap), the Health Establishment Act B.E. 2559 regime: นวดเพื่อสุขภาพ
  "massage for health". Certificate with a number, displayed on the wall,
  issued by กรมสนับสนุนบริการสุขภาพ (สบส. / HSS).
- `hss-beauty` — นวดเพื่อเสริมสวย, the beauty variant of the same regime.
- `hss-spa` — กิจการสปา, the spa variant (higher bar: a certified spa manager).
- `ttm-clinic` — สถานพยาบาลการแพทย์แผนไทย, a licensed Thai-traditional-medicine
  clinic; a practitioner with a professional licence, and it can issue receipts.
- `entertainment` — **สถานบริการ** under the Entertainment Places Act. This is
  where อาบอบนวด sits. Different act, different licence, different trade.
- `operator` sub-values, which are the good stories: `blind-coop`
  (นวดโดยคนตาบอด), `ex-prisoner` (we already carry two of those records),
  `hospital-ttm`, `hotel-spa`, `home-shop`.

`hss-*` vs `entertainment` is the whole distinction people are fumbling for,
except stated as a fact about paperwork instead of a hint about morals. It is
on a plaque. Beer can photograph it.

## What the reader sees

One line, front-loaded, at the top of the card — built only from recorded
values, in a fixed grammar, big type (low-vision rule):

```
นวดแผนไทย · ใส่เสื้อผ้า บนเบาะ ห้องรวม · 250 ฿/ชม. · ใบอนุญาต สบส. ติดหน้าร้าน
Thai traditional · clothed, floor mat, shared room · 250 ฿/hr · HSS certificate displayed
```

```
ตอกเส้น + ประคบสมุนไพร · บนเบาะ · 350–500 ฿/ชม. · ร้านบ้าน ไม่เห็นป้ายอนุญาต
Tok sen + herbal compress · floor mat · 350–500 ฿/hr · home shop, no certificate seen
```

And the empty state, which is most of the 294 today, worded as an invitation
rather than a warning (auspicious-wording rule):

```
มดยังไม่ได้แวะร้านนี้ — โทรถามก่อนไปได้เลย
No ant has stopped here yet — a phone call first will tell you.
```

That empty state is the actual safety mechanism. The mistake happens in the
absence of information, so the absence has to be **loud and actionable**,
never a silent gap that reads as ordinary.

Price carries the spread as computed, per the price-forward rule — asking
whether something is แพง is normal Thai conversation and the card should
answer it.

## Filter chips on /lists/massage-chiang-mai.html

The hurried reader does not read cards, they tap once. Chip row:

`ใส่เสื้อผ้า` · `บนเบาะ` · `นวดเท้า` · `ตอกเส้น` · `ประคบ` · `ป้ายราคาหน้าร้าน` ·
`ใบอนุญาต สบส.` · `เปิดถึง 22:00`

Each chip is a positive fact. Nothing is filtered *out* by innuendo.

## How the fields get filled

1. **Name mining** — free, runs today, 36% yield, positive modalities only,
   written at `confidence: crawled` and visibly marked as read-off-the-sign.
   Safe for `ap-ob-nuat` too, since that is the venue naming itself.
2. **Door survey** — the real fill. A ~14-question card for Beer and the BPO
   shop, all of it answerable from the pavement and the doorway in under two
   minutes, no conversation needed: sign terms, price board, licence plaque
   (photograph the number), mat or table visible, closing hour.
3. **Owner submissions** — the `/suggest` Worker already exists; massage shops
   have more to gain from a correct listing than most categories do.

## Sequencing (conservative-scoping rule)

- **A.** Add the thirteen Axis-1 children to `categories.json`; run name
  mining; ship whatever it finds. Empty children render as wireframe shelves,
  which the tree already supports and which is the correct look for "we know
  this exists and have not walked it yet."
- **B.** Add the massage facet set to `facets.json` (Axes 2 and 3), with the
  door-survey `ask_th` / `ask_en` written on every facet, as that file's
  convention requires.
- **C.** The one-line summary and the chip row.
- **D.** A one-page handout — *how to read a massage sign in Chiang Mai* —
  replacing `assets/handouts/massage.pdf`. Arguably the highest-value item
  here: someone in a hurry is on the pavement, not on the site, and thirteen
  Thai words on one printed page solve the problem where it actually occurs.

## What this proposal refuses to build

- Any inferred, scored, or derived rating of what a shop "really is."
- Any pairing that sorts shops into wholesome and otherwise.
- Any listing that excludes a venue for what it sells, or names workers.

The claim of this design is narrower and stronger than a safety label: a
reader who can see the thirteen words, the frame, and the plaque does not
need us to tell them anything.
