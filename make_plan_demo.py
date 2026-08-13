#!/usr/bin/env python3
"""The 200x200 looping demo that sits beside the planner on plan.html.

Routed on the same graph the page routes on, so the demo cannot claim anything
the tool would not. It shows the thing a visitor would never guess from a map:
the walking line and the scooter line are different lines. Same three stops,
same city, two journeys — because a footbridge is a road to one and a wall to
the other, and a one-way soi costs a scooter a lap.

No text. At 200 px Thai and English both turn to mud, and the two diverging
lines are the whole argument anyway.

THE GROUND
----------
The lines are drawn over the real basemap — the same cm-cr.pmtiles the live
maps use, decoded and painted by map_ground.py through this script's own
projector, so the ground and the route cannot drift apart. Before that this was
two lines on a cream square with a hand-drawn moat, and it read the way every
pins-on-paper map reads: like something was still loading. The drawn moat is
gone when the ground is there, because the ground carries the true moat instead
of a square through four corner nodes. With no archive on disk the old paper
and the old moat come back exactly as they were, so the picture still builds on
a machine that has never seen the tiles.

    python3 make_plan_demo.py                    # the 200px tile -> assets/plan-demo.gif
    python3 make_plan_demo.py --plan afternoon   # a real errand run, bigger, labelled

Any plan can be drawn: --stops takes catalogue ids, --size a pixel size, --out a
path. So a gif of a genuine afternoon is a flag away, and it is routed by the
same code as the page rather than illustrated by hand.

build.py copies assets/plan-demo.gif into docs/ (docs/ is wiped every build, so
it can never be hand-placed there).
"""
import argparse
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import map_ground

ROOT = Path(__file__).resolve().parent

SS = 3                      # supersample, then downsample — no aliased pins
PAPER = (251, 246, 238)
ANT = (163, 35, 28)
ANT_DARK = (125, 23, 18)
# The page draws the moat in #2a78d6 at 55% over paper; a GIF has no alpha, so
# the blend is precomputed. It also has to be pale enough not to be mistaken for
# the scooter's line, which is the other blue in the picture.
MOAT = (136, 177, 225)
INK = (36, 28, 21)
GLOSS = (111, 99, 83)
RIDE = (28, 90, 168)

# --- the plans this script knows how to draw --------------------------------
# "tile" is the 200 px loop that sits beside the planner: noodles, a haircut,
# then somewhere across the east moat. Small, wordless, one idea.
#
# "afternoon" is a real errand run in the old city — every stop a business in
# the catalogue with its own phone number and opening hours, sequenced the way
# appointments actually fall rather than the way geometry would prefer. It
# exists to show the thing the tile only hints at: the scooter's leg to the
# dentist is more than twice the walker's, because the moat is between them and
# a footbridge is no use to a scooter.
PLANS = {
    "tile": {
        "size": 200, "labels": False, "out": "assets/plan-demo.gif",
        "stops": [
            ("cm-osm-node-11492126219", None),   # Nam Ngiaw Loong Pong — noodles
            ("cm-osm-node-7295643885", None),    # Backstreet Barber Shop
            ("cm-osm-node-2649612347", None),    # Karinthip Village — across the moat
        ],
    },
    "afternoon": {
        "size": 560, "labels": True, "out": "assets/plan-afternoon.gif",
        "stops": [
            ("cm-osm-way-334004235", "12:30 ข้าวเที่ยง / lunch"),
            ("cm-osm-node-4784119225", "14:00 ทำเล็บ / nails"),
            ("cm-osm-way-357059049", "15:30 นวด / massage"),
            ("cm-osm-node-2414315188", "16:30 หมอฟัน / dentist"),
            ("cm-osm-way-385577703", "17:30 ตลาด / market"),
        ],
    },
}

DIGIT_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]

FOOT_FWD, FOOT_BWD, RIDE_FWD, RIDE_BWD = 1, 2, 4, 8
BITS = {"foot": (FOOT_FWD, FOOT_BWD), "ride": (RIDE_FWD, RIDE_BWD)}


def _unused_load_geo():
    cm = {r["id"]: r for r in json.loads(
        (ROOT / "data" / "canonical" / "cm.json").read_text())}
    stops = [(cm[i]["lat"], cm[i]["lng"]) for i in STOP_IDS]
    corners = [(cm[i]["lat"], cm[i]["lng"]) for i in
               (__import__("build").MOAT_CORNER_IDS[k] for k in ("nw", "ne", "se", "sw"))]
    return stops, corners


# ------------------------------------------------------------------- routing
# The same graph and the same directed search the page runs, so a line drawn
# here is a line the tool would draw. Duplicated rather than imported because
# the page's copy is JavaScript; tests/test_routing.py holds them to the same
# answers.
class Router:
    def __init__(self):
        g = json.loads((ROOT / "data" / "road_graph.json").read_text())
        s = g["scale"]
        self.nodes = [(p[0] / s, p[1] / s) for p in g["nodes"]]
        self.edges = g["edges"]
        self.geom = []
        self.adj = defaultdict(list)
        for i, e in enumerate(self.edges):
            a, b, ln, fl = e[0], e[1], e[2], e[3]
            pts, la, ln_ = [self.nodes[a]], 0, 0
            d = e[4] or []
            for k in range(0, len(d), 2):
                if k == 0:
                    la, ln_ = d[0], d[1]
                else:
                    la += d[k]
                    ln_ += d[k + 1]
                pts.append((la / s, ln_ / s))
            pts.append(self.nodes[b])
            self.geom.append(pts)
            self.adj[a].append((b, ln, fl, i, True))
            self.adj[b].append((a, ln, fl, i, False))

    def ok(self, flags, mode, fwd):
        f, bw = BITS[mode]
        return bool(flags & (f if fwd else bw))

    def nearest(self, pt, mode):
        """Kept for tests that only want a junction."""
        best, bi = None, None
        for i in range(len(self.nodes)):
            if not any(self.ok(e[2], mode, e[4]) for e in self.adj[i]):
                continue
            d = hav_m(pt, self.nodes[i])
            if best is None or d < best:
                best, bi = d, i
        return bi

    def snap(self, pt, mode):
        """Nearest point on the nearest usable road, mirroring md.js.

        Snapping to junctions instead was out by up to a block per stop — on the
        dentist leg it read 465 m where the page read 546 m. A demo that
        disagrees with the tool by a sixth is not a demo of the tool.
        """
        best = None
        for i, pts in enumerate(self.geom):
            fl = self.edges[i][3]
            if not (self.ok(fl, mode, True) or self.ok(fl, mode, False)):
                continue
            run = 0.0
            for k in range(len(pts) - 1):
                d, t, seg = _to_seg(pt, pts[k], pts[k + 1])
                if best is None or d < best["d"]:
                    best = {"d": d, "edge": i, "from_a": run + t * seg}
                run += seg
            if best and best["edge"] == i:
                best["total"] = run
        if best is None:
            return None
        e = self.edges[best["edge"]]
        best["a"], best["b"] = e[0], e[1]
        best["to_a"] = best["from_a"]
        best["to_b"] = max(0.0, best["total"] - best["from_a"])
        return best

    def route(self, s, t, mode):
        """Metres (including both walk-ins) and the polyline, mirroring md.js."""
        if s is None or t is None:
            return None, None
        if s["edge"] == t["edge"]:
            fwd = t["from_a"] >= s["from_a"]
            if self.ok(self.edges[s["edge"]][3], mode, fwd):
                return abs(t["from_a"] - s["from_a"]) + s["d"] + t["d"], None
        dist, prev = {}, {}
        pq = []
        if self.ok(self.edges[s["edge"]][3], mode, False):
            dist[s["a"]] = s["to_a"]
            heapq.heappush(pq, (s["to_a"], s["a"]))
        if self.ok(self.edges[s["edge"]][3], mode, True):
            if s["to_b"] < dist.get(s["b"], math.inf):
                dist[s["b"]] = s["to_b"]
                heapq.heappush(pq, (s["to_b"], s["b"]))
        goals = {}
        if self.ok(self.edges[t["edge"]][3], mode, True):
            goals[t["a"]] = t["to_a"]
        if self.ok(self.edges[t["edge"]][3], mode, False):
            goals[t["b"]] = t["to_b"]
        if not goals:
            return None, None
        best_goal, best_cost = None, math.inf
        while pq:
            c, n = heapq.heappop(pq)
            if c > dist.get(n, math.inf):
                continue
            if c >= best_cost:
                break
            if n in goals and c + goals[n] < best_cost:
                best_cost, best_goal = c + goals[n], n
            for to, ln, fl, ei, fwd in self.adj[n]:
                if not self.ok(fl, mode, fwd):
                    continue
                nc = c + ln
                if nc < dist.get(to, math.inf):
                    dist[to] = nc
                    prev[to] = (n, ei)
                    heapq.heappush(pq, (nc, to))
        if best_goal is None:
            return None, None
        chain, cur = [], best_goal
        while cur in prev:
            p, ei = prev[cur]
            chain.append((ei, cur))
            cur = p
        chain.reverse()
        line = []
        for ei, into in chain:
            pts = self.geom[ei]
            seq = pts if self.edges[ei][1] == into else list(reversed(pts))
            for q in seq:
                if not line or line[-1] != q:
                    line.append(q)
        return best_cost + s["d"] + t["d"], line

    def path(self, a, b, mode):
        """Metres and the polyline, or (None, None)."""
        dist = {a: 0.0}
        prev = {}
        pq = [(0.0, a)]
        while pq:
            c, n = heapq.heappop(pq)
            if n == b:
                break
            if c > dist.get(n, math.inf):
                continue
            for to, ln, fl, ei, fwd in self.adj[n]:
                if not self.ok(fl, mode, fwd):
                    continue
                nc = c + ln
                if nc < dist.get(to, math.inf):
                    dist[to] = nc
                    prev[to] = (n, ei)
                    heapq.heappush(pq, (nc, to))
        if b not in dist:
            return None, None
        chain, cur = [], b
        while cur in prev:
            p, ei = prev[cur]
            chain.append((ei, cur))
            cur = p
        chain.reverse()
        line = []
        for ei, into in chain:
            pts = self.geom[ei]
            seq = pts if self.edges[ei][1] == into else list(reversed(pts))
            for pt in seq:
                if not line or line[-1] != pt:
                    line.append(pt)
        return dist[b], line


def hav_m(a, b):
    R = 6371000.0
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def _to_seg(p, a, b):
    """Metres from p to segment ab, how far along it the foot falls, and the
    segment's length. Flat local projection, same as md.js."""
    kx = math.cos(math.radians(p[0])) * 111320
    ky = 110540
    ax, ay = (a[1] - p[1]) * kx, (a[0] - p[0]) * ky
    bx, by = (b[1] - p[1]) * kx, (b[0] - p[0]) * ky
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = max(0.0, min(1.0, (-(ax * dx + ay * dy) / L) if L else 0.0))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(cx, cy), t, math.sqrt(L)


def projector(pts, W, H, pad=0.22):
    lats = [p[0] for p in pts]
    lngs = [p[1] for p in pts]
    n, s = max(lats), min(lats)
    e, w = max(lngs), min(lngs)
    pad_lat = max((n - s) * pad, 0.0008)
    pad_lng = max((e - w) * pad * 0.75, 0.0008)
    n, s, e, w = n + pad_lat, s - pad_lat, e + pad_lng, w - pad_lng
    kx = math.cos(math.radians((n + s) / 2))
    # Keep the frame square so the moat runs at its true angle rather than
    # being sheared by the canvas.
    span_lng = (e - w) * kx
    span_lat = n - s
    if span_lng > span_lat:
        grow = (span_lng - span_lat) / 2
        n, s = n + grow, s - grow
    else:
        grow = (span_lat - span_lng) / 2 / kx
        e, w = e + grow, w - grow

    def xy(p):
        return ((p[1] - w) / (e - w) * W, (n - p[0]) / (n - s) * H)

    def scale_px_per_km():
        return 1.0 / ((e - w) * kx * 111.32) * W
    xy.px_per_km = scale_px_per_km()
    # What the frame actually covers, so the basemap can be asked for exactly
    # this ground and no more.
    xy.bbox = (s, w, n, e)
    return xy


def dashed(d, pts, colour, width, dash=9 * SS, gap=7 * SS, phase=0.0):
    """Pillow has no dash pattern, so walk the polyline and lay them down."""
    carry = phase
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        seg = math.hypot(x2 - x1, y2 - y1)
        if seg < 1e-6:
            continue
        ux, uy = (x2 - x1) / seg, (y2 - y1) / seg
        t = 0.0
        while t < seg:
            cycle = (carry + t) % (dash + gap)
            if cycle < dash:
                run = min(dash - cycle, seg - t)
                d.line([(x1 + ux * t, y1 + uy * t),
                        (x1 + ux * (t + run), y1 + uy * (t + run))],
                       fill=colour, width=width)
                t += run
            else:
                t += (dash + gap) - cycle
        carry = (carry + seg) % (dash + gap)


def walk(pts, frac):
    """The first `frac` of a polyline, for drawing the route as it is laid."""
    total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                for i in range(len(pts) - 1))
    want = total * frac
    out = [pts[0]]
    run = 0.0
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        seg = math.hypot(x2 - x1, y2 - y1)
        if run + seg >= want:
            t = (want - run) / seg if seg else 0
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
            return out
        out.append((x2, y2))
        run += seg
    return out


def load_font(size, bold=True):
    """Thai needs a face that actually has Thai in it. Arial Unicode does, and
    is on every Mac; Thonburi is the system Thai face. Falls back rather than
    dying, because a demo gif is not worth failing a build over."""
    faces = (["/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
              "/System/Library/Fonts/Thonburi.ttc"]
             + (DIGIT_FONTS if bold else []))
    for p in faces:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def digit_font(size):
    for p in DIGIT_FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return load_font(size)


def pin(d, xy, label, r, font, halo=True):
    x, y = xy
    if halo:
        h = r + max(2, int(1.6 * SS))
        d.ellipse([x - h, y - h, x + h, y + h], fill=(255, 252, 246))
    d.ellipse([x - r, y - r, x + r, y + r], fill=ANT, outline=ANT_DARK, width=max(2, int(0.7 * SS)))
    if r > 7 * SS:
        d.text((x, y), str(label), font=font, fill=PAPER, anchor="mm")


def plan_label_boxes(d, stops_xy, captions, font, W, H, r):
    """Decide where every caption sits, once, before any is drawn.

    Placing each one independently produced a pile-up in the middle of the map:
    five labels on a tight errand run overlapped each other and buried the very
    route lines they were annotating. So each caption is offered eight positions
    around its pin, ordered by how far they point away from the centre of the
    run — outward is where the empty paper is — and takes the first that fits on
    the canvas and clears every box already placed.
    """
    pad = int(2.4 * SS)
    gap = r + int(2.5 * SS)
    cx = sum(p[0] for p in stops_xy) / len(stops_xy)
    cy = sum(p[1] for p in stops_xy) / len(stops_xy)
    dirs = [(1, 0), (-1, 0), (0, -1), (0, 1),
            (1, -1), (-1, -1), (1, 1), (-1, 1)]
    # The pins are obstacles too: a caption laid over a numbered pin hides the
    # one thing telling you which stop it belongs to.
    placed = [(px - r, py - r, px + r, py + r) for px, py in stops_xy]
    out = []
    for (x, y), text in zip(stops_xy, captions):
        if not text:
            out.append(None)
            continue
        bb = d.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
        vx, vy = x - cx, y - cy
        norm = math.hypot(vx, vy) or 1
        ranked = sorted(dirs, key=lambda v: -(v[0] * vx / norm + v[1] * vy / norm))
        best = None
        for dx, dy in ranked:
            ax = x + gap if dx > 0 else (x - gap - tw if dx < 0 else x - tw / 2)
            ay = y - th / 2 if dy == 0 else (y - gap - th if dy < 0 else y + gap)
            if ax < 0 or ay < 0 or ax + tw > W or ay + th > H:
                continue
            box = (ax, ay, ax + tw, ay + th)
            if any(box[0] < q[2] and q[0] < box[2] and box[1] < q[3] and q[1] < box[3]
                   for q in placed):
                continue
            best = box
            break
        if best is None:                     # nowhere clean: clamp and accept
            ax = max(0, min(x + gap, W - tw))
            ay = max(0, min(y - th / 2, H - th))
            best = (ax, ay, ax + tw, ay + th)
        placed.append(best)
        out.append((best, text, bb))
    return out, pad


def draw_label(d, slot, font, pad):
    box, text, bb = slot
    d.rectangle(box, fill=(255, 253, 248), outline=(214, 198, 164),
                width=max(1, int(0.45 * SS)))
    d.text((box[0] + pad - bb[0], box[1] + pad - bb[1]), text, font=font, fill=INK)


def base_image(cfg, xy, size):
    """The unchanging half of every frame: the ground, its credit, its scale.

    Painted once and copied, because it is the same in all forty-odd frames and
    decoding the tiles once per frame would take the build from a second to a
    minute for a picture that does not change.

    Returns (image, ground_drawn). ground_drawn False means there is no archive
    on this machine and the caller should draw the old moat square itself.
    """
    W, H = cfg["W"], cfg["H"]
    im = Image.new("RGB", (W, H), PAPER)
    g = map_ground.shared()
    # Zoom is chosen for the size the gif is *seen* at, not the supersampled
    # canvas: ask at 3x and the 200 px tile fills with driveways that survive
    # the downsample as noise. Widths are still measured on the big canvas.
    ok = False
    if g.available:
        # Buildings stay on even at 200 px. Tested both ways: without them the
        # tile is a grid of pale lines that could be any town on earth, and with
        # them it is visibly a dense old city with a moat down one side. At that
        # size they are not buildings, they are texture, and the texture is the
        # part that says "here".
        ok = g.paint(im, xy, xy.bbox, width_px=W, zoom=g.zoom_for(xy.bbox, size, 256),
                     buildings=True, fade=0.92)
    if not ok:
        return im, False

    # A scale bar, because a map without one only says "somewhere" — and on a
    # plan whose whole argument is that 400 m of wall costs a scooter a
    # kilometre, the reader needs the metres. Below about 300 px the bar and its
    # label eat the picture, so the small tile carries the credit alone.
    if size >= 300:
        map_ground.scale_bar(im, xy.px_per_km)
    map_ground.credit_mark(im)

    d = ImageDraw.Draw(im)
    # A hairline inside the edge: the ground now runs to the corners, and
    # without a rule it bleeds into whatever card the gif is sitting in.
    d.rectangle([0, 0, W - 1, H - 1], outline=(214, 198, 164),
                width=max(1, int(0.5 * SS)))
    return im, True


def frame(cfg, stops_xy, moat_xy, routes_xy, shown, ride_frac, foot_frac, pin_grow,
          labels_shown=0):
    """One frame. The scooter's line goes down solid and first, the walker's
    dashed over it, so where they agree you read one road and where they part
    company you read two."""
    W, H = cfg["W"], cfg["H"]
    im = cfg["base"].copy()
    d = ImageDraw.Draw(im)
    if not cfg["ground"]:
        dashed(d, moat_xy + [moat_xy[0]], MOAT, int(2.2 * SS), dash=7 * SS, gap=6 * SS)
    # Over a real basemap both route lines need a halo. On cream paper a 4 px
    # blue line was unmistakable; over a street grid drawn in the same family of
    # warm neutrals it becomes just another road. The halo is what makes the
    # route sit ON the city rather than in it.
    halo = (255, 252, 246) if cfg["ground"] else None
    if ride_frac > 0:
        for pth in routes_xy["ride"]:
            seg = walk(pth, ride_frac)
            if len(seg) > 1:
                if halo:
                    d.line(seg, fill=halo, width=int(6.6 * SS), joint="curve")
                d.line(seg, fill=RIDE, width=int(3.8 * SS), joint="curve")
    if foot_frac > 0:
        for pth in routes_xy["foot"]:
            seg = walk(pth, foot_frac)
            if len(seg) > 1:
                if halo:
                    dashed(d, seg, halo, int(6.2 * SS), dash=8 * SS, gap=5 * SS)
                dashed(d, seg, ANT, int(3.2 * SS), dash=8 * SS, gap=5 * SS)
    for i in range(min(labels_shown, len(cfg["slots"]))):
        if cfg["slots"][i]:
            draw_label(d, cfg["slots"][i], cfg["font_label"], cfg["label_pad"])
    return im


def pack(frames):
    """Quantise every frame against ONE palette, with no dithering.

    This is the whole reason a basemap can live in a gif at all. Left to
    itself Pillow picks a fresh palette per frame and dithers it, so the
    ground — which is identical in all forty-odd frames — comes out as a
    different speckle each time, nothing matches its neighbour, and the file
    goes from under a megabyte to ten. Quantised once against a shared palette
    with dithering off, the untouched ground is byte-identical frame to frame,
    which is exactly the case gif's delta frames were built for: the encoder
    ends up storing the pins and the growing line and nothing else.

    Dithering off costs a little banding on the landcover washes. On flat map
    fills that is invisible, and it buys a tenfold file.
    """
    master = frames[-1].convert("P", palette=Image.ADAPTIVE, colors=128)
    return [f.quantize(palette=master, dither=Image.Dither.NONE) for f in frames]


def write_facts(stops, legs, names):
    """The caption beside the tile quotes its own numbers, so it is written from
    the routes the frames are drawn from. A caption that can drift from the
    picture it captions is worse than no caption."""
    last = legs[-1]
    facts = {"crowM": round(hav_m(stops[-2], stops[-1])),
             "footM": round(last["foot"][0]),
             "rideM": round(last["ride"][0]),
             "footTotalM": round(sum(l["foot"][0] for l in legs)),
             "rideTotalM": round(sum(l["ride"][0] for l in legs)),
             "stops": names}
    (ROOT / "assets" / "plan-demo.json").write_text(
        json.dumps(facts, ensure_ascii=False, indent=1))
    return facts


def render(plan_name, plan, size=None, out=None):
    cm = {r["id"]: r for r in json.loads(
        (ROOT / "data" / "canonical" / "cm.json").read_text())}
    ids = [s[0] for s in plan["stops"]]
    captions = [s[1] for s in plan["stops"]]
    missing = [i for i in ids if i not in cm]
    if missing:
        raise SystemExit(f"unknown catalogue id(s): {', '.join(missing)}")
    stops = [(cm[i]["lat"], cm[i]["lng"]) for i in ids]
    names = [cm[i].get("name") for i in ids]
    corners = [(cm[i]["lat"], cm[i]["lng"]) for i in
               (__import__("build").MOAT_CORNER_IDS[k] for k in ("nw", "ne", "se", "sw"))]

    r = Router()
    legs = []
    for i in range(len(stops) - 1):
        entry = {}
        for mode in ("foot", "ride"):
            a = r.snap(stops[i], mode)
            b = r.snap(stops[i + 1], mode)
            m, line = r.route(a, b, mode)
            if m is None:
                raise SystemExit(f"leg {i + 1}→{i + 2} has no {mode} route — "
                                 "pick other stops or widen the graph")
            entry[mode] = (m, line)
        legs.append(entry)

    SIZE = size or plan["size"]
    W = H = SIZE * SS
    labels = plan.get("labels") and any(captions)
    cfg = {"W": W, "H": H, "captions": captions if labels else [None] * len(stops),
           "font_label": load_font(int(SIZE * 0.030) * SS // 1 or 12 * SS),
           "pin_r": int(SIZE * 0.055) * SS // 1}
    cfg["pin_r"] = max(9 * SS, int(SIZE * 0.052) * SS // 1) if SIZE < 300 else int(SIZE * 0.038) * SS // 1
    font_pin = digit_font(int(cfg["pin_r"] * 0.95))

    # Frame the stops and the roads the routes use — deliberately NOT the moat
    # corners. Including them pulls the whole 1.4 km square into the box, and the
    # two lines parting company, which is the entire point of the picture,
    # shrinks to a smudge. The moat gets drawn and clipped instead, the same way
    # plan.html's own map handles it.
    allpts = list(stops)
    for l in legs:
        for mode in ("foot", "ride"):
            allpts += l[mode][1]
    xy = projector(allpts, W, H, pad=0.34 if labels else 0.22)
    stops_xy = [xy(p) for p in stops]
    moat_xy = [xy(p) for p in corners]
    routes_xy = {m: [[xy(p) for p in l[m][1]] for l in legs] for m in ("foot", "ride")}
    # Label positions are settled once against a scratch canvas, so they do not
    # jitter from frame to frame as more of them appear.
    _probe = ImageDraw.Draw(Image.new("RGB", (W, H)))
    cfg["slots"], cfg["label_pad"] = plan_label_boxes(
        _probe, stops_xy, cfg["captions"], cfg["font_label"], W, H, cfg["pin_r"])
    cfg["base"], cfg["ground"] = base_image(cfg, xy, SIZE)

    frames, durs = [], []

    def shot(shown, rf, ff, grow, labs=0):
        im = frame(cfg, stops_xy, moat_xy, routes_xy, shown, rf, ff, grow, labs)
        d = ImageDraw.Draw(im)
        for i in range(shown):
            rr = cfg["pin_r"] * (grow if i == shown - 1 else 1.0)
            pin(d, stops_xy[i], i + 1, rr, font_pin)
        return im.resize((SIZE, SIZE), Image.LANCZOS)

    def add(im, ms):
        frames.append(im)
        durs.append(ms)

    n = len(stops)
    add(shot(0, 0, 0, 1), 520)
    for i in range(n):                          # each stop lands and settles
        for g in (0.45, 1.22, 1.0):
            add(shot(i + 1, 0, 0, g, i + 1 if labels else 0), 70)
        add(shot(i + 1, 0, 0, 1.0, i + 1 if labels else 0), 300 if n <= 3 else 240)
    L = n if labels else 0
    for k in range(1, 13):                      # the scooter's roads go down first
        add(shot(n, k / 12, 0, 1.0, L), 60)
    add(shot(n, 1, 0, 1.0, L), 420)
    for k in range(1, 13):                      # then the walking line over them
        add(shot(n, 1, k / 12, 1.0, L), 60)
    add(shot(n, 1, 1, 1.0, L), 2000)

    dest = ROOT / (out or plan["out"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    frames = pack(frames)
    frames[0].save(dest, save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, optimize=True, disposal=1)
    kb = dest.stat().st_size / 1024
    print(f"{dest.relative_to(ROOT)} — {len(frames)} frames, {SIZE}x{SIZE}, {kb:.0f} KB")
    for i in range(len(legs)):
        f_, r_ = legs[i]["foot"][0], legs[i]["ride"][0]
        crow = hav_m(stops[i], stops[i + 1])
        flag = "   <- the moat" if r_ > f_ * 1.2 else ""
        print(f"  leg {i + 1}→{i + 2}: crow {crow:4.0f} m · walk {f_:4.0f} m · ride {r_:4.0f} m{flag}")
    tf = sum(l["foot"][0] for l in legs)
    tr = sum(l["ride"][0] for l in legs)
    print(f"  whole run: walk {tf / 1000:.2f} km ({tf / 1000 / 4.6 * 60:.0f} min) · "
          f"ride {tr / 1000:.2f} km ({tr / 1000 / 18 * 60:.0f} min)")
    if plan_name == "tile":
        write_facts(stops, legs, names)
    return legs, names


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", default="tile", choices=sorted(PLANS) + ["all"])
    ap.add_argument("--stops", help="comma-separated catalogue ids, instead of a named plan")
    ap.add_argument("--size", type=int, help="pixels square")
    ap.add_argument("--out", help="output path, relative to the repo")
    a = ap.parse_args()
    if a.stops:
        plan = {"size": a.size or 560, "labels": False,
                "out": a.out or "assets/plan-custom.gif",
                "stops": [(s.strip(), None) for s in a.stops.split(",") if s.strip()]}
        render("custom", plan, a.size, a.out)
        return
    names = sorted(PLANS) if a.plan == "all" else [a.plan]
    for nm in names:
        render(nm, PLANS[nm], a.size, a.out)


if __name__ == "__main__":
    main()
