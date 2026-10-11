#!/usr/bin/env python3
"""The RTGS reader, held to the standard and to the catalogue's own names.

Two kinds of check, because they answer different questions.

FIXED CASES are the ones where RTGS's published rules give exactly one answer
and the answer is checkable against a road sign: Chiang Mai, Doi Suthep, Huai
Kaeo. Every one of them is here because it broke at some point — เชียงใหม่ read
"chiangamai" while a leading vowel was mistaken for a syllable head, ห้วยแก้ว
read "wayakwae" while ห้ was mistaken for a silent ho nam, ศูนย์ read "su" while
the killer mark was eating the น in front of it. These must not regress.

THE CORPUS FLOOR is different. It compares the reading against the human
English names already in data/canonical/ and asserts only that agreement stays
above where it stands today. It is a floor, not a target, and it can never be
100%: the site's own /what.html cites the 2024 study that romanised 3,305 Thai
names and got 7,243 spellings back. When this reader writes "Huai Kaeo" and a
shop's sign says "Huay Kaew", both are right and the test counts a miss. What
the floor catches is a change that makes the reader broadly worse — the class
of regression a fixed list of 40 names would sail straight past.

    python3 tests/test_translit.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import translit as T  # noqa: E402

FAIL = []


def check(got, want, why):
    if got != want:
        FAIL.append(f"{why}\n     got  {got!r}\n     want {want!r}")


# ---------------------------------------------------------------------------
# 1. The rules, on names whose romanisation is not in dispute
# ---------------------------------------------------------------------------
FIXED = [
    # the two provinces and the ground everybody navigates by
    ("เชียงใหม่", "Chiang Mai"),
    ("เชียงราย", "Chiang Rai"),
    ("ดอยสุเทพ", "Doi Suthep"),
    ("ห้วยแก้ว", "Huai Kaeo"),
    ("ท่าแพ", "Tha Phae"),
    ("ช้างเผือก", "Chang Phueak"),
    ("สันทราย", "San Sai"),
    ("หางดง", "Hang Dong"),
    ("แม่ริม", "Mae Rim"),
    ("แม่ฮ่องสอน", "Mae Hong Son"),
    ("ลำพูน", "Lamphun"),
    # syllable shapes that each broke once
    ("คน", "Khon"),            # unwritten o in a closed syllable
    ("ลม", "Lom"),
    ("สบาย", "Sabai"),         # unwritten a in an open one
    ("นคร", "Nakhon"),         # three consonants: open then closed
    ("ขนม", "Khanom"),
    ("ถนน", "Thanon"),
    ("มงคล", "Mongkhon"),      # ง closes wherever it can
    ("สงกรานต์", "Songkran"),
    ("สวน", "Suan"),           # ว as the vowel ua
    ("หลวง", "Luang"),
    ("ด่วน", "Duan"),
    ("กวาง", "Kwang"),         # ...but ว is still a consonant here
    ("ศูนย์", "Sun"),          # the killer takes ย only, never the น too
    ("จันทร์", "Chan"),        # ...but it takes a whole ...ทร cluster
    ("ศาสตร์", "Sat"),
    ("จักร", "Chak"),          # word-final ร after a stop is silent
    ("บัตร", "Bat"),
    ("ทราย", "Sai"),           # ทร is /s/
    ("ศรีภูมิ", "Si Phum"),
    ("สารภี", "Saraphi"),
    ("พระสิงห์", "Phra Sing"),
    ("อาหาร", "Ahan"),
    ("ข้าวซอย", "Khao Soi"),
    ("น้ำพริก", "Nam Phrik"),
    ("กาแฟ", "Kafae"),
    ("พร้าว", "Phrao"),
    ("เวียงป่าเป้า", "Wiang Pa Pao"),
    ("แม่สาย", "Mae Sai"),
    ("เชียงของ", "Chiang Khong"),
    ("พะเยา", "Phayao"),
    ("ฝาง", "Fang"),
    ("ดอยหล่อ", "Doi Lo"),
    # 2026-09-07 (WO-72): the three classes a 30-name random sample of the
    # live index turned up, each measured over all 8,700 printed readings
    ("ประตูท่าแพ", "Pratu Tha Phae"),   # a compound the dictionary held whole read "Pratuthaphae" (778 run-ons)
    ("ป่าช้า", "Pa Cha"),
    ("ท่ารถ", "Tha Rot"),
    ("บุ่น", "Bun"),                    # greedy cutting stranded the น and read "Bu Na" (53 orphans)
    ("หมูบุ่น", "Mu Bun"),
    ("ต้นหมื้อ", "Ton Mue"),            # a cut inside the ho-nam pair, "Tanaha Mue"
    ("แก้ทรง", "Kaesong"),              # ทร taken as a final: "Kaetrong"
    ("น้ำแพร่", "Nam Phrae"),           # a cluster behind แ at word end: "Namphaen"
    ("อนาคามี", "Anakhami"),            # a name shredded into dictionary syllables: "A Na Kha Mi"
    ("หฤทัย", "Haruethai"),             # ห before ฤ is said
    ("สุรพงษ์", "Suraphong"),
    ("อุโบสถ", "Ubosot"),
    ("สันติสุข", "Santisuk"),           # ...and an element-opening word that is ONE word stays one
    ("หอนาฬิกา", "Ho Nalika"),
    ("มอร์", "Mo"),                     # a killed ร takes the letter before it only in a cluster (was "Ma")
    ("ปรินท์", "Prin"),                 # a one-consonant residue is the tail of the word before it (was "Pri Na")
]

for th, want in FIXED:
    check(T.title(th), want, f"RTGS reading of {th}")

# ---------------------------------------------------------------------------
# 2. The generic head word: translated, and put where English puts it
# ---------------------------------------------------------------------------
HEADS = [
    # วัด, ดอย, บ้าน and ร้าน are borrowed into English WITH the name: they lead
    ("วัดพระธาตุดอยสุเทพ", "Wat Phra That Doi Suthep"),
    # a generic noun INSIDE a name is read, never translated (was "Wat Cave Phra")
    ("วัดถ้ำพระ", "Wat Tham Phra"),
    ("อัมพรคลินิก", "Amphon Clinic"),
    ("วัดเจดีย์หลวง", "Wat Chedi Luang"),
    # a translated generic noun trails, because that is how English says it
    ("น้ำตกห้วยแก้ว", "Huai Kaeo Waterfall"),
    ("โรงพยาบาลแม่ริม", "Mae Rim Hospital"),
    ("โรงพยาบาลนครพิงค์", "Nakhon Ping Hospital"),
    ("โรงเรียนบ้านสันทราย", "Ban San Sai School"),
    ("ตลาดวโรรส", "Warorot Market"),
    ("ชุมชนบ้านหนองหอย", "Ban Nong Hoi Community"),
    ("ร้านขายยาบ้านสันทราย", "Ban San Sai Pharmacy"),
]
for th, want in HEADS:
    check(T.reading(th), want, f"head word of {th}")

# ---------------------------------------------------------------------------
# 3. English written in Thai script comes back as the English
# ---------------------------------------------------------------------------
LOANS = [
    ("คอนโดมิเนียม", "Condominium"),
    ("ฟาร์มาซี", "Pharmacy"),
    ("อควา บิ้วตี้ แอนด์ มาสสาจ", "Aqua Beauty & Massage"),
    ("เอ็กซ์ต้า", "eXta"),
    ("บาร์เบอร์ช็อป", "Barber Shop"),
    # a short entry must not cut a longer word: คัท inside คัทลียา
    ("บ้านคัทลียา", "Ban Cattleya"),
]
for th, want in LOANS:
    check(T.reading(th), want, f"loanword {th}")

# ---------------------------------------------------------------------------
# 4. Things the reader must NEVER do
# ---------------------------------------------------------------------------
check(T.romanize("7-Eleven"), "7-Eleven", "Latin text passes through untouched")
check(T.romanize(""), "", "empty in, empty out")
check(T.romanize("ร้าน 7-Eleven"), "ran 7-Eleven", "mixed script keeps its Latin half")
check(T.title("ร้าน 7-Eleven"), "Ran 7-Eleven", "title() capitalises only what it built")

# ---------------------------------------------------------------------------
# 5. The corpus floor
# ---------------------------------------------------------------------------
# Where it stands as this test is written. Raise it when the reader improves;
# never lower it to make a change pass.
#
# History: 0.44 / 0.70 set 2026-08-31. Measured 2026-09-07 BEFORE WO-72 at
# 42.8% / 68.1% — both red without the reader having been touched, because
# the pair set is drawn live from data/canonical and new records had arrived
# whose nameEn is a different name altogether (บ้านขวัญเคียงดาว is listed as
# "Bamboo House & Café"). The floor measures name-vs-brand pairs as well as
# transcription, so it drifts with the corpus. After WO-72: 46.9% / 70.4%.
FLOOR_EXACT = 0.46
FLOOR_CLOSE = 0.70


def _lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _has_thai(s):
    return bool(s) and bool(re.search(r"[฀-๿]", s))


recs = []
for prov in ("cm", "cr"):
    path = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            recs += json.load(fh)

# Names that are Thai through and through — a temple, a village, a waterfall.
# The shop called "อควา บิ้วตี้" is English in Thai letters and belongs to the
# loanword case above, not to a measurement of the romaniser.
NATIVE = ("วัด", "บ้าน", "ดอย", "ห้วย", "แม่", "ป่า", "หนอง", "สัน", "ท่า",
          "น้ำตก", "ถ้ำ", "เวียง", "พระ")
pairs = []
for r in recs:
    nm = (r.get("name") or "").strip()
    th = (r.get("nameTh") or "").strip() or (nm if _has_thai(nm) else "")
    en = (r.get("nameEn") or "").strip() or ("" if _has_thai(nm) else nm)
    if th and en and th != en and th.startswith(NATIVE):
        pairs.append((th, en))

if pairs:
    def norm(s):
        return re.sub(r"[^a-z]", "", s.lower())

    exact = close = 0
    for th, en in pairs:
        a, b = norm(T.reading(th)), norm(en)
        if not b:
            continue
        if a == b:
            exact += 1
        elif _lev(a, b) <= max(2, int(len(b) * 0.25)):
            close += 1
    n = len(pairs)
    print(f"corpus floor: {n} Thai-native pairs — "
          f"exact {exact / n:.1%}, within 25% edits {(exact + close) / n:.1%}")
    if exact / n < FLOOR_EXACT:
        FAIL.append(f"exact agreement fell to {exact / n:.1%} (floor {FLOOR_EXACT:.0%})")
    if (exact + close) / n < FLOOR_CLOSE:
        FAIL.append(f"close agreement fell to {(exact + close) / n:.1%} "
                    f"(floor {FLOOR_CLOSE:.0%})")
else:
    print("corpus floor: skipped — data/canonical not built")

# ---------------------------------------------------------------------------
if FAIL:
    print(f"\nFAIL — {len(FAIL)} problem(s):\n")
    for f in FAIL:
        print("  *", f)
    sys.exit(1)
print(f"OK — {len(FIXED) + len(HEADS) + len(LOANS) + 3} readings correct")
