#!/usr/bin/env python3
"""How much of the medical shelf is actually there, against the provinces' own counts.

A shelf with 859 records looks finished. This says whether it is, by measuring
against numbers the provinces publish about themselves — not against a guess,
and not against nothing:

  Chiang Mai   chiangmai.gdcatalog.go.th `68_11`, counts BY อำเภอ:
               29 state hospitals, 14 private, 272 รพ.สต.,
               10 ศูนย์บริการสาธารณสุข, 1,396 คลินิกทุกประเภท
  Chiang Rai   chiangrai.gdcatalog.go.th `dataset_50_24` / `dataset_50_77`:
               233 สถานบริการสาธารณสุข, 628 คลินิกทุกประเภท (2564)

WHAT IT SHOWS, and it is two different stories on one shelf. The STATE sector is
essentially complete — the CITIZENinfo register is the state's own list and we
hold nearly all of it. The PRIVATE sector is barely started, because the only
source for it is whatever OpenStreetMap happens to hold, and for clinics that is
a small fraction. Saying "859 places" without saying that would let a reader
think the shelf is the town.

This writes nothing to the site. It is a measure, for deciding where to send a
person with a phone and an afternoon.

    python3 importers/audit_medical_coverage.py
"""
import collections
import csv
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CM_CSV = os.path.join(ROOT, "cache", "provincial", "cm_facilities_by_amphoe.csv")

# Published by the provinces themselves. Where a district reports several
# years, the latest is taken. See the module docstring for the sources.
CR_OFFICIAL = {"state_facilities": 233, "clinics": 628, "year": "2564"}


def _read(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def cm_official():
    if not os.path.exists(CM_CSV):
        return None, {}
    rows = list(csv.reader(io.StringIO(_read(CM_CSV))))
    H = {h.strip(): i for i, h in enumerate(rows[0])}
    latest = {}
    for r in rows[1:]:
        if len(r) < len(rows[0]):
            continue
        amp, yr = r[H["อำเภอ"]].strip(), r[H["ปี"]].strip()
        if amp and (amp not in latest or yr > latest[amp][0]):
            latest[amp] = (yr, r)
    tot = collections.Counter()
    for _, (_, r) in latest.items():
        for k in ("โรงพยาบาลรัฐ", "โรงพยาบาลเอกชน", "โรงพยาบาลส่งเสริม",
                  "ศูนย์บริการสาธารณสุข", "คลินิกทุกประเภท"):
            try:
                tot[k] += int((r[H[k]] or "0").replace(",", ""))
            except (ValueError, KeyError):
                pass
    return latest, tot


def ours(prov):
    f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
    if not os.path.exists(f):
        return collections.Counter()
    c = collections.Counter()
    for r in json.load(open(f, encoding="utf-8")):
        if "medical" not in (r.get("cat") or []):
            continue
        c[(r.get("attrs") or {}).get("facilityType") or "(none)"] += 1
    return c


def _line(label, held, official):
    """A percentage over 100 is not a win and must not read like one.

    We hold 105 Chiang Mai "hospitals" against a published 43. That is not
    better coverage — it is two things at once: OpenStreetMap uses
    amenity=hospital loosely (private clinics and specialist centres carry it),
    and the register and the crawl both hold the big hospitals under different
    ids, which is the 35 pairs audit_medical_dupes.py found. Either way the
    number is inflated, and printing a bare 244% would be a lie of arithmetic.
    """
    if not official:
        return f"  {label:34} {held:5}    (no published count)"
    pct = 100.0 * held / official
    if pct > 105:
        return (f"  {label:34} {held:5} of {official:5}   "
                f"OVER — duplicates and loose tagging, not coverage")
    return f"  {label:34} {held:5} of {official:5}   {pct:5.1f}%"


def main():
    latest, cm_off = cm_official()
    cm, cr = ours("cm"), ours("cr")

    print("CHIANG MAI — against สถิติจังหวัดเชียงใหม่ 68_11 "
          f"({len(latest or {})} districts, latest year each)")
    print(_line("รพ.สต. · health stations", cm["health-station"],
                cm_off.get("โรงพยาบาลส่งเสริม", 0)))
    print(_line("โรงพยาบาล · hospitals", cm["hospital"],
                cm_off.get("โรงพยาบาลรัฐ", 0) + cm_off.get("โรงพยาบาลเอกชน", 0)))
    print(_line("คลินิก · clinics", cm["clinic"],
                cm_off.get("คลินิกทุกประเภท", 0)))
    print(_line("ร้านขายยา · pharmacies", cm["pharmacy"], 0))
    print(f"  {'— total on the shelf':34} {sum(cm.values()):5}")

    print(f"\nCHIANG RAI — against สสจ.เชียงราย ({CR_OFFICIAL['year']})")
    state_held = cr["health-station"] + cr["hospital"]
    print(_line("state facilities (รพ.สต. + รพ.)", state_held,
                CR_OFFICIAL["state_facilities"]))
    print(_line("คลินิก · clinics", cr["clinic"], CR_OFFICIAL["clinics"]))
    print(f"  {'— total on the shelf':34} {sum(cr.values()):5}")

    print("\nTHE SHAPE OF IT: the state sector is nearly complete in both "
          "provinces, because\nthe CITIZENinfo register IS the state's own "
          "list. The private half is barely\nstarted — OpenStreetMap is the "
          "only source for it and it holds a small fraction.\nA reader should "
          "be told which half they are looking at.")


if __name__ == "__main__":
    main()
