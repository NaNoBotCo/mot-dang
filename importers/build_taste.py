#!/usr/bin/env python3
"""รสเมือง — bake the cuisine terroir.

Every place carrying an OpenStreetMap cuisine tag becomes a colored dot:
1,900-odd of them, every token in the data — mined at full breadth, not a
curated shortlist. Tokens fold into six families plus "other" for the dot
colors; the token itself is kept on every dot, so nothing is flattened away.

The dot takes the FIRST cuisine token as its color (a shop tagged
"thai;japanese" paints thai) — stated on the page, not hidden. A place with
no cuisine tag is simply absent: absence is silence, never "no cuisine".

Also baked: per-token geography for every token with n>=12 — centroid,
huddle radius (median distance of its dots to their own centroid), median
distance from the moat centre, and the compass direction of its centroid
from the moat — the numbers behind "which cuisines huddle, which spread".

Deterministic: same canonical data in, byte-same JSON out.

    python3 importers/build_taste.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "taste.json"

# Mean of the four แจ่ง corners (MOAT_CORNER_IDS in build.py), computed from
# the canonical records 2026-08-03; recompute if the corner ways ever move.
MOAT_LAT, MOAT_LNG = 18.78841, 98.98603

# Fixed family order (by size), fixed hues — never cycled, never re-ranked.
# Palette note: CVD separation, normal-vision floor and contrast-vs-surface
# all PASS the dataviz validator on the dark surface. Its lightness-band and
# chroma-floor checks FAIL by design: these are luminous glow-dots on
# near-black cartography (the nitnoy lamp look), and "other" is meant to
# read muted. Identity is never color-alone — legend chips carry counts and
# every dot answers on hover.
FAMILIES = [
    ("thai", "#f6b73c", "ไทย-พื้นเมือง", "Thai & local"),
    ("cafe", "#ff9fc7", "กาแฟ-ของหวาน", "coffee & sweet"),
    ("western", "#e05252", "ตะวันตก", "western"),
    ("eastasia", "#6fa8ff", "เอเชียตะวันออก", "east asian"),
    ("grill", "#58c9a0", "ปิ้งย่าง-ทะเล", "grill & seafood"),
    ("mideast", "#b98bff", "อินเดีย-ตะวันออกกลาง", "Indian & Middle Eastern"),
    ("other", "#8f9bab", "อื่น ๆ", "everything else"),
]

FAMILY_OF = {}
for fam, toks in {
    "thai": ["thai", "regional", "local", "noodle", "noodles", "curry",
             "khao_soi", "northern_thai_food", "som_tam", "isan", "buffet"],
    "cafe": ["coffee_shop", "coffee", "tea", "cake", "ice_cream", "dessert",
             "bubble_tea", "juice", "pancake", "crepe", "donut", "bagel",
             "smoothie", "bakery", "breakfast", "sandwich", "waffle"],
    "western": ["pizza", "italian", "burger", "american", "steak_house",
                "steak", "pasta", "french", "german", "mexican",
                "fish_and_chips", "european", "spanish", "mediterranean",
                "tapas", "western", "italian_pizza", "fries", "fine_dining",
                "international", "salad"],
    "eastasia": ["japanese", "chinese", "korean", "sushi", "ramen",
                 "vietnamese", "burmese", "asian", "dim_sum", "dimsum",
                 "shabu", "shabu-shabu", "hot_pot", "udon", "izakaya"],
    "grill": ["seafood", "barbecue", "grill", "fish", "chicken"],
    "mideast": ["indian", "middle_eastern", "turkish", "kebab", "halal",
                "lebanese", "arab", "pakistani"],
}.items():
    for t in toks:
        FAMILY_OF[t] = fam

BEARINGS = ["เหนือ N", "ตอ.เฉียงเหนือ NE", "ตะวันออก E", "ตอ.เฉียงใต้ SE",
            "ใต้ S", "ตต.เฉียงใต้ SW", "ตะวันตก W", "ตต.เฉียงเหนือ NW"]


def dist_m(la1, ln1, la2, ln2):
    cosla = math.cos(math.radians((la1 + la2) / 2))
    return math.hypot((la1 - la2) * 111320, (ln1 - ln2) * 111320 * cosla)


def bearing_label(la, ln):
    x = (ln - MOAT_LNG) * math.cos(math.radians(MOAT_LAT))
    y = la - MOAT_LAT
    deg = (math.degrees(math.atan2(x, y)) + 360) % 360
    return BEARINGS[int((deg + 22.5) // 45) % 8]


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def main():
    recs = []
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / (prov + ".json")
        if p.exists():
            recs.extend(json.loads(p.read_text()))

    dots = []
    for r in sorted(recs, key=lambda r: r["id"]):
        cu = r["attrs"].get("cuisine")
        if not cu or r.get("lat") is None:
            continue
        tokens = [t.strip().lower().replace(" ", "_")
                  for t in str(cu).split(";") if t.strip()]
        if not tokens:
            continue
        t = tokens[0]
        dots.append({
            "id": r["id"],
            "n": r.get("nameTh") or r["name"],
            "la": round(r["lat"], 5),
            "ln": round(r["lng"], 5),
            "p": r["province"],
            "t": t,
            "f": FAMILY_OF.get(t, "other"),
        })

    # Geography is measured on Chiang Mai dots ONLY: a centroid computed
    # across two provinces 140 km apart is a point in a rice field between
    # them, and Chiang Rai's kitchen is still growing. CR dots are still
    # drawn on the map; they just don't vote in these numbers. (Same rule
    # as seven.html: frame the numbers where the finding lives.)
    by_token = {}
    for d in dots:
        if d["p"] == "cm":
            by_token.setdefault(d["t"], []).append(d)

    stats = []
    for tok in sorted(by_token):
        group = by_token[tok]
        if len(group) < 12:
            continue
        cla = sum(d["la"] for d in group) / len(group)
        cln = sum(d["ln"] for d in group) / len(group)
        huddle = median([dist_m(d["la"], d["ln"], cla, cln) for d in group])
        moat = median([dist_m(d["la"], d["ln"], MOAT_LAT, MOAT_LNG)
                       for d in group])
        stats.append({
            "t": tok, "n": len(group), "f": FAMILY_OF.get(tok, "other"),
            "huddle_m": round(huddle), "moat_m": round(moat),
            "dir": bearing_label(cla, cln),
        })
    stats.sort(key=lambda s: -s["n"])

    fam_counts = {}
    for d in dots:
        fam_counts[d["f"]] = fam_counts.get(d["f"], 0) + 1

    latest = max((r.get("updatedAt") or "" for r in recs
                  if r["attrs"].get("cuisine")), default="")
    out = {
        "generated": latest,
        "note": "dot color = FIRST cuisine token's family; every token kept "
                "on the dot; a place without a cuisine tag is absent, which "
                "is silence, never 'no cuisine'",
        "families": [{"key": k, "color": c, "th": th, "en": en,
                      "n": fam_counts.get(k, 0)}
                     for k, c, th, en in FAMILIES],
        "family_of": {t: f for t, f in sorted(FAMILY_OF.items())},
        "dots": dots,
        "stats": stats,
        "stats_scope": "cm",
        "moat_centre": [MOAT_LAT, MOAT_LNG],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False,
                              separators=(",", ":")) + "\n")
    print("taste: %d dots, %d tokens (%d with n>=12 in stats), families %s"
          % (len(dots), len(by_token), len(stats),
             {k: v for k, v in sorted(fam_counts.items(),
                                      key=lambda kv: -kv[1])}))


if __name__ == "__main__":
    main()
