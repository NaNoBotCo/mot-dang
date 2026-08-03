#!/usr/bin/env python3
"""Fold cache/overpass/*.json (the gentle crawl's snapshot) into Mot Dang records.

Called by import_all.py. Classification: OSM tags -> (category, subcategory).
Unnamed elements are skipped — no shelf for the nameless. Subcategory lands in
record["sub"]; build.py matches children by key against that list.
"""
import json
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
    if a == "school":
        return "school-intl", None
    if a == "university":
        return "learn", "university"
    if a == "language_school":
        return "learn", "language"
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


def records(province="cm"):
    out = []
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
            hit = classify(t)
            if not hit:
                continue
            cat, sub = hit
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
                "cat": [cat], "sub": [sub] if sub else [],
                "name": name, "nameTh": t.get("name:th"), "nameEn": t.get("name:en"),
                "lat": lat, "lng": lng, "geoPrecision": "exact",
                "address": addr_line,
                "phone": phone,
                "website": website,
                "hours": t.get("opening_hours"),
                "attrs": {k: v for k, v in {
                    **addr_parts,
                    "brand": t.get("brand"), "cuisine": t.get("cuisine"),
                    "operator": t.get("operator"), "lineId": line,
                    "email": t.get("email") or t.get("contact:email"),
                    "whatsapp": t.get("contact:whatsapp"),
                    "facebook": t.get("contact:facebook") or t.get("facebook"),
                    "instagram": t.get("contact:instagram") or t.get("instagram"),
                    "brandWebsite": (t.get("brand:website") if not website else None),
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
    return out
