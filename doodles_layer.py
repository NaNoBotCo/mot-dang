"""The cover doodles, reused (Nan, 2026-10-02: "start reusing motdang cover
doodles for events/locations/festivals that lack enough graphics").

data/curated/doodles.json `kinds` says what each drawing fits; the drawings
are assets/front/doodles.js (over skyline.js, MDSKY), the stills assets/doodles/<kind>.png
(make_doodle_stills.py). copy() puts both under docs/front/.

Nan, 2026-10-02: "If any of my minisites have doodles, ok to use those as well for
related topics." A kind with `from` is one of those drawings: its still credits and
links the minisite and plays in place (doodles.js play()); `places` lets it fit a
place page with no picture (fit_place).
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data/curated/doodles.json"
STILLS = ROOT / "assets/doodles"
_K = None


def kinds():
    global _K
    if _K is None:
        k = json.loads(SRC.read_text()).get("kinds", {}) if SRC.exists() else {}
        _K = {n: dict(v, rx=re.compile(v["fits"], re.I)) for n, v in k.items() if v.get("fits")}
    return _K


def fit(*texts):
    """The first kind whose `fits` matches any of the texts, or ""."""
    t = " ".join(x for x in texts if x)
    for n, v in kinds().items():
        if t and v["rx"].search(t):
            return n
    return ""


def fit_place(r):
    """A place page with no picture: the first kind with `places` whose `fits` matches
    the place's names or stated trade, unless every category it is filed under is one
    the kind skips; or ""."""
    a = r.get("attrs") or {}
    cats = set(r.get("cat") or [])
    sv = a.get("services")
    t = " ".join(x for x in (r.get("name"), r.get("nameEn"), a.get("kind") if isinstance(a.get("kind"), str) else "",
                             " ".join(map(str, sv)) if isinstance(sv, list) else "") if x)
    for n, v in kinds().items():
        pl = v.get("places")
        if not pl or (cats and cats <= set(pl.get("skip") or [])):
            continue
        if t and v["rx"].search(t):
            return n
    return ""


def fit_festival(f):
    for n, v in kinds().items():
        if f.get("id") in (v.get("festivals") or []):
            return n
    return fit(f.get("name_th"), f.get("name_en"), " ".join(f.get("tags") or []))


def still(kind):
    """Root-relative path of the kind's still, or "" when it has not been drawn."""
    return "front/doodles/%s.png" % kind if kind and (STILLS / (kind + ".png")).exists() else ""


def alt(kind):
    v = kinds().get(kind) or {}
    return v.get("th", ""), v.get("en", "")


def plays(kind):
    """True when the kind came from a minisite drawing that doodles.js plays in place."""
    return bool((kinds().get(kind) or {}).get("from"))


def credit(kind, r, bi=None, style=""):
    """'from <minisite>', linked, for a kind drawn from one of her minisites; else ""."""
    fr = (kinds().get(kind) or {}).get("from")
    if not fr:
        return ""
    href = fr["href"] if "://" in fr["href"] else r + fr["href"]
    txt = bi("ภาพจาก " + fr["th"], "from " + fr["en"]) if bi else "ภาพจาก %s · from %s" % (fr["th"], fr["en"])
    return f'<a href="{href}"{style}>{txt}</a>'


def script(r):
    """The drawings' scripts, in the front page's order: the weaver comes from the
    doodler's paper-cut kit (doodler.js), which stands on skyline.js."""
    return "".join(f'<script src="{r}front/{js}" defer></script>' for js in ("skyline.js", "doodler.js", "doodles.js"))


def figure(kind, r, att, cls="doodlefig", bi=None):
    """The still as an <img>; r is the path back to the root. A minisite's drawing
    carries its credit and plays in place."""
    src = still(kind)
    if not src:
        return ""
    th, en = alt(kind)
    img = (f'<img class="{cls}" src="{r}{src}" alt="{att(th + " / " + en)}" loading="lazy" '
           + (f'data-dd="{kind}" ' if plays(kind) else "")
           + 'style="width:100%;aspect-ratio:1200/630;object-fit:cover;border-radius:12px;display:block">')
    if not plays(kind):
        return img
    return (f'<figure style="margin:0">{img}<figcaption class="tinynote">{credit(kind, r, bi)}</figcaption></figure>'
            + script(r))


def copy(docs):
    d = Path(docs) / "front"
    (d / "doodles").mkdir(parents=True, exist_ok=True)
    front = ROOT / "assets/front"
    # findpeek.js: the peek card and drawn thumbnails on /find and the shelves (Nan, 2026-10-04)
    for js in ["skyline.js", "doodles.js", "portrait.js", "findpeek.js"] + sorted(p.name for p in front.glob("doodler*.js")):
        if (front / js).exists():
            shutil.copy(front / js, d / js)
    n = 0
    for p in STILLS.glob("*.png"):
        shutil.copy(p, d / "doodles" / p.name)
        n += 1
    return n


# ---------------------------------------------------------------- portraits of one place
# A place page with no photograph of its own draws that place from its own facts with the
# auto-doodler (Nan, 2026-10-02: "utilize the doodler to avoid filler"). The scene shows what
# the place does, under its own name, in its own setting. Wats, historic sights and museums
# keep their map: a drawing would be a temple that is not this temple.
PORTRAIT_SKIP = {"wat", "sights", "museums-galleries"}
PORTRAIT = [  # (cat, sub or None, scene) — first match wins
    ("food", "cafe", "cafe"), ("food", "bar-pub", "bar"), ("food", "bakery-dessert", "bakery"),
    ("food", "street-food", "streetfood"), ("food", "noodle", "noodle"), ("food", None, "restaurant"),
    ("hotel", "hostel", "hostel"), ("hotel", "guesthouse", "guesthouse"), ("hotel", None, "hotel"),
    ("realestate", "condo", "condo"), ("realestate", "apartment", "apartment"), ("realestate", "dorm", "dorm"),
    ("realestate", "moobaan", "moobaan"), ("realestate", "agent", "agent"), ("realestate", None, "condo"),
    ("essentials", "pharmacy", "pharmacy"), ("essentials", "convenience", "convenience"), ("essentials", "bank", "bank"),
    ("essentials", "laundry", "laundry"), ("essentials", "gov", "gov"), ("essentials", "post", "post"),
    ("essentials", "printing", "printing"), ("essentials", None, "gov"),
    ("repair", "auto", "garage"), ("repair", None, "fixit"),
    ("shopping", "mall", "mall"), ("shopping", "clothes", "clothes"), ("shopping", "crafts", "crafts"),
    ("shopping", "secondhand", "secondhand"), ("shopping", None, "clothes"),
    ("business", None, "office"),
    ("beauty", None, "salon"),
    ("transport", "fuel", "fuel"), ("transport", "parking", "parking"), ("transport", "motorcycle-parking", "parking"),
    ("transport", "motorbike", "rental"), ("transport", "rental", "rental"), ("transport", "motorbike-rental", "rental"), ("transport", "car-rental", "rental"), ("transport", "bicycle", "rental"),
    ("transport", "tours", "tours"), ("transport", "bus", "busstop"), ("transport", None, "busstop"),
    ("school", "university", "university"), ("school", "campus", "university"), ("school", "college", "university"),
    ("school", "training", "training"), ("school", None, "school"),
    ("medical", "hospital", "hospital"), ("medical", "dentist", "dentist"), ("medical", "optometrist", "optician"),
    ("medical", "health-station", "healthstation"), ("medical", None, "clinic"),
    ("community", "cremation", ""), ("community", None, "community"),
    ("market", None, "freshmarket"), ("massage", None, "massage"), ("muaythai", None, "muaythai"),
    ("cooking", None, "cooking"), ("chang", None, "elephants"), ("tattoo", None, "tattoo"),
    ("sport", None, "gym"), ("parks", None, "park"), ("pets", None, "pets"),
]
HILLS = {"แม่ริม", "แม่แตง", "สะเมิง", "ดอยสะเก็ด", "แม่ออน", "จอมทอง", "แม่แจ่ม", "เชียงดาว", "พร้าว", "ฝาง", "แม่อาย",
         "อมก๋อย", "ดอยเต่า", "ฮอด", "กัลยาณิวัฒนา", "เวียงแหง", "ไชยปราการ", "แม่สรวย", "เวียงป่าเป้า", "แม่ฟ้าหลวง", "แม่จัน",
         "เทิง", "ขุนตาล", "เวียงแก่น", "ดอยหลวง", "แม่สาย", "พาน"}


BEAUTY_CLINIC = re.compile(r"คลินิกความงาม|ความงาม|เสริมความงาม|aesthetic|beauty clinic|skin clinic|ผิวหนัง|ผิวพรรณ|เลเซอร์หน้า|"
                           r"derma|botox|โบท็อก|ฟิลเลอร์|filler|ร้อยไหม|สลายไขมัน|whitening|ผิวใส|laser clinic|คลินิกเลเซอร์", re.I)


def place_scene(r):
    """The portrait scene for a place, or "" when it keeps its map."""
    cats = r.get("cat") or []
    if not cats or cats[0] in PORTRAIT_SKIP:
        return ""
    a = r.get("attrs") or {}
    if cats[0] in ("medical", "beauty", "massage") and BEAUTY_CLINIC.search(
            " ".join(str(x) for x in (r.get("name"), r.get("nameEn"), a.get("specialty"), a.get("facilityType")) if x)):
        return "beautyclinic"
    subs = set(r.get("sub") or [])
    if fit_place(r) == "akha" and not subs & {"cafe", "bar-pub", "bakery-dessert", "guesthouse", "hostel", "hotel-full"} \
            and cats[0] not in {"food", "hotel"}:
        return "akha"   # an Akha village, museum, church or school keeps the Akha scene
    for cat, sub, scene in PORTRAIT:
        if cats[0] == cat and (sub is None or sub in subs):
            return scene
    return ""


_PROPS = None


def place_props(r, scene, tags):
    """The drawn props (data/curated/portrait_props.json) this place's tags call for."""
    global _PROPS
    if _PROPS is None:
        f = ROOT / "data" / "curated" / "portrait_props.json"
        _PROPS = json.loads(f.read_text()).get("props", {}) if f.exists() else {}
    ts = set(tags or ())
    return [k for k, p in _PROPS.items() if p.get("drawn") and ts & set(p.get("tags") or ())
            and scene not in (p.get("not_scenes") or ())]


def place_facts(r, tags=None, scene=None):
    """What the portrait draws from: only this place's own fields, and props from its tags."""
    a = r.get("attrs") or {}
    sv = a.get("services")
    f = {"id": r.get("id"), "name": r.get("name"), "nameTh": r.get("nameTh") or r.get("name"), "nameEn": r.get("nameEn"),
         "cat": (r.get("cat") or [""])[0], "sub": r.get("sub") or [], "brand": a.get("brand"), "hours": r.get("hours"),
         "road": a.get("road"), "moo": a.get("moo"), "tambon": a.get("tambon"), "amphoe": a.get("amphoe"),
         "oldCity": bool(a.get("inOldCity")), "hills": a.get("amphoe") in HILLS, "inside": a.get("insideOf"),
         "services": sv if isinstance(sv, list) else [], "cuisine": [s for s in (r.get("sub") or []) if s not in ("cafe", "bar-pub")],
         "levels": a.get("levels"), "facility": a.get("facilityType"), "specialty": a.get("specialty"),
         "province": r.get("province"), "lat": r.get("lat"), "lng": r.get("lng")}
    if a.get("riverName") and a.get("riverM") is not None:
        f["river"] = {"name": a["riverName"], "m": a["riverM"]}
    f["props"] = place_props(r, scene if scene is not None else place_scene(r), r.get("tags") if tags is None else tags)
    return {k: v for k, v in f.items() if v not in (None, "", [], False) or k in ("name",)}


PORTRAIT_WORDS = {
    "restaurant": ("ร้านอาหาร", "restaurant"), "cafe": ("ร้านกาแฟ", "café"), "bar": ("บาร์", "bar"), "bakery": ("ร้านขนม", "bakery"),
    "streetfood": ("ร้านริมทาง", "street stall"), "noodle": ("ร้านก๋วยเตี๋ยว", "noodle shop"), "hotel": ("โรงแรม", "hotel"),
    "guesthouse": ("เกสต์เฮาส์", "guesthouse"), "hostel": ("โฮสเทล", "hostel"), "condo": ("คอนโด", "condominium"),
    "apartment": ("อพาร์ตเมนต์", "apartments"), "dorm": ("หอพัก", "dormitory"), "moobaan": ("หมู่บ้านจัดสรร", "housing estate"),
    "agent": ("นายหน้าอสังหาฯ", "estate agent"), "massage": ("ร้านนวด", "massage"), "akha": ("ชุมชนอาข่า", "Akha"),
    "beautyclinic": ("คลินิกความงาม", "beauty clinic"),
}


def portrait(r, scene, rel, att, bi=None, tags=None):
    """The place drawn from its own facts by the auto-doodler (assets/front/portrait.js), for a
    page with no photograph of it. The words say it is a drawing."""
    nm = r.get("nameTh") or r.get("name") or ""
    w = PORTRAIT_WORDS.get(scene)
    label = ("ภาพวาด%s %s" % (w[0], nm), "Drawing of %s, %s" % (nm, w[1])) if w else ("ภาพวาด %s" % nm, "Drawing of %s" % nm)
    facts = json.dumps(place_facts(r, tags, scene), ensure_ascii=False, separators=(",", ":"))
    cap = bi("ภาพวาด", "Drawing") if bi else "ภาพวาด · Drawing"
    return (f'<figure class="portrait" style="margin:0"><canvas class="mdportrait" data-set="{att(scene)}" data-p="{att(facts)}" '
            f'role="img" aria-label="{att(label[0] + " / " + label[1])}" '
            'style="width:100%;aspect-ratio:2/1;display:block;border-radius:12px;background:#121330"></canvas>'
            f'<figcaption class="tinynote">{cap}</figcaption></figure>'
            + "".join(f'<script src="{rel}front/{js}" defer></script>' for js in ("skyline.js", "doodler.js", "portrait.js")))


# ---------------------------------------------------------------- /sites/doodles/: every drawing, in one place
# Nan, 2026-10-04: "add all the doodles from the place pages and the minisites, too, and link back to them".
# as data/doodles/ (build.py works the rows out in its parent process): index.json (kinds, counts, chunk counts), <scene>-<n>.json (the facts the portrait draws
# from, plus "u", the page), names.json (for search), minisites.json (the drawings harvested from her minisites).

CHUNK = 240


def _minisites():
    """The minisite drawings: kinds with `from` (doodles.js) and the harvest ledger's doodler scenes."""
    import sites_layer
    cards = {c.get("id"): c for c in sites_layer.load().get("cards", [])}
    led = json.loads((ROOT / "data/curated/minisite_harvest.json").read_text()).get("sites", {})
    out, have = [], set()
    for slug, h in led.items():
        if h.get("state") != "harvested":
            continue
        c = cards.get(slug) or {}
        href = c.get("href") or "https://nanobotco.github.io/%s/" % slug
        href = href if "://" in href else "/" + href.lstrip("/")
        name = (c.get("th") or h.get("th") or slug.replace("-", " "), c.get("en") or h.get("en") or slug.replace("-", " ").title())
        for lib, names in re.findall(r"(doodles\.js|doodler[\w-]*\.js) ([a-z, -]+?)(?=\s*\(|;|$)", h.get("doodle", "")):
            for n in [x.strip() for x in names.split(",") if x.strip()]:
                kind = "dd" if lib == "doodles.js" else "scene"
                if (kind, n) in have:
                    continue
                have.add((kind, n))
                k = (kinds().get(n) or {}) if kind == "dd" else {}
                out.append({"lib": kind, "k": n, "site": slug, "href": href, "th": name[0], "en": name[1],
                            "alt_th": k.get("th", ""), "alt_en": k.get("en", ""), "date": h.get("date", "")})
    return out


def gallery(docs, rows):
    """Write data/doodles/ under docs. rows: [(record, scene, tags, href)]. With no rows it puts back
    the last list that had some (cache/doodles-gallery/) rather than publish an empty one."""
    keep = ROOT / "cache" / "doodles-gallery"
    if not rows:
        print("doodles gallery: NO place portraits this build — the last good list stands in")
        if keep.exists():
            out = docs / "data" / "doodles"
            if out.exists():
                shutil.rmtree(out)
            shutil.copytree(keep, out)
            return json.loads((out / "index.json").read_text()).get("total", 0)
        return 0
    out = docs / "data" / "doodles"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    import translit
    thai, amp = re.compile("[\u0e00-\u0e7f]"), {}
    by = {}
    for r, scene, tags, href in rows:
        f = place_facts(r, tags, scene)
        f["u"] = href
        # the English side reads Latin letters (Nan, 2026-10-04): a Thai-only name and the district, romanized
        if not f.get("nameEn") and thai.search(f.get("name") or ""):
            f["nameRom"] = translit.reading(f["name"])
        if f.get("amphoe") and thai.search(f["amphoe"]):
            f["amphoeRom"] = amp.get(f["amphoe"]) or amp.setdefault(f["amphoe"], translit.reading(f["amphoe"]))
        by.setdefault(scene, []).append(f)
    idx, names = [], []
    for scene in sorted(by, key=lambda s: -len(by[s])):
        ps = sorted(by[scene], key=lambda f: (f.get("province") != "cm", (f.get("nameEn") or f.get("name") or "").lower()))
        n = (len(ps) + CHUNK - 1) // CHUNK
        for i in range(n):
            part = ps[i * CHUNK:(i + 1) * CHUNK]
            (out / ("%s-%d.json" % (scene, i))).write_text(json.dumps(part, ensure_ascii=False, separators=(",", ":")))
            for j, f in enumerate(part):
                names.append([f.get("nameTh") or f.get("name") or "", f.get("nameEn") or f.get("nameRom") or "", scene, i, j,
                              (f.get("amphoe") or "") + " " + (f.get("amphoeRom") or ""), f.get("province") or ""])
        w = PORTRAIT_WORDS.get(scene)
        idx.append({"set": scene, "n": len(ps), "chunks": n, "th": w[0] if w else "", "en": w[1] if w else "",
                    "cr": sum(1 for f in ps if f.get("province") == "cr")})
    (out / "names.json").write_text(json.dumps(names, ensure_ascii=False, separators=(",", ":")))
    (out / "minisites.json").write_text(json.dumps(_minisites(), ensure_ascii=False, separators=(",", ":")))
    (out / "index.json").write_text(json.dumps({"chunk": CHUNK, "total": sum(x["n"] for x in idx), "scenes": idx},
                                               ensure_ascii=False, separators=(",", ":")))
    if keep.exists():
        shutil.rmtree(keep)
    shutil.copytree(out, keep)
    return sum(x["n"] for x in idx)
