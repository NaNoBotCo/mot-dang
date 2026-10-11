#!/usr/bin/env python3
"""Hotel amenities from each lodging's own website: pool, airport shuttle, bar, food on site.

    python3 tools/hotel_amenities.py              # fetch what is not cached, then write
    python3 tools/hotel_amenities.py --offline    # write from the cache only
    python3 tools/hotel_amenities.py --retry-errors
    python3 tools/hotel_amenities.py --sample N   # print N random yes snippets per fact

Input: data/canonical/{cm,cr}.json, lodging = cat contains 'hotel' or sub names
hotel/hostel/guesthouse/resort/homestay/serviced. Also reads the raw OSM tags in
cache/overpass/<prov>/*.json and Overture categories in cache/overture/cmcr.jsonl.gz.

Output: data/curated/hotel_amenities.json
  {"_meta": {...}, "<record id>": {"pool": {value, evidence, url, fetched, source}, ...}}
value is "yes", or "no" only where a page or tag states it. An absent fact is unknown.

Page cache: cache/hotel_amenities/pages/<sha1 of url>.json (cache/ is gitignored).
Stdlib only.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import gzip
import hashlib
import html
import html.parser
import json
import random
import re
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "hotel_amenities" / "pages"
OUT = ROOT / "data" / "curated" / "hotel_amenities.json"
TODAY = dt.date.today().isoformat()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
TIMEOUT = 20
PARALLEL = 12
MAX_EXTRA = 4
MAX_BYTES = 3_000_000

SKIP_HOSTS = re.compile(
    r"(^|\.)(facebook\.com|fb\.me|fb\.com|m\.me|instagram\.com|line\.me|lin\.ee|"
    r"booking\.[a-z.]+|agoda\.[a-z.]+|tripadvisor\.[a-z.]+|linktr\.ee|airbnb[a-z]*\.[a-z.]+|abnb\.me|air\.tl|"
    r"oyorooms\.com|trip\.com|expedia\.[a-z.]+|hotels\.com|traveloka\.com|tiktok\.com|"
    r"youtube\.com|youtu\.be|gmail\.com|plus\.google\.com|google\.com|goo\.gl|maps\.app\.goo\.gl|"
    r"renthub\.in\.th|onab\.go\.th|wa\.me|twitter\.com|x\.com|hostelworld\.com|"
    r"ddproperty\.com|hipflat\.co\.th|wongnai\.com)$")

LODGING_SUB = re.compile(r"hotel|hostel|guest-?house|resort|homestay|serviced")


# ---------------------------------------------------------------- records

def lodging_records():
    out = []
    for prov in ("cm", "cr"):
        for r in json.load(open(ROOT / "data" / "canonical" / f"{prov}.json")):
            cat = r.get("cat") or []
            sub = r.get("sub") or []
            cat = [cat] if isinstance(cat, str) else cat
            sub = [sub] if isinstance(sub, str) else sub
            if any("hotel" in c for c in cat) or any(LODGING_SUB.search(s) for s in sub):
                out.append(r)
    return out


def host_of(url):
    try:
        h = urllib.parse.urlsplit(url).hostname or ""
    except ValueError:
        return ""
    h = h.lower()
    return h[4:] if h.startswith("www.") else h


def norm_url(url):
    url = (url or "").strip()
    if not url:
        return None
    if not re.match(r"https?://", url, re.I):
        url = "http://" + url.lstrip("/")
    return url.split("#")[0]


def own_site(r):
    u = norm_url(r.get("website"))
    if not u:
        return None
    h = host_of(u)
    if not h or "." not in h or SKIP_HOSTS.search(h):
        return None
    return u


# ---------------------------------------------------------------- fetch + cache

class Extract(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5",
             "h6", "section", "article", "header", "footer", "nav", "table", "dd", "dt", "option",
             "figcaption", "blockquote", "a", "button", "span", "label", "title"}
    SKIP = {"script", "style", "noscript", "svg", "template", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.skip, self.title = [], [], 0, ""
        self._a, self._in_title = None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "meta" and (a.get("name") or a.get("property") or "").lower() in (
                "description", "og:description", "og:title"):
            self.parts.append("\n" + (a.get("content") or "") + "\n")
        if tag in self.SKIP and tag != "head":
            self.skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "img" and a.get("alt"):
            self.parts.append("\n" + a["alt"] + "\n")
        if tag == "a" and a.get("href"):
            self._a = [a["href"], []]

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in self.SKIP and tag != "head" and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "a" and self._a:
            self.links.append([self._a[0], " ".join("".join(self._a[1]).split())[:80]])
            self._a = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            self.parts.append("\n" + data + "\n")
            return
        if self.skip:
            return
        self.parts.append(data)
        if self._a is not None:
            self._a[1].append(data)


def decode(raw, ctype):
    cs = None
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    if m:
        cs = m.group(1)
    else:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", raw[:4000], re.I)
        if m:
            cs = m.group(1).decode("ascii", "ignore")
    for c in [cs, "utf-8", "cp874"]:
        if not c:
            continue
        c = {"tis-620": "cp874", "windows-874": "cp874", "iso-8859-11": "cp874"}.get(c.lower(), c)
        try:
            return raw.decode(c)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
try:
    SSL_CTX.set_ciphers("DEFAULT@SECLEVEL=0")
    SSL_CTX.minimum_version = ssl.TLSVersion.TLSv1
except (ssl.SSLError, ValueError):
    pass


def cache_path(url):
    return CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")


OFFLINE = False


def fetch(url):
    """One GET, cached. Returns the cache dict."""
    p = cache_path(url)
    if p.exists():
        return json.loads(p.read_text())
    if OFFLINE:
        return {"url": url, "error": "not cached"}
    rec = {"url": url, "fetched": TODAY}
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en,th;q=0.8", "Accept-Encoding": "gzip"})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
            raw = r.read(MAX_BYTES)
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            ctype = r.headers.get("Content-Type", "")
            rec.update(status=r.status, final=r.geturl(), ctype=ctype)
        if "html" not in ctype and not raw.lstrip()[:200].lower().startswith((b"<!doctype", b"<html")):
            rec["text"], rec["links"], rec["title"] = "", [], ""
        else:
            ex = Extract()
            try:
                ex.feed(decode(raw, ctype))
            except Exception:
                pass
            text = "".join(ex.parts)
            text = re.sub(r"[ \t\r\f\v ]+", " ", text)
            text = re.sub(r"\n\s*\n+", "\n", text).strip()
            rec["text"] = text[:400_000]
            rec["links"] = ex.links[:1500]
            rec["title"] = " ".join(ex.title.split())[:200]
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:160]}"
    p.write_text(json.dumps(rec, ensure_ascii=False))
    return rec


LINK_WORDS = re.compile(
    r"facilit|amenit|room|service|dining|restaurant|pool|transfer|about|accommodation|"
    r"shuttle|bar\b|food|cafe|stay|feature|overview|ห้องพัก|บริการ|สิ่งอำนวยความสะดวก|"
    r"ร้านอาหาร|ห้องอาหาร|สระว่ายน้ำ|รถรับส่ง|เกี่ยวกับ|ที่พัก", re.I)
LINK_SKIP = re.compile(r"\.(jpe?g|png|gif|webp|pdf|zip|mp4|mp3|svg|ics|docx?)(\?|$)|"
                       r"mailto:|tel:|javascript:|whatsapp|/wp-login|/cart|/checkout|"
                       r"/feed|\?replytocom|/tag/|/author/|/category/", re.I)


def pick_links(page, start):
    base = page.get("final") or start
    bh = host_of(base)
    sh = host_of(start)
    # a start URL with a path (chain sites: /chiang-mai/) keeps sub-pages under that path
    sp = urllib.parse.urlsplit(base if host_of(base) == host_of(start) else start).path or "/"
    if not sp.endswith("/"):
        last = sp.rsplit("/", 1)[-1]
        sp = sp.rsplit("/", 1)[0] + "/" if "." in last else sp + "/"
    prefix = "/" if re.fullmatch(r"/((th|en|th-th|en-us|index)/)?", sp) else sp
    seen, scored = set(), []
    for href, text in page.get("links") or []:
        if LINK_SKIP.search(href):
            continue
        u = urllib.parse.urljoin(base, html.unescape(href)).split("#")[0]
        if not u.startswith("http"):
            continue
        h = host_of(u)
        if h not in (bh, sh):
            continue
        path = urllib.parse.urlsplit(u).path or "/"
        if prefix != "/" and not path.startswith(prefix):
            continue
        if u.rstrip("/") in (start.rstrip("/"), base.rstrip("/")) or u in seen:
            continue
        seen.add(u)
        hay = urllib.parse.unquote(u) + " " + text
        hits = LINK_WORDS.findall(hay)
        if hits:
            s = len(hits) + (3 if re.search(r"facilit|amenit|สิ่งอำนวย|pool|สระ|transfer|shuttle|รับส่ง|dining|"
                                            r"restaurant|ห้องอาหาร|ร้านอาหาร|service|บริการ", hay, re.I) else 0)
            scored.append((-s, len(u), u))
    scored.sort()
    out, parents = [], Counter()
    for _, _, u in scored:
        key = re.sub(r"/(th|en)(/|$)", "/", u.rstrip("/"))
        if key in {re.sub(r"/(th|en)(/|$)", "/", x.rstrip("/")) for x in out}:
            continue
        path = urllib.parse.urlsplit(u).path.rstrip("/")
        parent = path.rsplit("/", 1)[0]
        kind = "room" if re.search(r"room|ห้องพัก|suite|villa|deluxe|superior|standard|twin|double", path, re.I) else parent
        if parents[kind] >= 2 or parents[parent] >= 2:
            continue
        parents[kind] += 1
        if kind != parent:
            parents[parent] += 1
        out.append(u)
        if len(out) == MAX_EXTRA:
            break
    return out


def alternates(url):
    """Other spellings of a start URL to try when it does not answer: www / bare, https / http."""
    sp = urllib.parse.urlsplit(url)
    h = sp.hostname or ""
    hs = [h[4:]] if h.startswith("www.") else ["www." + h]
    out = []
    for scheme in ([sp.scheme] + [x for x in ("https", "http") if x != sp.scheme]):
        for host in [h] + hs:
            u = urllib.parse.urlunsplit((scheme, host, sp.path or "/", sp.query, ""))
            if u.rstrip("/") != url.rstrip("/"):
                out.append(u)
    return out[:3]


def fetch_home(start):
    home = fetch(start)
    if not home.get("error") and (home.get("status") or 0) < 400:
        return home
    alts = alternates(start)
    sp = urllib.parse.urlsplit(start)
    if (sp.path.strip("/") or sp.query) and home.get("status") in (404, 410) or "404" in str(home.get("error", "")):
        alts.append(urllib.parse.urlunsplit((sp.scheme, sp.netloc, "/", "", "")))
    for alt in alts:
        a = fetch(alt)
        if not a.get("error") and (a.get("status") or 0) < 400 and a.get("text"):
            a = dict(a, via_alternate=alt)
            return a
    return home


def crawl_site(urls):
    """Fetch every start URL of one host and its extra pages, one request at a time."""
    result = {}
    for start in urls:
        home = fetch_home(start)
        pages = [home]
        if not home.get("error") and home.get("text") is not None:
            for u in pick_links(home, start):
                if not cache_path(u).exists():
                    time.sleep(0.4)
                pages.append(fetch(u))
        result[start] = pages
    return result


# ---------------------------------------------------------------- detection

def S(p):
    return re.compile(p, re.I)


# off-site context: a pool/bar/restaurant "nearby" is not on site
NEAR = S(r"\bnear(by)?\b|\bclose to\b|\bwalking distance\b|\bwithin (a )?\d|\bminutes?\b|\bmins?\b|"
         r"\bkm\b|\bkilomet|\bmetres?\b|\bmeters?\b|\baway\b|\bsurround|\baround (the )?(hotel|corner|area)|"
         r"\bneighbou?rhood\b|\bnext door\b|\bopposite\b|\bacross (the|from)\b|\bstep(s)? (away|from)\b|"
         r"ใกล้|ห่าง|นาที|กม\.|กิโลเมตร|เมตร|รอบๆ|ละแวก|ติดกับ|ตรงข้าม|เดินถึง|เดินไป")

FACTS = {
    "pool": {
        "yes": [
            (3, S(r"\b(swimming|infinity|outdoor|indoor|rooftop|roof-top|salt-?water|plunge|private|lap|"
                  r"kids'?|children'?s?|heated|lagoon|jacuzzi and)[ -]pools?\b")),
            (3, S(r"\bpool ?villas?\b|\bpool ?access\b|\bpool ?side\b|\bpoolside\b|\bpool ?bar\b|\bpool ?view\b|"
                  r"\bpool ?deck\b|\bpool ?area\b|\bpool ?suite")),
            (3, S(r"สระว่ายน้ำ|พูล ?วิลล่า|พูลวิลล่า|พูลวิลล่า|พูลวิล่า")),
            (2, S(r"\bpools?\b")),
            (1, S(r"สระน้ำ")),
        ],
        "trap": S(r"pool ?tables?|\bcar ?-?pool|liverpool|whirlpool|pool ?cleaning|pool ?of |pool ?(hall|party|parties)|"
                  r"\bbilliards?\b|snooker|\bpool ?noodle|dead ?pool|\bpool ?(fund|resources|staff)|talent ?pool|"
                  r"gene ?pool|pool ?fence|swimming pool (contractor|construction|equipment|supplies)|รับสร้างสระ|"
                  r"ทำความสะอาดสระ|สระน้ำ ?(ใน|ของ) ?วัด|สระบัว|บ่อ"),
        "no": [S(r"\b(?:no|without|don'?t have|do not have|does not have|doesn'?t have|there is no|not have)"
                 r" (?:a |any )?(?:swimming )?pool\b(?! ?(tables?|view|access|party|villas?|parties|cleaning|fence|towels?|toys|heat|lifeguard|use|after|noise|deck|bar))"),
               S(r"ไม่มีสระว่ายน้ำ|ไม่มีสระน้ำ")],
        "near": True,
    },
    "shuttle": {
        "yes": [
            (3, S(r"\bairport[ -]?(transfers?|shuttles?|pick ?-?ups?|pickups?|drop ?-?offs?|"
                  r"transport(ation)?|limousines?|limo|service|run|taxi service)\b")),
            (3, S(r"\b(transfers?|shuttles?|shuttle bus|pick ?-?up|pickup|drop[ -]?off|transport(ation)?|"
                  r"limousine|ride|car service|taxi service)( service)? (?:to|from|to and from|to/from|from/to|"
                  r"between|at)(?: the)?(?: (?:hotel|resort) and(?: the)?)?(?: chiang ?(?:mai|rai))?"
                  r"(?: international)?(?: mae fah luang)?(?: \(?cnx\)?| \(?cei\)?)? airport\b")),
            (3, S(r"\bpick(?:ed)? (?:you |guests? )?up (?:at|from) (?:the )?(?:chiang ?(?:mai|rai) )?"
                  r"(?:international )?airport\b")),
            (3, S(r"รับ ?-? ?ส่ง ?(?:ที่|จาก|ถึง)? ?สนามบิน|รับส่งสนามบิน|airport ?(?:transfer|pick ?up)")),
            (2, S(r"(?:รถรับ ?-? ?ส่ง|บริการรับ ?-? ?ส่ง|รถตู้รับ ?-? ?ส่ง)[^\n]{0,40}สนามบิน|"
                  r"สนามบิน[^\n]{0,25}(?:รถรับ ?-? ?ส่ง|บริการรับ ?-? ?ส่ง)")),
        ],
        "trap": S(r"\bfrom (?:the )?airport,? (?:take|by taxi|it is|it's)|\bgrab\b|\bbolt\b|\bmeter taxi|"
                  r"\bcar rentals?\b|\brent(?:al|ing)? a car\b|\bcar hire\b|\brecommend\b|รถเช่า"),
        "no": [S(r"\b(?:no|don'?t (?:offer|provide|have)|do not (?:offer|provide|have)|does not (?:offer|provide|have)|"
                 r"not (?:offer|provide)) (?:an? |any )?(?:free )?airport (?:transfers?|shuttles?|pick ?-?ups?|"
                 r"pickups?|transportation)\b"),
               S(r"ไม่มี(?:บริการ)?(?:รถ)?รับ ?-? ?ส่ง ?สนามบิน")],
        "near": False,
    },
    "bar": {
        "yes": [
            (3, S(r"\b(roof ?top|sky|lobby|pool|pool ?side|wine|cocktail|beer|whisk(e)?y|gin|jazz|garden|"
                  r"lounge|river ?side|terrace|sunset|hotel|our|the hotel's|on-?site|in-?house|a cozy|cosy|craft beer)"
                  r"[ -]bars?\b")),
            (3, S(r"\bbar (?:&|and|\+|/) ?(?:restaurant|grill|lounge|bistro|cafe|café|kitchen|terrace)\b|"
                  r"\b(?:restaurant|cafe|café|bistro|grill|kitchen|lounge) ?(?:&|and|\+|/) ?bar\b")),
            (3, S(r"(?<!มินิ)(?<!มินิ )บาร์(?!บี|บิ|เบอร์|โค้ด|เบล|เบิ้ล)")),
            (2, S(r"\bbar\b(?!s)")),
        ],
        "trap": S(r"\bmini ?-?bars?\b|\b(salad|juice|snack|coffee|espresso|breakfast|candy|chocolate|granola|"
                  r"protein|oxygen|nail|brow|lash|blow ?dry|tool|side|nav(igation)?|menu|search|status|top|"
                  r"progress|scroll|admin|grab|towel|safety|handle|iron|steel|soap|cereal|smoothie|tea|milk|"
                  r"yogurt|dessert|ice ?cream|noodle|sushi|oyster|raw|tapas|hair|toast)[ -]?bars?\b|"
                  r"\bbar[ -]?(fridges?|stools?|soaps?|codes?|b[ -]?q|be ?cue|graphs?|charts?|rates?|tables?|counters? for work)\b|"
                  r"โต๊ะบาร์|เก้าอี้บาร์|บาร์สำหรับทำงาน|ซาวด์บาร์|ซาวน์บาร์|\bsound ?bars?\b|\bBAR\b(?= ?rate)|"
                  r"best available rate|\bbar (exam|association|council|mitzvah)|\bbars? (?:nearby|around)|"
                  r"\b\d+(\.\d+)? ?bar\b|มินิบาร์|บาร์บีคิว"),
        "no": [S(r"\b(?:no|don'?t have|do not have|does not have|doesn'?t have|there is no|not have)"
                 r" (?:a |an |any )?(?:on-?site )?bar\b(?! ?(?:fridge|stool|code))"),
               S(r"ไม่มีบาร์")],
        "near": True,
    },
    "food": {
        "yes": [
            (3, S(r"\b(?:our|on-?site|in-?house|hotel|resort|the hotel'?s|garden|riverside|rooftop|"
                  r"open-?air|all-?day dining|thai|signature|a|an)(?: own)? restaurants?\b")),
            (3, S(r"\b(?:breakfast (?:is )?(?:included|served|buffet|available|daily|each morning|from \d)|"
                  r"(?:free|complimentary|buffet|continental|american|full|thai|daily|homemade|home-?cooked)"
                  r" breakfast|room (?:and|&|with) breakfast|bed (?:and|&) breakfast|with breakfast|"
                  r"includ(?:es|ing|ed) breakfast|breakfast room|room service|dining room|all-?day dining|"
                  r"(?:our|on-?site|in-?house) (?:café|cafe|coffee shop|kitchen|bakery))\b")),
            (3, S(r"ห้องอาหาร|(?<!ไม่)รวมอาหารเช้า|พร้อมอาหารเช้า|บริการอาหารเช้า|อาหารเช้าฟรี|"
                  r"ฟรีอาหารเช้า|ร้านอาหาร(?:ของ|ภายใน|ใน)(?:โรงแรม|รีสอร์ท|ที่พัก)|รูมเซอร์วิส|"
                  r"บริการอาหาร(?:และเครื่องดื่ม)?")),
            (2, S(r"\brestaurant\b|\bbreakfast\b|\bcaf[eé]\b|\bcafeteria\b|\bcoffee shop\b|\bbistro\b|อาหารเช้า|"
                  r"(?:มี|ภายใน|บริการ|ของเรา)\s?(?:ร้านอาหาร|คาเฟ่|ร้านกาแฟ)|ที่พัก[^\n]{0,15}(?:และ|&|\+)\s?(?:ร้านอาหาร|คาเฟ่)|"
                  r"^(?:ร้านอาหาร|คาเฟ่|ร้านกาแฟ)$")),
        ],
        "trap": S(r"\b(?:no|without|excluding|exclude[sd]?|not include[sd]?|room only)\b[^\n]{0,15}breakfast|"
                  r"breakfast[^\n]{0,12}\bnot (?:included|available|provided|served)|"
                  r"ไม่รวมอาหารเช้า|ไม่มีอาหารเช้า|restaurants? (?:nearby|around|in the area)|"
                  r"\b(?:many|plenty of|lots of|local|various|numerous|several|best|famous|popular|other) "
                  r"(?:restaurants|cafes|cafés)\b|\brestaurant (?:guide|review|recommendation)|"
                  r"\bbreakfast (?:not|isn'?t)|\bbreakfast ?: ?no\b"),
        "no": [S(r"\b(?:no|don'?t have|do not have|does not have|doesn'?t have|there is no|not have)"
                 r" (?:a |an |any )?(?:on-?site )?(?:restaurant|food service|dining facilit(?:y|ies))\b|"
                 r"\b(?:we )?(?:do not|don'?t) serve (?:any )?(?:food|meals)\b"),
               S(r"(?:ไม่มีร้านอาหาร|ไม่มีห้องอาหาร|ไม่มีบริการ ?อาหาร)(?!\s?(?:มื้อ|เช้า|กลางวัน|เที่ยง|เย็น|ค่ำ|ว่าง|ใน ?ห้อง))")],
        "near": True,
    },
}

NEG_BEFORE = S(r"not provided|not available|not offered|not included|unavailable|\bwithout\b|\bno\b[^.,;]{0,12}$|"
               r"ไม่มี|ไม่ได้|ไม่รวม")

FREE = S(r"\bfree\b|complimentary|no charge|free of charge|without charge|ฟรี|ไม่มีค่าใช้จ่าย|ไม่เสียค่า")
PAID = S(r"(?<!free )\bcharge[sd]?\b|surcharge|\bfees?\b|\bTHB\b|\bbaht\b|฿|บาท|ค่าบริการ|ค่าใช้จ่าย(?!ใด)|"
         r"extra cost|additional cost|at (?:a|an extra|additional) cost|\bper (?:car|way|trip|person|vehicle)\b|"
         r"\bpaid\b|on a fee|for a fee|chargeable")

SPAM = S(r"สล็อต|บาคาร่า|แทงบอล|เว็บพนัน|คาสิโน|\bgacor\b|\bjudi\b|\btogel\b|\bslot online\b|"
         r"\bufabet\b|\bpg ?slot\b|\bonline casino\b|\bviagra\b|\bcialis\b|\bescort\b")
PARKED = S(r"domain (?:is |may be )?for sale|buy this domain|this domain (?:is|has been) (?:parked|registered)|"
           r"domain parking|website is (?:under construction|coming soon)|account (?:has been )?suspended|"
           r"index of /|default web site page|apache2? (?:ubuntu )?default page|welcome to nginx|"
           r"it works!|โดเมนนี้")

GENERIC = set("""hotel hotels resort resorts guest house guesthouse home homestay hostel hostels villa villas
the and chiang mai rai thailand boutique residence residences place garden gardens inn lodge room rooms
apartment apartments serviced service mansion city view house stay spa pool hill hills river riverside old
town village valley mountain mountains suite suites by at of in de la le grand royal golden green white
nimman nimmanhaemin north northern lanna thai baan ban camp camping farm farmstay new best nice good
private group co ltd company bed breakfast cafe restaurant bar poshtel capsule backpackers backpacker
mae doi""".split())
TH_GENERIC = re.compile(r"โรงแรม|รีสอร์ท|รีสอร์ต|เกสต์เฮาส์|เกสท์เฮาส์|เกสเฮาส์|โฮมสเตย์|โฮสเทล|"
                        r"อพาร์ทเม้นท์|อพาร์ทเมนท์|แมนชั่น|วิลล่า|บ้านพัก|ที่พัก|เชียงใหม่|เชียงราย|จังหวัด|"
                        r"อำเภอ|และ|[\s\-–&,()./]+")


def name_keys(r):
    """Distinctive name tokens to check that a fetched site is this place's own."""
    keys = set()
    for n in (r.get("nameEn"), r.get("name"), r.get("nameTh")):
        if not n:
            continue
        for w in re.findall(r"[A-Za-z][A-Za-z']{2,}", n):
            wl = w.lower().strip("'")
            if wl not in GENERIC and len(wl) >= 4:
                keys.add(wl)
        squashed = re.sub(r"[^a-z0-9]", "", n.lower())
        if len(squashed) >= 6:
            keys.add("~" + squashed)
        th = TH_GENERIC.sub("", n)
        th = re.sub(r"[A-Za-z0-9]", "", th)
        if len(th) >= 3:
            keys.add("#" + th)
    return keys


def property_path(url):
    sp = urllib.parse.urlsplit(url)
    path = sp.path.strip("/").lower()
    if sp.query and re.search(r"id=|hotel|property", sp.query, re.I):
        return True
    return bool(path) and not re.fullmatch(r"(index|home|default|main)\.\w+|th|en|th-th|en-us|th/index\.\w+|en/index\.\w+|home", path)


def names_differ(rs):
    """Two records on one host whose latin name words share nothing."""
    toks = []
    for r in rs:
        k = {x for x in name_keys(r) if x[0] not in "~#"}
        if k:
            toks.append(k)
    return any(not (a & b) for i, a in enumerate(toks) for b in toks[i + 1:])


def identified(r, pages, start):
    blob = "\n".join((p.get("title") or "") + "\n" + (p.get("text") or "")[:200_000] for p in pages)
    low = blob.lower()
    squash = re.sub(r"[^a-z0-9]", "", low)
    th_squash = re.sub(r"\s+", "", blob)
    keys = name_keys(r)
    for k in keys:
        if k.startswith("~"):
            if k[1:] in squash:
                return True
        elif k.startswith("#"):
            if k[1:] in th_squash:
                return True
        elif re.search(r"\b" + re.escape(k) + r"\b", low):
            return True
    # the domain label in the page text (dehughotel.com → "De Hug Hotel")
    lab = re.sub(r"[^a-z0-9]", "", host_of(start).split(".")[0])
    for _ in range(2):
        lab = re.sub(r"(hotel|resort|chiangmai|chiangrai|cm|cr|house|guesthouse|hostel|homestay|villa|thailand)$", "", lab)
    return len(lab) >= 5 and lab in squash


def snippet(line, m, width=120):
    a, b = m.start(), m.end()
    pad = max(0, (width - (b - a)) // 2)
    s, e = max(0, a - pad), min(len(line), b + pad)
    out = line[s:e].strip()
    if len(out) > width:
        out = out[:width]
    return " ".join(out.split())


EMAIL_URL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+|https?://\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|co\.th|in\.th)\S*")


def scan_text(text):
    """→ {fact: [(strength, kind, snippet, extra)]}"""
    hits = defaultdict(list)
    text = EMAIL_URL.sub(" ", text or "")
    for line in (text or "").split("\n"):
        line = line.strip()
        if len(line) < 3 or len(line) > 4000:
            continue
        question = line.endswith("?") or bool(re.match(r"(is|are|do|does|can|will|how|what|where)\b", line, re.I))
        for fact, spec in FACTS.items():
            no_spans = []
            for rx in spec["no"]:
                for m in rx.finditer(line):
                    hits[fact].append((9, "no", snippet(line, m), None))
                    no_spans.append((m.start(), m.end()))
            for strength, rx in spec["yes"]:
                for m in rx.finditer(line):
                    if any(a <= m.start() < b or a < m.end() <= b for a, b in no_spans):
                        continue
                    win = line[max(0, m.start() - 70): m.end() + 70]
                    tw = 60 if fact == "shuttle" else 25
                    if spec["trap"].search(line[max(0, m.start() - tw): m.end() + tw]):
                        continue
                    if question or NEG_BEFORE.search(line[max(0, m.start() - 40): m.start()]):
                        continue
                    if spec["near"] and NEAR.search(win):
                        continue
                    if fact == "food" and strength == 2 and re.search(r"restaurants\b", m.group(0), re.I):
                        continue
                    extra = None
                    if fact == "shuttle":
                        cw = line[max(0, m.start() - 90): m.end() + 90]
                        f, pd = bool(FREE.search(cw)), bool(PAID.search(cw))
                        if re.search(r"free of charge|ฟรี|complimentary", cw, re.I) and not re.search(
                                r"\bTHB\b|฿|บาท|\bbaht\b", cw, re.I):
                            pd = False
                        extra = "free" if f and not pd else "paid" if pd and not f else None
                    hits[fact].append((strength, "yes", snippet(line, m), extra))
                    break
    return hits


SITE_SOURCE = "own-site"


def facts_from_pages(pages):
    """Best evidence per fact across a site's pages."""
    best = {}
    for p in pages:
        if p.get("error") or not p.get("text"):
            continue
        hits = scan_text((p.get("title") or "") + "\n" + p["text"])
        for fact, hs in hits.items():
            for strength, kind, snip, extra in hs:
                cand = {"value": kind, "evidence": snip, "url": p.get("final") or p["url"],
                        "fetched": p.get("fetched", TODAY), "source": SITE_SOURCE, "_s": strength}
                if extra:
                    cand["cost"] = extra
                cur = best.get(fact)
                # the strongest yes wins; an explicit no stands only with no yes on the site
                # a strong yes outranks an explicit no; the no outranks a bare-word yes
                rank = ((2 if strength >= 3 else 0) if kind == "yes" else 1, strength, 1 if extra else 0)
                if cur is None or rank > cur["_rank"]:
                    cand["_rank"] = rank
                    if cur is not None and cur["value"] != kind:
                        cand["conflict"] = {"value": cur["value"], "evidence": cur["evidence"], "url": cur["url"]}
                    best[fact] = cand
                elif cur["value"] != kind and "conflict" not in cur:
                    cur["conflict"] = {"value": kind, "evidence": snip, "url": cand["url"]}
                cur = best[fact]
                if fact == "shuttle" and kind == "yes" and "cost" not in cur and extra:
                    cur["cost"] = extra
    return best


# ---------------------------------------------------------------- tags already on disk

OSM_RULES = {
    "swimming_pool": "pool", "bar": "bar", "restaurant": "food", "breakfast": "food",
    "breakfast:buffet": "food", "airport_shuttle": "shuttle", "shuttle": "shuttle",
}


def load_osm():
    tags = {}
    for f in sorted((ROOT / "cache" / "overpass").glob("*/*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        fetched = dt.date.fromtimestamp(f.stat().st_mtime).isoformat()
        for e in d.get("elements", []):
            tags[f"{e['type']}/{e['id']}"] = (e.get("tags") or {}, fetched)
    return tags


def load_overture():
    p = ROOT / "cache" / "overture" / "cmcr.jsonl.gz"
    out = {}
    if not p.exists():
        return out, None
    man = json.loads((ROOT / "cache" / "overture" / "manifest.json").read_text())
    for line in gzip.open(p, "rt"):
        r = json.loads(line)
        out[r["id"]] = [r.get("cat")] + (r.get("catAlt") or [])
    return out, man


OVT_FOOD = re.compile(r"restaurant$|^cafe$|^coffee_shop$|^eat_and_drink$|^diner$|^bistro$|^bakery$|^breakfast")
OVT_BAR = re.compile(r"^(bar|pub|cocktail_bar|wine_bar|beer_bar|lounge|sports_bar|beer_garden|whiskey_bar|"
                     r"hookah_bar|dive_bar|gay_bar|tiki_bar|jazz_and_blues|karaoke)$")


def tag_facts(r, osm, ovt, ovt_man):
    out = {}
    for s in r.get("sources") or []:
        if s.get("type") == "osm" and s.get("ref") in osm:
            t, fetched = osm[s["ref"]]
            for k, fact in OSM_RULES.items():
                v = t.get(k)
                if v is None:
                    continue
                val = "no" if v == "no" else "yes"
                out.setdefault(fact, {"value": val, "evidence": f"{k}={v}", "url":
                                      f"https://www.openstreetmap.org/{s['ref']}", "fetched": s.get("fetched", fetched),
                                      "source": "osm", "tag": f"{k}={v}"})
            am = t.get("amenity")
            if am in ("restaurant", "cafe", "fast_food", "food_court"):
                out.setdefault("food", {"value": "yes", "evidence": f"amenity={am}", "url":
                                        f"https://www.openstreetmap.org/{s['ref']}", "fetched": s.get("fetched", fetched),
                                        "source": "osm", "tag": f"amenity={am}"})
            if am in ("bar", "pub", "biergarten"):
                out.setdefault("bar", {"value": "yes", "evidence": f"amenity={am}", "url":
                                       f"https://www.openstreetmap.org/{s['ref']}", "fetched": s.get("fetched", fetched),
                                       "source": "osm", "tag": f"amenity={am}"})
            if t.get("leisure") == "swimming_pool":
                out.setdefault("pool", {"value": "yes", "evidence": "leisure=swimming_pool", "url":
                                        f"https://www.openstreetmap.org/{s['ref']}", "fetched": s.get("fetched", fetched),
                                        "source": "osm", "tag": "leisure=swimming_pool"})
    ids = set()
    if r["id"].split("-", 1)[1].startswith("ovt-"):
        ids.add(r["id"].split("-ovt-", 1)[1])
    for s in r.get("sources") or []:
        if s.get("via") == "overture" and s.get("ref"):
            ids.add(s["ref"])
    for oid in ids:
        cats = [c for c in ovt.get(oid, []) if c]
        for c in cats:
            fact = ("pool" if c == "swimming_pool" else "bar" if OVT_BAR.match(c) else
                    "food" if OVT_FOOD.search(c) else "shuttle" if c in ("airport_shuttles", "airport_shuttle") else None)
            if fact:
                out.setdefault(fact, {"value": "yes", "evidence": f"Overture category {c} (the place's own Facebook page category)",
                                      "url": f"overture:{oid}", "fetched": ovt_man.get("fetched") if ovt_man else None,
                                      "source": "overture", "tag": f"category={c}",
                                      "release": ovt_man.get("release") if ovt_man else None})
    return out


NAME_FACTS = [
    ("pool", S(r"\bpool\b|\bpools\b|สระว่ายน้ำ|พูล ?วิลล่า|พูลวิล่า")),
    ("bar", S(r"\bbar\b(?![ -]?b)|บาร์(?!บี)")),
    ("food", S(r"\brestaurant\b|\bresturant\b|\bcaf[eé]\b|\bcafeteria\b|\bbistro\b|\bkitchen\b|ร้านอาหาร|ห้องอาหาร|คาเฟ่|"
               r"\bbed (?:&|and) breakfast\b|\bb ?& ?b\b")),
]
NAME_TRAP = S(r"pool ?table|liverpool|carpool|snooker|billiard")


def name_facts(r):
    out = {}
    for field in ("name", "nameEn", "nameTh"):
        n = r.get(field)
        if not n or NAME_TRAP.search(n):
            continue
        for fact, rx in NAME_FACTS:
            if fact not in out and rx.search(n):
                out[fact] = {"value": "yes", "evidence": n[:120], "url": None, "fetched": r.get("updatedAt"),
                             "source": "own-name", "field": field}
    return out


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sample", type=int, default=0)
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)

    recs = lodging_records()
    by_url = defaultdict(list)
    for r in recs:
        u = own_site(r)
        if u:
            by_url[u].append(r)
    by_host = defaultdict(list)
    for u in by_url:
        by_host[host_of(u)].append(u)
    hosts = sorted(by_host)
    if args.limit:
        hosts = hosts[: args.limit]
    print(f"lodging {len(recs)} · with own site {sum(len(v) for v in by_url.values())} · "
          f"urls {len(by_url)} · hosts {len(by_host)}", flush=True)

    if args.retry_errors:
        for u in by_url:
            p = cache_path(u)
            if p.exists() and "error" in json.loads(p.read_text()):
                p.unlink()

    site_pages = {}
    if not args.offline:
        lock = threading.Lock()
        done = [0]
        t0 = time.time()

        def work(h):
            res = crawl_site(sorted(by_host[h]))
            with lock:
                done[0] += 1
                if done[0] % 50 == 0:
                    print(f"  {done[0]}/{len(hosts)} hosts · {time.time() - t0:.0f}s", flush=True)
            return res

        with cf.ThreadPoolExecutor(PARALLEL) as ex:
            for res in ex.map(work, hosts):
                site_pages.update(res)
    else:
        global OFFLINE
        OFFLINE = True
        for h in hosts:
            site_pages.update(crawl_site(sorted(by_host[h])))

    # a chain's front page names several properties: a root URL on such a host is set aside
    host_chain = {}
    for h, us in by_host.items():
        rs = [r for u in us for r in by_url[u]]
        host_chain[h] = any(property_path(u) for u in us) and len(rs) > 1 or names_differ(rs)
    osm = load_osm()
    ovt, ovt_man = load_overture()
    out = {}
    stats = Counter()
    site_status = {}
    for u, pages in site_pages.items():
        home = pages[0]
        rs = by_url[u]
        if home.get("error") or (home.get("status") or 0) >= 400:
            site_status[u] = "unreachable"
            continue
        blob = "\n".join((p.get("text") or "") for p in pages)
        if len(SPAM.findall(blob)) >= 2:
            site_status[u] = "spam"
            continue
        if len(blob) < 400 and PARKED.search(blob) or (PARKED.search(blob[:3000]) and len(blob) < 3000):
            site_status[u] = "parked"
            continue
        fh, sh = host_of(home.get("final") or u), host_of(u)
        if fh != sh and SKIP_HOSTS.search(fh):
            site_status[u] = "redirect-ota"
            continue
        names_ok = [r for r in rs if identified(r, pages, u)]
        if not names_ok:
            site_status[u] = "unidentified"
            continue
        if host_chain.get(sh) and not property_path(home.get("via_alternate") or u):
            site_status[u] = "chain-root"
            continue
        site_status[u] = "read"
        facts = facts_from_pages(pages)
        for r in names_ok:
            out[r["id"]] = {k: v for k, v in facts.items()}
        for r in rs:
            if r not in names_ok:
                stats["record-unidentified-on-shared-url"] += 1

    # tags + own name, for every lodging record
    for r in recs:
        cur = out.setdefault(r["id"], {})
        for src in (tag_facts(r, osm, ovt, ovt_man), name_facts(r)):
            for fact, ev in src.items():
                if fact not in cur:
                    cur[fact] = ev
                else:
                    cur[fact].setdefault("also", [])
                    if len(cur[fact]["also"]) < 3 and ev["source"] not in {a["source"] for a in cur[fact]["also"]}:
                        cur[fact]["also"].append({k: ev[k] for k in ("value", "evidence", "source", "url") if ev.get(k)})
                    if cur[fact]["value"] != ev["value"] and "conflict" not in cur[fact]:
                        cur[fact]["conflict"] = {"value": ev["value"], "evidence": ev["evidence"], "url": ev["url"]}
        if not cur:
            del out[r["id"]]

    for v in out.values():
        for ev in v.values():
            ev.pop("_s", None)
            ev.pop("_rank", None)
            if "also" in ev and not ev["also"]:
                del ev["also"]

    status_n = Counter(site_status.values())
    recs_with_site = {r["id"] for u in by_url for r in by_url[u]}
    read_recs = {r["id"] for u, s in site_status.items() if s == "read" for r in by_url[u]
                 if identified(r, site_pages[u], u)}
    counts = {}
    for fact in FACTS:
        c = Counter()
        for v in out.values():
            ev = v.get(fact)
            if ev:
                c[f"{ev['value']}:{ev['source']}"] += 1
                c[ev["value"]] += 1
        counts[fact] = dict(sorted(c.items()))
    shuttle_cost = Counter(v["shuttle"].get("cost", "unstated") for v in out.values()
                           if v.get("shuttle", {}).get("value") == "yes")
    meta = {
        "run": TODAY,
        "lodging_records": len(recs),
        "records_with_own_site": len(recs_with_site),
        "site_urls": len(by_url),
        "site_hosts": len(by_host),
        "site_urls_status": dict(sorted(status_n.items())),
        "records_read_from_own_site": len(read_recs),
        "records_with_any_fact": len(out),
        "facts": counts,
        "shuttle_cost": dict(shuttle_cost),
        "method": (
            "Own website: home page plus up to 4 same-site pages chosen by link text or URL "
            "(facilities, amenities, rooms, services, dining, pool, transfer, about; Thai สิ่งอำนวยความสะดวก, "
            "บริการ, ห้องพัก, ร้านอาหาร, สระว่ายน้ำ, รถรับส่ง). Visible text, image alt text and meta "
            "descriptions read line by line with English and Thai patterns in tools/hotel_amenities.py. "
            "A site counts when a distinctive word of the record's name appears on it; spam, parked, "
            "OTA-redirect and chain front pages are set aside. Words like near, km, minutes, ใกล้, ห่าง in "
            "the same line drop a pool, bar or restaurant hit as off-site. 'no' is recorded only where a "
            "page states it (no pool, ไม่มีสระว่ายน้ำ) or an OSM tag says =no. An absent fact is unknown. "
            "Also folded in: raw OSM tags from cache/overpass (swimming_pool, bar, restaurant, breakfast, "
            "amenity, leisure), Overture categories from cache/overture (the place's own Facebook page "
            "categories), and the record's own name (Pool Villa, Restaurant, Bar). source names which."),
        "sources": {"own-site": "the place's own website, fetched on the date given",
                    "osm": "OpenStreetMap tag on the matched element (ODbL)",
                    "overture": f"Overture Maps places {ovt_man.get('release') if ovt_man else ''} (CDLA-Permissive-2.0)",
                    "own-name": "the place's own name as recorded"},
    }
    final = {"_meta": meta}
    for k in sorted(out):
        final[k] = out[k]
    OUT.write_text(json.dumps(final, ensure_ascii=False, indent=2))
    print(json.dumps(meta, ensure_ascii=False, indent=1)[:3000])

    if args.sample:
        rnd = random.Random(4)
        for fact in FACTS:
            ys = [(k, v[fact]) for k, v in out.items() if v.get(fact, {}).get("source") == SITE_SOURCE
                  and v[fact]["value"] == "yes"]
            print(f"\n== {fact}: {len(ys)} own-site yes")
            for k, ev in rnd.sample(ys, min(args.sample, len(ys))):
                print(f"  {k} | {ev['evidence']} | {ev['url']}")


if __name__ == "__main__":
    main()
