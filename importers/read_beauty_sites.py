#!/usr/bin/env python3
"""Read each hair shop's OWN site for the services it states. Fills the
`stated` block of data/curated/beauty.json. WO-22, door 2.

Same manners and the same first-hand rule as enrich_sites.py, which this
imports rather than reimplements: robots.txt asked once per host and obeyed,
one page per shop, a second between requests, an identified User-Agent, and
nothing retried in a loop. These are one-chair businesses' servers.

WHAT COUNTS AS A SOURCE. The shop's own domain, and nothing else. That rule
was already written down in enrich_sites.NOT_FIRST_HAND, and it cuts this
queue down hard: of the 18 beauty records carrying a link, ELEVEN are Facebook
pages and one is a LINE contact link. A Facebook page is not a first-hand
source by this repo's standard, it answers a robot with a login wall anyway,
and a wall is not the same as a shop that offers nothing. Every one of them is
recorded in `could_not_read` with the reason, by name — the same discipline
the elephant register uses for a camp whose pages would not open.

WHAT IT WILL AND WILL NOT CLAIM. A `stated` key is written ONLY when the
shop's own page contains the words for it, and the matched phrase is stored
beside the claim as `evidence` so no line here is unauditable. A page that
does not mention a service produces NOTHING for that service — not a "no".
Absent is silence, which is the rule the whole facet layer runs on.

It does not read prices (a price on a page is not a price at the chair, and
the unwalked label exists for that), and it does not infer. A skin clinic
using the word "treatment" about lasers is exactly the failure this design
guards against, which is why every claim carries the sentence it came from.

    python3 importers/read_beauty_sites.py --dry-run    # look first
    python3 importers/read_beauty_sites.py              # then write
    python3 importers/read_beauty_sites.py --refresh    # re-read shops already held

Re-running is safe: a shop already in the register is skipped unless
--refresh is passed.
"""
import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import enrich_sites as es  # noqa: E402  (robots, fetch, first_hand, strip_tags)

REG = ROOT / "data" / "curated" / "beauty.json"
CANON = ROOT / "data" / "canonical"

# facet key -> the words a shop uses for it, Thai first. Every Latin term is
# bounded; every Thai term is a compound, for the same reason audit_beauty.py
# never writes a bare เปีย. Order does not matter — all are tested.
TERMS = {
    "textured":   [r"ผมหยิกฝอย", r"ผมหยิก", r"แอฟโฟร", r"\bafro\b", r"textured\s+hair",
                   r"curly\s+hair", r"coily"],
    "braids":     [r"ถักเปีย", r"เดรดล็อค", r"\bbraid(s|ing)?\b", r"\bdreadlocks?\b",
                   r"corn\s?rows?\b", r"\blocs\b"],
    "extensions": [r"ต่อผม", r"hair\s+extensions?", r"extensions?\s+hair"],
    "wigs":       [r"วิกผม", r"\bwigs?\b", r"hairpiece"],
    "updo":       [r"เกล้าผม", r"ทำผมเจ้าสาว", r"\bupdo\b", r"bridal\s+hair", r"wedding\s+hair"],
    "digiperm":   [r"ดัดดิจิตอล", r"ดัดดิจิทัล", r"digital\s+perm"],
    # "Japanese straightening" is the commonest English name for this here and
    # the first page read used exactly that phrase — a rule anchored on
    # "hair straighten" walked straight past it.
    "rebond":     [r"ยืดผม", r"รีบอนด", r"\brebond(ing)?\b",
                   r"(hair|japanese|thermal|permanent)\s+straighten(ing|ed)?\b"],
    "colour":     [r"ทำสีผม", r"ไฮไลท์", r"hair\s+colou?r", r"colou?ring", r"highlights?\b"],
    "bleach":     [r"ฟอกผม", r"\bbleach(ing)?\b"],
    "fade":       [r"ตัดเฟด", r"สกินเฟด", r"\bskin\s+fade\b", r"\bfade\s+haircut\b"],
    "razorshave": [r"โกนหน้า", r"มีดโกน", r"straight\s+razor", r"hot\s+towel", r"โกนหนวด"],
    "beard":      [r"แต่งเครา", r"ตัดเครา", r"\bbeard\s+(trim|shap|groom)"],
    "scalpcheck": [r"ส่องหนังศีรษะ", r"ตรวจหนังศีรษะ", r"scalp\s+(analys|camera|scan|check)"],
    "treatment":  [r"ทรีตเมนต์ผม", r"สปาผม", r"hair\s+spa", r"hair\s+treatment"],
    "keratin":    [r"เคราติน", r"\bkeratin\b", r"โบทอกซ์ผม", r"hair\s+botox"],
    "housecall":  [r"นอกสถานที่", r"ถึงบ้าน", r"ถึงที่พัก", r"home\s+service",
                   r"mobile\s+(hair|stylist|barber)"],
    "kids":       [r"ตัดผมเด็ก", r"kids?\s+haircut", r"children'?s?\s+haircut"],
    "booking":    [r"จองคิว", r"นัดหมายล่วงหน้า", r"by\s+appointment", r"book\s+in\s+advance"],
    "walkin":     [r"ไม่ต้องจอง", r"walk[-\s]?ins?\s+welcome", r"no\s+appointment\s+needed"],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in TERMS.items()}


def load_records():
    out = []
    for p in ("cm", "cr"):
        f = CANON / f"{p}.json"
        if f.exists():
            out += json.loads(f.read_text())
    return out


def queue(records):
    """Every beauty record carrying a link, with its link and whether that link
    is a source this repo will read."""
    rows = []
    for r in records:
        if "beauty" not in (r.get("cat") or []):
            continue
        a = r.get("attrs") or {}
        url = r.get("website") or a.get("facebook") or a.get("instagram")
        if not url:
            continue
        rows.append((r, url, es.first_hand(url)))
    return sorted(rows, key=lambda t: (t[0].get("name") or "").lower())


def read_one(url):
    """(text, final_url) or (None, reason)."""
    if not es.allowed(url):
        return None, "robots.txt says no"
    try:
        html, final = es.get(url)
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:60]}"
    if not html:
        return None, "not an HTML page"
    return es.strip_tags(html), final


def claims(text):
    """facet key -> the phrase on the page that says so. Nothing inferred."""
    got = {}
    for key, pats in COMPILED.items():
        for rx in pats:
            m = rx.search(text)
            if m:
                lo, hi = max(0, m.start() - 55), min(len(text), m.end() + 55)
                got[key] = {"phrase": m.group(0), "context": text[lo:hi].strip()}
                break
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    reg = json.loads(REG.read_text()) if REG.exists() else {"shops": []}
    reg.setdefault("shops", [])
    reg.setdefault("could_not_read", [])
    held = {s["place"] for s in reg["shops"]}

    rows = queue(load_records())
    firsthand = [t for t in rows if t[2]]
    social = [t for t in rows if not t[2]]
    print(f"{len(rows)} beauty records carry a link: "
          f"{len(firsthand)} on the shop's own domain, "
          f"{len(social)} on Facebook/Instagram/LINE (not a first-hand source here)")

    unread = []
    for r, url, _ in social:
        unread.append({"place": r["id"], "name": r.get("name"), "url": url,
                       "why": "social or messaging link — not a first-hand source "
                              "(enrich_sites.NOT_FIRST_HAND); a login wall is not a "
                              "statement about the shop",
                       "checked": str(date.today())})

    todo = [t for t in firsthand if a.refresh or t[0]["id"] not in held]
    if a.limit:
        todo = todo[:a.limit]
    print(f"reading {len(todo)} own-domain page(s)\n")

    found = []
    for r, url, _ in todo:
        name = r.get("name") or r["id"]
        text, info = read_one(url)
        time.sleep(es.PAUSE)
        if text is None:
            print(f"  ✗ {name[:38]:40} {url[:44]}  — {info}")
            unread.append({"place": r["id"], "name": r.get("name"), "url": url,
                           "why": info, "checked": str(date.today())})
            continue
        c = claims(text)
        print(f"  ✓ {name[:38]:40} {len(text):>7,} chars  — "
              + (", ".join(sorted(c)) if c else "states none of the services asked about"))
        for k, ev in sorted(c.items()):
            print(f"        {k:11} “{ev['phrase']}”")
        found.append({
            "place": r["id"], "name": r.get("name"),
            "stated": {k: "yes" for k in sorted(c)},
            "evidence": {k: ev["context"] for k, ev in sorted(c.items())},
            "source": info, "fetched": str(date.today()),
            "stated_by": "the shop's own site",
        })

    print(f"\n{len(found)} shop(s) read, {len(unread)} could not be read")
    if a.dry_run:
        print("--dry-run: nothing written")
        return
    by_id = {s["place"]: s for s in reg["shops"]}
    for s in found:
        by_id[s["place"]] = s
    reg["shops"] = sorted(by_id.values(), key=lambda s: (s.get("name") or ""))
    seen = {}
    for u in reg["could_not_read"] + unread:
        seen[u["place"]] = u
    reg["could_not_read"] = sorted(seen.values(), key=lambda s: (s.get("name") or ""))
    reg["verified_on"] = str(date.today())
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {REG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
