#!/usr/bin/env python3
"""Turn Nan's hand-picked pictures into a licensed, local catalogue of city art.

This is not the place-photo pipeline. `harvest_commons.py` answers "is there a
free photograph OF this shop", and has to prove identity before it will use one.
This answers a different question — "what does Chiang Mai look like" — for the
site's own furniture: the hero, the category cards, the section art. A picture
of a red songthaew belongs at the top of the transport shelf whether or not it
is that particular songthaew, so identity is not the test here. Her eye is.

She sent the picks two ways, and both are handled:

  https://share.google/<id>          a shared Google Image result
  https://commons.wikimedia.org/...  a Commons file page, any URL shape

Google Images licenses nothing — it is an index. What makes the share links
usable is that every one of hers lands on Wikimedia Commons, where the licence
and the photographer arrive as facts attached to the file. Anything resolving
somewhere else is reported and dropped; it is never guessed at.

The files are DOWNLOADED, not hotlinked. Two reasons. The site tells readers in
five places that it follows no one around, and an image served from someone
else's CDN hands that reader's address to a third party on every page view.
And this art appears in the page furniture, so hotlinking would put the whole
site's appearance at the mercy of a URL we do not control.

    python3 importers/import_image_picks.py            # resolve + fetch metadata
    python3 importers/import_image_picks.py --download  # ...and pull the files
    python3 importers/import_image_picks.py --refresh   # ignore the cache

Reads  data/curated/image_picks_sources.txt
Writes data/curated/image_picks.json   (merged — hand-added keys survive)
       assets/site/<slug>.jpg          (with --download)
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "data", "curated", "image_picks_sources.txt")
OUT = os.path.join(ROOT, "data", "curated", "image_picks.json")
CACHE = os.path.join(ROOT, "cache", "imagepicks")
ART = os.path.join(ROOT, "assets", "site")
API = "https://commons.wikimedia.org/w/api.php"

UA = ("mot-dang-directory/1.0 (+https://motdang.net; cataloguing hand-picked "
      "freely-licensed city photographs; contact 530kings@proton.me)")
# Google answers a share link with an empty shell unless it believes a person is
# asking. This is the one request in the pipeline that has to look like a
# browser, and it only ever reads back a link the user already holds.
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PAUSE = 0.5
WIDTH = 1000          # what we ask Commons for
LONGEST = 1100        # what we keep: the hero shows ~1000 CSS px, cards ~300

# Licences we will actually publish. Anything else is catalogued with its
# verdict so the reason is on the record, but never handed to build.py.
OK_LICENCE = re.compile(r"^(cc[ -]?(by|zero|0)|public domain|pd|cc[ -]?by[ -]?sa)", re.I)

SHARE = re.compile(r"share\.google/([A-Za-z0-9_-]+)")
FILEPAGE = re.compile(r"commons\.wikimedia\.org/wiki/(File:[^\s\"'#&\\]+)", re.I)
# Some share pages quote the image bytes without ever naming the file page they
# came from. The filename is still in the path, and on Commons the filename IS
# the title — so the pick is recoverable rather than lost. Both shapes:
#   /wikipedia/commons/c/c8/Name.jpg
#   /wikipedia/commons/thumb/8/8c/Name.jpg/1280px-Name.jpg
UPLOAD = re.compile(
    r"upload\.wikimedia\.org/wikipedia/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/"
    r"([^\s\"'/?#\\]+\.(?:jpe?g|png|gif|svg|webp|tif+))", re.I)


def get(url, ua=UA, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def api(params):
    params = dict(params, format="json", formatversion="2")
    return json.loads(get(API + "?" + urllib.parse.urlencode(params)).decode("utf-8"))


def strip_html(s):
    """extmetadata values are HTML fragments — a credit line is often a link."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def file_title(raw):
    """Pull a `File:...` title out of any shape of Commons URL she might send."""
    m = FILEPAGE.search(raw)
    if m:
        title = urllib.parse.unquote(m.group(1))
    else:
        m = UPLOAD.search(raw)
        if not m:
            return None
        # A thumb path repeats the name; the first capture is the real file.
        title = "File:" + urllib.parse.unquote(m.group(1))
    # `#/media/File:X` repeats the title; `?uselang=th` and friends are noise.
    title = title.split("?")[0].replace("_", " ").strip()
    return title


def resolve_share(sid, cache, refresh=False):
    """A share link is an index entry. Follow it to whatever it actually indexes."""
    if not refresh and sid in cache:
        return cache[sid]
    url = "https://www.google.com/share.google?q=" + urllib.parse.quote(sid)
    try:
        body = get(url, ua=BROWSER_UA, timeout=30).decode("utf-8", "replace")
    except Exception as e:                                   # noqa: BLE001
        cache[sid] = {"ok": False, "why": "fetch failed: %s" % e}
        return cache[sid]
    title = file_title(body)
    if title:
        cache[sid] = {"ok": True, "title": title}
    else:
        # Say where it went, so a non-Commons pick is a fact she can act on
        # rather than a silent omission.
        host = re.search(r'"(https?://([a-z0-9.-]+)/[^"]{6,120})"', body)
        cache[sid] = {"ok": False, "why": "not a Commons file",
                      "landed": host.group(2) if host else "unknown"}
    time.sleep(PAUSE)
    return cache[sid]


# --------------------------------------------------------------- the four axes
# Nan's ask: usable by topic, by season, by location, to set a mood. The buckets
# below were written AFTER reading all 151 resolved titles, not before — the
# same rule the food subcategories were rebuilt under. Every term here earns its
# place from something actually in the set.
#
# Matching is on title + description, both lowercased. An entry can carry
# several topics; that is the point, since a picture of monks releasing lanterns
# is a temple picture and a festival picture and belongs on both shelves.
TOPICS = {
    "food": ("khao soi", "khaosoi", "som tam", "somtam", "phat thai", "pad thai",
             "roti", "thua paep", "nam phrik", "cuisine", "larb", "laap", "mohinga",
             "nasi", "riz", "rice", "street food", "food court", "restaurant",
             "cooking class", "khantoke", "latte", "coffee", "vegetarian", "soup",
             "salad", "kai yang", "crispy pork", "kluai khai"),
    # "templo" and "tempel" earn their place: her picks came from Commons, whose
    # uploaders describe things in their own languages.
    "wat": ("wat ", "temple", "templo", "tempel", "monk", "buddha", "chedi",
            "pagoda", "phrathat", "prathat", "stupa", "naga", "ordination",
            "วัด", "พระธาตุ"),
    "faith": ("mosque", "masjid", "church", "shrine", "มัสยิด"),
    "stay": ("hostel", "hotel", "guesthouse", "resort", "room", "โรงแรม"),
    "mu": ("sak yant", "yant", "tattoo", "spirit house", "spirit-house",
           "spirit-offerings", "spirit ", "amulet", "shrine", "religious goods",
           "indra", "opium"),
    "festival": ("songkran", "krathong", "yi peng", "lantern", "โคม",
                 "poy sang long", "phansa", "flower festival", "new year",
                 "baci", "procession", "cremation", "สงกรานต์"),
    "market": ("market", "bazaar", "walking street", "warorot", "kad ", "ตลาด"),
    "night": ("night", "cabaret", "party", "dancing", "bar ", "evening"),
    "nature": ("waterfall", "mekong", "national park", "river", "doi ", "montage",
               "flower", "orchid", "junglefowl", "น้ำตก"),
    "people": ("akha", "lahu", "karen", "lisu", "meo", "hmong", "tribe", "tribal",
               "villag", "kindje", "woman", "girls"),
    "arts": ("dance", "ramayana", "music", "seung", "museum", "folklife",
             "graffiti", "art ", "fresco", "ceramic", "mural", "statue",
             "monument", "vaporwave", "kinnaree", "tung", "montage",
             "black house", "baan dum", "thawan", "duchanee", "kositpipat"),
    "sport": ("muay", "boxing", "thai-boxing"),
    "wellness": ("massage", "spa "),
    "transport": ("bus", "songthaew", "red car", "bike", "fiets", "cruise",
                  "anywheel", "railway", "station", "รถแดง"),
    "animals": ("elephant", "buffalo", "junglefowl", "myna", "coucal", "ช้าง"),
    "city": ("moat", "city wall", "gate", "clock tower", "bridge", "kamphaeng",
             "กำแพงเมือง", "หอนาฬิกา", "คูเมือง", "three kings"),
    "history": ("1945", "1976", "opium", "naresuan", "ancient", "ruin", "1830"),
}
# Northern Thailand has three seasons, not four, and everyone here names them:
# ฤดูร้อน hot, ฤดูฝน rains, ฤดูหนาว cool. Festivals fix a picture to one of them
# more reliably than any visual cue could.
SEASONS = {
    "hot": ("songkran", "poy sang long", "สงกรานต์"),          # Mar–May
    "rains": ("phansa", "waterfall", "น้ำตก", "green", "rice paddy"),   # Jun–Oct
    "cool": ("krathong", "yi peng", "lantern", "โคม", "flower festival",
             "new year", "mist", "montage"),                    # Nov–Feb
}
PLACES = {
    "cm": ("chiang mai", "chiangmai", "chiang-mai", "เชียงใหม่", "doi suthep",
           "doi inthanon", "wualai", "warorot", "nimman", "suandok", "chedi luang",
           "phra singh", "tonkwen", "pha lat"),
    "cr": ("chiang rai", "chiangrai", "เชียงราย", "rong khun", "rong suea ten",
           "golden triangle", "sop ruak", "baan dum", "black house", "mae salong",
           "maejantai", "white temple", "blue temple", "mekong"),
    "lanna": ("lanna", "phayao", "lamphun", "lampang", "ล้านนา", "พะเยา"),
}
# What the picture is FOR, emotionally — the thing she asked for last. A mood
# follows from the topics rather than being guessed at separately.
MOOD_FROM_TOPIC = {
    "food": "appetite", "market": "streetlife", "transport": "streetlife",
    "people": "streetlife", "wat": "sacred", "mu": "sacred", "faith": "sacred",
    "stay": "calm",
    "festival": "festive", "arts": "festive", "sport": "festive",
    "night": "neon", "nature": "green", "animals": "green",
    "city": "landmark", "history": "landmark", "wellness": "calm",
}


# Seven of her picks are named things like "Chiang Mai photo-66.jpg" and
# described as "Photo I took in Chiang Mai". No matcher can read those, so they
# were tagged by opening them and looking. Worth knowing why this matters: the
# design study assigned pictures by filename and captioned photo-7544 as ของกิน
# and as a khao soi shop — it is a spirit house with red Fanta on it — and
# photo-68, a green spirit house, as Warorot Market. A picture that says the
# wrong thing about a place is the same fault as a wrong phone number, and the
# reason harvest_commons.py has to prove identity before it uses anything.
HAND_TAGS = {
    "chiang-mai-photo-7544": (["mu"], "ศาลพระภูมิ มีน้ำแดงถวาย",
                              "a spirit house with red drinks set out for it"),
    "chiang-mai-photo-7498": (["mu"], "ศาลพระภูมิ ล้อมด้วยตุ๊กตาและพวงมาลัย",
                              "a spirit house crowded with figurines and garlands"),
    "chiang-mai-photo-68": (["mu"], "ศาลพระภูมิสีเขียว หน้าร้าน",
                            "a bright green spirit house outside a shopfront"),
    "chiang-mai-717": (["mu"], "ศาลเจ้าที่หลังใหญ่ ประดับดอกดาวเรือง",
                       "a large roadside shrine dressed in marigold garlands"),
    "chiang-mai-photo-66": (["wat", "arts"], "ปูนปั้นมอมเฝ้าบันไดวัด",
                            "a white stucco guardian on a temple stair"),
    "dara-thong2": (["food"], "ดาราทอง (ทองเอกกระจัง) ขนมไทยปิดทองคำเปลว",
                    "dara thong, a Thai sweet finished with gold leaf"),
    "lanna-chiang-mai": (["arts", "history"], "แผนที่เขตล้านนาในภาคเหนือ",
                         "a map of the Lanna districts of the north"),
}


def classify(e):
    """Tag one pick on all four axes. Everything is derived and re-derivable;
    a hand-set value in data/curated/ overrides it on the next merge."""
    hay = (" " + e["title"][5:] + " " + e.get("description", "") + " ").lower()
    # Commons filenames join words with any of these. Leaving hyphens in place
    # cost 6 pictures a topic on the first pass — "Thai-Cooking-Class" simply
    # does not contain "cooking class".
    for ch in "_-.":
        hay = hay.replace(ch, " ")
    e["topic"] = [k for k, terms in TOPICS.items() if any(t in hay for t in terms)]
    hand = HAND_TAGS.get(e["slug"])
    if hand:
        e["topic"], e["caption_th"], e["caption_en"] = hand[0], hand[1], hand[2]
        e["tagged_by"] = "eye"
    e["season"] = [k for k, terms in SEASONS.items() if any(t in hay for t in terms)]
    place = [k for k, terms in PLACES.items() if any(t in hay for t in terms)]
    # Said plainly rather than assumed: several of her picks are of the dish or
    # the custom rather than of this city — a Lanna restaurant in Germany, a
    # baci in Laos, a massage in Cambodia. They are fine as mood, and wrong as
    # "here", so the caption writer is told which is which instead of guessing.
    e["place"] = place or ["elsewhere"]
    moods = []
    for t in e["topic"]:
        m = MOOD_FROM_TOPIC.get(t)
        if m and m not in moods:
            moods.append(m)
    if "night" in e["topic"] and "neon" in moods:
        moods = ["neon"] + [m for m in moods if m != "neon"]
    e["mood"] = moods
    return e


def slug_for(title, taken=None):
    """A readable ASCII filename, and never two different pictures sharing one.

    ASCII for the reason place_slug is: git on macOS renormalizes Unicode
    filenames and the mismatch is a 404 after deploy. Truncating at 60 is what
    keeps them readable — and it is also what made
    "Baan Dum ... Chiang Rai - Thailand - 03" and "- 20" the same slug, so one
    file overwrote the other and one catalogue entry then named the wrong
    photographer. A short digest of the FULL title breaks the tie; it only
    appears where a collision actually happens, so no existing name moves.
    """
    s = title[5:] if title.lower().startswith("file:") else title
    s = os.path.splitext(s)[0].lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    base = (s[:60] or "pic").strip("-")
    if taken is None or taken.get(base, title) == title:
        return base
    return "%s-%08x" % (base[:51].strip("-"), zlib.crc32(title.encode()))


def shrink(path, quality=62):
    """Re-encode in place. Commons serves its thumbnails at a quality meant for
    looking closely at; these are 165 px cards and a hero. The first pass came
    to 65 MB across 145 files — a weight the repository would carry forever and
    every reader would pay for on a phone connection. `sips` ships with macOS,
    so this needs nothing installed; where it is absent the file is simply left
    as it arrived rather than the build failing over decoration."""
    if not shutil.which("sips"):
        return
    before = os.path.getsize(path)
    # -Z fits the LONGEST side, which is the one that matters: asking Commons
    # for a 1000 px width hands back a 1280x1920 portrait, and the tall ones
    # were the whole of the weight problem.
    r = subprocess.run(["sips", "-Z", str(LONGEST), "-s", "format", "jpeg",
                        "-s", "formatOptions", str(quality), path, "--out", path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Only keep the result if it actually helped and is still a real file.
    if r.returncode != 0 or os.path.getsize(path) < 2000:
        return
    return before - os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="pull the image files too")
    ap.add_argument("--refresh", action="store_true", help="ignore the resolve cache")
    args = ap.parse_args()

    os.makedirs(CACHE, exist_ok=True)
    cache_path = os.path.join(CACHE, "resolve.json")
    cache = {}
    if os.path.exists(cache_path) and not args.refresh:
        cache = json.load(open(cache_path, encoding="utf-8"))

    with open(SOURCES, encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh
                 if ln.strip() and not ln.strip().startswith("#")]

    titles, dropped = [], []
    for ln in lines:
        m = SHARE.search(ln)
        if m:
            r = resolve_share(m.group(1), cache, args.refresh)
            json.dump(cache, open(cache_path, "w", encoding="utf-8"))  # incremental
            if r.get("ok"):
                titles.append(r["title"])
            else:
                dropped.append((ln, r.get("why", "?") +
                                (" → " + r["landed"] if r.get("landed") else "")))
            continue
        t = file_title(ln)
        (titles.append(t) if t else dropped.append((ln, "unrecognised link")))

    seen, order = set(), []
    for t in titles:
        if t not in seen:
            seen.add(t)
            order.append(t)
    print("%d links → %d distinct Commons files (%d dropped)"
          % (len(lines), len(order), len(dropped)))
    for ln, why in dropped:
        print("  dropped  %s  (%s)" % (ln, why))

    # ---- metadata, 50 at a time (the API's limit for imageinfo) -------------
    meta = {}
    taken = {}   # slug -> the title that claimed it, so a clash is visible
    for i in range(0, len(order), 50):
        batch = order[i:i + 50]
        d = api({"action": "query", "titles": "|".join(batch), "prop": "imageinfo",
                 "iiprop": "extmetadata|url|size", "iiurlwidth": WIDTH})
        for pg in d.get("query", {}).get("pages", []):
            if "missing" in pg or not pg.get("imageinfo"):
                dropped.append((pg.get("title", "?"), "no such file on Commons"))
                continue
            ii = pg["imageinfo"][0]
            em = ii.get("extmetadata", {})
            val = lambda k: strip_html(em.get(k, {}).get("value", ""))   # noqa: E731
            taken.setdefault(slug_for(pg["title"], taken), pg["title"])
            meta[pg["title"]] = {
                "title": pg["title"],
                "slug": slug_for(pg["title"], taken),
                "page": ii.get("descriptionurl", ""),
                "thumb": ii.get("thumburl", ""),
                "width": ii.get("thumbwidth") or ii.get("width"),
                "height": ii.get("thumbheight") or ii.get("height"),
                "licence": val("LicenseShortName") or val("License"),
                "artist": val("Artist") or val("Credit") or "unknown",
                "credit": val("Credit"),
                "description": val("ImageDescription"),
                "date": val("DateTimeOriginal") or val("DateTime"),
            }
        time.sleep(PAUSE)

    out = []
    for t in order:
        m = meta.get(t)
        if not m:
            continue
        classify(m)
        m["usable"] = bool(OK_LICENCE.match(m["licence"] or ""))
        if not m["usable"]:
            print("  not publishable  %s  (%s)" % (t, m["licence"] or "no licence stated"))
        out.append(m)

    # data/curated/ is field truth: anything a human added by hand to an entry
    # — a slot assignment, a better caption — outranks what the API says and is
    # carried across rather than overwritten.
    HAND = ("slot", "caption_th", "caption_en", "crop", "note", "skip")
    if os.path.exists(OUT):
        prev = {e["title"]: e for e in json.load(open(OUT, encoding="utf-8"))["picks"]}
        for e in out:
            for k in HAND:
                if k in prev.get(e["title"], {}):
                    e[k] = prev[e["title"]][k]

    if args.download:
        os.makedirs(ART, exist_ok=True)
        got = 0
        for e in out:
            if not e["usable"] or not e["thumb"]:
                continue
            dest = os.path.join(ART, e["slug"] + ".jpg")
            e["file"] = "site/" + e["slug"] + ".jpg"
            if os.path.exists(dest) and os.path.getsize(dest) > 1000:
                continue
            try:
                open(dest, "wb").write(get(e["thumb"], timeout=60))
                shrink(dest)
                got += 1
            except Exception as ex:                          # noqa: BLE001
                print("  download failed  %s  (%s)" % (e["slug"], ex))
                e.pop("file", None)
            time.sleep(PAUSE)
        print("downloaded %d new file(s) into assets/site/" % got)
    else:
        for e in out:
            dest = os.path.join(ART, e["slug"] + ".jpg")
            if os.path.exists(dest):
                e["file"] = "site/" + e["slug"] + ".jpg"

    json.dump({"note": ("Hand-picked city photographs for the site's own "
                        "furniture. Every entry carries the licence and the "
                        "photographer it arrived with; nothing is published "
                        "without them."),
               "source": "data/curated/image_picks_sources.txt",
               "picks": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    usable = sum(1 for e in out if e["usable"])
    print("wrote %s — %d picks, %d publishable, %d with a local file"
          % (os.path.relpath(OUT, ROOT), len(out), usable,
             sum(1 for e in out if e.get("file"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
