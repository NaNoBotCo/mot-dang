#!/usr/bin/env python3
"""fleetsearch/crawl.py — read every built page of the fleet into one corpus.

The corpus is the local build of each site on the roster (index/data/fleet.json):
docs/ on disk is what the live site serves, so nothing is fetched. One row per
page: url, title, abstract, last-modified, size, and the tokenised text the
edge matches on.

    python3 fleetsearch/crawl.py            # → cache/fleetsearch/pages.jsonl
    python3 fleetsearch/crawl.py --site wichaa --limit 200   # a sample

Thai is written without spaces, so every Thai run is split with the same
dictionary the Worker uses at query time (docs/data/search_segdict.txt, the
file publish/worker.js loads from R2). Index and query splitting the same way
is the whole trick; nothing else about Thai is special here.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PROJECTS = REPO.parent
SEARCHCORE = PROJECTS / "search-core"
SEGDICT = REPO / "docs" / "data" / "search_segdict.txt"
if not SEGDICT.exists():            # docs/ is wiped for a build; the file build.py copies there lives in data/
    SEGDICT = REPO / "data" / "search_segdict.txt"
OUT_DIR = REPO / "cache" / "fleetsearch"
OUT = OUT_DIR / "pages.jsonl"

BODY_CAP = 4000        # characters of page text kept per page, after the title
ABSTRACT_CAP = 240
MEMBERS_MAX = 400      # a list's own items read for its picture strip (pages.jsonl only; D1 gets the few chosen)
READ_CAP = 2_000_000   # bytes read from one file; the hub pages run to 68 MB

sys.path.insert(0, str(HERE))
from deboil import brand_suffix, strip_chrome  # noqa: E402

ROSTER = PROJECTS / "index" / "data" / "fleet.json"
DEV = PROJECTS.parent              # ~/Developer: a few repos live beside the projects folder
BUILD_DIRS = ("docs", "dist", "site", "public", ".")

# id, local build, public base. The base wins over a page's own canonical when
# the canonical points elsewhere (muay-thai's build says github.io; the roster
# says motdang.net/muay-thai/, and both answer).
#
# The site list itself comes from the roster (sites() below); these lines are
# the builds whose folder the roster's repo name does not lead to. A roster
# site served inside another site's build (motdang.net/muay-thai/ is
# mot-dang/docs/muay-thai) is read from that folder, which is what is served.
SITES = [
    ("motdang", "mot-dang/docs", "https://motdang.net/"),
    ("wichaa", "nanobotco-lanna/docs", "https://wichaa.net/"),
    ("muay-thai", "muay-thai/docs", "https://motdang.net/muay-thai/"),
    ("hand-poke", "hand-poke/docs", "https://nanobotco.github.io/hand-poke/"),
    ("amulet-atlas", "amulet-atlas/docs", "https://nanobotco.github.io/amulet-atlas/"),
    ("carolina-barbecue", "carolina-barbecue/docs", "https://nanobotco.github.io/carolina-barbecue/"),
    ("buffalo-wings", "buffalo-wings/docs", "https://nanobotco.github.io/buffalo-wings/"),
    ("pink-box", "pink-box/docs", "https://nanobotco.github.io/pink-box/"),
    ("basque-tables", "basque-tables/docs", "https://nanobotco.github.io/basque-tables/"),
    ("pinot-noir", "pinot-noir/docs", "https://nanobotco.github.io/pinot-noir/"),
    ("care-abroad", "medical-tourism/docs", "https://nanobotco.github.io/care-abroad/"),
    ("mae-hong-son-loop", "mhs-loop/docs", "https://nanobotco.github.io/mae-hong-son-loop/"),
    ("thairoots", "thairoots", "https://nanobotco.github.io/thairoots/"),
    ("index", "index/docs", "https://nanobotco.github.io/index/"),
    ("uptake", "uptake/docs", "https://nanobotco.github.io/uptake/"),
    ("portal", "nanobotco-portal", "https://nanobotco.github.io/"),
    ("defiant", "defiant-site/docs", "https://defiant.to/"),
    ("hongdam", "hongdam-site/docs", "https://hongdam.net/"),
    ("offramp", "offramp/docs", "https://offrampt.net/"),
    ("hakfarang", "hak-farang/dist", "https://hakfarang.net/"),
    ("hunpayont", "hunpayont-apps/public", "https://hunpayont.net/"),
    ("chiangmaivisadesk", "visa-desk/site", "https://chiangmaivisadesk.com/"),
]


def _git_repos() -> dict:
    """GitHub repo name (lower case) → its checkout, from each folder's
    .git/config. A '-hold' copy is a parked duplicate, never the build."""
    out = {}
    for parent in (PROJECTS, DEV):
        try:
            kids = sorted(parent.iterdir())
        except OSError:
            continue
        for d in kids:
            if not d.is_dir() or d.name.endswith("-hold"):
                continue
            try:
                cfg = (d / ".git" / "config").read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in re.finditer(r"url\s*=\s*\S*github\.com[:/][^/\s]+/([^/\s]+?)(?:\.git)?\s*$", cfg, re.M):
                name = m.group(1).lower()
                # the folder named like the repo wins over another checkout of it
                if name not in out or d.name.lower() == name:
                    out[name] = d
    return out


def _build_of(repo: Path) -> Path | None:
    for sub in BUILD_DIRS:
        p = repo / sub
        if (p / "index.html").is_file():
            return p.resolve()
    return None


def roster() -> list[dict]:
    try:
        return json.loads(ROSTER.read_text(encoding="utf-8")).get("sites") or []
    except (OSError, ValueError):
        return []


def sites(report: list | None = None) -> list[tuple[str, Path, str]]:
    """(id, build folder, public base) for every roster site with a build on
    this disk. `report`, when given, collects (id, url) of those without one."""
    fixed = {s: (PROJECTS / rel, base) for s, rel, base in SITES}
    entries = [(s.get("id"), s.get("url"), s.get("repo") or "") for s in roster() if s.get("id") and s.get("url")]
    ids = {e[0] for e in entries}
    entries += [(s, base, "") for s, (_, base) in fixed.items() if s not in ids]
    repos = _git_repos()
    out: list[tuple[str, Path, str]] = []
    # shortest base first, so a parent is resolved before any site inside it
    for sid, url, repo in sorted(entries, key=lambda e: len(e[1])):
        base = url if url.endswith("/") else url + "/"
        root = None
        for psid, proot, pbase in sorted(out, key=lambda o: -len(o[2])):
            if base.startswith(pbase) and base != pbase:
                sub = proot / base[len(pbase):]
                if (sub / "index.html").is_file():
                    root = sub.resolve()
                break
        if root is None and sid in fixed:
            root = fixed[sid][0].resolve() if fixed[sid][0].is_dir() else None
            base = fixed[sid][1]
        if root is None:
            for name in (repo.rstrip("/").rsplit("/", 1)[-1].lower() if repo else "", sid.lower()):
                if name and name in repos:
                    root = _build_of(repos[name])
                    if root:
                        break
        if root is None:
            for parent in (PROJECTS, DEV):
                if (parent / sid).is_dir():
                    root = _build_of(parent / sid)
                    if root:
                        break
        if root is None:
            if report is not None:
                report.append((sid, url))
            continue
        out.append((sid, root, base))
    order = {e[0]: i for i, e in enumerate(entries)}
    return sorted(out, key=lambda o: order.get(o[0], 1 << 20))


def brands() -> dict:
    """site id → the names a site signs its titles with (fleet.json name, th)."""
    out = {}
    for s in roster():
        out[s.get("id")] = [x for x in (s.get("name"), s.get("th")) if x]
    return out

SKIP_DIRS = {"node_modules", ".git", "_to_delete", "__pycache__", ".venv", "docs.next"}
SKIP_NAMES = {"404.html", "google", "sw.html"}

RE_THAI = re.compile(r"[฀-๿]+")
RE_ZW = re.compile(r"[​-‏‪-‮﻿]")
RE_WS = re.compile(r"\s+")
RE_TAG = re.compile(r"<[^>]+>")
RE_DROP = re.compile(r"(?is)<(script|style|svg|noscript|template|iframe|canvas)\b[^>]*>.*?</\1\s*>")
RE_CHROME = re.compile(r"(?is)<(header|footer|nav)\b[^>]*>.*?</\1\s*>")
RE_COMMENT = re.compile(r"(?s)<!--.*?-->")
# Text a page carries that is not about the page: <head> (the title again),
# the skip link, and the list of neighbours — ten other places' names, which
# made every page within 100 m an answer for each of them.
RE_NOTPAGE = re.compile(r'(?is)<head\b.*?</head\s*>|<a\s+class="skiplink".*?</a\s*>'
                        r'|<ul\s+class="wander-near".*?</ul\s*>')
RE_TITLE = re.compile(r"(?is)<title[^>]*>(.*?)</title>")
RE_DESC = re.compile(r'(?is)<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']')
RE_DESC2 = re.compile(r'(?is)<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']')
RE_CANON = re.compile(r'(?is)<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']')
# Every robots meta on the page, quoted or not: Mot Dang's complete-roll pages
# carry two, "index,follow" and then "noindex,follow", and wichaa's moved
# stubs write theirs without quotes.
RE_ROBOTS = re.compile(r'(?is)<meta\s+name=["\']?robots["\']?\s+content=["\']?([^"\'>]*)')
# A page that sends the browser on (`http-equiv=refresh`) is a stub: Hand
# Poke's "Moved to wichaa.net", wichaa's /m/<n>/ forwards, /listings.html.
RE_REFRESH = re.compile(r'(?is)<meta\s+http-equiv=["\']?refresh["\']?')
RE_UNTITLED = re.compile(r"^Untitled\b\s*(?:\((.+?)\))?", re.I)
RE_TH_LINE = re.compile(r'(?is)<p\s+class=["\']?th["\']?>(.*?)</p>')
RE_H1 = re.compile(r"(?is)<h1[^>]*>(.*?)</h1>")
RE_LANG = re.compile(r'(?is)<html[^>]*\blang=["\']([a-zA-Z-]+)["\']')
RE_LD = re.compile(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>')
RE_GEOPOS = re.compile(r'(?is)<meta\s+name=["\']geo\.position["\']\s+content=["\']\s*'
                       r'(-?\d+\.?\d*)\s*[;,]\s*(-?\d+\.?\d*)')
RE_OGIMG = re.compile(r'(?is)<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']')
RE_MAIN = re.compile(r"(?is)<main\b[^>]*>(.*?)</main>")
RE_IMG = re.compile(r'(?is)<img\b[^>]*?\bsrc=["\']([^"\']+)["\']')
RE_WHATSON = re.compile(r'(?is)<div class="whatson">(.*?)</ul>')
RE_ICS = re.compile(r"data:text/calendar;base64,([A-Za-z0-9+/=]+)")
# The drawing a place page makes of itself when it has no photograph
# (doodles_layer.portrait): its scene name, so a result row can draw the same one.
RE_PORTRAIT = re.compile(r'class="mdportrait" data-set="([a-z][a-z-]*)"')

# A share card is a poster of the page's own title; shrunk to a thumbnail it is
# a strip of cut-off type, so it is not counted as a picture. Nor is a logo, an
# icon, a QR code or a drawing the page generates.
RE_NOT_PICTURE = re.compile(r"(?i)(/cards?/|/og/|(^|/)(og|card|og-default|logo|favicon|icon)[^/]*\.\w+$"
                            r"|/logo/|/icons?/|/qr/|/glyphs/|\.svg(\?|$)|^data:)")

# How a way of reaching a place is named in the index, in the order the place
# pages list them (build.py channels()).
WAYS = ("phone", "line", "whatsapp", "facebook", "instagram", "email", "web",
        "x", "tiktok", "youtube")
PLACE_PAGE = re.compile(r"^(cm|cr)/p/[^/]+\.html$")

_SEG = None
_FACETS = None
_GLOSS = None
_TIERS = None


class Toilets:
    """The toilet minisite's own knowledge (/toilets.html), read back for the
    search rows so a row and the minisite say the same thing:

      docs/data/toilets.json   what toilets_layer.py baked — the mapped
                               toilets, and every venue whose kind anyone
                               may walk into, with its tier and any field
                               report
      data/toilets.json        the model: tiers, reports, and `stated` — what
                               Nan has said outright (2026-09-23), which
                               outranks a tier's habit

    For a row: its own toilet, if there is one to speak of, else the nearest
    one within NEAR_M, measured only from a pin the record calls exact.
    """
    NEAR_M = 400
    CELL = 0.005                    # ~550 m; a pin looks in its cell and the eight around it

    def __init__(self):
        self.tiers, self.by_id, self.points = [], {}, []
        self.stated, self.reports = {}, {}
        try:
            model = json.loads((REPO / "data" / "toilets.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            model = {}
        self.reports = model.get("reports") or {}
        self.stated = model.get("stated") or {}
        try:
            baked = json.loads((REPO / "docs" / "data" / "toilets.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            baked = {}
        self.tiers = baked.get("tiers") or []
        cols = baked.get("columns") or []
        ix = {c: i for i, c in enumerate(cols)}
        # toilets_layer.py writes a `said` column once it reads `stated`: an
        # index into head["said"]. Where it is there, the minisite's own match
        # is used and said() below is not asked.
        said_list = baked.get("said") or []
        self.baked_said = "said" in ix
        try:
            cust = json.loads((REPO / "docs" / "data" / "toilets-customers.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cust = {}
        grid = {}
        rows = [(r, True) for r in baked.get("places") or []] + [(r, False) for r in cust.get("places") or []]
        for row, walk_in in rows:
            try:
                rid = row[ix["id"]]
                ti = row[ix["tier"]]
            except (KeyError, IndexError, TypeError):
                continue
            t = self.tiers[ti] if isinstance(ti, int) and 0 <= ti < len(self.tiers) else None
            sd = None
            if self.baked_said and ix["said"] < len(row) and isinstance(row[ix["said"]], int) \
                    and 0 <= row[ix["said"]] < len(said_list):
                sd = said_list[row[ix["said"]]]
            self.by_id[rid] = (t, row[ix["report"]] or "", sd)
            # The nearest-toilet line counts doors a stranger may walk through.
            if walk_in and ((t and t.get("strength") == "strong") or row[ix["report"]] or sd):
                name = row[ix["th"]] or row[ix["en"]]
                self._put(grid, row[ix["lat"]], row[ix["lng"]], (name, rid, "place"))
        vcols = {c: i for i, c in enumerate(baked.get("verified_columns") or [])}
        for v in baked.get("verified") or []:
            try:
                self._put(grid, v[vcols["lat"]], v[vcols["lng"]],
                          (v[vcols["th"]] or v[vcols["en"]] or "", "", "mapped"))
            except (KeyError, IndexError, TypeError):
                continue
        self.grid = grid

    def _put(self, grid, lat, lng, what):
        grid.setdefault((int(lat / self.CELL), int(lng / self.CELL)), []).append((lat, lng, what))

    # --- Nan's word ------------------------------------------------------

    @staticmethod
    def _starts(name: str, prefix: str) -> bool:
        """A Latin prefix ends at a word boundary — "big c" is Big C Extra,
        not Big Coffee. A Thai one only has to begin the name."""
        if not name.startswith(prefix):
            return False
        nxt = name[len(prefix):len(prefix) + 1]
        return not (prefix[-1:].isascii() and prefix[-1:].isalnum() and nxt.isascii() and nxt.isalnum())

    def said(self, rec: dict):
        """(th, en) when Nan has said this place, or this kind of place, has a
        toilet; else None."""
        for p in self.stated.get("places") or []:
            if p.get("id") and p["id"] == rec.get("id"):
                return p["th"], p["en"]
        names = [str(rec.get(k) or "").strip() for k in ("name", "nameTh", "nameEn")]
        low = [n.lower() for n in names if n]
        subs, cats = set(rec.get("sub") or []), set(rec.get("cat") or [])
        a = rec.get("attrs") or {}
        for k in self.stated.get("kinds") or []:
            m = k.get("match") or {}
            if m.get("sub") and not subs & set(m["sub"]):
                continue
            if m.get("cat") and not cats & set(m["cat"]):
                continue
            if m.get("not_sub") and subs & set(m["not_sub"]):
                continue
            if m.get("name_prefix") and not any(self._starts(n, w.lower()) for n in low for w in m["name_prefix"]):
                continue
            if m.get("not_name") and any(w.lower() in n for n in low for w in m["not_name"]):
                continue
            if m.get("brand_any"):
                hay = " ".join(low + [str(a.get("brand") or "").lower(), str(a.get("operator") or "").lower()])
                if not any(w.lower() in hay for w in m["brand_any"]):
                    continue
            if m.get("big"):
                try:
                    big = (float(a.get("stars") or 0) >= 4 or int(a.get("rooms") or 0) >= 50
                           or int(a.get("chainSize") or 0) >= 2)
                except (TypeError, ValueError):
                    big = False
                if not big:
                    continue
            return k["th"], k["en"]
        return None

    # --- a row -----------------------------------------------------------

    REPORT_WORDS = {"toiletfree": ("ห้องน้ำฟรี", "free toilet"),
                    "toiletfee5": ("ห้องน้ำ 5 บาท", "toilet, 5 baht"),
                    "toiletfee10": ("ห้องน้ำ 10 บาท", "toilet, 10 baht"),
                    "toilethere": ("มีห้องน้ำ", "toilet")}

    def of(self, rec: dict, facets: dict):
        """['r'|'s'|'h', th, en] for the place's own toilet — a report or a
        recorded facet, Nan's word, or a tier's habit — or None. A report of
        none, from anyone who stood there, ends it."""
        tier, report, sd = self.by_id.get(rec.get("id"), (None, "", None))
        got = set(facets or {})
        if report == "toiletnone" or "toiletnone" in got:
            return None
        for k in ("toiletfee10", "toiletfee5", "toiletfree", "toilethere"):
            if report == k or k in got:
                return ["r", *self.REPORT_WORDS[k]]
        if "toilet" in got:
            return ["r", "มีห้องน้ำ", "toilet"]
        said = (sd["th"], sd["en"]) if sd else (None if self.baked_said else self.said(rec))
        if said:
            return ["s", *said]
        if tier and tier.get("access") in ("public", "visitor"):
            return ["h", "ปกติมีห้องน้ำ", "usually a toilet"]
        return None

    def near(self, rec: dict):
        """['n', name, metres] for the nearest toilet within NEAR_M of an exact
        pin, or None. Under 25 m only a mapped toilet counts: two records a few
        metres apart are as often one centroid as two neighbours."""
        if rec.get("geoPrecision") != "exact" or rec.get("lat") is None:
            return None
        lat, lng = float(rec["lat"]), float(rec["lng"])
        ci, cj = int(lat / self.CELL), int(lng / self.CELL)
        k = math.cos(math.radians(lat))
        best = None
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for plat, plng, (name, rid, kind) in self.grid.get((ci + di, cj + dj), ()):
                    if rid and rid == rec.get("id"):
                        continue
                    m = math.hypot((plat - lat) * 111320, (plng - lng) * 111320 * k)
                    if m > self.NEAR_M or (m < 25 and kind != "mapped"):
                        continue
                    if best is None or m < best[2]:
                        best = ["n", name, m]
        if best:
            best[2] = int(round(best[2] / 10.0) * 10)
        return best


_TOILETS = None


def toilets() -> Toilets:
    global _TOILETS
    if _TOILETS is None:
        _TOILETS = Toilets()
    return _TOILETS


def facet_names() -> dict:
    """facet key → (icon, th, en), from the directory's own schema. A key that
    appears in two sets carries the same icon in both, so the first wins."""
    global _FACETS
    if _FACETS is None:
        _FACETS = {}
        try:
            doc = json.loads((REPO / "data" / "facets.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            doc = []
        for s in (doc.get("sets") if isinstance(doc, dict) else doc) or []:
            for f in s.get("facets") or []:
                _FACETS.setdefault(f["key"], (f.get("icon") or "", f.get("th") or "", f.get("en") or ""))
    return _FACETS


def gloss() -> dict:
    """Thai crumb name → its English, from the shelves' own bilingual names.
    Mot Dang's BreadcrumbList carries the Thai alone."""
    global _GLOSS
    if _GLOSS is None:
        _GLOSS = {"หน้าแรก": "Home", "ป้ายกำกับ": "Tags"}
        try:
            doc = json.loads((REPO / "data" / "categories.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            doc = {}

        def walk_cats(items):
            for c in items or []:
                if isinstance(c, dict) and c.get("th") and c.get("en"):
                    _GLOSS.setdefault(c["th"], c["en"])
                    walk_cats(c.get("children"))
        walk_cats(doc.get("categories"))
        prov = doc.get("provinces") or {}
        for p in (prov.values() if isinstance(prov, dict) else prov):
            if isinstance(p, dict) and p.get("th") and p.get("en"):
                _GLOSS.setdefault(p["th"], p["en"])
    return _GLOSS


def ld_nodes(raw: str) -> list:
    """Every top-level JSON-LD object on the page, @graph flattened."""
    out = []
    for block in RE_LD.findall(raw):
        try:
            doc = json.loads(block)
        except (ValueError, RecursionError):
            continue
        for d in (doc if isinstance(doc, list) else [doc]):
            if isinstance(d, dict) and isinstance(d.get("@graph"), list):
                out.extend(x for x in d["@graph"] if isinstance(x, dict))
            elif isinstance(d, dict):
                out.append(d)
    return out


def _types(node) -> set:
    t = node.get("@type")
    return set(t) if isinstance(t, list) else {t} if isinstance(t, str) else set()


def crumbs_of(nodes, base: str, url: str) -> list:
    """[name, url, english] from the page's BreadcrumbList, without the site's
    front page (the row already names the site) and without the page itself."""
    for n in nodes:
        if "BreadcrumbList" not in _types(n):
            continue
        items = [x for x in n.get("itemListElement") or [] if isinstance(x, dict)]
        items.sort(key=lambda x: x.get("position") or 0)
        out = []
        for x in items:
            item = x.get("item")
            href = item.get("@id") if isinstance(item, dict) else item
            name = clean(html.unescape(str(x.get("name") or (item.get("name") if isinstance(item, dict) else "") or "")))
            if not name:
                continue
            out.append([name[:60], href if isinstance(href, str) else ""])
        root = {base, base + "index.html", base.rstrip("/")}
        if out and (out[0][1] in root or out[0][1] == ""):
            out = out[1:]
        if out and (out[-1][1] in (url, "") or out[-1][1].rstrip("/") == url.rstrip("/")):
            out = out[:-1]
        g = gloss()
        return [[n_, h, g.get(n_, "")] for n_, h in out[:4]]
    return []


def url_way(u: str) -> str:
    h = u.split("//", 1)[-1].split("/", 1)[0].lower()
    if u.startswith("tel:"):
        return "phone"
    if u.startswith("mailto:"):
        return "email"
    for host, way in (("facebook.com", "facebook"), ("fb.com", "facebook"), ("instagram.com", "instagram"),
                      ("line.me", "line"), ("lin.ee", "line"), ("wa.me", "whatsapp"),
                      ("whatsapp.com", "whatsapp"), ("twitter.com", "x"), ("x.com", "x"),
                      ("tiktok.com", "tiktok"), ("youtube.com", "youtube"), ("youtu.be", "youtube")):
        if h == host or h.endswith("." + host):
            return way
    if "wikipedia.org" in h or "wikidata.org" in h or "wikimedia.org" in h:
        return ""                          # reading about it, not reaching it
    return "web" if u.startswith("http") else ""


def _ics_events(uri_b64: str) -> list:
    try:
        doc = base64.b64decode(uri_b64).decode("utf-8", "ignore")
    except (ValueError, TypeError):
        return []
    out = []
    for ve in doc.split("BEGIN:VEVENT")[1:]:
        m = re.search(r"DTSTART[^:\r\n]*:(\d{4})(\d{2})(\d{2})", ve)
        if not m:
            continue
        ev = {"d": f"{m.group(1)}-{m.group(2)}-{m.group(3)}"}
        rr = re.search(r"RRULE:([^\r\n]+)", ve)
        if rr and "FREQ=WEEKLY" in rr.group(1):
            days = re.search(r"BYDAY=([A-Z,]+)", rr.group(1))
            codes = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            ev["w"] = ([codes.index(c) for c in days.group(1).split(",") if c in codes]
                       if days else [datetime.strptime(ev["d"], "%Y-%m-%d").weekday()])
            until = re.search(r"UNTIL=(\d{4})(\d{2})(\d{2})", rr.group(1))
            if until:
                ev["u"] = f"{until.group(1)}-{until.group(2)}-{until.group(3)}"
        s = re.search(r"SUMMARY:([^\r\n]+)", ve)
        if s:
            ev["t"] = s.group(1).replace("\\,", ",").replace("\\;", ";")[:80]
        out.append(ev)
    return out


def image_of(nodes, raw: str) -> str:
    """The page's own picture: the main entity's image, else og:image, else
    the first picture inside <main>. Empty when the only candidates are share
    cards, logos or drawings."""
    cands = []
    for n in nodes:
        if _types(n) & {"BreadcrumbList", "WebSite", "ItemList", "Organization", "Dataset"}:
            continue
        im = n.get("image")
        for x in (im if isinstance(im, list) else [im]):
            if isinstance(x, dict):
                x = x.get("contentUrl") or x.get("url")
            if isinstance(x, str):
                cands.append(x)
    m = RE_OGIMG.search(raw)
    if m:
        cands.append(html.unescape(m.group(1)))
    mm = RE_MAIN.search(raw)
    if mm:
        cands.extend(html.unescape(x) for x in RE_IMG.findall(mm.group(1))[:3])
    for c in cands:
        c = c.strip()
        if c and not RE_NOT_PICTURE.search(c):
            return c
    return ""


def resolve_img(src: str, path: Path, root: Path, base: str) -> str:
    """An image reference as the page wrote it → `file:<absolute path>` when
    the build holds the file, the URL itself when another host serves it, or
    empty. Pages write their pictures three ways: absolute on their own host,
    rooted at the site's public path (/muay-thai/images/…), and relative to
    the page (../../images/…)."""
    src = src.split("#", 1)[0].strip()
    if not src:
        return ""
    host = base.split("/")[2]
    bpath = "/" + base.split("/", 3)[3] if base.count("/") >= 3 else "/"
    rel = None
    if src.startswith("//"):
        src = "https:" + src
    if src.startswith("http"):
        h = src.split("/")[2]
        if h != host:
            return src
        src = "/" + src.split("/", 3)[3] if src.count("/") >= 3 else "/"
    src = src.split("?", 1)[0]
    if src.startswith("/"):
        if src.startswith(bpath):
            rel = src[len(bpath):]
        elif bpath == "/":
            rel = src[1:]
        else:
            return ""
        f = root / rel
    else:
        f = (path.parent / src)
    try:
        f = f.resolve()
        f.relative_to(root.resolve())
    except (ValueError, OSError):
        return ""
    return f"file:{f}" if f.is_file() else ""


def richness(raw: str, nodes, path: Path, site: str, rel: str, pin) -> dict:
    """What a result row can say about the listing behind it, besides its words:
    the ways to reach it, a toilet, what is on there, whether hours are known,
    the facts recorded about it — read from the place's own .json twin where
    Mot Dang writes one, and from the page's schema.org otherwise."""
    ways, fac, events = [], [], []
    evc = 0
    toilet = False
    sched = None
    photo = ""
    credit = ""
    twin = path.with_suffix(".json")
    if site == "motdang" and PLACE_PAGE.match(rel) and twin.exists():
        try:
            rec = json.loads(twin.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rec = {}
        for c in rec.get("channels") or []:
            k = c.get("kind")
            if k in WAYS and k not in ways:
                ways.append(k)
        names = facet_names()
        for k in (rec.get("facets") or {}):
            if k in names and k != "toiletnone":
                fac.append([k] + list(names[k]))
        toilet = toilets().of(rec, rec.get("facets") or {}) or toilets().near(rec)
        # events held here, coming and gone (build.py place_event_history)
        _evc = (rec.get("events") or {}).get("n")
        if isinstance(_evc, int) and _evc > 0:
            evc = _evc
        if isinstance(rec.get("sched"), list) and rec["sched"]:
            sched = [[int(a), int(b)] for a, b in rec["sched"]]
        ph = rec.get("photo") or {}
        if ph.get("url"):
            photo = ph["url"]
            credit = " · ".join(str(ph[k]) for k in ("author", "license") if ph.get(k))[:120]
        said = said_of(rec)
    else:
        for n in nodes:
            geo = n.get("geo")
            if not (isinstance(geo, dict) or isinstance(n.get("address"), dict)):
                continue
            if n.get("telephone") and "phone" not in ways:
                ways.append("phone")
            if n.get("email") and "email" not in ways:
                ways.append("email")
            same = n.get("sameAs")
            for u in ([same] if isinstance(same, str) else same or []):
                w = url_way(u) if isinstance(u, str) else ""
                if w and w not in ways:
                    ways.append(w)
            if n.get("openingHours") or n.get("openingHoursSpecification"):
                sched = sched or []
    for block in RE_WHATSON.findall(raw):
        for b64 in RE_ICS.findall(block):
            events.extend(_ics_events(b64))
    for n in nodes:
        if any("Event" in t for t in _types(n)) and isinstance(n.get("startDate"), str):
            if re.match(r"\d{4}-\d{2}-\d{2}", n["startDate"]):
                events.append({"d": n["startDate"][:10], "t": clean(str(n.get("name") or ""))[:80]})
    ways.sort(key=WAYS.index)
    out = {}
    if ways:
        out["ways"] = ways
    if fac:
        out["fac"] = fac[:12]
    if toilet:
        # r reported or recorded at the place · s Nan's word · h a habit of its
        # kind (the minisite's tier) · n the nearest one, in metres
        out["toilet"] = toilet
    if events:
        out["ev"] = events[:8]
    if evc:
        out["evc"] = evc
    if sched is not None:
        out["sched"] = sched
    if photo:
        out["photo"] = photo
    if credit:
        out["credit"] = credit
    if site == "motdang" and PLACE_PAGE.match(rel) and twin.exists():
        out.update(said)
        if not photo:
            m = RE_PORTRAIT.search(raw)
            if m:
                out["sc"] = m.group(1)
    return out


def said_of(rec: dict) -> dict:
    """What a result row says about a place beyond its title (Nan, 2026-10-04,
    "not enough transliteration … not enough preview"):
      rd   [script, text] — the name read in the script it lacks, the same
           reading the city map carries (front_layer._reading)
      bear [th, en] — where it stands, from the page's own bearings
      pr   the price range the record states"""
    out = {}
    nm, ne = rec.get("nameTh") or rec.get("name") or "", rec.get("nameEn") or ""
    try:
        rd = reading_of(nm, ne if ne != nm else "")
    except Exception:              # noqa: BLE001 — a reading is a nicety, not a reason to drop a row
        rd = ""
    if rd:
        out["rd"] = ["th" if re.search(r"[\u0e00-\u0e7f]", rd) else "en", rd[:90]]
    bs = [b for b in (rec.get("bearings") or []) if isinstance(b, dict) and b.get("th") and b.get("en")]
    bs.sort(key=lambda b: b.get("kind") != "near")
    if bs:
        out["bear"] = [bs[0]["th"][:90], bs[0]["en"][:90]]
    pr = (rec.get("attrs") or {}).get("priceRange")
    if isinstance(pr, str) and pr.strip():
        out["pr"] = pr.strip()[:24]
    return out


_READ = None


def reading_of(th: str, en: str) -> str:
    global _READ
    if _READ is None:
        sys.path.insert(0, str(REPO))
        from front_layer import _reading  # noqa: E402
        _READ = _reading
    return _READ(th, en)


def members_of(nodes, base: str) -> list:
    """A list page's own ItemList, as addresses under its host, in its order —
    load.py picks the best few to show as pictures beside the row."""
    out = []
    for n in nodes:
        if "ItemList" not in _types(n):
            continue
        for it in n.get("itemListElement") or []:
            u = it.get("url") if isinstance(it, dict) else None
            if not isinstance(u, str) and isinstance(it, dict) and isinstance(it.get("item"), (str, dict)):
                u = it["item"] if isinstance(it["item"], str) else it["item"].get("@id") or it["item"].get("url")
            if isinstance(u, str) and u.startswith(base):
                out.append(u[len(base):])
            if len(out) >= MEMBERS_MAX:
                return out
    return out


def kind_of(nodes, raw: str, rel: str, site: str, pin) -> tuple[str, int]:
    """place · list · page, and how many items a list holds."""
    for n in nodes:
        if "ItemList" in _types(n):
            k = n.get("numberOfItems")
            if not isinstance(k, int):
                k = len(n.get("itemListElement") or [])
            if k > 1:
                return "list", k
    if pin or (site == "motdang" and PLACE_PAGE.match(rel)):
        return "place", 0
    out = set()
    for block in RE_LD.findall(raw):
        try:
            _geos(json.loads(block), out)
        except (ValueError, RecursionError):
            continue
    return ("list", len(out)) if len(out) > 1 else ("page", 0)


def _geos(obj, out):
    """Every schema.org GeoCoordinates in a parsed JSON-LD tree."""
    if isinstance(obj, dict):
        g = obj.get("geo")
        if isinstance(g, dict):
            try:
                lat, lon = float(g["latitude"]), float(g["longitude"])
            except (KeyError, TypeError, ValueError):
                pass
            else:
                if -90 <= lat <= 90 and -180 <= lon <= 180 and (lat or lon):
                    out.add((round(lat, 6), round(lon, 6)))
        for v in obj.values():
            _geos(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _geos(v, out)


def page_pin(raw: str):
    """Where the page says IT is — its own `geo.position` meta, or the one
    GeoCoordinates in its JSON-LD.

    A directory page carries a coordinate for every place it lists, and none
    of them is the page's position, so more than one distinct coordinate means
    no pin rather than a guess at which one counts.
    """
    m = RE_GEOPOS.search(raw)
    if m:
        try:
            lat, lon = float(m.group(1)), float(m.group(2))
        except ValueError:
            return None
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    out = set()
    for block in RE_LD.findall(raw):
        try:
            _geos(json.loads(block), out)
        except (ValueError, RecursionError):
            continue
    return out.pop() if len(out) == 1 else None


def segmenter():
    """The dictionary segmenter, loaded once per process from the file the
    Worker loads from R2 — so a word splits the same way on both sides."""
    global _SEG
    if _SEG is None:
        sys.path.insert(0, str(SEARCHCORE))
        import searchcore  # noqa: E402
        words = [w for w in SEGDICT.read_text(encoding="utf-8").split("\n")
                 if w.strip() and not w.startswith("#")]
        _SEG = searchcore.Segmenter(words)
    return _SEG


def clean(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = RE_ZW.sub("", s)
    return RE_WS.sub(" ", s).strip()


def tokenise(s: str) -> str:
    """Text as the edge will match it: NFC, no zero-width, every Thai run
    split into dictionary words with a space between them."""
    seg = segmenter()
    s = clean(s)
    return RE_THAI.sub(lambda m: " ".join(seg.split(m.group(0))), s)


def strip_tags(fragment: str) -> str:
    return clean(html.unescape(RE_TAG.sub(" ", fragment)))


def page_text(raw: str) -> str:
    s = RE_COMMENT.sub(" ", raw)
    s = RE_DROP.sub(" ", s)
    s = strip_chrome(s)          # deboil.py: share, ads, the ride button, around here …
    s = RE_CHROME.sub(" ", s)
    s = RE_NOTPAGE.sub(" ", s)
    s = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|td|th|dd|dt|section|article|br)\s*>", " ", s)
    return strip_tags(s)


def extract(path: Path, site: str, base: str, root: Path, lastmods: dict) -> dict | None:
    try:
        with open(path, "rb") as f:
            raw = f.read(READ_CAP).decode("utf-8", "ignore")
    except OSError:
        return None
    head = raw[:4000].lower()
    # lersi's page opens straight on <title>, with no <html> or doctype
    if "<html" not in head and "<!doctype" not in raw[:200].lower() and not head.lstrip().startswith("<title"):
        return None
    if RE_REFRESH.search(raw[:20000]):
        return None
    rel = path.relative_to(root).as_posix()
    # noindex keeps a page out, except a Mot Dang place page: it is the one
    # page its place has (build.py marks a thin record noindex for engines),
    # where a complete roll (all.html) repeats its shelf.
    if any("noindex" in x.lower() for x in RE_ROBOTS.findall(raw)) \
            and not (site == "motdang" and PLACE_PAGE.match(rel)):
        return None
    m = RE_TITLE.search(raw)
    title = strip_tags(m.group(1)) if m else ""
    if not title:
        return None

    own = base + rel
    if rel.endswith("index.html"):
        own = base + rel[: -len("index.html")]
    url = own
    m = RE_CANON.search(raw)
    if m and m.group(1).startswith(base):
        url = m.group(1)

    m = RE_DESC.search(raw) or RE_DESC2.search(raw)
    desc = strip_tags(m.group(1)) if m else ""
    m = RE_H1.search(raw)
    h1 = strip_tags(m.group(1)) if m else ""
    # a place page's description ends on the site's name too ("… · เชียงใหม่ · มดแดง")
    desc_s = brand_suffix(desc, site_brands(site))[0]
    # wichaa catalogues a manuscript with no title of its own as "Untitled
    # (what it is about)"; 606 rows read "Untitled" on 2026-10-02. The
    # bracket is the name a reader would search, so it becomes the title.
    um = RE_UNTITLED.match(title)
    if um:
        name = um.group(1) or ("" if RE_UNTITLED.match(h1) else h1)
        if not name:
            return None
        tm = RE_TH_LINE.search(raw)
        th = strip_tags(tm.group(1)) if tm else ""
        pm = re.search(r"\((.+?)\)", th)
        th = pm.group(1).strip() if pm else th
        tail = title.rsplit(" — ", 1)[1] if " — " in title else ""
        title = name + (" · " + th if th else "") + (" — " + tail if tail else "")
    match_title, _ = brand_suffix(title, site_brands(site))
    text = page_text(raw)
    abstract = desc or text[:ABSTRACT_CAP]
    if len(abstract) > ABSTRACT_CAP:
        abstract = abstract[:ABSTRACT_CAP].rsplit(" ", 1)[0] + "…"

    body = " ".join(x for x in (desc_s, h1, text) if x)[:BODY_CAP]
    m = RE_LANG.search(raw)
    lang = (m.group(1).lower() if m else "")[:5]
    pin = page_pin(raw)

    lastmod = lastmods.get(url) or lastmods.get(url.rstrip("/")) or lastmods.get(url + "index.html")
    if not lastmod:
        lastmod = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")
    nodes = ld_nodes(raw)
    kind, items = kind_of(nodes, raw, rel, site, pin)
    rich = richness(raw, nodes, path, site, rel, pin)
    # A Mot Dang place page's picture is its twin's photo or none: the first
    # <img> in its <main> is the Around-here strip since 2026-10-02 — a
    # neighbour's picture, not this place's.
    own_only = site == "motdang" and PLACE_PAGE.match(rel)
    img = resolve_img(rich.pop("photo", "") or ("" if own_only else image_of(nodes, raw)), path, root, base)
    if not img:
        rich.pop("credit", None)
    row = {
        "site": site,
        "host": base.split("/")[2],
        "url": url,
        "title": title[:300],
        "abstract": abstract,
        "lang": lang,
        "lat": pin[0] if pin else None,
        "lon": pin[1] if pin else None,
        "lastmod": lastmod[:10],
        "kb": max(1, round(path.stat().st_size / 1024)),
        "kind": kind,
        "items": items,
        "crumbs": crumbs_of(nodes, base, url),
        "img": img,
        "rich": rich,
        "title_s": tokenise(match_title)[:300],
        "body_s": tokenise(body),
        "url_s": url.split("//", 1)[-1],
    }
    if kind == "list":
        mem = members_of(nodes, base)
        if mem:
            row["members"] = mem   # load.py turns these into the row's picture strip
    if own != url:
        row["_own"] = own          # for dedupe(); dropped before the row is written
    return row


_BRANDS = None


def site_brands(site: str) -> list:
    global _BRANDS
    if _BRANDS is None:
        _BRANDS = brands()
    return _BRANDS.get(site) or []


def sitemap_lastmods(root: Path) -> dict:
    """url → YYYY-MM-DD from every sitemap*.xml under the build (index files
    followed one level). A page the sitemaps do not date falls back to mtime."""
    out = {}
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    seen = set()

    def read(p: Path):
        if p in seen or not p.exists() or p.stat().st_size > 60_000_000:
            return
        seen.add(p)
        try:
            tree = ET.parse(p)
        except ET.ParseError:
            return
        r = tree.getroot()
        for u in r.iter(ns + "url"):
            loc = u.find(ns + "loc")
            lm = u.find(ns + "lastmod")
            if loc is not None and lm is not None and loc.text and lm.text:
                out[loc.text.strip()] = lm.text.strip()[:10]
        for sm in r.iter(ns + "sitemap"):
            loc = sm.find(ns + "loc")
            if loc is not None and loc.text:
                name = loc.text.strip().rsplit("/", 1)[-1]
                read(root / name)

    for p in sorted(root.glob("sitemap*.xml")):
        read(p)
    return out


def walk(root: Path, exclude=()):
    """Every page under root, minus the folders another roster site owns
    (mot-dang/docs/muay-thai is the muay-thai site, read once, as itself)."""
    skip = {Path(x).resolve() for x in exclude}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.startswith((".", "_")) and " " not in d
                       and (Path(dirpath) / d).resolve() not in skip]
        for fn in filenames:
            if fn.endswith(".html") and fn not in SKIP_NAMES:
                yield Path(dirpath) / fn


def _job(args):
    path, site, base, root, lastmods = args
    try:
        return extract(Path(path), site, base, Path(root), lastmods)
    except Exception as e:  # one bad page must not stop the crawl
        return {"_error": f"{path}: {e!r}"}


EXTRA = Path(__file__).resolve().parent / "extra_pages.json"
FETCH_TIMEOUT = 20


def fetch_row(p: dict):
    """A page another Worker renders (the Anthill, the home-help board), read
    over HTTP now and put through extract() like a built page. None when it
    does not answer 200 with HTML."""
    import tempfile
    import urllib.request
    url = p["url"]
    req = urllib.request.Request(url, headers={"User-Agent": "motdang-fleetsearch/1 (+https://motdang.net/find)"})
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
            if r.status != 200 or "html" not in (r.headers.get("content-type") or ""):
                return None
            raw = r.read(READ_CAP)
    except Exception:  # noqa: BLE001 — a page that does not answer keeps its static row
        return None
    base = p.get("base") or "/".join(url.split("/")[:3]) + "/"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rel = url[len(base):].split("?", 1)[0] if url.startswith(base) else "page"
        if not rel or rel.endswith("/"):
            rel += "index.html"
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(raw)
        row = extract(f, p["site"], base, root, {})
    if not row:
        return None
    if p.get("brand"):           # a section's own name on its subpages: "Jobs — รังมด · The Anthill"
        row["title_s"] = tokenise(brand_suffix(row["title"], site_brands(p["site"]) + p["brand"])[0])[:300]
        # … and in their bodies, where it names the section, not the page: the
        # section's own front page is the answer to its name
        for w in p["brand"]:
            row["body_s"] = re.sub(re.escape(tokenise(w)), " ", row["body_s"], flags=re.I)
    row["url"] = url if "?" in url else row["url"]
    row["url_s"] = row["url"].split("//", 1)[-1]
    row.pop("_own", None)
    row["lastmod"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if row["img"].startswith("file:"):
        row["img"] = ""
    return row


def extra_rows(fetch: bool = True):
    """Rows for pages listed in extra_pages.json — pages no local build
    holds. An entry with "fetch": true is read over HTTP at crawl time; its
    title and body, when the entry has them, stand in if the fetch fails.
    Otherwise: site, url, title, abstract, body, and optionally lang, kind,
    img. Everything else as a built page has it."""
    if not EXTRA.exists():
        return []
    rows = []
    for p in json.loads(EXTRA.read_text(encoding="utf-8")):
        if p.get("fetch") and fetch:
            row = fetch_row(p)
            if row:
                rows.append(row)
                continue
            print(f"  extra: {p['url']} did not answer"
                  + ("; its listed text stands in" if p.get("title") else "; left out"), file=sys.stderr)
        if not p.get("title"):
            continue
        url, title, body = p["url"], clean(p["title"]), clean(p.get("body", ""))
        rows.append({
            "site": p["site"], "host": url.split("/")[2], "url": url,
            "title": title[:300], "abstract": clean(p.get("abstract", ""))[:240],
            "lang": p.get("lang", "th"), "lat": None, "lon": None,
            "lastmod": p.get("lastmod") or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "kb": 12, "kind": p.get("kind", "list"), "items": 0, "crumbs": [], "img": p.get("img"),
            "rich": {}, "title_s": tokenise(brand_suffix(title, site_brands(p["site"]))[0])[:300],
            "body_s": tokenise(title + " " + body),
            "url_s": url.split("//", 1)[-1],
        })
    return rows


# What a person's own page is called in the index, Thai first. A page found by
# "ร้านอาหาร" or by "restaurant" is a page of kind food whether or not it uses
# either word.
OWN_KINDS = {
    "shop": ("ร้านค้า", "Shop", "ร้านค้า ร้าน ขายของ", "shop store"),
    "food": ("ร้านอาหาร", "Food", "ร้านอาหาร อาหาร ของกิน", "food restaurant eatery"),
    "service": ("บริการ", "Service", "บริการ ช่าง รับงาน", "service"),
    "me": ("หน้าส่วนตัว", "Personal page", "หน้าส่วนตัว เกี่ยวกับฉัน", "personal page about me"),
    "event": ("งาน", "Event", "งาน กิจกรรม", "event"),
    "group": ("กลุ่ม", "Group", "กลุ่ม ชุมชน", "group community"),
}
OWN_SITE = "sites"
OWN_FEED_CACHE = OUT_DIR / "own_pages_feed.json"


def own_row(p: dict):
    """One page of the page maker (sites.motdang.net) as an index row, or None.

    Everything textual goes into the body - tagline, about, address, each menu
    item with its price, the kind in both languages - so a word on the page
    finds the page. The pin goes in lat/lon, the cover (small copy) is the
    picture, the ways to reach it are counted, and hours and an event date are
    kept in the shapes the Worker reads."""
    import own_pages as op
    url = p.get("url") or ""
    title = clean(str(p.get("title") or ""))
    if not (url.startswith(op.PAGES_HOST) and title):
        return None
    kind = p.get("kind") if p.get("kind") in OWN_KINDS else "shop"
    kth, ken, wth, wen = OWN_KINDS[kind]
    tag, about, addr = (clean(str(p.get(k) or "")) for k in ("tagline", "about", "addr"))
    facts = op.facts_of(p)
    items = " ".join(" ".join(x for x in (i.get("n"), i.get("p"), i.get("note")) if x)
                     for i in facts.get("items", []))
    abstract = tag or about
    if len(abstract) > ABSTRACT_CAP:
        abstract = abstract[:ABSTRACT_CAP].rsplit(" ", 1)[0] + "…"
    body = " ".join(x for x in (title, tag, about, addr, items, wth, wen,
                                "หน้าของร้านเอง own page", p.get("cc") or "") if x)[:BODY_CAP]
    ways = [w for w, k in (("phone", "phone"), ("line", "line"), ("facebook", "facebook"),
                           ("instagram", "instagram"), ("web", "web")) if facts.get(k)]
    ways.sort(key=WAYS.index)
    rich: dict = {}
    if ways:
        rich["ways"] = ways
    sched = op.sched_of(p.get("hours"))
    if sched:
        rich["sched"] = sched
    ev = p.get("event")
    if isinstance(ev, dict) and re.match(r"\d{4}-\d{2}-\d{2}", str(ev.get("start") or "")):
        rich["ev"] = [{"d": ev["start"][:10], "t": title[:80]}]
    lat, lon = p.get("lat"), p.get("lng")
    pin = isinstance(lat, (int, float)) and isinstance(lon, (int, float))
    cover = str(p.get("cover") or "")
    img = next((ph.get("small") for ph in facts.get("photos", []) if ph.get("url") == cover and ph.get("small")), cover)
    return {
        "site": OWN_SITE, "host": url.split("/")[2], "url": url,
        "title": title[:300], "abstract": abstract,
        "lang": str(p.get("lang") or "th")[:5],
        "lat": float(lat) if pin else None, "lon": float(lon) if pin else None,
        "lastmod": (str(p.get("updated") or p.get("published") or "")[:10]
                    or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "kb": 4, "kind": "place" if kind in ("shop", "food", "service") else "page", "items": 0,
        "crumbs": [[kth, None, ken]], "img": img if img.startswith("https://") else "",
        "rich": rich, "title_s": tokenise(title)[:300], "body_s": tokenise(body),
        "url_s": url.split("//", 1)[-1],
    }


def own_rows(fetch: bool = True, fixture=None):
    """Rows for the pages made with the page maker, from its public feed
    (sites.motdang.net/feed.json). A feed that does not answer falls back to
    the last good copy in cache/fleetsearch/; with neither, no rows."""
    sys.path.insert(0, str(REPO / "importers"))
    import own_pages as op
    doc, via = op.fetch_feed(cache=OWN_FEED_CACHE, fixture=fixture, offline=not fetch, timeout=FETCH_TIMEOUT)
    if doc is None:
        print("  own pages: the feed did not answer and no copy is cached; none indexed", file=sys.stderr)
        return []
    if via == "cache":
        print("  own pages: the feed did not answer; the cached copy stands in", file=sys.stderr)
    rows = [r for r in (own_row(p) for p in op._pages_of(doc)) if r]
    return rows


def _same_name(a: str, b: str) -> bool:
    """Two titles that name the same page: equal once the shared tail after
    the last " — " is set aside, or sharing most of their words."""
    a, b = a.lower().strip(), b.lower().strip()
    if " — " in a and " — " in b and a.rsplit(" — ", 1)[1] == b.rsplit(" — ", 1)[1]:
        a, b = a.rsplit(" — ", 1)[0], b.rsplit(" — ", 1)[0]
    if a == b:
        return True
    wa, wb = set(re.findall(r"\w+", a)), set(re.findall(r"\w+", b))
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= 0.6


def dedupe(src: Path, dst: Path) -> dict:
    """One row per address. Several files that claim one canonical are either
    copies of it (another language, an old front page) or pages of their own
    that point at their list (each Ghost stop names /ghost/stops/). The file
    that IS the canonical keeps it; a copy — the same name — is dropped; a
    page of its own is kept at its own address. A later site never repeats an
    address an earlier one wrote, and a row Mot Dang's own build holds wins
    over extra_pages.json. Returns counts."""
    claims: dict = {}
    with open(src, encoding="utf-8") as f:
        for i, line in enumerate(f):
            r = json.loads(line)
            claims.setdefault(r["url"], []).append((i, r.get("_own") or r["url"], r["title"], r["kb"]))
    keep_as: dict = {}                     # line → url, or None to drop
    for url, group in claims.items():
        if len(group) == 1:
            continue
        owner = next((g for g in group if g[1] == url), None) or max(group, key=lambda g: g[3])
        for g in group:
            if g is owner:
                continue
            keep_as[g[0]] = None if (_same_name(g[2], owner[2]) or g[1] == url) else g[1]
    seen, n, dropped, moved = set(), 0, 0, 0
    with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as out:
        for i, line in enumerate(f):
            r = json.loads(line)
            if i in keep_as:
                if keep_as[i] is None:
                    dropped += 1
                    continue
                r["url"] = keep_as[i]
                r["url_s"] = r["url"].split("//", 1)[-1]
                moved += 1
            r.pop("_own", None)
            if r["url"] in seen:
                dropped += 1
                continue
            seen.add(r["url"])
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return {"rows": n, "dropped": dropped, "own_address": moved}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", action="append", help="only these site ids")
    ap.add_argument("--limit", type=int, default=0, help="pages per site (a sample)")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    ap.add_argument("--no-fetch", action="store_true", help="extra pages from their listed text only")
    ap.add_argument("--own-fixture", help="read the own-pages feed from this file")
    a = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    totals = {}
    errors = []
    n = 0
    nobuild: list = []
    fleet = sites(nobuild)
    raw_out = Path(a.out).with_suffix(".raw.jsonl")
    with open(raw_out, "w", encoding="utf-8") as out, Pool(a.jobs, initializer=segmenter) as pool:
        for site, root, base in fleet:
            if a.site and site not in a.site:
                continue
            inner = [r for s, r, _ in fleet if s != site and r != root and root in r.parents]
            lastmods = sitemap_lastmods(root)
            files = sorted(walk(root, inner))
            if a.limit:
                files = files[: a.limit]
            jobs = [(str(p), site, base, str(root), lastmods) for p in files]
            kept = 0
            for row in pool.imap_unordered(_job, jobs, chunksize=64):
                if not row:
                    continue
                if "_error" in row:
                    errors.append(row["_error"])
                    continue
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                kept += 1
                n += 1
            totals[site] = (len(files), kept)
            print(f"  {site:20} {len(files):7} html  {kept:7} pages  {time.time()-t0:6.0f}s", file=sys.stderr)
        # PAGES NO LOCAL BUILD HOLDS — extra_pages.json: the home-help board
        # and the Anthill are served by Workers of their own, so no docs/
        # folder has them.
        if not a.site or "extra" in a.site:
            kept = 0
            for row in extra_rows(fetch=not a.no_fetch):
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                kept += 1
                n += 1
            totals["extra"] = (kept, kept)
            print(f"  {'extra':20} {kept:7} rows", file=sys.stderr)
        # PEOPLE'S OWN PAGES - sites.motdang.net, the page maker's public feed.
        if not a.site or OWN_SITE in a.site:
            kept = 0
            for row in own_rows(fetch=not a.no_fetch, fixture=a.own_fixture):
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                kept += 1
                n += 1
            totals[OWN_SITE] = (kept, kept)
            print(f"  {OWN_SITE:20} {kept:7} rows", file=sys.stderr)
    dd = dedupe(raw_out, Path(a.out))
    raw_out.unlink()
    n = dd["rows"]
    print(f"{n} pages → {a.out} in {time.time()-t0:.0f}s; {dd['dropped']} copies dropped, "
          f"{dd['own_address']} kept at their own address; {len(errors)} errors", file=sys.stderr)
    for sid, url in nobuild:
        print(f"  no build on this disk: {sid} {url}", file=sys.stderr)
    for e in errors[:10]:
        print("   ", e, file=sys.stderr)
    (OUT_DIR / "crawl.json").write_text(json.dumps({
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pages": n, "sites": {k: {"html": v[0], "pages": v[1]} for k, v in totals.items()},
        "dedupe": dd, "no_build": [s for s, _ in nobuild],
        "errors": errors[:50],
    }, ensure_ascii=False, indent=1))
    return 0 if n else 2


if __name__ == "__main__":
    sys.exit(main())
