# ขัดขี้ไคล — the glove question, and the shelf it opened

A reader asked, in English, for a Korean scrub, a Turkish bath, a Moroccan
hammam — anywhere in Chiang Mai doing a full-body exfoliation **with a mitt**
rather than with bare hands. Mot Dang held 294 massage records and could not
answer, because the catalogue was searched in the wrong language.

## The finding

Nobody here sells this as Korean or Turkish. The trade word is **ขัดขี้ไคล**
(khàt khîi khlai — khàt, to scour; khîi khlai, the grime that rolls off skin),
also sold as **ระเบิดขี้ไคล**, rá-bèet khîi khlai, "blow the khîi khlai off".
In English, Google Maps for Chiang Mai returns a sponsored ad and nothing else.
In that Thai word it returns a trade with price boards.

So the shelf is `massage/khat-khi-khlai`, named in the shops' own word, not
"Korean-style" — the practice here is Thai and calling it Korean would be the
same error that sent the question to a dead end in the first place.

Five records added to `data/curated/additions-chiang-mai.json`, each with dated
sources: Darin Health Massage (Wat Ket), Aqua Beauty & Massage (Brique Hotel),
ร้าน At Spa ขัดผิวเชียงใหม่ (Chiang Mai–Lamphun Rd), บ้านรังสราญ (Soi Chiang
Kham), The Home Massage and Spa (Ragang). A sixth, Bhura Onsen, is the soak and
not the scrub, and says so.

## What the sources actually support, and what they do not

Four of the five name the treatment and **not the instrument**. Only Darin has
a dated third-party review naming ถุงมือขัดผิว, a scrub mitt. That is recorded
as `attrs.scrubTool: "glove"` with `scrubToolVia: "reader-review"` — provenance
in the field itself, because a reader review is not the shop's own declaration
and must never be rendered as if it were.

**No facet was ticked from it.** `scrubglove` (🧤, "ขัดขี้ไคลด้วยถุงมือ") was
added to the massage set with its `ask_th`/`ask_en`, and it stays empty until
somebody stands at a door and asks. Same reasoning as the absent "no
certificate seen" facet: a tick on a named business is testimony, and a review
by a stranger is not testimony we can sign.

Prices carry `_pricesVerified: false`. The Home Massage prices come off the
shop's own website; the rest are quoted from posts and reviews and say so.

## Open leads, for whoever walks this

- **Princess Home (ปริ้นเซส โฮม)** — advertises herbal ขัดขี้ไคล with a Chiang
  Mai branch on 096-642-3642 (TikTok @princesshome88). No pin, no address that
  a second source confirms, so it is not in the catalogue. One phone call fixes
  that.
- **OSM node `cm-osm-node-822570080` "Home Massage"** at 18.7844, 98.9965 sits
  near neither of The Home Massage and Spa's two branches. It may be the Chiang
  Mai Gate branch mispinned, or a different shop with a similar name. Not
  merged — `merges.json` takes human-confirmed pairs only.
- **K-sauna cm, San Kamphaeng** — the one Korean-branded sauna in the province.
  Its Google listing carries the soapland category, which puts it in the
  อาบอบนวด frame under a different Act; it shares a phone with K-Garden &
  Resort. Nothing was recorded from that, since a platform's category is not a
  venue's own declaration. If the door survey reaches it, the question is
  simply what is on the menu.
- **Hammam** — no Chiang Mai venue found. The hammam chambers at the Dheva Spa,
  Dhara Dhevi, are real and predate the resort's staged reopening; worth a call
  to 053-888-888 before the shelf claims anything.

## The reusable lesson

This is the same shape as ตอกเส้น and ย่ำขาง: a treatment offered all over the
city, invisible to a directory that only reads English or only reads OSM tags.
The fix was never a better crawl. It was asking what the shops call it.

## The card (added the same day)

The five shops are now one picture: `assets/og/shelf-cm-massage-khat-khi-khlai.png`,
the og:image for `/cm/massage/khat-khi-khlai/` and downloadable from the page
itself through the 🖼 บันทึกการ์ด pill. It carries the shelf name in Thai and
English, the count, and the five names with their ตำบล/อำเภอ and prices —
Darin 700 บาท / 1.5 ชม., The Home 700–1,200 บาท, At Spa 399 บาท / 1 ชม.
(โปรฯ) — under the caption ราคาตามที่ร้านบอก ยังไม่ได้เดินตรวจ.

The glove is deliberately not on the card. Only Darin has evidence of a mitt
and it is a reader review; a card that implied five shops use one would be the
same overclaim as ticking `scrubglove` on all five.

Generalised to every list page on the site: `make_shelf_cards.py`, 231 cards.
