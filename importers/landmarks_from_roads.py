#!/usr/bin/env python3
"""Landmarks — the gates, corners, bridges and named places of the old city —
minted as first-class Mot Dang places from the Roads of Chiang Mai corpus.

Nan, 2026-09-26: "if I'm searching for tha phae gate, I actually want the gate
up top, fully enriched. Should be LOTS of pictures and history." A gate was in
the data only as a landmark other listings borrowed (a car park "400 m from Tha
Phae Gate", a coworking space "Tha Phae Gate branch") — never as itself. This
turns the roads minisite's own records (assets/roads/api/{gate,place,bridge,
junction}/*.json — English + Thai history, an exact pin, Commons photographs
already downloaded) into curated Mot Dang place records under the `sights`
shelf.

Two tiers, by Nan's instruction (2026-09-26):
  * gates, corners, bridges, named places — ENRICHED: a sourced history block
    (roads `text.what` + `text.story`, cited, never invented), a photo gallery
    (the roads Commons images, copied with each photographer and licence), a
    lead photograph that also becomes the search thumbnail, and links out to
    the roads page and to Nan's own field photographs of the place.
  * junctions and underpasses — THIN: a real, findable place with a pin and the
    flag, no history and no gallery. Road infrastructure, not a thing to visit.

Writes  data/curated/landmarks-chiang-mai.json  (ingested by import_all.py),
copies photographs into assets/photos/, and merges the lead-photo credits into
assets/photos/credits.json so the built page and the fleet search both carry
the picture. Idempotent: safe to re-run; it rewrites its own outputs only.

    python3 importers/landmarks_from_roads.py
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROADS_API = ROOT / "assets" / "roads" / "api"
ROADS_IMG = ROOT / "assets" / "roads" / "images"
PHOTOS = ROOT / "assets" / "photos"
LAND_IMG = PHOTOS / "landmarks"           # gallery images, per landmark id
CREDITS = PHOTOS / "credits.json"
FIELD_SCENES = ROOT / "docs" / "field" / "scenes"
DOCS_ROADS = ROOT / "docs" / "roads"
OUT = ROOT / "data" / "curated" / "landmarks-chiang-mai.json"
TODAY = "2026-09-26"

# roads api folder -> (Mot Dang sub, the /roads/<dir>/ path, enrich?)
KINDS = {
    "gate":     ("gate",     "gates",     True),
    "place":    ("landmark", "places",    True),
    "bridge":   ("bridge",   "bridges",   True),
    "junction": ("junction", "junctions", False),
}

# The roads corpus grades a pin exact / street / town / … ; Mot Dang's place map
# reads geoPrecision. A landmark whose spot is known to the metre is exact; a
# river or a moat is a line, a district a shape — approx is the word for it, and
# the map widens itself rather than claim a doorway.
PRECISION = {"exact": "exact", "street": "approx", "town": "approx",
             "district": "approx", "area": "approx"}

# The GO-ASK guard (tests/test_no_blurbs.py) rejects prose that tells a reader
# to phone and ask, or that narrates a gap. Cited history does neither; the
# corpus is large enough to check rather than trust.
GO_ASK = re.compile(
    r"(ring and ask|call and ask|phone them|ring them|ask them|worth asking"
    r"|call (?:them|ahead|first)|phone (?:ahead|first)"
    r"|nobody has|no one has|we haven'?t"
    r"|ควรโทรถาม|โทรถาม(?!ก่อน)|ลองโทร|ยังไม่ได้ไป|ยังไม่มีใคร|ยังไม่ได้ยืนดู)",  # stylecheck: allow — a regex pattern
    re.I)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def field_scenes_for(landmark_id):
    """Nan's own field photographs of this landmark, as read-more links.

    Matched by the scene's own slug carrying the landmark id — the gate's
    scenes are tha-phae-gate, tha-phae-gate-mural-at-sunset, the fountain at
    tha-phae-gate-square. A scene names itself in its <h1>; we take that where
    we can read it, and fall back to the slug read plainly.
    """
    out = []
    if not FIELD_SCENES.exists():
        return out
    for d in sorted(FIELD_SCENES.iterdir()):
        if not d.is_dir() or landmark_id not in d.name:
            continue
        en = d.name.replace("-", " ").strip().capitalize()
        th = ""
        idx = d / "index.html"
        if idx.exists():
            html = idx.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            if m:
                t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                # The scene's h1 abuts its Thai and English names with no
                # separator ("ประตูท่าแพTha Phae Gate"). Split at the boundary
                # into the two names, so each link carries a clean pair.
                t = re.sub(r"([฀-๿])([A-Za-z])", r"\1\t\2", t)
                if "\t" in t:
                    th, en = (p.strip() for p in t.split("\t", 1))
                elif re.search(r"[฀-๿]", t):
                    th = t
                else:
                    en = t
        out.append({"url": f"/field/scenes/{d.name}/", "th": th, "en": en})
    return out


def copy_gallery(landmark_id, images):
    """Copy the roads Commons photographs into assets/photos/landmarks/<id>/,
    full frame and pre-made thumbnail, and return the gallery rows plus the
    primary (lead) image row. Nothing is downloaded; the files are already on
    disk under assets/roads/images/ with their licences recorded."""
    dest = LAND_IMG / landmark_id
    if dest.exists():
        shutil.rmtree(dest)
    gallery, primary = [], None
    for im in images:
        src = ROADS_IMG / im["file"]
        if not src.exists():
            print(f"  ! missing image on disk: {im['file']}", file=sys.stderr)
            continue
        dest.mkdir(parents=True, exist_ok=True)
        base = pathlib.Path(im["file"]).name
        shutil.copy(src, dest / base)
        thumb_src = src.with_name(src.stem + ".thumb" + src.suffix)
        thumb = None
        if thumb_src.exists():
            shutil.copy(thumb_src, dest / thumb_src.name)
            thumb = f"photos/landmarks/{landmark_id}/{thumb_src.name}"
        row = {
            "file": f"photos/landmarks/{landmark_id}/{base}",
            "thumb": thumb,
            "author": im.get("author") or "Wikimedia Commons",
            "license": im.get("license") or "",
            "licenseUrl": im.get("license_url") or "",
            "source": im.get("page_url") or im.get("url") or "",
            "alt": (im.get("alt") or "").strip().rstrip(")"),
        }
        gallery.append(row)
        if im.get("primary") and primary is None:
            primary = (im, base, src)
    if primary is None and images:
        # No image flagged primary: the first one that copied leads the page.
        im = images[0]
        base = pathlib.Path(im["file"]).name
        if (dest / base).exists():
            primary = (im, base, ROADS_IMG / im["file"])
    return gallery, primary


def history_of(rec):
    """The sourced history, English and Thai, from the roads record. `what`
    (a sentence placing the thing) then `story` (how it came to stand there),
    joined with a blank line so the template renders two paragraphs. Never
    invented — absent when the corpus is silent."""
    def join(block):
        if not block:
            return ""
        parts = [block.get("what", "").strip(), block.get("story", "").strip()]
        return "\n\n".join(p for p in parts if p)
    en = join(rec.get("text"))
    th = join(rec.get("text_th"))
    if not en and not th:
        return None
    h = {}
    if en:
        h["en"] = en
    if th:
        h["th"] = th
    return h


def build():
    LAND_IMG.mkdir(parents=True, exist_ok=True)
    credits = json.loads(CREDITS.read_text()) if CREDITS.exists() else {}
    records, warnings, n_enriched, n_thin, n_pics = [], [], 0, 0, 0

    for kind, (sub, roads_dir, enrich) in KINDS.items():
        src_dir = ROADS_API / kind
        if not src_dir.exists():
            continue
        for f in sorted(src_dir.glob("*.json")):
            rec = json.loads(f.read_text())
            rid = rec["id"]
            cid = f"cm-curated-{rid}"
            names = rec.get("names") or {}
            geo = rec.get("geo") or {}
            name_th = (names.get("th") or "").strip()
            name_en = (names.get("name") or "").strip()
            is_corner = rid.endswith("-corner")

            out = {
                "id": cid,
                "province": "cm",
                "cat": ["sights"],
                "sub": ["corner"] if is_corner else [sub],
                "name": name_th or name_en,
                "nameTh": name_th or None,
                "nameEn": name_en or None,
                "lat": geo.get("lat"),
                "lng": geo.get("lon"),
                "geoPrecision": PRECISION.get(geo.get("precision"), "approx"),
                "address": None,
                "phone": None,
                "website": None,
                "hours": None,
                "attrs": {},
                "featured": bool(enrich),
                "landmark": True,
                "sources": [{
                    "type": "curated",
                    "ref": f"/roads/{roads_dir}/{rid}/",
                    "credit": "Roads of Chiang Mai",
                    "fetched": rec.get("updated") or TODAY,
                }],
                # Mot Dang's provenance tier (import_all): curated sits above a
                # crawl, below a field visit. The roads record's own
                # medium/low is a different scale — source reliability — and is
                # kept on the source line, not mapped onto this one.
                "confidence": "curated",
                "updatedAt": TODAY,
            }

            # The road-building history page this record was drawn from.
            if (DOCS_ROADS / roads_dir / rid).exists() or True:
                out["attrs"]["roadsUrl"] = f"/roads/{roads_dir}/{rid}/"
            # Nan's own field photographs of the place.
            fs = field_scenes_for(rid)
            if fs:
                out["attrs"]["fieldScenes"] = fs

            if enrich:
                hist = history_of(rec)
                if hist:
                    out["history"] = hist
                    for lang, text in hist.items():
                        if GO_ASK.search(text):
                            warnings.append(f"{cid}: history.{lang} trips GO-ASK "
                                            f"— {GO_ASK.search(text).group(0)!r}")
                gallery, primary = copy_gallery(rid, rec.get("images") or [])
                if gallery:
                    out["gallery"] = gallery
                    n_pics += len(gallery)
                if primary:
                    im, base, srcpath = primary
                    lead = PHOTOS / f"{cid}.jpg"
                    shutil.copy(srcpath, lead)   # -> assets/photos/<id>.jpg
                    credits[cid] = {
                        "author": im.get("author") or "Wikimedia Commons",
                        "license": im.get("license") or "",
                        "licenseUrl": im.get("license_url") or "",
                        "source": im.get("page_url") or im.get("url") or "",
                        "credit": (f'{im.get("author") or "Wikimedia Commons"}, '
                                   f'{im.get("license") or ""}, via Wikimedia Commons'),
                    }
                n_enriched += 1
            else:
                n_thin += 1

            records.append(out)

    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1))
    CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1))

    print(f"landmarks: {len(records)} records "
          f"({n_enriched} enriched, {n_thin} thin) · {n_pics} gallery photos")
    print(f"  -> {OUT.relative_to(ROOT)}")
    print(f"  -> {LAND_IMG.relative_to(ROOT)}/  ·  lead photos in {PHOTOS.relative_to(ROOT)}/")
    if warnings:
        print("WARNINGS:")  # stylecheck: allow — console output
        for w in warnings:
            print("  " + w)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(build())
