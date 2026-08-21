# WO-26 — สุขภาพคนข้ามเพศ · trans health & gender-affirming care (2026-08-21)

Nan's ask: "Enrich gender affirming care and trans resources (particularly
medical, but other items are welcome) on MotDang."

(WO-25 was claimed the same day by the ongoing-care gemba session — the one
that added the menopause/วัยทอง/hormone cases to test_search.py and routes
"hormone" to the womens-health door. This order took WO-26 and kept "hormone"
out of its own panel triggers so the two do not fight over the word; the Thai
ฮอร์โมน still *lands on* the trans rows through the index, doored or not.)

## The measurement that shaped everything

Across all 19,975 records: **zero** name a trans or gender-affirming service.
No ข้ามเพศ, no แปลงเพศ, no hormone, no LGBT, no HIV, no PrEP in any name, in
either language. Thai clinics are named for their doctors (specialty.py's old
survey), and the community organizations sit in OSM as bare points — CAREMAT
was in the catalogue filed under community/centre with nothing saying what it
is. The one direct signal the crawl DID hold — lgbtq=welcome / lgbtq:trans=
welcome / lgbtq=primary tags on three venues — was being dropped at import.

So the enrichment is a curated register, not a name rule. There is no rule to
write; `audit_transhealth.py` prints the zero every run so the hole stays
visible (the beauty-audit lesson applied in reverse — here the names were read
and genuinely say nothing).

## Built (all zero-network except the sourced reads below)

- **`data/curated/transhealth.json`** — the register. 10 rows in four grades
  (stated / community-listed / route / reference), each quoting only what the
  place states itself, every row sourced and dated 2026-08-21. Plus the NHSO
  benefit block, the community org, 3 welcome-tagged venues, and unverified[]
  leads that render nowhere.
- **5 new place records** — `additions-chiang-mai.json` gains Mplus Foundation
  Chiang Mai (the province's biggest trans/LGBTQ+ health org — absent from
  every source we crawl), Hugsa (Klang Wiang), Piman Clinic (RIHES CMU), PrEP
  by CWC; new **`additions-chiang-rai.json`** carries Mplus Chiang Rai (and
  import_all.py now reads that file, so CR curated additions have a home).
  Pins via geocode_local (no external geocoder, per its own rule), precision
  `approx` with pinVia/pinUncertaintyM in attrs, the import_opendata pattern.
- **`importers/import_all.py: apply_lgbtq()`** — lgbtq / lgbtq:trans tags now
  survive import into attrs (Ram Bar, Soho, 1678 Cafe today; self-updating on
  future crawls).
- **`transhealth_layer.py` → `/trans-health.html`** — the graded lists, the
  สปสช. hormone-benefit box (โทร 1330), the credential registers (checkmd ·
  ราชวิทยาลัยจิตแพทย์ · ThPRS · WPATH SOC-8 · NHSO · clinic licence — every URL
  verified reachable 2026-08-21), and the sign glossary (script · RTGS ·
  gloss), womens-health's shape reused deliberately. The measured zero is
  computed live at build so the sentence heals itself if a record ever states
  this care.
- **build.py** — TRANSHEALTH_ROWS feeds the index the same one-file way the
  OB-GYN grade does (only stated/community-listed rows carry topic words —
  route hospitals must not answer "transgender" as if they had said yes);
  `trans_health_band()` on the medical shelf; layer hooked after
  womens-health; transhealth_layer.py added to the source archive.
- **Search door** — `trans-health` panel in search_panels.json (variants
  ข้ามเพศ · transgender · กะเทย · lgbtq · lgbt; query-substring ข้ามเพศ so
  segmentation of compounds cannot dodge it). Guard case: "transport" must
  never door here. 5 new test_search cases.
- **`importers/audit_transhealth.py`** — the four reports; exits 1 if a
  register id stops resolving.

## Decisions worth remembering

- **Grades track evidence, never likelihood** — the womens-health discipline.
  Mplus/CAREMAT/Sriphat/CWC say it themselves ("stated"); Hugsa and Piman are
  in the community's own directory (SISTERHOOD เพื่อนสาว, thaisisterhood.com)
  but their own statements are general ("community-listed" — both provenances
  on the row); Maharaj and Suan Prung are "route — not confirmed, ring first".
- **The NHSO fact is the systemic answer**: บริการฮอร์โมนยืนยันเพศสภาพ entered
  the benefit package (บอร์ดอนุมัติ ก.ค. 2568, ~140M฿), tablet + injection +
  multidisciplinary counselling + interval bloodwork, rolling out via
  medical-school hospitals in big provinces, existing clinics, telemedicine.
  Sourced to the two nhso.go.th announcements. The page says "โทร 1330 ถามสิทธิ
  ของตัวเอง" rather than promising anyone anything.
- **No pharmacy line.** "Hormones are pharmacy-dispensed in Thailand" drifts
  toward regimen advice and is nobody's stated, checkable, per-venue fact.
  The NHSO benefit + clinic rows carry the how-to-get-care answer.
- **No legal-status line.** คำนำหน้านาม / gender-recognition law status was
  left off the page — it could not be verified current today, and a wrong
  legal claim is worse than a missing one. Lead below.
- **กะเทย is in the glossary and the panel variants** — the community's own
  word, treated as a word to recognize; the glossary says how it lands
  differently from a stranger.

## Door 3 RUN, same day — the surgery register + the rules + the pharmacy line

Nan: "start with 3, put a pin in 1 and 2."

- **The scan answered: exactly ONE place in either province states operative
  gender-affirming care** — คลินิกหมอวิมล / Dr Wimon Clinic, Chang Khlan, whose
  own site carries a ศัลยกรรมแปลงเพศ section plus the facial/jaw/chin/tracheal-shave
  categories that the regulation puts inside the same definition. Added as
  `cm-curated-drwimon-clinic`. Everyone else doing this work is Bangkok or
  Phuket and stays out of a two-province directory. Surgery rows band on their
  own (`surgery: true`), because the rules for an operation are different rules.
- **The credential closed the loop the page had opened.** The ThPRS register —
  the register this page's own table tells readers to check — carries the
  clinic's surgeon: **licence no. 14725**, listed with the plastic-surgery unit
  of the Department of Surgery at รพ.มหาราชนครเชียงใหม่, and it is where the
  clinic's street address came from (its own contact page shows a map and no
  readable address). New `credential` field renders as a ✓ linking to the
  register entry. **A credential is a register row, never a rating** — that
  rule is written into transhealth.json's readme and into row_html.
- **THE PRIMARY SOURCE MATTERED.** Secondary reporting contradicted itself on
  the surgery age — one outlet headlined "18 and over". Pulled the actual
  Royal Gazette PDF (`ratchakitcha.soc.go.th/documents/59327.pdf`, fetched
  clean) and read the clauses: **hormones 18+ self-consent (ข้อ ๗), under 18 by
  guardian consent; surgery 20+ self-consent (ข้อ ๙), 18-to-under-20 by
  guardian consent**; physician assesses mental health before hormones and may
  refer to a psychiatrist (ข้อ ๘); the surgeon must be a specialist in plastic
  surgery, OB-GYN or ENT **and** trained in gender-affirming surgery within
  that branch (ข้อ ๑๐). Citation: ข้อบังคับแพทยสภา ... พ.ศ. 2567, ราชกิจจานุเบกษา
  เล่ม ๑๔๒ ตอนพิเศษ ๖๖ ง หน้า ๓๒, 13 Feb 2568, in force the next day.
  **Gotcha for anyone re-reading that PDF:** its Thai font subset has no
  ToUnicode map, so `pdftotext` returns cipher for the Thai and clean text for
  the Latin. The clause numbers decode `_`=๑ … `g`=๙, `^`=๐ — which is how
  `_f`=18 and `` `^ ``=20 were read. The ten procedure names are in the
  document in English and are printed on the page verbatim, because that list
  is what tells a reader facial, voice and tracheal-shave surgery are all
  inside the same regulated category.
- **Thai SOC-8 exists** — WPATH's own Thai translation, live, now in the rules
  sources. A Thai-language standards document is worth more here than an
  English one.
- **The pharmacy line is IN, and I had it wrong.** I had left it out as
  drifting toward regimen advice. Nan's correction, field truth: nearly every
  pharmacy sells some estrogen/progesterone/testosterone from behind the
  counter, **the variable is stock size, not culture**, and the scarce thing is
  the FORMULATION — estradiol cream is the hard one. That is a fact about shops
  and stock, which is what a directory is for, and it is the question a reader
  actually arrives with. Rendered with a `field report` grade, the live
  pharmacy count baked from the data (not typed), links to both pharmacy
  shelves, and one bold line: this site holds no view on what anyone should
  take, names no dose, recommends no brand. No substance is named beyond what
  the field report itself distinguishes. Cross-check
  [[feedback_meds_no_advice]] before touching this block: the rule is
  substance-agnostic infrastructure, and a stock fact about shops is exactly
  the "structural fact" that rule permits.

## Doors that need a go (or a person)

1. **PINNED 2026-08-21 (her call) — ring-and-confirm** Maharaj Nakorn
   (แผนกต่อมไร้ท่อ: does it take gender-affirming hormone patients under the new
   benefit?) and Suan Prung (จิตแพทย์ประเมิน?). Two phone calls turn "route"
   into "stated". Worst case: two rows stay marked unconfirmed, which is what
   they already say. **Maharaj gained a reason to ring since door 3 ran:** the
   ThPRS register lists the Dr Wimon surgeon with Maharaj's own plastic-surgery
   unit, so the hospital plainly has a surgeon who does this work — which is
   still NOT a statement that the hospital runs the service, and the row stays
   at `route` until somebody rings. That is the question to ask.
2. **สปสช. designated-provider list** for CM/CR under the hormone benefit —
   not findable today; when published, rows graduate with a source.
3. **PINNED 2026-08-21 (her call) — dupe adjudications** (also in unverified[]): CAREMAT pair
   cm-osm-node-13717806001/13717807501 (213 m apart, identical facts), Ram Bar
   pair 3318180864/4240667690, Suan Prung MOPH/OSM pair. Each needs a person
   to pick the true pin before a merges.json receipt.
4. ~~**Surgery register**~~ — **RUN 2026-08-21**, see above. Remaining thread:
   the ThPRS "find a surgeon" register is browsable by name and could be walked
   for any OTHER CM/CR-based plastic surgeon, but a register entry is not a
   statement that a clinic offers this surgery — only the clinic's own words
   are. So that walk yields leads, not rows, and needs a go before it runs.
5. **search-core thesaurus groups** — queued, NOT hand-run today (parity gate,
   and another session was in the search block): proposed earned groups
   `[ข้ามเพศ, transgender]`, `[กะเทย, kathoey]`, `[ยืนยันเพศสภาพ, gender
   affirming]`. The panel + index keywords cover the reach meanwhile.
6. **rcpt.org HTTPS broken** (endocrinology college) — recheck someday;
   checkmd covers the lookup need.
6b. **llms.txt lists none of the topic pages** — not womens-health, not beauty,
   not namphuron, and now not trans-health either. So this is a pre-existing
   site-wide gap rather than something this order left behind, and the fix is
   one llms.txt section covering all of them at once. Worth doing when nobody
   else is holding build.py; deliberately not edited mid-build here.
7. **womens-health ↔ trans-health cross-door** — the ongoing-care session owns
   the womens-health panel today; adding a trans-health door there is a
   one-line panel edit when the dust settles.

## Sources read today (all dated in the register)

mplusthailand.com (CM office, contact/all-offices) · caremat.org ·
sriphat.med.cmu.ac.th/th/knowledge-381 · prepclinicchiangmai.com ·
hugsamedical.com · pimanclinic.rihes.cmu.ac.th · thaisisterhood.com/resources/
clinics (the community directory that mapped the north) · nhso.go.th ×2 ·
ihri.org/tangerine · youngpridefoundation.org — plus reachability checks on
checkmd.tmc.or.th, rcpsycht.org, thprs.org, wpath.org, nhso.go.th (all 200)
and rcpt.org (https 000 / http 200, excluded).
