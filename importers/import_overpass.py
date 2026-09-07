#!/usr/bin/env python3
"""Fold cache/overpass/*.json (the gentle crawl's snapshot) into Mot Dang records.

Called by import_all.py. Classification: OSM tags -> (category, subcategory).
Unnamed elements are skipped — no shelf for the nameless. Subcategory lands in
record["sub"]; build.py matches children by key against that list.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Per-field provenance lives at the repo root, not in importers/. Needed here
# so a name this file WRITES (the parking fence) says who wrote it.
sys.path.insert(0, str(ROOT))
import provenance  # noqa: E402


FOOD_INTL = {"japanese", "italian", "chinese", "korean", "indian", "vietnamese",
             "american", "french", "german", "mediterranean", "mexican", "pizza",
             "burger", "steak_house", "steak", "sushi", "western", "european",
             "international", "asian", "sandwich", "fish_and_chips",
             "italian_pizza", "barbecue", "grill", "curry"}


def food_sub(t):
    """Real-data-backed food granularity: amenity first (unambiguous), then
    the cuisine tag (683 thai / 90 japanese / 86 regional / ... in the actual
    crawl — see the survey that justified these buckets)."""
    a, s = t.get("amenity"), t.get("shop")
    cuisines = {c.strip() for c in (t.get("cuisine") or "").split(";") if c.strip()}
    if a in ("fast_food", "food_court"):
        return "street-food"
    if s == "bakery" or a == "ice_cream" or cuisines & {"cake", "ice_cream", "dessert"}:
        return "bakery-dessert"
    if a in ("bar", "pub", "biergarten"):
        return "bar-pub"
    # diet:vegetarian=only means the kitchen IS vegetarian; =yes only means it
    # has options, and 151 omnivore places carry that. Sweeping =yes onto the
    # มังสวิรัติ-เจ shelf would send someone keeping เจ to a pork-and-rice shop,
    # so only `only` counts — which is why the shelf read 0 before.
    diets = {t.get("diet:vegetarian"), t.get("diet:vegan")}
    if cuisines & {"vegetarian", "vegan"} or "only" in diets:
        return "vegetarian"
    # THE TAG RULE WAS WRITTEN AND THE NAME RULE NEVER WAS. The diet rule above
    # is right and it only fires on a tag 51 places carry; meanwhile 40 shops
    # said it on their own signboards — Ming Kwan Vegetarian, Imjai Vegan,
    # Pakbai Vegetarian and Vegan Food, and one simply called มังสวิรัติ — and
    # every one of them was filed `thai` or `cafe`. That is the WO-22 lesson
    # one shelf further along: before a shelf is called thin, READ THE NAMES.
    # Bare เจ is deliberately not in this list: it is a common syllable in Thai
    # names (เจ็ดยอด, เจริญ) and would sweep in hundreds of unrelated places.
    name = " ".join(str(t.get(k) or "") for k in ("name", "name:th", "name:en")).lower()
    if any(w in name for w in ("มังสวิรัติ", "อาหารเจ", "ร้านเจ", "vegetarian", "vegan")):
        return "vegetarian"
    # อาหารเหนือ has no cuisine tag and no shelf until now: `regional` is the
    # nearest OSM value and it means nothing in particular. In the province
    # that is this food's home ground, that is the inverse-coverage law on our
    # own tree — the categories were written by people for whom sai ua was
    # exotic. The dish names ARE the signboards here.
    if any(w in name for w in ("อาหารเหนือ", "ขันโตก", "ไส้อั่ว", "แคบหมู", "จิ้นส้ม",
                               "ลาบเหนือ", "น้ำพริกหนุ่ม", "northern thai", "khantoke",
                               "kantoke", "lanna cuisine")):
        return "northern"
    if any(w in name for w in ("ข้าวซอย", "khao soi", "khaosoi", "น้ำเงี้ยว")):
        return "noodle"
    if cuisines & {"seafood", "fish"}:
        return "seafood"
    if cuisines & {"noodle", "noodles", "ramen"}:
        return "noodle"
    if cuisines & FOOD_INTL:
        return "international"
    return "thai"


# craft=* is a grab-bag: a bakery, a tailor and a glazier all carry it, and
# they belong on three different shelves. Sorting by what the place IS beats
# inventing a "crafts" shelf nobody would look under — someone wanting a suit
# altered searches for a tailor, not for a craft.
CRAFT_TO = {
    "handicraft": ("shopping", "crafts"), "jeweller": ("shopping", "crafts"),
    "woodworking": ("shopping", "crafts"), "furniture": ("shopping", "crafts"),
    "pottery": ("shopping", "crafts"), "basket_maker": ("shopping", "crafts"),
    "tailor": ("shopping", "tailor"),
    "dressmaker": ("shopping", "tailor"), "leather": ("shopping", "tailor"),
    # WO-56 batch: the menders. A cobbler mends what a tailor does not, and
    # sat on the tailor shelf since the first crawl; an electronics repairer
    # is not a phone shop. Both join sewing-machine and appliance repair on
    # repair/mend — the trades that fix the thing rather than sell it.
    "shoemaker": ("repair", "mend"), "sewing": ("repair", "mend"),
    "electronics_repair": ("repair", "mend"),
    "bakery": ("food", "bakery-dessert"), "confectionery": ("food", "bakery-dessert"),
    "coffee_roaster": ("food", "cafe"), "caterer": ("food", "thai"),
    "computer_repair": ("repair", "tech"),
    # The building trades — exactly what repair/home (ช่างบ้าน-ประปา-ไฟ) was
    # drawn for, and why it stayed a wireframe: the shelf existed, the query
    # never did.
    "plumber": ("repair", "home"), "electrician": ("repair", "home"),
    "carpenter": ("repair", "home"), "painter": ("repair", "home"),
    "hvac": ("repair", "home"), "glaziery": ("repair", "home"),
    "metal_construction": ("repair", "home"), "roofer": ("repair", "home"),
    "builder": ("repair", "home"), "locksmith": ("repair", "home"),
    "gardener": ("home-services", "landscaper"),
}


# --- กัญชา และ กระท่อม · cannabis and kratom ---------------------------------
#
# Two trades on one shelf, kept in separate children because they are not the
# same thing and nobody here treats them as the same thing. กัญชา has been sold
# over a counter since 2022 and the shops are mapped as `shop=cannabis`.
# กระท่อม is older, plainer and cheaper, and has no tag of its own at all: a
# ร้านน้ำกระท่อม is mapped as shop=herbalist, shop=convenience or nothing, and
# is found by its name or it is not found.
#
# THE HUT GUARD, which is where the name matching earns its keep or ruins the
# shelf. กระท่อม on its own is the ordinary word for a hut — กระท่อมริมน้ำ is a
# cottage by the water, not a kratom bar — so only the forms that name the leaf
# or the drink are matched. The same care in the other direction: `\bweed\b`
# and never a bare `weed`, or every seaweed shop in two provinces arrives.
KRATOM_NAME = re.compile(
    r"ใบกระท่อม|น้ำกระท่อม|ร้านกระท่อม|กระท่อมสด|น้ำใบกระท่อม"
    r"|\bkratom\w*|\bkrathom\w*", re.I)
CANNABIS_NAME = re.compile(
    r"กัญชา|กัญชง|\bcannabis\b|\bdispensar\w*|\bganja\b|\bweed\b", re.I)

# A name is a weaker witness than a tag. Where the tags already say plainly
# that the place is something else, the name does not get to overrule them —
# it only gets to raise the question. A ก๋วยเตี๋ยวกัญชา is a noodle shop that
# cooks with the leaf; a monument named "Weed leaf" is a monument. Both are
# real, neither is a dispensary, and neither is a call an importer should make
# on its own, so they go to a review file for a person.
CONTESTED_KEYS = ("amenity", "tourism", "historic", "leisure", "office",
                  "healthcare", "craft", "aeroway", "railway", "natural")

AMBIGUOUS = object()

# amenity / healthcare value -> which kind of medical place it is.
#
# A PHARMACY IS MEDICAL, and it sat on no shelf at all: `shop=chemist` had no
# rule here, so 32 Chiang Mai chemists were classified as nothing and dropped
# at import. In this city a ร้านขายยา is where most people go first with a
# fever, ahead of any clinic, and filing it under shopping beside the hardware
# stores would describe the wrong errand.
#
# `healthcare=alternative` is matched ABOVE this, to thai-medicine, because
# แพทย์แผนไทย is its own tradition and not a lesser clinic.
MEDICAL_SUB = {
    "hospital": "hospital",
    "clinic": "clinic",
    "doctors": "doctors",
    "dentist": "dentist",
    "pharmacy": "pharmacy",
    "centre": "clinic",
    "laboratory": "laboratory",
    "physiotherapist": "physio",
    "optometrist": "optometrist",
    "midwife": "clinic",
    "birthing_centre": "clinic",
    "psychotherapist": "clinic",
    "rehabilitation": "physio",
    # WO-55: OSM's healthcare=occupational_therapist. Zero elements carry it
    # in either province today (cache/census, 2026-09-04); the rule is here so
    # the first one mapped lands on the rehabilitation shelf, not nowhere.
    "occupational_therapist": "physio",
    "blood_donation": "laboratory",
    "dialysis": "clinic",
}


_SETTLED = None


def _settled():
    """data/curated/cannabis.json — verdicts a person has already given.

    Curated outranks crawled, here as everywhere. Keyed by the OSM ref so a
    verdict survives a re-crawl; `cannabis` shelves it (with the sub the
    person chose), anything else keeps it wherever its own tags put it.
    """
    global _SETTLED
    if _SETTLED is None:
        f = ROOT / "data" / "curated" / "cannabis.json"
        _SETTLED = json.loads(f.read_text()).get("settled", {}) if f.exists() else {}
    return _SETTLED


def cannabis_sub(t, name):
    """Which child of the shelf. Kratom first — it is the one the name states
    outright, and a shop selling both is still, to a reader, the kratom shop
    on that corner."""
    if KRATOM_NAME.search(name):
        return "kratom"
    if (t.get("healthcare") or t.get("amenity") == "clinic"
            or t.get("shop") == "chemist" or "คลินิก" in name):
        return "clinic"
    if (t.get("amenity") in ("cafe", "restaurant", "bar", "pub")
            or t.get("cuisine") or "คาเฟ่" in name
            or re.search(r"\b(cafe|café|coffee|lounge|bar)\b", name, re.I)):
        return "cannabis-cafe"
    if (t.get("landuse") in ("farmland", "greenhouse_horticulture")
            or t.get("man_made") == "greenhouse"
            or re.search(r"ฟาร์ม|สวนกัญชา|วิสาหกิจ|\bfarm\b|\bgrow\w*", name, re.I)):
        return "farm"
    return "dispensary"


# The chang shelf's name rules live in ONE place — importers/audit_elephant.py
# — and are borrowed here rather than copied, because two copies of "what
# counts as an elephant name" would drift and the drift would be invisible.
# The audit reads canonical records; this reads raw OSM tags; the compounds
# are the same either way. Bare ช้าง is never a rule there and so never one
# here: ลุงช้าง is a nickname, ช้างเผือก a quarter, ดอยช้าง a mountain.
import audit_elephant as _chang_rules
# Same arrangement for the view rules (WO-21): audit_views owns the compounds
# and the fences, this file borrows them. One copy.
import audit_views as _views_rules
# And for the springs (WO-23): audit_hotsprings owns the compounds and the
# fences — bare โป่ง never matched, the village and the school and the bus
# stop that wear a spring's name kept off the shelf — this file borrows them.
import audit_hotsprings as _spring_rules
# And for the housing estates (WO-27 door 3): audit_realestate owns the fence
# — จัดสรร or a named developer, never bare หมู่บ้าน, which is the ordinary
# word for a village and would file somebody's home as a gated estate.
import audit_realestate as _estate_rules
# And for long-term care (WO-32): audit_longcare owns the tag rule and the
# fences — nursing_home/assisted_living/rehabilitation file as care, the
# orphanage and the training centre stay volunteer work, bare ผู้สูงอายุ is
# never a rule (it is in the name of every senior club).
import audit_longcare as _longcare_rules
# And for the shrines (WO-39): audit_shrines owns the compounds and the
# fences — ศาลา is not ศาล, the courts and the เจ้าพ่อหลวงอุปถัมภ์ schools
# never file, a name after หน้า/ใกล้ is navigating not naming. The `shrines`
# crawl group is STAGED and unfetched; this import is inert until it runs.
import audit_shrines as _shrine_rules


def chang_hit(t):
    """(sub) if an element from the elephants crawl group declares itself an
    elephant venue BY NAME, else None. Only ever consulted for elements of
    cache/overpass/<prov>/elephants.json — see the fence in records().

    The mapper's other tag wins the same way the audit's lodging fence works:
    a restaurant or a hotel that carries an elephant-camp name is that
    restaurant's or hotel's record (and a lead), not a camp — the camp, where
    there is one, is its own element or enters from its own page.
    """
    name = " ".join(v for v in (t.get("name"), t.get("name:th"), t.get("name:en"),
                                t.get("alt_name")) if v)
    if not name:
        return None
    if (t.get("amenity") in ("restaurant", "cafe", "bar", "pub", "fast_food")
            or t.get("tourism") in ("hotel", "guest_house", "hostel")):
        return None
    # A mapper who writes "(closed 2022)" into the name is stating the place
    # has shut, in the one field that always survives. Chok Chai Elephant Camp
    # (way 768135712) carries exactly that and no lifecycle tag, so is_gone()
    # cannot see it. Fenced here — it stays in the review file as evidence —
    # rather than in is_gone(), whose sitewide reach this order has no
    # business widening.
    if re.search(r"\(\s*closed\b|ปิดถาวร|ปิดกิจการ", name, re.I):
        return None
    low = name.lower()

    def hits(rules):
        return any(re.search(pat, low, re.I) for _, pat in rules)

    if hits(_chang_rules.CRAFT_RULES):
        return "elephant-craft"
    if hits(_chang_rules.CARE_RULES):
        return "elephant-care"
    if hits(_chang_rules.CAMP_RULES):
        return "elephant-camp"
    return None


def views_hit(t):
    """(sub) if an element from the elephants crawl group declares a waterfall
    or a viewpoint BY NAME, else None. Same fence and same reasons as
    chang_hit above: only ever consulted for cache/overpass/<prov>/
    elephants.json, whose WO-19 dragnet (tourism=zoo / theme_park /
    attraction, both provinces, fetched 2026-08-20) already caught น้ำตกแม่สา,
    น้ำตกบัวตอง, วชิรธาร, แม่ยะ, ขุนกรณ์ and the Chiang Rai skywalk, and left
    every one of them in the review file. A name that declares nothing stays
    there (WO-21, notes/views-proposal-2026-08-20.md).

    The lodging/food fence guards a different lunch here: น้ำตก is also a
    laab cousin, so a restaurant wearing the word stays a restaurant.
    """
    name = " ".join(v for v in (t.get("name"), t.get("name:th"), t.get("name:en"),
                                t.get("alt_name")) if v)
    if not name:
        return None
    if (t.get("amenity") in ("restaurant", "cafe", "bar", "pub", "fast_food")
            or t.get("tourism") in ("hotel", "guest_house", "hostel")):
        return None
    if re.search(r"\(\s*closed\b|ปิดถาวร|ปิดกิจการ", name, re.I):
        return None
    low = name.lower()

    def hits(rules):
        return any(re.search(pat, low, re.I) for _, pat in rules)

    if hits(_views_rules.WATERFALL_RULES):
        return "waterfall"
    if hits(_views_rules.VIEWPOINT_RULES):
        return "viewpoint"
    return None


def springs_hit(t):
    """(sub) if an element declares a hot spring, else None. Consulted for
    cache/overpass/<prov>/hotsprings.json (WO-23's own dragnet, fenced the
    same way the elephants file is) and — after chang and views — for the
    WO-19 elephants file, whose dragnet had already caught สันกำแพง,
    โป่งเดือด and เทพพนม and left them on the menu.

    The rules live in audit_hotsprings.py (one copy): `natural=hot_spring`
    states the thing itself; the fence keeps the resort, the school, the
    temple, the village and the bus stop that wear a spring's name on the
    shelves their tags earned; bare โป่ง is never matched — บ้านโป่ง and
    โป่งแยง are villages, not soaks.
    """
    name = " ".join(v for v in (t.get("name"), t.get("name:th"), t.get("name:en"),
                                t.get("alt_name")) if v)
    if not name:
        return None
    if re.search(r"\(\s*closed\b|ปิดถาวร|ปิดกิจการ", name, re.I):
        return None
    return _spring_rules.spring_hit_tags(t, name)


def moobaan_hit(t):
    """'moobaan' if a landuse=residential element declares a housing ESTATE,
    else None. Consulted for cache/overpass/<prov>/moobaan.json only.

    The rules live in audit_realestate.py (one copy): จัดสรร — the word for
    an allotted development — or a developer's own name on the arch. Bare
    หมู่บ้าน is not matched: it is the ordinary word for
    a village, this catalogue already holds eighteen real ones wearing it,
    and a village filed as a gated estate is a falsehood about where people
    live. An element the mapper already called a village keeps that.
    """
    return _estate_rules.moobaan_hit(t)


def cannabis_hit(t, ref=""):
    """(sub) if this belongs on the cannabis shelf, AMBIGUOUS if a person has
    to say, None if it has nothing to do with the shelf."""
    settled = _settled().get(ref)
    if settled:
        if settled.get("verdict") == "cannabis":
            return settled.get("sub") or cannabis_sub(t, t.get("name") or "")
        return None
    name = " ".join(v for v in (t.get("name"), t.get("name:th"), t.get("name:en"),
                                t.get("alt_name")) if v)
    # The tag settles it outright, whatever else the place also is. A shop
    # with `shop=cannabis` and `amenity=cafe` is a cannabis cafe, not a cafe.
    if t.get("shop") == "cannabis" or t.get("cannabis:cbd") == "yes":
        return cannabis_sub(t, name)
    if not (CANNABIS_NAME.search(name) or KRATOM_NAME.search(name)):
        return None
    if any(k in t for k in CONTESTED_KEYS):
        return AMBIGUOUS
    return cannabis_sub(t, name)


def is_gone(t):
    """True for things that are named on the map but not places you can go.

    OSM keeps a feature after it shuts, marked rather than deleted, and it
    keeps military ground under the same tags as civil ground. Both were being
    filed as ordinary destinations: the CR stations crawl brought in
    "สนามบินเก่าเชียงราย / Old Chiang Rai Airport", which is `disused=yes`,
    `military=airfield`, `operator=Military of Thailand` — and which the
    toilets page promptly offered as a free clean toilet open all day. Sending
    somebody there would be wrong twice over, and worse for a foreigner.

    Deliberately not a judgement call about how busy a place is. Only what the
    map states outright: it has closed, or it is not civil ground.

    A namespaced `disused:amenity=restaurant` is NOT tested, and that is the
    point. It marks what a building used to be, and it sits happily beside a
    live tag when something new opened in the old shell — Xaviernimman5 on
    Nimman carries `disused:amenity=restaurant` and `amenity=pub`, surveyed
    2025-03-28, `opening_hours=24/7`. A rule that read the namespaced key would
    close a pub that is open right now. Where there is no live tag to go with
    it, classify() returns nothing and the record never arrives anyway.
    """
    if t.get("disused") == "yes" or t.get("abandoned") == "yes":
        return True
    return bool(t.get("military") or t.get("landuse") == "military")


# --- schools -------------------------------------------------------------
#
# `amenity=school` used to return ("school-intl", None) — every school in both
# provinces filed as an international school. It did not show, because the
# crawl only ever asked for schools with International or นานาชาติ in the
# name, so the rule was never wrong about anything it actually saw. The moment
# that filter came off, it would have filed 800 village schools as
# international, which is the single worst thing this shelf could say.
#
# What a school IS, it mostly says in its own name, and Thai school names are
# unusually honest: โรงเรียนอนุบาล is a kindergarten, โรงเรียนสอนขับรถ teaches
# driving, ค่ายมวย is a muay thai camp. The tag settles the easy cases and the
# name settles the rest.

# THE หมวย GUARD, the same shape as the กระท่อม one on the cannabis shelf.
# Bare มวย cannot be matched: หมวย is an ordinary nickname and ร้านหมวย is
# Muay's shop, not a boxing camp. Only the compounds a camp actually uses.
MUAYTHAI_NAME = re.compile(r"มวยไทย|ค่ายมวย|สนามมวย|ยิมมวย|โรงเรียนมวย"
                           r"|\bmuay\b|\bmuaythai\b|boxing (?:gym|camp|stadium)",
                           re.I)
INTL_NAME = re.compile(r"นานาชาติ|\binternational\b", re.I)
# THE INTERNATIONAL GATE, and it is a tag gate because the word cannot carry
# this on its own. "International" is an ordinary word in the name of an
# organisation that teaches ADULTS, and the name rule — which used to run
# first and above everything — read it as โรงเรียนนานาชาติ every time:
#   WVS ITC Worldwide Veterinary Service International Training Center
#     (office=educational_institution) — veterinary CPD, and the Listing
#     Sheet reported it to a family in Nam Phrae as the nearest international
#     school, 1,587 m away.
#   International College of Digital Innovation (amenity=university) — CMU's
#     tertiary college.
#   International Sustainable Development Studies Institute (ISDSI).
#   International language school (amenity=training, training=language).
# นานาชาติ is not the failure mode: all four are English-named. Every one of
# the 15 genuine international schools in these two provinces carries
# amenity=school or amenity=kindergarten, so the tag settles it at no cost —
# it says "a school children attend", which is the whole claim this shelf
# makes. A record without one of those tags falls through to the ordinary
# ordering below and lands on the shelf its own words earn.
INTL_SCHOOL_AMENITY = {"school", "kindergarten"}
# A campus is full of buildings that are not schools. 70 records — ภาควิชาเคมี,
# โรงอาหารคณะครุศาสตร์, อาคารเรียนรวม C — were sitting on the universities
# shelf, so "universities in Chiang Mai" answered with a canteen. They are real
# places worth finding; they are simply parts of one, and they get to say so.
CAMPUS_PART = re.compile(r"^\s*(?:อาคาร|ภาควิชา|คณะ|สาขาวิชา|หอพัก|หอประชุม"
                         r"|โรงอาหาร|ห้อง|ศูนย์หนังสือ|สนามกีฬา|ลาน|โรงยิม"
                         r"|สำนัก|สโมสรนักศึกษา|กอง|โรงฝึกงาน|บัณฑิตวิทยาลัย"
                         r"|ศูนย์วิจัย|หอสมุด"
                         r"|faculty\b|department\b|dept\b|building\b|hall\b"
                         r"|library\b|canteen\b|dormitory\b)", re.I)
# The same thing said mid-name: "CMU Faculty of Agriculture, Khunchangkhian".
# Anchored only where a bare word would over-reach — `hall` unanchored eats
# Marshall — so these are the two phrases that cannot mean anything else.
CAMPUS_PART_MID = re.compile(r"faculty of\b|\bcampus\b", re.I)
SCHOOL_NAME_SUB = (
    # (sub, pattern) — first match wins, so the specific sit above the general.
    ("monastic", r"พระปริยัติธรรม|ปริยัติธรรม|ธรรมศึกษา|พุทธศาสนาวันอาทิตย์"),
    ("religious", r"อิสลาม|ปอเนาะ|มัสยิด|ศาสนาอิสลาม|คริสเตียน|คาทอลิก"
                  r"|สอนศาสนา|\bislamic\b|\bchristian\b|\bcatholic\b"
                  r"|\bbible\b|\bmadrasa\w*\b"),
    ("special", r"โสตศึกษา|สอนคนตาบอด|ศึกษาพิเศษ|ปัญญานุกูล|ราชประชานุเคราะห์"
                r"|ศึกษาสงเคราะห์|การศึกษาพิเศษ|คนพิการ"),
    ("muaythai", None),                       # handled by MUAYTHAI_NAME
    # `culinary (?:school|academy)` missed "Gap's Thai Culinary Art School",
    # which then fell through to music-art on "art school" (WO-14, 2026-08-19).
    # The optional "art(s)" is the fix; the cooking shelf's own audit
    # (importers/audit_cooking.py) reads the same words off existing records.
    ("cooking", r"สอนทำอาหาร|สอนอาหาร|โรงเรียนอาหาร|cooking (?:school|class)"
                r"|cookery|culinary (?:arts? )?(?:school|academy|institute)"),
    ("massage-school", r"โรงเรียนสอนนวด|สอนนวด|massage school"
                       r"|school of (?:thai )?massage"),
    # ฝึกขับขี่ and "driving training center" are here so the general
    # training rule at the bottom never takes a driving school off this line:
    # ศูนย์ฝึกขับขี่ปลอดภัย กรีนวิง / Green Wing Safety Driving Training Center
    # is tagged amenity=driving_school and must stay a driving school.
    ("driving", r"สอนขับรถ|โรงเรียนขับรถ|ฝึกขับขี่|ขับขี่ปลอดภัย"
                r"|driving (?:school|training|cent(?:re|er))|safety driving"),
    ("language", r"สอนภาษา|โรงเรียนภาษา|สถาบันภาษา|language (?:school|institute"
                 r"|centre|center)|school of english|\btesol\b"),
    ("tutoring", r"กวดวิชา|ติวเตอร์|โรงเรียนติว|\btutor\w*\b|cram school"),
    ("music-art", r"โรงเรียนดนตรี|สอนดนตรี|สอนศิลปะ|โรงเรียนศิลปะ|ดุริยางค"
                  r"|music (?:school|academy|institute)|art school"),
    ("dance", r"สอนเต้น|โรงเรียนสอนเต้น|ลีลาศ|นาฏศิลป์|บัลเล่ต์"
              r"|dance (?:school|studio|academy)|\bballet\b"),
    # มหาวิทยาลัย CONTAINS วิทยาลัย, so Chiang Mai Rajabhat University arrived
    # as a college on the first dry run. Bare เทคนิค is worse: เทคนิคการแพทย์
    # is medical technology, and CMU's Faculty of Medical Technology was filed
    # as a vocational college by it. Both need the longer word, not the
    # fragment — the same lesson as กระท่อม and หมวย.
    ("college", r"(?<!มหา)วิทยาลัย|อาชีวศึกษา|วิทยาลัยเทคนิค|โปลีเทคนิค"
                r"|พาณิชยการ|\bcollege\b|\bpolytechnic\b|vocational"),
    ("kindergarten", r"อนุบาล|เตรียมอนุบาล|เนอสเซอรี่|ศูนย์พัฒนาเด็ก"
                     r"|kindergarten|nursery|pre-?school|childcare|daycare"),
    # Last, because it is the most general word here and every specific kind
    # above it is also, technically, training. amenity=training already maps
    # to this sub; this is the same answer read off the name, for the places
    # that carry office=educational_institution instead and would otherwise
    # take the university fallback at the bottom of school_sub(). WVS ITC —
    # veterinary CPD, four days a week in Hang Dong — is one of those, and
    # ศูนย์ฝึกอบรม is what its shelf label already says in Thai. Bare ศูนย์ฝึก
    # is NOT here: ศูนย์ฝึกขับขี่ปลอดภัย is a driving school and says so in
    # its tag, and a general name word must never out-rank a specific tag.
    ("training", r"ฝึกอบรม|อบรมวิชาชีพ"
                 r"|training (?:cent(?:re|er)|institute|academy|school)"),
)
SCHOOL_NAME_SUB = tuple((sub, re.compile(pat, re.I) if pat else None)
                        for sub, pat in SCHOOL_NAME_SUB)

# Tag -> sub, where OSM has already been explicit. The name still gets a look
# first for the kinds OSM has no tag for at all.
EDUCATION_AMENITIES = {"school", "university", "college", "kindergarten",
                       "childcare", "prep_school", "language_school",
                       "music_school", "driving_school", "training",
                       "cooking_school"}
SCHOOL_TAG_SUB = {
    "language_school": "language",
    "music_school": "music-art",
    "driving_school": "driving",
    "prep_school": "tutoring",
    "kindergarten": "kindergarten",
    "childcare": "kindergarten",
    "college": "college",
    "university": "university",
    "training": "training",
    # OSM's own approved tag for a cooking school. The census of 2026-08-07
    # counts it on ZERO elements in TH-50 and TH-57 and the schools crawl group
    # does not ask for it yet (a selector is a network change — Nan's go), so
    # today this line is a promise: the day a mapper uses the tag, the record
    # lands on the right shelf without a name rule.
    "cooking_school": "cooking",
}


# สองแถว / rot daeng, written in the name because OSM has no tag for it.
# Latin spellings vary as much as the trucks do: songthaew, songtaew, song thaew.
SONGTHAEW_NAME = re.compile(r"สองแถว|รถแดง|song ?t[ha]?aew|songtaew|rot daeng", re.I)
# WO-57. A water shop or a gas agent, read off its own sign. น้ำดื่ม is the
# drinking-water word and collides with nothing; ส่งน้ำ is NOT here, because
# คลองส่งน้ำ is an irrigation canal and there are dozens in this valley.
UTILITY_NAME = re.compile(
    r"น้ำดื่ม|ร้านแก๊ส|ส่งแก๊ส|แก๊สหุงต้ม|ตู้น้ำหยอดเหรียญ|drinking water", re.I)
# WO-57. The handicraft names the `making` group asked for and this file then
# had no rule to file: the two celadon works, the Bo Sang sa-paper and
# umbrella centre, and WO-51's carving-village centre. They carry a craft name
# and man_made=works, tourism=attraction or building=retail — never a shop
# tag. The name is the evidence, as it is for songthaew and for the water
# shops above. Fenced against a WAT with a craft word in its name.
# WO-58. A village cremation ground, read off its own name. สุสาน is the
# ground — not a "cemetery" in the western sense, because the north cremates;
# ป่าช้า is the older word for the same place, เมรุ the furnace building,
# ฌาปนสถาน the formal one. This exists because 155 of Chiang Rai's 156
# shop=funeral_directors elements are grounds, not shops.
# ณาปน with ณ is on real signs and in OSM as often as the correct ฌาปน.
# The English/French spellings are here because three grounds in this crawl
# are named only "Crematorium" and would otherwise read as a business.
CREMATION_GROUND = re.compile(
    r"สุสาน|ป่าช้า|ฌาปน|ณาปน|เมรุ|graveyard|cemetery|cr[ée]matorium|crematory", re.I)

MAKING_NAME = re.compile(
    r"ศิลาดล|celadon|เครื่องเขิน|lacquer|กระดาษสา|ร่มบ่อสร้าง|หัตถกรรม|handicraft"
    r"|เครื่องเงิน|silversmith|ผ้าทอ|woodcarv|แกะสลัก", re.I)


def school_sub(t, name):
    """Which kind of school this is, or None if it is not one.

    Read in this order: the school's own word for itself first, because a
    Thai school name says what it is more reliably than an OSM tag chosen by
    whoever mapped it; the tag second; the plain fallback last.
    """
    n = " ".join(v for v in (name, t.get("name:th"), t.get("name:en"),
                             t.get("alt_name")) if v)
    a = t.get("amenity")
    # International first among the name rules: it is the one distinction a
    # reader is most often searching for, and a school that calls itself
    # นานาชาติ is telling us on purpose. Gated on the tag — see
    # INTL_SCHOOL_AMENITY for the four records that gate exists for.
    if INTL_NAME.search(n) and a in INTL_SCHOOL_AMENITY:
        return "international"
    if MUAYTHAI_NAME.search(n) or t.get("sport") == "muay_thai":
        return "muaythai"
    # A part of a campus, tested before any name rule and only where the tags
    # already put us on a campus. คณะเทคนิคการแพทย์ and บัณฑิตวิทยาลัย read as
    # colleges to the name rules below, and a School of English tagged as a
    # language school never reaches this line at all.
    if (a in ("university", "college")
            or t.get("office") == "educational_institution"):
        if CAMPUS_PART.search(n) or CAMPUS_PART_MID.search(n):
            return "campus"
    for sub, pat in SCHOOL_NAME_SUB:
        if pat is not None and pat.search(n):
            return sub
    if a == "university" or t.get("office") == "educational_institution":
        return "university"
    if a in SCHOOL_TAG_SUB:
        return SCHOOL_TAG_SUB[a]
    if a == "school":
        return "government"
    return None


_RE_DORM = re.compile(r"\bdorm(itor(y|ies))?s?\b", re.I)
_RE_CONDO = re.compile(r"\bcondo(minium)?s?\b", re.I)


def realestate_sub(t, name):
    """building=apartments -> the residential shelf the building's own words
    put it on: dorm, condo, or apartment.

    Until 2026-08-21 every named building=apartments was filed as "condo"
    and the shelf label read Condo Buildings. The shelf held 316; the names
    held 53 condos. The rest are แมนชั่น, คอร์ท, อพาร์ตเมนต์ and หอพัก —
    monthly buildings a reader hunting a condominium does not mean, and the
    readers hunting those buildings could not see them under a condo label.
    Same class of error as the barber shelf (6 of 62): the truth was on the
    buildings' own signs, most of it in Thai.

    Order matters. หอพัก first — student housing is its own trade with its
    own price shape and its own asker. Then คอนโด, where a mapper's
    description=condo counts too: it is the mapper stating the building's
    kind, the same voice as the tag. A name that states nothing files as
    apartment, because that is the word the tag itself uses —
    building=apartments — and it claims less than "condo" did. "Condotel"
    stays off the condo shelf by the word boundary: a condotel sells nights,
    and its building files by the rest of its name.
    """
    n = " ".join(filter(None, [name, t.get("name:th"), t.get("name:en")]))
    if "หอพัก" in n or _RE_DORM.search(n):
        return "dorm"
    desc = t.get("description") or ""
    if "คอนโด" in n or "คอนโด" in desc or _RE_CONDO.search(n) or _RE_CONDO.search(desc):
        return "condo"
    return "apartment"


def classify(t):
    """tags -> (cat, sub or None), or None to skip."""
    s, a, tr = t.get("shop"), t.get("amenity"), t.get("tourism")
    craft = t.get("craft")
    if craft in CRAFT_TO:
        return CRAFT_TO[craft]
    # A laundry is not a housekeeper. 59 of them is the single biggest thing
    # this crawl found, and สะดวกซัก on a soi corner is a city essential in
    # exactly the way a bank is, so it gets its own shelf rather than being
    # filed under staff-you-hire.
    if s in ("laundry", "dry_cleaning") or a == "laundry":
        return "essentials", "laundry"
    # WO-56 batch (2026-09-04). Six trades the census counted in the
    # hundreds and no group had asked for — see the foot of QUERIES in
    # crawl_overpass.py. Each gets the shelf a reader would look under, not
    # a "misc" bin: a funeral director beside post and gov (it is the errand
    # nobody plans), bicycles with the other ways of getting around, water
    # and cooking gas with the city essentials, and the menders on the
    # repair tree beside the motor and phone shops.
    # WO-58, corrected the same day. **155 of the 156 Chiang Rai elements
    # tagged shop=funeral_directors are village cremation grounds** — สุสาน
    # and ป่าช้า, named for their village — and exactly one is a business.
    # A mapper there has used the shop tag for the ground itself. Filing all
    # 156 on a shop shelf beside the banks and the post offices would tell a
    # reader Chiang Rai holds 156 funeral businesses when it holds about one,
    # which is the "read the content, not the columns" rule in one line.
    # So the NAME decides: a name that says สุสาน / ป่าช้า / ฌาปนสถาน / เมรุ
    # is the village's cremation ground and files as a community facility;
    # everything else on those tags is the trade.
    _fun_name = " ".join(str(t.get(k) or "") for k in ("name", "name:th", "name:en"))
    if (s == "funeral_directors" or a in ("crematorium", "grave_yard")
            or t.get("landuse") == "cemetery"
            # Ten of these carry a สุสาน name and NO tag this function reads,
            # so they were dropped entirely: the name is the only evidence
            # there is, exactly as it is for songthaew stops and water shops.
            or CREMATION_GROUND.search(_fun_name)):
        if CREMATION_GROUND.search(_fun_name):
            return "community", "cremation"
        return "essentials", "funeral"
    if s in ("bicycle", "bicycle_repair") or a == "bicycle_rental":
        return "transport", "bicycle"
    if a == "motorcycle_rental":
        return "transport", "rental"
    if s == "motorcycle":
        return "transport", "motorbike"
    if s in ("water", "gas"):
        return "essentials", "utilities"
    # The name outranks the tag here, as it does for songthaew: a water shop
    # is mapped shop=yes or nothing at all, and writes น้ำดื่ม on its own
    # front. Fenced hard against คลองส่งน้ำ (an irrigation canal), the road
    # beside one, and the Royal Irrigation Department's ส่งน้ำและบำรุงรักษา
    # offices — the whole northern valley is threaded with them.
    if UTILITY_NAME.search(" ".join(str(t.get(k) or "") for k in
                                    ("name", "name:th", "name:en"))):
        if not (t.get("waterway") or t.get("highway") or t.get("landuse") == "government"):
            return "essentials", "utilities"
    if s in ("shoe_repair", "sewing", "electronics_repair", "appliance"):
        return "repair", "mend"
    if s == "garden_centre":
        return "home-services", "landscaper"
    if s in ("wholesale", "trade"):
        return "business", "wholesale"
    if t.get("office") == "coworking" or a == "coworking_space":
        return "business", "coworking"
    if t.get("office") in ("lawyer", "accountant", "tax_advisor", "notary"):
        return "business", "professional"
    # WO-54. The paper trades, filed as city essentials beside post and gov
    # because that is where the reader stands when they need one: outside
    # an office that wants two copies and a photo. Two voices, kept apart:
    # a copy shop SELLS you a copy; a translator or visa agent PREPARES a
    # document, which is a different trade with a different price.
    if s == "copyshop" or a == "copyshop":
        return "essentials", "copyshop"
    if craft == "printer" or s in ("printing", "print"):
        return "essentials", "printing"
    if t.get("office") in ("translator", "translation"):
        return "essentials", "translation"
    if t.get("office") == "visa":
        return "essentials", "visa"
    # WO-32. Until 2026-08-26 every amenity=social_facility filed here as
    # "Volunteering" and the social_facility=nursing_home|assisted_living|
    # rehabilitation subtag was thrown away — a nursing home, an
    # assisted-living garden and the best-known residential rehab in the
    # province all stood on the volunteer shelf. The rule lives in
    # importers/audit_longcare.py (one copy); the orphanage, the training
    # centre and the outreach office it fences stay volunteer work, which
    # for them is the right shelf.
    if _longcare_rules.longcare_hit(t):
        return "medical", "long-care"
    if t.get("office") in ("ngo", "charity") or a == "social_facility":
        return "community", "volunteer"
    # WO-27 door 2. A government office is an essentials record — the shelf
    # already holds townhalls under `gov` and this is the same door. It is
    # here for the สำนักงานที่ดิน above all: every chanote transfer in the
    # north walks through one and the catalogue held ZERO, which was the
    # buying question's biggest hole. The land offices are surfaced again on
    # /realestate.html by NAME (realestate_layer), not by a sub of their own:
    # a Land Office is a government office that happens to answer a property
    # question, and filing it anywhere else would hide it from the reader
    # looking for แขวง/อำเภอ offices.
    if t.get("office") == "government":
        return "essentials", "gov"
    # WO-27 door 4. Student housing OSM tags on the building itself rather
    # than in the name. building=apartments never reaches these, so the dorm
    # shelf could only ever hold the ones that wrote หอพัก on the sign.
    if t.get("building") == "dormitory":
        return "realestate", "dorm"
    if t.get("club") or t.get("office") == "association":
        return "community", "clubs"
    if a == "community_centre":
        return "community", "centre"
    if tr == "hotel":
        return "hotel", "hotel-full"
    if tr == "guest_house":
        return "hotel", "guesthouse"
    if tr == "hostel":
        return "hotel", "hostel"
    if a == "marketplace":
        return "market", "fresh"
    if s in ("mall", "department_store"):
        return "shopping", "mall"
    # The whole education family in one branch. It used to be three lines that
    # sent every school to the international shelf; school_sub() above carries
    # the reasoning and the guards.
    if (a in EDUCATION_AMENITIES
            or t.get("office") == "educational_institution"
            or t.get("leisure") in ("sports_centre", "dance")
            or t.get("sport") == "muay_thai"
            # A gym only leaves the gym shelf when it says muay thai itself.
            or (t.get("leisure") == "fitness_centre"
                and MUAYTHAI_NAME.search(t.get("name") or ""))):
        sub = school_sub(t, t.get("name") or "")
        if sub:
            return "school", sub
        # A sports centre that teaches nothing is a place to play, not a
        # school, and keeps the shelf it has always had.
        if t.get("leisure") in ("sports_centre", "dance"):
            return "sport", "gym"
        return None
    if t.get("office") == "estate_agent":
        return "realestate", "agent"
    if t.get("building") == "apartments":
        return "realestate", realestate_sub(t, t.get("name") or "")
    if a == "fuel":
        return "transport", "fuel"
    if a == "car_rental" or s == "motorcycle_rental":
        return "transport", "rental"
    # An aerodrome is its own thing, not a bus station: it keeps its own sub so
    # a reader (and the toilets page's landmark list) can ask for the airport
    # and get the airport, rather than the nearest record with the word in its
    # name — which is how "สนามบินเชียงใหม่ / Airport" once pinned a petrol
    # station two kilometres short of the terminal.
    #
    # An IATA code is the line between an airport and an airstrip, and the
    # distinction matters because /toilets.html tiers this sub as "free,
    # signposted, an accessible one, reachable without a ticket". True of a
    # passenger terminal; nonsense at Chiang Mai Sky Adventure, Chiang Mai
    # Airsport Airfield and Thong Kwao — three microlight strips that carry
    # aeroway=aerodrome and nothing else. Only CNX and CEI carry `iata`.
    # ICAO alone is not enough: the disused military field at Chiang Rai has
    # one (VTCR) and no scheduled passenger has ever walked into it.
    #
    # The strips are real places and Sky Adventure is a genuine attraction —
    # they are simply not transport, and belong to a leisure query nobody has
    # written yet rather than to a shelf that would misdescribe them.
    if t.get("aeroway") == "terminal":
        return "transport", "airport"
    if t.get("aeroway") == "aerodrome" and (t.get("iata")
                                            or t.get("aerodrome") == "international"):
        return "transport", "airport"
    if t.get("aeroway"):
        return None
    if a == "ferry_terminal":
        return "transport", "pier"
    # WO-13, the station split. All of this arrived on 2026-07-27 and was
    # thrown away at import: bus terminal, railway station, taxi rank and the
    # Doi Suthep funicular were folded into ONE sub called "station", and
    # amenity=taxi had no branch at all, so five taxi ranks — one with a phone
    # — were dropped before the canonical file. The tags were on disk the whole
    # time; this is a branch, not a crawl.
    if a == "taxi":
        return "transport", "taxi"
    # The funicular before the railway test, because it carries railway=station
    # too: the two "stations" at Doi Suthep are the top and bottom of the
    # temple's cable car, and a reader looking for a train must not meet them.
    if t.get("station") == "funicular" or t.get("railway") == "funicular":
        return "transport", "funicular"
    # The name outranks the tag here, deliberately and only here. A สองแถว
    # stop is not a bus station in any sense a reader means, and OSM has no tag
    # for one — so mappers write it in the name, 21 times across the two
    # provinces: "Songthaew Stop from Chiangmai to Samoeng", "ท่ารถสองแถวกิ่วสไต".
    # Reading that is the only way this shelf child can ever fill.
    if SONGTHAEW_NAME.search(" ".join(
            str(t.get(k) or "") for k in ("name", "name:th", "name:en", "description"))):
        return "transport", "songthaew"
    if t.get("railway") in ("station", "halt"):
        return "transport", "train"
    if a == "bus_station" or t.get("public_transport") == "station":
        return "transport", "bus"
    if s in ("car_repair", "motorcycle_repair"):
        return "repair", "auto"
    if s in ("computer", "mobile_phone"):
        return "repair", "tech"
    if s == "hairdresser":
        return "beauty", "barber" if t.get("hairdresser") == "barber" else "hair"
    if s == "beauty":
        # beauty= is a semicolon list in the wild ("nails;waxing"), so split it
        # rather than compare whole. A shop=beauty with nothing else said is a
        # beauty salon, not an unfiled record: returning None left 44 of them
        # off every shelf in the category they were crawled for.
        kinds = {k.strip() for k in (t.get("beauty") or "").split(";") if k.strip()}
        return "beauty", "nails" if "nails" in kinds else "beauty-spa"
    if a == "veterinary":
        return "pets", "vet"
    if s == "pet_grooming":
        return "pets", "grooming"
    if s == "pet":
        return "pets", None
    if t.get("leisure") == "fitness_centre":
        return "sport", "gym"
    if a == "bank":
        return "essentials", "bank"
    if a == "post_office":
        return "essentials", "post"
    if s == "convenience":
        return "essentials", "convenience"
    if a == "townhall":
        return "essentials", "gov"
    if tr == "museum":
        return "museums-galleries", "museum"
    if tr == "gallery":
        return "museums-galleries", "gallery"
    # WO-10, 2026-08-18. Libraries and books, neither ever crawled before this.
    #
    # amenity=library gets NO SUB on purpose. OSM does not say whether a library
    # is the district public one, a faculty's, or a temple's, and that
    # difference is substantially the whole shelf — it decides whether a reader
    # may walk in. The sub comes off the name in importers/audit_culture.py, and
    # a library whose name will not say stays sub-less rather than being guessed
    # onto a shelf. Same shape as the 237 sub-less massage records, and the
    # reason `read` will want appliesToCat when its facets land.
    if a == "library":
        return "read", None
    if s == "books":
        # OSM's own second_hand=* where it exists; `bookshop-new` is the general
        # ร้านหนังสือ shelf rather than a claim that a shop sells nothing used.
        if t.get("second_hand") in ("only", "yes"):
            return "read", "bookshop-used"
        return "read", "bookshop-new"
    if s in ("stationery", "newsagent"):
        return "read", "stationery"
    # shop=art is OSM stating that the place SELLS art. That is the one fact no
    # name and no other tag gives us, and it is exactly what separates a dealer
    # from an artist-run space — so it is the only route to gallery-commercial.
    if s == "art":
        return "museums-galleries", "gallery-commercial"
    # The celadon shelf is labelled ศิลาดล-เครื่องปั้นดินเผา and covers pottery
    # generally, so shop=pottery lands on it without overclaiming a tradition.
    # 2026-08-31: that shelf does not exist yet. categories.json holds no
    # `crafts` TOP-LEVEL category and no `celadon` child — only
    # shopping > crafts — so this rule returned a cat key the tree cannot
    # name, and three pottery shops (cm-osm-node-2005888864, -7041105907,
    # -8619103749) reached build.py as a KeyError. Mapped to the shelf that
    # exists, matching the CRAFT table above and the fallback below; restore
    # the celadon pair the day the child lands in categories.json.
    if s == "pottery":
        return "shopping", "crafts"
    # Tattoo is its own top-level category: 41 records were stranded under
    # 'sights' with no rule at all, so the whole trade was invisible.
    if s == "tattoo":
        return "tattoo", "studio"
    if s == "piercing":
        return "tattoo", "piercing"
    # Parks were never crawled before, so the directory simply had none.
    lz = t.get("leisure")
    if lz == "park":
        return "parks", "park"
    if lz == "garden":
        return "parks", "garden"
    if lz == "nature_reserve" or t.get("boundary") == "national_park":
        return "parks", "nature"
    if lz == "playground":
        return "parks", "playground"
    if t.get("natural") == "water":
        return "parks", "water"
    if tr == "viewpoint":
        return "sights", "viewpoint"
    # WO-21, after the crawl of 2026-08-21 and not before it. Both of these
    # are written against elements that have now been fetched and counted
    # (cm 42 waterfalls / 132 named peaks, cr 17 / 36) rather than against a
    # guess about what the north holds — the same discipline that left
    # shop=fabric and shop=antiques deliberately unclassified in WO-10.
    #
    # They sit BELOW natural=water on purpose. A waterfall is very often
    # mapped with the stream it falls down, and filing น้ำตกแม่สา as a body of
    # water rather than as the falls would bury the thing people travel for.
    # Reaching this line means the element said waterfall in its own tag.
    if t.get("waterway") == "waterfall":
        return "sights", "waterfall"
    # `natural=peak` is the summit itself. 79 of Chiang Mai's 131 carry `ele`,
    # so the elevation row lights up for most of them — and ดอยอินทนนท์ at
    # 2,565 m is the roof of the kingdom, which the directory did not hold in
    # any form until today. Named only (the selector says so): an unnamed
    # contour bump is not a place anyone looks up.
    if t.get("natural") == "peak":
        return "sights", "peak"
    if "historic" in t:
        return "sights", "historic"
    if s in ("doityourself", "hardware"):
        return "shopping", "diy"
    if s == "gift":
        return "shopping", "crafts"
    if s == "second_hand":
        return "shopping", "secondhand"
    # WO-50, after the crawl of 2026-08-31 and not before it — the same
    # discipline that left shop=fabric unclassified in WO-10 until somebody
    # had looked at the elements. These four values were never once asked for
    # by any selector in crawl_overpass.py, so there has never been a rule
    # here to file one, and the directory has held ZERO clothes shops and ZERO
    # shoe shops since the day it was built. The census of 2026-08-07 counts
    # 134 shop=clothes in TH-50 and 72 in TH-57.
    #
    # shop=boutique files with clothes rather than beside it: OSM's boutique
    # is a small clothes shop, and a shelf split on the shopkeeper's ambition
    # would ask a reader to guess which of two identical shelves has the
    # shirt. shop=bag is NOT here and is deliberately unclassified — see the
    # note on the `clothing` group; eight elements is too few to file blind
    # and a bag is not apparel.
    if s in ("clothes", "boutique"):
        return "shopping", "clothes"
    if s == "shoes":
        return "shopping", "shoes"
    # WO-57. The `making` group HAS run (2026-08-31, WO-51's crawl) and eleven
    # of its forty-two Chiang Mai elements were dropped at this function for
    # want of a rule: four shop=fabric (Golden Thai Silk, Kashmir Cashmere,
    # เฮือนฝ้าย ด้ายงาม, จักรเย็บผ้านครพิงค์), shop=antiques, shop=jewelry
    # (หลุยส์หัตถกรรมเครื่องเงิน — a silversmith), and four that carry a
    # handicraft NAME with no shop tag at all: บริษัท สยามศิลาดล and Baan
    # Celadon (the two celadon works), ศูนย์หัตถกรรมกระดาษสาและร่ม (the Bo
    # Sang sa-paper and umbrella centre) and ศูนย์หัตถกรรมไม้แกะสลักบ้านถวาย
    # (WO-51's own carving village centre). A crawl that runs and then drops
    # its find is the same failure as a crawl that never runs, and harder to
    # see. shop=fabric earns its own child: WO-46 gave the bedding trade one
    # and ผ้าฝ้าย/ผ้าทอ is its neighbour, not a craft souvenir.
    if s == "fabric":
        return "shopping", "fabric"
    # shop=musical_instrument, likewise never ruled on. The music shelf holds
    # 23 records and every one of them is a CURATED addition from the
    # instruments order — the mapped shops (Piano Center in Chiang Mai, two in
    # Chiang Rai) were dropped here for want of two lines.
    if s == "musical_instrument":
        return "shopping", "music"
    # WO-58/60. The glasses shops. MEDICAL_SUB knows healthcare=optometrist,
    # which nobody in either province uses; `shop=optician` is the tag the 85
    # actual shops carry and it had no rule, so the optometrist shelf stood at
    # ONE record — a mapped clinic — while Top Charoen alone has a dozen
    # branches here. A shop that fits glasses is medical enough for the shelf
    # a reader looks under, and /eyecare.html says plainly that a refraction
    # for glasses is not a diagnosis.
    if s == "optician":
        return "medical", "optometrist"
    if s in ("antiques", "jewelry", "jewellery"):
        return "shopping", "crafts"
    if MAKING_NAME.search(" ".join(str(t.get(k) or "") for k in
                                   ("name", "name:th", "name:en"))):
        if not (t.get("amenity") == "place_of_worship" or t.get("historic")):
            return "shopping", "crafts"
    # Sport as RETAIL, not as fitness. This shelf existed with exactly one
    # record in it (Decathlon) and no selector behind it. It earns its place
    # in this order because the sports chains are where a EU 46 boot is
    # actually stocked in this city — the answer to half of WO-50's question
    # is a shop nobody would think to file under clothing.
    if s in ("sports", "outdoor"):
        return "shopping", "sports-shop"
    if s == "herbalist" or t.get("healthcare") == "alternative":
        return "medical", "thai-medicine"
    # Medicine, which this crawl had never once asked for. There was no
    # selector for a clinic and no rule here to file one, so the whole shelf
    # came in sideways from the women's-health import and Chiang Rai held
    # three records. See MEDICAL_SUB for why a pharmacy counts.
    med = MEDICAL_SUB.get(a) or MEDICAL_SUB.get(t.get("healthcare"))
    if med or s == "chemist":
        return "medical", med or "pharmacy"
    if a == "cafe":
        return "food", "cafe"
    if a in ("restaurant", "fast_food", "food_court", "bar", "pub", "biergarten") \
            or s == "bakery" or a == "ice_cream":
        return "food", food_sub(t)
    if a == "cinema":
        return "whats-on", "cinema"
    if a in ("music_venue", "theatre"):
        return "whats-on", "live-music"
    if a == "events_venue":
        return "whats-on", "events-venue"
    return None


SEVEN_NAME_RX = re.compile(r"7[\s‐-]?eleven|7-11\b|เซเว่น|เซเวน", re.I)
# What may surround the brand on a real branch's sign and still mean nothing:
# the brand itself in any spelling (names arrive as name+name:th+name:en
# concatenated, so it often appears twice) and the generic shop word.
SEVEN_NOISE_RX = re.compile(
    r"7[\s‐/-]?eleven|7[\s‐/-]?11|เซเว่นอีเลฟเว่น|เซเว่น|เซเวน|"
    r"ร้านสะดวกซื้อ|convenience\s*store", re.I)


def seven_from_name(t, sub, name):
    """WO-38: the barber lie again, on the convenience shelf.

    57 records NAMED 7-Eleven carried no `brand` tag — the mapper typed the
    name and skipped the tag, and the record arrived brandless, off the brand
    tag page and out of every count. The name is the shop's own sign, so it
    fills the brand, provenance `brandFrom: osm-name` (audit:
    importers/audit_convenience.py prints every one).

    Fences, all three witnessed in the cache:
    - `not:brand:wikidata` wins. way/544559166 is named "7-Eleven" and carries
      not:brand:wikidata=Q259340 — a mapper explicitly saying *not really
      one* — and a denial outranks a name.
    - convenience sub only. เซเว่น สตาร์ is a condominium; a name rule that
      reaches past its own shelf files a building as a shop.
    - The sign must say the brand and NOTHING ELSE. "7-11 หลอด biers Bier
      Stube" (way/482772359) is the famous beer stall trading in 7-Eleven
      livery — the brand word inside a longer name is a nickname or an
      imitation, and branding it would put CP All's name on somebody's bar.
      So after stripping the brand in every spelling (it often appears twice:
      name and name:en concatenated) and the generic shop word, any residue
      refuses the fill. The refusal is visible in the audit's REFUSED report.

    Only 7-Eleven ships in this rule: its patterns are unambiguous. The
    Lotus/Big-C-named strays the same read surfaced are murkier (which era of
    the chain's name?) and wait in the audit's report for Nan.
    """
    if sub != "convenience" or t.get("not:brand:wikidata"):
        return None
    if not SEVEN_NAME_RX.search(name or ""):
        return None
    residue = SEVEN_NOISE_RX.sub(" ", name)
    if re.sub(r"[\s\-‐·.,/()#&+']+", "", residue):
        return None
    return "7-Eleven"


def _is_thai(s):
    return any("฀" <= ch <= "๿" for ch in s)


def address_of(t):
    """The addr:* family, kept as parts and as one readable line.

    OSM here is a mix of scripts — 'Suthep' and 'สุเทพ' both occur, sometimes on
    neighbouring shops — so the ต./อ. prefixes go on only where the value is
    already Thai. Nothing is translated or transliterated: what the mapper wrote
    is what the record carries.
    """
    parts = {
        "houseNumber": t.get("addr:housenumber") or t.get("addr:housename"),
        "street": t.get("addr:street"),
        "streetEn": t.get("addr:street:en"),
        "moo": t.get("addr:place") or t.get("addr:hamlet"),
        "subdistrict": t.get("addr:subdistrict"),
        "district": t.get("addr:district"),
        "postcode": t.get("addr:postcode"),
    }
    parts = {k: v.strip() for k, v in parts.items() if v and v.strip()}
    if not parts:
        return None, {}

    def tag(prefix, key):
        v = parts.get(key)
        if not v:
            return None
        if _is_thai(v) and not v.startswith(("ต.", "ตำบล", "อ.", "อำเภอ", "หมู่")):
            return prefix + v
        return v

    moo = parts.get("moo")
    if moo and moo.isdigit():
        moo = "หมู่ " + moo
    line = " ".join(x for x in (
        parts.get("houseNumber"), parts.get("street") or parts.get("streetEn"),
        moo, tag("ต.", "subdistrict"), tag("อ.", "district"), parts.get("postcode"),
    ) if x)
    # A bare house number with nothing to hang it on is not an address.
    if not (parts.get("street") or parts.get("streetEn") or parts.get("subdistrict")
            or parts.get("district") or parts.get("postcode")):
        return None, parts
    return line or None, parts


# Plain yes/no/qualified tags. The value is kept as the mapper wrote it:
# "yes", "no", "limited", "customers" and "only" all mean different things and
# flattening them to a boolean would throw the qualification away.
FEATURE_TAGS = {
    "wheelchair": "wheelchair",
    "outdoor_seating": "outdoorSeating",
    "indoor_seating": "indoorSeating",
    "air_conditioning": "airConditioning",
    "smoking": "smoking",
    "takeaway": "takeaway",
    "delivery": "delivery",
    "drive_through": "driveThrough",
    "self_service": "selfService",
    "changing_table": "changingTable",
    "atm": "atmOnSite",
    "toilets": "toilets",
    "toilets:wheelchair": "toiletsWheelchair",
    "fee": "fee",
    "access": "access",
    # What a คนที่มายืนหน้าร้าน actually came to ask. OSM namespaces these under
    # cannabis:* and the first pass read none of them, so a shop that had
    # already said what it sells arrived on the shelf saying nothing. Values
    # stay as written — "yes", "no", "only" and "licensed" are four different
    # answers and flattening them to a tick throws the answer away.
    "cannabis:recreational": "cannabisRecreational",
    "cannabis:medical": "cannabisMedical",
    "cannabis:cbd": "cannabisCbd",
    "cannabis:thc": "cannabisThc",
    "cannabis:edibles": "cannabisEdibles",
    "cannabis:seeds": "cannabisSeeds",
    "cannabis:smoking": "cannabisSmoking",
    # WO-67, the parking fence. Every one of these is a qualification, never a
    # boolean: `access=customers` is the difference between a car park and a
    # shop's forecourt you will be moved off, `fee=yes` with no `charge` is "it
    # costs, nobody wrote how much", and `supervised=yes` is the ยาม in the hut
    # who watches it. Absent stays absent — see the note at features_of(): on
    # this site silence means nobody has said, and for parking that matters
    # more than usual, because the tempting reading of a missing `fee` is
    # "free" and the tempting reading of a missing `access` is "anyone".
    "supervised": "supervised",
    "covered": "covered",
    "surface": "surface",
    "lit": "lit",
    "park_ride": "parkRide",
    # Whether a CAR park also takes motorbikes. Its own question: nearly every
    # car park here does in practice and almost none of them says so, which is
    # exactly why the tag is kept where it exists and never assumed where it
    # does not.
    "motorcycle": "motorcycle",
}

# Straight copies. Renamed only where the OSM key would collide with a field
# this catalogue already uses for something else — addr:province is the
# postal province, not the record's own `province`, so it keeps its own name.
SCALAR_TAGS = {
    "level": "level",
    "building:levels": "buildingLevels",
    "stars": "stars",
    "rooms": "rooms",
    "capacity": "capacity",
    "brand:th": "brandTh",
    "brand:en": "brandEn",
    "operator:th": "operatorTh",
    "operator:en": "operatorEn",
    "brand:wikipedia": "brandWikipedia",
    "description": "description",
    "description:en": "descriptionEn",
    "description:th": "descriptionTh",
    "addr:city": "city",
    "addr:province": "addrProvince",
    "source": "osmSource",
    # WO-67. `parking` is the STRUCTURE — surface, multi-storey, underground,
    # rooftop, street_side — and it is the one tag that changes what a reader
    # is looking for on the ground: a multi-storey is a building with a ramp,
    # street_side is a painted bay. `capacity:motorcycle` is not in either
    # province today (0 of 1,796) and is carried anyway, so that the first
    # mapper who writes it is not throwing it into a field nobody reads.
    "parking": "parkingType",
    "capacity:motorcycle": "capacityMotorcycle",
    "capacity:disabled": "capacityDisabled",
    "maxstay": "maxstay",
    "charge": "charge",
    "fee:conditional": "feeConditional",
}


# --------------------------------------------------------------- WO-67 ----
# THE PARKING FENCE, and the one place in this importer where a record without
# a name is allowed through.
#
# "Unnamed elements are skipped — no shelf for the nameless" is the rule at the
# top of this file and it is right nearly everywhere: an unnamed noodle shop is
# a rectangle somebody drew, and a directory of rectangles helps no one. A car
# park is the exception, and it is not a marginal one. Of the 1,796 parking
# features in these two provinces, 85 carry a name and 1,711 do not — 95%. The
# name is missing because there is nothing to write: the place is a piece of
# ground behind a shop, and what a reader needs to know about it is where it
# is, whether it costs, and whether they are allowed on it. All three are
# tagged. Only the signboard is missing, and only because there is no
# signboard.
#
# Nan, 2026-09-06, asked whether unnamed lots should publish: "Of course we
# want unnamed lots to publish!" So they are named from what they DO carry —
# the structure (multi-storey, surface, street-side), the vehicle, and the
# operator where one is given — and the bearings layer says where each one is
# ("580 m from Chang Phueak Gate"), which is the sentence a person standing on
# a scooter actually wants.
#
# THE SYNTHESISED NAME IS STAMPED `derived`, NOT `stated` (provenance.py). It
# was computed from tags OSM states; no mapper wrote it. That grade is what
# keeps it out of any give-back — we must never hand OpenStreetMap back a name
# we made up for a lot they deliberately left unnamed — and it is what lets a
# page say "described by its tags" instead of implying a signboard.
PARKING_KINDS = {
    # amenity -> (sub key, Thai word, English word)
    "parking":            ("parking",            "ที่จอดรถ",           "Parking"),
    "motorcycle_parking": ("motorcycle-parking", "ที่จอดมอเตอร์ไซค์",  "Motorcycle parking"),
    "bicycle_parking":    ("bicycle-parking",    "ที่จอดจักรยาน",      "Bicycle parking"),
    "parking_entrance":   ("parking-entrance",   "ทางเข้าที่จอดรถ",    "Parking entrance"),
}

# The structure, where OSM states it — and it is stated on 363 of the 1,796,
# which makes it by far the commonest thing we know about an unnamed lot. A
# multi-storey is a building you drive up inside; a street-side bay is a line
# of paint. Calling both "Parking" would be true and useless.
PARKING_STRUCTURE = {
    "multi-storey": ("อาคารจอดรถ", "Multi-storey car park"),
    "multi_storey": ("อาคารจอดรถ", "Multi-storey car park"),
    "garage":       ("อาคารจอดรถ", "Parking garage"),
    "garage_boxes": ("โรงจอดรถ", "Lock-up garages"),
    "underground":  ("ที่จอดรถใต้ดิน", "Underground car park"),
    "rooftop":      ("ที่จอดรถบนดาดฟ้า", "Rooftop car park"),
    "street_side":  ("ที่จอดริมถนน", "Street-side parking"),
    "lane":         ("ที่จอดริมถนน", "Street-side parking"),
    "layby":        ("ที่จอดริมทาง", "Lay-by"),
    "carports":     ("โรงจอดรถ", "Carports"),
    "surface":      ("ลานจอดรถ", "Car park"),
}


def parking_name(t):
    """(name, name_th, name_en, subs) for one parking element, or None.

    Returns None only when the element is not a parking feature at all, which
    inside the parking file means somebody widened the selectors without
    coming here — the fence refuses it rather than letting classify() guess.

    A named lot keeps its own name untouched; the synthesis is for the 95%
    that have none, and even for a named one the subs come from the tags.
    """
    amenity = (t.get("amenity") or "").strip()
    kind = PARKING_KINDS.get(amenity)
    if not kind:
        return None
    sub, th, en = kind
    # The car park shelf holds every kind of it — a motorbike bay IS parking,
    # and a reader who asks the shelf for parking should not have to know we
    # filed it under a second word. The specific child comes with it, so
    # "motorcycle parking" is a shelf query rather than a name search, which
    # is the whole of what Michael typed.
    subs = ["parking"] if sub != "parking" else []
    subs.append(sub)

    given = t.get("name") or t.get("name:th") or t.get("name:en")
    if given:
        return given, t.get("name:th"), t.get("name:en"), subs

    # Structure first: it is the more useful word and it is stated more often
    # than anything else here. Only for car parks — a multi-storey tag on a
    # motorcycle bay would be describing the building it sits in.
    if amenity == "parking":
        st = PARKING_STRUCTURE.get((t.get("parking") or "").strip().lower())
        if st:
            th, en = st
    # An operator is a name in all but the tag: "ที่จอดรถ เซ็นทรัลเฟสติวัล"
    # tells a reader exactly which lot this is. Thai operator name preferred
    # for the Thai side, since that is the side a Thai reader reads.
    op_th = (t.get("operator:th") or t.get("operator") or "").strip()
    op_en = (t.get("operator:en") or t.get("operator") or "").strip()
    name_th = f"{th} {op_th}".strip() if op_th else th
    name_en = f"{en} — {op_en}".strip() if op_en else en
    return name_th, name_th, name_en, subs


def features_of(t):
    """Facts the crawl already fetched and the first importer never read.

    Same family as the addr:* find — the network cost was paid on the first
    pass, these keys simply fell on the floor between the cache and the
    record. Nothing here is inferred: a tag that is absent is left out
    entirely rather than written as a "no", because on this site silence
    means nobody has said, not that the answer is no.

    Two things are deliberately NOT taken. `note` and `fixme` are mapper-to-
    mapper working notes, not facts about the place. `internet_access:password`
    is somebody's credential — public in OSM does not make it ours to
    republish beside their phone number.
    """
    a = {}
    for tag, key in FEATURE_TAGS.items():
        v = (t.get(tag) or "").strip()
        if v:
            a[key] = v
    for tag, key in SCALAR_TAGS.items():
        v = (t.get(tag) or "").strip()
        if v:
            a[key] = v

    # Wi-Fi. `internet_access` is the current tag and by far the commonest;
    # a bare `wifi` is the older form and still occurs. Whether it costs is a
    # separate question from whether it exists, so it keeps its own key.
    net = (t.get("internet_access") or t.get("wifi") or "").strip()
    if net:
        a["wifi"] = net
    for tag, key in (("internet_access:fee", "wifiFee"),
                     ("internet_access:ssid", "wifiSsid")):
        v = (t.get(tag) or "").strip()
        if v:
            a[key] = v

    # When a person last stood in front of the place. Link health says whether
    # a website still answers; this is the only first-hand signal in the
    # dataset that somebody checked the shop itself.
    for tag in ("check_date", "survey:date"):
        v = (t.get(tag) or "").strip()
        if v:
            a.setdefault("checkedOn", v)

    # The other names people actually use. Never rendered anywhere, but they
    # are what a reader types into the search box.
    alts = [v.strip() for v in (t.get("alt_name"), t.get("alt_name:en"),
                                t.get("short_name"), t.get("old_name"))
            if v and v.strip()]
    if alts:
        a["altNames"] = list(dict.fromkeys(alts))
    other = {lang: t["name:" + lang].strip()
             for lang in ("zh", "ja", "ko", "fr", "de", "ru", "es")
             if (t.get("name:" + lang) or "").strip()}
    if other:
        a["namesOther"] = other

    # How you pay. "Cash only" is the fact a reader most wants before setting
    # out, and OSM states it plainly often enough to be worth carrying.
    pay = {key: t[tag].strip() for tag, key in (
        ("payment:cash", "cash"), ("payment:credit_cards", "credit"),
        ("payment:debit_cards", "debit"), ("payment:cards", "cards"),
        ("payment:qr_code", "qr"), ("payment:visa", "visa"),
        ("payment:mastercard", "mastercard"),
    ) if (t.get(tag) or "").strip()}
    if pay:
        a["payment"] = pay

    # A small, real, entirely local cluster that no other directory of this
    # city carries. Only an outright yes counts — these tags are also used to
    # record that a place stopped accepting it.
    crypto = [name for tag, name in (
        ("currency:XBT", "bitcoin"), ("payment:onchain", "on-chain"),
        ("payment:lightning", "lightning"),
        ("payment:lightning_contactless", "lightning-contactless"),
        ("currency:XMR", "monero"),
    ) if (t.get(tag) or "").strip() in ("yes", "only")]
    if crypto:
        a["crypto"] = crypto

    diet = {k.split(":", 1)[1]: v.strip() for k, v in t.items()
            if k.startswith("diet:") and (v or "").strip()}
    if diet:
        a["diet"] = diet

    # Which pumps. On a town of scooters the question is never "is there a
    # petrol station" but "does that one have gasohol 91 / E20 / LPG".
    fuel = sorted(k.split(":", 1)[1] for k, v in t.items()
                  if k.startswith("fuel:") and (v or "").strip() == "yes")
    if fuel:
        a["fuel"] = fuel
    return a


def records(province="cm"):
    # fetched_0820: every id that entered from the elephants file (chang and
    # sights alike) — the 2026-08-20 fetch, restamped below so provenance
    # tells the truth about when its group was actually asked.
    out, review, ele_review, fetched_0820 = [], [], [], set()
    # spring_review / fetched_hs: the hotsprings group's own fence and its
    # own restamp set (WO-23) — same arrangement, its own date.
    spring_review, fetched_hs = [], set()
    # estate_review: the moobaan group's own fence (WO-27 door 3) — every
    # named residential area that does NOT declare an estate, which in this
    # province is nearly all of them, because they are villages.
    estate_review = []
    # shrine_review / fetched_sh: the shrines group's fence (WO-39, staged);
    # fetched_sh maps id -> the snapshot's own date, because the group has
    # no fetch date until Nan lets it run.
    shrine_review, fetched_sh = [], {}
    cache = ROOT / "cache" / "overpass" / province
    if not cache.exists():
        return out
    for f in sorted(cache.glob("*.json")):
        data = json.loads(f.read_text())
        for el in data.get("elements", []):
            t = el.get("tags", {})
            name = t.get("name") or t.get("name:th") or t.get("name:en")
            # THE ONE EXEMPTION FROM "no shelf for the nameless" (WO-67). A car
            # park is unnamed because there is no signboard, not because nobody
            # has got round to it: 1,711 of the 1,796 in these two provinces
            # carry no name and never will. See parking_name() for what is put
            # there instead and why the result is stamped `derived`.
            park_hit = parking_name(t) if f.stem == "parking" else None
            if park_hit:
                name, park_th, park_en, park_subs = park_hit
            elif not name:
                continue
            if is_gone(t):
                continue
            ref = f"{el['type']}/{el['id']}"
            # A lens a group's own fence assigned, carried to the record's
            # attrs below. Only the shrines branch sets one today
            # (wat/spirit-house matches on a lens, not a sub).
            lens_hit = None
            # THE ELEPHANTS FILE IS FENCED (WO-19). tourism=attraction is a
            # dragnet — waterfalls, gardens, tiger parks, snake farms, hot
            # springs — and this order asked for the elephants, not for an
            # attractions shelf. Only an element whose NAME declares an
            # elephant venue enters, on the chang shelf; every other element
            # in the file goes to cache/elephant_review_<prov>.txt, where it
            # is the ready-made menu for a FUTURE attractions decision (its
            # own order, its own tree thinking) rather than a record placed
            # by accident. Nothing from this file may reach classify(): a
            # generic rule (historic, museum, food) grabbing a province-wide
            # attraction element would widen the crawl's scope silently.
            if f.stem == "elephants":
                ele_sub = chang_hit(t)
                view_sub = None if ele_sub else views_hit(t)
                spring_sub = None if (ele_sub or view_sub) else springs_hit(t)
                if not ele_sub and not view_sub and not spring_sub:
                    ele_review.append((ref, name, dict(t)))
                    continue
                # WO-21 rides the same fence: a name that declares a waterfall
                # or a viewpoint files onto sights, and everything else still
                # goes to the review file, which stays the menu for whatever
                # attractions order comes next. classify() remains unreachable
                # from this file either way. WO-23 rides it the same way for
                # the springs the dragnet had already caught — สันกำแพง,
                # โป่งเดือด, เทพพนม — and takes nothing off the menu that is
                # not a spring.
                hit = (("chang", ele_sub) if ele_sub
                       else ("sights", view_sub or spring_sub))
                fetched_0820.add(f"{province}-osm-{el['type']}-{el['id']}")
            elif f.stem == "moobaan":
                # THE MOOBAAN FILE IS FENCED THE SAME WAY (WO-27 door 3).
                # `landuse=residential["name"]` returns every named
                # residential area in the province, and here that is mostly
                # VILLAGES — บ้านสันทราย, หมู่บ้านป่าไผ่ — not gated estates.
                # Only an element whose own name says จัดสรร or names a
                # developer files (moobaan_hit; rules in audit_realestate.py,
                # one copy); everything else goes to
                # cache/moobaan_review_<prov>.txt for a person. classify() is
                # unreachable from this file: a generic rule catching a
                # province-wide landuse element would widen the crawl's scope
                # silently, and the thing being widened over is where people
                # live.
                estate_sub = moobaan_hit(t)
                if not estate_sub:
                    estate_review.append((ref, name, dict(t)))
                    continue
                hit = ("realestate", estate_sub)
            elif f.stem == "shrines":
                # THE SHRINES FILE IS FENCED THE SAME WAY (WO-39, staged —
                # this branch is unreachable until Nan gives the group its
                # go). Its name selectors are a dragnet like the others:
                # courts, royal-patronage schools and pork-leg stalls wear
                # ศาล in their names. Only an element that states the shrine
                # files (shrines_hit; rules in audit_shrines.py, one copy) —
                # onto wat/shrine, the child the วัด-สิ่งศักดิ์สิทธิ์ shelf
                # was named for; everything else goes to
                # cache/shrine_review_<prov>.txt and classify() is
                # unreachable from this file. Records are stamped with the
                # snapshot file's own date, not the constructor's default,
                # so provenance stays true whenever the group first runs.
                shrine_sub = _shrine_rules.shrines_hit(t, name)
                if not shrine_sub:
                    shrine_review.append((ref, name, dict(t)))
                    continue
                hit = ("wat", shrine_sub)
                # ศาลพระภูมิ is its own shelf (wat/spirit-house, matched on a
                # lens) and had no path from a crawled name until now.
                lens_hit = _shrine_rules.shrine_lens(name)
                fetched_sh[f"{province}-osm-{el['type']}-{el['id']}"] = (
                    date.fromtimestamp(f.stat().st_mtime).isoformat())
            elif f.stem == "hotsprings":
                # THE HOTSPRINGS FILE IS FENCED THE SAME WAY (WO-23). Its
                # name selectors are a dragnet too: schools, temples and
                # whole villages wear a spring's name, and a bus stop called
                # น้ำพุร้อนสันกำแพง is where you get off FOR the spring —
                # filing it would pin the spring to the roadside. Only an
                # element that states the spring files (springs_hit; rules in
                # audit_hotsprings.py, one copy); everything else goes to
                # cache/hotspring_review_<prov>.txt where a person can see
                # it, and classify() is unreachable from this file. An
                # element the WO-19 fence already filed this run (สันกำแพง is
                # tourism=attraction AND answers the name selectors) keeps
                # its elephants-file lineage rather than arriving twice.
                if f"{province}-osm-{el['type']}-{el['id']}" in fetched_0820:
                    continue
                spring_sub = springs_hit(t)
                if not spring_sub:
                    spring_review.append((ref, name, dict(t)))
                    continue
                hit = ("sights", spring_sub)
                fetched_hs.add(f"{province}-osm-{el['type']}-{el['id']}")
            elif f.stem == "parking":
                # FENCED like the others, and for the same reason: nothing in
                # this file may reach classify(). The parking group asks four
                # amenity values province-wide, and an element that answers
                # none of them arrived because somebody widened the selectors
                # — it is refused here rather than being shelved by a generic
                # rule that happens to match its other tags. A named car park
                # inside a mall would otherwise classify as the mall.
                if not park_hit:
                    review.append((ref, name or "(unnamed)", dict(t)))
                    continue
                hit = ("transport", park_subs[-1])
            else:
                # The cannabis shelf is asked first, because the tag that puts a
                # place on it (`shop=cannabis`) sits happily beside a tag that
                # would otherwise put it somewhere else. Where only the NAME says
                # cannabis and the tags say something else, the place keeps the
                # shelf its tags earned and the disagreement goes to a person.
                weed = cannabis_hit(t, ref)
                if weed is AMBIGUOUS:
                    review.append((ref, name, dict(t)))
                    hit = classify(t)
                elif weed:
                    hit = ("cannabis", weed)
                else:
                    hit = classify(t)
                    # It came back from a query that asked for cannabis shops by
                    # trade name — 420, kush, sativa, budtender — and the
                    # classifier could not place it. That is not nothing: the
                    # vocabulary is short and deliberately not made of ordinary
                    # words, so a hit is worth a person's glance even when no rule
                    # can shelve it. Silence here would throw away the one search
                    # that reaches shops tagged shop=yes, which no other group asks
                    # for at all.
                    if f.stem == "cannabis" and t.get("shop") != "cannabis":
                        review.append((ref, name, dict(t)))
            if not hit:
                continue
            cat, sub = hit
            # Two shelves for a pharmacy, on purpose — see import_all's
            # import_womens_health for the reasoning. classify() answers with
            # one category because almost everything has one; this is the
            # exception, so it is widened here rather than by making every
            # rule return a list.
            cats = ["essentials", "medical"] if sub == "pharmacy" else [cat]
            # An international school belongs on both shelves and for two
            # different readers. โรงเรียนนานาชาติ is where a parent who moved
            # here looks first, and it has been a top-level shelf since the
            # site launched, so it keeps its place and its URLs; the schools
            # shelf carries it too, because a directory that separates the
            # international schools from all the others has quietly said the
            # others are a different kind of thing.
            # GATED ON THE CATEGORY, and it has to be: `international` is also
            # what food_sub() returns for international cuisine, so an
            # unguarded test on the sub alone put 579 restaurants on the
            # international-SCHOOLS shelf the first time this ran.
            if cat == "school" and sub == "international":
                cats = ["school", "school-intl"]
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lng = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None:
                continue
            # contact info is the directory's real currency — take every form OSM offers
            phone = (t.get("phone") or t.get("contact:phone") or t.get("phone:mobile")
                     or t.get("mobile") or t.get("contact:mobile"))
            website = (t.get("website") or t.get("contact:website") or t.get("url")
                       or t.get("website:en"))
            line = t.get("contact:line")
            addr_line, addr_parts = address_of(t)
            brand = t.get("brand")
            brand_from = None
            if not brand:
                _probe = " ".join(filter(None, (name, t.get("name:th"),
                                                t.get("name:en"))))
                brand = seven_from_name(t, sub, _probe)
                if brand:
                    brand_from = "osm-name"
            out.append({
                "id": f"{province}-osm-{el['type']}-{el['id']}", "province": province,
                "cat": cats,
                # A parking feature carries both its shelf word and its vehicle
                # (["parking", "motorcycle-parking"]), so it answers the shelf
                # AND the specific ask. Everywhere else one sub is the answer.
                "sub": park_subs if park_hit else ([sub] if sub else []),
                "name": name,
                "nameTh": park_th if park_hit else t.get("name:th"),
                "nameEn": park_en if park_hit else t.get("name:en"),
                "lat": lat, "lng": lng, "geoPrecision": "exact",
                "address": addr_line,
                "phone": phone,
                "website": website,
                "hours": t.get("opening_hours"),
                "attrs": {k: v for k, v in {
                    **addr_parts,
                    **features_of(t),
                    **({"lens": [lens_hit]} if lens_hit else {}),
                    # The medical children in categories.json match on
                    # attrs.facilityType, not on sub — that shape was set by
                    # the cm-womens-health import years before this crawl
                    # existed. A crawled clinic has to speak the same way or it
                    # arrives on the shelf and lands under none of its
                    # children.
                    # No `sector` is written here. It would have to be guessed,
                    # and it would be guessed wrong: โรงพยาบาลนครพิงค์ and
                    # โรงพยาบาลมหาราชนครเชียงใหม่ are state hospitals carrying
                    # the same amenity=hospital as any private one. Only the
                    # CITIZENinfo import states a sector, because there it is
                    # true by construction — that register IS the state list.
                    "facilityType": (sub if cat == "medical" else None),
                    "brand": brand, "brandFrom": brand_from,
                    "cuisine": t.get("cuisine"),
                    "operator": t.get("operator"), "lineId": line,
                    "email": t.get("email") or t.get("contact:email"),
                    "whatsapp": t.get("contact:whatsapp"),
                    "facebook": t.get("contact:facebook") or t.get("facebook"),
                    "instagram": t.get("contact:instagram") or t.get("instagram"),
                    "brandWebsite": (t.get("brand:website") if not website else None),
                    # A viewpoint's bearing and the height of the ground are
                    # measurements a mapper stood there and took (WO-21).
                    # Kept wherever OSM holds them; known_facts renders them
                    # as the measurements they are and never turns a westward
                    # bearing into "sunset point" — whether the horizon is
                    # open at dusk is the venue's or the door survey's to say.
                    "direction": t.get("direction"),
                    "ele": t.get("ele"),
                    # A spring's stated water temperature (WO-23) — the
                    # mapper's or the operator's measurement, kept as given
                    # and rendered as a measurement, never rounded into
                    # "very hot".
                    "temperature": t.get("temperature"),
                    # Reference tags, dropped since the first crawl. Small in
                    # number — 35 wikidata, 10 wikipedia — but they are the only
                    # links in the whole dataset that lead to a written account
                    # of the place itself. brand:wikidata is far commoner (697)
                    # and is a different animal: it describes the chain, not the
                    # branch, so it is kept under its own key and never
                    # presented as being about this shop.
                    "wikidata": t.get("wikidata"),
                    "wikipedia": t.get("wikipedia"),
                    "brandWikidata": t.get("brand:wikidata"),
                }.items() if v},
                "featured": False, "landmark": False,
                "sources": [{"type": "osm", "ref": f"{el['type']}/{el['id']}",
                             "fetched": "2026-07-27", "via": "mot-dang overpass"}],
                "confidence": "crawled", "updatedAt": "2026-07-27",
            })
            # A NAME WE WROTE SAYS SO, IN THE ONE PLACE THAT TRAVELS WITH IT.
            # `derived` is the exact grade: computed from tags the source
            # states — amenity, parking, operator — with nothing invented and
            # nothing surveyed. provenance.giveable() will not export it, so
            # the give-back can never offer OpenStreetMap a name for a lot
            # their mappers left bare on purpose. A lot that DID carry a name
            # is stamped `stated`, because a mapper wrote it.
            if park_hit:
                _psrc = out[-1]["sources"][0]
                _how = "stated" if (t.get("name") or t.get("name:th")
                                    or t.get("name:en")) else "derived"
                # Only fields that HOLD something. A receipt for a field that
                # is not there is not provenance, it is noise — and
                # provenance.validate() says so, which is how this was caught:
                # a mapper-named lot has `name` and no name:th, and stamping
                # all three left 148 receipts for empty fields.
                for _f in ("name", "nameTh", "nameEn"):
                    if out[-1].get(_f):
                        provenance.stamp(out[-1], _f, _psrc, _how)
                provenance.stamp(out[-1], "sub", _psrc, "derived")
    # The shared constructor stamps every record with the ORIGINAL crawl's
    # date. The elephants group was fetched 2026-08-20, and a record claiming
    # it was fetched three weeks before its group existed is a false statement
    # about provenance — so its records are re-stamped with their own date.
    for r in out:
        if r["id"] in fetched_0820:
            r["updatedAt"] = "2026-08-20"
            for src in r.get("sources", []):
                if src.get("type") == "osm":
                    src["fetched"] = "2026-08-20"
    # Same truth-telling for the hotsprings group (WO-23), fetched
    # 2026-08-20 on Nan's go: its records carry the date their group was
    # actually asked, not the constructor's default.
    for r in out:
        if r["id"] in fetched_hs:
            r["updatedAt"] = "2026-08-20"
            for src in r.get("sources", []):
                if src.get("type") == "osm":
                    src["fetched"] = "2026-08-20"
    _write_cannabis_review(province, review)
    _write_elephant_review(province, ele_review)
    # Same truth-telling for the shrines group (WO-39, staged): each record
    # carries its snapshot file's own date, captured above, because the
    # group has no fetch date until it is allowed to run.
    for r in out:
        stamp = fetched_sh.get(r["id"])
        if stamp:
            r["updatedAt"] = stamp
            for src in r.get("sources", []):
                if src.get("type") == "osm":
                    src["fetched"] = stamp
    _write_hotspring_review(province, spring_review)
    _write_shrine_review(province, shrine_review)
    _write_moobaan_review(province, estate_review)
    return out


def _write_elephant_review(province, rows):
    """What the elephants dragnet caught that is NOT an elephant venue.

    Not errors and not discards — the menu. tourism=zoo / theme_park /
    attraction over a whole province returns the waterfalls, the gardens, the
    hot springs, the tiger parks, everything a province calls an attraction;
    WO-19 took only the elephant-declaring names and this file is everything
    else, kept where a person can see it. If an attractions shelf ever becomes
    an order, its work-list is already written; if one of these IS an elephant
    venue under a name the rules don't read (a Karen village name, a Thai
    name with no ปางช้าง in it), the fix is a data/curated/shelves.json entry
    or a curated addition with a source — never a wider regex on a guess.
    """
    out = ROOT / "cache" / f"elephant_review_{province}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, unique = set(), []
    for row in rows:
        if row[0] not in seen:
            seen.add(row[0])
            unique.append(row)
    if not unique:
        out.write_text(f"# {province}: the elephants group is not in cache, or held "
                       f"nothing beyond the elephant venues.\n")
        return
    lines = [
        f"# {province}: {len(unique)} elements from the elephants crawl group",
        "# (tourism=zoo / theme_park / attraction, fetched 2026-08-20) that do",
        "# NOT declare an elephant venue by name, filed here instead of onto a",
        "# shelf. This is the ready-made menu for a future attractions order.",
        "# A real elephant venue hiding under another name enters through",
        "# data/curated/shelves.json or a curated addition, with a source.",
        "#",
    ]
    for ref, name, t in sorted(unique, key=lambda r: r[1].lower()):
        kind = (t.get("tourism") or t.get("historic") or t.get("leisure") or "?")
        lines.append(f"{ref:<22} [{kind}] {name}")
    out.write_text("\n".join(lines) + "\n")


def _write_shrine_review(province, rows):
    """What the shrines dragnet caught that does NOT state a shrine.

    Same posture as the others: not errors and not discards. The ศาล name
    family reaches courts, royal-patronage schools, pavilions and stalls
    navigating by a shrine; each is fenced here where a person can see it.
    A real shrine hiding under a name the rules don't read (Roi Dvarapala
    Ban Devalaya on community/clubs is the standing example) enters through
    data/shrines.json or a curated seat with a source — never a wider regex
    on a guess. Inert until the staged group runs.
    """
    out = ROOT / "cache" / f"shrine_review_{province}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, unique = set(), []
    for row in rows:
        if row[0] not in seen:
            seen.add(row[0])
            unique.append(row)
    if not unique:
        out.write_text(f"# {province}: the shrines group is not in cache "
                       f"(staged, unfetched — WO-39), or held nothing beyond "
                       f"the shrines.\n")
        return
    lines = [
        f"# {province}: {len(unique)} elements from the shrines crawl group",
        "# (historic=wayside_shrine / place_of_worship by stated religion /",
        "# shop=religion / the ศาลเจ้า name family) that do NOT state a",
        "# public shrine, filed here instead of onto a shelf.",
        "#",
    ]
    for ref, name, t in sorted(unique, key=lambda r: r[1].lower()):
        kind = (t.get("historic") or t.get("amenity") or t.get("shop")
                or t.get("religion") or "?")
        lines.append(f"{ref:24s} {kind:18s} {name}")
    out.write_text("\n".join(lines) + "\n")


def _write_hotspring_review(province, rows):
    """What the hotsprings dragnet caught that does NOT state a spring.

    The same posture as the elephant review: not errors and not discards.
    The name selectors reach schools, temples, villages, bus stops and
    resorts wearing a spring's name, and amenity=public_bath reaches shower
    blocks; each is fenced here where a person can see it. A real spring
    hiding under a name the rules don't read enters through
    data/curated/hotsprings.json or a curated addition, with a source —
    never a wider regex on a guess.
    """
    out = ROOT / "cache" / f"hotspring_review_{province}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, unique = set(), []
    for row in rows:
        if row[0] not in seen:
            seen.add(row[0])
            unique.append(row)
    if not unique:
        out.write_text(f"# {province}: the hotsprings group is not in cache, or "
                       f"held nothing beyond the springs.\n")
        return
    lines = [
        f"# {province}: {len(unique)} elements from the hotsprings crawl group",
        "# (natural=hot_spring / amenity=public_bath / the น้ำพุร้อน name",
        "# family, fetched 2026-08-20) that do NOT state a hot spring, filed",
        "# here instead of onto a shelf. A real spring hiding under another",
        "# name enters through data/curated/hotsprings.json or a curated",
        "# addition, with a source.",
        "#",
    ]
    for ref, name, t in sorted(unique, key=lambda r: r[1].lower()):
        kind = (t.get("natural") or t.get("amenity") or t.get("tourism")
                or t.get("place") or t.get("highway") or "?")
        lines.append(f"{ref:<22} [{kind}] {name}")
    out.write_text("\n".join(lines) + "\n")


def _write_moobaan_review(province, rows):
    """What the moobaan dragnet caught that is NOT a housing estate.

    The same posture as the elephant and spring reviews, and the stakes are
    higher: `landuse=residential["name"]` over a province returns the places
    people LIVE, and nearly all of them here are villages — บ้านสันทราย,
    หมู่บ้านป่าไผ่ — mapped with the ordinary Thai word that also appears on
    an estate's arch. Filing one as a gated development is a falsehood about
    somebody's home address, so only จัดสรร or a developer's own name files
    and everything else waits here for a person. A real estate hiding under
    a name these rules do not read enters through a curated addition with a
    source — never a wider regex on a guess.
    """
    out = ROOT / "cache" / f"moobaan_review_{province}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, unique = set(), []
    for row in rows:
        if row[0] not in seen:
            seen.add(row[0])
            unique.append(row)
    if not unique:
        out.write_text(f"# {province}: the moobaan group is not in cache, or "
                       f"held nothing beyond the estates.\n")
        return
    lines = [
        f"# {province}: {len(unique)} named residential areas that do NOT",
        "# declare a housing estate (landuse=residential[name]). Villages,",
        "# quarters and neighbourhoods — where people live, not developments",
        "# somebody is selling. Kept here rather than filed. A real estate",
        "# under a name the rules do not read enters through a curated",
        "# addition, with a source.",
        "#",
    ]
    for ref, name, t in sorted(unique, key=lambda r: r[1].lower()):
        kind = (t.get("place") or t.get("landuse") or "?")
        lines.append(f"{ref:<22} [{kind}] {name}")
    out.write_text("\n".join(lines) + "\n")


def _write_cannabis_review(province, review):
    """The disagreements, written down where a person can settle them.

    Not a log and not a warning — a worklist. Each line is a place whose NAME
    says cannabis or kratom and whose TAGS say something else, which is a
    question about a real shop that only somebody who has walked past it can
    answer. Nothing here reaches the shelf until it is answered in
    data/curated/cannabis.json, and a place already answered there never
    appears in this file again.
    """
    out = ROOT / "cache" / f"cannabis_review_{province}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    # A place caught by two crawl groups arrives twice — "cannabis cafe" is in
    # both restaurants.json and cannabis.json — and asking somebody the same
    # question twice is how a worklist stops being read.
    seen, unique = set(), []
    for row in review:
        if row[0] not in seen:
            seen.add(row[0])
            unique.append(row)
    review = unique
    if not review:
        out.write_text(f"# {province}: nothing to settle.\n")
        return
    lines = [
        f"# {province}: {len(review)} places whose name says cannabis or kratom",
        "# and whose tags say something else. Settle each one in",
        "# data/curated/cannabis.json under \"settled\", keyed by the ref below:",
        '#   "node/123": {"verdict": "cannabis", "sub": "dispensary",',
        '#                "why": "...", "on": "YYYY-MM-DD"}',
        '# verdict "no" keeps it on the shelf its own tags earned.',
        "#",
        "# THE ANSWER IS OFTEN BOTH, and there is already a way to say so. A",
        "# cannabis cafe really is a restaurant AND a dispensary, and forcing it",
        "# onto one shelf loses a reader either way. data/curated/shelves.json",
        "# ADDS a cat/sub to a record without arguing with the one it has — use",
        "# that instead of a verdict here, and name the source that attests it.",
        "",
    ]
    for ref, name, t in sorted(review, key=lambda r: r[1]):
        told = " ".join(f"{k}={v}" for k, v in sorted(t.items())
                        if k in CONTESTED_KEYS or k == "shop")
        lines.append(f"{ref}\t{name}\t{told}")
        lines.append(f"\thttps://www.openstreetmap.org/{ref}")
    out.write_text("\n".join(lines) + "\n")
