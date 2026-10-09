"""360 views for place pages, from NaN's GoPro Max 2 spheres.

  python3 importers/make_panos.py copy      raw frames from the Passport to _incoming/pano/raw/
  python3 importers/make_panos.py level     levelled 7680 equirects + a gridded look sheet per frame
  python3 importers/make_panos.py make      mask the rider, blur faces, write assets/pano/ + panos.json
  python3 importers/make_panos.py sheets    numbered review crops of each published sphere
  python3 importers/make_panos.py all       the four in order
  add a frame id (e.g. GSAA7017_175) to run one frame only

Steps, and why:
  1. select   BATCH below, chosen by hand from own_pictures.json picks with a placeId and the
              frames.csv of each ride: stopped or on foot, daylight, few people (counted with
              Vision on the flat views), a place a reader would stand in. Held frames
              (tools/ride.py held(), the swim-school bursts, the 27 Sep video from 934 s on)
              are refused by held().
  2. copy     the Passport drops out under load, so each .36p is copied to the Mac and
              compared byte for byte; every later step reads only the Mac copy.
              A .36p is an MPO: frame 0 is the stitched 7680x3840 equirect JPEG.
  3. level    the sphere is turned so true up is up (tools/sphere.py): the ride's own
              pass2/level_settled.json when it has the frame, else sphere.find_up().
  4. mask     NaN is in every sphere: on the bike the camera faces her; on foot it rides a
              stick over her head. Her region is listed per frame in BATCH ("nan": cap below a
              pitch, and yaw/pitch boxes), drawn from the look sheet, and filled with an
              in-painted, heavily blurred patch from the surrounding pixels: nothing inside
              the region is copied.
  5. blur     everyone else: Vision (faces, people) on 12 yaws x 3 pitches of 60-degree tiles
              at the source's native scale, and 24 x 2 30-degree tiles at twice it along the horizon; a face box grown 60% and the top 42% of a person
              box are mapped back to the equirect (across the +-180 seam) and blurred there.
              BATCH "blur" adds boxes Vision missed (plates, small faces); "sharp" keeps
              statues and images. Vision is run again on the result and its count logged.
  6. write    assets/pano/<slug>.jpg (6144x3072 when under 2.5 MB, else 4096x2048, q80, no
              metadata), assets/pano/prev/<slug>.jpg (a flat cut at the initial view) and
              data/curated/panos.json.
  7. sheets   _incoming/pano/sheets/<slug>_{a,b}.jpg: 8 numbered crops covering the sphere,
              for a person to look at every one. The verdict goes in BATCH "reviewed"/"note".

Compass: northOffset (the compass heading of yaw 0) comes from the sun where it shows
(solar azimuth at the frame's time and place), else from the GPS heading of travel and the
rider's direction (ahead = opposite her). With neither, the viewer hides the compass.

Needs: opencv-python, numpy, Pillow; _incoming/gopro-2026-09-24/tools/sphere.py;
_incoming/pano/tools/visionfp (swiftc -O visionfp.swift -o visionfp).
"""
import csv, datetime, json, math, os, shutil, subprocess, sys
from pathlib import Path

import cv2
import numpy as np

MD = Path(__file__).resolve().parent.parent
INC = MD / "_incoming"
PANO = INC / "pano"
RAW, WORK, SHEETS = PANO / "raw", PANO / "work", PANO / "sheets"
VISION = PANO / "tools" / "visionfp"
OUT = MD / "assets" / "pano"
PREV = OUT / "prev"
PANOS_JSON = MD / "data" / "curated" / "panos.json"
sys.path.insert(0, str(INC / "gopro-2026-09-24" / "tools"))
import sphere as S  # noqa: E402

W0, H0 = 7680, 3840

# ---------------------------------------------------------------- the batch
# nan: regions to cover (levelled yaw/pitch, degrees). {"cap": p} = everything below pitch p;
#      {"box": [yaw_lo, yaw_hi, pitch_lo, pitch_hi]} (yaw_hi may pass 180 to cross the seam).
# blur: extra boxes to blur, same box form. sharp: [yaw, pitch] points; a Vision box whose
#      centre lies within 6 degrees stays sharp (statues, images).
# view: initial [yaw, pitch, hfov]. hold: built and listed in panos.json with an empty "reviewed",
#      so pano_layer leaves it off the page. drop: not built.
BATCH = [
    {"date": "2026-09-24", "frame": "GSAA3729_274", "level": "pass2", "placeId": "cm-ovt-040e5ebd-80c7-40d3-905d-1066775452f7",
     "drop": "same wall of Wat Lok Moli as GSAA3729_282, 50 m earlier; 282 shows the chedi"},
    {"date": "2026-09-24", "frame": "GSAA3729_282", "level": "pass2", "placeId": "cm-ovt-040e5ebd-80c7-40d3-905d-1066775452f7",
     "nan": [{"box": [40, 150, -90, 33]}, {"cap": -45}], "view": [-140, 12, 100], "ahead": -70,
     "reviewed": "2026-09-28", "note": "Wat Lok Moli's chedi and wall from the lane; rider and nadir covered; 2 scooter riders' heads blurred"},
    {"date": "2026-09-24", "frame": "GSAA3729_339", "level": "pass2", "placeId": "cm-osm-node-3298131066",
     "drop": "no levelling holds (bike leaning at the stop, a canopy of hanging wires); NaN and the bike fill half the sphere"},
    {"date": "2026-09-24", "frame": "GSAA2731_941", "level": "vA", "placeId": "cm-osm-way-658996885",
     "nan": [{"box": [40, 140, -90, 40]}, {"cap": -50}], "view": [-155, 8, 100], "north": False,
     "blur": [[-24, -11, -12, -4], [-75, -66, -17, -8]],
     "sharp": [[-152, -1], [-117, -2]],
     "reviewed": "2026-09-28", "note": "Thanyawintra's entrance; rider and nadir covered; faces, a pickup plate and a scooter plate blurred; the two terracotta guardian statues left sharp"},
    {"date": "2026-09-24", "frame": "GSAA3729_473", "level": "vB", "placeId": "cm-ovt-0fb3873d-a0a0-467e-aa2a-9737a8e24eaf",
     "nan": [{"box": [40, 150, -90, 38]}, {"cap": -48}], "view": [-120, 5, 100], "ahead": -80,
     "blur": [[-99, -92, -20, -12], [-65, -52, -10, -4], [-136, -129, -11, -5]],
     "reviewed": "2026-09-28", "note": "Tiger Second Hand's shed; rider and nadir covered; Grab rider, car and pickup plates blurred"},
    {"date": "2026-09-24", "frame": "GSAE5456_063", "level": "pass2", "placeId": "cm-ovt-9450a101-7380-49da-b548-42b5f8f45a83",
     "nan": [{"box": [-130, -30, -90, 35]}, {"cap": -52}], "view": [0, 8, 100], "north": False,
     "blur": [[166, 184, -2, 2.5], [73, 78, -14, -9], [67, 72, -17, -12]],
     "reviewed": "2026-09-28", "note": "Teenonpeenang at the lights; rider and nadir covered; waiting riders' heads and two pedestrians blurred; compass off (the sun is behind cloud)"},
    {"date": "2026-09-27", "frame": "GSAA7017_105", "level": "vB", "placeId": "cm-curated-mae-kham-sai",
     "nan": [{"box": [-158, -12, -90, 3]}, {"cap": -68}], "view": [15, 0, 100],
     "blur": [[50, 56, -2, 3], [17, 22, -1, 3]],
     "reviewed": "2026-09-28", "note": "Mae Kham Sai's stall; NaN (camera on her cap) and nadir covered; vendors and walkers blurred"},
    {"date": "2026-09-27", "frame": "GSAA7017_175", "level": "cam", "placeId": "cm-osm-node-10815775054",
     "nan": [{"box": [-152, -32, -90, 18]}, {"cap": -66}], "view": [75, 5, 100],
     "reviewed": "2026-09-28", "note": "Chamcha lane under the paper streamers; NaN and nadir covered; faces blurred"},
    {"date": "2026-09-27", "frame": "GSAA7017_245", "level": "vB", "placeId": "cm-curated-loang-him-kao",
     "nan": [{"box": [-156, -32, -90, 4]}, {"box": [-168, -140, -90, -58]}, {"cap": -68}], "view": [165, 0, 95],
     "blur": [[55.5, 59, -1.5, 2.5], [66, 70, -1, 2.5]],
     "reviewed": "2026-09-28", "note": "Loang Him Kao; NaN and nadir covered; a companion walks beside her, head blurred, legs sharp; 2 distant faces added by hand"},
    {"date": "2026-09-27", "frame": "GSAA7017_273", "level": "vA", "placeId": "cm-curated-toh-toh",
     "nan": [{"box": [-112, -12, -90, 2]}, {"cap": -64}], "view": [10, 5, 100],
     "blur": [[172, 179, -21, -12], [106, 119, 0, 8]],
     "reviewed": "2026-09-28", "note": "Toh Toh cafe; NaN and nadir covered; cafe sitters and a seated stallholder blurred by hand"},
    {"date": "2026-09-27", "frame": "GSAA7017_333", "level": "cam", "placeId": "cm-curated-baan-u-sa",
     "nan": [{"box": [-48, 118, -90, 7]}, {"box": [-102, -40, -90, -52]}, {"cap": -68}], "view": [-80, -5, 100],
     "reviewed": "2026-09-28", "note": "Baan U-Sa; NaN and nadir covered; faces blurred"},
    {"date": "2026-09-27", "frame": "GSAA7017_381", "level": "vA", "placeId": "cm-curated-yong-le-tea-house",
     "nan": [{"box": [8, 192, -90, 5]}, {"cap": -68}], "view": [-45, 5, 100],
     "blur": [[-162, -157, -11, -7]],
     "reviewed": "2026-09-28", "note": "Yong Le Tea House; NaN and nadir covered; walkers and a car plate blurred"},
    {"date": "2026-09-27", "frame": "GSAA7017_423", "level": "cam", "placeId": "cm-curated-huen-wanida",
     "nan": [{"box": [22, 138, -90, 7]}, {"cap": -72}], "view": [-150, 5, 100],
     "hold": "a NO PHOTO sign hangs on the shop's door, in the initial view"},
    {"date": "2026-09-27", "frame": "GSAA7017_441", "level": "cam", "placeId": "cm-osm-node-10815775054",
     "drop": "no levelling holds under the arch and trees; the market page takes GSAA7017_175"},
]


def held(date, frame):
    """Frames held from publishing (memory: project_gopro_ride_pipeline)."""
    b, n = frame.split("_")[:2]
    n = int(n)
    if date == "2026-09-23":
        return (b == "GSAA1911" and n <= 86) or b in ("GSAC2558", "GSAD2579", "GSAE2595", "GSAF2725")
    if date == "2026-09-24":
        return (b == "GSAA2731" and n <= 83) or b == "GSAE5914"
    if date == "2026-09-27":
        return b in ("GS017990", "GS017991")      # the video: not a still source here
    return False


def src_raw(e):
    return INC / f"gopro-{e['date']}" / "raw" / f"{e['frame']}.36p"


def slug_of(e):
    return f"{e['date'].replace('-', '')}-{e['frame'].lower().replace('_', '-')}"


# ---------------------------------------------------------------- frame facts

def frame_row(e):
    """(local ISO time, lat, lng, kmh, heading) from the ride's frames.csv."""
    f = INC / f"gopro-{e['date']}" / "frames.csv"
    rows = list(csv.reader(open(f)))
    if rows[0][0] == "burst":
        hd = rows[0]
        rs = {f"{r[0]}_{int(r[1]):03d}": dict(zip(hd, r)) for r in rows[1:]}
        order = list(rs)
        r = rs[e["frame"]]
        head = None
        i = order.index(e["frame"])
        for d in range(0, 8):          # the heading of travel from the nearest moving frame
            for j in (i - d, i + d):
                if 0 <= j < len(order):
                    q = rs[order[j]]
                    if q["kmh"] and float(q["kmh"]) >= 5 and q["heading"]:
                        head = float(q["heading"]); break
            if head is not None: break
        return r["local_time"], float(r["lat"]), float(r["lon"]), float(r["kmh"] or 0), head
    rs = {r[0]: r for r in rows}
    r = rs[e["frame"]]
    t = datetime.datetime.strptime(r[1], "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S+07:00")
    return t, float(r[2]), float(r[3]), 0.0, None


def sun_position(iso, lat, lng):
    """Solar azimuth (degrees from north, clockwise) and elevation; NOAA's short form."""
    t = datetime.datetime.fromisoformat(iso).astimezone(datetime.timezone.utc)
    n = t.timetuple().tm_yday
    hr = t.hour + t.minute / 60 + t.second / 3600
    g = 2 * math.pi / 365 * (n - 1 + (hr - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
           + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hr * 60 + eqt + 4 * lng
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha)
    zen = math.acos(max(-1, min(1, cz)))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(dec) * math.cos(la))) + 180
    return az % 360, 90 - math.degrees(zen)


def find_sun(eq, elev):
    """Yaw of the sun's disc in a levelled equirect, if a saturated round blob sits near the
    expected elevation."""
    s = cv2.resize(eq, (1440, 720), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
    m = (g >= 252).astype(np.uint8)
    m[400:] = 0
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    best = None
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 12: continue
        cy = cen[i][1]
        pitch = 90 - (cy + .5) / 720 * 180
        if abs(pitch - elev) > 10: continue
        if best is None or a > best[0]:
            best = (a, (cen[i][0] + .5) / 1440 * 360 - 180, pitch)
    return best


# ---------------------------------------------------------------- geometry

def wrap(a):
    return (a + 180) % 360 - 180


def level_eq(eq, R):
    """Equirect of the levelled sphere: sample the camera ray R @ world for each output pixel."""
    H, W = eq.shape[:2]
    out = np.empty_like(eq)
    lon = ((np.arange(W, dtype=np.float32) + .5) / W * 2 * np.pi - np.pi)
    Rf = R.astype(np.float32)
    for y0 in range(0, H, 256):
        ys = np.arange(y0, min(H, y0 + 256), dtype=np.float32)
        lat = np.pi / 2 - (ys + .5) / H * np.pi
        LA, LO = np.meshgrid(lat, lon, indexing="ij")
        d = np.stack([np.cos(LA) * np.sin(LO), np.sin(LA), np.cos(LA) * np.cos(LO)], -1)
        v = d @ Rf.T
        lo2 = np.arctan2(v[..., 0], v[..., 2])
        la2 = np.arcsin(np.clip(v[..., 1], -1, 1))
        mx = ((lo2 + np.pi) / (2 * np.pi) * W - .5).astype(np.float32)
        my = ((np.pi / 2 - la2) / np.pi * H - .5).astype(np.float32)
        out[y0:y0 + len(ys)] = cv2.remap(eq, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
    return out


def view_R(yaw, pitch):
    return S.rot_y(math.radians(yaw)) @ S.rot_x(-math.radians(pitch))


def tile(eq, yaw, pitch, hfov, w, h):
    return S.sample(eq, S.view_rays(w, h, hfov, yaw, pitch), None, cv2.INTER_LINEAR)


def box_region(W, H, yaw, pitch, hfov, w, h, box, pad=4):
    """Equirect rows, wrapped columns and the boolean mask of pixels that fall inside a
    normalised box of a rectilinear tile."""
    fx = (w / 2) / math.tan(math.radians(hfov) / 2)
    Rv = view_R(yaw, pitch)
    bx, by, bw, bh = box
    xs = np.linspace(bx, bx + bw, 17) * w
    ys = np.linspace(by, by + bh, 17) * h
    pts = [(x, by * h) for x in xs] + [(x, (by + bh) * h) for x in xs] + \
          [(bx * w, y) for y in ys] + [((bx + bw) * w, y) for y in ys] + [((bx + bw / 2) * w, (by + bh / 2) * h)]
    lons, lats = [], []
    for px, py in pts:
        d = np.array([(px - w / 2) / fx, -(py - h / 2) / fx, 1.0])
        v = Rv @ (d / np.linalg.norm(d))
        lons.append(yaw + wrap(math.degrees(math.atan2(v[0], v[2])) - yaw))
        lats.append(math.degrees(math.asin(max(-1, min(1, v[1])))))
    x0 = int(math.floor((min(lons) + 180) / 360 * W)) - pad
    x1 = int(math.ceil((max(lons) + 180) / 360 * W)) + pad
    y0 = max(0, int(math.floor((90 - max(lats)) / 180 * H)) - pad)
    y1 = min(H, int(math.ceil((90 - min(lats)) / 180 * H)) + pad)
    if x1 - x0 > W * .75 or y1 <= y0:
        return None
    xu = np.arange(x0, x1)
    lat = np.radians(90 - (np.arange(y0, y1) + .5) / H * 180)
    lon = np.radians((xu + .5) / W * 360 - 180)
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    d = np.stack([np.cos(LA) * np.sin(LO), np.sin(LA), np.cos(LA) * np.cos(LO)], -1)
    loc = d @ Rv           # world -> tile axes (Rv is orthonormal)
    z = loc[..., 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        px = loc[..., 0] / z * fx + w / 2
        py = -loc[..., 1] / z * fx + h / 2
    m = (z > 0) & (px >= bx * w) & (px <= (bx + bw) * w) & (py >= by * h) & (py <= (by + bh) * h)
    return y0, y1, xu % W, m


def yp_region(W, H, b):
    """Rows, wrapped columns and mask for a yaw/pitch box [yaw_lo, yaw_hi, pitch_lo, pitch_hi]."""
    ylo, yhi, plo, phi = b
    if yhi < ylo: yhi += 360
    x0 = int(math.floor((ylo + 180) / 360 * W)); x1 = int(math.ceil((yhi + 180) / 360 * W))
    y0 = max(0, int(math.floor((90 - phi) / 180 * H))); y1 = min(H, int(math.ceil((90 - plo) / 180 * H)))
    return y0, y1, np.arange(x0, x1) % W, np.ones((y1 - y0, x1 - x0), bool)


def blur_region(eq, y0, y1, cols, m, strength=None):
    """Blur the masked pixels hard, with context from around them, across the seam."""
    H, W = eq.shape[:2]
    hgt, wid = m.shape
    k = strength or max(10.0, min(hgt, wid) / 3.0)
    pad = int(k * 3)
    Y0, Y1 = max(0, y0 - pad), min(H, y1 + pad)
    c0 = cols[0]
    ccols = np.arange(c0 - pad, c0 + wid + pad) % W
    roi = eq[Y0:Y1][:, ccols].copy()
    b = cv2.GaussianBlur(roi, (0, 0), k)
    b = cv2.GaussianBlur(b, (0, 0), k / 2)
    mm = np.zeros(roi.shape[:2], np.float32)
    mm[y0 - Y0:y0 - Y0 + hgt, pad:pad + wid] = m
    fe = max(2.0, min(hgt, wid) * .06)            # soft edge, the box itself stays fully covered
    d = int(fe * 2) * 2 + 1
    mm = cv2.dilate(mm, np.ones((d, d), np.uint8))
    mm = cv2.GaussianBlur(mm, (0, 0), fe)
    mm = np.clip(mm * 1.5, 0, 1)[..., None]
    out = (roi * (1 - mm) + b * mm).astype(np.uint8)
    eq[Y0:Y1, ccols] = out


def nan_mask(W, H, shapes):
    M = np.zeros((H, W), np.uint8)
    for s in shapes:
        if "cap" in s:
            y = int((90 - s["cap"]) / 180 * H)
            M[y:] = 1
        if "top" in s:
            y = int((90 - s["top"]) / 180 * H)
            M[:y] = 1
        if "box" in s:
            y0, y1, cols, m = yp_region(W, H, s["box"])
            M[y0:y1, cols] = 1
    return M


def cover(eq, M):
    """Fill the region with an in-painted, blurred patch from the pixels around it."""
    H, W = eq.shape[:2]
    if not M.any():
        return eq
    sw, sh, pad = 1024, 512, 96
    small = cv2.resize(eq, (sw, sh), interpolation=cv2.INTER_AREA)
    sm = (cv2.resize(M * 255, (sw, sh), interpolation=cv2.INTER_AREA) > 0).astype(np.uint8)
    sm = cv2.dilate(sm, np.ones((7, 7), np.uint8))
    sp = np.concatenate([small[:, -pad:], small, small[:, :pad]], 1)
    mp = np.concatenate([sm[:, -pad:], sm, sm[:, :pad]], 1)
    sp = sp.copy(); sp[mp > 0] = 0
    fill = cv2.inpaint(sp, mp * 255, 9, cv2.INPAINT_TELEA)
    fill = cv2.GaussianBlur(fill, (0, 0), 7)
    fill = fill[:, pad:pad + sw]
    big = cv2.resize(fill, (W, H), interpolation=cv2.INTER_CUBIC)
    f = cv2.dilate(M, np.ones((61, 61), np.uint8)).astype(np.float32)
    f = cv2.GaussianBlur(f, (0, 0), 24)
    f = np.maximum(f, cv2.dilate(M, np.ones((9, 9), np.uint8)).astype(np.float32))[..., None]
    return (eq * (1 - f) + big * f).astype(np.uint8)


# ---------------------------------------------------------------- vision

def vision(paths):
    out = subprocess.run([str(VISION)], input="\n".join(map(str, paths)) + "\n",
                         capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        res[d["path"]] = d
    return res


TW = 1280
# (hfov, vfov, yaws, pitches): 60-degree tiles at the source's native scale over the sphere, then
# 30-degree tiles at twice that scale along the horizon, where people 15-30 m off stand ~20 px tall
# and Vision misses them at native scale.
PASSES = [(60, 45, range(-180, 180, 30), (-35, -5, 25)),
          (30, 22, range(-180, 180, 15), (-9, 7))]


def tile_h(hfov, vfov):
    return int(round(2 * (TW / 2) / math.tan(math.radians(hfov / 2)) * math.tan(math.radians(vfov / 2))))


def detect(eq, tag):
    """Face and person boxes on every tile, as (kind, yaw, pitch, hfov, box, centre yaw, centre pitch)."""
    tdir = WORK / "tiles" / tag
    tdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for hfov, vfov, yaws, pitches in PASSES:
        th = tile_h(hfov, vfov)
        for pitch in pitches:
            for yaw in yaws:
                p = tdir / f"h{hfov}_y{yaw}_p{pitch}.jpg"
                cv2.imwrite(str(p), tile(eq, yaw, pitch, hfov, TW, th), [cv2.IMWRITE_JPEG_QUALITY, 92])
                paths.append((p, yaw, pitch, hfov, th))
    res = vision([p for p, *_ in paths])
    boxes = []
    for p, yaw, pitch, hfov, th in paths:
        d = res.get(str(p), {})
        for kind in ("faces", "people"):
            for b in d.get(kind, []):
                x, y, w, h = b["box"]
                cy, cp = centre(yaw, pitch, x + w / 2, y + (h * .15 if kind == "people" else h / 2), hfov, TW, th)
                boxes.append((kind, yaw, pitch, hfov, b["box"], cy, cp))
    shutil.rmtree(tdir, ignore_errors=True)
    return boxes


def centre(yaw, pitch, cx, cy, hfov, w, h):
    fx = (w / 2) / math.tan(math.radians(hfov) / 2)
    d = np.array([(cx * w - w / 2) / fx, -(cy * h - h / 2) / fx, 1.0])
    v = view_R(yaw, pitch) @ (d / np.linalg.norm(d))
    return math.degrees(math.atan2(v[0], v[2])), math.degrees(math.asin(max(-1, min(1, v[1]))))


def in_nan(M, yaw, pitch):
    H, W = M.shape
    x = int((wrap(yaw) + 180) / 360 * W) % W
    y = min(H - 1, max(0, int((90 - pitch) / 180 * H)))
    return bool(M[y, x])


# ---------------------------------------------------------------- stages

def entries(only):
    for e in BATCH:
        if only and e["frame"] not in only:
            continue
        if held(e["date"], e["frame"]):
            print("held, skipped:", e["frame"]); continue
        yield e


def st_copy(only):
    RAW.mkdir(parents=True, exist_ok=True)
    for e in entries(only):
        dst = RAW / f"{e['frame']}.36p"
        if dst.exists():
            continue
        src = src_raw(e)
        shutil.copyfile(src, dst)
        if subprocess.run(["cmp", "-s", str(src), str(dst)]).returncode:
            dst.unlink(); raise SystemExit(f"copy differs: {e['frame']}")
        print("copied", e["frame"])


def vertical_segments(small, pitches=(0, 25, -20), maxang=40, w=640, hfov=60):
    """Great-circle normals and lengths of near-vertical edges in 60-degree views."""
    ns, ls = [], []
    for p in pitches:
        for y in range(-180, 180, 30):
            Rv = view_R(y, p)
            v = tile(small, y, p, hfov, w, w)
            e = cv2.Canny(cv2.cvtColor(v, cv2.COLOR_BGR2GRAY), 60, 160)
            L = cv2.HoughLinesP(e, 1, np.pi / 360, 45, minLineLength=w // 10, maxLineGap=4)
            for x1, y1, x2, y2 in (L.reshape(-1, 4) if L is not None else []):
                if math.degrees(math.atan2(abs(x2 - x1), abs(y2 - y1))) > maxang:
                    continue
                a, b = Rv @ S._pix_ray(x1, y1, w, w, hfov), Rv @ S._pix_ray(x2, y2, w, w, hfov)
                n = np.cross(a, b); k = np.linalg.norm(n)
                if k > 1e-6:
                    ns.append(n / k); ls.append(math.hypot(x2 - x1, y2 - y1))
    return np.array(ns), np.array(ls)


def best_up(ns, ls, maxt=45, tol=0.8):
    """The up direction (within maxt of the camera's) most vertical edges point through."""
    st = math.sin(math.radians(tol))

    def dirs(th, ph):
        return np.stack([np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)], -1)

    def score(U):
        return (ls[None, :] * (np.abs(U @ ns.T) < st)).sum(1)
    TH, PH = np.meshgrid(np.radians(np.arange(0, maxt + .1, 1.0)), np.radians(np.arange(0, 360, 2.0)))
    U = dirs(TH.ravel(), PH.ravel()); u = U[score(U).argmax()]
    for step in (0.5, 0.15):
        t0 = math.acos(np.clip(u[1], -1, 1)); p0 = math.atan2(u[2], u[0])
        TH, PH = np.meshgrid(np.abs(t0 + np.radians(np.arange(-3, 3.01, step))),
                             p0 + np.radians(np.arange(-6, 6.01, step * 2)))
        U = dirs(TH.ravel(), PH.ravel()); u = U[score(U).argmax()]
    return u


def up_vector(e, eq):
    """True up in camera axes. Every method is fooled by some frame (hanging wires, a market
    roof, a leaning bike), so the method is chosen per frame from the look sheets:
    pass2 = the ride's level_settled.json; cam = as shot; vA = all near-vertical edges;
    vB = only edges at and below the horizon within 25 degrees of vertical; find_up = sphere.py."""
    how = e.get("level", "pass2")
    small = cv2.resize(eq, (2048, 1024), interpolation=cv2.INTER_AREA)
    if how == "pass2":
        L = json.load(open(INC / f"gopro-{e['date']}" / "pass2" / "level_settled.json"))
        return np.array(L[e["frame"]]["up"]), "pass2"
    if how == "cam":
        return np.array([0, 1.0, 0]), "cam"
    if how == "vA":
        return best_up(*vertical_segments(small)), "vA"
    if how == "vB":
        return best_up(*vertical_segments(small, pitches=(0, -15), maxang=25), maxt=35), "vB"
    return S.find_up(small)[0], "find_up"


def look_sheet(eq, path, shapes=()):
    """2048x1024 levelled equirect with a 30-degree grid and the NaN region outlined."""
    s = cv2.resize(eq, (2048, 1024), interpolation=cv2.INTER_AREA)
    for yaw in range(-180, 181, 30):
        x = int((yaw + 180) / 360 * 2048)
        cv2.line(s, (x, 0), (x, 1023), (0, 255, 255), 1)
        cv2.putText(s, str(yaw), (x + 3, 520), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
    for p in range(-60, 61, 30):
        y = int((90 - p) / 180 * 1024)
        cv2.line(s, (0, y), (2047, y), (0, 255, 255), 1)
        cv2.putText(s, str(p), (3, y - 4), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
    if shapes:
        M = nan_mask(2048, 1024, shapes)
        cs, _ = cv2.findContours(M, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(s, cs, -1, (255, 0, 255), 3)
    cv2.imwrite(str(path), s, [cv2.IMWRITE_JPEG_QUALITY, 85])


def st_level(only):
    WORK.mkdir(parents=True, exist_ok=True)
    for e in entries(only):
        if e.get("drop"):
            continue
        lev = WORK / f"{e['frame']}_lev.jpg"
        meta = WORK / f"{e['frame']}.json"
        if not lev.exists():
            eq = cv2.imread(str(RAW / f"{e['frame']}.36p"))
            assert eq is not None and eq.shape[:2] == (H0, W0), e["frame"]
            u, how = up_vector(e, eq)
            R = S.up_to_R(u / np.linalg.norm(u))
            out = level_eq(eq, R)
            cv2.imwrite(str(lev), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
            t, lat, lng, kmh, head = frame_row(e)
            az, el = sun_position(t, lat, lng)
            sun = find_sun(out, el)
            json.dump({"up": [round(float(x), 5) for x in u], "how": how, "tilt": round(S.tilt_deg(R), 1),
                       "taken": t, "lat": lat, "lng": lng, "kmh": kmh, "heading": head,
                       "sun_az": round(az, 1), "sun_el": round(el, 1),
                       "sun_yaw": round(sun[1], 1) if sun else None,
                       "sun_pitch": round(sun[2], 1) if sun else None}, open(meta, "w"), indent=1)
            print("levelled", e["frame"], how, "sun", sun and round(sun[1], 1))
        look_sheet(cv2.imread(str(lev)), WORK / f"{e['frame']}_look.jpg", e.get("nan", ()))


def north_offset(e, meta):
    """Compass heading of yaw 0, or None."""
    if e.get("north") is False:
        return None
    if e.get("north") is not None:
        return e["north"]
    if meta.get("sun_yaw") is not None and abs(meta["sun_pitch"] - meta["sun_el"]) <= 4.5:
        return round((meta["sun_az"] - meta["sun_yaw"]) % 360, 1)
    if meta.get("heading") is not None and e.get("ahead") is not None:
        return round((meta["heading"] - e["ahead"]) % 360, 1)
    return None


def st_make(only):
    OUT.mkdir(parents=True, exist_ok=True); PREV.mkdir(parents=True, exist_ok=True)
    rows = {r["slug"]: r for r in (json.load(open(PANOS_JSON)) if PANOS_JSON.exists() else [])}
    for e in entries(only):
        if e.get("drop"):
            print("dropped", e["frame"], e["drop"]); rows.pop(slug_of(e), None); continue
        slug = slug_of(e)
        meta = json.load(open(WORK / f"{e['frame']}.json"))
        eq = cv2.imread(str(WORK / f"{e['frame']}_lev.jpg"))
        H, W = eq.shape[:2]
        M = nan_mask(W, H, e["nan"])
        boxes = detect(eq, e["frame"])
        n = 0
        for kind, yaw, pitch, hfov, b, cy, cp in boxes:
            if in_nan(M, cy, cp):
                continue
            if any(abs(wrap(cy - sy)) < 6 and abs(cp - sp) < 6 for sy, sp in e.get("sharp", ())):
                continue
            x, y, w, h = b
            if kind == "faces":
                b2 = (x - .3 * w, y - .3 * h, w * 1.6, h * 1.6)
            else:
                b2 = (x - .1 * w, y - .07 * h, w * 1.2, h * .42)
            r = box_region(W, H, yaw, pitch, hfov, TW, tile_h(hfov, 45 if hfov == 60 else 22), b2)
            if r is None or not r[3].any():
                continue
            blur_region(eq, *r); n += 1
        for b in e.get("blur", ()):
            y0, y1, cols, m = yp_region(W, H, b)
            blur_region(eq, y0, y1, cols, m); n += 1
        eq = cover(eq, M)
        after = [b for b in detect(eq, e["frame"] + "_after") if not in_nan(M, b[5], b[6]) and b[0] == "faces"]
        # write: 6144 wide when it stays under 2.5 MB, else 4096
        for w in (6144, 4096):
            img = cv2.resize(eq, (w, w // 2), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80, cv2.IMWRITE_JPEG_PROGRESSIVE, 1,
                                                cv2.IMWRITE_JPEG_OPTIMIZE, 1])
            if len(buf) < 2.5e6 or w == 4096:
                (OUT / f"{slug}.jpg").write_bytes(buf.tobytes()); break
        yaw, pitch, hfov = e["view"]
        pv = tile(eq, yaw, pitch, 80, 960, 540)
        cv2.imwrite(str(PREV / f"{slug}.jpg"), pv, [cv2.IMWRITE_JPEG_QUALITY, 78, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
        cv2.imwrite(str(WORK / f"{e['frame']}_pub.jpg"), eq, [cv2.IMWRITE_JPEG_QUALITY, 92])
        rows[slug] = {"slug": slug, "placeId": e["placeId"], "lat": meta["lat"], "lng": meta["lng"],
                      "taken": meta["taken"], "yaw": yaw, "pitch": pitch, "hfov": hfov,
                      "northOffset": north_offset(e, meta), "width": w,
                      "reviewed": "" if e.get("hold") else e.get("reviewed", ""),
                      "note": ("held: " + e["hold"]) if e.get("hold") else e.get("note", "")}
        print(slug, "blurred", n, "faces seen after", len(after), "bytes", len(buf), "w", w)
        (WORK / f"{e['frame']}_after.json").write_text(json.dumps([[a[0], a[1], a[2], a[3], a[4], round(a[5], 1), round(a[6], 1)] for a in after]))
    order = [slug_of(e) for e in BATCH]
    out = sorted(rows.values(), key=lambda r: order.index(r["slug"]) if r["slug"] in order else 999)
    PANOS_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")


def st_sheets(only):
    SHEETS.mkdir(parents=True, exist_ok=True)
    views = [(y, 0, 90) for y in (-150, -90, -30, 30, 90, 150)] + [(0, 65, 110), (0, -65, 110)]
    for e in entries(only):
        if e.get("drop"):
            continue
        p = WORK / f"{e['frame']}_pub.jpg"
        if not p.exists():
            continue
        eq = cv2.imread(str(p))
        cells = []
        for i, (yaw, pitch, hfov) in enumerate(views, 1):
            c = tile(eq, yaw, pitch, hfov, 960, 640)
            lab = f"{i}  yaw {yaw} pitch {pitch}"
            cv2.rectangle(c, (0, 0), (300, 30), (0, 0, 0), -1)
            cv2.putText(c, lab, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, .65, (255, 255, 255), 2)
            cells.append(c)
        for k, part in (("a", cells[:4]), ("b", cells[4:])):
            sheet = np.vstack([np.hstack(part[:2]), np.hstack(part[2:])])
            cv2.imwrite(str(SHEETS / f"{slug_of(e)}_{k}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("sheets", slug_of(e))


if __name__ == "__main__":
    a = sys.argv[1:]
    stage = a[0] if a else "all"
    only = set(a[1:])
    for name, fn in (("copy", st_copy), ("level", st_level), ("make", st_make), ("sheets", st_sheets)):
        if stage in (name, "all"):
            fn(only)
