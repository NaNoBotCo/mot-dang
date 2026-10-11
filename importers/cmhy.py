#!/usr/bin/env python3
"""The CMHY.city read, made a job — one reader, many trades. WO-56+.

WO-54 wrote read_paper_sites.py for the paper trades: snapshot-first into a
cache directory, one page at a time, a pause between fetches, an identified
User-Agent, stdlib only, and the JSON-LD LocalBusiness block parsed
leniently. Every trade Nan asks for after it needs the same read against a
different set of the directory's categories, so this file reuses that
module's fetch and parse functions verbatim and only swaps the two globals
that name the job: which categories, which cache directory.

The directory's own numbering is the contract (category/46-Health/53-…).
A job lists its categories with the Thai and English names the directory
prints, so the note can say what was read in the directory's own words.

  python3 importers/cmhy.py <job>            # fetch what is missing, read the places
  python3 importers/cmhy.py <job> --report   # parse the cache, print the tally
  python3 importers/cmhy.py --jobs           # list the jobs

Cache: cache/cmhy/<job>/ (cat-<id>-p<n>.html, place-<id>.html, index.json,
places.json). A category page cached under another job (WO-55 read 53
Other-Health-Services into cache/ot/) is copied in by hand rather than
fetched twice; the reader never re-fetches a file that exists.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_paper_sites as reader  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

JOBS = {
    # WO-56 — the physiotherapy shelf, which matched nothing (no OSM
    # healthcare=physiotherapist in either province). CMHY files physio
    # clinics under "other health services" beside hearing-aid centres,
    # nursing homes and wellness shops; the register sorts by the words.
    "physio": {"53": ("46-Health/53-Other-Health-Services", "บริการสุขภาพอื่นๆ", "other health services")},
    "dental": {"50": ("46-Health/50-Dental-Clinic", "คลินิกทันตกรรม", "dental clinic")},
    "eye": {"51": ("46-Health/51-Eye-Clinic", "คลินิกตา", "eye clinic"),
            "111": ("46-Health/111-Eyeglasses-Shop", "ร้านแว่นตา", "eyeglasses shop")},
    "ent": {"178": ("46-Health/178-Otolaryngology", "หู คอ จมูก", "ear, nose and throat")},
    "psych": {"181": ("46-Health/181-Psychiatry", "จิตเวช", "psychiatry")},
    "peds": {"203": ("46-Health/203-Pediatrics", "กุมารเวช", "paediatrics")},
    "hospital": {"114": ("46-Health/114-Hospital", "โรงพยาบาล", "hospital")},
    "general": {"99": ("46-Health/99-General-Clinic", "คลินิกทั่วไป", "general clinic")},
    "lab": {"177": ("46-Health/177-Lab-Examination", "แล็บตรวจ", "laboratory")},
    "vets": {"52": ("46-Health/52-Animal-Clinic", "คลินิกสัตว์", "animal clinic"),
             "184": ("85-Services/184-Pet-Shop", "ร้านสัตว์เลี้ยง", "pet shop"),
             "183": ("85-Services/183-Bath-Pet-Grooming", "อาบน้ำตัดขน", "pet grooming")},
    "mend": {"265": ("33-Personal/265-Repair-Service-Apparel", "ซ่อมเสื้อผ้า", "apparel repair"),
             "77": ("85-Services/77-Repair-Tools-Services", "ซ่อมเครื่องมือ", "tool repair"),
             "267": ("85-Services/267-General-Appliance-Repair", "ซ่อมเครื่องใช้ไฟฟ้า", "appliance repair"),
             "70": ("60-Automotive/70-Bicycle", "จักรยาน", "bicycle")},
    "laundry": {"126": ("85-Services/126-Laundry-Service", "ซักรีด", "laundry service"),
                "266": ("85-Services/266-Laundromat", "สะดวกซัก", "laundromat"),
                "110": ("85-Services/110-Washing-Drying-Machine", "เครื่องซักผ้าหยอดเหรียญ", "coin washer-dryer")},
    "motorbike": {"127": ("60-Automotive/127-Motorcycle-Showroom", "โชว์รูมมอเตอร์ไซค์", "motorcycle showroom"),
                  "146": ("60-Automotive/146-Motorcycle-Repair-Shop", "ซ่อมมอเตอร์ไซค์", "motorcycle repair"),
                  "67": ("60-Automotive/67-Car-Rental", "เช่ารถ", "car rental")},
    "water-gas": {"194": ("85-Services/194-Coin-Water-Machine", "ตู้น้ำหยอดเหรียญ", "coin water machine"),
                  "209": ("85-Services/209-Gas-Delivery", "ส่งแก๊ส", "gas delivery"),
                  "120": ("60-Automotive/120-LPG-Station", "ปั๊มแก๊ส LPG", "LPG station")},
    "coworking": {"230": ("85-Services/230-Co-working-Space", "โคเวิร์กกิ้ง", "co-working space"),
                  "76": ("85-Services/76-Lawyer", "ทนายความ", "lawyer"),
                  "200": ("85-Services/200-Acounting", "บัญชี", "accounting")},
    "funeral": {"125": ("71-Business/125-Shop-used-for-Religious-Ceremonies", "ร้านสังฆภัณฑ์-พิธี", "ceremony supplies"),
                "160": ("96-Religious-Place/160-Cemetery", "สุสาน", "cemetery"),
                "225": ("85-Services/225-Foundation", "มูลนิธิ", "foundation")},
}


def run(job, report_only=False):
    if job not in JOBS:
        raise SystemExit(f"unknown job {job!r}; --jobs lists them")
    reader.CACHE = ROOT / "cache" / "cmhy" / job
    reader.CATEGORIES = JOBS[job]
    places = reader.CACHE / "places.json"
    if report_only and places.exists():
        reader.report(json.loads(places.read_text()))
        return
    index = reader.harvest()
    rows = reader.read_places(index)
    reader.report(rows)


def rows_of(job):
    """The read, zero network — for the register builders."""
    p = ROOT / "cache" / "cmhy" / job / "places.json"
    return json.loads(p.read_text()) if p.exists() else []


def main():
    if "--jobs" in sys.argv:
        for k, v in JOBS.items():
            print(f"  {k:12s} " + " · ".join(f"{cid} {th}" for cid, (_, th, _) in v.items()))
        return
    jobs = [a for a in sys.argv[1:] if not a.startswith("--")]
    for job in jobs:
        print(f"== {job} ==")
        run(job, report_only="--report" in sys.argv)


if __name__ == "__main__":
    main()
