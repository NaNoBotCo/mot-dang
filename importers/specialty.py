#!/usr/bin/env python3
"""What a clinic says it does, read off its own sign.

WHY THIS IS AN ATTRIBUTE AND NOT A SHELF TREE. A survey of all 873 clinic,
doctor, dentist and hospital names in both provinces first, before any bucket
was invented — the same order the food cuisines were done in:

  คลินิกทันตกรรม   19        คลินิกเวชกรรม     10
  คลินิกหมอกร  ·  คลินิกหมอธเนศ  ·  คลินิกหมอเจษฎา  ·  คลินิกนายแพทย์…

**Thai clinics are named after their doctor, not their speciality.** Only
ทันตกรรม and เวชกรรม are reliably on the sign; everything else is somebody's
name. A speciality is stated on 116 of 467 records (25%), and dental is 72 of
those 116. Twelve child shelves, ten of them holding three records each, would
be a wall of wireframes claiming the city has two eye clinics. So this fills a
FIELD — the medical equivalent of `cuisine`, which build.py already renders and
links to a search — and the other 351 stay silent until somebody reads a door.

WHAT COUNTS AS EVIDENCE, in order:
  osm-tag  `healthcare:speciality`, where a mapper stated it. There are only 17
           in both provinces and the values are rough ("yes", "แพทย์์;ความงาม"
           with the typo, semicolon lists), so they are normalised against the
           same table and anything unrecognised is dropped rather than shown raw.
  name     the place's own sign says it. This is the massage-modality rule
           (importers/audit_massage.py): a venue's own name is evidence about
           that venue and nothing else is.

WHAT IS DELIBERATELY NOT DONE. A name saying ทันตกรรม does NOT rewrite
`facilityType` to dentist, even though it usually would be right. The crawled
tag is a mapper's statement about what the place IS; this is a reading of its
name. Where they disagree the reader should see both, not have one quietly
overwritten — and a shelf that moves under a place because a regex read its sign
is how a directory stops being checkable.
"""
import re

# Each pattern is a phrase that actually appears on signs here — taken from the
# survey, not from a list of medical specialities. Order matters only for
# readability; every pattern is tested and a place may state several.
SPECIALTIES = [
    ("dental", "ทันตกรรม", "Dental",
     r"ทันตกรรม|ทันตแพทย์|ทันตคลินิก|ทันต\s*คลินิก|\bdental\b|\bdentist"),
    ("general", "เวชกรรมทั่วไป", "General practice",
     r"เวชกรรม(?!ความงาม)|\bpolyclinic\b|\bgeneral practice\b"),
    ("skin", "ผิวหนัง-ความงาม", "Skin & aesthetic",
     r"ผิวหนัง|ความงาม|\bskin\b|\bderma|\baesthetic|\bbeauty\b"),
    ("eye", "จักษุ-ตา", "Eyes",
     r"จักษุ|คลินิกตา|\bophthalm|\beye clinic\b"),
    ("obgyn", "สูตินรีเวช", "Women's health",
     r"สูตินรีเวช|นรีเวช|\bobgyn\b|\bgynae|\bobstetric"),
    ("paediatric", "กุมารเวช-เด็ก", "Children",
     r"กุมารเวช|คลินิกเด็ก|\bpaediatric|\bpediatric"),
    ("ortho", "กระดูกและข้อ", "Bones & joints",
     r"กระดูกและข้อ|ออร์โธ|\bortho(?!dont)"),
    ("ent", "หู คอ จมูก", "Ear, nose & throat",
     r"หู\s*คอ\s*จมูก|โสต\s*ศอ|\bENT\b"),
    ("psych", "จิตเวช", "Mental health",
     r"จิตเวช|สุขภาพจิต|\bpsychiatr"),
    ("physio", "กายภาพบำบัด", "Physiotherapy",
     r"กายภาพบำบัด|\bphysiotherap|\brehabilitation\b"),
    ("thai-med", "แพทย์แผนไทย", "Thai traditional medicine",
     r"แพทย์แผนไทย|แผนไทยประยุกต์"),
    ("chinese-med", "แพทย์แผนจีน-ฝังเข็ม", "Chinese medicine & acupuncture",
     r"แพทย์แผนจีน|ฝังเข็ม|\bacupunctur|\bchinese medicine"),
    ("kidney", "ไตเทียม-ฟอกไต", "Dialysis",
     r"ไตเทียม|ฟอกไต|\bdialysis\b|\bnephro"),
    ("heart", "โรคหัวใจ", "Heart",
     r"โรคหัวใจ|\bcardio"),
    ("lab", "แล็บ-ตรวจวิเคราะห์", "Lab & testing",
     r"แล็ป|แล็บ|ห้องปฏิบัติการ|\blaborator"),
]

LABELS = {k: (th, en) for k, th, en, _ in SPECIALTIES}

# healthcare:speciality values seen in this corpus, mapped onto the same keys.
# Anything not here is dropped: publishing a raw "yes" or a mapper's typo as a
# speciality would be worse than saying nothing.
OSM_SPECIALITY = {
    "dentistry": "dental", "stomatology": "dental", "orthodontics": "dental",
    "dentist": "dental",
    "general": "general", "community": "general",
    "dermatology": "skin", "aesthetic": "skin", "plastic_surgery": "skin",
    "cosmetic": "skin", "ความงาม": "skin",
    "ophthalmology": "eye", "optometry": "eye",
    "gynaecology": "obgyn", "obstetrics": "obgyn",
    "paediatrics": "paediatric", "pediatrics": "paediatric",
    "orthopaedics": "ortho", "orthopedics": "ortho",
    "otolaryngology": "ent",
    "psychiatry": "psych", "psychotherapy": "psych",
    "physiotherapy": "physio", "rehabilitation": "physio",
    "traditional_chinese_medicine": "chinese-med", "acupuncture": "chinese-med",
    "nephrology": "kidney", "dialysis": "kidney",
    "cardiology": "heart",
    "radiology": "lab", "laboratory": "lab", "clinical_pathology": "lab",
}


def from_name(*names):
    """Specialities the place states on its own sign."""
    blob = " ".join(n for n in names if n)
    if not blob:
        return []
    return [key for key, _, _, pat in SPECIALTIES if re.search(pat, blob, re.I)]


def from_tag(value):
    """Specialities from healthcare:speciality, normalised; unknowns dropped."""
    if not value:
        return []
    out = []
    for part in re.split(r"[;,]", value):
        k = OSM_SPECIALITY.get(part.strip().lower())
        if k and k not in out:
            out.append(k)
    return out


def of(record, tags=None):
    """-> (specialities, how) where how is 'osm-tag' or 'name'. Tag wins: a
    mapper stating it outright beats us reading a sign."""
    tagged = from_tag((tags or {}).get("healthcare:speciality")
                      or (tags or {}).get("healthcare:specialty"))
    if tagged:
        return tagged, "osm-tag"
    named = from_name(record.get("name"), record.get("nameEn"),
                      record.get("nameTh"))
    return (named, "name") if named else ([], None)


# ---------------------------------------------------------------------------
# The graded OB-GYN signal, filtered
# ---------------------------------------------------------------------------

# Single-specialty facilities that run no OB-GYN department. The upstream
# harvester (cm-womens-health) already drops eye, dental, geriatric, psychiatric
# and orthopaedic; these are the ones that reached the Mot Dang corpus anyway,
# found by reading all 44 records the grade landed on rather than by imagining
# which specialities exist. Matched against the place's own name, which is the
# only evidence there is.
_NOT_OBGYN = r"""ประสาท|จักษุ|คลินิกตา|ทันตกรรม|ทันตแพทย์|จิตเวช|สุขภาพจิต|กระดูกและข้อ|
ผู้สูงอายุ|สัตว|กุมารเวช|คลินิกเด็ก|พัฒนาการเด็ก|ธาลัสซีเมีย|
\bneurolog|\bophthalm|\bdental\b|\bpsychiatr|\borthopaed|\borthoped|\bgeriatric|
\bveterinar|\bpaediatric|\bpediatric|\bchild health|\bthalass"""
_NOT_OBGYN_RE = re.compile("|".join(
    p for p in re.sub(r"\s+", "", _NOT_OBGYN).split("|") if p), re.I)


# A subdistrict health-promoting hospital — รพ.สต., the local primary-care
# station. Deliberately requires ตำบล on the Thai side: โรงพยาบาลส่งเสริมสุขภาพ
# เชียงใหม่ is the regional health-promotion HOSPITAL and not one of these.
_RPSAT_RE = re.compile(
    r"โรงพยาบาลส่งเสริมสุขภาพตำบล|รพ\.?ส\.?ต|สถานีอนามัย"
    r"|\b(?:sub)?district health (?:promoting|cent)"
    r"|\btambon health promoting", re.I)


def obgyn_grade(attrs, *names):
    """The OB-GYN grade this place may honestly be listed under, or None.

    `attrs["obgyn"]` arrives from the cm-womens-health harvester, where the
    grade is deliberately generous: `hospital-likely` means "a general hospital,
    and in Thailand those almost always run a สูตินรีเวช department". Generous is
    right for a facility crawl and wrong for a page a reader searches, because
    the grade landed on three ร้านยา, a neurological hospital, a child-health
    institute and a thalassaemia screening centre — none of which run one.

    So `tagged` (a mapper's statement, or the clinic's own sign) passes through,
    and `hospital-likely` has to earn it: the record must be typed as a hospital,
    and must not name a speciality that rules an OB-GYN department out. Anything
    that fails is not downgraded to a weaker claim — it makes no claim at all.

    Returns "tagged", "hospital-likely", "health-station" or None. The third is
    a รพ.สต., which is a different kind of place from a general hospital and is
    said so rather than folded in.
    """
    a = attrs or {}
    grade = a.get("obgyn")
    if grade == "tagged" or "obgyn" in (a.get("specialty") or []):
        return "tagged"
    if grade != "hospital-likely":
        return None
    blob = " ".join(n for n in names if n)
    if _NOT_OBGYN_RE.search(blob):
        return None
    # A รพ.สต. is not a general hospital and must not be labelled one — it is the
    # local primary-care station, where ฝากครรภ์ and family planning are routine
    # and free or near-free. Its own grade, checked BEFORE the facilityType gate
    # because the one record carrying the signal is typed `hospital` while its
    # name plainly says โรงพยาบาลส่งเสริมสุขภาพตำบล.
    #
    # Only the records that CARRY the signal get it, which is one, not the 469
    # รพ.สต. in the directory. That is the same rule `tagged` already runs on:
    # five clinics of 873 are tagged, not because only five do OB-GYN but because
    # only five say so. The grade tracks the evidence, never the likelihood —
    # and sweeping all 469 in would rebuild the flood this work exists to undo.
    if _RPSAT_RE.search(blob) or a.get("facilityType") == "health-station":
        return "health-station"
    if a.get("facilityType") != "hospital":
        return None
    return "hospital-likely"
