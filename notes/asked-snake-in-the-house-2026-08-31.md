# snake-in-the-house — งูเข้าบ้าน โทรใคร ให้เขาจับไปปล่อย ไม่ต้องฆ่า

*A snake got into the house — who do I call, and can they take it away alive?*

- asked_on: 2026-08-31
- via: Nan, 2026-08-31 — "can you also add a section on humane snake removal?
  Big thing around here."
- status: PUBLISHED as a **candid gap** (`gap: true`), on purpose. See Decision.

## The question, in the trade's own word

There is no trade. That is the finding, and it is the whole answer.

- word tried: **จับงู** (catch a snake), **งูเข้าบ้าน** (a snake got into the house).
  Neither returns a business. Both return **199** — the fire-and-rescue number —
  and accounts from people who dialled it.
- The sentence the page exists for: **ไม่ต้องฆ่านะคะ/ครับ ขอให้เอาไปปล่อยได้ไหม**
  — please don't kill it, can it be taken away and released. Everything else on
  the page is scaffolding around that one line.

## Why this is NOT a pest-control question, and why the two must never share a voice

`data/curated/pest.json` holds both strands in one file with a `_readme` that
forbids merging them:

> `pest` is a TRADE you hire: companies, prices, a licence, a contract. `snake`
> is a FREE PUBLIC SERVICE you call. Folding them together would sell a
> householder a pest contract for a problem a state crew answers for nothing —
> which is exactly the mistake a directory makes when it lets one word ("pests")
> cover both.

The toilets rule, applied to a second subject. The one place the two halves are
allowed to touch is the rats: snakes follow rats, rats follow food, so dealing
with the rats is dealing with the snakes — and that is the ONLY pest-control
answer to a snake this site will give. It is one sentence, on both pages, in
both directions.

## Sources (url · fetched 2026-08-31 · what it supports)

- https://www.thairath.co.th/lifestyle/life/2549421 — the national hotline list:
  **199** filed explicitly under สัตว์เข้าบ้าน (animals in the house), and 1367
- https://www.samsenfire.com/blog/จับงู-โทร199/ — a Thai fire-and-rescue
  station's OWN advice: identify before acting, do not chase, keep family and
  pets back, watch where it goes, stay calm and move slowly
- https://www.rama.mahidol.ac.th/poisoncenter/th/contactus — **1367**, 24 hours,
  for the public as well as for doctors, LINE @rpc1367
- https://www.nakornthon.com/article/detail/… — snakebite first aid: no
  tourniquet, no cutting, no sucking, no ice; wash, keep still, go
- https://www.sanook.com/news/9537374/ — the **14 snake species** named
  protected wildlife by ministerial regulation, and what is forbidden
- https://portal.dnp.go.th/Content/LegalAffairs?contentId=22540 — the department's
  own legal page, linked as the checker rather than copied as a table
- https://thailandsnakes.com/need-a-snake-removed-call-these-numbers/ — the
  English-language directory, used as a source for what NOT to do (below)
- data/curated/emergency.json — 199, 1669, 191, 1155 were already on this site,
  with their issuing agencies. Nothing there needed changing.

## The refusal, written down rather than left as a silent gap

**A snake farm is not a removal service, and it is not listed here.**
thailandsnakes.com gives "Mae Sai Valley Snake Farm (053-860719)" as the Chiang
Mai entry on a snake-removal list — on the same page that tells readers *not* to
call snake shows, because the animal is killed or ends up in a display. Both
cannot be true. A name on a removal list is a recommendation, so it is refused,
and the page says so in words. This is consistent with `wildlife.json`'s
venue-states / no-ethics-rank rule: we say what a venue does, we do not rank it —
and we do not put it on a list whose heading makes a claim about it.

## What could NOT be confirmed, and is said out loud on the page

**The words "free" and "released" do not yet have a Chiang Mai first-party
source.** They rest on:
- accounts from people who dialled 199 and were not charged, and
- a Bangkok fire station's own page.

No Chiang Mai station or municipal page could be found stating either in its own
words. **One phone call closes this**: เทศบาลนครเชียงใหม่ 053-259000, ask for
งานป้องกันและบรรเทาสาธารณภัย, two questions — คิดค่าใช้จ่ายไหม, and เอางูไปปล่อยไหม.
Recorded in `pest.json -> snake.open`.

Also NOT published, because it could not be verified: the ม.15 penalty for
releasing protected wildlife without permission (a figure of 6 months / 50,000
baht circulates; the primary text was not read). The page makes the protected-
species point without any penalty number attached.

## Decision

- found 0 places / **gap: true** — and the gap is the point, not a failure. The
  `panel` says it plainly: **คำตอบคือเบอร์โทร ไม่ใช่ที่อยู่ / the answer is a phone
  number, not an address.** There was a real temptation to point `find` at the
  fire stations (the catalogue holds 2, one with a phone) or at the hospitals.
  Both were refused: a fire-station list reframes the answer as "go somewhere"
  when the answer is "dial 199", and a hospital list under a question about a
  snake in the kitchen is the wrong voice and against the auspicious-wording
  rule.
- **the cost of that decision, accepted knowingly:** a `gap` entry gets no share
  card, so this answer cannot be posted as one picture. It still has its own URL
  — /asked/snake-in-the-house.html — which is what a Facebook-group reply needs
  most. The rule stands as written rather than being bent for a case that
  happens to be encouraging.
- shelf: none. There is no trade to shelve.
- facet: none.
- register: `data/curated/pest.json -> snake` — the four numbers with their
  issuing agencies, the six phone sentences, while-you-wait do/don't, bitten
  do/don't, the protected-species fact with its checker, why-they-came, the
  refusal, and the open question.
- what was NOT recorded: no species identification guide. Telling a monocled
  cobra from a rat snake is not something a directory should teach a frightened
  person at 10pm, and the page says so — that is the trained crew's job, and
  they come for nothing.
- **emergency.json was deliberately NOT touched.** Its `_rule` says numbers only,
  nationally issued, no triage and no "what to do if". This answer is triage, so
  it belongs on an asked page and nowhere else. 199 was already there.

## Prices

None. That is the answer.

## The four outputs

- [x] records — n/a, and the page says why in its first sentence
- [x] entry in data/asked.json filled (lead / notes / panel), `draft` deleted
- [x] page at asked/snake-in-the-house.html; **no share card, by rule** —
      test_asked.py checks that a gap entry has neither a card nor an og:image
      pointing at one, and it passes
- [ ] `python3 make_post.py snake-in-the-house` — the reply, when Nan wants it

## Doors left open

- **The Chiang Mai call.** 053-259000, two questions, and "free" and "released"
  stop being reported and start being ours. Highest value on this page.
- Whether Chiang Mai has a named volunteer snake-catcher the way Phuket, Samui
  and Krabi do. Nothing found on 2026-08-31 in Thai or English. If one exists,
  they belong here by name — with their own consent, on the add.html route, the
  shibari rule.
- Hornet and wasp nests (รังต่อ, รังแตน) are the same 199 call and are named in
  `pest.json -> snake.numbers` but get only a clause on the page. They may
  deserve their own question if anyone asks it.
