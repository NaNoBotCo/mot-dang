# CALL SHEET — ฉีดน้ำเลี้ยงข้อเข่า (knee viscosupplementation)

**WO-29 door 1.** Twelve calls, in dialling order. An afternoon, one telephone,
no network. Working instrument — lives in `notes/`, which `emit_source()` does
not ship.

Every number below came out of the catalogue or the care register. Where the
line reads **NO NUMBER**, the catalogue holds no phone for that place: that row
is a door survey or a site read, not a call, and it is listed so the gap is
visible rather than quietly skipped.

---

## THE SENTENCE

Read this one aloud. It is the whole call.

> **สวัสดีค่ะ ขอสอบถามหน่อยค่ะ ที่นี่มีบริการฉีดน้ำเลี้ยงข้อเข่าไหมคะ**
>
> *sawatdi kha, kho sopham noi kha — thini mi borikan chit nam liang kho khao mai kha*
>
> "Hello, may I ask — do you offer knee viscosupplementation injections here?"

**Particles:** ค่ะ / คะ if you are speaking as a woman, **ครับ** in both places
if not. Nothing else in the sentence changes.

**If ฉีดน้ำเลี้ยงข้อเข่า draws a blank, try these three, in this order.** Which
one they recognise is itself worth recording — it tells us which word the page
should lead with:

| Say | RTGS | Literally |
|---|---|---|
| ฉีดน้ำไขข้อ | *chit nam khai kho* | inject synovial fluid |
| ฉีดน้ำไขข้อเทียม | *chit nam khai kho thiam* | inject **artificial** synovial fluid |
| ฉีดไฮยาลูรอนเข้าข้อเข่า | *chit haiyaluron khao kho khao* | inject hyaluronan into the knee joint |

**The four follow-ups**, once they say yes:

1. **แผนกไหนคะ** — *phanaek nai kha* — "which department?"
2. **ต้องนัดล่วงหน้าไหมคะ** — *tong nat luang na mai kha* — "do I need an appointment?"
3. **หมอออกตรวจวันไหนคะ** — *mo ok truat wan nai kha* — "which days does the doctor see patients?"
4. **ราคาประมาณเท่าไหร่คะ** — *rakha praman thaorai kha* — "roughly how much?"

---

## THE SIX FIELDS — record these, nothing else

Six one-word answers per call. Write them straight onto the row.

| # | Field | Write |
|---|---|---|
| 1 | **Offered?** | `yes` · `no` · `refer` · `unclear` · `no answer` |
| 2 | **Department** | what THEY called it, their words |
| 3 | **Appointment** | `nat` (appointment) · `walk-in` · `both` |
| 4 | **Days / hours** | only if stated |
| 5 | **Price** | only if stated, verbatim, and it stays `_pricesVerified: false` |
| 6 | **Their word for it** | the Thai they used — **this field is the gold** |

Plus the two that are automatic: the **number you dialled** and **today's date**.
Both go into the source block. A spoken claim is dated and attributed or it does
not exist.

---

## THE TWELVE

Private hospitals first — this is a scheduled elective procedure and they are
the likeliest to say yes quickly. Government hospitals answer differently and
their answer matters more to the Thai reader.

| # | Place | Dial | Note before you dial |
|---|---|---|---|
| 1 | **Bangkok Hospital Chiang Mai** | **052 089 888** | Has an international desk. Ask in English if easier — but still record field 6 in Thai. |
| 2 | **Chiangmai Ram Hospital** | **052 004 601** | Register-verified line. Its own site states heart + neuro clinics; ortho is unread. |
| 3 | **Rajavej Chiang Mai** | **052 011 999** | Its own site states a physio/rehab department (Mo–Fr 08–18, Sa–Su 08–16) — ask whether the injection sits with them or with a visiting ortho. **Ext. 121** is the TRICARE/FMP desk if the paperwork question comes up. |
| 4 | **Sriphat Medical Center** (CMU private wing) | **NO NUMBER** — try **053 936 150** (Maharaj switchboard) and ask to be put through | Its site did not resolve on 2026-08-21 and it is on `care.json`'s `unread` list. Highest-likelihood holder of a named orthopaedic clinic in this city. |
| 5 | **Maharaj Nakorn CM (Suan Dok)** — after-hours specialist clinic | **053 935 740** or **053 935 751** | คลินิกเฉพาะทางนอกเวลาราชการ. The teaching hospital: if anyone here does it, this is where the specialist sits. |
| 6 | **McCormick Hospital** | **053 921 777** | Site dead in the crawl (`unread`). The phone works and is from the catalogue. |
| 7 | **Theppanya Hospital** | **053 852 990** | Private, north side. Not yet in the care register at all. |
| 8 | **Lanna Hospital** | **NO NUMBER** in catalogue | Private, well known, and the record is a name and a pin. **Getting its number is itself a fix** — file it with a receipt. |
| 9 | **Chiangmai Hospital** | **053 225 222** | Register-verified. Its roster names internal-med, neuro, obgyn, physio — no ortho. Absent is silence, so ask. |
| 10 | **Nakornping Hospital** | **053 999 200** | The province's general hospital. Its clinic pages number each consulting room — expect to be given a room number, and record it. |
| 11 | **Tanawat Clinic Orthopaedics** | **080 850 5087** | **The one specialist clinic in the whole catalogue with a phone.** A mobile — expect the doctor or their nurse, not a switchboard. Ask fields 3 and 4 carefully; a one-doctor clinic runs on days, not hours. |
| 12 | **Clinic กระดูกและข้อ** + **คลีนิก ชนะการ เมตตาภรณ์** | **NO NUMBER** — door survey | Both south-east of the old city and **1.5 km apart** — one survey run: 18.7669 / 98.9876 and 18.7672 / 99.0021. Chanakan's stored hours are Mo–Fr 17:30–19:30, Sa 09:00–12:00. One photograph of each sign settles name, hours and number together. |

---

## THE FOUR ANSWERS THAT ARE NOT A YES

The whole value of this sheet is that it does not turn a maybe into a listing.

1. **"มีค่ะ" to the wrong question.** A receptionist who heard only *ฉีดยา*
   ("an injection") will say yes. Confirm with field 6: if they cannot name the
   fluid, it is `unclear`, not `yes`.
2. **A referral to another branch.** A chain's other branch is not this
   branch — the Kasemrad rule from WO-25. Record `refer` and the branch named,
   and make that branch its own call.
3. **"หมอไม่อยู่" / "หมอมาวันอังคาร".** A visiting specialist's schedule is a
   **schedule**, not a no. Record `yes` + field 4.
4. **"ต้องมาตรวจก่อนค่ะ"** — must be examined first. Correct, normal, and still
   not a no. Record `yes` + `nat`. It is also the moment to **stop**: do not
   describe a condition, do not accept advice, do not write any of it down. The
   register records services, never patients and never medicine.

**No answer is data too.** `no answer` × 3 attempts, with dates, is a publishable
fact about a hospital that cannot be reached — and this catalogue holds 154
hospitals of which nearly all are contactless.

---

## WHEN THE CALLS ARE DONE

Rows go into `data/curated/care.json` as a `services` block on the entry, each
claim carrying its own `{"type": "call", "ref": <number>, "asked": <question>,
"said": <answer>, "fetched": <date>}`. New entries for Theppanya, Lanna, Tanawat
and the two unnamed clinics. Field 6 across all twelve calls goes into
`hand.thesaurus.json` as one ongoing-care group — **a thesaurus term is never
segmented**, which is what took โรคหัวใจ from 641 rows of noise to 0-with-a-door.

Then the asked card, `knee-injection`, `via: facebook`, `asked_on: 2026-08-21`.
