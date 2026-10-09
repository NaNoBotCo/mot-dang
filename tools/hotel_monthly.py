#!/usr/bin/env python3
"""Monthly and long-stay rates that lodgings state on their own websites.

    python3 tools/hotel_monthly.py              # fetch rate pages not cached, then write
    python3 tools/hotel_monthly.py --offline    # write from the caches only
    python3 tools/hotel_monthly.py --sample N   # print N random monthly quotes

Input: data/canonical/{cm,cr}.json, lodging = cat contains 'hotel' or sub names
hotel/hostel/guesthouse/resort/homestay/serviced/apartment (the same set as
tools/hotel_amenities.py, plus apartment).

Pages read, in order:
  1. cache/hotel_amenities/pages/   (read only; written by tools/hotel_amenities.py)
  2. cache/hotel_monthly/pages/     (this tool's own: up to 3 same-site pages per
     site whose link text or URL names rates, prices, long stay or monthly)

Output: data/curated/hotel_monthly.json
  {"_meta": {...}, "<record id>": {
      "monthly":   [{"thb": 9000, "thb_max": 12000, "quote", "url", "fetched"}],
      "min_stay":  {"months": 3, "quote", "url", "fetched"},
      "utilities": {"value": "included" | "metered" | "partly", "quote", "url", "fetched",
                    "electric_thb_unit": 8, "water_thb_unit": 20},
      "long_stay": {"value": "yes", "quote", "url", "fetched"},
      "site": "<start url>", "site_shared_by": N}}
A record appears only where at least one page states one of these. An absent
fact is unknown.

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
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AMEN_CACHE = ROOT / "cache" / "hotel_amenities" / "pages"
CACHE = ROOT / "cache" / "hotel_monthly" / "pages"
OUT = ROOT / "data" / "curated" / "hotel_monthly.json"
TODAY = dt.date.today().isoformat()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
TIMEOUT = 20
PARALLEL = 12
MAX_EXTRA = 3
MAX_BYTES = 3_000_000
OFFLINE = False

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

SKIP_HOSTS = re.compile(
    r"(^|\.)(facebook\.com|fb\.me|fb\.com|m\.me|instagram\.com|line\.me|lin\.ee|"
    r"booking\.[a-z.]+|agoda\.[a-z.]+|tripadvisor\.[a-z.]+|linktr\.ee|airbnb[a-z]*\.[a-z.]+|abnb\.me|air\.tl|"
    r"oyorooms\.com|trip\.com|expedia\.[a-z.]+|hotels\.com|traveloka\.com|tiktok\.com|"
    r"youtube\.com|youtu\.be|gmail\.com|plus\.google\.com|google\.com|goo\.gl|maps\.app\.goo\.gl|"
    r"renthub\.in\.th|onab\.go\.th|wa\.me|twitter\.com|x\.com|hostelworld\.com|"
    r"ddproperty\.com|hipflat\.co\.th|wongnai\.com|"
    r"chiangraifocus\.com|chiangmaibaan\.com|livinginsider\.com|fazwaz\.[a-z.]+|dotproperty\.[a-z.]+|"
    r"thailandproperty\.com|propertyhub\.in\.th|perfecthomes\.co\.th|kaidee\.com)$")
LODGING_SUB = re.compile(r"hotel|hostel|guest-?house|resort|homestay|serviced|apartment")


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
        h = (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""
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


# ---------------------------------------------------------------- fetch + caches

class Extract(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5",
             "h6", "section", "article", "header", "footer", "nav", "table", "dd", "dt", "option",
             "figcaption", "blockquote", "a", "button", "label", "title"}
    SKIP = {"script", "style", "noscript", "svg", "template", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.skip, self.title = [], [], 0, ""
        self._a, self._in_title = None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "a" and a.get("href"):
            self._a = [a["href"], ""]

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "a" and self._a:
            self._a[1] = " ".join(self._a[1].split())[:120]
            self.links.append(self._a)
            self._a = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self.skip:
            return
        self.parts.append(data)
        if self._a is not None:
            self._a[1] += data


def decode(raw, ctype):
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I) or re.search(rb"charset=[\"']?([\w-]+)", raw[:4000], re.I)
    enc = m.group(1) if m else "utf-8"
    enc = enc.decode() if isinstance(enc, bytes) else enc
    if enc.lower() in ("tis-620", "tis620", "windows-874", "iso-8859-11"):
        enc = "cp874"
    try:
        return raw.decode(enc, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def key(url):
    return hashlib.sha1(url.encode()).hexdigest() + ".json"


def cached(url):
    for d in (AMEN_CACHE, CACHE):
        p = d / key(url)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except ValueError:
                return None
    return None


def fetch(url):
    """One GET into this tool's cache. Reads either cache first."""
    hit = cached(url)
    if hit is not None:
        return hit
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
            text = re.sub(r"[ \t\r\f\v ]+", " ", "".join(ex.parts))
            rec["text"] = re.sub(r"\n\s*\n+", "\n", text).strip()[:400_000]
            rec["links"] = ex.links[:1500]
            rec["title"] = " ".join(ex.title.split())[:200]
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:160]}"
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / key(url)).write_text(json.dumps(rec, ensure_ascii=False))
    return rec


def alternates(url):
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


def home_page(start):
    """The home page from either cache; fetched only when neither holds it."""
    for u in [start] + alternates(start):
        p = cached(u)
        if p and not p.get("error") and (p.get("status") or 0) < 400 and p.get("text") is not None:
            return p
    p = fetch(start)
    if not p.get("error") and (p.get("status") or 0) < 400:
        return p
    for alt in alternates(start):
        a = fetch(alt)
        if not a.get("error") and (a.get("status") or 0) < 400 and a.get("text"):
            return a
    return p


RATE_LINK = re.compile(
    r"rate|price|tariff|long[- _]?stay|long[- _]?term|monthly|month|apartment|rent|promotion|offer|"
    r"ราคา|รายเดือน|เดือน|ระยะยาว|ห้องพัก|เช่า|โปรโมชั่น|อัตรา", re.I)
STRONG_LINK = re.compile(r"long[- _]?stay|long[- _]?term|monthly|month|รายเดือน|ระยะยาว|เดือน|rent|เช่า", re.I)
LINK_SKIP = re.compile(r"\.(jpe?g|png|gif|webp|pdf|zip|mp4|mp3|svg|ics|docx?)(\?|$)|"
                       r"mailto:|tel:|javascript:|whatsapp|/wp-login|/cart|/checkout|/feed|"
                       r"\?replytocom|/tag/|/author/|/category/|/20\d\d/\d\d/", re.I)


def rate_links(page, start):
    base = page.get("final") or start
    hosts = {host_of(base), host_of(start)}
    seen, scored = set(), []
    for href, text in page.get("links") or []:
        if LINK_SKIP.search(href):
            continue
        u = urllib.parse.urljoin(base, html.unescape(href)).split("#")[0]
        if not u.startswith("http") or host_of(u) not in hosts:
            continue
        if u.rstrip("/") in (start.rstrip("/"), base.rstrip("/")) or u in seen:
            continue
        seen.add(u)
        hay = urllib.parse.unquote(u) + " " + text
        hits = RATE_LINK.findall(hay)
        if hits:
            scored.append((-(len(hits) + (4 if STRONG_LINK.search(hay) else 0)), len(u), u))
    scored.sort()
    return [u for _, _, u in scored[:MAX_EXTRA]]


def linked_cached(page, start):
    """Same-site pages tools/hotel_amenities.py already fetched from this home page."""
    base = page.get("final") or start
    out = []
    for href, _ in page.get("links") or []:
        u = urllib.parse.urljoin(base, html.unescape(href)).split("#")[0]
        if u.startswith("http") and (AMEN_CACHE / key(u)).exists():
            out.append(u)
    return out[:8]


def crawl_site(start):
    home = home_page(start)
    pages = [home]
    if home.get("error") or home.get("text") is None:
        return pages
    urls = []
    for u in linked_cached(home, start) + rate_links(home, start):
        if u not in urls:
            urls.append(u)
    for u in urls:
        if cached(u) is None and not OFFLINE:
            time.sleep(0.4)
        pages.append(fetch(u))
    return pages


# ---------------------------------------------------------------- detection

def S(p):
    return re.compile(p, re.I)


MONTH = S(r"\bper\s+month\b|/\s*month\b|/\s*mo\b|\ba\s+month\b|\bmonthly\b|\bmonth(?:ly)?\s+(?:rate|price|rental|stay)\b|"
          r"\b(?:1|one)\s+month\b|รายเดือน|ต่อเดือน|/\s*เดือน|เดือนละ|บาท\s*/\s*เดือน|ราย\s*เดือน")
LONG = S(r"long[- ]?stay|long[- ]?term (?:stay|rental|guests?)|monthly (?:stay|rental|rates?)|"
         r"พักระยะยาว|เช่าระยะยาว|พักรายเดือน|ห้องพักรายเดือน|ห้องเช่ารายเดือน|ให้เช่ารายเดือน")
NOT_RENT = S(r"newsletter|subscri|payment plan|instal+ment|per month (?:for|of) (?:the )?(?:first|next)|"
             r"months? (?:ago|old)|this month|next month|last month|every month we|monthly (?:event|market|special|promotion of the)|"
             r"salary|เงินเดือน|ผ่อน|งวด|ประจำเดือน|เดือนนี้|เดือนหน้า|month of|honeymoon|"
             r"spa|massage|gym membership|membership|parking|ที่จอดรถ|car rental|motorbike|scooter|bike rental|"
             r"เช่ารถ|รถเช่า|มอเตอร์ไซค์|coworking|co-working|desk|tour|visa|breakfast|อาหาร|per ?person|/\s*person|"
             r"ต่อคน|/\s*คน|average daily cost|will cost you|review")
NUM = r"(\d{1,3}(?:,\d{3})+|\d{4,6})(?:\.\d+)?"
CUR = r"(?:฿|THB|thb|Baht|baht|BAHT|บาท|B\b|\.-)"
PRICE = S(rf"(?:{CUR}\s*{NUM}(?:\s*(?:-|–|to|ถึง)\s*{CUR}?\s*{NUM})?|{NUM}(?:\s*(?:-|–|to|ถึง)\s*{NUM})?\s*{CUR})")
YEAR = re.compile(r"^(19|20|25)\d\d$")
MIN_STAY = S(r"(?:minimum|min\.?|at least)\s*(?:stay|rental|contract|lease|booking)?\s*(?:of\s*)?(\d{1,2})\s*(month|months|mo|"
             r"night|nights|day|days|week|weeks)\b|(\d{1,2})[- ]?(month|months)\s*(?:minimum|min\b|contract|lease)|"
             r"ขั้นต่ำ\s*(\d{1,2})\s*(เดือน|คืน|วัน)|สัญญา\s*(?:เช่า)?\s*(?:ขั้นต่ำ)?\s*(\d{1,2})\s*(เดือน|ปี)|"
             r"(?:พัก|เช่า)\s*(?:ขั้นต่ำ|อย่างน้อย)\s*(\d{1,2})\s*(เดือน|คืน|วัน)")
UTIL_WORD = S(r"electric(?:ity)?|water bill|water and electric|utilities|utility|ค่าไฟ|ค่าน้ำ|ค่าน้ำค่าไฟ|ค่าน้ำ-ค่าไฟ|ค่าส่วนกลาง")
UTIL_INCL = S(r"includ(?:e|es|ed|ing)|รวม(?:ค่า|แล้ว)?|ฟรี|free|no extra")
UTIL_EXCL = S(r"not includ|exclud|extra|additional|charged|ไม่รวม|แยก|คิดตาม|ตามมิเตอร์|ตามจริง|according to (?:the )?meter|"
              r"by (?:the )?meter|metered|\bper unit\b|/\s*unit|หน่วยละ|ยูนิตละ|/\s*หน่วย")
UNIT_PRICE = S(r"(?:electric(?:ity)?|ค่าไฟ(?:ฟ้า)?)[^0-9\n]{0,30}?(\d{1,2}(?:\.\d+)?)\s*(?:฿|THB|baht|บาท)?\s*(?:/|per|ต่อ)?\s*(?:unit|kwh|หน่วย|ยูนิต)|"
               r"(?:water|ค่าน้ำ(?:ประปา)?)[^0-9\n]{0,30}?(\d{1,3}(?:\.\d+)?)\s*(?:฿|THB|baht|บาท)?\s*(?:/|per|ต่อ)\s*(?:unit|cubic|m3|หน่วย|ยูนิต|คน|person|เดือน|month)")
SPAM = S(r"สล็อต|บาคาร่า|แทงบอล|เว็บพนัน|คาสิโน|\bgacor\b|\bjudi\b|\btogel\b|\bslot online\b|\bufabet\b|\bpg ?slot\b|"
         r"\bonline casino\b|\bviagra\b|\bcialis\b|\bescort\b")
OTHER_PERIOD = S(r"\b(?:day|days|daily|night|nights|nightly|week|weeks|weekly|year|yearly|annual)\b|คืน|ต่อวัน|/\s*วัน|วันละ|สัปดาห์|อาทิตย์|ต่อปี|/\s*ปี|"
                 r"มัดจำ|deposit|ประกัน|advance")
THIRTY = S(r"\b(?:30|31)\s*(?:คืน|nights?|days?|วัน)")
DEPOSIT = S(r"มัดจำ|deposit|ประกัน|advance|ล่วงหน้า|ค่าแรกเข้า|booking fee|ค่าจอง")
UTIL_BEFORE = S(r"electric(?:ity)?\b(?! *(?:&|and) *water\))|ค่าไฟ|ค่าน้ำ(?!\s*และ)|meter|มิเตอร์|expect to pay|internet|wifi|ค่าเน็ต|ค่าส่วนกลาง|"
                r"parking|ที่จอดรถ|cleaning fee|ค่าทำความสะอาด")
VEHICLE_URL = S(r"scooter|motorbike|motorcycle|bike|car-?rent|vehicle|tour|coworking|spa|massage|visa")
EMAIL_URL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+|https?://\S+|www\.\S+")
PHONE = re.compile(r"(?:\+?66|0)\d[\d\- ]{7,11}\d")


def clip(line, a, b, width=160):
    pad = max(0, (width - (b - a)) // 2)
    s, e = max(0, a - pad), min(len(line), b + pad)
    return " ".join(line[s:e].split())[:width]


def num(s):
    return int(s.replace(",", "")) if s else None


def prices_near(line, m):
    """Monthly prices in a window around a monthly marker on one line."""
    lo, hi = max(0, m.start() - 90), min(len(line), m.end() + 90)
    win = PHONE.sub(" ", line[lo:hi])
    mk = (m.start() - lo, m.end() - lo)
    out = []
    for p in PRICE.finditer(win):
        between = win[p.end():mk[0]] if p.end() <= mk[0] else win[mk[1]:p.start()] if p.start() >= mk[1] else ""
        between = THIRTY.sub(" ", between)
        if OTHER_PERIOD.search(between) or PRICE.search(between) or len(between) > 45:
            continue
        if UTIL_BEFORE.search(win[max(0, p.start() - 60):p.start()]):
            continue
        if DEPOSIT.search(win[max(0, p.start() - 18):p.start()]) or OTHER_PERIOD.match(win[p.end():p.end() + 12].lstrip(" /")):
            continue
        vals = [num(g) for g in p.groups() if g]
        vals = [v for v in vals if v and not YEAR.match(str(v))]
        if not vals:
            continue
        a, b = min(vals), max(vals)
        if 1500 <= a <= 250_000 and b <= 400_000 and b <= a * 4:
            out.append((a, b))
    return out


def scan(text):
    """→ dict of lists: monthly [(thb, thb_max, quote)], min_stay [(months, quote)],
    utilities [(value, quote, e_unit, w_unit)], long [quote]"""
    found = defaultdict(list)
    text = EMAIL_URL.sub(" ", text or "")
    if SPAM.search(text[:20000]):
        return found
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 4 or len(line) > 3000:
            continue
        for m in MONTH.finditer(line):
            ctx = line[max(0, m.start() - 60): m.end() + 60]
            if NOT_RENT.search(ctx):
                continue
            for a, b in prices_near(line, m):
                found["monthly"].append((a, b if b != a else None, clip(line, m.start(), m.end())))
            break
        for m in LONG.finditer(line):
            if not NOT_RENT.search(line[max(0, m.start() - 50): m.end() + 50]):
                found["long"].append(clip(line, m.start(), m.end()))
            break
        for m in MIN_STAY.finditer(line):
            g = [x for x in m.groups() if x]
            if len(g) < 2:
                continue
            n, unit = int(g[0]), g[1].lower()
            months = (n if unit.startswith(("month", "mo", "เดือน")) else n * 12 if unit == "ปี"
                      else round(n / 30, 1) if unit.startswith(("night", "day", "คืน", "วัน")) else round(n / 4.3, 1))
            if unit.startswith(("night", "day", "คืน", "วัน", "week")) and n < 28:
                continue
            if 0 < months <= 24:
                found["min_stay"].append((months, clip(line, m.start(), m.end())))
        for m in UTIL_WORD.finditer(line):
            win = line[max(0, m.start() - 50): m.end() + 70]
            if not (MONTH.search(line) or LONG.search(line) or UNIT_PRICE.search(win)):
                continue
            e = w = None
            for u in UNIT_PRICE.finditer(win):
                if u.group(1):
                    v = float(u.group(1))
                    e = v if 3 <= v <= 15 else e
                if u.group(2):
                    v = float(u.group(2))
                    w = v if 5 <= v <= 400 else w
            excl, incl = bool(UTIL_EXCL.search(win)) or e is not None, bool(UTIL_INCL.search(win))
            val = "metered" if excl and not incl else "included" if incl and not excl else "partly" if incl and excl else None
            if val:
                found["utilities"].append((val, clip(line, m.start(), m.end()), e, w))
            break
    return found


def facts(pages):
    out = {}
    monthly, seen = [], set()
    best = {}
    for p in pages:
        if p.get("error") or not p.get("text"):
            continue
        url, fetched = p.get("final") or p["url"], p.get("fetched", TODAY)
        if VEHICLE_URL.search(urllib.parse.urlsplit(url).path):
            continue
        f = scan((p.get("title") or "") + "\n" + p["text"])
        for a, b, q in f["monthly"]:
            if (a, b) in seen:
                continue
            seen.add((a, b))
            monthly.append({"thb": a, **({"thb_max": b} if b else {}), "quote": q, "url": url, "fetched": fetched})
        if f["min_stay"] and "min_stay" not in best:
            months, q = min(f["min_stay"])
            best["min_stay"] = {"months": months, "quote": q, "url": url, "fetched": fetched}
        if f["utilities"] and "utilities" not in best:
            val, q, e, w = f["utilities"][0]
            u = {"value": val, "quote": q, "url": url, "fetched": fetched}
            if e:
                u["electric_thb_unit"] = e
            if w:
                u["water_thb_unit"] = w
            best["utilities"] = u
        if f["long"] and "long_stay" not in best:
            best["long_stay"] = {"value": "yes", "quote": f["long"][0], "url": url, "fetched": fetched}
    if monthly:
        monthly.sort(key=lambda x: x["thb"])
        out["monthly"] = monthly[:6]
        if "long_stay" not in best:
            best["long_stay"] = {"value": "yes", "quote": monthly[0]["quote"], "url": monthly[0]["url"],
                                 "fetched": monthly[0]["fetched"]}
    out.update(best)
    return out


GENERIC = set("""hotel hotels resort resorts guest house guesthouse home homestay hostel hostels villa villas
the and chiang mai rai thailand boutique residence residences place garden gardens inn lodge room rooms
apartment apartments serviced service mansion city view house stay spa pool hill hills river riverside old
town village valley mountain mountains suite suites by at of in de la le grand royal golden green white
nimman north northern lanna thai baan ban camp farm new best nice good private group co ltd company bed
breakfast cafe restaurant bar mae doi""".split())
TH_GENERIC = re.compile(r"โรงแรม|รีสอร์ท|รีสอร์ต|เกสต์เฮาส์|เกสท์เฮาส์|เกสเฮาส์|โฮมสเตย์|โฮสเทล|อพาร์ทเม้นท์|อพาร์ทเมนท์|"
                        r"อพารต์เมนต์|แมนชั่น|วิลล่า|บ้านพัก|ที่พัก|หอพัก|เชียงใหม่|เชียงราย|จังหวัด|อำเภอ|และ|[\s\-–&,()./]+")


def identified(r, pages, start):
    """The site names this place: a distinctive name word, the squashed name, or the domain label."""
    blob = "\n".join((p.get("title") or "") + "\n" + (p.get("text") or "")[:200_000] for p in pages)
    low = blob.lower()
    squash = re.sub(r"[^a-z0-9]", "", low)
    th_squash = re.sub(r"\s+", "", blob)
    for n in (r.get("nameEn"), r.get("name"), r.get("nameTh")):
        if not n:
            continue
        for w in re.findall(r"[A-Za-z][A-Za-z']{3,}", n):
            wl = w.lower().strip("'")
            if wl not in GENERIC and re.search(r"\b" + re.escape(wl) + r"\b", low):
                return True
        sq = re.sub(r"[^a-z0-9]", "", n.lower())
        if len(sq) >= 6 and sq in squash:
            return True
        th = re.sub(r"[A-Za-z0-9]", "", TH_GENERIC.sub("", n))
        if len(th) >= 3 and th in th_squash:
            return True
    lab = re.sub(r"[^a-z0-9]", "", host_of(start).split(".")[0])
    for _ in range(2):
        lab = re.sub(r"(hotel|resort|chiangmai|chiangrai|cm|cr|house|guesthouse|hostel|homestay|villa|thailand)$", "", lab)
    return len(lab) >= 5 and lab in squash


# ---------------------------------------------------------------- main

def main():
    global OFFLINE
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    OFFLINE = args.offline

    recs = lodging_records()
    by_site = defaultdict(list)
    for r in recs:
        u = own_site(r)
        if u:
            by_site[u].append(r)
    starts = sorted(by_site)
    if args.limit:
        starts = starts[:args.limit]
    host_count = Counter(host_of(u) for u in by_site)

    results = {}
    t0 = time.time()
    with cf.ThreadPoolExecutor(PARALLEL) as ex:
        futs = {ex.submit(crawl_site, s): s for s in starts}
        for i, fu in enumerate(cf.as_completed(futs), 1):
            s = futs[fu]
            try:
                results[s] = fu.result()
            except Exception as e:
                results[s] = [{"url": s, "error": f"{type(e).__name__}: {e}"}]
            if i % 200 == 0:
                print(f"  {i}/{len(starts)} sites, {time.time() - t0:.0f}s", file=sys.stderr)

    out, counts = {}, Counter()
    for s, pages in results.items():
        f = facts(pages)
        if not f:
            continue
        shared = len(by_site[s])
        for r in by_site[s]:
            if not identified(r, pages, s):
                counts["_not_named_on_site"] += 1
                continue
            out[r["id"]] = dict(f, site=s, **({"site_shared_by": shared} if shared > 1 else {}))
            for k in f:
                counts[k] += 1
    sites_read = sum(1 for p in results.values() if p and not p[0].get("error"))
    meta = {
        "built": TODAY,
        "lodging_records": len(recs),
        "with_own_site": sum(len(v) for v in by_site.values()),
        "sites": len(by_site),
        "sites_read": sites_read,
        "records_with_any": len(out),
        "counts": dict(counts),
        "hosts_shared": sum(1 for h, n in host_count.items() if n > 1),
        "method": ("Own website only, and only where the site names the place: the home page and same-site pages already in cache/hotel_amenities, plus up "
                   "to 3 pages whose link names rates, prices, long stay or monthly. A monthly price is a number "
                   "with a currency mark within 90 characters of a monthly marker on the same line (EN + TH), "
                   "1,500–250,000 THB. Quotes are cut from the page text as fetched."),
        "fields": {"monthly": "THB per month as stated; thb_max when the page gives a range",
                   "min_stay": "months, from 'minimum N months' / 'ขั้นต่ำ N เดือน' / 'สัญญา N เดือน'",
                   "utilities": "included / metered / partly, with unit prices when stated",
                   "long_stay": "the page names long stay or monthly rental"},
    }
    OUT.write_text(json.dumps({"_meta": meta, **dict(sorted(out.items()))}, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(meta, ensure_ascii=False, indent=1))

    if args.sample:
        rows = [(rid, m) for rid, v in out.items() for m in v.get("monthly", [])]
        for rid, m in random.sample(rows, min(args.sample, len(rows))):
            print(f"{rid}\t{m['thb']}\t{m.get('thb_max', '')}\t{m['quote']}\t{m['url']}")


if __name__ == "__main__":
    main()
