#!/usr/bin/env python3
"""streetphoto_layer.py — a photograph at the pin. WO-79.

WHAT THIS DRAWS
---------------
One picture of the street a place stands on: on the place page, in the frame
that currently holds either a Commons photograph or the little drawn map, and
on the map's tap sheet, where a card today carries a name and a distance and
nothing you could recognise a shopfront by.

TWO SOURCES, IN THIS ORDER, AND THE ORDER IS THE POINT
------------------------------------------------------
  1. HER OWN PHOTOGRAPHS. `assets/streetphotos/own/`, geotagged out of their
     own EXIF by `scan_own()` below, served from our own bucket. No token, no
     account, no third party at any point in the chain — not at harvest, not
     at build, not at read. This is the path that owes nobody anything, and
     it wins wherever it has a picture.
  2. MAPILLARY, baked. `importers/harvest_mapillary.py` downloads the JPEG
     bytes onto our disk; build copies them into docs/, which is the R2
     bucket. A reader fetches from our origin like every other picture here.
     NO READER EVER TALKS TO META. That is the whole design and it is why
     hot-linking a Mapillary thumbnail is forbidden in the importer even as a
     fallback.

Compare what the site does today: the Commons photographs on place pages are
hot-linked to upload.wikimedia.org, so every reader of those pages tells
Wikimedia they are reading them. That is a live third-party request on a site
whose README says the last one was removed in August. Not this layer's to
fix, and named here so the next person does not assume it was already true.

THE CAPTURE DATE IS PART OF THE PICTURE
---------------------------------------
Mapillary's Chiang Mai coverage is old and patchy. A 2016 photograph of a soi
presented as what is there now is a false fact about a real place, and this
site's whole claim is that its facts carry when they were read. So:

  · every photograph prints its capture date, in Buddhist Era as the site
    does everywhere else, with the Gregorian year beside it;
  · past STALE_YEARS the caption says outright that the street may have
    changed, in words, not as a faded style somebody might not notice;
  · a photograph whose date is unknown says its date is unknown. It does not
    quietly omit the line, because an omitted date reads as a recent one.

The alt text says what a reader who cannot see it needs: that this is a
street-level view of where the place stands, whose photograph it is, and
when. It never describes what is in the frame, because nobody read the frame.

WHAT THIS DOES NOT DO
---------------------
It does not put a photograph on a listing to make the listing look complete,
and it never draws a photograph of a DIFFERENT place. A street photo taken
35 m away is a picture of the street, and the caption says "the street where
this stands", not "this place". The distinction is the same one
harvest_commons.py already makes and the same reason `wat.svg` is only ever
drawn on wat and sights.

Nothing here fetches. Nothing here is imported by build.py yet — the hook
lines are in notes/maps-grow-2026-09-08.txt §11.
"""

import json
import struct
import zlib
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWN_DIR = ROOT / "assets" / "streetphotos" / "own"
MLY_DIR = ROOT / "assets" / "streetphotos"
MLY_INDEX = ROOT / "data" / "street_photos.json"
OWN_INDEX = ROOT / "data" / "own_photos.json"

# Same threshold the importer picks with, for the same reason: past this the
# camera is looking at somebody else's shopfront.
NEAR_M = 35.0
STALE_YEARS = 5
BE_OFFSET = 543


# ── her own photographs: EXIF in, index out ──────────────────────────────────
# exif_gps.py already reads coordinates out of raw JPEG bytes, stdlib only,
# and is exercised by tests/test_exif_gps.py against JPEGs with known answers.
# This reuses it rather than writing a second EXIF reader, and adds the one
# tag it does not read: when the shutter fired.

def _exif():
    import sys
    p = str(ROOT / "importers")
    if p not in sys.path:
        sys.path.insert(0, p)
    import exif_gps
    return exif_gps


def taken(jpeg_bytes):
    """DateTimeOriginal (0x9003) as an ISO date, or None. Never guesses.

    Falls back to DateTime (0x0132) — the file's own timestamp — only when
    the original is absent, and that is a real distinction: DateTime is
    rewritten by editors, so it says when the file was last written, not when
    the picture was taken. Both are better than a file mtime, which says when
    it was copied onto this laptop.
    """
    ex = _exif()
    tiff = ex._app1(jpeg_bytes)
    if not tiff or len(tiff) < 8:
        return None
    bo = ">" if tiff[:2] == b"MM" else "<" if tiff[:2] == b"II" else None
    if not bo:
        return None
    (ifd0,) = struct.unpack(bo + "I", tiff[4:8])
    best = fallback = None
    sub = None
    for tag, typ, cnt, raw in ex._entries(tiff, ifd0, bo):
        v = ex._read(tiff, typ, cnt, raw, bo)
        if tag == 0x8769:
            sub = v[0] if v else None
        elif tag == 0x0132:
            fallback = v
    if sub:
        for tag, typ, cnt, raw in ex._entries(tiff, sub, bo):
            if tag == 0x9003:
                best = ex._read(tiff, typ, cnt, raw, bo)
    return _exif_date(best) or _exif_date(fallback)


def _exif_date(v):
    """'2023:11:14 09:31:02' -> '2023-11-14'. Anything else -> None."""
    if not v:
        return None
    s = str(v).strip().strip("\x00")
    if len(s) < 10:
        return None
    head = s[:10].replace(":", "-")
    try:
        datetime.strptime(head, "%Y-%m-%d")
    except ValueError:
        return None
    return head


def scan_own(folder=None, records=None, near_m=NEAR_M):
    """Every geotagged JPEG in the folder, matched to its nearest record.

    Returns (index, unmatched). A photo with no coordinates is UNMATCHED, not
    dropped and not attached to a guess — the exif_gps docstring is emphatic
    about why, and it applies doubly here: a street photo pinned to the wrong
    shop is a picture of the wrong shop with a real business's name under it.

    LINE strips EXIF from anything sent as a *photo* and keeps it on anything
    sent as a *file*. That is measured (exif_gps, 2026-09-07) and it is the
    single most likely reason this returns nothing: the pictures arrived the
    wrong way, not the code failed. `unmatched` says which, and why.
    """
    folder = Path(folder or OWN_DIR)
    idx, unmatched = {}, []
    if not folder.exists():
        return idx, unmatched
    recs = [r for r in (records or [])
            if r.get("lat") is not None and r.get("lng") is not None]
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg"):
            continue
        raw = f.read_bytes()
        pt = _exif().gps(raw)
        if not pt:
            unmatched.append({"file": f.name, "why": "no GPS tag in the file "
                              "(sent through LINE as a photo, or the camera "
                              "had location off)"})
            continue
        lat, lng = pt
        best, bd = None, 1e9
        for r in recs:
            d = _metres(lat, lng, r["lat"], r["lng"])
            if d < bd:
                bd, best = d, r
        if not best or bd > near_m:
            unmatched.append({"file": f.name, "why": "nothing on the catalogue "
                              "within %.0f m of %.5f,%.5f" % (near_m, lat, lng),
                              "lat": lat, "lng": lng})
            continue
        idx[best["id"]] = {
            "placeId": best["id"], "file": f.name, "own": True,
            "captured": taken(raw),
            "lat": lat, "lng": lng, "distanceM": round(bd, 1),
            # Her own photograph. No licence line, no photographer credit, no
            # third party — those exist to satisfy somebody else's terms and
            # there is nobody else here.
            "by": None, "licence": None, "source": None,
        }
    return idx, unmatched


def _metres(lat1, lng1, lat2, lng2):
    import math
    r = 6371000.0
    dlat, dlng = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


# ── the merged table build.py reads ──────────────────────────────────────────

def load(own_index=None, mly_index=None):
    """{place id: photo}. Her own photographs win, always.

    Both files missing is the normal state today and returns {} — a site that
    fell over because an optional index was absent would be a site that
    cannot be built on a fresh clone.
    """
    out = {}
    mly = Path(mly_index or MLY_INDEX)
    if mly.exists():
        try:
            for pid, p in (json.loads(mly.read_text()).get("photos") or {}).items():
                q = dict(p)
                q["own"] = False
                q.setdefault("dir", "streetphotos")
                out[pid] = q
        except (ValueError, OSError):
            pass
    own = Path(own_index or OWN_INDEX)
    if own.exists():
        try:
            for pid, p in (json.loads(own.read_text()).get("photos") or {}).items():
                q = dict(p)
                q["own"] = True
                q.setdefault("dir", "streetphotos/own")
                out[pid] = q            # overwrites Mapillary. Deliberate.
        except (ValueError, OSError):
            pass
    return out


# ── the display ──────────────────────────────────────────────────────────────

def _be(iso):
    """A year the way this site writes years everywhere else."""
    try:
        y = int(iso[:4])
    except (TypeError, ValueError):
        return None
    return "%d (%d)" % (y + BE_OFFSET, y)


def is_stale(iso, today=None, years=STALE_YEARS):
    """Unknown counts as stale: we cannot say a photograph is current."""
    if not iso:
        return True
    today = today or date.today()
    try:
        d = datetime.strptime(iso[:10], "%Y-%m-%d").date()
    except ValueError:
        return True
    return (today - d).days > years * 365.25


def when_line(photo, g, today=None):
    """The date, in words, always. Three shapes and no fourth."""
    bi = g["bi"]
    iso = (photo or {}).get("captured")
    if not iso:
        return bi("ไม่รู้ว่าถ่ายเมื่อไหร่ — อาจเก่ามาก",
                  "Date of this photograph unknown — it may be very old")
    be = _be(iso)
    if is_stale(iso, today):
        return bi("ถ่ายเมื่อ พ.ศ. %s — ตอนนี้หน้าร้านอาจเปลี่ยนไปแล้ว" % be,
                  "Taken in %s — the street may have changed since" % be)
    return bi("ถ่ายเมื่อ พ.ศ. %s" % be, "Taken in %s" % be)


def credit_line(photo, g):
    """Attribution. CC BY-SA is a condition of use, not a courtesy — the same
    sentence build.py already writes about the Commons pictures.

    A Mapillary photo with no photographer name never reaches here: the
    importer drops it rather than crediting it to a company."""
    bi, esc, att = g["bi"], g["esc"], g["att"]
    if not photo:
        return ""
    if photo.get("own"):
        # Hers. Named as hers, and nothing else — no licence line, because
        # there is no third party whose terms need satisfying.
        return ('<span class="stcred">%s</span>'
                % bi("ภาพถ่ายของมดแดงเอง", "Our own photograph"))
    by, lic = photo.get("by"), photo.get("licence")
    if not by or not lic:
        return ""
    src = photo.get("source") or ""
    who = ('<a href="%s" rel="noopener nofollow">%s</a>'
           % (att(photo.get("byUrl") or src), esc(by))) if (photo.get("byUrl") or src) else esc(by)
    lict = ('<a href="%s" rel="noopener nofollow license">%s</a>'
            % (att(photo["licenceUrl"]), esc(lic))) if photo.get("licenceUrl") else esc(lic)
    where = ('<a href="%s" rel="noopener nofollow">%s</a>'
             % (att(src), esc(photo.get("sourceName") or "Mapillary"))) if src else ""
    bits = [who, lict] + ([where] if where else [])
    return '<span class="stcred">%s</span>' % " · ".join(bits)


def alt_text(photo, rec, g):
    """What a reader who cannot see it is owed: what kind of picture this is,
    whose it is, and when. Never what is in the frame — nobody read the
    frame, and inventing a description is inventing a fact."""
    bi_text = g["bi_text"]
    name = g["name_th"](rec), g["name_en"](rec)
    who = (photo or {}).get("by")
    iso = (photo or {}).get("captured")
    yr = (" พ.ศ. %s" % _be(iso)) if iso else ""
    yr_en = (" in %s" % _be(iso)) if iso else ""
    return bi_text(
        "ภาพถนนตรงที่ %s ตั้งอยู่%s%s" % (name[0] or name[1] or "",
                                          (" ถ่ายโดย %s" % who) if who else "", yr),
        "A street-level view of where %s stands%s%s"
        % (name[1] or name[0] or "", (", by %s" % who) if who else "", yr_en))


def figure_html(rec, photo, g, depth=2):
    """The whole block for a place page. Empty string when there is no
    photograph — the caller keeps whatever it draws today."""
    if not photo or not photo.get("file"):
        return ""
    att, bi = g["att"], g["bi"]
    up = "../" * depth
    src = "%s%s/%s" % (up, photo.get("dir") or "streetphotos", photo["file"])
    cred = credit_line(photo, g)
    d = photo.get("distanceM")
    # THE CAPTION SAYS "THE STREET", NOT "THIS PLACE". A frame taken 30 m up
    # the soi is a picture of the soi, and saying otherwise would put a shop
    # in a photograph nobody checked it was in.
    near = ""
    if isinstance(d, (int, float)) and d >= 1:
        near = bi(" (ถ่ายห่างออกไป %d ม.)" % round(d),
                  " (taken %d m away)" % round(d))
    return (
        '<figure class="stfig">'
        '<img class="photo stphoto" src="%s" alt="%s" loading="lazy" '
        'decoding="async">'
        '<figcaption class="stcap">%s%s<br>%s%s</figcaption>'
        '</figure>'
        % (att(src), att(alt_text(photo, rec, g)),
           bi("ถนนตรงที่นี่ตั้งอยู่", "The street where this stands"), near,
           when_line(photo, g), (" · " + cred) if cred else ""))


CSS = """/* streetphoto_layer — a photograph at the pin. */
.stfig{margin:0 0 .8rem}
.stphoto{width:100%;height:auto;border-radius:.4rem;display:block}
.stcap{font-size:.82rem;color:var(--ink-soft);margin:.3rem 0 0;line-height:1.5}
/* The credit is a condition of the licence, so it is never smaller than the
   caption it sits in and never grey enough to skim past. */
.stcred{color:var(--ink-soft)}
.stcred a{color:inherit}
/* On the map sheet the picture is a strip, not a portrait: the sheet is
   already short and a tall photo pushes the name and the phone number off
   a phone screen. */
.mdcard .stphoto{max-height:132px;object-fit:cover}
.mdcard .stcap{font-size:.76rem}
@media print{.stfig{break-inside:avoid}}
"""

# The sheet variant.
#
# TWO THINGS ABOUT MDCARD THAT THIS HAD TO BE WRITTEN AROUND, both read out
# of build.py rather than assumed:
#
#  1. MDCARD.show() has NO photo slot. Its card is name / sub / meta / two
#     buttons, and an unknown key on the item object is silently ignored. So
#     this does not pass `photo` and hope — it puts the <img> into the card's
#     own DOM after show() has drawn it. A first draft passed opts.photo and
#     would have done nothing at all, forever, without erroring.
#  2. tap.js (tapcard.py) REPLACES window.MDCARD after md.js defines it, and
#     build.py's own comment says every caller must ask for the card by name
#     at the moment of the touch. So this wraps on DOMContentLoaded — after
#     every deferred script has run — and wraps whichever card won.
JS = r"""/* streetphoto.js — the photo at the pin, on the map's tap sheet.

   NOTHING HERE FETCHES FROM ANYBODY ELSE. `data/street_photos.json` is on
   our own origin and holds only what was baked; the JPEGs are ours too. A
   reader who opens a tap sheet makes one request, to the same host that
   served the page. */
(function(){
var TAB=null,loading=false,pending=[];
function root(){return document.documentElement.getAttribute('data-root')||'';}
function load(then){
  if(TAB)return then(TAB);
  pending.push(then);
  if(loading)return;
  loading=true;
  fetch(root()+'data/street_photos.json').then(function(r){return r.json();})
    .then(function(d){TAB=d.photos||{};})
    /* No index, no photos, no noise. The sheet is complete without one. */
    .catch(function(){TAB={};})
    .then(function(){
      loading=false;
      var q=pending;pending=[];
      q.forEach(function(fn){fn(TAB);});
    });
}
/* Draw into the card MDCARD has already built. Removed first, every time:
   a card reused for the next pin must never keep the last pin's picture. */
function draw(p){
  var card=document.querySelector('.mdcard .mdcard-in');
  if(!card)return;
  var old=card.querySelector('.stfig');
  if(old)old.remove();
  if(!p||!p.file)return;
  var fig=document.createElement('figure');
  fig.className='stfig';
  var img=document.createElement('img');
  img.className='photo stphoto';
  img.src=root()+(p.dir||'streetphotos')+'/'+p.file;
  img.alt='';                 /* the caption below says it in words */
  img.loading='lazy';img.decoding='async';
  fig.appendChild(img);
  if(p.capLine){
    var cap=document.createElement('figcaption');
    cap.className='stcap';
    /* textContent, not innerHTML: the caption carries a photographer's
       own username and a username is somebody else's text. */
    cap.textContent=p.capLine;
    fig.appendChild(cap);
  }
  var name=card.querySelector('.mdcard-name');
  card.insertBefore(fig,name||card.firstChild);
}
function wrap(){
  var C=window.MDCARD;
  if(!C||C.__stwrapped)return;
  var show=C.show;
  C.show=function(opts,host){
    var r=show(opts,host);
    var id=opts&&opts.id;
    if(!id){draw(null);return r;}
    load(function(tab){draw(tab[id]);});
    return r;
  };
  C.__stwrapped=true;
}
/* AFTER every deferred script, so this wraps the card tap.js installed and
   not the one md.js defined and tap.js then threw away. */
if(document.readyState==='loading')
  document.addEventListener('DOMContentLoaded',wrap);
else wrap();
})();
"""


def version():
    return "%08x" % (zlib.crc32((JS + CSS).encode("utf-8")) & 0xFFFFFFFF)


def emit(g):
    """Copy the photographs into docs/ and write the sheet's script.

    Called from build.py's asset pass — the hook lines are in
    notes/maps-grow-2026-09-08.txt §11 and are NOT applied here.
    """
    import shutil
    docs = g["DOCS"]
    table = load()
    n = 0
    for pid, p in table.items():
        sub = p.get("dir") or "streetphotos"
        src = ROOT / "assets" / sub / p["file"]
        if not src.exists():
            continue
        dest = docs / sub / p["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        n += 1
    # The table the sheet reads, with the caption already worded so the
    # browser never has to decide what "stale" means.
    out = {}
    for pid, p in table.items():
        q = {k: p.get(k) for k in ("file", "dir", "by", "byUrl", "licence",
                                   "licenceUrl", "source", "captured", "own")}
        q["capLine"] = g["bi_text"](*_cap_pair(p))
        out[pid] = q
    (docs / "data").mkdir(exist_ok=True)
    (docs / "data" / "street_photos.json").write_text(
        json.dumps({"generated": datetime.now(tz=timezone.utc)
                    .isoformat(timespec="seconds"), "photos": out},
                   ensure_ascii=False))
    (docs / "streetphoto.js").write_text(JS)
    return {"photos": n, "own": sum(1 for p in table.values() if p.get("own"))}


def _cap_pair(photo):
    """(th, en) for the sheet's one-line caption: date, staleness, credit."""
    iso = photo.get("captured")
    be = _be(iso) if iso else None
    if photo.get("own"):
        who_th, who_en = "ภาพของมดแดงเอง", "our own photograph"
    else:
        who_th = who_en = "%s · %s" % (photo.get("by") or "?",
                                       photo.get("licence") or "")
    if not iso:
        return ("ไม่รู้ปีที่ถ่าย · %s" % who_th,
                "date unknown · %s" % who_en)
    if is_stale(iso):
        return ("พ.ศ. %s — อาจเปลี่ยนไปแล้ว · %s" % (be, who_th),
                "%s — may have changed · %s" % (be, who_en))
    return ("พ.ศ. %s · %s" % (be, who_th), "%s · %s" % (be, who_en))


if __name__ == "__main__":
    import sys
    tab = load()
    sys.stderr.write("street photos on disk: %d (%d hers, %d Mapillary)\n"
                     % (len(tab), sum(1 for p in tab.values() if p.get("own")),
                        sum(1 for p in tab.values() if not p.get("own"))))
    if not tab:
        sys.stderr.write(
            "Nothing yet. Either:\n"
            "  python3 importers/harvest_mapillary.py --bbox w,s,e,n  "
            "(needs MAPILLARY_TOKEN, which is Nan's to make)\n"
            "  or drop geotagged JPEGs into assets/streetphotos/own/ and run "
            "scan_own() — no token, no third party.\n")
