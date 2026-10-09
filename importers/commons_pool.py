#!/usr/bin/env python3
"""Commons photographs of the north, chosen, tagged and fetched for the site.

Two inputs:
  * cache/commons_area/files.json — every geotagged file in both provinces,
    from importers/harvest_commons_area.py
  * ../commons-crawl/found.jsonl + data/curated/commons_found_keep.json — the
    topic crawl of 2026-09-30 and the rows of it judged worth showing, each
    with its tags written by hand (the crawl also returned the Western Wall,
    Portland khao soi and a Luge World Cup, which is why it needs a keep list)

Three outputs:
  * data/curated/commons_pool.json — picks in image_picks.json's shape (topic,
    season, place, mood, licence, artist, file) plus lat/lng, month, amphoe and
    the record ids a picture is OF. build.py adds them to SITE_ART, so every
    art() caller draws from them.
  * data/commons_images.json — merged: a place with no picture gains one where
    a file within 200 m carries the place's own name (harvest_commons.py's
    identifies()/names_agree(), unchanged). Existing rows are kept.
  * assets/site/<slug>.jpg (960 px) and assets/band/<slug>.jpg (520 px), with
    --download. Served from our own bucket like the rest of the pool.

    python3 importers/commons_pool.py              # choose + tag, write the JSON
    python3 importers/commons_pool.py --download   # ...and fetch what is missing
"""
import argparse
import hashlib
import io
import json
import math
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
sys.path.insert(0, str(ROOT))
import harvest_commons as hc  # noqa: E402

AREA = ROOT / "cache" / "commons_area" / "files.json"
EXTRA = ROOT / "cache" / "commons_area" / "extra.json"
CATS = ROOT / "cache" / "commons_area" / "cats.json"     # importers/harvest_commons_cats.py
FOUND = ROOT.parent / "commons-crawl" / "found.jsonl"
KEEP = ROOT / "data" / "curated" / "commons_found_keep.json"
PICKS = ROOT / "data" / "curated" / "image_picks.json"
OUT = ROOT / "data" / "curated" / "commons_pool.json"
CI = ROOT / "data" / "commons_images.json"
SITE = ROOT / "assets" / "site"
BAND = ROOT / "assets" / "band"
BOUNDS = ROOT / "data" / "admin_boundaries.json"
UA = hc.UA

OK_LIC = re.compile(r"^(cc0|pd|public domain|cc[- ]by(-sa)?[- ]\d)", re.I)
# Not photographs of anywhere: maps, logos, scans of paper, specimens on pins.
BAD = re.compile(r"\b(map|logo|flag|diagram|coat of arms|svg|screenshot|locator|chart|"
                 r"seal of|emblem|document|scan|MHNT|dorsal|ventral|specimen|herbarium|"
                 r"plan of|blueprint|signature|stamp|banknote|coin|poster|"
                 r"selfie|portrait of|headshot|exploitation|ISS\d{3}|view of earth|bottles?|shower gel|"
                 r"shampoo|receipt|ticket|pattaya|bangkok|phuket|krabi|samut ?prakan|museo)\b", re.I)
BAD_CAT = re.compile(r"(Maps of|Logos|Documents|Text|Signatures|Insects|Lepidoptera|"
                     r"Moths|Beetles|Specimens|Herbarium|Portrait|Selfies|People of Thailand by name|"
                     r"Military|Protests|Politicians|Accidents|Funerals|Deaths)", re.I)

# Keyword → (topics, moods). Read against title + description + categories, in
# English and Thai. First the specific, then the broad; a file collects every
# rule it matches.
RULES = [
    (r"yi ?peng|yee ?peng|loy ?krathong|loi ?krathong|lantern|khom ?loi|krathong|ยี่เป็ง|ลอยกระทง|โคม",
     ("festival", "night"), ("festive",)),
    (r"songkran|สงกรานต์|water festival", ("festival",), ("festive",)),
    (r"flower festival|parade|procession|festival|fair\b|ประเพณี|เทศกาล|งาน", ("festival",), ("festive",)),
    (r"\bwat\b|temple|chedi|stupa|ubosot|uposatha|viharn|vihara|wihan|ordination|monk|novice|"
     r"buddha|วัด|เจดีย์|พระธาตุ|วิหาร|อุโบสถ|พระพุทธ", ("wat",), ("sacred",)),
    (r"shrine|spirit house|san phra phum|pillar|inthakhin|ศาล|เสาอินทขิล", ("faith", "mu"), ("sacred",)),
    (r"mosque|church|cathedral|gurdwara|มัสยิด|โบสถ์คริสต์", ("faith",), ("sacred",)),
    (r"market|bazaar|walking street|kad |kat |\bkaad|ตลาด|กาด|ถนนคนเดิน", ("market",), ("streetlife",)),
    (r"night|evening|dusk|ยามค่ำ|กลางคืน", ("night",), ("neon",)),
    (r"khao ?soi|noodle|food|restaurant|cafe|café|coffee|dish|meal|kitchen|ข้าวซอย|อาหาร|ร้าน|กาแฟ",
     ("food",), ("appetite",)),
    (r"waterfall|\bfalls?\b|น้ำตก", ("nature", "waterfall"), ("green", "calm")),
    (r"\bdoi\b|mountain|peak|summit|viewpoint|view point|sea of (mist|fog|clouds)|ดอย|จุดชมวิว",
     ("nature", "view"), ("green", "landmark")),
    (r"national park|forest|jungle|tree|garden|park\b|rice|paddy|field|valley|lake|reservoir|dam\b|"
     r"river|stream|mekong|\bping\b|kok river|อุทยาน|ป่า|นา|แม่น้ำ|อ่างเก็บน้ำ|สวน",
     ("nature",), ("green",)),
    (r"hot spring|น้ำพุร้อน|cave|tham |ถ้ำ", ("nature",), ("calm",)),
    (r"sunrise|sunset|mist|fog|cloud|พระอาทิตย์", ("nature",), ("calm",)),
    (r"elephant|buffalo|bird|monkey|dog|cat\b|cattle|tiger|ช้าง|ควาย|นก", ("animals",), ("green",)),
    (r"akha|hmong|karen|kayan|lahu|lisu|mien|\byao\b|lawa|lua|hill ?tribe|ethnic|อาข่า|ม้ง|กะเหรี่ยง|ลาหู่|ลีซู|เมี่ยน",
     ("hill",), ("calm",)),
    (r"silk|weav|loom|textile|cloth|fabric|embroider|ผ้า|ทอ", ("textile",), ("calm",)),
    (r"umbrella|parasol|bo sang|lacquer|pottery|ceramic|celadon|woodcarv|silverware|craft|handicraft|ร่ม|เครื่องปั้น|หัตถกรรม",
     ("arts", "craft"), ("streetlife",)),
    (r"museum|gallery|mural|painting|sculpture|statue|art\b|arts\b|exhibit|พิพิธภัณฑ์|จิตรกรรม|ศิลปะ",
     ("arts",), ("landmark",)),
    (r"graffiti|street art|stencil|กราฟฟิตี", ("arts", "streetart"), ("streetlife",)),
    (r"ruin|ancient|historic|wiang|old city|city wall|moat|gate|ประตู|คูเมือง|กำแพง|โบราณ|เวียง",
     ("history", "city"), ("landmark",)),
    (r"street|road|soi|alley|lane|thanon|ถนน|ซอย|intersection|traffic|building|shophouse|clock tower|หอนาฬิกา",
     ("city",), ("streetlife",)),
    (r"songthaew|song ?thaew|red car|rot daeng|tuk|bus\b|bus station|train|railway|station|airport|"
     r"motorbike|motorcycle|bicycle|รถแดง|สถานี|สนามบิน", ("transport",), ("streetlife",)),
    (r"bridge|สะพาน", ("city",), ("landmark",)),
    (r"hotel|resort|guesthouse|homestay|โรงแรม|รีสอร์ท", ("stay",), ("calm",)),
    (r"university|school|college|มหาวิทยาลัย|โรงเรียน", ("city",), ("calm",)),
    (r"muay|boxing|stadium|football|golf|run\b|marathon|มวย|สนามกีฬา", ("sport",), ("festive",)),
    (r"border|golden triangle|sop ruak|mae sai|chiang saen|chiang khong|สามเหลี่ยมทองคำ|แม่สาย|เชียงแสน",
     ("border",), ("landmark",)),
    (r"amulet|พระเครื่อง", ("mu", "amulets"), ("sacred",)),
    (r"tea|coffee plantation|ชา\b|ไร่ชา", ("nature", "food"), ("green",)),
    (r"wires|cables|power lines|utility pole", ("city", "wires"), ("streetlife",)),
]
RULES = [(re.compile(p, re.I), t, m) for p, t, m in RULES]

# Province-level clues where coordinates are missing (the topic crawl).
CM_WORDS = re.compile(r"chiang ?mai|เชียงใหม่|doi suthep|nimman|tha ?phae|mae rim|san kamphaeng|hang dong|"
                      r"mae taeng|chiang dao|inthanon|mae chaem|fang\b|sanpatong|san pa tong", re.I)
CR_WORDS = re.compile(r"chiang ?rai|เชียงราย|mae sai|chiang saen|sop ruak|golden triangle|mae salong|"
                      r"doi tung|chiang khong|phu chi fa|wat rong khun|baan dam|black house", re.I)


def season_of(month):
    if month in (3, 4, 5):
        return "hot"
    if month in (6, 7, 8, 9, 10):
        return "rains"
    if month in (11, 12, 1, 2):
        return "cool"
    return None


def month_of(date):
    m = re.search(r"(\d{4})[-:/](\d{1,2})[-:/](\d{1,2})", date or "")
    if not m:
        return None, None
    y, mo = int(m.group(1)), int(m.group(2))
    if not (1990 <= y <= 2030 and 1 <= mo <= 12):
        return None, None
    return y, mo


def ascii_slug(title, n=46):
    t = re.sub(r"^File:|\.\w+$", "", title)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:n].strip("-")
    h = hashlib.sha1(title.encode()).hexdigest()[:6]
    return ("c-" + t + "-" + h) if t else ("c-" + h)


# ---------------------------------------------------------------- geography

def _pip(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


class Amphoe:
    def __init__(self):
        feats = json.loads(BOUNDS.read_text())["levels"]["amphoe"]["features"]
        self.polys = []
        for f in feats:
            g = f["geometry"]
            rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
            for ring in rings:
                xs = [p[0] for p in ring]
                ys = [p[1] for p in ring]
                self.polys.append((min(xs), min(ys), max(xs), max(ys), ring, f["properties"]))

    def at(self, lat, lng):
        for x0, y0, x1, y1, ring, pr in self.polys:
            if x0 <= lng <= x1 and y0 <= lat <= y1 and _pip(lng, lat, ring):
                return pr
        return None


def hav(a1, o1, a2, o2):
    return hc.haversine(a1, o1, a2, o2)


# ---------------------------------------------------------------- metadata

def api(params):
    params = dict(params, format="json", formatversion="2")
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                        timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            print("  retry", i, e, file=sys.stderr)
            time.sleep(3 * (i + 1))
    return {}


def strip(h):
    return hc.strip(h or "")


def fetch_meta(titles):
    """Metadata for files the area sweep did not return (the topic crawl)."""
    have = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
    todo = [t for t in titles if t not in have]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        d = api({"action": "query", "titles": "|".join(batch),
                 "prop": "imageinfo|categories|coordinates", "iiprop": "url|size|mime|extmetadata",
                 "iiurlwidth": 960, "cllimit": "max", "clshow": "!hidden",
                 "iiextmetadatafilter": "LicenseShortName|Artist|ImageDescription|DateTimeOriginal|ObjectName"})
        time.sleep(0.4)
        for pg in d.get("query", {}).get("pages", []):
            ii = (pg.get("imageinfo") or [None])[0]
            if not ii:
                continue
            md = ii.get("extmetadata", {})
            co = (pg.get("coordinates") or [{}])[0]
            have[pg["title"]] = {
                "lat": co.get("lat"), "lng": co.get("lon"),
                "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
                "url": ii.get("url"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
                "licence": strip(md.get("LicenseShortName", {}).get("value")),
                "artist": strip(md.get("Artist", {}).get("value"))[:120],
                "desc": strip(md.get("ImageDescription", {}).get("value"))[:600],
                "name": strip(md.get("ObjectName", {}).get("value"))[:200],
                "date": strip(md.get("DateTimeOriginal", {}).get("value"))[:40],
                "cats": [c["title"][9:] for c in pg.get("categories", [])],
            }
        EXTRA.write_text(json.dumps(have, ensure_ascii=False))
    return have


# ---------------------------------------------------------------- tagging

def tags_of(title, m):
    hay = " ".join([re.sub(r"^File:|\.\w+$", "", title).replace("_", " "), m.get("desc") or "",
                    m.get("name") or "", " ".join(m.get("cats") or [])])
    topics, moods = [], []
    for rx, t, mo in RULES:
        if rx.search(hay):
            topics += [x for x in t if x not in topics]
            moods += [x for x in mo if x not in moods]
    return topics, moods, hay


def score_of(m, title):
    cats = " ".join(m.get("cats") or [])
    s = min((m.get("w") or 0) * (m.get("h") or 0) / 4e6, 3)
    if "Featured pictures" in cats:
        s += 6
    if "Quality images" in cats:
        s += 3
    if "Valued images" in cats:
        s += 2
    if "Pictures of the day" in cats or "Media of the day" in cats:
        s += 4
    if len(m.get("desc") or "") > 20:
        s += 0.7
    if "panoramio" in title.lower():
        s -= 0.6          # small, old phone frames, often of nothing in particular
    if re.search(r"\b(IMG|DSC|DSCF|P\d{6,}|\d{8}_\d{6})", title) and len(m.get("desc") or "") < 12:
        s -= 1.2
    w, h = m.get("w") or 1, m.get("h") or 1
    if w < h:
        s -= 0.8          # bands and cards are wide
    return round(s, 2)


def describe(title, m):
    for c in (m.get("desc"), m.get("name"), re.sub(r"^File:|\.\w+$", "", title).replace("_", " ")):
        c = (c or "").strip()
        if len(c) > 3 and not re.fullmatch(r"(?i)(photo i took.*|chiang mai photo|thailand \d+)", c):
            return re.sub(r"\s+", " ", c)[:300]
    return ""


# ---------------------------------------------------------------- records

# harvest_commons.identifies() matched "October" (a café) to a cheesecake and a
# parking lot to the district's photo. Here a file is OF a place only when it
# carries the place's whole name, or every distinctive word of it, or the Thai
# name, or (names_agree) a long Latin reading of it.
STOP = hc.GENERIC | {"the", "and", "cafe", "coffee", "house", "home", "hostel", "hotel", "resort",
                     "restaurant", "shop", "store", "park", "school", "office", "post", "center",
                     "centre", "station", "garden", "bar", "guesthouse", "village", "bridge", "tree",
                     "sanctuary", "elephant", "river", "phra", "doi", "baan", "ban", "national",
                     "khun", "mae", "san", "nong", "huai", "chiangrai", "chiangmai"}
NOT_PICTURED = re.compile(r"^(parking|car park|motorcycle parking|ที่จอด|ลานจอด)", re.I)


def is_of(names, cats, title, desc):
    if "transport" in cats and not set(cats) - {"transport"}:
        return None
    hay = (re.sub(r"^File:|\.\w+$", "", title).replace("_", " ") + " " + (desc or "")).lower()
    for nm in names:
        if NOT_PICTURED.match(nm or ""):
            return None
    for nm in names:
        n = re.sub(r"\s+", " ", (nm or "").lower()).strip()
        if len(n) >= 8 and n in hay:
            return "name"
        if re.search(r"[\u0e00-\u0e7f]", n) and len(n) >= 6 and n.replace(" ", "") in hay.replace(" ", ""):
            return "thai name"
    toks = set()
    for nm in names:
        t = {x for x in hc.name_tokens(nm) if x not in STOP and not x.isdigit()}
        kinds = set(re.findall(r"school|hotel|hostel|resort|cafe|restaurant|hospital|clinic|market|condo",
                               (nm or "").lower()))
        if len(t) >= 2 and t <= hc.name_tokens(hay) and all(k in hay for k in kinds):
            return ",".join(sorted(t))
        toks |= t
    why = hc.names_agree(names, title, desc)
    if why and len(why.split()[-1]) >= 8:
        return why
    return None

def load_records():
    recs = []
    for p in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text()):
            if r.get("lat") is None:
                continue
            names = [n for n in (r.get("name"), r.get("nameEn"), r.get("nameTh")) if n]
            if names:
                recs.append((r["id"], r["lat"], r["lng"], names, r.get("cat") or []))
    grid = defaultdict(list)
    for rec in recs:
        grid[(int(rec[1] / 0.003), int(rec[2] / 0.003))].append(rec)
    return grid


def near_records(grid, lat, lng, metres):
    k = (int(lat / 0.003), int(lng / 0.003))
    out = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for rec in grid.get((k[0] + dy, k[1] + dx), []):
                d = hav(lat, lng, rec[1], rec[2])
                if d <= metres:
                    out.append((d, rec))
    return sorted(out, key=lambda x: x[0])


# ---------------------------------------------------------------- choose

def build(args):
    area = json.loads(AREA.read_text()) if AREA.exists() else {}
    keep = json.loads(KEEP.read_text())["keep"]
    found = {}
    for line in FOUND.read_text().splitlines():
        r = json.loads(line)
        found[r["title"]] = r
    extra = fetch_meta([t for t in keep if t not in area])
    picked_titles = {p["title"] for p in json.loads(PICKS.read_text())["picks"]}
    amph = Amphoe()
    grid = load_records()

    cands = {}
    # 1. The topic crawl, as judged.
    for title, k in keep.items():
        m = area.get(title) or extra.get(title)
        if not m or title in picked_titles:
            continue
        cands[title] = dict(m, _hand=k)
    # 2. The sweep, then the categories (each file carrying its category's tags).
    dropped = Counter()
    cats = json.loads(CATS.read_text()) if CATS.exists() else {}
    for title, m in list(area.items()) + [(t, v) for t, v in cats.items() if t not in area]:
        if title in cands or title in picked_titles:
            continue
        if m.get("mime") != "image/jpeg":
            dropped["not jpeg"] += 1
            continue
        if not OK_LIC.match(m.get("licence") or ""):
            dropped["licence"] += 1
            continue
        if (m.get("w") or 0) < 1000 or (m.get("h") or 0) < 600:
            dropped["small"] += 1
            continue
        if BAD.search(title) or BAD.search(m.get("desc") or "") or any(BAD_CAT.search(c) for c in m.get("cats") or []):
            dropped["not a view"] += 1
            continue
        cands[title] = dict(m)
        if (cats.get(title) or {}).get("tags"):
            cands[title]["_cat"] = cats[title]["tags"]

    picks, idents = [], {}
    for title, m in cands.items():
        topics, moods, hay = tags_of(title, m)
        hand = m.get("_hand") or m.get("_cat")
        lat, lng = m.get("lat"), m.get("lng")
        pr = amph.at(lat, lng) if lat is not None else None
        if m.get("_cat") and BAD.search(title + " " + (m.get("desc") or "")):
            continue
        if pr:
            place = [pr["province"]]
        elif m.get("_cat") and lat is not None and hand["place"] in ("cm", "cr"):
            continue          # a "Chiang Mai" category file standing somewhere else
        elif hand:
            place = [hand["place"]]
        elif lat is not None:
            continue          # outside both provinces (Laos, Myanmar, Phayao, Lamphun)
        else:
            place = ["cm"] if CM_WORDS.search(hay) else ["cr"] if CR_WORDS.search(hay) else ["elsewhere"]
        if hand:
            # Hand tags stand as written; the rules only add a night shot.
            topics = list(dict.fromkeys(hand["topic"] + [t for t in topics if t == "night"]))
            moods = list(hand["mood"])
        if not topics:
            topics = ["city"] if pr and pr["nameEn"].startswith("Mueang") else ["nature"]
            moods = moods or (["streetlife"] if topics == ["city"] else ["green"])
        if not hand and re.search(r"\b(people|portrait|woman|women|girls?|boys?|child|children|family|crowd|"
                                  r"students?|dancers?|vendors?)\b", hay, re.I) and "people" not in topics:
            topics.append("people")
        y, mo = month_of(m.get("date"))
        season = list(hand.get("season") or []) if hand else []
        if not season:
            if re.search(r"songkran|สงกรานต์", hay, re.I):
                season = ["hot"]
            elif re.search(r"yi ?peng|loy ?krathong|loi ?krathong|ยี่เป็ง|ลอยกระทง|flower festival", hay, re.I):
                season = ["cool"]
            elif mo and not set(topics) & {"food", "arts", "mu", "amulets", "textile"}:
                season = [season_of(mo)]
        p = {
            "title": title,
            "slug": ascii_slug(title),
            "page": m.get("page") or ("https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))),
            "src": m.get("thumb") or m.get("url"),
            "width": m.get("w"), "height": m.get("h"),
            "licence": m.get("licence"),
            "artist": (m.get("artist") or "unknown").strip(),
            "credit": "Wikimedia Commons",
            "description": describe(title, m),
            "date": ("%04d-%02d" % (y, mo)) if y else "",
            "month": mo,
            "topic": topics, "season": [s for s in season if s], "place": place, "mood": moods[:3] or ["calm"],
            "usable": True,
            "file": "",
            "score": score_of(m, title) + (4 if m.get("_hand") else 2 if m.get("_cat") else 0),
            "_cat": (m.get("_cat") or {}).get("cat"),
            "source": "commons-pool",
        }
        if lat is not None:
            p["lat"], p["lng"] = round(lat, 6), round(lng, 6)
        if pr:
            p["amphoe"] = pr["name"]
            p["amphoeEn"] = pr["nameEn"]
        # What it is OF: a listed place within 200 m whose own name the file carries.
        if lat is not None:
            ofs = []
            for d, rec in near_records(grid, lat, lng, 200):
                why = is_of(rec[3], rec[4], title, p["description"])
                if why:
                    ofs.append((d, rec[0], why))
            if 1 <= len(ofs) <= 2:
                p["places"] = [x[1] for x in ofs]
                p["placeId"] = ofs[0][1]
                for d, pid, why in ofs:
                    idents.setdefault(pid, []).append((p["score"] - d / 200, p, round(d), why))
        picks.append(p)

    # ------------------------------------------------ selection
    by_slug = {p["slug"]: p for p in picks}
    chosen = set()
    # a) the hand-kept rows, and the best of each category
    for p in picks:
        if title_hand(p, cands):
            chosen.add(p["slug"])
    by_cat = defaultdict(list)
    for p in picks:
        if p.get("_cat"):
            by_cat[p["_cat"]].append(p)
    for c, rows in by_cat.items():
        for p in sorted(rows, key=lambda p: -p["score"])[:14]:
            if p["score"] >= 0.5:
                chosen.add(p["slug"])
    # b) up to three pictures OF each listed place
    for pid, rows in idents.items():
        for sc, p, d, why in sorted(rows, key=lambda x: -x[0])[:3]:
            chosen.add(p["slug"])
    # c) burst control, then spatial coverage: the best frame in each cell.
    #    ~550 m cells in the two city centres, ~2.2 km elsewhere.
    def cell(p):
        city = (18.74 < p["lat"] < 18.83 and 98.94 < p["lng"] < 99.04) or \
               (19.88 < p["lat"] < 19.94 and 99.80 < p["lng"] < 99.87)
        s = 0.005 if city else 0.02
        return (round(p["lat"] / s), round(p["lng"] / s), city)
    cells = defaultdict(list)
    for p in picks:
        if p.get("lat") is not None and "people" not in p["topic"]:
            cells[cell(p)].append(p)
    for k, rows in cells.items():
        rows.sort(key=lambda p: -p["score"])
        n = 2 if k[2] else 1
        took, seen_art = 0, set()
        for p in rows:
            if took >= n:
                break
            if p["score"] < 0.6:
                break
            if p["artist"] in seen_art:      # two frames by one hand at one spot is one picture
                continue
            seen_art.add(p["artist"])
            chosen.add(p["slug"])
            took += 1
    # d) every topic × province × season gets depth: the top few of each.
    combos = defaultdict(list)
    for p in picks:
        for t in p["topic"]:
            for pl in p["place"]:
                for s in (p["season"] or ["-"]):
                    combos[(t, pl, s)].append(p)
    for k, rows in combos.items():
        for p in sorted(rows, key=lambda p: -p["score"])[:6]:
            if p["score"] >= 1.0 and "people" not in p["topic"]:
                chosen.add(p["slug"])
    # e) quality anywhere
    for p in picks:
        if p["score"] >= 6:
            chosen.add(p["slug"])

    pool = sorted((by_slug[s] for s in chosen), key=lambda p: p["slug"])
    if args.cap and len(pool) > args.cap:
        pool = sorted(pool, key=lambda p: -p["score"])[:args.cap]
        pool.sort(key=lambda p: p["slug"])
    keep_slugs = {p["slug"] for p in pool}
    for p in pool:
        p["file"] = "site/%s.jpg" % p["slug"]
        p.pop("score", None)
        if p.get("_cat"):
            p["category"] = p["_cat"]
        p.pop("_cat", None)

    print("candidates %d · dropped %s" % (len(cands), dict(dropped)))
    print("pool %d · with a place %d · places pictured %d" % (
        len(pool), sum(1 for p in pool if p.get("places")),
        len({pid for p in pool for pid in p.get("places", [])})))
    print("topics", Counter(t for p in pool for t in p["topic"]).most_common(30))
    print("place", Counter(t for p in pool for t in p["place"]).most_common())
    print("season", Counter(t for p in pool for t in p["season"]).most_common())
    OUT.write_text(json.dumps({
        "_note": "Commons photographs of Chiang Mai and Chiang Rai, chosen and tagged by "
                 "importers/commons_pool.py from the area sweep and the 2026-09-30 topic crawl. "
                 "Each carries its photographer and licence; /pictures.html lists them all.",
        "generated": time.strftime("%Y-%m-%d"),
        "picks": pool}, ensure_ascii=False, indent=1))

    # place photos: merge into commons_images.json for places with none there yet
    ci = json.loads(CI.read_text()) if CI.exists() else {"images": {}}
    imgs = ci.setdefault("images", {})
    added = 0
    for pid, rows in idents.items():
        if pid in imgs:
            continue
        rows = [r for r in sorted(rows, key=lambda x: -x[0]) if r[1]["slug"] in keep_slugs]
        if not rows:
            continue
        sc, p, d, why = rows[0]
        imgs[pid] = {"placeId": pid, "title": p["title"], "file": p["file"], "thumb": p["src"],
                     "full": p["page"], "licence": p["licence"], "artist": p["artist"],
                     "credit": "", "description": p["description"], "distance_m": d,
                     "matched_on": why, "via": "commons_pool"}
        added += 1
    ci["count"] = len(imgs)
    ci["generated_pool"] = time.strftime("%Y-%m-%d")
    CI.write_text(json.dumps(ci, ensure_ascii=False, indent=1))
    print("commons_images.json: +%d places (now %d)" % (added, len(imgs)))
    return pool


def title_hand(p, cands):
    return bool((cands.get(p["title"]) or {}).get("_hand"))


# ---------------------------------------------------------------- download

def download(pool):
    from concurrent.futures import ThreadPoolExecutor
    from PIL import Image
    SITE.mkdir(parents=True, exist_ok=True)
    BAND.mkdir(parents=True, exist_ok=True)

    def one(p):
        out, band = SITE / (p["slug"] + ".jpg"), BAND / (p["slug"] + ".jpg")
        if out.exists() and band.exists():
            return "have"
        if not p.get("src"):
            return "failed"
        for i in range(3):
            try:
                req = urllib.request.Request(p["src"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read()
                im = Image.open(io.BytesIO(raw)).convert("RGB")
                im.thumbnail((720, 720 * 3))
                im.save(out, "JPEG", quality=70, optimize=True, progressive=True)
                b = im.copy()
                b.thumbnail((400, 400 * 3))
                b.save(band, "JPEG", quality=72, optimize=True, progressive=True)
                return "fetched"
            except Exception as e:  # noqa: BLE001
                err = e
                time.sleep(3 * (i + 1))
        print("  x", p["slug"], err, file=sys.stderr)
        return "failed"

    tally = Counter()
    with ThreadPoolExecutor(4) as ex:      # four at a time: polite, and four times faster
        for i, res in enumerate(ex.map(one, pool)):
            tally[res] += 1
            if i % 100 == 0:
                print(f"  {i}/{len(pool)} · {dict(tally)}", flush=True)
    print("download:", dict(tally))
    # A pick whose file never arrived is not usable; build.py skips it.
    for p in pool:
        if not (SITE / (p["slug"] + ".jpg")).exists():
            p["usable"] = False
    d = json.loads(OUT.read_text())
    d["picks"] = pool
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--cap", type=int, default=3200)
    a = ap.parse_args()
    pool = build(a)
    if a.download:
        download(pool)


if __name__ == "__main__":
    main()
