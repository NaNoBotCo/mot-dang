#!/usr/bin/env python3
"""Map doodles: drawn marks for places anywhere on earth, for every map on motdang.net and its minisites.

Nan, 2026-10-12: "Create a whole bunch of attribute doodles suitable for worldwide mapping
functionality in motdang and its mini sites. We should have eifel tower and easter island
heads ready to go, not emojis."

    python3 tools/map_doodles.py check                    # every svg/<id>.svg against the drawing contract
    python3 tools/map_doodles.py sheet [ids…] -o x.png    # a contact sheet at 96 px and 32 px (rsvg-convert)
    python3 tools/map_doodles.py build                    # map-doodles.svg (the sprite) from svg/ + the manifest
    python3 tools/map_doodles.py wikidata                 # landmarks: wikidata id, coordinates, fame rank

    from tools.map_doodles import match, img              # in a build layer: match({"amenity": "fuel"}) → "fuel-station"

Source: assets/sites/map-doodles/svg/<id>.svg, one drawing a file, and map-doodles.json, one
row a drawing. build writes the sprite; the gallery, the loader and every map read those two.

THE DRAWING CONTRACT (check refuses anything else)
    viewBox 0 0 64 64; the drawing stands on the bottom centre (32, 60), which is the map point
    <title>English · ไทย</title>, then shapes only: path rect circle ellipse polygon polyline line g
    colour written on each shape (fill= / stroke=); ink #2b2118; no text, no ids, no <use>, no style,
    no gradients or filters, so a canvas, MapLibre and an <img> all draw it the same
    under 3,000 bytes a file
"""
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "assets" / "sites" / "map-doodles"
SVG = SITE / "svg"
MANIFEST = SITE / "map-doodles.json"
SPRITE = SITE / "map-doodles.svg"
NS = "{http://www.w3.org/2000/svg}"
SHAPES = {"path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "g"}
ATTRS = {"d", "x", "y", "width", "height", "rx", "ry", "cx", "cy", "r", "points", "x1", "y1", "x2", "y2",
         "fill", "stroke", "stroke-width", "stroke-linejoin", "stroke-linecap", "stroke-dasharray",
         "opacity", "fill-opacity", "stroke-opacity", "transform", "fill-rule"}
PAPER = "#f5ecd7"
MAX_BYTES = 3000


def ids():
    return sorted(p.stem for p in SVG.glob("*.svg"))


def inner(text):
    """The drawing without its <svg> wrapper and <title>."""
    body = re.sub(r"^.*?<svg\b[^>]*>", "", text, count=1, flags=re.S)
    body = re.sub(r"</svg>\s*$", "", body.strip())
    return re.sub(r"<title>.*?</title>", "", body, flags=re.S).strip()


def check_one(path):
    """A list of what is wrong with one file (empty when it passes)."""
    bad = []
    text = path.read_text(encoding="utf-8")
    if len(text.encode()) > MAX_BYTES:
        bad.append("%d bytes (max %d)" % (len(text.encode()), MAX_BYTES))
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", path.stem):
        bad.append("id is not kebab-case")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return ["does not parse: %s" % e]
    if root.tag != NS + "svg":
        bad.append("root is not <svg> in the SVG namespace")
    if root.get("viewBox") != "0 0 64 64":
        bad.append("viewBox is %r" % root.get("viewBox"))
    title = root.find(NS + "title")
    if title is None or " · " not in (title.text or ""):
        bad.append("needs <title>English · ไทย</title>")
    elif not re.search(r"[฀-๿]", title.text):
        bad.append("title has no Thai")
    n = 0
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if el is root or tag == "title":
            continue
        n += 1
        if tag not in SHAPES:
            bad.append("<%s> not allowed" % tag)
        for a in el.attrib:
            if a not in ATTRS:
                bad.append("<%s %s=> not allowed" % (tag, a))
    if n < 3:
        bad.append("only %d shapes" % n)
    if "#2b2118" not in text:
        bad.append("no ink (#2b2118)")
    return bad


def cmd_check(args):
    man = {r["id"]: r for r in json.loads(MANIFEST.read_text())} if MANIFEST.exists() else {}
    fails = 0
    for i in (args or ids()):
        p = SVG / (i + ".svg")
        bad = check_one(p) if p.exists() else ["no file"]
        if man and i not in man:
            bad.append("not in map-doodles.json")
        if bad:
            fails += 1
            print("%-28s %s" % (i, "; ".join(bad)))
    if man and not args:
        for i in sorted(set(man) - set(ids())):
            fails += 1
            print("%-28s in map-doodles.json, no svg/%s.svg" % (i, i))
    print("%d checked, %d failing" % (len(args or ids()), fails))
    return 1 if fails else 0


def cmd_sheet(args):
    out = "sheet.png"
    if "-o" in args:
        k = args.index("-o")
        out = args[k + 1]
        args = args[:k] + args[k + 2:]
    names = args or ids()
    cols = 6
    cw, ch = 168, 176
    rows = (len(names) + cols - 1) // cols
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">' % (cols * cw, rows * ch),
             '<rect width="100%%" height="100%%" fill="%s"/>' % PAPER]
    for k, i in enumerate(names):
        x, y = (k % cols) * cw, (k // cols) * ch
        p = SVG / (i + ".svg")
        if not p.exists():
            parts.append('<text x="%d" y="%d" font-size="12" fill="#b00">missing %s</text>' % (x + 8, y + 60, i))
            continue
        body = inner(p.read_text(encoding="utf-8"))
        nest = ('<svg x="%d" y="%d" width="%d" height="%d" viewBox="0 0 64 64" stroke-linejoin="round" '
                'stroke-linecap="round">%s</svg>')
        parts.append(nest % (x + 8, y + 8, 112, 112, body))
        parts.append(nest % (x + 124, y + 46, 32, 32, body))
        parts.append('<text x="%d" y="%d" font-family="Helvetica" font-size="12" fill="#2b2118">%s</text>'
                     % (x + 8, y + 140, i))
        parts.append('<text x="%d" y="%d" font-family="Helvetica" font-size="10" fill="#7a6a58">%d bytes</text>'
                     % (x + 8, y + 156, len(p.read_bytes())))
    parts.append("</svg>")
    tmp = pathlib.Path(out).with_suffix(".svg")
    tmp.write_text("\n".join(parts), encoding="utf-8")
    subprocess.run(["rsvg-convert", "-o", out, str(tmp)], check=True)
    print(out)
    return 0


def cmd_build(args):
    man = json.loads(MANIFEST.read_text())
    have = set(ids())
    rows = [r for r in man if r["id"] in have]
    out = ['<svg xmlns="http://www.w3.org/2000/svg"><defs>']
    for r in rows:
        body = inner((SVG / (r["id"] + ".svg")).read_text(encoding="utf-8"))
        out.append('<symbol id="d-%s" viewBox="0 0 64 64" stroke-linejoin="round" stroke-linecap="round">%s</symbol>'
                   % (r["id"], body))
    out.append("</defs></svg>")
    SPRITE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("%s: %d drawings, %d KB" % (SPRITE.name, len(rows), SPRITE.stat().st_size // 1024))
    return 0


def cmd_wikidata(args):
    """Each landmark's wikidata id, coordinates and fame (Wikipedia editions) from its `wiki` title.
    The map shows the most-written-about first (rank 1 = most editions); Thailand's count three times,
    the map being motdang's. A row with "area": true links a broader article (the city, the film's
    river, the mountain the chedis stand on): it keeps its own point and takes no wikidata id."""
    import urllib.parse
    import urllib.request
    man = json.loads(MANIFEST.read_text())
    marks = [r for r in man if r.get("wiki") and not r.get("area")]

    def get(host, params):
        req = urllib.request.Request("https://%s/w/api.php?%s" % (host, urllib.parse.urlencode(params)),
                                     headers={"User-Agent": "motdang-map-doodles/1 (https://motdang.net)"})
        data = json.load(urllib.request.urlopen(req, timeout=60))
        if "error" in data:
            raise SystemExit("%s: %s" % (host, data["error"].get("info")))
        return data

    # English Wikipedia title (redirects followed) → wikidata id
    qid_of = {}
    for i in range(0, len(marks), 40):
        data = get("en.wikipedia.org", {"action": "query", "format": "json", "redirects": 1, "prop": "pageprops",
                                        "ppprop": "wikibase_item", "titles": "|".join(r["wiki"] for r in marks[i:i + 40])})
        q = data["query"]
        alias = {}
        for step in q.get("normalized", []) + q.get("redirects", []):
            alias[step["from"]] = step["to"]
        final = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in q["pages"].values()}
        for r in marks[i:i + 40]:
            t = r["wiki"]
            while t in alias:
                t = alias[t]
            if final.get(t):
                qid_of[r["id"]] = final[t]
    # wikidata id → coordinates, number of Wikipedia editions
    found = {}
    ids = sorted(set(qid_of.values()))
    for i in range(0, len(ids), 40):
        data = get("www.wikidata.org", {"action": "wbgetentities", "ids": "|".join(ids[i:i + 40]),
                                        "props": "claims|sitelinks", "format": "json"})
        for qid, ent in data.get("entities", {}).items():
            coord = None
            for cl in ent.get("claims", {}).get("P625", []):
                v = cl.get("mainsnak", {}).get("datavalue", {}).get("value")
                if v:
                    coord = (round(v["latitude"], 4), round(v["longitude"], 4))
                    break
            wikis = sum(1 for k in ent.get("sitelinks", {}) if k.endswith("wiki") and k != "commonswiki")
            found[qid] = (qid, coord, wikis)
    for r in marks:
        hit = found.get(qid_of.get(r["id"]))
        if not hit:
            print("%-28s no Wikidata item for %r" % (r["id"], r["wiki"]))
            continue
        qid, coord, n = hit
        r["wd"], r["fame"] = qid, n
        if coord:
            d = abs(coord[0] - r.get("lat", coord[0])) + abs(coord[1] - r.get("lng", coord[1]))
            if d > 0.5:
                print("%-28s moved %.2f° to Wikidata's %s" % (r["id"], d, coord))
            r["lat"], r["lng"] = coord
    ranked = [r for r in man if r.get("group") == "landmark"]
    for k, r in enumerate(sorted(ranked, key=lambda r: -r.get("fame", 0) * (3 if r.get("region") == "thailand" else 1)), 1):
        r["rank"] = k
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("%d landmarks, %d with wikidata" % (len(marks), sum(1 for r in marks if r.get("wd"))))
    return 0


# ── for build layers: a doodle for a place ───────────────────────────────────
_RULES = None


def match(tags=None, kind=None):
    """The doodle id for a place's OSM tags (or its wikidata), else for a motdang category; None if none fits.
    The same rules as MDDOODLES.match in map-doodles.js."""
    global _RULES
    if _RULES is None:
        man = json.loads(MANIFEST.read_text())
        rules = [([kv.split("=", 1) for kv in rule.split("+")], r["id"]) for r in man for rule in r.get("osm", [])]
        _RULES = (sorted(rules, key=lambda x: -len(x[0])), {r["wd"]: r["id"] for r in man if r.get("wd")})
    tags = tags or {}
    rules, wd = _RULES
    if tags.get("wikidata") in wd:
        return wd[tags["wikidata"]]
    for need, i in rules:
        if all((k in tags) if v == "*" else str(tags.get(k)) == v for k, v in need):
            return i
    return MD_KINDS.get(kind)


def img(i, px=40, alt=""):
    """An <img> for a page on motdang.net."""
    return ('<img class="md-doodle" src="/sites/map-doodles/svg/%s.svg" width="%d" height="%d" alt="%s" '
            'loading="lazy" decoding="async">' % (i, px, px, alt))


# motdang categories (mappins_layer.KINDS) → a doodle; map-doodles.js carries the same table
MD_KINDS = {
    "wat": "buddhist-temple", "food": "restaurant", "massage": "spa", "medical": "hospital", "cannabis": "cannabis",
    "essentials": "bank", "hotel": "hotel", "school": "school", "school-intl": "school", "market": "fresh-market",
    "shopping": "mall", "transport": "songthaew", "sport": "gym", "muaythai": "muay-thai", "cooking": "street-food",
    "chang": "elephant", "museums-galleries": "museum", "parks": "park", "sights": "viewpoint", "whats-on": "live-music",
}


def main():
    cmds = {"check": cmd_check, "sheet": cmd_sheet, "build": cmd_build, "wikidata": cmd_wikidata}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    return cmds[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
