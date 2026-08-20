#!/usr/bin/env python3
"""Fold cache/overpass/*.json (the gentle crawl's snapshot) into Mot Dang records.

Called by import_all.py. Classification: OSM tags -> (category, subcategory).
Unnamed elements are skipped — no shelf for the nameless. Subcategory lands in
record["sub"]; build.py matches children by key against that list.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
    "tailor": ("shopping", "tailor"), "shoemaker": ("shopping", "tailor"),
    "dressmaker": ("shopping", "tailor"), "leather": ("shopping", "tailor"),
    "bakery": ("food", "bakery-dessert"), "confectionery": ("food", "bakery-dessert"),
    "coffee_roaster": ("food", "cafe"), "caterer": ("food", "thai"),
    "electronics_repair": ("repair", "tech"), "computer_repair": ("repair", "tech"),
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
    ("driving", r"สอนขับรถ|โรงเรียนขับรถ|driving school"),
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


def school_sub(t, name):
    """Which kind of school this is, or None if it is not one.

    Read in this order: the school's own word for itself first, because a
    Thai school name says what it is more reliably than an OSM tag chosen by
    whoever mapped it; the tag second; the plain fallback last.
    """
    n = " ".join(v for v in (name, t.get("name:th"), t.get("name:en"),
                             t.get("alt_name")) if v)
    a = t.get("amenity")
    # International first and above everything: it is the one distinction a
    # reader is most often searching for, and a school that calls itself
    # นานาชาติ is telling us on purpose.
    if INTL_NAME.search(n):
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
    if s in ("laundry", "dry_cleaning"):
        return "essentials", "laundry"
    if s == "garden_centre":
        return "home-services", "landscaper"
    if s in ("wholesale", "trade"):
        return "business", "wholesale"
    if t.get("office") == "coworking" or a == "coworking_space":
        return "business", "coworking"
    if t.get("office") in ("lawyer", "accountant", "tax_advisor", "notary"):
        return "business", "professional"
    if t.get("office") in ("ngo", "charity") or a == "social_facility":
        return "community", "volunteer"
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
            return "learn", "gym"
        return None
    if t.get("office") == "estate_agent":
        return "realestate", "agent"
    if t.get("building") == "apartments":
        return "realestate", "condo"
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
    if (a == "bus_station" or t.get("railway") in ("station", "halt")
            or t.get("public_transport") == "station"):
        return "transport", "station"
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
        return "learn", "gym"
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
    if s == "pottery":
        return "crafts", "celadon"
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
    if "historic" in t:
        return "sights", "historic"
    if s in ("doityourself", "hardware"):
        return "shopping", "diy"
    if s == "gift":
        return "shopping", "crafts"
    if s == "second_hand":
        return "shopping", "secondhand"
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
}


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
    cache = ROOT / "cache" / "overpass" / province
    if not cache.exists():
        return out
    for f in sorted(cache.glob("*.json")):
        data = json.loads(f.read_text())
        for el in data.get("elements", []):
            t = el.get("tags", {})
            name = t.get("name") or t.get("name:th") or t.get("name:en")
            if not name:
                continue
            if is_gone(t):
                continue
            ref = f"{el['type']}/{el['id']}"
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
                if not ele_sub and not view_sub:
                    ele_review.append((ref, name, dict(t)))
                    continue
                # WO-21 rides the same fence: a name that declares a waterfall
                # or a viewpoint files onto sights, and everything else still
                # goes to the review file, which stays the menu for whatever
                # attractions order comes next. classify() remains unreachable
                # from this file either way.
                hit = ("chang", ele_sub) if ele_sub else ("sights", view_sub)
                fetched_0820.add(f"{province}-osm-{el['type']}-{el['id']}")
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
            out.append({
                "id": f"{province}-osm-{el['type']}-{el['id']}", "province": province,
                "cat": cats, "sub": [sub] if sub else [],
                "name": name, "nameTh": t.get("name:th"), "nameEn": t.get("name:en"),
                "lat": lat, "lng": lng, "geoPrecision": "exact",
                "address": addr_line,
                "phone": phone,
                "website": website,
                "hours": t.get("opening_hours"),
                "attrs": {k: v for k, v in {
                    **addr_parts,
                    **features_of(t),
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
                    "brand": t.get("brand"), "cuisine": t.get("cuisine"),
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
    _write_cannabis_review(province, review)
    _write_elephant_review(province, ele_review)
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
