#!/usr/bin/env python3
"""Read each building's OWN site for what it states about itself. Fills the
`stated` block of data/curated/realestate.json. WO-27, door 1.

Same manners and the same first-hand rule as enrich_sites.py, which this
imports rather than reimplements: robots.txt asked once per host and obeyed,
one page per building, a second between requests, an identified User-Agent,
nothing retried in a loop.

WHAT COUNTS AS A SOURCE. The building's own domain, and nothing else
(enrich_sites.NOT_FIRST_HAND). A Facebook page answers a robot with a login
wall, and a wall is not a statement by a building. Every skipped link is
recorded in `could_not_read` with the reason, by name.

TWO RULES THIS READER NEEDS THAT THE HAIR READER DID NOT.

  NEGATION. A page that says ไม่อนุญาตให้เลี้ยงสัตว์ — pets are NOT allowed —
  contains the words "เลี้ยงสัตว์" and would otherwise be read as a building
  that takes your cat. Same for "no pets", "ห้ามเลี้ยงสัตว์", "ไม่มีลิฟต์".
  Every match's left-hand context is checked for a negator and dropped if it
  finds one. This layer cannot render an absence, so a wrongly-claimed yes is
  not a small error: it is somebody arriving with a dog.

  PRICES ARE NOT PARSED. A number beside the word เช่า on a web page may be a
  monthly rent, a nightly rate, a deposit or last year's promotion, and this
  repo has already shipped one price welded to the wrong duration
  (make_shelf_cards, 2026-08-19). So rent sentences are captured whole into
  `rent_evidence` — the sentence, nothing extracted — and `rents_th`/
  `rents_en` stay empty for a person to fill from a board they have seen.
  The page never prints rent_evidence as a price.

WHAT IT WILL AND WILL NOT CLAIM. A `stated` key is written ONLY when the
building's own page contains the words for it, and the sentence it came from
is stored beside the claim as `evidence`, so no line here is unauditable. A
page that does not mention something produces NOTHING for it — not a "no".

    python3 importers/read_realestate_sites.py --dry-run    # look first
    python3 importers/read_realestate_sites.py              # then write
    python3 importers/read_realestate_sites.py --refresh    # re-read held ones

Re-running is safe: a building already in the register is skipped unless
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

REG = ROOT / "data" / "curated" / "realestate.json"
CANON = ROOT / "data" / "canonical"

# facet key -> the words a building uses for it, Thai first. Every Latin term
# is bounded; every Thai term is a compound. Keys are exactly the `realestate`
# set in data/facets.json — nothing here invents a facet the site cannot label.
TERMS = {
    "monthly":   [r"รายเดือน", r"ค่าเช่าต่อเดือน", r"monthly\s+(rate|rent|price)",
                  r"per\s+month\b", r"\blong[-\s]?stay\b"],
    "daily":     [r"รายวัน", r"ค่าเช่าต่อวัน", r"daily\s+(rate|rent)", r"per\s+night\b",
                  r"\bnightly\b", r"short[-\s]?stay"],
    "furnished": [r"เฟอร์ครบ", r"เฟอร์นิเจอร์ครบ", r"พร้อมเฟอร์นิเจอร์",
                  r"fully\s+furnished", r"\bfurnished\b"],
    "lift":      [r"ลิฟต์", r"ลิฟท์", r"\belevators?\b", r"\blifts?\b"],
    "pool":      [r"สระว่ายน้ำ", r"swimming\s+pool", r"\bpool\b"],
    "gym":       [r"ฟิตเนส", r"ห้องออกกำลังกาย", r"\bgym\b", r"fitness\s+(room|centre|center)"],
    "keycard":   [r"คีย์การ์ด", r"คีย์\s*การ์ด", r"key\s*card", r"access\s+card",
                  r"card\s+access"],
    "pets":      [r"เลี้ยงสัตว์ได้", r"รับเลี้ยงสัตว์", r"pet[-\s]?friendly",
                  r"pets?\s+(are\s+)?(allowed|welcome)"],
    "laundry":   [r"ซักรีด", r"เครื่องซักผ้า", r"\blaundry\b", r"washing\s+machine"],
    "rateboard": [r"ค่าไฟหน่วยละ", r"ค่าน้ำหน่วยละ", r"ค่าส่วนกลาง", r"ค่าไฟฟ้าหน่วยละ",
                  r"(electric(ity)?|water)\s+\d+\s*(baht|บาท)?\s*(per|/)\s*unit",
                  r"common\s+(area\s+)?fee"],
    "shortok":   [r"สัญญาระยะสั้น", r"ไม่ต้องทำสัญญา", r"เช่าระยะสั้น",
                  r"short[-\s]?term\s+(lease|contract|rental)",
                  r"no\s+(minimum\s+)?contract"],
    "guard":     [r"รปภ", r"รักษาความปลอดภัย", r"ยามรักษาการณ์",
                  r"security\s+(guard|staff|24)", r"24\s*(-|\s)?hour\s+security"],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in TERMS.items()}

# A negator anywhere in the ~40 characters before a match kills it. Cheap,
# and the failure it prevents is somebody turning up with a dog.
NEGATOR = re.compile(r"ไม่อนุญาต|ไม่รับ|ห้าม|ไม่มี|งดรับ|\bno\b|\bnot\b|\bwithout\b|"
                     r"\bunfurnished\b|ไม่อนุญาตให้", re.I)

# Sentences that talk about rent AND carry a number. Captured whole, never
# parsed — see the module docstring.
RENT_LINE = re.compile(
    r"[^.\n]{0,90}(ค่าเช่า|เช่าเริ่มต้น|ราคาเช่า|rent(al)?\s+(from|price|rate)|"
    r"starting\s+(from|at))[^.\n]{0,90}", re.I)
HAS_NUMBER = re.compile(r"\d[\d,]{2,}")


def load_records():
    out = []
    for p in ("cm", "cr"):
        f = CANON / f"{p}.json"
        if f.exists():
            out += json.loads(f.read_text())
    return out


def queue(records):
    """Every residential record carrying a link, with its link and whether
    that link is a source this repo will read."""
    rows = []
    for r in records:
        if "realestate" not in (r.get("cat") or []):
            continue
        a = r.get("attrs") or {}
        url = r.get("website") or a.get("facebook") or a.get("instagram")
        if not url:
            continue
        rows.append((r, url, es.first_hand(url)))
    return sorted(rows, key=lambda t: (t[0].get("name") or "").lower())


def read_one(url):
    """(text, final_url) or (None, reason).

    THE FIRST-HAND RULE IS CHECKED AGAIN AFTER THE REDIRECTS, and that is not
    belt-and-braces — it caught a live case on the first run. Life in Town's
    own domain no longer belongs to the building: it 302s to
    rogotravel.com/red.php?url=…booking.com…, an affiliate redirector into an
    OTA listing. Checked only before the fetch, that page passed as "the
    building's own site" and its silence would have been published as the
    building's own silence. A lapsed domain pointed at an affiliate farm is
    the commonest way this goes wrong, and an OTA is never the building
    speaking — it is somebody selling nights on it.
    """
    if not es.allowed(url):
        return None, "robots.txt says no"
    try:
        html, final = es.get(url)
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:60]}"
    if not html:
        return None, "not an HTML page"
    if not es.first_hand(final):
        return None, (f"redirects off the building's own domain to {final[:70]} "
                      "— an OTA or affiliate landing is not a statement by the building")
    return es.strip_tags(html), final


def claims(text):
    """facet key -> the phrase on the page that says so. Nothing inferred,
    and nothing kept whose left context negates it."""
    got = {}
    for key, pats in COMPILED.items():
        for rx in pats:
            for m in rx.finditer(text):
                left = text[max(0, m.start() - 40):m.start()]
                if NEGATOR.search(left):
                    continue                     # "ไม่อนุญาตให้เลี้ยงสัตว์"
                lo, hi = max(0, m.start() - 55), min(len(text), m.end() + 55)
                got[key] = {"phrase": m.group(0), "context": text[lo:hi].strip()}
                break
            if key in got:
                break
    return got


def rent_lines(text):
    """Whole sentences mentioning rent and carrying a number. Evidence for a
    person, never a price on a page."""
    out = []
    for m in RENT_LINE.finditer(text):
        s = " ".join(m.group(0).split())
        if HAS_NUMBER.search(s) and s not in out:
            out.append(s)
    return out[:6]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    reg = json.loads(REG.read_text()) if REG.exists() else {"buildings": []}
    reg.setdefault("buildings", [])
    reg.setdefault("could_not_read", [])
    held = {s["place"] for s in reg["buildings"]}

    rows = queue(load_records())
    firsthand = [t for t in rows if t[2]]
    social = [t for t in rows if not t[2]]
    print(f"{len(rows)} residential records carry a link: "
          f"{len(firsthand)} on the building's own domain, "
          f"{len(social)} on Facebook/Instagram/LINE (not a first-hand source here)")

    unread = []
    for r, url, _ in social:
        unread.append({"place": r["id"], "name": r.get("name"), "url": url,
                       "why": "social or messaging link — not a first-hand source "
                              "(enrich_sites.NOT_FIRST_HAND); a login wall is not a "
                              "statement about the building",
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
            print(f"  ✗ {name[:38]:40} {url[:42]}  — {info}")
            unread.append({"place": r["id"], "name": r.get("name"), "url": url,
                           "why": info, "checked": str(date.today())})
            continue
        c = claims(text)
        rents = rent_lines(text)
        print(f"  ✓ {name[:38]:40} {len(text):>7,} chars  — "
              + (", ".join(sorted(c)) if c else "states none of the things asked about"))
        for k, ev in sorted(c.items()):
            print(f"        {k:10} “{ev['phrase']}”")
        for s in rents:
            print(f"        rent?     “{s[:96]}”")
        found.append({
            "place": r["id"], "name": r.get("name"),
            "stated": {k: "yes" for k in sorted(c)},
            "evidence": {k: ev["context"] for k, ev in sorted(c.items())},
            # Captured, never parsed. rents_th/rents_en stay empty until a
            # person has read a board — see the module docstring.
            "rent_evidence": rents,
            "rents_th": "", "rents_en": "",
            # How much text was actually there. Several of these sites are
            # client-rendered shells that hand a robot 56 characters, and a
            # building that "states nothing" out of 56 characters has not
            # been read — it has been visited. Kept so the difference stays
            # visible to whoever reads this register next.
            "page_chars": len(text),
            "source": info, "fetched": str(date.today()),
            "stated_by": "the building's own site",
        })

    print(f"\n{len(found)} building(s) read, {len(unread)} could not be read")
    if a.dry_run:
        print("--dry-run: nothing written")
        return
    by_id = {s["place"]: s for s in reg["buildings"]}
    for s in found:
        by_id[s["place"]] = s
    reg["buildings"] = sorted(by_id.values(), key=lambda s: (s.get("name") or ""))
    seen = {}
    for u in reg["could_not_read"] + unread:
        seen[u["place"]] = u
    reg["could_not_read"] = sorted(seen.values(), key=lambda s: (s.get("name") or ""))
    reg["verified_on"] = str(date.today())
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {REG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
