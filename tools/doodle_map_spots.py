#!/usr/bin/env python3
"""The spots on the doodle map (docs/sites/doodle-map/), picked from the canonical record.

Nan, 2026-10-03: "I want an interactive doodle map of the city", after Nancy Chandler's
Map of Chiang Mai; then "big markets very important", "make distinctive landmarks look
like themselves", "each city gate looks different", "some wats are quite unique",
"please also highlight parks", "quality more important than quantity", and names and
descriptions in the chosen language only.

So: LOOKS pins the landmarks that get their own drawing and always appear; the rest are
a short, ranked pick per kind. A spot needs its name in both Thai and English, and its
note is built only from fields that can be said in both.

    python3 tools/doodle_map_spots.py          writes docs/sites/doodle-map/data/spots.json
    python3 tools/doodle_map_spots.py --dry    counts per kind, writes nothing
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DRY = "--dry" in sys.argv
import build  # noqa: E402  (slug functions; build.py runs nothing on import)

OUT = ROOT / "docs" / "sites" / "doodle-map" / "data" / "spots.json"
CURATED = ROOT / "data" / "curated" / "doodle_points.json"     # trees and public art, each with its source
SHEET = (18.735, 18.835, 98.925, 99.035)
INSETS = {
    "suthep": (18.79, 18.83, 98.87, 98.93),
    "bosang": (18.74, 18.80, 99.05, 99.12),
    "tawai":  (18.64, 18.69, 98.96, 99.00),
    "kham":   (18.75, 18.77, 98.91, 98.93),
    "kumkam": (18.74, 18.76, 98.99, 99.01),
}
CAPS = {"wat": 22, "market": 10, "eat": 22, "craft": 10, "see": 16, "green": 12, "well": 5, "go": 10, "spirit": 10}

# look key, kind, English-name pattern. The first record matching (curated ids first) is pinned.
LOOKS = [
    ("tha-phae-gate", "go", r"^(tha ?phae|thapae) gate$"),
    ("chang-phueak-gate", "go", r"^chang phueak gate$"),
    ("suan-dok-gate", "go", r"^suan dok gate$"),
    ("suan-prung-gate", "go", r"^suan prung gate$"),
    ("chiang-mai-gate", "go", r"^chiang mai gate$"),
    ("saen-pung-gate", "go", r"^saen pung gate$"),
    ("chang-moi-gate", "go", r"^chang moi gate$"),
    ("iron-bridge", "go", r"iron bridge"),
    ("nawarat-bridge", "go", r"^nawarat bridge$"),
    ("chedi-luang", "wat", r"^wat chedi luang"),
    ("phra-singh", "wat", r"^wat phra singh"),
    ("chiang-man", "wat", r"^wat chiang man"),
    ("sri-suphan", "wat", r"^wat sri ?suphan$|^wat srisuphan$"),
    ("phan-tao", "wat", r"^wat phan tao"),
    ("umong", "wat", r"^wat umong(?! maha)", "วัดอุโมงค์"),
    ("chet-yot", "wat", r"^wat (chet yot|jed yod|jet yod)", "วัดเจ็ดยอด"),
    ("suan-dok", "wat", r"^wat suan dok", "วัดสวนดอก"),
    ("lok-molee", "wat", r"^wat lok mo"),
    ("doi-suthep", "wat", r"^wat phra that doi suthep"),
    ("doi-kham", "wat", r"^wat phra that doi kham"),
    ("pha-lat", "wat", r"^wat pha lat"),
    ("warorot", "market", r"^warorot market$"),
    ("night-bazaar", "market", r"^(chiang mai )?night bazaar$", "ไนท์บาซาร์"),
    ("sunday-walk", "market", r"sunday (market|walking)", "ถนนคนเดินวันอาทิตย์"),
    ("ton-lamyai", "market", r"^ton lam ?yai market$", "ตลาดต้นลำไย"),
    ("chang-phueak-market", "market", r"^kad chang phueak$|^chang phueak market$"),
    ("jing-jai", "market", r"^jing ?jai market$", "จริงใจมาร์เก็ต"),
    ("chiang-mai-gate-market", "market", r"^chiang mai gate market$"),
    ("anusarn", "market", r"^anusarn market$"),
    ("three-kings", "see", r"^three kings monument$"),
    ("wiang-kum-kam", "see", r"^wiang kum kam$"),
    ("buak-hat", "green", r"^(nong )?buak ha(a)?d park$|^buak hat park$"),
]


CHAINS = re.compile(r"yoshinoya|ootoya|\bmk\b|fuji|sukishi|bar ?b ?q plaza|swensen|kfc|mcdonald|starbucks|amazon|s ?& ?p\b|black canyon|pizza company|sizzler|burger king|dairy queen|after you|shabushi|moo kata|buffet|7-eleven|tesco|lotus|big c|makro|central|maya", re.I)
DROP = re.compile(r"^(chiang mai airport|the ping|doi suthep)$", re.I)


def where(la, ln):
    if la is None:
        return None
    if SHEET[0] < la < SHEET[1] and SHEET[2] < ln < SHEET[3]:
        return "sheet"
    for k, b in INSETS.items():
        if b[0] < la < b[1] and b[2] < ln < b[3]:
            return k
    return None


def kind_of(r):
    cats, sub = set(r["cat"]), set(r.get("sub") or [])
    if cats & {"realestate", "hotel", "tattoo", "cannabis", "repair", "business", "transport"}:
        return None
    if sub & {"shrine", "spirit-house"}:
        return "spirit"
    if (r.get("nameEn") or "").lower().endswith(" gate"):
        return "go"
    if "wat" in cats:
        return "wat"
    if "market" in cats or "walking-street" in sub or "flea" in sub:
        return "market"
    if "massage" in cats:
        return "well"
    if "parks" in cats or sub & {"nature", "waterfall", "viewpoint"}:
        return "green"
    if sub & {"bridge", "corner"} or re.search(r"station|terminal", r.get("nameEn") or "", re.I):
        return "go"
    if "museums-galleries" in cats or "sights" in cats:
        return "see"
    if "shopping" in cats and sub & {"crafts", "fabric"}:
        return "craft"
    if "food" in cats and not cats & {"shopping", "sights"}:
        return "eat"
    return None


def notes(r, cl):
    """Lines from the record's own fields, only those that can be said in both languages."""
    a = r.get("attrs") or {}
    en, th = [], []
    if a.get("foundedCE"):
        en.append(f"founded {a['foundedCE']}"); th.append(f"สร้าง พ.ศ. {a.get('foundedBE') or a['foundedCE'] + 543}")
    if a.get("riverside"):
        en.append("on the Ping"); th.append("ริมแม่น้ำปิง")
    if cl:
        en.append(f"Citylife wrote it up, {cl['year']}"); th.append(f"Citylife เคยเขียนถึง ปี {cl['year']}")
    return " · ".join(en), " · ".join(th)


def _first_en(t):
    """The first sentence of an English paragraph, its asides in brackets taken out."""
    t = re.sub(r"\s*\([^()]*\)", "", (t or "").split("\n")[0]).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    t = m.group(1) if m else t
    return t if 20 <= len(t) <= 240 else ""


def _first_th(t):
    """Thai runs on with spaces between phrases: the opening phrases, up to about a line."""
    t = re.sub(r"\s*\([^()]*\)\s*", "", (t or "").split("\n")[0]).strip()
    if len(t) <= 110:
        return t if len(t) >= 15 else ""
    dangle = ("พ.ศ.", "ค.ศ.", "ปี", "ราว", "ที่", "ช่วง", "ชื่อ", "คือ", "และ", "หรือ", "ใน", "ของ")
    for m in re.finditer(r" ", t):
        i = m.start()
        if i < 45:
            continue
        if i > 150:
            break
        head, nxt = t[:i], t[i + 1:i + 2]
        if nxt.isdigit() or head.endswith(dangle) or re.search(r"\d$", head) and nxt in "กมคปวชพ":
            continue
        return head
    return ""


def story(r):
    """One line about the place in each language: the record's own history first, else the two
    Wikipedia summaries (each in its own language, credited). Both languages or nothing."""
    h = r.get("history") or {}
    se, st = _first_en(h.get("en")), _first_th(h.get("th"))
    if se and st:
        return {"se": se, "st": st}
    a = r.get("attrs") or {}
    s_th, s_en = a.get("summary") or {}, a.get("summaryEn") or {}
    if isinstance(s_th, dict) and isinstance(s_en, dict) and s_th.get("lang") == "th" and s_en.get("lang") == "en":
        se, st = _first_en(s_en.get("text")), _first_th(s_th.get("text"))
        if se and st:
            return {"se": se, "st": st, "wk": [s_th.get("url"), s_en.get("url")]}
    return {}


def main():
    recs = json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())
    clash = build._slug_clash()
    cl_links = json.loads((ROOT / "data" / "citylife_links.json").read_text())["links"]
    imgs = json.loads((ROOT / "data" / "commons_images.json").read_text())["images"]
    wats = {w["id"]: w for w in json.loads((ROOT / "data" / "wats.json").read_text())["wats"]}
    labels = json.loads((ROOT / "docs" / "sites" / "city-live" / "data" / "labels.json").read_text())
    label_names = {(x.get("en") or "").lower() for x in labels}
    th_by_en = {(x.get("en") or "").lower(): x.get("th") for x in labels if x.get("th")}
    th_by_en.update({(w.get("nameEn") or "").lower(): w.get("nameTh") for w in wats.values() if w.get("nameTh")})

    def spot(r, k, w, look=None, th_given=None):
        en = (r.get("nameEn") or "").strip()
        th = (th_given or r.get("nameTh") or (wats.get(r["id"]) or {}).get("nameTh") or th_by_en.get(en.lower()) or "").strip()
        if not en or not th or not re.search(r"[฀-๿]", th):
            return None
        en = re.sub(r"\s*\(.*?\)\s*$", "", en)          # "Wat Umong (Suan Buddha Dhamma)" → "Wat Umong"
        if look == "sunday-walk":
            en = "Sunday Walking Street"
        cl = cl_links.get(r["id"])
        ne, nt = notes(r, cl)
        im = imgs.get(r["id"])
        s = {"id": r["id"], "k": k, "w": w, "en": en, "th": th,
             "lat": round(r["lat"], 5), "lng": round(r["lng"], 5), "ne": ne, "nt": nt,
             "u": f"/{r['province']}/p/{clash.get(r['id']) or build._slug_stem(r)}.html"}
        if look:
            s["look"] = look
        if cl:
            s["cl"] = cl["url"]
        if im:
            s.update(img=im["thumb"], imc=f"{im.get('artist', '')} · {im.get('licence', '')}", imu=im["full"])
        s.update(story(r))
        a = r.get("attrs") or {}
        hrs = r.get("hours") or a.get("openingHours")
        if isinstance(hrs, str) and re.search(r"\d\d:\d\d-\d\d:\d\d", hrs):
            s["hrs"] = hrs                            # OpenStreetMap opening_hours, read by the map at the reader's hour
        if a.get("roadsUrl"):
            s["ru"] = a["roadsUrl"]                   # Roads of Chiang Mai's page for it
        return s

    out, seen = [], set()

    def add(s):
        key = s["en"].lower().replace("thapae", "tha phae")
        if key in seen:
            return False
        seen.add(key); out.append(s); return True

    # the landmarks first, each in its own look
    geo = [r for r in recs if r.get("lat") is not None and where(r["lat"], r["lng"])]
    geo.sort(key=lambda r: (not r["id"].startswith("cm-curated-"), r["id"] not in wats, r["id"]))
    for row in LOOKS:
        look, k, pat = row[:3]
        rx = re.compile(pat, re.I)
        for r in geo:
            if rx.search((r.get("nameEn") or "").strip()):
                s = spot(r, k, where(r["lat"], r["lng"]), look, row[3] if len(row) > 3 else None)
                if s and add(s):
                    break
        else:
            lb = next((x for x in labels if rx.search(x.get("en") or "")), None)
            if lb and lb.get("th"):              # a landmark the map labels but the record lacks
                add({"id": "label-" + look, "k": k, "w": "sheet", "look": look, "en": lb["en"], "th": lb["th"],
                     "lat": lb["lat"], "lng": lb["lng"], "ne": "", "nt": ""})
            else:
                print("no record for look", look)

    pools = {k: [] for k in CAPS}
    for r in geo:
        a = r.get("attrs") or {}
        if a.get("status") in ("closed", "abandoned") or a.get("brand") or (a.get("chainSize") or 0) > 1 or CHAINS.search(r.get("nameEn") or ""):
            continue                                      # her map left the chains off
        k = kind_of(r)
        if not k or DROP.search(r.get("nameEn") or ""):
            continue
        sub, cl = set(r.get("sub") or []), cl_links.get(r["id"])
        score = 0
        score += 50 if (r.get("nameEn") or "").lower() in label_names else 0
        score += 30 if r.get("landmark") or r.get("featured") else 0
        score += 25 if r["id"] in wats else 0
        score += 25 if cl else 0
        score += 20 if r["id"] in imgs else 0
        score += 10 if r["id"].startswith("cm-curated-") else 0
        if k == "wat":
            if not (r["id"] in wats or a.get("foundedCE")):
                continue
            if a.get("foundedCE"):
                score += max(0, 40 - (a["foundedCE"] - 1290) // 15)
        if k == "eat" and not (cl or (r["id"].startswith("cm-curated-") and sub & {"street-food", "noodle", "thai"})):
            continue
        if k == "market" and not (cl or r["id"] in imgs or (r.get("nameEn") or "").lower() in label_names):
            continue
        if k == "see" and not (r["id"] in imgs or cl or a.get("foundedCE") or (r.get("nameEn") or "").lower() in label_names):
            continue
        if k in ("craft", "well") and not cl:
            continue
        if k == "spirit" and not r["id"].startswith("cm-curated-") and "historic" not in sub:
            continue
        s = spot(r, k, where(r["lat"], r["lng"]))
        if s:
            pools[k].append((score, s))
    per_inset = {}
    for k, pool in pools.items():
        pool.sort(key=lambda t: -t[0])
        n = sum(1 for s in out if s["k"] == k)
        for _, s in pool:
            if n >= CAPS[k]:
                break
            if s["w"] != "sheet":
                if per_inset.get((s["w"], k), 0) >= 2:
                    continue
                per_inset[(s["w"], k)] = per_inset.get((s["w"], k), 0) + 1
            if add(s):
                n += 1

    # trees and public art, from the curated file (each row carries its own source)
    if CURATED.exists():
        cur = json.loads(CURATED.read_text())
        for k, rows in (("tree", cur.get("trees", [])), ("art", cur.get("art", []))):
            for i, t in enumerate(rows):
                if not (t.get("en") and t.get("th") and t.get("src")):
                    continue
                s = {"id": f"{k}-{i}", "k": k, "w": "sheet", "en": t["en"], "th": t["th"], "lat": t["lat"], "lng": t["lng"],
                     "ne": t.get("note_en", ""), "nt": t.get("note_th", ""), "src": t["src"]}
                if t.get("kind"):
                    s["ak"] = t["kind"]
                if t.get("u"):
                    s["u"] = t["u"]
                add(s)

    # the moat is drawn as water, not a spot; a tap on it reads its own record
    moat = None
    mr = next((r for r in recs if r["id"] == "cm-curated-the-moat"), None)
    if mr:
        moat = {k: v for k, v in (spot(mr, "go", "sheet") or {}).items() if k in ("id", "en", "th", "lat", "lng", "u", "se", "st", "ru", "img", "imc", "imu")}

    counts = {}
    for s in out:
        counts[s["k"]] = counts.get(s["k"], 0) + 1
    print(len(out), counts, "looks:", sum(1 for s in out if s.get("look")))
    if DRY:
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated": __import__("datetime").date.today().isoformat(),
                               "source": "Mot Dang canonical record (data/canonical/cm.json); photos Wikimedia Commons; trees and art data/curated/doodle_points.json",
                               "spots": out, "moat": moat}, ensure_ascii=False, separators=(",", ":")))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
