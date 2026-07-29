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
    if cuisines & {"vegetarian", "vegan"}:
        return "vegetarian"
    if cuisines & {"seafood", "fish"}:
        return "seafood"
    if cuisines & {"noodle", "noodles", "ramen"}:
        return "noodle"
    if cuisines & FOOD_INTL:
        return "international"
    return "thai"


def classify(t):
    """tags -> (cat, sub or None), or None to skip."""
    s, a, tr = t.get("shop"), t.get("amenity"), t.get("tourism")
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
    if a == "bus_station" or t.get("railway") == "station":
        return "transport", "station"
    if s in ("car_repair", "motorcycle_repair"):
        return "repair", "auto"
    if s in ("computer", "mobile_phone"):
        return "repair", "tech"
    if s == "hairdresser":
        return "beauty", "hair"
    if s == "beauty":
        return "beauty", "nails" if t.get("beauty") == "nails" else None
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
            out.append({
                "id": f"{province}-osm-{el['type']}-{el['id']}", "province": province,
                "cat": [cat], "sub": [sub] if sub else [],
                "name": name, "nameTh": t.get("name:th"), "nameEn": t.get("name:en"),
                "lat": lat, "lng": lng, "geoPrecision": "exact",
                "address": None,
                "phone": phone,
                "website": website,
                "hours": t.get("opening_hours"),
                "attrs": {k: v for k, v in {
                    "brand": t.get("brand"), "cuisine": t.get("cuisine"),
                    "operator": t.get("operator"), "lineId": line,
                    "email": t.get("email") or t.get("contact:email"),
                    "whatsapp": t.get("contact:whatsapp"),
                    "facebook": t.get("contact:facebook") or t.get("facebook"),
                    "instagram": t.get("contact:instagram") or t.get("instagram"),
                    "brandWebsite": (t.get("brand:website") if not website else None),
                }.items() if v},
                "featured": False, "landmark": False,
                "sources": [{"type": "osm", "ref": f"{el['type']}/{el['id']}",
                             "fetched": "2026-07-27", "via": "mot-dang overpass"}],
                "confidence": "crawled", "updatedAt": "2026-07-27",
            })
    return out
