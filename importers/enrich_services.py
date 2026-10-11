#!/usr/bin/env python3
"""What a place actually DOES, read off its own website by a model.

THE GAP THIS FILLS, measured 2026-09-07. 18,118 of 25,914 records carry no
phone, no hours and no website — nothing a reader could act on. Worse for
answering a question: the median record holds 92 characters of text, a name
and an address, so when somebody asks for electrolysis, a mole biopsy or a
marching band, every door on the site fails the same way. Keyword search
fails, the vector door fails and invents (asked for a women's health clinic
it returned a psychology centre at 0.718), and no amount of ranking reaches a
fact nobody ever wrote down. The site can only answer a question whose answer
is already spelled in a shop's name.

enrich_sites.py already walks these same sites for the CONTACT block — phone,
LINE, socials — and files it with per-field provenance. This is its sibling
and takes the other half: the services, the specialisms, the languages, the
words the place uses for what it sells. It reuses that module's robots.txt
handling, its fetcher and its politeness rather than opening a second, ruder
front door.

THE RULES THE MODEL WORKS UNDER, and they are the whole design:

  ONLY THE PAGE. The model is given the place's own page and nothing else. It
  may not use what it knows about the brand, the street or the trade.

  A CATEGORY IS NOT A FACT. The shelf a directory filed a place under says
  which drawer it went in, not what it does. Tested 2026-09-07 on the shirt-
  maker question: without this rule the model called a fabric dyer and a
  school-uniform embroiderer shirtmakers, on the strength of `sub: tailor`
  alone. With it, both dropped out and the survivors quoted ตัดสูท.

  UNKNOWN IS AN ANSWER. Absence of evidence is not evidence of absence: a page
  that does not mention a service means we do not know, never that the place
  does not do it. Nothing here may write a negative.

  EVERY FIELD CARRIES ITS QUOTE. Each extracted fact keeps the words it was
  read from, so a line on the built site can be argued with.

    python3 importers/enrich_services.py --limit 5 --dry-run   # look first
    python3 importers/enrich_services.py --kind medical --limit 40
    python3 importers/enrich_services.py                       # the whole queue

WRONG PAGE, fixed 2026-10-02. Nothing checked that the page belonged to the
place: on 9/30 14 of 42 entries came off someone else's page (eleven schools
read onab.go.th). queue() now skips a website host shared by more than one
record (facebook.com/<page>, linktr.ee/<x> and kin count by path) and a list of
aggregators; the model must answer page_is_this_place: true or nothing is
written. Held entries that fail either test are listed every run and removed
only with --prune; --recheck also re-asks the model about their cached pages.

Output: data/curated/services.json, keyed by place id in the enrich.json shape
(fields / how / source / fetched), owned wholesale by this importer.
"""
import argparse, json, os, re, sys, time, urllib.parse, hashlib, pathlib
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enrich_sites as ES          # robots, fetcher, politeness, first_hand

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "curated" / "services.json"
PAGECACHE = ROOT / "cache" / "site_pages"
KEYS = json.load(open(pathlib.Path.home() / ".config/nanobotco/keys.json"))
CF = KEYS["cloudflare"]
ACCT = CF.get("account_id") or "fe332688b1b25b543f8429d7f08292a3"
MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
MAX_TEXT = 6000

# Hosts that are not one place's own site: aggregators, directories, mail.
NOT_A_PLACE = {"share.google", "booking.com", "wongnai.com", "wongn.ai",
               "flickr.com", "hotmail.com", "gmail.com", "data.bopp-obec.info",
               "thaischool.in.th"}
# Hosts where the first path segment names the place (facebook.com/<page>).
BY_PATH = {"facebook.com", "m.facebook.com", "web.facebook.com", "fb.me",
           "fb.com", "m.me", "linktr.ee", "instagram.com", "tiktok.com",
           "youtube.com", "sites.google.com", "page.line.me", "shop.line.me",
           "lin.ee", "line.me"}

SCHEMA = """{
 "does": ["<what they actually do or sell, in their own words, up to 8>"],
 "does_th": ["<the same, in Thai, as the page writes it>"],
 "not_stated": true|false,
 "languages": ["<only if the page says so>"],
 "appointment": "required|walk-in|unknown",
 "price_hint": "<only if the page prints a price, else null>",
 "page_is_this_place": true|false,
 "evidence": {"<each key above>": "<the exact words on the page, <=20 words>",
              "page_is_this_place": "<the words naming THIS business, or why not>"}
}"""

PROMPT = """You are reading ONE business's own web page for a Chiang Mai directory.

Extract only what THIS PAGE states. You may not use anything you know about
this business, its brand, or its trade from anywhere else.

A category or shelf label is NOT a fact about what they do.
If the page does not say, the answer is unknown — set "not_stated": true and
leave the field out. Never write that they do NOT do something: a page that is
silent about a service tells us nothing about whether they offer it.
Every field you fill must have the page's own words in "evidence".

FIRST decide whether this page is the PLACE's own page. If it is a parent
organisation, a chain's head office, a government or directory site, a hosting
ad, or a different business, set "page_is_this_place": false and fill nothing
else. A branch counts only if the page is about that branch.

Return ONLY JSON in this shape:
""" + SCHEMA + """

PLACE: {name}
PAGE TEXT:
{text}"""


def call(prompt, maxtok=700):
    import urllib.request
    body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                       "max_tokens": maxtok, "temperature": 0}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/ai/run/{MODEL}",
        data=body, headers={"Authorization": "Bearer " + CF["api_token"],
                            "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
    except Exception as e:
        return {"_error": str(e)}
    res = r.get("result") or {}
    txt = res.get("response")
    if not isinstance(txt, str):
        txt = (((res.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
    i, j = txt.find("{"), txt.rfind("}")
    try:
        return json.loads(txt[i:j + 1])
    except Exception:
        return {"_error": "unparsed"}


def page_text(url):
    """One page per place, cached on disk, robots obeyed — ES's rules."""
    PAGECACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()[:20]
    f = PAGECACHE / f"{key}.txt"
    if f.exists():
        return f.read_text(encoding="utf-8"), True
    if "//" not in url:
        url = "https://" + url.lstrip("/")
    if not ES.first_hand(url) or not ES.allowed(url):
        return None, False
    try:
        html, final = ES.get(url)
    except Exception:
        return None, False
    if not html:
        return None, False
    text = ES.strip_tags(html).strip()
    f.write_text(text[:40000], encoding="utf-8")
    time.sleep(ES.PAUSE)
    return text, False


def site_key(url):
    """The host, or host + first path segment where the path names the place."""
    if "//" not in url:
        url = "https://" + url.lstrip("/")
    u = urllib.parse.urlsplit(url.strip())
    host = (u.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host in BY_PATH:
        seg = [x for x in u.path.split("/") if x]
        return host + "/" + (seg[0].lower() if seg else "")
    return host


def shared_keys(records):
    n = {}
    for r in records:
        if r.get("website"):
            k = site_key(r["website"])
            n[k] = n.get(k, 0) + 1
    return n


def not_this_place(url, counts):
    """Why a URL cannot be trusted as one place's own page, or None."""
    k = site_key(url)
    host = k.split("/")[0]
    if any(host == b or host.endswith("." + b) for b in NOT_A_PLACE):
        return "aggregator"
    if counts.get(k, 0) > 1:
        return f"host shared by {counts[k]} records"
    return None


def queue(records, kind=None, counts=None):
    counts = counts if counts is not None else shared_keys(records)
    out = []
    for r in records:
        if not r.get("website"):
            continue
        if not_this_place(r["website"], counts):
            continue
        if kind and kind not in (r.get("cat") or []):
            continue
        a = r.get("attrs") or {}
        # a place that already says what it does in detail is not the priority
        thin = len(a.get("desc") or "") < 60 and not a.get("tradeTags")
        out.append((0 if thin else 1, r))
    out.sort(key=lambda x: x[0])
    return [r for _, r in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kind", help="only this cat, e.g. medical")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--prune", action="store_true",
                    help="remove held entries that fail the wrong-page guard")
    ap.add_argument("--recheck", action="store_true",
                    help="ask the model whether each held entry's cached page is the place")
    a = ap.parse_args()

    held = {}
    if OUT.exists() and not a.refresh:
        held = json.loads(OUT.read_text())
    records = ES.load_records()
    byid = {r["id"]: r for r in records}
    counts = shared_keys(records)

    # Held entries that fail the guard are listed; --prune removes them.
    dropped = []
    for pid in [k for k in held if not k.startswith("_")]:
        src = held[pid].get("src") or (byid.get(pid) or {}).get("website") or ""
        why = not_this_place(src, counts) if src else None
        if not why and a.recheck and src:
            text, _ = page_text(src)
            if text:
                name = (byid.get(pid) or {}).get("name") or pid
                got = call(PROMPT.replace("{name}", str(name)).replace("{text}", text[:MAX_TEXT]))
                if got.get("page_is_this_place") is False:
                    why = "model: " + str((got.get("evidence") or {}).get("page_is_this_place") or "not this place")[:80]
        if why:
            dropped.append((pid, src, why))
            if a.prune:
                del held[pid]
    for pid, src, why in dropped:
        print(f"  - {pid:<40} {src[:50]:<50} {why}")
    if dropped:
        print(f"{len(dropped)} held entries fail the wrong-page guard"
              f"{' — removed' if a.prune else ' — kept; --prune removes them'}")

    q = queue(records, a.kind, counts)
    if a.limit:
        q = [r for r in q if a.refresh or r["id"] not in held][:a.limit]

    print(f"queue: {len(q)} places with a website"
          f"{' in ' + a.kind if a.kind else ''}")
    wrote = read = silent = 0
    for r in q:
        text, cached = page_text(r["website"])
        if not text:
            silent += 1
            continue
        read += 1
        prompt = PROMPT.replace("{name}", str(r.get("name") or "")).replace("{text}", text[:MAX_TEXT])
        got = call(prompt)
        if got.get("_error"):
            print(f"  ! {r['name'][:40]}: {got['_error'][:60]}")
            continue
        if got.get("page_is_this_place") is not True:
            print(f"  ✗ {r['name'][:40]:<40} not this place's page: "
                  f"{str((got.get('evidence') or {}).get('page_is_this_place') or '')[:60]}")
            continue
        does = [d for d in (got.get("does") or []) if d]
        if not does:
            print(f"  · {r['name'][:40]:<40} page says nothing about what they do")
            continue
        fields = {"attrs": {"services": does}}
        ev = got.get("evidence") or {}
        # Every field carries its quote or it does not get written. The Thai
        # list arrived unquoted on all 35 places in the first medical batch
        # (2026-09-07), which is the one thing this importer may not do.
        if got.get("does_th") and ev.get("does_th"):
            fields["attrs"]["servicesTh"] = got["does_th"]
        if got.get("languages") and ev.get("languages"):
            fields["attrs"]["languages"] = got["languages"]
        if got.get("appointment") in ("required", "walk-in") and ev.get("appointment"):
            fields["attrs"]["appointment"] = got["appointment"]
        if got.get("price_hint") and ev.get("price_hint"):
            fields["attrs"]["priceNote"] = got["price_hint"]
        held[r["id"]] = {
            "fetched": date.today().isoformat(),
            "fields": fields,
            "how": {k: "read off the place's own page by a model, quote kept"
                    for k in fields["attrs"]},
            "evidence": {k: v for k, v in ev.items() if v},
            "license": "official-site",
            "src": r["website"],
            "model": MODEL,
        }
        wrote += 1
        print(f"  ✓ {r['name'][:40]:<40} {', '.join(does[:3])[:70]}")

    print(f"\nread {read} pages, {silent} unreachable, {wrote} places gained services")
    if a.dry_run:
        print("(dry run — nothing written)")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    held["_readme"] = [
        "What a place does, read off its own site by a model — importers/enrich_services.py.",
        "Every field keeps the page's own words in `evidence`. A field that is absent",
        "means the page did not say, NEVER that the place does not do it.",
    ]
    OUT.write_text(json.dumps(held, ensure_ascii=False, indent=1))
    print(f"wrote {OUT}  ({len([k for k in held if not k.startswith('_')])} places)")


if __name__ == "__main__":
    main()
