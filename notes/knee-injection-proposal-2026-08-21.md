# ฉีดน้ำเลี้ยงข้อเข่า — the knee-injection question: the silence, the words, the twelve calls

*2026-08-21. A stranger on Facebook: "Who can provide me with a knee
viscosupplementation injection in Chiang Mai?" Nan brought it to the site and
asked the only question that matters here — **can มดแดง answer this?** It
cannot, not today, and this note is the measurement of exactly how far short it
falls, the rule a knee card would have to obey, and the twelve phone calls that
turn the silence into an answer. Read with `MARCHING-ORDERS.md` WO-29.*

*Privacy fence, same as WO-25's: the asker is not a record. Nothing that reaches
`data/` is a fact about a person — no name, no condition, no thread link. What
gets published is a fact about a FACILITY: what a desk said when it was phoned,
on the day it was phoned. The question is kept as a QUESTION (the `asked` shape,
the same as `pap-smear` and `physio`, both of which arrived by this same door),
never as a case.*

*And the standing medical rule, restated because this order sits closest to the
line of any so far: **the desk states, the register records, nobody advises.**
This page will never say whether a person should have this injection, which
brand, how many, or whether it works. It says who answered the phone and what
they said they do. A directory that starts advising is a directory nobody can
check.*

## 1. The measurement — the corpus

Zero-network, whole-catalogue scan, both provinces, run 2026-08-21 against
`data/canonical/{cm,cr}.json`. **19,980 records, of which 2,038 are medical.**
Every form of the question a person could type or read off a sign:

| What was searched | Records that carry it |
|---|---|
| `viscosupp` · ฉีดน้ำเลี้ยงข้อ · น้ำไขข้อ · ไขข้อเทียม | **0** |
| `hyaluron` · ไฮยาลูรอน · ไฮยาลูโรนิก | **0** |
| osteoarthritis · ข้อเข่าเสื่อม · ข้อเสื่อม · ข้ออักเสบ · arthritis · รูมาตอยด์ | **0** |
| PRP · เกล็ดเลือด · stem cell · สเต็มเซลล์ | **0** |
| `knee` · เข่า | **1** — วัดพระธาตุดอยสุเทพ (the blurb mentions climbing) |
| ฉีด · `injection` | **1** — PrEP by CWC, and that is a different injection |
| orthopaedics, all spellings | **2** |

**Two records. In a province of two million people.** They are:

- **Tanawat Clinic Orthopaedics** (`cm-osm-node-6322159249`) — `sub: doctors`,
  phone **+668 0850 5087**, no hours, no site, no address. The only one of the
  three that can be phoned from the catalogue as it stands.
- **Clinic กระดูกและข้อ** (`cm-osm-way-844924728`) — `sub: clinic`, a pin at
  18.7669 / 98.9876 and nothing else. No phone, no hours, no name in either
  language beyond the word for its own speciality.
- **คลีนิก ชนะการ เมตตาภรณ์ / Chanakan Clinic** (`cm-osm-node-1361128547`) —
  carries `specialty: ortho` from an OSM `healthcare:speciality` tag, not from
  its name. Hours Mo–Fr 17:30–19:30, Sa 09:00–12:00. No phone.

That third one is the important one, because it is invisible to every rule that
reads signs. **A Thai clinic is named after its doctor** (`importers/specialty.py`
says so in its own docstring, off a survey of all 873 clinic names) — so the
speciality is stated on the sign for 116 of 467 records, and 72 of those are
dental. The ortho silence is not a mapping failure. It is the naming custom.

**The widening was tested and gains nothing.** A candidate rule adding
หมอกระดูก · ศัลยกรรมกระดูก · ข้อเข่า · เวชศาสตร์การกีฬา · sports medicine to the
existing `ortho` pattern was run across all 19,980 records: **zero new records.**
The corpus holds five records containing กระดูก at all, and three are food —
ไก่ไร้กระดูก (boneless chicken), ซุปกระดูก (bone soup) — which is precisely why
bare กระดูก is not in the pattern and must not be added.

**One adjacent record, deliberately not folded in.** `บุญบัวคลีนิค นวดจัดกระดูก`
is filed `medical / thai-medicine` — จัดกระดูก, bone-setting massage. It is a
real thing a person with a sore knee may want and it is **not** what was asked
for. It must never be returned as an answer to this question, and the reason
belongs on the page in both languages.

**The already-correct fence, worth recording so nobody "fixes" it.** The `ortho`
pattern reads `\bortho(?!dont)`, and `OSM_SPECIALITY` maps orthodontics → dental.
**M-Brace Orthodontic Clinic is braces, not knees**, and the specialty layer
already knows. Any selector written for a knee card by NAME MATCHING alone will
re-open that hole — see §4, decision 2.

## 2. The measurement — search

The shipped search block could not be run on the walk: `docs/data/index.json`
was mid-rebuild (two builds live, `cache/build.lock` held at 17:27). The probe
is written and standing at **`notes/knee-search-probe.py`**; it lifts the same
JS block `tests/test_search.py` does, so it measures the shipped code and not a
paraphrase. Run it from the repo root once a build has landed —
`python3 notes/knee-search-probe.py` — and **paste the table in here before the
first door.**

What can be said without it, from the corpus census alone: every query in the
left column above returns **either nothing or a namesake**, because a search
cannot return what the data does not hold. The one prediction worth writing down
before the run — `knee` will return **วัดพระธาตุดอยสุเทพ**, and `เข่า` will do
the same — is exactly the shape of the WO-25 gemba, where `CHAMPVA` returned the
Duang Champa hotel. If the run disagrees, the run wins.

## 3. The rule — what a knee card may say

Inherited whole from WO-25's register, because it was written for this:

- **The desk states; the paper carries its date; nothing is awarded.** A claim
  is written only where a named facility said it, and `evidence` carries the
  sentence it was read or heard from, with `fetched`/`called` and the date.
- **Absent is silence, never a "no".** A hospital that was not reached, or that
  did not answer the question, produces nothing — not a "does not offer".
- **No medical advice.** Not which brand, not how many, not whether it works,
  not whether to have it.
- **Prices carry `_pricesVerified: false`** until somebody has stood at the
  counter — and a chain's price tagged to another branch is worse than no price
  (the Kasemrad rule).
- **A phone call is a source like any other.** New source type: `{"type":
  "call", "ref": "<the number dialled>", "asked": "<the question asked>",
  "said": "<what was answered>", "fetched": "<date>"}`. Same shape, same
  discipline — a spoken claim is dated and attributed or it does not exist.

## 4. The two decisions the build needs

**Decision 1 — a register, not a facet.** Follow `transhealth.json`, not the
facet route. The knee answer is a *stated service inside a department*, which is
exactly what `care.json` already models, and the trans-health order proved the
pattern of feeding curated register rows into the index (`TRANSHEALTH_ROWS` in
build.py) so a word with zero corpus rows still lands on real places. A facet
would ask every one of 2,038 medical records a question only twelve of them can
answer. **Proposed: fold it into `care.json` as a new `services` block on the
existing entries, rather than a new file** — the seven hospitals are already
there with verified sites and desk numbers, and a knee is ongoing care.

**Decision 2 — the `asked` selector needs one small thing.** `_match()` in
`asked_layer.py` treats `attr` as a truthiness test (`a.get(f["attr"])`), so
`specialty: ["ortho"]` cannot be selected: `{"attr": "specialty"}` matches every
record with any speciality, dental included. The two honest routes:

- add a **`spec` clause** — one line, `if "spec" in f and f["spec"] not in
  (a.get("specialty") or []): return False` — which is the smallest change and
  keeps the selector's stated promise of staying small; or
- write `{"any": [{"name": "ortho"}, {"name": "กระดูกและข้อ"}]}`, which needs no
  code — but **misses Chanakan** (whose ortho comes from a tag, not its name)
  and re-opens the orthodontic hole the specialty layer already closed.

Take the first. And note `show: "phone"` cannot be used as pap-smear uses it:
of the three ortho records **one has a phone**, so a phone-only card renders a
single row. The card leads with the register rows once the calls are made.

## 5. The doors, numbered, awaiting Nan's go

1. **The twelve calls.** §6 below — the whole substance of this order. Zero
   network, one telephone, an afternoon.
2. **The site reads.** `read_care_sites.py` already verifies-before-it-believes;
   point it at the orthopaedic/department pages of the seven verified hospitals
   plus Bangkok Hospital CM, Theppanya, Lanna and McCormick. Cheap, and it may
   answer half the calls before they are made.
3. **Sriphat, retried.** `sriphat.med.cmu.ac.th` did not resolve on WO-25's day
   and sits in `care.json`'s `unread` list. CMU's private wing is the likeliest
   holder of a named orthopaedic clinic in this city, and it is one fetch.
4. **The OSM speciality sweep.** There are only 17 `healthcare:speciality` tags
   in both provinces and they were normalised at import. A wide re-pull of
   `healthcare=*` for both provinces would say whether more ortho tags have
   landed since 2026-07-27 — the same shape as WO-19's fenced group.
5. **The pin and the phone for Clinic กระดูกและข้อ.** It is at 18.7669 /
   98.9876 — 3.1 km from Suan Dok, 1.5 km from Chanakan, both south-east of the
   old city. One survey run photographs both signs and settles name, hours and
   number for each at once.
6. **TTD**, pinned on WO-17's key like everything else.

Doors 2–4 are network and wait for a numbered go. Door 1 needs nothing but the
sheet.

## 6. The call sheet

Built and standing at **`notes/knee-call-sheet-2026-08-21.md`** — twelve numbered
calls in dialling order, the Thai sentence to read aloud with its RTGS, the six
fields to record, and the four answers that are *not* a yes. It is a working
instrument for Nan, kept in `notes/` where `emit_source()` does not ship it.

The reader-facing half comes after: if the calls land, the page gets the
glossary (`ฉีดน้ำเลี้ยงข้อเข่า` · `น้ำไขข้อ` · `ข้อเข่าเสื่อม` · `แผนกกระดูกและข้อ`),
the register rows, and the asked card. If the calls come back empty, **that is
also publishable** — the census of the silence, the same way `/beauty.html`
prints that 0 of 18,686 records name a house call. A question closed is worth
as much as a question answered, and it is the one thing no other directory in
this city will tell you.

## 7. What this order will not build

No booking, no referral, no "we can arrange it", no lead capture, no partner
inventory in this order — and this topic is exactly where somebody would try.
Whether any of them is ever built is Nan's call. No condition pages. No treatment comparisons. No prices
without a counter visit. And no English-first framing: the Thai reader with a
sore knee and a government-scheme card is the first reader of this page, not the
second.
