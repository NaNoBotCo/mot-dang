"""When and which way: capture time and compass heading for every picture NaN took.

  python3 importers/make_picture_meta.py          # writes data/curated/own_pictures_meta.json
  python3 importers/make_picture_meta.py --table  # also prints the calibration table

Reads (nothing here is written to but the one output):
  data/curated/own_pictures.json          the picks (slug, lat/lng, view, placeId)
  assets/photos/credits.json              NaN's place lead photos, keyed photo:<record id> in the output
  data/canonical/*.json + curated/additions-*.json + curated/enrich.json   record pins
  _incoming/gopro-2026-09-23, -24         frames.csv (time, fix), publish manifests, aesthetic picks, pass2 reads,
                                          placeshots.json + new_records.json (first-pass place photos),
                                          sign_matches.csv + ocr.jsonl (calibration)
  _incoming/passed                        items/finds/verify/cuts (place photos cut centred on a record)
  _incoming/gopro-2026-09-25/raw          EXIF time of the three mall frames (cf-20260925-*)
  _incoming/gopro-2026-09-27              frames.csv, cut/ + cutv/ picks, placecut/plan.json, reads/,
                                          video/GS017990_gpx_* and tools/ride.py (video start)

Writes data/curated/own_pictures_meta.json: {slug | "photo:<id>": {taken, takenSrc, cap?, heading, headingSrc,
headingErr}}, plus _note and _calibration.

Heading. "pin": the bearing from the capture point to the record's pin, when the picture shows a record whose pin
was not itself taken from the camera and the two are 10-50 m apart. "track+view": the direction of travel
(GPS, prev->next fix, over 5 km/h) plus the picture's yaw in the 360 frame plus a mount offset. The mount is not
fixed (it faces the rider, and was turned round between rides), so the offset is measured per burst x view against
records seen from the road (verified passed-place cuts, sign reads located by their OCR box, named places in the
video) and used only where those agree; where a pin and the camera disagree by over 60 deg the camera wins.
Otherwise null. Rerun after each ride; the tables it reads are appended to.
"""
import csv, datetime as dt, difflib, glob, json, math, re, statistics as st, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "_incoming"
OUT = ROOT / "data/curated/own_pictures_meta.json"
TZ = dt.timezone(dt.timedelta(hours=7))
FWD_YAW = -80                                   # the ride tools' forward yaw (render.py, cut.py, zoom.py)
VIEWS = {"L": -90, "F": 0, "R": 90, "B": 180}
MIN_PIN_M, MAX_PIN_M, CAL_MIN_M, CAL_MAX_M = 10, 50, 15, 80   # past 50 m a third of pins point wrong
MOVING_KMH = 5                                  # under this (stopped, walking) there is no travel heading
CAL_N, CAL_MAD = 5, 20                          # a burst x view is used when n >= 5 and median |dev| <= 20 deg
PIN_ERR_M = 12                                  # pin + GPS uncertainty, metres, for a pin heading's +/-
# first-pass mall frames, 25 Sep (hero/*_raw.jpg were rendered from these; no tool file records it)
CF_FRAMES = {"cf-20260925-atrium": ("GSAF6825_144", "R"), "cf-20260925-cosmarche": ("GSAF6825_094", "L"),
             "cf-20260925-chagee": ("GSAF6825_014", "F")}


# ---------------------------------------------------------------- geometry
def wrap(a):
    return (a + 180) % 360 - 180


def metres(a, b, c, d):
    x = math.radians(d - b) * math.cos(math.radians((a + c) / 2))
    return 6371000 * math.hypot(x, math.radians(c - a))


def bearing(a, b, c, d):
    p1, p2, dl = math.radians(a), math.radians(c), math.radians(d - b)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def view_yaw(view, cx=.5):
    """Yaw in the 360 frame of a point cx across a 1600 px, 100-degree view (cut.direction, zoom.direction)."""
    fx = 800 / math.tan(math.radians(50))
    return wrap(FWD_YAW + VIEWS[view] + math.degrees(math.atan((float(cx) * 1600 - 800) / fx)))


def view_of_yaw(yaw):
    return min(VIEWS, key=lambda v: abs(wrap(yaw - FWD_YAW - VIEWS[v])))


def circ_median(xs):
    s = sum(math.sin(math.radians(x)) for x in xs); c = sum(math.cos(math.radians(x)) for x in xs)
    m = math.degrees(math.atan2(s, c))
    med = wrap(m + st.median([wrap(x - m) for x in xs]))
    return med, st.median([abs(wrap(x - med)) for x in xs])


def skel(s):
    return re.sub(r"[^0-9a-z฀-๿]", "", re.sub(r"[ัิ-ฺ็-๎]", "", (s or "").lower()))


def load(p, default=None):
    p = Path(p)
    return json.load(open(p)) if p.exists() else default


def jsonl(pattern):
    for fn in sorted(glob.glob(str(pattern))):
        for line in open(fn):
            try:
                v = json.loads(line)
            except ValueError:
                continue
            if isinstance(v, dict):
                yield v


# ---------------------------------------------------------------- record pins
def camera_pinned(r):
    """A pin set from the camera's own position (a sign read from the road, a shop inside a building): no use
    as a target to take a bearing to."""
    a = r.get("attrs") or {}
    return r.get("confidence") == "field" or bool(a.get("insideOfId")) or "frame" in (a.get("pinVia") or "") \
        or any((s or {}).get("type") == "field" for s in r.get("sources") or [])


PINS, NAMES_OF = {}, {}
for f in sorted(glob.glob(str(ROOT / "data/curated/additions-*.json"))) + sorted(glob.glob(str(ROOT / "data/canonical/*.json"))):
    for r in json.load(open(f)):
        if r.get("lat") is None or r.get("lng") is None:
            continue
        PINS[r["id"]] = (r["lat"], r["lng"], camera_pinned(r))
        NAMES_OF[r["id"]] = {skel(n) for n in (r.get("name"), r.get("nameTh"), r.get("nameEn"),
                                                 *((r.get("attrs") or {}).get("altNames") or [])) if n and len(skel(n)) >= 3}
for rid, e in (load(ROOT / "data/curated/enrich.json", {}) or {}).items():
    fl = (e or {}).get("fields") or {} if isinstance(e, dict) else {}
    if rid in PINS and fl.get("lat") is not None and fl.get("lng") is not None:
        PINS[rid] = (fl["lat"], fl["lng"], PINS[rid][2])
BY_XY = defaultdict(list)
for rid, (la, lo, _) in PINS.items():
    BY_XY[(round(la, 5), round(lo, 5))].append(rid)


def pin_at(lat, lng):
    """The record whose pin a picture's lat/lng was set to, if any."""
    ids = BY_XY.get((round(lat, 5), round(lng, 5))) or []
    return next((i for i in ids if metres(lat, lng, *PINS[i][:2]) < 1.5), None)


# ---------------------------------------------------------------- frames: time and fix
FR = {}          # frame id -> {t, lat, lon, fix, burst, item, ride}
for day in ("2026-09-23", "2026-09-24"):
    fn = INC / f"gopro-{day}/frames.csv"
    if not fn.exists():
        continue
    for r in csv.DictReader(open(fn)):
        k = f"{r['burst']}_{int(r['item']):03d}"
        FR[k] = dict(t=dt.datetime.fromisoformat(r["local_time"]), lat=float(r["lat"]) if r["lat"] else None,
                     lon=float(r["lon"]) if r["lon"] else None, fix=r["position"] == "fix", burst=r["burst"],
                     item=int(r["item"]), ride=day, src="frames.csv")
D27 = INC / "gopro-2026-09-27"
if (D27 / "frames.csv").exists():
    for r in csv.reader(open(D27 / "frames.csv")):
        if len(r) < 4 or r[0].startswith("GS0"):
            continue
        b, n = r[0].rsplit("_", 1)
        FR[r[0]] = dict(t=dt.datetime.strptime(r[1], "%Y:%m:%d %H:%M:%S").replace(tzinfo=TZ),
                        lat=float(r[2]) if r[2] else None, lon=float(r[3]) if r[3] else None, fix=bool(r[2]),
                        burst=b, item=int(n), ride="2026-09-27", src="frames.csv")
BURST = defaultdict(list)
for k, f in FR.items():
    BURST[f["burst"]].append(f)
for b in BURST:
    BURST[b].sort(key=lambda f: f["item"])
    for j, f in enumerate(BURST[b]):
        f["j"] = j

# the ride video: start from tools/ride.py, track from its GPX
VIDEO = {}
if (D27 / "tools/ride.py").exists():
    src = (D27 / "tools/ride.py").read_text()
    name = re.search(r'^VIDEO = "(\w+)"', src, re.M); start = re.search(r'^VIDEO_START_UTC = "([^"]+)"', src, re.M)
    if name and start:
        gpx = "".join(open(p).read() for p in sorted(glob.glob(str(D27 / f"video/{name.group(1)}_gpx_*"))))
        pts = sorted((dt.datetime.fromisoformat(t.replace("Z", "+00:00")), float(a), float(b))
                     for a, b, t in re.findall(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)">.*?<time>([^<]+)</time>', gpx, re.S)
                     if float(a) > 1 and t.startswith("2026"))
        VIDEO = {"name": name.group(1), "t0": dt.datetime.fromisoformat(start.group(1).replace("Z", "+00:00")), "pts": pts}
VPOS = {r[0]: (float(r[2]), float(r[3])) for r in csv.reader(open(D27 / "frames.csv"))
        if len(r) > 3 and r[0].startswith("GS0") and r[2]} if (D27 / "frames.csv").exists() else {}


def video_at(u):
    pts = VIDEO["pts"]
    lo, hi = 0, len(pts) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if pts[mid][0] < u: lo = mid + 1
        else: hi = mid
    cand = [p for p in pts[max(0, lo - 1):lo + 1]]
    best = min(cand, key=lambda p: abs((p[0] - u).total_seconds()))
    return best if abs((best[0] - u).total_seconds()) <= 1.0 else None


def video_frame(fid):
    ms = int(fid.rsplit("_", 1)[1])
    return VIDEO["t0"] + dt.timedelta(milliseconds=ms)


def frame_info(fid):
    """(time, (lat, lon) or None, travel heading or None, km/h or None) for a frame id."""
    if VIDEO and fid.startswith(VIDEO["name"] + "_"):
        u = video_frame(fid)
        pos = VPOS.get(fid)
        if pos is None:
            p = video_at(u); pos = (p[1], p[2]) if p else None
        a, c = video_at(u - dt.timedelta(seconds=1)), video_at(u + dt.timedelta(seconds=1))
        hd = kmh = None
        if a and c and c[0] > a[0]:
            d = metres(a[1], a[2], c[1], c[2]); kmh = d / (c[0] - a[0]).total_seconds() * 3.6
            hd = bearing(a[1], a[2], c[1], c[2]) if d >= 3 else None
        return u.astimezone(TZ), pos, hd, kmh
    f = FR.get(fid)
    if not f:
        return None, None, None, None
    pos = (f["lat"], f["lon"]) if f["lat"] is not None else None
    L = BURST[f["burst"]]
    prev = next((g for g in reversed(L[:f["j"]]) if g["fix"] and (f["t"] - g["t"]).total_seconds() <= 6), None)
    nxt = next((g for g in L[f["j"] + 1:] if g["fix"] and (g["t"] - f["t"]).total_seconds() <= 6), None)
    a = prev or (f if f["fix"] else None); c = nxt or (f if f["fix"] else None)
    hd = kmh = None
    if a and c and a is not c and c["t"] > a["t"]:
        d = metres(a["lat"], a["lon"], c["lat"], c["lon"]); kmh = d / (c["t"] - a["t"]).total_seconds() * 3.6
        hd = bearing(a["lat"], a["lon"], c["lat"], c["lon"]) if d >= 3 else None
    return f["t"], pos, hd, kmh


def near_fix(fid, span=5):
    """A walking frame with no fix of its own: the nearest fix within `span` frames either side."""
    f = FR.get(fid)
    if not f:
        return None
    L = BURST[f["burst"]]
    for d in range(1, span + 1):
        for j in (f["j"] - d, f["j"] + d):
            if 0 <= j < len(L) and L[j]["fix"] and abs((L[j]["t"] - f["t"]).total_seconds()) <= 12:
                return (L[j]["lat"], L[j]["lon"])
    return None


def burst_of(fid):
    return fid.rsplit("_", 1)[0]


def exif_time(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            e = im.getexif().get_ifd(0x8769)
        t, off = e.get(36867), (e.get(36881) or "+07:00").strip("\x00")
        return dt.datetime.strptime(t.strip("\x00"), "%Y:%m:%d %H:%M:%S").replace(
            tzinfo=dt.timezone(dt.timedelta(hours=int(off[:3]), minutes=int(off[0] + off[4:6]))))
    except Exception:
        return None


def iso(t):
    if t is None:
        return None
    t = t.astimezone(TZ)
    ms = t.microsecond // 1000
    return t.strftime("%Y-%m-%dT%H:%M:%S") + (f".{ms:03d}" if ms else "") + "+07:00"


# ---------------------------------------------------------------- where each picture came from
# slug -> {frame, yaw, exact (yaw of the picture's centre known), full (a whole 100-degree view), pin (record id)}
SRC = {}


def put(slug, **kw):
    if slug and slug not in SRC:
        SRC[slug] = kw


def tile_yaw(name):
    m = re.match(r"(GS\w+?_\d+)_y(-?\d+)_p(-?\d+)", name or "")
    return (m.group(1), int(m.group(2))) if m else (None, None)


READ_CX = {}     # (frame, view, of) -> cx, from the pass-2 reads that marked a place picture
for day, p2 in (("23", INC / "gopro-2026-09-23/pass2-local"), ("23", INC / "gopro-2026-09-23/pass2"),
                ("24", INC / "gopro-2026-09-24/pass2")):
    for v in jsonl(p2 / "reads/*.jsonl"):
        ph = v.get("photo")
        if isinstance(ph, dict) and ph.get("of") and ph.get("cx") is not None and v.get("view") in VIEWS:
            READ_CX.setdefault((v["frame"], v["view"], ph["of"]), ph["cx"])
            READ_CX.setdefault((v["frame"], v["view"], None), ph["cx"])

for man_path in (INC / "gopro-2026-09-23/pass2-local/publish/manifest.json", INC / "gopro-2026-09-23/pass2/publish/manifest.json",
                 INC / "gopro-2026-09-24/pass2/publish/manifest.json"):
    man = load(man_path, {}) or {}
    for p in (man.get("points") or []) + (man.get("scenes") or []):
        if p.get("yaw") is not None:
            put(p["slug"], frame=p["frame"], yaw=float(p["yaw"]), exact=True)
    for p in man.get("places") or []:
        cx = READ_CX.get((p["frame"], p["view"], p["of"]))
        put(p["slug"], frame=p["frame"], yaw=view_yaw(p["view"], cx if cx is not None else .5), exact=cx is not None,
            full=cx is None, of=p["of"] if p["of"] in PINS else None)
for ap in (INC / "gopro-2026-09-23/pass2-local/aesthetic/picks.json", INC / "gopro-2026-09-23/pass2/aesthetic/picks.json",
           INC / "gopro-2026-09-24/pass2/aesthetic/picks.json"):
    for p in load(ap, []) or []:
        if p.get("slug") and p.get("yaw") is not None:
            put(p["slug"], frame=p["frame"], yaw=float(p["yaw"]), exact=True)

# passed: place photos cut centred on the record, found by a reader and checked by a verifier
PASSED = INC / "passed"
P_ITEMS = {x["n"]: x for x in load(PASSED / "items.json", []) or []}
P_FINDS = {v["n"]: v for v in jsonl(PASSED / "finds/*.jsonl") if "n" in v}
P_OK = {v["n"]: v.get("ok") for v in jsonl(PASSED / "verify/*.jsonl") if "n" in v}
P_EXCL = {int(k) for k in (load(PASSED / "excluded.json", {}) or {})}
for c in load(PASSED / "cuts.json", []) or []:
    f = P_FINDS.get(c["n"])
    if f and f.get("found") and f.get("view") in VIEWS:
        put(c["slug"], frame=f["frame"], yaw=view_yaw(f["view"], f.get("cx", .5)), exact=True,
            of=(P_ITEMS.get(c["n"]) or {}).get("id"))

# first pass, 23 Sep: place photos cut from the OCR tile that read the sign
RENAMES = load(INC / "gopro-2026-09-23/id_renames.json", {}) or {}
for p in load(INC / "gopro-2026-09-23/placeshots.json", []) or []:
    rid = RENAMES.get(p["id"], p["id"])
    fr, y = tile_yaw(p.get("best_tile")) if p.get("best_tile") else (p.get("frame"), p.get("yaw"))
    if fr and y is not None:
        put(("ride-20260923-place-" + rid)[:80], frame=fr, yaw=float(y), exact=True, of=rid)
for r in load(INC / "gopro-2026-09-23/new_records.json", []) or []:
    rid = RENAMES.get(r["id"], r["id"])
    fr, y = tile_yaw(((r.get("attrs") or {}).get("signFrames") or [None])[0])
    if fr:
        put(("ride-20260923-place-" + rid)[:80], frame=fr, yaw=float(y), exact=True, of=rid)

# 24 Sep, second look (local/picks.json): place photos re-cut for records, slug ride-20260924-place-<id>
for p in ((load(INC / "gopro-2026-09-24/local/picks.json", {}) or {}).values()):
    if isinstance(p, dict) and p.get("of") and p.get("view") in VIEWS:
        put(("ride-20260924-place-" + p["of"])[:80], frame=p["frame"], yaw=view_yaw(p["view"], p.get("cx", .5)),
            exact=True, of=p["of"])

# 27 Sep: the market walk (cut/, placecut/) and the ride video (cutv/)
def pick_yaw(p):
    if p.get("yaw") is not None:
        return float(p["yaw"])
    return view_yaw(p["view"], p.get("cx", .5)) if p.get("view") in VIEWS else None


for p in load(D27 / "cut/picks.json", []) or []:
    put(p["slug"], frame=p["frame"], yaw=pick_yaw(p), exact=True)
for p in load(D27 / "placecut/plan.json", []) or []:
    slug = "chamcha-20260927-place-" + re.sub(r"[^a-z0-9]+", "-", p["id"].split("cm-", 1)[1])[-40:].strip("-")
    put(slug, frame=p["frame"], yaw=view_yaw(p["view"], p.get("cx", .5)), exact=True, of=p["id"])
for p in load(D27 / "cutv/picks.json", []) or []:
    put(p["slug"], frame=p["frame"], yaw=pick_yaw(p), exact=True)


def from_slug(slug, view):
    """ride-2026092x-<burst>-<frame>-<view>[-n]: a whole view of that frame."""
    m = re.match(r"ride-\d{8}-([a-z]{2}\d{4})-(\d{3})-([lfrb])(?:-\d{4})?$", slug)
    if not m:
        return None
    fr, v = f"GS{m.group(1).upper()}_{m.group(2)}", m.group(3).upper()
    cx = READ_CX.get((fr, v, None))
    return dict(frame=fr, yaw=view_yaw(v, cx if cx is not None else .5), exact=cx is not None, full=cx is None)


# ---------------------------------------------------------------- calibration: pin bearing - travel - yaw
CAL = []         # (burst, view, residual, metres, source)


def cal_add(fid, yaw, rid, why):
    pin = PINS.get(rid)
    if not pin or pin[2]:
        return
    t, pos, hd, kmh = frame_info(fid)
    if pos is None or hd is None or kmh is None or kmh <= MOVING_KMH:
        return
    d = metres(pos[0], pos[1], pin[0], pin[1])
    if not CAL_MIN_M <= d <= CAL_MAX_M:
        return
    CAL.append((burst_of(fid), view_of_yaw(yaw), wrap(bearing(pos[0], pos[1], pin[0], pin[1]) - hd - yaw), d, why, fid))


for n, f in P_FINDS.items():                               # verified passed-place cuts
    if f.get("found") and P_OK.get(n) is True and n not in P_EXCL and f.get("view") in VIEWS and n in P_ITEMS:
        cal_add(f["frame"], view_yaw(f["view"], f.get("cx", .5)), P_ITEMS[n]["id"], "passed")

OCR = {}                                                     # tile -> text boxes, only for the tiles we need
SIGN_ROWS = []
for sm in (INC / "gopro-2026-09-23/sign_matches.csv", INC / "gopro-2026-09-24/pass2/sign_matches.csv"):
    if sm.exists():
        SIGN_ROWS += list(csv.DictReader(open(sm)))
WANT = {r["best_tile"] for r in SIGN_ROWS}
for oc in (INC / "gopro-2026-09-23/ocr.jsonl", INC / "gopro-2026-09-24/pass2/ocr.jsonl"):
    if oc.exists():
        for line in open(oc):
            i = line.find('"path"')
            m = re.search(r'"path":"tiles\\?/([^"]+)\.jpg"', line[i:i + 120]) if i >= 0 else None
            if m and m.group(1) in WANT:
                try:
                    OCR[m.group(1)] = json.loads(line).get("text") or []
                except ValueError:
                    pass
for r in SIGN_ROWS:                                          # sign reads, located by the OCR box within the tile
    fr, ty = tile_yaw(r["best_tile"])
    texts = OCR.get(r["best_tile"])
    if not fr or not texts:
        continue
    t = max(texts, key=lambda x: difflib.SequenceMatcher(None, x.get("s", ""), r["text_read"]).ratio())
    x = t["box"][0] + t["box"][2] / 2
    cal_add(fr, wrap(ty + math.degrees(math.atan((x - .5) * 2 * math.tan(math.radians(25))))), r["id"], "sign")

if VIDEO:                                                    # the video: named places matched to a record nearby
    def name_match(names, pos, within=150):
        ks = {skel(n) for n in names if n and len(skel(n)) >= 3}
        best = None
        for rid, nm in NAMES_OF.items():
            if not (nm & ks):
                continue
            la, lo, cam = PINS[rid]
            d = metres(pos[0], pos[1], la, lo)
            if d <= within and not cam and (best is None or d < best[1]):
                best = (rid, d)
        return best[0] if best else None
    vx = [(p["frame"], pick_yaw(p), [re.sub(r"\s*(sign|billboard).*$", "", p["of"])])
          for p in load(D27 / "cutv/picks.json", []) or [] if p.get("of") and pick_yaw(p) is not None]
    for v in jsonl(D27 / "reads/v*.jsonl"):
        for pl in v.get("places") or []:
            m = re.match(r"zoom/(GS\w+?_\d+)_([LFRB])_([\d.]+)_", pl.get("source") or "")
            if m and (pl.get("name") or pl.get("name_other")):
                vx.append((m.group(1), view_yaw(m.group(2), float(m.group(3))), [pl.get("name"), pl.get("name_other")]))
    for fr, yaw, names in vx:
        pos = frame_info(fr)[1]
        rid = pos and name_match(names, pos)
        if rid:
            cal_add(fr, yaw, rid, "video-name")

GROUPS = defaultdict(list)
for b, v, res, d, why, _ in CAL:
    GROUPS[(b, v)].append(res); GROUPS[(b, "*")].append(res)
CALIB = {}
for k, xs in GROUPS.items():
    med, mad = circ_median(xs)
    CALIB[k] = dict(n=len(xs), offset=round(med, 1), mad=round(mad, 1), ok=len(xs) >= CAL_N and mad <= CAL_MAD)


def track_view(fid, yaw):
    """(heading, err) from the direction of travel and a calibrated mount, or None."""
    t, pos, hd, kmh = frame_info(fid)
    if hd is None or kmh is None or kmh <= MOVING_KMH:
        return None
    b, v = burst_of(fid), view_of_yaw(yaw)
    c, extra = CALIB.get((b, v)), 0
    if not (c and c["ok"]):
        if c and c["n"] >= CAL_N:
            return None                              # measured for this view, and it does not agree: no heading
        few = c
        c, extra = CALIB.get((b, "*")), 10         # too few for this view: the burst pooled, a wider +/-
        if not (c and c["ok"] and c["n"] >= 2 * CAL_N):
            return None
        if few and abs(wrap(few["offset"] - c["offset"])) > 30:
            return None                              # the view's few points already disagree with the pool
    return (hd + yaw + c["offset"]) % 360, max(10, round(1.4826 * c["mad"])) + extra


# ---------------------------------------------------------------- one entry per picture
def entry(p):
    slug = p["slug"]
    s = SRC.get(slug) or from_slug(slug, p.get("view"))
    e = {"taken": None, "takenSrc": None, "heading": None, "headingSrc": None, "headingErr": None}
    lat, lng = p.get("lat"), p.get("lng")
    cap = None
    if slug in CF_FRAMES:
        fr, v = CF_FRAMES[slug]
        t = exif_time(INC / f"gopro-2026-09-25/raw/{fr}.36p")
        e.update(taken=iso(t), takenSrc="exif" if t else None)
        e["cap"] = None                        # indoors, no fix; the picture's pin is the mall's
        return e
    if s:
        t, pos, hd, kmh = frame_info(s["frame"])
        if t is not None:
            e.update(taken=iso(t), takenSrc="video+gpx" if VIDEO and s["frame"].startswith(VIDEO["name"]) else "frames.csv")
        cap = pos or near_fix(s["frame"])
    # the picture's own lat/lng: the capture point, or a record's pin?
    pin_id = p.get("placeId") or (s or {}).get("of")
    if lat is not None and cap and metres(lat, lng, *cap) < 3:
        at_capture = True
    else:
        at_capture = False
        pin_id = pin_id or (pin_at(lat, lng) if lat is not None else None)
    if not at_capture:
        e["cap"] = [round(cap[0], 7), round(cap[1], 7)] if cap else None
    here = cap if cap else (None if not at_capture else (lat, lng))
    # 1. pin
    pin = PINS.get(pin_id) if pin_id else None
    pin_h = None
    if pin and not pin[2] and here:
        d = metres(here[0], here[1], pin[0], pin[1])
        if MIN_PIN_M <= d <= MAX_PIN_M:
            err = math.degrees(math.atan2(PIN_ERR_M, d))
            if s and s.get("full"):
                err = math.hypot(err, 25)       # a whole 100-degree view: the place need not sit at its centre
            pin_h = (bearing(here[0], here[1], pin[0], pin[1]), max(5, round(err)))
    # 2. travel + view
    tv = track_view(s["frame"], s["yaw"]) if s and s.get("yaw") is not None else None
    if pin_h and tv and abs(wrap(pin_h[0] - tv[0])) > (90 if s.get("full") else 60):
        # the camera's own direction outranks a pin that disagrees with it (a pin across the road, a wrong match)
        e.update(heading=round(tv[0]), headingSrc="track+view", headingErr=tv[1],
                 headingNote=f"the record's pin is {abs(round(wrap(pin_h[0] - tv[0])))} deg off the camera's direction")
    elif pin_h:
        e.update(heading=round(pin_h[0]), headingSrc="pin", headingErr=pin_h[1])
    elif tv:
        e.update(heading=round(tv[0]), headingSrc="track+view", headingErr=tv[1])
    return e


def main():
    own = json.load(open(ROOT / "data/curated/own_pictures.json"))["picks"]
    out = {}
    for p in own:
        out[p["slug"]] = entry(p)
    # NaN's place lead photos: the same cut as one of her picks
    by_shared, by_pid = {}, defaultdict(list)
    for p in own:
        if p.get("shared"):
            by_shared[Path(p["shared"]).stem] = p["slug"]
        if p.get("placeId"):
            by_pid[p["placeId"]].append(p["slug"])
    stage = {}
    for sp in (INC / "gopro-2026-09-23/pass2-local/stage/place_photos.json", INC / "gopro-2026-09-24/stage/place_photos.json"):
        for rid, v in (load(sp, {}) or {}).items():
            stage[RENAMES.get(rid, rid)] = v["slug"]
    cred = load(ROOT / "assets/photos/credits.json", {}) or {}
    for rid, c in cred.items():
        if not isinstance(c, dict) or c.get("author") != "NaN Peacock":
            continue
        cands = [by_shared.get(rid), stage.get(rid)] + sorted(by_pid.get(rid, []), key=lambda s: not re.search(r"-\d{4}$", s))
        slug = next((s for s in cands if s and s in out), None)
        if slug and out[slug]["taken"]:
            out[f"photo:{rid}"] = dict(out[slug], pick=slug)
    table = [dict(burst=b, view=v, **c) for (b, v), c in sorted(CALIB.items())]
    doc = {"_note": "Capture time and compass heading for NaN's own pictures (own_pictures.json slugs) and her place "
                    "lead photos (photo:<record id>). taken: ISO, +07:00. cap: the capture point where the picture's "
                    "lat/lng is a record's pin (null: not known). heading: degrees true the picture faces; headingSrc "
                    "'pin' = bearing capture->record pin, 'track+view' = travel direction + yaw in the 360 frame + a "
                    "per-burst mount offset (_calibration); headingErr = +/- degrees. Null where it cannot be known. "
                    "Written by importers/make_picture_meta.py; rerun after each ride.",
           "_generated": dt.date.today().isoformat(), "_calibration": table}
    # A pass that could not read a source (the Passport unplugged, a ride folder
    # moved) keeps what an earlier pass found rather than blanking it.
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text())
        except ValueError:
            prev = {}
        for k, pv in prev.items():
            if k.startswith("_") or not isinstance(pv, dict):
                continue
            if k not in out:
                out[k] = pv
            elif not out[k].get("taken") and pv.get("taken"):
                out[k] = dict(pv, **{f: v for f, v in out[k].items() if v is not None})
            elif out[k].get("heading") is None and pv.get("heading") is not None:
                for f in ("heading", "headingSrc", "headingErr", "headingNote", "cap"):
                    if pv.get(f) is not None:
                        out[k][f] = pv[f]
    doc.update(out)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    tmp.replace(OUT)
    pics = [v for k, v in out.items() if not k.startswith("photo:")]
    ph = [v for k, v in out.items() if k.startswith("photo:")]
    cnt = lambda xs, k, val: sum(1 for x in xs if x.get(k) == val)
    print(f"pictures {len(pics)}: taken {sum(1 for x in pics if x['taken'])}, heading pin {cnt(pics, 'headingSrc', 'pin')}, "
          f"track+view {cnt(pics, 'headingSrc', 'track+view')}, null {cnt(pics, 'headingSrc', None)}; "
          f"pin overruled by track+view {sum(1 for x in pics if x.get('headingNote'))}")
    print(f"lead photos {len(ph)}: heading pin {cnt(ph, 'headingSrc', 'pin')}, track+view {cnt(ph, 'headingSrc', 'track+view')}")
    if "--table" in sys.argv:
        for r in table:
            print(f"  {r['burst']:10} {r['view']}  n={r['n']:3}  offset {r['offset']:7.1f}  mad {r['mad']:5.1f}  {'ok' if r['ok'] else '--'}")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
