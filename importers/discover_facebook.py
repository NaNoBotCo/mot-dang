#!/usr/bin/env python3
"""discover_facebook.py — find the places that describe themselves on Facebook,
starting FROM Facebook, for every shelf the site has. Stdlib only.

WHY (Nan, 2026-09-06): "OSM should not be the single or even the first source of
ground truth." Measured that day: 24,059 records, 63% OSM, 1% carrying a
Facebook page. Eight hand-run searches found 46 real Chiang Mai businesses with
active pages — clothing, shoes, board-game cafes, an escape room, clinics,
salons — and 43 of them matched nothing in the catalogue. This importer is that
experiment made systematic: every category and child label in
data/categories.json, Thai and English, both provinces.

HOW. A search restricted to facebook.com returns page URL + title + snippet,
and the snippet is the search engine's read of the page's About tab — often the
hours and the address. Facebook itself serves a logged-out fetcher a shell
(HTTP 400 to a plain fetch, og:title only to a lenient one), so nothing here
ever asks Facebook for anything. Reading a page's About tab needs a logged-in
browser and is the facebook-reader bot's job (BOTS.md, Tier 0); this finds.

WHO RUNS THE SEARCHES — measured 2026-09-06. html.duckduckgo.com answers a
self-identified bot UA with a "select all squares containing a duck" challenge
(HTTP 202) and answers a browser UA with results. We do not pretend to be a
browser to get past bot detection: this script keeps its own name in its UA,
and when it is challenged it stops. The volume goes through the Opus bots
instead, whose web search is a sanctioned tool: `--queue N` prints the next N
queries nobody has run; the bot runs them and writes each result set to
_incoming/fb-search/*.json in the shape below; `--deposit` folds those into the
cache exactly as if this script had fetched them, and `--report` matches and
counts. A keyed search API (Brave, Bing) can be wired into fetch() later — see
source_register.json — and would make the direct path live again.

    deposit shape, one JSON file, a list of:
      {"q": "site:facebook.com ร้านรองเท้า เชียงใหม่", "fetched": "2026-09-06",
       "results": [{"url": "...", "title": "...", "snippet": "..."}], "via": "facebook-reader webSearch"}
    (prov/cat/child/lang/word are recovered from the query text against the vocabulary.)

WHAT IT WRITES.
  cache/fb_discovery/queries/<sha1>.json   one file per query, dated; a query
                                           fetched within --fresh-days is not
                                           re-run, so the pass is resumable and
                                           a re-run costs only what changed.
  data/curated/fb_discovery.json           every page found, with its shelf,
                                           its query, the snippet, and a MATCH
                                           against the catalogue — by page
                                           identity (certain) or by whole name
                                           (check it) — plus per-shelf
                                           denominators. A row that matches
                                           nothing is a LEAD, not a record, and
                                           "no match" is not "absent": it says
                                           no record carries this page or this
                                           name, which is all a lookup can say.

WHAT IT WILL NOT DO. It does not write records: a record needs a person (or the
reader bot) to have read the page. It does not token-match names — "heritage"
matched a hotel, "พริกหวาน" a kitchen, "serene" a resort, "ปังปัง" a dentist
when that was tried; only the whole name, with city and generic words removed,
counts, and even that is graded "check". It does not decide a page is in the
province from the search alone: `mentions_province` is a flag, not a filter.

    python3 importers/discover_facebook.py                 both provinces, all shelves
    python3 importers/discover_facebook.py --only shopping --province cm
    python3 importers/discover_facebook.py --dry-run       print the query list
    python3 importers/discover_facebook.py --limit 40      a short polite run
    python3 importers/discover_facebook.py --report        rebuild the JSON from cache, no network
    python3 importers/discover_facebook.py --queue 60      next 60 unrun queries, as JSON, for a bot
    python3 importers/discover_facebook.py --deposit _incoming/fb-search/2026-09-06.json

Politeness: one request at a time, --pause seconds (default 3) plus jitter,
a bot UA that names us, and it stops — saving progress — the moment the
endpoint answers with a challenge page instead of results.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fburl import fb_url_of, fb_key  # noqa: E402

CATS = ROOT / "data" / "categories.json"
VOCAB = ROOT / "data" / "curated" / "fb_vocabulary.json"
CANON = ROOT / "data" / "canonical"
QCACHE = ROOT / "cache" / "fb_discovery" / "queries"
OUT = ROOT / "data" / "curated" / "fb_discovery.json"

UA = "MotDangBot/1.0 (+https://motdang.net/about.html; directory discovery; 530kings@proton.me)"
ENDPOINT = "https://html.duckduckgo.com/html/"

PROVINCES = {
    "cm": {"th": "เชียงใหม่", "en": "Chiang Mai", "words": ["เชียงใหม่", "chiang mai", "chiangmai", "cnx"]},
    "cr": {"th": "เชียงราย", "en": "Chiang Rai", "words": ["เชียงราย", "chiang rai", "chiangrai"]},
}
# Words that carry no identity when two names are compared.
GENERIC = {"ร้าน", "shop", "store", "official", "page", "the", "and", "&", "co", "ltd",
           "จำกัด", "บริษัท", "หจก", "สาขา", "chiangmai", "chiang", "mai", "cnx", "เชียงใหม่",
           "เชียงราย", "chiangrai", "rai", "thailand", "ประเทศไทย"}
# Labels that are not a trade anyone searches Facebook for; they would only
# pull noise. Kept short and named so a future pass can widen it.
SKIP_LABELS = {"Featured", "แนะนำ", "All", "ทั้งหมด"}


# ---- vocabulary -------------------------------------------------------------

def _split(label):
    """'ศาลเจ้า-ศาลหลักเมือง' -> two words; 'Shrines & City Pillars' -> two."""
    parts = re.split(r"\s*[-/&·,]\s*|\s+และ\s+|\s+and\s+|\s+or\s+", label or "")
    return [p.strip() for p in parts if p and p.strip() and p.strip() not in SKIP_LABELS]


def vocabulary(only=None):
    """(cat_key, child_key, lang, word) for every shelf label — tier 1."""
    doc = json.loads(CATS.read_text(encoding="utf-8"))
    out = []
    for cat in doc["categories"]:
        if only and cat.get("key") != only:
            continue
        for lang in ("th", "en"):
            for w in _split(cat.get(lang)):
                out.append((cat["key"], None, lang, w))
        for ch in cat.get("children") or []:
            for lang in ("th", "en"):
                for w in _split(ch.get(lang)):
                    out.append((cat["key"], ch.get("key"), lang, w))
    seen, uniq = set(), []
    for row in out:
        k = row[3].lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(row)
    return uniq


def vocab2(only=None):
    """(group, None, lang, word) for the self-description words — tier 2.

    Facebook's own page-category strings, which is what a business picks to say
    what it is. Seeded by hand and grown by reconcile() from the fbCategories
    the reader harvests, so the vocabulary comes to be written by this city's
    businesses rather than by us.
    """
    if not VOCAB.exists():
        return []
    doc = json.loads(VOCAB.read_text(encoding="utf-8"))
    out = []
    for w in doc.get("tier2_words") or []:
        if only and w.get("group") != only:
            continue
        out.append((w.get("group", "fbcat"), None, w.get("lang", "th"), w["w"]))
    return out


def amphoe(prov):
    if not VOCAB.exists():
        return []
    doc = json.loads(VOCAB.read_text(encoding="utf-8"))
    return (doc.get("geo", {}).get(prov, {}) or {}).get("amphoe") or []


def yielded_words(prov):
    """Words whose province query has already returned at least one page.

    The amphoe pass is adaptive: a word earns its 25 (or 18) district queries
    only once it has proved it returns anything at all. A word that returns
    nothing province-wide costs one query, not forty-four.
    """
    good = set()
    for p in QCACHE.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if rec.get("prov") != prov or rec.get("area"):
            continue
        if rec.get("results"):
            good.add(rec["word"])
    return good


def queries(provinces, only=None, tier="all"):
    """Every query, in the order they should be run.

    tier 1  shelf label x province        — the site's own tree, both languages
    tier 2  self-description x province   — what businesses call themselves
    tier 3  yielding word x AMPHOE        — the pass that covers the province
            rather than the city; adaptive, see yielded_words()
    """
    want = {"all": {1, 2, 3}, "1": {1}, "2": {2}, "3": {3}, "12": {1, 2}}[str(tier)]
    for prov in provinces:
        P = PROVINCES[prov]
        base = []
        if 1 in want:
            base += [(c, ch, l, w, 1) for c, ch, l, w in vocabulary(only)]
        if 2 in want:
            base += [(c, ch, l, w, 2) for c, ch, l, w in vocab2(only)]
        for cat, child, lang, word, tr in base:
            city = P[lang]
            yield {"prov": prov, "cat": cat, "child": child, "lang": lang, "word": word,
                   "tier": tr, "area": None, "q": f"site:facebook.com {word} {city}"}
        if 3 in want:
            good = yielded_words(prov)
            seen = set()
            for cat, child, lang, word in list(vocabulary(only)) + list(vocab2(only)):
                if word not in good or (word, lang) in seen:
                    continue
                seen.add((word, lang))
                for amp in amphoe(prov):
                    yield {"prov": prov, "cat": cat, "child": child, "lang": lang, "word": word,
                           "tier": 3, "area": amp, "q": f"site:facebook.com {word} {amp}"}


# ---- fetching --------------------------------------------------------------

class Challenge(Exception):
    """The endpoint answered with a bot challenge, not results. Stop politely."""


def fetch(q):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"q": q})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "th,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", "replace")
    results = parse(body)
    # DDG's normal page also contains the word "bots"; the challenge page is
    # the one with no results AND the instruction to complete a challenge.
    if not results and re.search(r"complete the following challenge|Select all squares|captcha", body, re.I):
        raise Challenge()
    return results


def parse(body):
    out = []
    for block in body.split('<div class="result ')[1:]:
        m = re.search(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        href, title = m.group(1), m.group(2)
        target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
        s = re.search(r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</div>', block, re.S)
        snippet = (s.group(1) or s.group(2) or "") if s else ""
        clean = lambda x: html.unescape(re.sub(r"<.*?>", "", x)).strip()
        out.append({"url": html.unescape(target), "title": clean(title), "snippet": clean(snippet)})
    return out


def qpath(q):
    return QCACHE / (hashlib.sha1(q.encode("utf-8")).hexdigest()[:16] + ".json")


def unrun(qs, fresh_days):
    """The queries with no fresh file in the cache, in vocabulary order."""
    today = dt.date.today()
    out = []
    for spec in qs:
        p = qpath(spec["q"])
        if p.exists():
            prev = json.loads(p.read_text(encoding="utf-8"))
            if (today - dt.date.fromisoformat(prev["fetched"])).days < fresh_days:
                continue
        out.append(spec)
    return out


def deposit(path, provinces, only=None):
    """Fold result sets a bot ran (through its own web search) into the cache,
    in the same file shape fetch() would have written. Returns (accepted, unknown)."""
    QCACHE.mkdir(parents=True, exist_ok=True)
    spec_by_q = {s["q"]: s for s in queries(provinces, only, "all")}
    # A bot may write the query without the site: prefix or with extra spaces.
    def canon(q):
        q = re.sub(r"\s+", " ", q.strip())
        return q if q.startswith("site:facebook.com ") else "site:facebook.com " + q
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = entries.get("searches") or entries.get("results") or [entries]
    accepted = unknown = 0
    for e in entries:
        q = canon(e.get("q") or e.get("query") or "")
        spec = spec_by_q.get(q)
        if not spec:
            unknown += 1
            print(f"  ? not a vocabulary query, kept under its own text: {q}", file=sys.stderr)
            spec = {"prov": e.get("prov") or ("cr" if "เชียงราย" in q or "Chiang Rai" in q else "cm"),
                    "cat": e.get("cat") or "unshelved", "child": e.get("child"),
                    "lang": "th" if re.search(r"[ก-๙]", q) else "en", "tier": e.get("tier") or 0,
                    "area": e.get("area"), "word": e.get("word") or q.replace("site:facebook.com ", ""), "q": q}
        results = []
        for r in e.get("results") or []:
            if r.get("url"):
                results.append({"url": r["url"], "title": r.get("title") or "", "snippet": r.get("snippet") or ""})
        rec = dict(spec, fetched=e.get("fetched") or dt.date.today().isoformat(), results=results,
                   error=None, via=e.get("via") or f"deposit:{Path(path).name}")
        qpath(spec["q"]).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        accepted += 1
    return accepted, unknown


def run_queries(qs, pause, fresh_days, limit):
    QCACHE.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    ran = cached = 0
    for spec in qs:
        p = qpath(spec["q"])
        if p.exists():
            prev = json.loads(p.read_text(encoding="utf-8"))
            age = (today - dt.date.fromisoformat(prev["fetched"])).days
            if age < fresh_days:
                cached += 1
                continue
        if limit is not None and ran >= limit:
            break
        try:
            results = fetch(spec["q"])
        except Challenge:
            print(f"\n  challenge page after {ran} queries — stopping; progress is saved. "
                  f"Re-run later; cached queries are skipped.", file=sys.stderr)
            break
        except Exception as e:  # network hiccup: record it and move on
            results = None
            print(f"  ! {spec['q']}: {e}", file=sys.stderr)
        rec = dict(spec, fetched=today.isoformat(),
                   results=results if results is not None else [],
                   error=None if results is not None else "fetch failed")
        p.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        ran += 1
        print(f"  {ran:4d}  {len(rec['results']):2d}  {spec['q']}")
        time.sleep(pause + random.uniform(0, pause / 2))
    return ran, cached


# ---- matching --------------------------------------------------------------

def _norm(s):
    return re.sub(r"[^a-z0-9ก-๙]", "", str(s or "").lower())


def _identity(name):
    """A name with the city and the generic words taken out, normalised."""
    words = re.split(r"[\s|/·,\-–—()]+", str(name or "").lower())
    words = [w for w in words if w and w not in GENERIC]
    return _norm("".join(words))


def load_catalogue():
    recs = []
    for prov in ("cm", "cr"):
        f = CANON / f"{prov}.json"
        if f.exists():
            recs += json.loads(f.read_text(encoding="utf-8"))
    by_key, by_name = {}, {}
    for r in recs:
        a = r.get("attrs") or {}
        for v in (a.get("facebook"), r.get("website"), a.get("website")):
            k = fb_key(v) if v else None
            if k:
                by_key.setdefault(k, r["id"])
        for n in (r.get("name"), r.get("nameEn"), r.get("nameTh")):
            i = _identity(n)
            if len(i) >= 6:
                by_name.setdefault(i, []).append((r["id"], n))
    return by_key, by_name


def page_name(title):
    """'รสริน รองเท้าแฟชั่น-rosarin | Chiang Mai | Facebook' -> (name, city hint)."""
    parts = [p.strip() for p in re.split(r"\s+\|\s+|\s+-\s+Facebook$|\s+·\s+", title) if p.strip()]
    parts = [p for p in parts if p.lower() != "facebook"]
    name = parts[0] if parts else title
    hint = parts[1] if len(parts) > 1 else ""
    return name, hint


def match(name, key, by_key, by_name):
    if key and key in by_key:
        return {"id": by_key[key], "how": "facebook page identity", "grade": "link"}
    i = _identity(name)
    if len(i) >= 6 and i in by_name:
        rid, rn = by_name[i][0]
        return {"id": rid, "how": f"whole name = {rn!r}", "grade": "name — check it"}
    return None


# ---- report ----------------------------------------------------------------

def build_report(provinces):
    by_key, by_name = load_catalogue()
    rows, seen = [], {}
    n_q = 0
    for p in sorted(QCACHE.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec["prov"] not in provinces:
            continue
        n_q += 1
        for res in rec["results"]:
            url = fb_url_of(res["url"])
            k = fb_key(url) if url else None
            if not k:
                continue
            # Posts, videos, groups and reels are not pages: keep the page they
            # belong to as the lead, once.
            path = urllib.parse.urlsplit(url).path
            kind = "page"
            if re.search(r"/(posts|videos|photos|reels?|events|groups|mentions)(/|$)", path):
                kind = path.split("/")[2] if path.count("/") >= 2 else "post"
            name, hint = page_name(res["title"])
            text = (res["title"] + " " + res["snippet"]).lower()
            prov_words = PROVINCES[rec["prov"]]["words"]
            row = seen.get(k)
            if row is None:
                row = {"key": k, "url": url if kind == "page" else "https://www.facebook.com/" + (k.split(":")[1] if k.startswith("profile:") else k),
                       "name": name, "city_hint": hint, "snippet": res["snippet"],
                       "prov": rec["prov"], "shelves": [], "queries": [],
                       "mentions_province": any(w in text for w in prov_words),
                       "seen_as": [kind], "fetched": rec["fetched"],
                       "match": match(name, k, by_key, by_name), "status": "lead"}
                seen[k] = row
                rows.append(row)
            shelf = rec["cat"] + ("/" + rec["child"] if rec["child"] else "")
            row.setdefault("areas", [])
            if rec.get("area") and rec["area"] not in row["areas"]:
                row["areas"].append(rec["area"])
            if shelf not in row["shelves"]:
                row["shelves"].append(shelf)
            if rec["q"] not in row["queries"]:
                row["queries"].append(rec["q"])
            if kind not in row["seen_as"]:
                row["seen_as"].append(kind)
            if kind == "page" and not row["url"].endswith(k) and not k.startswith("profile:"):
                row["url"] = url
    # SATURATION — the only honest reading of "complete". Per shelf, in the order
    # the queries were run: how many pages each query added that no earlier query
    # had seen. A shelf whose last queries are still finding new pages is not
    # finished; one whose last 8 queries added under 10% new is saturated FOR THIS
    # VOCABULARY, which is a statement about our searching, never about the city.
    order = []
    for p in sorted(QCACHE.glob("*.json"), key=lambda f: f.stat().st_mtime):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec["prov"] in provinces:
            order.append(rec)
    sat, seen_keys = {}, {}
    for rec in order:
        shelf = rec["cat"] + ("/" + rec["child"] if rec["child"] else "")
        s = sat.setdefault(shelf, {"queries": 0, "returned": 0, "new": 0, "recent": []})
        known = seen_keys.setdefault(shelf, set())
        fresh = 0
        for res in rec["results"]:
            k = fb_key(res["url"])
            if not k:
                continue
            s["returned"] += 1
            if k not in known:
                known.add(k)
                fresh += 1
        s["queries"] += 1
        s["new"] += fresh
        s["recent"] = (s["recent"] + [fresh])[-8:]

    by_shelf = {}
    for row in rows:
        for s in row["shelves"]:
            d = by_shelf.setdefault(s, {"pages": 0, "matched_link": 0, "matched_name": 0, "unmatched": 0, "mentions_province": 0})
            d["pages"] += 1
            if row["match"] is None:
                d["unmatched"] += 1
            elif row["match"]["grade"] == "link":
                d["matched_link"] += 1
            else:
                d["matched_name"] += 1
            d["mentions_province"] += bool(row["mentions_province"])
    for shelf, d in by_shelf.items():
        s = sat.get(shelf) or {}
        recent, ran = s.get("recent") or [], s.get("queries", 0)
        d["queries_run"] = ran
        d["new_in_last_8_queries"] = sum(recent)
        d["state"] = ("not started" if not ran else
                      "searching" if ran < 8 else
                      "saturated for this vocabulary" if sum(recent) <= max(1, 0.1 * (s.get("returned") or 1)) else
                      "still finding")
    counts = {
        "queries_on_disk": n_q,
        "pages": len(rows),
        "matched_link": sum(1 for r in rows if r["match"] and r["match"]["grade"] == "link"),
        "matched_name": sum(1 for r in rows if r["match"] and r["match"]["grade"] != "link"),
        "unmatched": sum(1 for r in rows if r["match"] is None),
        "mentions_province": sum(1 for r in rows if r["mentions_province"]),
        "by_province": {p: sum(1 for r in rows if r["prov"] == p) for p in provinces},
    }
    rows.sort(key=lambda r: (r["shelves"][0], r["match"] is not None, r["name"]))
    doc = {
        "_readme": [
            "Facebook-first discovery — importers/discover_facebook.py. Nan, 2026-09-06: 'OSM should not",
            "be the single or even the first source of ground truth.' Every row is a Facebook page a",
            "search engine returned for one of this site's own shelf words plus the province name.",
            "A row is a LEAD. `match` says whether the catalogue already carries the page (grade 'link',",
            "certain) or a record of the same whole name (grade 'name — check it'); null means no record",
            "carries this page or this name — which is NOT the same as the place being absent from OSM,",
            "and never a claim about the city. `mentions_province` is a flag, not a filter: the engine",
            "returns pages from elsewhere and a person (or the reader bot) decides. `snippet` is the",
            "engine's read of the page's About tab and often already holds hours and an address; it is",
            "dated by `fetched` and is not a source until the page itself has been read.",
            "The record is made by the facebook-reader bot (BOTS.md Tier 0), which reads the About tab in",
            "a logged-in browser and writes data/curated/additions-*.json with type 'own-facebook'.",
        ],
        "_built": dt.date.today().isoformat(),
        "counts": counts,
        "by_shelf": dict(sorted(by_shelf.items())),
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return counts, by_shelf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--province", default="both", choices=["cm", "cr", "both"])
    ap.add_argument("--only", help="one category key from data/categories.json")
    ap.add_argument("--limit", type=int, help="run at most this many new queries")
    ap.add_argument("--fresh-days", type=int, default=30, help="a query fetched within N days is not re-run")
    ap.add_argument("--pause", type=float, default=3.0)
    ap.add_argument("--dry-run", action="store_true", help="print the query list and exit")
    ap.add_argument("--report", action="store_true", help="rebuild the JSON from cache; no network")
    ap.add_argument("--tier", default="all", choices=["all", "1", "2", "3", "12"],
                    help="1 shelf labels, 2 self-description words, 3 amphoe sweep")
    ap.add_argument("--status", action="store_true", help="how far along the sweep is; no network")
    ap.add_argument("--queue", type=int, metavar="N", help="print the next N unrun queries as JSON (for a bot) and exit")
    ap.add_argument("--deposit", metavar="FILE", help="fold a bot's result sets into the cache, then report")
    a = ap.parse_args()
    provinces = ["cm", "cr"] if a.province == "both" else [a.province]

    if a.status:
        status(provinces, a.only)
        return 0
    if a.queue is not None:
        todo = unrun(list(queries(provinces, a.only, a.tier)), a.fresh_days)
        print(json.dumps(todo[:a.queue], ensure_ascii=False, indent=1))
        print(f"{len(todo)} unrun of {len(list(queries(provinces, a.only, a.tier)))}; printed {min(a.queue, len(todo))}", file=sys.stderr)
        return 0
    if a.deposit:
        acc, unk = deposit(a.deposit, provinces, a.only)
        print(f"deposited {acc} result sets ({unk} outside the vocabulary)")
        a.report = True

    if not a.report:
        qs = list(queries(provinces, a.only, a.tier))
        if a.dry_run:
            for q in qs:
                print(f"{q['prov']}  {q['cat']:<12} {q['child'] or '-':<18} {q['q']}")
            print(f"\n{len(qs)} queries", file=sys.stderr)
            return 0
        print(f"{len(qs)} queries across {len(provinces)} province(s); pause {a.pause}s")
        ran, cached = run_queries(qs, a.pause, a.fresh_days, a.limit)
        print(f"\nran {ran}, skipped {cached} fresh in cache")
    counts, by_shelf = build_report(provinces)
    print(f"\n{OUT.relative_to(ROOT)}")
    for k, v in counts.items():
        print(f"  {k:18} {v}")
    empties = [s for s, d in by_shelf.items() if d["unmatched"] >= 5]
    print(f"\n{len(by_shelf)} shelves touched; {len(empties)} with 5+ unmatched pages")
    status(provinces, a.only)
    return 0


def status(provinces, only=None):
    """How far along the sweep is — the answer to 'is it complete yet'."""
    total = len(list(queries(provinces, only, "12")))
    todo12 = len(unrun(list(queries(provinces, only, "12")), 30))
    print(f"\nSWEEP  tier 1+2: {total - todo12}/{total} queries run ({todo12} to go)")
    if OUT.exists():
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        st = {}
        for d in doc.get("by_shelf", {}).values():
            st[d.get("state", "?")] = st.get(d.get("state", "?"), 0) + 1
        print("       shelves:", ", ".join(f"{v} {k}" for k, v in sorted(st.items())))
        print(f"       leads: {doc['counts']['pages']} pages, {doc['counts']['unmatched']} matching no record")
    # Count the generator itself, not an estimate: queries() dedupes a word that
    # appears in both vocabularies, so multiplying words by districts overstates it.
    t3 = list(queries(provinces, only, "3"))
    print(f"       tier 3 (amphoe) unlocked so far: {len(t3)} queries "
          f"({len(unrun(t3, 30))} to go)")


if __name__ == "__main__":
    sys.exit(main())
